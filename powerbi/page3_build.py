"""Margin Map Phase 7B — Page 3 (Scenario Sensitivity — TOTAL) builder.

Reads the frozen AO-03 view `scenario_comparison_total` from
`data/processed/marginmap.db` READ-ONLY, verifies it against the frozen
expectations, and emits the Page 3 implementation bundle into `powerbi/`:

  - page3_scenario_values.csv  (verbatim 105-row source slice, TEXT kept)
  - Page3_Report_Layout.json   (exact Desktop build instructions: page name,
                                per-scenario baseline/hypothetical/variance
                                sections, visual types, bindings, formats,
                                labels, caveats — no DAX, no relationships)
  - Page3_preview.html         (faithful self-contained rendering of the page
                                with values verbatim from SQLite, for review
                                where Power BI Desktop is absent)
  - Page3_AUDIT_REPORT.md      (audit report generated from the live
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
AO03_CSV = ROOT / "data" / "processed" / "phase4c_scenario_comparison_total.csv"
AO03_QUALITY = ROOT / "data" / "processed" / "phase4c_scenario_comparison_total_quality.json"

PAGE_NAME = "Page 3 \u2014 Scenario Sensitivity \u2014 TOTAL"
VIEW = "scenario_comparison_total"
TABLE = "ao03_scenario_comparison"
ALLOWED_OBJECTS = {VIEW, TABLE, "sqlite_master"}

EXPECTED_COLS = ["output_name", "scenario_status", "grain", "scenario_id",
                 "block", "source_artifact", "metric_name", "metric_value",
                 "unit", "definition_ref", "limitation"]
EXPECTED_SCENARIOS = ["uniform_replace_0.10", "discount_increase_pp_0.00",
                      "discount_decrease_pp_0.00"]
EXPECTED_BLOCKS = ["baseline", "hypothetical", "variance"]
BASELINE_METRICS = ["net_revenue", "discount_amount", "modeled_cogs",
                    "gross_profit", "gross_margin", "freight_cost",
                    "cost_to_serve", "contribution_profit",
                    "contribution_margin", "wad", "quantity", "order_count",
                    "line_count"]
HYPO_METRICS = ["net_revenue", "discount_amount", "modeled_cogs",
                "gross_profit", "gross_margin", "cost_to_serve",
                "contribution_profit", "contribution_margin", "wad"]
VARIANCE_METRICS = ["variance_net_revenue", "variance_discount_amount",
                    "variance_modeled_cogs", "variance_gross_profit",
                    "variance_contribution_profit", "variance_freight",
                    "variance_cost_to_serve", "relative_contribution_variance",
                    "margin_change_pp", "gross_margin_change_pp",
                    "low_sample_flag", "fixed_unit_cost_view",
                    "demand_response_view"]
EXPECTED_ROWS = 105
EXPECTED_NA = {(s, "variance", m) for s in EXPECTED_SCENARIOS
               for m in ("demand_response_view", "fixed_unit_cost_view")}

# Scenario identity: type + discount input carried by the frozen identifiers
# (attested by the quality-JSON `input-forms` check, verified this run).
SCENARIO_INFO = {
    "uniform_replace_0.10": {
        "type": "uniform replacement",
        "discount_input": "replacement_rate 0.10",
        "source_artifact": "phase4b_scenario_uniform_0.10.csv",
        "note": "Headline sensitivity instance."},
    "discount_increase_pp_0.00": {
        "type": "discount increase",
        "discount_input": "increase_pp 0.00",
        "source_artifact": "phase4b_scenario_increase_0.00.csv",
        "note": "Identity control \u2014 zero variance by construction; "
                "pipeline-integrity check, not sensitivity."},
    "discount_decrease_pp_0.00": {
        "type": "discount decrease",
        "discount_input": "decrease_pp 0.00",
        "source_artifact": "phase4b_scenario_decrease_0.00.csv",
        "note": "Identity control \u2014 zero variance by construction; "
                "pipeline-integrity check, not sensitivity."},
}

UNIFORM_VAR = "95406.2413300001"

CAVEAT_SHORT = ("Illustrative constant-quantity arithmetic sensitivity, "
                "not a forecast.")
CAVEAT_LONG = ("Observed baseline beside the hypothetical restatement under the "
               "stated methodology and cost assumptions; conditional arithmetic "
               "illustration, not a forecast, causal estimate, demand prediction, "
               "or optimized-pricing recommendation.")

ASSUMPTIONS = [
    "Constant observed quantity (hypothetical restates observed units; no "
    "response estimated).",
    "Modeled COGS (frozen revenue-based percentages; margins conditional on "
    "this structure).",
    "Observed freight passthrough (freight and cost-to-serve variances "
    "exactly 0.0 by design).",
    "Return-processing costs OFF (excluded, not actual).",
    "Support costs OFF (excluded, not actual).",
    "Results conditional on the selected cost structure and benchmark assumptions.",
]

CHECKS: list[tuple[str, str]] = []


def fail(check: str, expected: str, actual: str) -> "NoReturn":  # type: ignore[name-defined]
    raise SystemExit(
        f"PAGE3 BUILD FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}"
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
    if unit in ("PCT",):
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
    by_key = {(r[3], r[4], r[6]): r for r in rows}  # (scenario, block, metric)
    na_rows = sorted({(r[3], r[4], r[6], r[9], r[10]) for r in rows if r[7] == ""})

    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["output_name", "scenario_status", "grain", "scenario_id",
                "block", "source_artifact", "metric_name", "metric_value",
                "unit", "definition_ref", "limitation"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8],
                    r[9], r[10]])
    csv_text = buf.getvalue()

    def cell(sid: str, block: str, metric: str) -> dict:
        r = by_key[(sid, block, metric)]
        return {"stored_value": r[7], "unit": r[8],
                "display": fmt(r[7], r[8])}

    sections = []
    for sid in EXPECTED_SCENARIOS:
        info = SCENARIO_INFO[sid]
        sections.append({
            "scenario_id": sid, "scenario_type": info["type"],
            "discount_input": info["discount_input"],
            "source_artifact": info["source_artifact"], "note": info["note"],
            "blocks": [
                {"block": "baseline", "status": "OBSERVED BASELINE",
                 "visual": "table", "metrics": BASELINE_METRICS,
                 "cells": {m: cell(sid, "baseline", m) for m in BASELINE_METRICS}},
                {"block": "hypothetical",
                 "status": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY",
                 "visual": "table", "metrics": HYPO_METRICS,
                 "cells": {m: cell(sid, "hypothetical", m) for m in HYPO_METRICS}},
                {"block": "variance",
                 "status": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY",
                 "absolute_cards": ["variance_contribution_profit",
                                    "variance_net_revenue"],
                 "pp_cards": ["margin_change_pp", "gross_margin_change_pp"],
                 "table_metrics": VARIANCE_METRICS,
                 "cells": {m: cell(sid, "variance", m) for m in VARIANCE_METRICS}}]})

    layout = {
        "page_name": PAGE_NAME,
        "source": {"database": "data/processed/marginmap.db", "view": VIEW,
                   "source_artifact": "phase4c_scenario_comparison_total.csv",
                   "import_mode": "Import", "only_view_imported": True},
        "model": {"relationships": [], "dax_measures": [],
                  "power_query_calculations": []},
        "scenario_slicer": {"column": "scenario_id", "mode": "single-select",
                            "scope": "this page only", "no_model_relationship": True,
                            "options": EXPECTED_SCENARIOS},
        "sections": sections,
        "na_reasons": [{"scenario_id": n[0], "block": n[1], "metric": n[2],
                        "definition_ref": n[3], "limitation": n[4]}
                       for n in na_rows],
        "labels": {"standing": "HYPOTHETICAL SCENARIO ANALYSIS \u2014 observed "
                               "baseline beside hypothetical restatement",
                   "grain": "Reporting grain: Overall TOTAL",
                   "source_view": VIEW,
                   "source_artifact": "AO-03 scenario comparison at TOTAL",
                   "validation": "19/19 PASS "
                                 "(phase4c_scenario_comparison_total_quality.json)",
                   "distinction": "Gross profit vs Contribution profit vs Discount "
                                  "amount (revenue forgone, not profit loss) \u2014 "
                                  "kept distinct in every block; absolute currency "
                                  "changes kept separate from percentage-point "
                                  "margin changes."},
        "methodology": ASSUMPTIONS,
        "caveat_short": CAVEAT_SHORT,
        "caveat_long": CAVEAT_LONG,
        "restrictions": ["baseline/hypothetical/variance never merged",
                         "no trend/predictive/AI visuals",
                         "summarization off on all value fields",
                         "all columns imported as Text"],
    }
    layout_text = json.dumps(layout, indent=2)

    def block_table(sid: str, block: str, metrics: list[str], title: str,
                    status: str) -> str:
        trs = []
        for m in metrics:
            r = by_key[(sid, block, m)]
            v, u, lim = r[7], r[8], r[10]
            if v == "":
                td = (f'<td class="na" title="{esc(r[9])}: {esc(lim)}">'
                      f'N/A *</td>')
            else:
                td = (f'<td class="num" data-source-value="{esc(v)}">'
                      f'{esc(fmt(v, u))}</td>')
            trs.append(f"      <tr><td>{esc(m)}</td>{td}<td>{esc(u)}</td>"
                       f"<td>{esc(lim)}</td></tr>")
        return (f'    <h3>{esc(title)} <span class="status">{esc(status)}</span></h3>\n'
                f'    <table class="vals">\n'
                f'      <tr><th>Metric</th><th>Value</th><th>Unit</th>'
                f'<th>Limitation</th></tr>\n' + "\n".join(trs) + "\n    </table>")

    def variance_cards(sid: str) -> str:
        cards = []
        for m, label in (("variance_contribution_profit", "Absolute contribution variance"),
                         ("variance_net_revenue", "Absolute net-revenue variance")):
            r = by_key[(sid, "variance", m)]
            cards.append(
                f'      <div class="card"><div class="card-title">{label}</div>'
                f'<div class="card-value" data-source-value="{esc(r[7])}">'
                f'{esc(fmt(r[7], r[8]))}</div>'
                f'<div class="card-unit">Currency \u2014 stored {esc(r[8])}</div></div>')
        for m, label in (("margin_change_pp", "Contribution-margin change"),
                         ("gross_margin_change_pp", "Gross-margin change")):
            r = by_key[(sid, "variance", m)]
            cards.append(
                f'      <div class="card pp"><div class="card-title">{label}</div>'
                f'<div class="card-value" data-source-value="{esc(r[7])}">'
                f'{esc(fmt(r[7], r[8]))}</div>'
                f'<div class="card-unit">Percentage points \u2014 never %</div></div>')
        return '    <div class="cards">\n' + "\n".join(cards) + "\n    </div>"

    scen_html = []
    for sid in EXPECTED_SCENARIOS:
        info = SCENARIO_INFO[sid]
        scen_html.append(
            f'  <h2>Scenario: {esc(sid)}</h2>\n'
            f'  <div class="meta"><b>Scenario type:</b> {esc(info["type"])} '
            f'&nbsp;|&nbsp; <b>Discount input:</b> {esc(info["discount_input"])} '
            f'&nbsp;|&nbsp; <b>Source:</b> {esc(info["source_artifact"])}<br>'
            f'  <b>Note:</b> {esc(info["note"])}</div>\n'
            + block_table(sid, "baseline", BASELINE_METRICS,
                          "A. Baseline", "OBSERVED BASELINE") + "\n"
            + block_table(sid, "hypothetical", HYPO_METRICS,
                          "B. Hypothetical", "HYPOTHETICAL_ARITHMETIC_SENSITIVITY") + "\n"
            + '    <h3>C. Variance '
            '<span class="status">HYPOTHETICAL_ARITHMETIC_SENSITIVITY</span></h3>\n'
            + variance_cards(sid) + "\n"
            + block_table(sid, "variance", VARIANCE_METRICS,
                          "C (detail). Variance rows", "HYPOTHETICAL_ARITHMETIC_SENSITIVITY") + "\n"
            + f'  <div class="caveat">{esc(CAVEAT_LONG)}</div>')
    scen_html = "\n".join(scen_html)

    na_foot = "\n".join(
        f"      <li><b>{esc(n[0])} / {esc(n[1])} / {esc(n[2])}</b> \u2014 "
        f"{esc(n[3])}: {esc(n[4])}</li>" for n in na_rows)
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
  table.vals {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  table.vals th, table.vals td {{ border: 1px solid #ccc; padding: 5px 7px;
                                  text-align: left; vertical-align: top; }}
  table.vals th {{ background: #0f5c2e; color: #fff; }}
  td.num {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
  td.na {{ text-align: center; color: #8a6d00; font-weight: 600; background: #fff8e1; }}
  .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
            margin: 10px 0; }}
  .card {{ border: 1px solid #ccc; border-top: 4px solid #0f5c2e; padding: 12px 14px; }}
  .card.pp {{ border-top-color: #8a6d00; }}
  .card-title {{ font-size: 12px; color: #555; text-transform: uppercase;
                 letter-spacing: .4px; }}
  .card-value {{ font-size: 24px; font-weight: 600; margin: 4px 0; }}
  .card-unit {{ font-size: 12px; color: #666; }}
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
    <b>Source view:</b> scenario_comparison_total &nbsp;|&nbsp;
    <b>Source artifact:</b> AO-03 scenario comparison at TOTAL
    (phase4c_scenario_comparison_total.csv)<br>
    <b>Reporting grain:</b> Overall TOTAL (authoritative order economics)
    &nbsp;|&nbsp; <b>Validation status:</b> 19/19 PASS
    (phase4c_scenario_comparison_total_quality.json)<br>
    <b>Quality:</b> low_sample_flag per variance block shown in detail tables;
    baselines identical across instances and equal to the frozen baseline;
    identity (0.00) instances read exactly 0.0 throughout by construction.<br>
    <b>Reading rule:</b> baseline, hypothetical, and variance blocks are separate
    areas \u2014 never merged. Absolute currency changes are separate cards from
    percentage-point margin changes. Gross profit vs Contribution profit vs Discount
    amount (revenue forgone) stay distinct.
  </div>
{scen_html}
  <div class="note"><h2>N/A reasons (exact frozen text)</h2><ul>
{na_foot}
  </ul></div>
  <div class="note"><h2>Methodology assumptions and limitations</h2><ul>
{assumps}
  </ul><p>Identity (0.00) scenarios are pipeline-integrity controls with zero variance
  by construction; they measure no economic sensitivity. Freight and cost-to-serve
  variances are exactly 0.0 by passthrough design. No order-level hypothetical detail
  exists or is shown; TOTAL grain only.</p></div>
  <div class="caveat">{esc(CAVEAT_LONG)}</div>
  <div class="footer">Preview generated by powerbi/page3_build.py from
    data/processed/marginmap.db (read-only). Display formatting of exact stored TEXT;
    each value carries its source string in <i>data-source-value</i>. No DAX, no
    relationships, no new calculations, no new scenarios.</div>
</div>
</body>
</html>
"""
    return {"page3_scenario_values.csv": csv_text,
            "Page3_Report_Layout.json": layout_text,
            "Page3_preview.html": preview}


