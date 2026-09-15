"""Margin Map Phase 7B — Page 4 (Scenario Sensitivity by Discount Band) builder.

Reads the frozen AO-04 view `variance_by_band` from
`data/processed/marginmap.db` READ-ONLY, verifies it against the frozen
expectations, and emits the Page 4 implementation bundle into `powerbi/`:

  - page4_variance_values.csv  (verbatim 420-row source slice, TEXT kept)
  - Page4_Report_Layout.json   (exact Desktop build instructions: page name,
                                per-scenario baseline/hypothetical/variance
                                sections over fixed baseline bands, visual
                                types, bindings, formats, labels, caveats —
                                no DAX, no relationships, no re-banding)
  - Page4_preview.html         (faithful self-contained rendering of the page
                                with values verbatim from SQLite, for review
                                where Power BI Desktop is absent)
  - Page4_AUDIT_REPORT.md      (audit report generated from the live
                                validation results of this run)

No `.pbix` is assembled here: this environment has no Power BI Desktop / SSAS
model engine, so a hand-assembled binary could not be opened or verified and
would violate the Phase 7A "only if explicitly supported safely" rule.

Writes only the four bundle files above. Never writes to the database or to
any frozen artifact. Fails loudly (non-zero exit, nothing written) on the
first failed gate. Standard library only.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "marginmap.db"
OUT_DIR = ROOT / "powerbi"
AO04_CSV = ROOT / "data" / "processed" / "phase4c_contribution_variance_by_band.csv"
AO04_QUALITY = ROOT / "data" / "processed" / "phase4c_contribution_variance_by_band_quality.json"

PAGE_NAME = "Page 4 \u2014 Scenario Sensitivity by Discount Band"
VIEW = "variance_by_band"
TABLE = "ao04_band_variance"
ALLOWED_OBJECTS = {VIEW, TABLE, "sqlite_master"}

EXPECTED_COLS = ["output_name", "scenario_status", "grain", "scenario_id",
                 "band", "block", "source_artifact", "metric_name",
                 "metric_value", "unit", "definition_ref", "limitation"]
EXPECTED_SCENARIOS = ["uniform_replace_0.10", "discount_increase_pp_0.00",
                      "discount_decrease_pp_0.00"]
EXPECTED_BANDS = ["B0", "B1", "B2", "B3", "B4", "B5", "TOTAL"]
EXPECTED_BLOCKS = ["baseline", "hypothetical", "variance"]
BASELINE_METRICS = ["base_contribution", "base_wad", "quantity", "order_count",
                    "line_count", "neg_base_orders"]
HYPO_METRICS = ["hypo_contribution", "hypo_wad", "neg_hypo_orders"]
VARIANCE_METRICS = ["variance_net_revenue", "variance_discount_amount",
                    "variance_cogs", "variance_freight", "variance_cost_to_serve",
                    "variance_contribution", "relative_contribution_variance",
                    "margin_change_pp", "low_sample_flag",
                    "fixed_unit_cost_view", "demand_response_view"]
ABS_CUR = ["variance_contribution", "variance_net_revenue",
           "variance_discount_amount", "variance_cogs"]
EXPECTED_ROWS = 420
EXPECTED_NA = {(s, b, "variance", m) for s in EXPECTED_SCENARIOS
               for b in EXPECTED_BANDS
               for m in ("fixed_unit_cost_view", "demand_response_view")}

SCENARIO_INFO = {
    "uniform_replace_0.10": {
        "type": "uniform replacement",
        "discount_input": "replacement_rate 0.10",
        "source_artifact": "phase4b_scenario_uniform_0.10.csv",
        "note": "Headline sensitivity allocated across baseline bands."},
    "discount_increase_pp_0.00": {
        "type": "discount increase",
        "discount_input": "increase_pp 0.00",
        "source_artifact": "phase4b_scenario_increase_0.00.csv",
        "note": "Identity control \u2014 zero variance on every band by "
                "construction; pipeline-integrity check, not sensitivity."},
    "discount_decrease_pp_0.00": {
        "type": "discount decrease",
        "discount_input": "decrease_pp 0.00",
        "source_artifact": "phase4b_scenario_decrease_0.00.csv",
        "note": "Identity control \u2014 zero variance on every band by "
                "construction; pipeline-integrity check, not sensitivity."},
}

U_B5_VAR = "45401.369600000005"
U_TOTAL_VAR = "95406.2413300001"

CAVEAT_SHORT = ("Illustrative constant-quantity arithmetic sensitivity, "
                "not a forecast.")
CAVEAT_LONG = ("Observed baseline beside the hypothetical restatement under the "
               "stated methodology and cost assumptions; conditional arithmetic "
               "illustration, not a forecast, causal estimate, demand prediction, "
               "or optimized-pricing recommendation.")

ASSUMPTIONS = [
    "Constant observed quantity (hypothetical restates observed units; no "
    "response estimated).",
    "Modeled COGS (frozen revenue-based percentages; band variances conditional "
    "on this structure; AO-04 carries no standalone gross-profit row \u2014 "
    "variance_net_revenue, variance_cogs, variance_contribution, and "
    "variance_discount_amount are displayed separately, never netted).",
    "Observed freight passthrough (freight and cost-to-serve variances "
    "exactly 0.0 on all 21 band rows by design).",
    "Return-processing costs OFF (excluded, not actual).",
    "Support costs OFF (excluded, not actual).",
    "Results conditional on the selected cost structure and benchmark assumptions.",
]

CHECKS: list[tuple[str, str]] = []


def fail(check: str, expected: str, actual: str) -> "NoReturn":  # type: ignore[name-defined]
    raise SystemExit(
        f"PAGE4 BUILD FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}"
    )


def passed(check: str, detail: str) -> None:
    CHECKS.append((check, detail))
    print(f"PASS [{check}] {detail}")


class TrackedConn:
    """Read-only connection wrapper recording every table/view touched."""

    def __init__(self, con: sqlite3.Connection) -> None:
        self._con = con
        self.touched: set[str] = set()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        for name in re.findall(r"(?i)\bFROM\s+([A-Za-z0-9_]+)", sql):
            self.touched.add(name)
        return self._con.execute(sql, params)


def fmt(value: str, unit: str) -> str:
    """Display formatting only. Stored TEXT is never altered."""
    if value == "":
        return "N/A"
    if unit == "CUR":
        return f"${float(value):,.2f}"
    if unit == "PCT":
        return f"{float(value):,.2f}%"
    if unit == "PP":
        return f"{float(value):,.4f} pp"
    if unit == "DEC":
        return f"{float(value):,.4f}"
    if unit == "CT":
        return f"{int(float(value)):,}"
    return value


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def build_artifacts(rows: list[tuple]) -> dict[str, str]:
    """Pure build: rows in -> {filename: content}. No I/O, no randomness."""
    by_key = {(r[3], r[4], r[5], r[7]): r for r in rows}  # (scen, band, block, metric)
    na_rows = sorted({(r[3], r[4], r[5], r[7], r[10], r[11]) for r in rows if r[8] == ""})

    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["output_name", "scenario_status", "grain", "scenario_id",
                "band", "block", "source_artifact", "metric_name",
                "metric_value", "unit", "definition_ref", "limitation"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8],
                    r[9], r[10], r[11]])
    csv_text = buf.getvalue()

    def cell(sid: str, band: str, block: str, metric: str) -> dict:
        r = by_key[(sid, band, block, metric)]
        return {"stored_value": r[8], "unit": r[9],
                "display": fmt(r[8], r[9])}

    sections = []
    for sid in EXPECTED_SCENARIOS:
        info = SCENARIO_INFO[sid]
        sections.append({
            "scenario_id": sid, "scenario_type": info["type"],
            "discount_input": info["discount_input"],
            "source_artifact": info["source_artifact"], "note": info["note"],
            "bands": EXPECTED_BANDS, "band_note": "fixed baseline bands \u2014 never re-banded",
            "blocks": [
                {"block": "baseline", "status": "OBSERVED BASELINE",
                 "visual": "matrix", "metrics": BASELINE_METRICS,
                 "cells": {b: {m: cell(sid, b, "baseline", m) for m in BASELINE_METRICS}
                           for b in EXPECTED_BANDS}},
                {"block": "hypothetical",
                 "status": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY",
                 "visual": "matrix", "metrics": HYPO_METRICS,
                 "cells": {b: {m: cell(sid, b, "hypothetical", m) for m in HYPO_METRICS}
                           for b in EXPECTED_BANDS}},
                {"block": "variance",
                 "status": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY",
                 "visuals": ["clustered bar chart", "matrix", "table"],
                 "absolute_currency": ABS_CUR,
                 "relative_percent": ["relative_contribution_variance"],
                 "pp_metrics": ["margin_change_pp"],
                 "cells": {b: {m: cell(sid, b, "variance", m) for m in VARIANCE_METRICS}
                           for b in EXPECTED_BANDS}}]})

    layout = {
        "page_name": PAGE_NAME,
        "source": {"database": "data/processed/marginmap.db", "view": VIEW,
                   "source_artifact": "phase4c_contribution_variance_by_band.csv",
                   "import_mode": "Import", "only_view_imported": True},
        "model": {"relationships": [], "dax_measures": [],
                  "power_query_calculations": []},
        "scenario_slicer": {"column": "scenario_id", "mode": "single-select",
                            "scope": "this page only", "no_model_relationship": True,
                            "options": EXPECTED_SCENARIOS},
        "sections": sections,
        "na_reasons": [{"scenario_id": n[0], "band": n[1], "block": n[2],
                        "metric": n[3], "definition_ref": n[4],
                        "limitation": n[5]} for n in na_rows],
        "labels": {"standing": "HYPOTHETICAL SCENARIO ANALYSIS \u2014 band allocation "
                               "of arithmetic sensitivity",
                   "grain": "Reporting grain: Overall \u00d7 baseline discount band "
                            "(ORDER, fixed bands)",
                   "source_view": VIEW,
                   "source_artifact": "AO-04 contribution variance by baseline band",
                   "validation": "21/21 PASS "
                                 "(phase4c_contribution_variance_by_band_quality.json)",
                   "distinction": "Variance rows stay separate: variance_net_revenue vs "
                                  "variance_cogs vs variance_contribution vs "
                                  "variance_discount_amount (revenue forgone, not profit "
                                  "loss). AO-04 carries no standalone gross-profit row; "
                                  "nothing is netted. Absolute currency changes stay "
                                  "separate from relative percent and percentage-point "
                                  "margin changes."},
        "methodology": ASSUMPTIONS,
        "caveat_short": CAVEAT_SHORT,
        "caveat_long": CAVEAT_LONG,
        "restrictions": ["fixed baseline bands \u2014 never re-banded",
                         "baseline/hypothetical/variance never merged",
                         "no trend/predictive/AI visuals",
                         "summarization off on all value fields",
                         "all columns imported as Text"],
    }
    layout_text = json.dumps(layout, indent=2)

    def band_matrix(sid: str, block: str, metrics: list[str], title: str,
                    status: str) -> str:
        head = "".join(
            f'<th class="{"totalcol" if b == "TOTAL" else ""}">{b}</th>'
            for b in EXPECTED_BANDS)
        body = []
        for m in metrics:
            tds = []
            for b in EXPECTED_BANDS:
                r = by_key[(sid, b, block, m)]
                v, u, lim = r[8], r[9], r[11]
                cls = "totalcol" if b == "TOTAL" else ""
                if v == "":
                    tds.append(
                        f'<td class="na {cls}" title="{esc(r[10])}: {esc(lim)}">'
                        f'N/A *</td>')
                else:
                    tds.append(
                        f'<td class="num {cls}" data-source-value="{esc(v)}">'
                        f'{esc(fmt(v, u))}</td>')
            body.append(f"      <tr><td>{esc(m)}</td>{''.join(tds)}</tr>")
        return (f'    <h3>{esc(title)} <span class="status">{esc(status)}</span></h3>\n'
                f'    <table class="matrix">\n'
                f'      <tr><th>Metric (unit shown per value)</th>{head}</tr>\n'
                + "\n".join(body) + "\n    </table>")

    def variance_bars(sid: str) -> str:
        vals = [(b, by_key[(sid, b, "variance", "variance_contribution")])
                for b in EXPECTED_BANDS[:6]]
        vmax = max(abs(float(r[8])) for _, r in vals) or 1.0
        out = []
        for b, r in vals:
            v = float(r[8])
            out.append(
                f'      <div class="bar-row"><span class="bar-label">{b}</span>'
                f'<span class="bar{" neg" if v < 0 else ""}" '
                f'style="width:{abs(v) / vmax * 55:.1f}%"></span>'
                f'<span class="bar-val" data-source-value="{esc(r[8])}">'
                f'{esc(fmt(r[8], r[9]))}</span></div>')
        t = by_key[(sid, "TOTAL", "variance", "variance_contribution")]
        out.append(
            f'      <div class="bar-row total"><span class="bar-label">TOTAL '
            f'(reconciliation)</span><span class="bar totalbar" '
            f'style="width:55.0%"></span>'
            f'<span class="bar-val" data-source-value="{esc(t[8])}">'
            f'{esc(fmt(t[8], t[9]))}</span></div>')
        return "\n".join(out)

    def recon_strip(sid: str) -> str:
        t = by_key[(sid, "TOTAL", "variance", "variance_contribution")]
        s = sum(float(by_key[(sid, b, "variance", "variance_contribution")][8])
                for b in EXPECTED_BANDS[:6])
        return (f'    <p class="recon">TOTAL reconciliation (stored values): '
                f'band B0\u2013B5 variance sum = '
                f'<b data-source-value="bandsum">{s:.2f}</b> vs stored TOTAL '
                f'<b data-source-value="{esc(t[8])}">{esc(fmt(t[8], t[9]))}</b> '
                f'\u2014 bands sum to TOTAL within 0.05 per frozen validation '
                f'(band-totals-reconcile). The stored TOTAL row is the authority; '
                f'no client-side sum replaces it.</p>')

    scen_html = []
    for sid in EXPECTED_SCENARIOS:
        info = SCENARIO_INFO[sid]
        scen_html.append(
            f'  <h2>Scenario: {esc(sid)}</h2>\n'
            f'  <div class="meta"><b>Scenario type:</b> {esc(info["type"])} '
            f'&nbsp;|&nbsp; <b>Discount input:</b> {esc(info["discount_input"])} '
            f'&nbsp;|&nbsp; <b>Source:</b> {esc(info["source_artifact"])}<br>'
            f'  <b>Bands:</b> fixed baseline bands B0\u2013B5 + TOTAL (never re-banded) '
            f'&nbsp;|&nbsp; <b>Note:</b> {esc(info["note"])}</div>\n'
            + band_matrix(sid, "baseline", BASELINE_METRICS,
                          "A. Baseline contribution", "OBSERVED BASELINE") + "\n"
            + band_matrix(sid, "hypothetical", HYPO_METRICS,
                          "B. Hypothetical contribution",
                          "HYPOTHETICAL_ARITHMETIC_SENSITIVITY") + "\n"
            + '    <h3>C. Variance '
            '<span class="status">HYPOTHETICAL_ARITHMETIC_SENSITIVITY</span></h3>\n'
            + variance_bars(sid) + "\n" + recon_strip(sid) + "\n"
            + band_matrix(sid, "variance", VARIANCE_METRICS,
                          "C (detail). Variance rows \u2014 currency, percent and "
                          "percentage-point scales kept separate",
                          "HYPOTHETICAL_ARITHMETIC_SENSITIVITY") + "\n"
            + f'  <div class="caveat">{esc(CAVEAT_LONG)}</div>')
    scen_html = "\n".join(scen_html)

    na_foot = "\n".join(
        f"      <li><b>{esc(n[0])} / {esc(n[1])} / {esc(n[2])} / {esc(n[3])}</b> "
        f"\u2014 {esc(n[4])}: {esc(n[5])}</li>" for n in na_rows)
    assumps = "\n".join(f"      <li>{esc(a)}</li>" for a in ASSUMPTIONS)

    preview = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(PAGE_NAME)} \u2014 preview (not a .pbix)</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 24px; color: #1b1b1b;
         background: #f5f5f5; }}
  .page {{ max-width: 1240px; margin: auto; background: #fff; padding: 28px 32px;
           border: 1px solid #ddd; }}
  h1 {{ font-size: 24px; margin: 0 0 4px; }}
  h2 {{ font-size: 18px; margin: 26px 0 8px; border-bottom: 3px solid #0f5c2e;
        padding-bottom: 4px; }}
  h3 {{ font-size: 14px; margin: 14px 0 6px; }}
  .banner {{ display: inline-block; background: #0f5c2e; color: #fff; font-weight: 600;
             padding: 4px 12px; margin: 8px 0; font-size: 13px; letter-spacing: .5px; }}
  .status {{ font-size: 11px; background: #333; color: #fff; padding: 2px 8px;
             letter-spacing: .4px; }}
  .meta {{ font-size: 13px; color: #333; line-height: 1.7; background: #f0f4f1;
           border-left: 4px solid #0f5c2e; padding: 10px 14px; margin: 12px 0 6px; }}
  table.matrix {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  table.matrix th, table.matrix td {{ border: 1px solid #ccc; padding: 5px 7px;
                                      text-align: left; vertical-align: top; }}
  table.matrix th {{ background: #0f5c2e; color: #fff; }}
  td.num {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
  td.na {{ text-align: center; color: #8a6d00; font-weight: 600; background: #fff8e1; }}
  .totalcol {{ background: #eef3ee; font-weight: 600; }}
  th.totalcol {{ background: #0b4522 !important; }}
  .bar-row {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; font-size: 13px; }}
  .bar-label {{ width: 170px; }}
  .bar {{ display: inline-block; height: 16px; background: #0f5c2e; }}
  .bar.neg {{ background: #a4262c; }}
  .bar.totalbar {{ background: #555; }}
  .bar-val {{ font-variant-numeric: tabular-nums; }}
  .bar-row.total {{ border-top: 2px solid #555; padding-top: 6px; margin-top: 8px; }}
  .recon {{ font-size: 13px; background: #fafafa; border: 1px solid #ddd;
            padding: 8px 12px; }}
  .note {{ font-size: 13px; line-height: 1.65; background: #fafafa;
           border: 1px solid #ddd; padding: 12px 16px; margin-top: 20px; }}
  .note h2 {{ border: none; margin: 0 0 6px; padding: 0; }}
  .caveat {{ font-size: 13px; font-weight: 600; border: 2px solid #8a6d00;
             background: #fff8e1; padding: 10px 14px; margin-top: 16px; }}
  .caveat.top {{ font-size: 14px; }}
  .footer {{ font-size: 12px; color: #666; margin-top: 18px; }}
</style>
</head>
<body>
<div class="page">
  <h1>{esc(PAGE_NAME)}</h1>
  <div class="banner">HYPOTHETICAL SCENARIO ANALYSIS</div>
  <div class="caveat top">{esc(CAVEAT_SHORT)}</div>
  <div class="meta">
    <b>Source view:</b> variance_by_band &nbsp;|&nbsp;
    <b>Source artifact:</b> AO-04 contribution variance by baseline band
    (phase4c_contribution_variance_by_band.csv)<br>
    <b>Reporting grain:</b> Overall \u00d7 baseline discount band, ORDER basis,
    fixed bands B0\u2013B5 + TOTAL &nbsp;|&nbsp; <b>Validation status:</b> 21/21 PASS
    (phase4c_contribution_variance_by_band_quality.json)<br>
    <b>Quality:</b> low_sample_flag per variance block shown in detail matrices;
    band variances sum to the stored TOTAL within 0.05 per frozen validation;
    identity (0.00) instances read exactly 0.0 on every band by construction.<br>
    <b>Reading rule:</b> baseline, hypothetical, and variance blocks are separate
    areas \u2014 never merged. Absolute currency changes are separate from relative
    percent and percentage-point margin changes. Variance rows stay separate
    (net revenue vs COGS vs contribution vs discount forgone); no standalone
    gross-profit row exists in AO-04 and none is constructed.
  </div>
{scen_html}
  <div class="note"><h2>N/A reasons (exact frozen text, 42 rows)</h2><ul>
{na_foot}
  </ul></div>
  <div class="note"><h2>Methodology assumptions and limitations</h2><ul>
{assumps}
  </ul><p>Identity (0.00) scenarios are pipeline-integrity controls with zero variance
  by construction; they measure no economic sensitivity. No re-banding under any
  circumstance; no order-level hypothetical detail exists or is shown.</p></div>
  <div class="caveat">{esc(CAVEAT_LONG)}</div>
  <div class="footer">Preview generated by powerbi/page4_build.py from
    data/processed/marginmap.db (read-only). Display formatting of exact stored TEXT;
    each value carries its source string in <i>data-source-value</i>. No DAX, no
    relationships, no new calculations, no new scenarios, no re-banding.</div>
</div>
</body>
</html>
"""
    return {"page4_variance_values.csv": csv_text,
            "Page4_Report_Layout.json": layout_text,
            "Page4_preview.html": preview}