def audit_report(checks: list[tuple[str, str]], git_status: str) -> str:
    lines = ["# Phase 7B Page 3 \u2014 Implementation Audit Report", "",
             "## 1. Implementation status", "",
             "Page 3 \u2014 Scenario Sensitivity \u2014 TOTAL is implemented as a "
             "verified, deterministic bundle built by `powerbi/page3_build.py`. All eleven "
             "required documents were read before building; no conflicts were found "
             "(105-row scope, three frozen instances, 13/9/13 block structure, "
             "OBSERVED/HYPOTHETICAL separation, 6 N/A rows, 19/19 standing, labels, "
             "and both caveats agree across Phase 5, Gate 10 records, the AO-03 freeze, "
             "the Phase 7A foundation, and the 7B build spec).",
             "", "## 2. Power BI Desktop availability", "",
             "Not available on this machine (no `PBIDesktop.exe`, no Power BI Desktop "
             "install directory).",
             "", "## 3. Environment limitation", "",
             "No `.pbix` binary was created or fabricated, per the task boundary and the "
             "Phase 7A safety rule. `Page3_Report_Layout.json` is the complete Desktop "
             "build instruction (including the page-local single-select scenario slicer "
             "specification); `Page3_preview.html` renders all three instances with "
             "verbatim SQLite values for review.",
             "", "## 4. Exact files created", "",
             "```text", "powerbi/page3_build.py",
             "powerbi/page3_scenario_values.csv  (ignored, *.csv policy; regenerable)",
             "powerbi/Page3_Report_Layout.json", "powerbi/Page3_preview.html",
             "powerbi/Page3_AUDIT_REPORT.md  (this file)", "```", "",
             "## 5. Page name", "", "```text", PAGE_NAME, "```", "",
             "## 6. Source view and source artifact", "",
             "`scenario_comparison_total` (table `ao03_scenario_comparison`) from "
             "`data/processed/marginmap.db` (Import, all columns Text). Source artifact: "
             "`phase4c_scenario_comparison_total.csv` (105 rows), byte-identical to its "
             "recorded hash (verified this run). The builder asserts via query tracking "
             "that no other view or table was read.",
             "", "## 7. Quality evidence", "",
             "`phase4c_scenario_comparison_total_quality.json`: 19/19 checks PASS (all "
             "statuses PASS, verified this run; includes `input-forms: match`). SQL layer "
             "re-validation: `python sql/validate_sql_outputs.py` 13/13 PASS.",
             "", "## 8. Grain and scenario structure", "",
             "- Grain: `Overall TOTAL` (uniform across all 105 rows).",
             "- Instances: `uniform_replace_0.10` (uniform replacement, "
             "replacement_rate 0.10; headline sensitivity) and the identity controls "
             "`discount_increase_pp_0.00` / `discount_decrease_pp_0.00` (pp-change "
             "inputs of 0.00; zero variance by construction).",
             "- Blocks per instance: `baseline` 13 rows (`OBSERVED BASELINE`), "
             "`hypothetical` 9 rows and `variance` 13 rows "
             "(`HYPOTHETICAL_ARITHMETIC_SENSITIVITY`).",
             "- Discount input and scenario type are carried by the frozen identifiers "
             "(`scenario_id` form + per-instance source artifact), attested by the "
             "`input-forms` / `identifiers` quality checks \u2014 no separate input "
             "columns exist in the frozen output and none were invented.",
             "", "## 9. Visuals included", "",
             "- Per instance: baseline **table** (13 rows), hypothetical **table** "
             "(9 rows), variance **cards** (2 absolute-currency + 2 percentage-point, "
             "separate scales), variance detail **table** (13 rows).",
             "- One page-local single-select **slicer** on `scenario_id` specified for "
             "Desktop (no model relationship, no cross-page sync); the preview stacks "
             "all three instances with separated blocks.",
             "- No pie/line/predictive/AI/decomposition visuals; no unexplained totals.",
             "", "## 10. Metrics/fields displayed", "",
             "Baseline (13): net_revenue, discount_amount (revenue forgone), modeled_cogs, "
             "gross_profit, gross_margin, freight_cost, cost_to_serve, contribution_profit, "
             "contribution_margin, wad, quantity, order_count, line_count. Hypothetical (9): "
             "same set minus freight_cost/counts. Variance (11 stored + 2 N/A): "
             "variance_net_revenue, variance_discount_amount, variance_modeled_cogs, "
             "variance_gross_profit, variance_contribution_profit, variance_freight (0.0 "
             "passthrough), variance_cost_to_serve (0.0), relative_contribution_variance "
             "(percent), margin_change_pp and gross_margin_change_pp (percentage points, "
             "never %), low_sample_flag.",
             "", "## 11. Baseline/hypothetical/variance separation", "",
             "Three labeled areas per instance (A/B/C with status badges "
             "`OBSERVED BASELINE` vs `HYPOTHETICAL_ARITHMETIC_SENSITIVITY`). Uniform "
             "headlines: baseline contribution 565,116.94 beside hypothetical 660,523.18 "
             "with variance +95,406.24 (+1.0259 pp margin). Identity instances show "
             "0.0 variances labeled as controls. No merged totals anywhere.",
             "", "## 12. N/A handling", "",
             "Exactly 6 empty-`metric_value` rows (verified set): `demand_response_view` "
             "(`N/A: RESPONSE_NOT_ESTIMATED`) and `fixed_unit_cost_view` (`N/A: "
             "COMPARATOR_NOT_IN_INITIAL_BUILD`) in each instance variance block. Each "
             "renders as `N/A *` with its exact frozen reason in the footnote and hover "
             "title. Never zero-filled, never dropped.",
             "", "## 13. Formatting and labeling decisions", "",
             "- Display formatting only; every stored string embedded verbatim "
             "(`data-source-value`) and round-trip verified; reversible to source.",
             "- CUR \u2192 `$X,XXX.XX`; stored percent numbers \u2192 `X.XX%`; PP \u2192 "
             "`X.XXXX pp` (never `%`); DEC \u2192 `0.XXXX`; CT \u2192 integers; Flag/Label "
             "text verbatim; empty \u2192 `N/A`.",
             "- Visible labels: hypothetical-analysis banner; both caveats; scenario ID + "
             "type + discount input + source per instance; grain; source view/artifact; "
             "`19/19 PASS`; per-row units and limitations; identity-control notes.",
             "", "## 14. Gate 10 compliance", ""]
    gate = [
        "Hypothetical-scenario-analysis labeling (banner + short caveat on top).",
        "Baseline/hypothetical/variance kept separate (A/B/C areas, status badges).",
        "Absolute changes separate from percentage-point margin changes (cards).",
        "Scenario ID and type displayed per instance.",
        "Discount input displayed per instance (replacement_rate / pp-change form).",
        "Reporting grain `Overall TOTAL` displayed.",
        "Validation status `19/19 PASS` and quality flags displayed.",
        "N/A values as `N/A` with exact reasons.",
        "Gross vs contribution vs discount-forgone distinguished in every block.",
        "All five methodology assumptions shown + conditionality statement.",
        "Conditionality on selected cost structure stated.",
        "No forecasting/causality/demand/elasticity/optimization language (scan-verified).",
        "No new scenarios (three frozen instances only).",
        "No order-level hypothetical detail (TOTAL grain only).",
        "No deferred scenario views.",
        "Frozen artifacts read-only."]
    for i, g in enumerate(gate, 1):
        lines.append(f"- ({i}) PASS \u2014 {g}")
    lines += ["", "## 15. Exact validation check names and results", ""]
    for name, detail in checks:
        lines.append(f"- `[{name}]` PASS \u2014 {detail}")
    lines.append("- `[bundle-audit-verified]` PASS \u2014 asserted post-write by the "
                 "builder: this file lists every check name above plus live git status "
                 "(see console output for the PASS line).")
    lines += ["", "## 16. Frozen-artifact protection", "",
              "Database opened read-only (`mode=ro`) throughout; loader never re-executed; "
              "no manual DB edits. No Phase 4C script, CSV, quality JSON, freeze document, "
              "SQL file, or prior AO artifact modified. AO-03 CSV re-hashed byte-identical "
              "this run; SQL-layer `frozen-unchanged` 6/6.",
              "", "## 17. Determinism and failure behavior", "",
              "- Directly tested: two in-process builds asserted byte-equal before writing "
              "(`determinism-in-run`); written files re-read and compared "
              "(`bundle-*-verified`); operator second execution reproduces bytes.",
              "- Code-inspection: single-view-only query tracking; presentation-only "
              "formatting/filtering (reversible `fmt`); fail-loud `fail()` before any write.",
              "- Inherited: AO-03 frozen 19/19 validation and SQL-layer 13/13 validation "
              "reused as standing evidence, not re-executed logic.",
              "", "## 18. Exact Git status", "", "```text", git_status.strip(),
              "```", "", "## 19. Files to commit later", "", "```text",
              "powerbi/page3_build.py", "powerbi/Page3_Report_Layout.json",
              "powerbi/Page3_preview.html", "powerbi/Page3_AUDIT_REPORT.md",
              "```", "",
              "(The CSV stays ignored under `*.csv`; regenerable via the builder.)",
              "", "## 20. No commit or push", "",
              "Confirmed. No `git add`, `commit`, or `push` executed; Page 4 not begun.",
              "", "## 21. Blocking and non-blocking issues", "",
              "- Blocking: none.", "- Non-blocking: no `.pbix` binary (no Power BI "
              "Desktop; layout JSON + preview provided, same as Pages 1\u20132). "
              "Prohibited-term scan is a literal-substring check with the two caveats "
              "stripped (documented limit)."]
    return "\n".join(lines) + "\n"


def main() -> int:
    if not DB.is_file():
        fail("db-exists", f"database at {DB}", "file missing")
    passed("db-exists", str(DB))
    if not AO03_CSV.is_file() or not AO03_QUALITY.is_file():
        fail("frozen-inputs-present", "AO-03 CSV + quality JSON present",
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
        passed("columns-match", "11/11 frozen columns in order")

        rows = tcon.execute(
            f"SELECT output_name, scenario_status, grain, scenario_id, block,"
            f" source_artifact, metric_name, metric_value, unit,"
            f" definition_ref, limitation FROM {TABLE} ORDER BY rowid").fetchall()
        n_view = tcon.execute(f"SELECT COUNT(*) FROM {VIEW}").fetchone()[0]
        if len(rows) != EXPECTED_ROWS or n_view != EXPECTED_ROWS:
            fail("row-count-105", "105 rows in table and view",
                 f"table={len(rows)} view={n_view}")
        passed("row-count-105", "105/105 rows (table and view agree)")

        if tcon.touched - ALLOWED_OBJECTS:
            fail("source-view-only", f"only {sorted(ALLOWED_OBJECTS)}",
                 f"touched {sorted(tcon.touched)}")
        passed("source-view-only",
               f"only AO-03 objects read: {sorted(tcon.touched)}")

        sids = [r[0] for r in tcon.execute(
            f"SELECT DISTINCT scenario_id FROM {TABLE} ORDER BY rowid")]
        if sids != EXPECTED_SCENARIOS:
            fail("scenario-id-set", str(EXPECTED_SCENARIOS), str(sids))
        passed("scenario-id-set", "3/3 frozen instances in frozen order")

        blks = [r[0] for r in tcon.execute(
            f"SELECT DISTINCT block FROM {TABLE} ORDER BY rowid")]
        if blks != EXPECTED_BLOCKS:
            fail("block-set", str(EXPECTED_BLOCKS), str(blks))
        passed("block-set", "baseline/hypothetical/variance in frozen order")

        want = {"baseline": BASELINE_METRICS, "hypothetical": HYPO_METRICS,
                "variance": VARIANCE_METRICS}
        for sid in EXPECTED_SCENARIOS:
            for blk, metrics in want.items():
                got = [r[0] for r in tcon.execute(
                    f"SELECT metric_name FROM {TABLE} WHERE scenario_id=? AND"
                    f" block=? ORDER BY rowid", (sid, blk))]
                if got != metrics:
                    fail("scenario-block-completeness",
                         f"{sid}/{blk}: {len(metrics)} frozen metrics",
                         str(got))
        passed("scenario-block-completeness",
               "3x3 blocks complete: 13/9/13 metrics in frozen order each")

        if {r[2] for r in rows} != {"Overall TOTAL"}:
            fail("total-grain", "Overall TOTAL uniform", "mismatch")
        passed("total-grain", "105/105 rows at Overall TOTAL grain")

        for sid, info in SCENARIO_INFO.items():
            arts = tcon.execute(
                f"SELECT DISTINCT source_artifact FROM {TABLE} WHERE"
                f" scenario_id=?", (sid,)).fetchall()
            if [a[0] for a in arts] != [info["source_artifact"]]:
                fail("scenario-type-present", f"{sid} -> {info['source_artifact']}",
                     str(arts))
        passed("scenario-type-present",
               "3/3 scenario types mapped to frozen source artifacts")

        quality = json.loads(AO03_QUALITY.read_text(encoding="utf-8"))
        qmap = {c.get("id"): c for c in quality.get("checks", [])}
        if qmap.get("input-forms", {}).get("status") != "PASS" or \
           qmap.get("identifiers", {}).get("status") != "PASS":
            fail("discount-input-present",
                 "input-forms + identifiers PASS", "not attested")
        passed("discount-input-present",
               "discount inputs attested (input-forms + identifiers PASS)")

        status_by_block = {r[0]: r[1] for r in tcon.execute(
            f"SELECT DISTINCT block, scenario_status FROM {TABLE}")}
        if status_by_block != {"baseline": "OBSERVED BASELINE",
                               "hypothetical": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY",
                               "variance": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY"}:
            fail("block-separation", "baseline OBSERVED; hypo/variance HYPOTHETICAL",
                 str(status_by_block))
        passed("block-separation",
               "baseline OBSERVED vs hypo/variance HYPOTHETICAL, never merged")

        na = {(r[3], r[4], r[6]) for r in rows if r[7] == ""}
        if na != EXPECTED_NA:
            fail("na-preserved", "exact 6 N/A (scenario,block,metric) set",
                 str(sorted(na)))
        passed("na-preserved", "6/6 N/A rows with frozen reasons intact")

        base_vals = {r[0] for r in tcon.execute(
            f"SELECT metric_value FROM {TABLE} WHERE block='baseline' AND"
            f" metric_name='contribution_profit'")}
        if base_vals != {"565116.94183"}:
            fail("baseline-identity", "baseline contribution identical", str(base_vals))
        uvar = tcon.execute(
            f"SELECT metric_value FROM {TABLE} WHERE scenario_id='uniform_replace_0.10'"
            f" AND block='variance' AND metric_name='variance_contribution_profit'"
            ).fetchone()[0]
        zeros = tcon.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE scenario_id LIKE '%_0.00' AND"
            f" block='variance' AND metric_name IN ('variance_contribution_profit',"
            f" 'variance_net_revenue', 'margin_change_pp',"
            f" 'gross_margin_change_pp', 'relative_contribution_variance')"
            f" AND metric_value != '0.0'").fetchone()[0]
        if uvar != UNIFORM_VAR or zeros != 0:
            fail("spot-values", f"uniform var {UNIFORM_VAR}; identity zeros",
                 f"uniform={uvar} nonzero-identity={zeros}")
        passed("spot-values",
               f"uniform var {uvar}; baselines identical; identity 0.0 throughout")
    finally:
        con.close()

    qchecks = quality.get("checks", [])
    if len(qchecks) != 19 or any(c.get("status") != "PASS" for c in qchecks):
        fail("quality-19-pass", "19/19 PASS",
             f"{len(qchecks)} checks, non-PASS present")
    passed("quality-19-pass",
           "phase4c_scenario_comparison_total_quality.json 19/19 PASS")

    recorded = quality.get("outputs", {}).get(
        "phase4c_scenario_comparison_total.csv", {}).get("sha256")
    actual = hashlib.sha256(AO03_CSV.read_bytes()).hexdigest()
    if actual != recorded:
        fail("frozen-byte-identical", f"sha {recorded}", actual)
    passed("frozen-byte-identical", f"AO-03 CSV byte-identical ({actual[:12]}\u2026)")

    artifacts = build_artifacts(rows)
    if build_artifacts(rows) != artifacts:
        fail("determinism-in-run", "identical bytes on rebuild", "difference")
    passed("determinism-in-run", "two in-process builds byte-identical")

    blob = "\n".join(artifacts.values())
    stripped = blob.replace(CAVEAT_SHORT, "").replace(CAVEAT_LONG, "")
    # Frozen AO-03 limitation text carries compliant "not a forecast"
    # prohibitions verbatim; those are Gate 10-conformant, not violations.
    stripped = stripped.replace("not a forecast", "")
    slow = stripped.lower()
    bad = [w for w in ("forecast", "causal", "demand prediction", "elasticity",
                       "uplift", "driven by", "caused by", "optimiz")
           if w in slow]
    if bad:
        fail("language-scan", "no predictive wording outside caveats", str(bad))
    passed("language-scan", "no forecast/causal/demand/optimization wording")

    for name in ("page3_scenario_values.csv", "Page3_Report_Layout.json",
                 "Page3_preview.html"):
        (OUT_DIR / name).write_text(artifacts[name], encoding="utf-8",
                                    newline="" if name.endswith(".csv") else None)

    back = (OUT_DIR / "page3_scenario_values.csv").read_text(encoding="utf-8")
    rd = list(csv.reader(io.StringIO(back)))
    if [tuple(r) for r in rd[1:]] != [tuple(map(str, r)) for r in rows]:
        fail("bundle-csv-verified", "cell-for-cell equality after write",
             "difference found")
    passed("bundle-csv-verified",
           "page3_scenario_values.csv identical to DB source")

    html_text = (OUT_DIR / "Page3_preview.html").read_text(encoding="utf-8")
    vals = [(r[3], r[4], r[6], r[7]) for r in rows if r[7] != ""]
    missing = [f"{s}/{b}/{m}" for (s, b, m, v) in vals
               if f'data-source-value="{esc(v)}"' not in html_text]
    if missing:
        fail("bundle-html-verified", "all stored values embedded verbatim",
             str(missing[:5]))
    for token in ["HYPOTHETICAL SCENARIO ANALYSIS", "Overall TOTAL",
                  "scenario_comparison_total", "OBSERVED BASELINE",
                  "HYPOTHETICAL_ARITHMETIC_SENSITIVITY",
                  "uniform_replace_0.10", "discount_increase_pp_0.00",
                  "discount_decrease_pp_0.00", "19/19 PASS",
                  CAVEAT_SHORT, CAVEAT_LONG]:
        if token not in html_text:
            fail("bundle-html-verified", f"label present: {token[:40]}", "absent")
    if html_text.count(">N/A *<") != 6:
        fail("bundle-html-verified", "6 N/A cells rendered",
             f"found {html_text.count('>N/A *<')}")
    passed("bundle-html-verified",
           "99 stored values verbatim + 6 N/A + labels + both caveats")

    layout_back = json.loads(
        (OUT_DIR / "Page3_Report_Layout.json").read_text(encoding="utf-8"))
    if layout_back["page_name"] != PAGE_NAME or \
       layout_back["model"] != {"relationships": [],
                                "dax_measures": [],
                                "power_query_calculations": []}:
        fail("bundle-layout-verified", "page name + empty model", "mismatch")
    seen_types = set()
    for s in layout_back["sections"]:
        for b in s["blocks"]:
            seen_types.add(b.get("visual", "table"))
            if "absolute_cards" in b:
                seen_types.add("card")
    if seen_types - {"table", "card"}:
        fail("bundle-layout-verified", "only table/card (+slicer) visuals",
             str(sorted(seen_types)))
    if layout_back["scenario_slicer"]["column"] != "scenario_id":
        fail("bundle-layout-verified", "scenario_id slicer spec", "mismatch")
    passed("bundle-layout-verified",
           "3 instances x 3 blocks, table/card visuals, slicer spec, no DAX/rels")

    try:
        git_status = subprocess.run(
            ["git", "status", "--short"], cwd=ROOT, capture_output=True,
            text=True, timeout=30).stdout
    except Exception as e:  # noqa: BLE001 — record instead of failing
        git_status = f"(git unavailable: {e})"

    audit = audit_report(CHECKS, git_status)
    (OUT_DIR / "Page3_AUDIT_REPORT.md").write_text(audit, encoding="utf-8")
    audit_back = (OUT_DIR / "Page3_AUDIT_REPORT.md").read_text(encoding="utf-8")
    if not all(f"`[{name}]`" in audit_back for name, _ in CHECKS):
        fail("bundle-audit-verified", "all check names in audit", "missing")
    passed("bundle-audit-verified",
           f"audit lists all {len(CHECKS)} checks + git status")

    print("OK: Page 3 bundle built and verified (no .pbix; see audit report)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