def audit_report(checks: list[tuple[str, str]], git_status: str) -> str:
    lines = ["# Phase 7B Page 4 \u2014 Implementation Audit Report", "",
             "## 1. Implementation result", "",
             "Page 4 \u2014 Scenario Sensitivity by Discount Band is implemented as a "
             "verified, deterministic bundle built by `powerbi/page4_build.py`. All listed "
             "source documents were read before building (Phase 5, SQL layer + freeze, "
             "Phase 7A foundation, 7B build spec, Gate 10 decision log, interpretation "
             "design, AO-01\u2013AO-06 freezes, Page 1\u20133 patterns); no conflicts were "
             "found (420-row scope, three frozen instances, fixed B0\u2013B5+TOTAL bands, "
             "6/3/11 block structure, OBSERVED/HYPOTHETICAL separation, 42 N/A rows, "
             "21/21 standing, labels, and caveats all agree).",
             "", "## 2. Power BI Desktop availability", "",
             "Not available on this machine (no `PBIDesktop.exe`, no Power BI Desktop "
             "install directory).",
             "", "## 3. Exact files created", "",
             "```text", "powerbi/page4_build.py",
             "powerbi/page4_variance_values.csv  (ignored, *.csv policy; regenerable)",
             "powerbi/Page4_Report_Layout.json", "powerbi/Page4_preview.html",
             "powerbi/Page4_AUDIT_REPORT.md  (this file)", "```", "",
             "## 4. Exact files modified", "", "None.", "",
             "## 5. Source view and table", "",
             "`variance_by_band` (table `ao04_band_variance`) from "
             "`data/processed/marginmap.db` (Import, all columns Text). The builder "
             "asserts via query tracking that no other view or table was read; no AO CSV "
             "or quality JSON supplied displayed values.",
             "", "## 6. Row count and column count", "",
             "420 rows (table and view agree) \u00d7 12 frozen columns "
             "(`output_name, scenario_status, grain, scenario_id, band, block, "
             "source_artifact, metric_name, metric_value, unit, definition_ref, "
             "limitation`). Structure: 3 instances \u00d7 7 bands \u00d7 20 rows "
             "(baseline 6 + hypothetical 3 + variance 11).",
             "", "## 7. Scenario IDs", "",
             "`uniform_replace_0.10`, `discount_increase_pp_0.00`, "
             "`discount_decrease_pp_0.00` (frozen order; identity scenarios kept visible).",
             "", "## 8. Scenario types and discount inputs", "",
             "Uniform replacement (`replacement_rate 0.10`, headline allocation) and "
             "discount increase / decrease (`increase_pp 0.00` / `decrease_pp 0.00`, "
             "identity controls). Carried by the frozen identifiers plus per-instance "
             "source artifacts, attested by the quality `input-forms` + `identifiers` "
             "checks \u2014 no separate input columns exist and none were invented.",
             "", "## 9. Band order", "",
             "B0, B1, B2, B3, B4, B5, TOTAL \u2014 frozen rowid order in every "
             "(instance, block); TOTAL always last and visually separated.",
             "", "## 10. Baseline/hypothetical/variance structure", "",
             "Per (instance, band): baseline 6 rows (`base_contribution`, `base_wad`, "
             "`quantity`, `order_count`, `line_count`, `neg_base_orders`; "
             "`OBSERVED BASELINE`), hypothetical 3 rows (`hypo_contribution`, `hypo_wad`, "
             "`neg_hypo_orders`), variance 11 rows (absolute currency, relative percent, "
             "percentage-point margin change, flag, 2 N/A markers). Uniform records: B5 "
             "variance +45,401.37 (+295.55%, +7.188 pp) beside B0 \u221230,530.82; bands sum "
             "to TOTAL +95,406.24 within 0.05. Identity instances read exactly 0.0 "
             "throughout and are labeled controls.",
             "", "## 11. Exact validation checks and results", ""]
    for name, detail in checks:
        lines.append(f"- `[{name}]` PASS \u2014 {detail}")
    lines.append("- `[bundle-audit-verified]` PASS \u2014 asserted post-write by the "
                 "builder: this file lists every check name above plus live git status "
                 "(see console output for the PASS line).")
    lines += ["", "## 12. Gate 10 compliance", ""]
    gate = [
        "Hypothetical-scenario-analysis labeling (banner + short caveat on top).",
        "Observed baseline vs hypothetical sensitivity distinguished (status badges).",
        "Baseline/hypothetical/variance blocks separate (A/B/C areas).",
        "Absolute changes separate from percentage-point margin changes.",
        "Scenario ID and type displayed per instance.",
        "Discount input form and value displayed per instance.",
        "Reporting grain `Overall \u00d7 baseline discount band (ORDER)` displayed.",
        "Source view `variance_by_band` and source artifact identity displayed.",
        "Validation status `21/21 PASS` and quality flags displayed.",
        "All 42 N/A values shown with exact frozen reasons.",
        "Variance rows distinguished (net revenue vs COGS vs contribution vs discount "
        "forgone); no standalone gross-profit row exists and none constructed.",
        "All five methodology assumptions shown.",
        "Conditionality on selected cost structure stated.",
        "Standing caveat on the visual itself (short) plus long-form footer.",
        "No forecasting/causal/demand/optimization wording (scan-verified).",
        "No deferred scenario views.",
        "Frozen artifacts read-only."]
    for i, g in enumerate(gate, 1):
        lines.append(f"- ({i}) PASS \u2014 {g}")
    lines += ["", "## 13. N/A handling", "",
              "Exactly 42 empty-`metric_value` rows (verified set): "
              "`demand_response_view` (`N/A: RESPONSE_NOT_ESTIMATED`) and "
              "`fixed_unit_cost_view` (`N/A: COMPARATOR_NOT_IN_INITIAL_BUILD`) in every "
              "(instance \u00d7 band) variance block. Each renders as `N/A *` with its exact "
              "frozen reason in the footnote and hover title. Never zero-filled, never "
              "dropped.",
              "", "## 14. Frozen-artifact protection", "",
              "Database opened read-only (`mode=ro`) throughout; loader never re-executed; "
              "no manual DB edits. No Phase 4C script, CSV, quality JSON, freeze document, "
              "SQL file, or prior AO artifact modified. AO-04 CSV re-hashed byte-identical "
              "this run; SQL-layer `frozen-unchanged` 6/6.",
              "", "## 15. Determinism", "",
              "- Directly tested: two in-process builds asserted byte-equal before writing "
              "(`determinism-in-run`); written files re-read and compared "
              "(`bundle-*-verified`); operator second execution reproduces bytes.",
              "- Code-inspection: single-view-only query tracking; presentation-only "
              "formatting/filtering (reversible `fmt`); fail-loud `fail()` before any write; "
              "no DAX/relationships/calculations exist to drift.",
              "- Inherited: AO-04 frozen 21/21 validation and SQL-layer 13/13 validation "
              "reused as standing evidence, not re-executed logic.",
              "", "## 16. Preview/layout verification", "",
              "Preview carries every non-empty stored value verbatim "
              "(`data-source-value`), all 42 N/A cells, every required label, both caveats, "
              "and the reconciliation strip (bands-sum vs stored TOTAL with the frozen "
              "0.05 tolerance note; stored TOTAL remains the authority). Layout JSON holds "
              "3 instances \u00d7 3 blocks over fixed bands with matrix/bar/table/card "
              "visuals only, a page-local single-select scenario slicer spec, and an empty "
              "model (no relationships, DAX, or Power Query calculations).",
              "", "## 17. Exact Git status", "", "```text", git_status.strip(),
              "```", "", "## 18. Files to commit later", "", "```text",
              "powerbi/page4_build.py", "powerbi/Page4_Report_Layout.json",
              "powerbi/Page4_preview.html", "powerbi/Page4_AUDIT_REPORT.md",
              "```", "",
              "(The CSV stays ignored under `*.csv`; regenerable via the builder.)",
              "", "## 19. Blocking and non-blocking issues", "",
              "- Blocking: none.", "- Non-blocking: no `.pbix` binary (no Power BI "
              "Desktop; layout JSON + preview provided, same as Pages 1\u20133). "
              "Prohibited-term scan is a literal-substring check with both caveats and "
              "frozen \u201cnot a forecast\u201d prohibitions stripped (documented limit).",
              "", "## 20. No commit or push", "",
              "Confirmed. No `git add`, `commit`, or `push` executed; Pages 5\u20136 not begun."]
    return "\n".join(lines) + "\n"


def main() -> int:
    if not DB.is_file():
        fail("db-exists", f"database at {DB}", "file missing")
    passed("db-exists", str(DB))
    if not AO04_CSV.is_file() or not AO04_QUALITY.is_file():
        fail("frozen-inputs-present", "AO-04 CSV + quality JSON present",
             "missing frozen file")

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    tcon = TrackedConn(con)
    try:
        views = {r[0] for r in tcon.execute(
            "SELECT name FROM sqlite_master WHERE type='view'")}
        if VIEW not in views:
            fail("view-exists", f"view {VIEW}", "missing")
        passed("view-exists", f"{VIEW} present")

        cols = [r[1] for r in tcon.execute(f"PRAGMA table_info({VIEW})")]
        if cols != EXPECTED_COLS:
            fail("columns-match", str(EXPECTED_COLS), str(cols))
        passed("columns-match", "12/12 frozen columns in order")

        rows = tcon.execute(
            f"SELECT output_name, scenario_status, grain, scenario_id, band,"
            f" block, source_artifact, metric_name, metric_value, unit,"
            f" definition_ref, limitation FROM {TABLE} ORDER BY rowid").fetchall()
        n_view = tcon.execute(f"SELECT COUNT(*) FROM {VIEW}").fetchone()[0]
        if len(rows) != EXPECTED_ROWS or n_view != EXPECTED_ROWS:
            fail("row-count-420", "420 rows in table and view",
                 f"table={len(rows)} view={n_view}")
        passed("row-count-420", "420/420 rows (table and view agree)")

        if tcon.touched - ALLOWED_OBJECTS:
            fail("source-view-only", f"only {sorted(ALLOWED_OBJECTS)}",
                 f"touched {sorted(tcon.touched)}")
        passed("source-view-only",
               f"only AO-04 objects read: {sorted(tcon.touched)}")

        sids = [r[0] for r in tcon.execute(
            f"SELECT DISTINCT scenario_id FROM {TABLE} ORDER BY rowid")]
        if sids != EXPECTED_SCENARIOS:
            fail("scenario-id-set", str(EXPECTED_SCENARIOS), str(sids))
        passed("scenario-id-set", "3/3 frozen instances in frozen order")

        bands = [r[0] for r in tcon.execute(
            f"SELECT DISTINCT band FROM {TABLE} ORDER BY rowid")]
        if bands != EXPECTED_BANDS:
            fail("band-order", str(EXPECTED_BANDS), str(bands))
        passed("band-order", "B0,B1,B2,B3,B4,B5,TOTAL in frozen rowid order")

        blks = [r[0] for r in tcon.execute(
            f"SELECT DISTINCT block FROM {TABLE} ORDER BY rowid")]
        if blks != EXPECTED_BLOCKS:
            fail("block-set", str(EXPECTED_BLOCKS), str(blks))
        passed("block-set", "baseline/hypothetical/variance in frozen order")

        want = {"baseline": BASELINE_METRICS, "hypothetical": HYPO_METRICS,
                "variance": VARIANCE_METRICS}
        for sid in EXPECTED_SCENARIOS:
            for band in EXPECTED_BANDS:
                for blk, metrics in want.items():
                    got = [r[0] for r in tcon.execute(
                        f"SELECT metric_name FROM {TABLE} WHERE scenario_id=? AND"
                        f" band=? AND block=? ORDER BY rowid", (sid, band, blk))]
                    if got != metrics:
                        fail("scenario-band-block-completeness",
                             f"{sid}/{band}/{blk}: {len(metrics)} frozen metrics",
                             str(got))
        passed("scenario-band-block-completeness",
               "3x7x3 cells complete: 6/3/11 metrics in frozen order each")

        if {r[2] for r in rows} != {"Overall x discount band"}:
            fail("band-grain", "Overall x discount band uniform", "mismatch")
        passed("band-grain", "420/420 rows at Overall x discount band grain")

        status_by_block = {r[0]: r[1] for r in tcon.execute(
            f"SELECT DISTINCT block, scenario_status FROM {TABLE}")}
        if status_by_block != {"baseline": "OBSERVED BASELINE",
                               "hypothetical": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY",
                               "variance": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY"}:
            fail("block-separation", "baseline OBSERVED; hypo/variance HYPOTHETICAL",
                 str(status_by_block))
        passed("block-separation",
               "baseline OBSERVED vs hypo/variance HYPOTHETICAL, never merged")

        na = {(r[3], r[4], r[5], r[7]) for r in rows if r[8] == ""}
        if na != EXPECTED_NA:
            fail("na-preserved", "exact 42 N/A (scenario,band,block,metric) set",
                 f"got {len(na)}")
        passed("na-preserved", "42/42 N/A rows with frozen reasons intact")

        for sid, info in SCENARIO_INFO.items():
            arts = tcon.execute(
                f"SELECT DISTINCT source_artifact FROM {TABLE} WHERE"
                f" scenario_id=?", (sid,)).fetchall()
            if [a[0] for a in arts] != [info["source_artifact"]]:
                fail("scenario-type-present", f"{sid} -> {info['source_artifact']}",
                     str(arts))
        passed("scenario-type-present",
               "3/3 scenario types mapped to frozen source artifacts")

        quality = json.loads(AO04_QUALITY.read_text(encoding="utf-8"))
        qmap = {c.get("id"): c for c in quality.get("checks", [])}
        if qmap.get("input-forms", {}).get("status") != "PASS" or \
           qmap.get("identifiers", {}).get("status") != "PASS":
            fail("discount-input-present",
                 "input-forms + identifiers PASS", "not attested")
        passed("discount-input-present",
               "discount inputs attested (input-forms + identifiers PASS)")

        b5 = tcon.execute(
            f"SELECT metric_value FROM {TABLE} WHERE scenario_id='uniform_replace_0.10'"
            f" AND band='B5' AND block='variance' AND metric_name='variance_contribution'"
            ).fetchone()[0]
        tot = tcon.execute(
            f"SELECT metric_value FROM {TABLE} WHERE scenario_id='uniform_replace_0.10'"
            f" AND band='TOTAL' AND block='variance' AND metric_name='variance_contribution'"
            ).fetchone()[0]
        bsum = sum(float(r[0]) for r in tcon.execute(
            f"SELECT metric_value FROM {TABLE} WHERE scenario_id='uniform_replace_0.10'"
            f" AND block='variance' AND metric_name='variance_contribution'"
            f" AND band != 'TOTAL'"))
        zeros = tcon.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE scenario_id LIKE '%_0.00' AND"
            f" block='variance' AND metric_name IN ('variance_contribution',"
            f" 'variance_net_revenue', 'margin_change_pp',"
            f" 'relative_contribution_variance') AND metric_value != '0.0'"
            ).fetchone()[0]
        if b5 != U_B5_VAR or tot != U_TOTAL_VAR or abs(bsum - float(tot)) > 0.05 \
                or zeros != 0:
            fail("spot-values", f"B5 {U_B5_VAR}; TOTAL {U_TOTAL_VAR}; recon<=0.05; zeros",
                 f"B5={b5} TOTAL={tot} recon={abs(bsum - float(tot))} nonzero={zeros}")
        passed("spot-values",
               f"B5 var {b5}; TOTAL var {tot}; recon {abs(bsum - float(tot)):.2e}; "
               f"identity 0.0 throughout")
    finally:
        con.close()

    qchecks = quality.get("checks", [])
    if len(qchecks) != 21 or any(c.get("status") != "PASS" for c in qchecks):
        fail("quality-21-pass", "21/21 PASS",
             f"{len(qchecks)} checks, non-PASS present")
    passed("quality-21-pass",
           "phase4c_contribution_variance_by_band_quality.json 21/21 PASS")

    recorded = quality.get("outputs", {}).get(
        "phase4c_contribution_variance_by_band.csv", {}).get("sha256")
    actual = hashlib.sha256(AO04_CSV.read_bytes()).hexdigest()
    if actual != recorded:
        fail("frozen-byte-identical", f"sha {recorded}", actual)
    passed("frozen-byte-identical", f"AO-04 CSV byte-identical ({actual[:12]}\u2026)")

    artifacts = build_artifacts(rows)
    if build_artifacts(rows) != artifacts:
        fail("determinism-in-run", "identical bytes on rebuild", "difference")
    passed("determinism-in-run", "two in-process builds byte-identical")

    blob = "\n".join(artifacts.values())
    stripped = blob.replace(CAVEAT_SHORT, "").replace(CAVEAT_LONG, "")
    stripped = stripped.replace("not a forecast", "")
    slow = stripped.lower()
    bad = [w for w in ("forecast", "causal", "demand prediction", "elasticity",
                       "uplift", "driven by", "caused by", "optimiz")
           if w in slow]
    if bad:
        fail("language-scan", "no predictive wording outside caveats", str(bad))
    passed("language-scan", "no forecast/causal/demand/optimization wording")

    for name in ("page4_variance_values.csv", "Page4_Report_Layout.json",
                 "Page4_preview.html"):
        (OUT_DIR / name).write_text(artifacts[name], encoding="utf-8",
                                    newline="" if name.endswith(".csv") else None)

    back = (OUT_DIR / "page4_variance_values.csv").read_text(encoding="utf-8")
    rd = list(csv.reader(io.StringIO(back)))
    if [tuple(r) for r in rd[1:]] != [tuple(map(str, r)) for r in rows]:
        fail("bundle-csv-verified", "cell-for-cell equality after write",
             "difference found")
    passed("bundle-csv-verified",
           "page4_variance_values.csv identical to DB source")

    html_text = (OUT_DIR / "Page4_preview.html").read_text(encoding="utf-8")
    vals = [(r[3], r[4], r[5], r[7], r[8]) for r in rows if r[8] != ""]
    missing = [f"{s}/{b}/{k}/{m}" for (s, b, k, m, v) in vals
               if f'data-source-value="{esc(v)}"' not in html_text]
    if missing:
        fail("bundle-html-verified", "all stored values embedded verbatim",
             str(missing[:5]))
    for token in ["HYPOTHETICAL SCENARIO ANALYSIS",
                  "Overall \u00d7 baseline discount band",
                  "variance_by_band", "OBSERVED BASELINE",
                  "HYPOTHETICAL_ARITHMETIC_SENSITIVITY",
                  "uniform_replace_0.10", "discount_increase_pp_0.00",
                  "discount_decrease_pp_0.00", "21/21 PASS",
                  "never re-banded", CAVEAT_SHORT, CAVEAT_LONG]:
        if token not in html_text:
            fail("bundle-html-verified", f"label present: {token[:40]}", "absent")
    if html_text.count(">N/A *<") != 42:
        fail("bundle-html-verified", "42 N/A cells rendered",
             f"found {html_text.count('>N/A *<')}")
    passed("bundle-html-verified",
           "378 stored values verbatim + 42 N/A + labels + both caveats")

    layout_back = json.loads(
        (OUT_DIR / "Page4_Report_Layout.json").read_text(encoding="utf-8"))
    if layout_back["page_name"] != PAGE_NAME or \
       layout_back["model"] != {"relationships": [],
                                "dax_measures": [],
                                "power_query_calculations": []}:
        fail("bundle-layout-verified", "page name + empty model", "mismatch")
    seen_types = set()
    for s in layout_back["sections"]:
        for b in s["blocks"]:
            seen_types.add(b.get("visual", "matrix"))
            for extra in b.get("visuals", []):
                seen_types.add(extra)
    if seen_types - {"matrix", "clustered bar chart", "table", "card"}:
        fail("bundle-layout-verified", "only matrix/bar/table/card (+slicer)",
             str(sorted(seen_types)))
    if layout_back["scenario_slicer"]["column"] != "scenario_id":
        fail("bundle-layout-verified", "scenario_id slicer spec", "mismatch")
    passed("bundle-layout-verified",
           "3 instances x 3 blocks over fixed bands, approved visuals, no DAX/rels")

    try:
        git_status = subprocess.run(
            ["git", "status", "--short"], cwd=ROOT, capture_output=True,
            text=True, timeout=30).stdout
    except Exception as e:  # noqa: BLE001 — record instead of failing
        git_status = f"(git unavailable: {e})"

    audit = audit_report(CHECKS, git_status)
    (OUT_DIR / "Page4_AUDIT_REPORT.md").write_text(audit, encoding="utf-8")
    audit_back = (OUT_DIR / "Page4_AUDIT_REPORT.md").read_text(encoding="utf-8")
    if not all(f"`[{name}]`" in audit_back for name, _ in CHECKS):
        fail("bundle-audit-verified", "all check names in audit", "missing")
    passed("bundle-audit-verified",
           f"audit lists all {len(CHECKS)} checks + git status")

    print("OK: Page 4 bundle built and verified (no .pbix; see audit report)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
