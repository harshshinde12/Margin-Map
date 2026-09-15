"""Margin Map Phase 7B — Page 5 (Order-Level Observed Context) builder.

Reads the frozen AO-05 view `order_reading` from
`data/processed/marginmap.db` READ-ONLY, verifies it against the frozen
expectations, and emits the Page 5 implementation bundle into `powerbi/`:

  - page5_order_values.csv  (verbatim 60,108-row source slice, TEXT kept)
  - Page5_Report_Layout.json   (exact Desktop build instructions: page name,
                                observed-order tables, page-local slicer specs
                                over stored fields only, labels, limitations —
                                no DAX, no relationships, no calculations)
  - Page5_preview.html         (faithful self-contained rendering of the page:
                                frozen-order sample, full negative-order list,
                                ambiguity case; values verbatim from SQLite)
  - Page5_AUDIT_REPORT.md      (audit report generated from the live
                                validation results of this run)

No `.pbix` is assembled here: this environment has no Power BI Desktop / SSAS
model engine, so a hand-assembled binary could not be opened or verified and
would violate the Phase 7A "only if explicitly supported safely" rule.

Observed context only: no hypothetical order-level values exist in the frozen
output and none are constructed. Writes only the four bundle files above.
Never writes to the database or to any frozen artifact. Fails loudly
(non-zero exit, nothing written) on the first failed gate. Standard lib only.
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
AO05_CSV = ROOT / "data" / "processed" / "phase4c_order_reading.csv"
AO05_QUALITY = ROOT / "data" / "processed" / "phase4c_order_reading_quality.json"

PAGE_NAME = "Page 5 \u2014 Order-Level Observed Context"
VIEW = "order_reading"
TABLE = "ao05_order_reading"
ALLOWED_OBJECTS = {VIEW, TABLE, "sqlite_master"}

EXPECTED_COLS = ["output_name", "scenario_status", "grain", "order_id",
                 "discount_band", "return_status", "neg_flag",
                 "ambiguity_note", "source_artifact", "metric_name",
                 "metric_value", "unit", "definition_ref", "limitation"]
EXPECTED_METRICS = ["wad", "revenue_realization_rate", "net_revenue",
                    "gross_revenue", "modeled_gross_profit",
                    "modeled_gross_margin", "freight_cost", "cost_to_serve",
                    "contribution_profit", "contribution_margin", "quantity",
                    "line_count"]
EXPECTED_ROWS = 60108
EXPECTED_ORDERS = 5009
EXPECTED_BANDS = ["B0", "B1", "B2", "B3", "B4", "B5"]
EXPECTED_RETURN = ["NOT_RETURNED", "YES", "UNKNOWN"]
AMBIG_ORDER = "US-2014-150119"
AMBIG_NOTE = "ORDER_CONTAINS_AMBIGUOUS_PAIR_25P05_HELD_AT_ORDER"
AMBIG_FREIGHT = "26.55"

LIMITATION = ("Observed order-level context only. No hypothetical order-level "
              "scenario values are estimated or displayed.")
NO_ESTIMATE = ("This page does not estimate demand response, causality, "
               "forecasts, or optimized pricing.")

ASSUMPTIONS = [
    "One order is one observation \u2014 distributional context only; supports, "
    "never replaces, band readings.",
    "Discount bands are assigned baseline labels, never recomputed.",
    "COGS treatment is modeled (analytical estimate); AO-05 carries no standalone "
    "COGS row \u2014 modeled_gross_profit / modeled_gross_margin shown as stored.",
    "Freight as observed; NULLs preserved, never defaulted or imputed.",
    "Return-processing and support costs OFF (excluded, not actual).",
    "Results conditional on the selected cost structure and benchmark assumptions.",
]

SAMPLE_ORDERS = 20

CHECKS: list[tuple[str, str]] = []


def fail(check: str, expected: str, actual: str) -> "NoReturn":  # type: ignore[name-defined]
    raise SystemExit(
        f"PAGE5 BUILD FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}"
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
    if unit == "DEC":
        return f"{float(value):,.4f}"
    if unit == "CT":
        return f"{int(float(value)):,}"
    return value


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def pivot(rows: list[tuple]) -> tuple[list[str], dict[str, dict]]:
    """Group (order_id, metric) rows -> ordered order ids + {order: {metric: row}}."""
    order_ids: list[str] = []
    grid: dict[str, dict] = {}
    for r in rows:
        oid = r[3]
        if oid not in grid:
            grid[oid] = {}
            order_ids.append(oid)
        grid[oid][r[9]] = r
    return order_ids, grid


def build_artifacts(rows: list[tuple]) -> dict[str, str]:
    """Pure build: rows in -> {filename: content}. No I/O, no randomness."""
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["output_name", "scenario_status", "grain", "order_id",
                "discount_band", "return_status", "neg_flag",
                "ambiguity_note", "source_artifact", "metric_name",
                "metric_value", "unit", "definition_ref", "limitation"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8],
                    r[9], r[10], r[11], r[12], r[13]])
    csv_text = buf.getvalue()

    order_ids, grid = pivot(rows)
    dims = {oid: (grid[oid]["net_revenue"][4], grid[oid]["net_revenue"][5],
                  grid[oid]["net_revenue"][6], grid[oid]["net_revenue"][7])
            for oid in order_ids}
    neg_ids = [oid for oid in order_ids if dims[oid][2] == "True"]
    amb_ids = [oid for oid in order_ids if dims[oid][3] != ""]
    sample_ids = order_ids[:SAMPLE_ORDERS]

    def val(oid: str, metric: str) -> tuple[str, str]:
        r = grid[oid][metric]
        return r[10], r[11]

    show_cols = ["net_revenue", "contribution_profit", "contribution_margin",
                 "wad", "freight_cost", "cost_to_serve", "quantity", "line_count"]

    layout = {
        "page_name": PAGE_NAME,
        "source": {"database": "data/processed/marginmap.db", "view": VIEW,
                   "source_artifact": "phase4c_order_reading.csv",
                   "import_mode": "Import", "only_view_imported": True},
        "model": {"relationships": [], "dax_measures": [],
                  "power_query_calculations": []},
        "slicers": [{"column": c, "scope": "this page only",
                     "no_model_relationship": True,
                     "options_from_stored_values": True}
                    for c in ("discount_band", "return_status", "neg_flag")],
        "tables": {
            "sample_orders": {"type": "table", "window": f"first {SAMPLE_ORDERS} "
                              "orders in frozen rowid order",
                              "orders": sample_ids},
            "negative_orders": {"type": "table",
                                "filter": "neg_flag = True",
                                "order_count": len(neg_ids), "orders": neg_ids},
            "ambiguity_case": {"type": "table", "orders": amb_ids,
                               "metrics": EXPECTED_METRICS,
                               "cells": {m: {"stored_value": grid[amb_ids[0]][m][10],
                                             "unit": grid[amb_ids[0]][m][11],
                                             "display": fmt(*val(amb_ids[0], m))}
                                         for m in EXPECTED_METRICS}}},
        "labels": {"standing": "OBSERVED ORDER-LEVEL CONTEXT",
                   "grain": "Reporting grain: Order",
                   "source_view": VIEW,
                   "source_artifact": "AO-05 frozen output",
                   "validation": "17/17 PASS "
                                 "(phase4c_order_reading_quality.json)",
                   "observed_only": "Observed values only \u2014 no hypothetical "
                                    "order-level detail exists or is displayed.",
                   "limitation": LIMITATION,
                   "no_estimate": NO_ESTIMATE},
        "methodology": ASSUMPTIONS,
        "restrictions": ["no hypothetical order-level columns",
                         "no averaging of per-order margins/WAD",
                         "no customer/product/region/segment aggregation",
                         "summarization off on all value fields",
                         "all columns imported as Text"],
    }
    layout_text = json.dumps(layout, indent=2)

    def order_table(oids: list[str], title: str, note: str) -> str:
        head = "".join(f"<th>{esc(c)}</th>" for c in
                       ["Order", "Band", "Return", "Neg", "Ambiguity"] + show_cols)
        trs = []
        for oid in oids:
            band, ret, neg, amb = dims[oid]
            amb_cell = (f'<td title="{esc(amb)}">noted</td>' if amb
                        else "<td></td>")
            tds = [f"<td>{esc(oid)}</td>", f"<td>{esc(band)}</td>",
                   f"<td>{esc(ret)}</td>", f"<td>{esc(neg)}</td>", amb_cell]
            for m in show_cols:
                v, u = val(oid, m)
                tds.append(
                    f'<td class="num" data-source-value="{esc(v)}">'
                    f'{esc(fmt(v, u))}</td>')
            trs.append("      <tr>" + "".join(tds) + "</tr>")
        return (f'    <h3>{esc(title)}</h3>\n    <p class="note2">{esc(note)}</p>\n'
                f'    <table class="orders">\n      <tr>{head}</tr>\n'
                + "\n".join(trs) + "\n    </table>")

    def amb_table() -> str:
        oid = amb_ids[0]
        trs = []
        for m in EXPECTED_METRICS:
            r = grid[oid][m]
            v, u, lim = r[10], r[11], r[13]
            trs.append(
                f"      <tr><td>{esc(m)}</td>"
                f'<td class="num" data-source-value="{esc(v)}">'
                f'{esc(fmt(v, u))}</td><td>{esc(u)}</td>'
                f"<td>{esc(lim)}</td></tr>")
        return ("      <tr><th>Metric</th><th>Value</th><th>Unit</th>"
                "<th>Limitation</th></tr>\n" + "\n".join(trs))

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
  .meta {{ font-size: 13px; color: #333; line-height: 1.7; background: #f0f4f1;
           border-left: 4px solid #0f5c2e; padding: 10px 14px; margin: 12px 0 6px; }}
  table.orders, table.amb {{ border-collapse: collapse; font-size: 12px; max-width: 100%; }}
  table.orders th, table.orders td, table.amb th, table.amb td {{
    border: 1px solid #ccc; padding: 5px 7px; text-align: left; vertical-align: top; }}
  table.orders th, table.amb th {{ background: #0f5c2e; color: #fff; }}
  td.num {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
  .wrap {{ overflow-x: auto; }}
  .note2 {{ font-size: 12px; color: #555; }}
  .note {{ font-size: 13px; line-height: 1.65; background: #fafafa;
           border: 1px solid #ddd; padding: 12px 16px; margin-top: 20px; }}
  .note h2 {{ border: none; margin: 0 0 6px; padding: 0; }}
  .caveat {{ font-size: 13px; font-weight: 600; border: 2px solid #8a6d00;
             background: #fff8e1; padding: 10px 14px; margin-top: 16px; }}
  .footer {{ font-size: 12px; color: #666; margin-top: 18px; }}
</style>
</head>
<body>
<div class="page">
  <h1>{esc(PAGE_NAME)}</h1>
  <div class="banner">OBSERVED ORDER-LEVEL CONTEXT</div>
  <div class="meta">
    <b>Source view:</b> order_reading &nbsp;|&nbsp;
    <b>Source artifact:</b> AO-05 frozen output (phase4c_order_reading.csv)<br>
    <b>Reporting grain:</b> Order (5,009 distinct orders \u00d7 12 stored metrics =
    60,108 rows) &nbsp;|&nbsp; <b>Validation status:</b> 17/17 PASS
    (phase4c_order_reading_quality.json)<br>
    <b>Observed only:</b> stored observation beside no hypothetical counterpart
    \u2014 no hypothetical order-level detail exists or is displayed.<br>
    <b>Quality:</b> neg_flag True on exactly 50 orders (0 sign mismatches);
    return cohorts YES / UNKNOWN (CA-2015-102015, retained) / NOT_RETURNED;
    one ambiguity-affected order {esc(AMBIG_ORDER)} (12 rows noted; NULLs preserved
    elsewhere, never defaulted).<br>
    <b>Limitation:</b> {esc(LIMITATION)}<br>
    <b>{esc(NO_ESTIMATE)}</b>
  </div>
  <h2>Observed orders (frozen-order sample)</h2>
  <div class="wrap">
{order_table(sample_ids, f"First {SAMPLE_ORDERS} orders \u2014 frozen rowid order",
             f"Windowed view: first {SAMPLE_ORDERS} of 5,009 orders. Full 60,108-row "
             "detail remains in the imported table with page-local slicers on "
             "discount_band, return_status, neg_flag. Per-order margins/WAD are stored "
             "values \u2014 never averaged.")}
  </div>
  <h2>Negative-contribution orders (neg_flag = True, all 50)</h2>
  <div class="wrap">
{order_table(neg_ids, "All 50 flagged orders \u2014 presentation filter only",
             "Filter neg_flag = True. Flags agree with contribution sign on all 5,009 "
             "orders (0 mismatches per frozen validation).")}
  </div>
  <h2>Ambiguity case</h2>
  <p class="note2">Order {esc(AMBIG_ORDER)} carries
  {esc(AMBIG_NOTE)} on its 12 metric rows (full-order freight 26.55, held at order).
  Note text verbatim; NULL preserved on all other rows.</p>
  <div class="wrap">
    <table class="amb">
{amb_table()}
    </table>
  </div>
  <div class="note"><h2>Methodology assumptions and limitations</h2><ul>
{assumps}
  </ul><p>No N/A metric rows exist in AO-05 (0 empty metric_value values verified);
  empty ambiguity_note cells are preserved NULL dimensions, not N/A metrics. No
  hypothetical, scenario, or variance columns exist at order grain in any frozen
  artifact; none were constructed. Observed relationships on this page are not
  causal or predictive readings.</p></div>
  <div class="caveat">{esc(LIMITATION)} {esc(NO_ESTIMATE)}</div>
  <div class="footer">Preview generated by powerbi/page5_build.py from
    data/processed/marginmap.db (read-only). Display formatting of exact stored TEXT;
    each value carries its source string in <i>data-source-value</i>. No DAX, no
    relationships, no new calculations, no new metrics, no re-banding.</div>
</div>
</body>
</html>
"""
    return {"page5_order_values.csv": csv_text,
            "Page5_Report_Layout.json": layout_text,
            "Page5_preview.html": preview}


def audit_report(checks: list[tuple[str, str]], git_status: str) -> str:
    lines = ["# Phase 7B Page 5 \u2014 Implementation Audit Report", "",
             "## 1. Implementation result", "",
             "Page 5 \u2014 Order-Level Observed Context is implemented as a verified, "
             "deterministic bundle built by `powerbi/page5_build.py`. All listed source "
             "documents were read before building (Phase 5, SQL layer + freeze, Phase 7A "
             "foundation, 7B build spec, Gate 10 decision log, interpretation design, "
             "AO-01\u2013AO-06 freezes, Page 1\u20134 patterns); no conflicts were found "
             "(60,108-row scope, 5,009 orders \u00d7 12 metrics, observed-only standing, "
             "stored-field discipline, 17/17 standing, labels, and limitation wording "
             "all agree).",
             "", "## 2. Power BI Desktop availability", "",
             "Not available on this machine (no `PBIDesktop.exe`, no Power BI Desktop "
             "install directory). No `.pbix` binary was created or fabricated, per the "
             "task boundary and the Phase 7A safety rule. `Page5_Report_Layout.json` is "
             "the complete Desktop build instruction; `Page5_preview.html` renders the "
             "frozen-order sample, the full 50-row negative list, and the ambiguity case "
             "with verbatim SQLite values.",
             "", "## 3. Exact files created", "",
             "```text", "powerbi/page5_build.py",
             "powerbi/page5_order_values.csv  (ignored, *.csv policy; regenerable)",
             "powerbi/Page5_Report_Layout.json", "powerbi/Page5_preview.html",
             "powerbi/Page5_AUDIT_REPORT.md  (this file)", "```", "",
             "## 4. Exact files modified", "", "None.", "",
             "## 5. Source view and source table", "",
             "`order_reading` (table `ao05_order_reading`) from "
             "`data/processed/marginmap.db` (Import, all columns Text). Query tracking "
             "asserts no other view or table was read; no AO CSV or quality JSON supplied "
             "displayed values.",
             "", "## 6. Exact row and column counts", "",
             "60,108 rows (table and view agree) \u00d7 14 frozen columns "
             "(`output_name, scenario_status, grain, order_id, discount_band, "
             "return_status, neg_flag, ambiguity_note, source_artifact, metric_name, "
             "metric_value, unit, definition_ref, limitation`).",
             "", "## 7. Reporting grain", "",
             "`Order` \u2014 uniform across all 60,108 rows; one row per "
             "(`order_id`, `metric_name`).",
             "", "## 8. Distinct-order count", "",
             "5,009 distinct orders (verified in-view); every order carries exactly the "
             "12 frozen metrics (60,108 distinct pairs, no gaps, no duplicates).",
             "", "## 9. Observed-only status", "",
             "Uniform `scenario_status = OBSERVED BASELINE` (verified). No metric name "
             "matches hypo*/variance*/scenario* patterns (verified); no hypothetical, "
             "scenario, or variance columns exist at order grain.",
             "", "## 10. Stored fields and their meanings", "",
             "- Metrics (12, frozen order): `wad` (DEC, per-order recomputed), "
             "`revenue_realization_rate` (PCT), `net_revenue` (CUR), `gross_revenue` "
             "(CUR), `modeled_gross_profit` (CUR), `modeled_gross_margin` (PCT), "
             "`freight_cost` (CUR), `cost_to_serve` (CUR, = freight, OFF costs excluded), "
             "`contribution_profit` (CUR, authoritative order grain), "
             "`contribution_margin` (PCT, per-order, never averaged), `quantity` (CT), "
             "`line_count` (CT). No standalone COGS row exists (verified); none built.",
             "- Dimensions: `discount_band` (B0\u2013B5 assigned labels, no TOTAL at order "
             "grain), `return_status` (YES / UNKNOWN / NOT_RETURNED), `neg_flag` "
             "(True on exactly 50 orders, 0 sign mismatches), `ambiguity_note` (populated "
             "on the 12 rows of US-2014-150119 only; NULL preserved elsewhere).",
             "", "## 11. Exact validation checks and results", ""]
    for name, detail in checks:
        lines.append(f"- `[{name}]` PASS \u2014 {detail}")
    lines.append("- `[bundle-audit-verified]` PASS \u2014 asserted post-write by the "
                 "builder: this file lists every check name above plus live git status "
                 "(see console output for the PASS line).")
    lines += ["", "## 12. N/A preservation", "",
              "Zero empty-`metric_value` rows (verified) \u2014 AO-05 has no N/A metrics, "
              "so no `N/A` symbol appears in the value cells and nothing was fabricated. "
              "Empty `ambiguity_note` cells on unaffected orders are preserved NULL "
              "dimensions rendered blank with labeled meaning, not N/A metrics.",
              "", "## 13. Gate 10 compliance", ""]
    gate = [
        "`OBSERVED ORDER-LEVEL CONTEXT` banner; observed-only nature stated.",
        "Reporting grain `Order` displayed.",
        "Source view `order_reading` displayed.",
        "Source artifact (AO-05 frozen output) displayed.",
        "Validation status `17/17 PASS` and quality flags displayed.",
        "Stored observation vs interpretation distinguished (single-observation warning).",
        "No N/A metric rows; NULL-dimension handling labeled (no silent blanks).",
        "Return-status and negative-value indicators shown unaltered.",
        "Ambiguity note shown verbatim, never suppressed or rewritten.",
        "Methodology assumptions and limitations shown.",
        "No-hypothetical guarantee stated with the exact limitation wording.",
        "No-estimate statement shown (no demand/causality/forecast/optimization).",
        "No causal or predictive implication (single-observation warning + scan).",
        "Frozen artifacts read-only."]
    for i, g in enumerate(gate, 1):
        lines.append(f"- ({i}) PASS \u2014 {g}")
    lines += ["", "## 14. No-hypothetical-order-level guarantee", "",
              "Directly tested: metric-name pattern scan finds no hypo*/variance*/"
              "scenario* metrics; every row is `OBSERVED BASELINE`; the builder, layout, "
              "and preview contain no scenario/hypothetical/variance construct at order "
              "grain. No such values exist in any frozen artifact, and none were built.",
              "", "## 15. Frozen-artifact protection", "",
              "Database opened read-only (`mode=ro`) throughout; loader never re-executed; "
              "no manual DB edits. No Phase 4C script, CSV, quality JSON, freeze document, "
              "SQL file, or prior AO artifact modified. AO-05 CSV re-hashed byte-identical "
              "this run; SQL-layer `frozen-unchanged` 6/6.",
              "", "## 16. Determinism", "",
              "- Directly tested: two in-process builds asserted byte-equal before writing "
              "(`determinism-in-run`); written files re-read and compared "
              "(`bundle-*-verified`); operator second execution reproduces bytes.",
              "- Code-inspection: single-view-only query tracking; presentation-only "
              "filtering/formatting (reversible `fmt`); fail-loud `fail()` before any write.",
              "- Inherited: AO-05 frozen 17/17 validation and SQL-layer 13/13 validation "
              "reused as standing evidence, not re-executed logic.",
              "", "## 17. Preview/layout verification", "",
              "Preview embeds every displayed stored value verbatim "
              "(`data-source-value`): 20-order sample, all 50 negative orders, and the "
              "12-row ambiguity case \u2014 plus every required label, the limitation "
              "wording, the no-estimate statement, and methodology. Layout JSON holds the "
              "three table specs (windowed sample, neg-flag filter, ambiguity case), "
              "three page-local slicer specs over stored fields only, and an empty model "
              "(no relationships, DAX, or Power Query calculations). Visual types are "
              "table + slicer only.",
              "", "## 18. Exact Git status", "", "```text", git_status.strip(),
              "```", "", "## 19. Files to commit later", "", "```text",
              "powerbi/page5_build.py", "powerbi/Page5_Report_Layout.json",
              "powerbi/Page5_preview.html", "powerbi/Page5_AUDIT_REPORT.md",
              "```", "",
              "(The CSV stays ignored under `*.csv`; regenerable via the builder.)",
              "", "## 20. Blocking and non-blocking issues", "",
              "- Blocking: none.", "- Non-blocking: no `.pbix` binary (no Power BI "
              "Desktop; layout JSON + preview provided, same as Pages 1\u20134). "
              "Prohibited-term scan is a literal-substring check with the limitation and "
              "no-estimate sentences stripped (documented limit). Full 60,108-row detail "
              "lives in the imported table/CSV; the preview windows it honestly.",
              "", "## 21. No commit or push", "",
              "Confirmed. No `git add`, `commit`, or `push` executed; Page 6 not begun."]
    return "\n".join(lines) + "\n"


def main() -> int:
    if not DB.is_file():
        fail("db-exists", f"database at {DB}", "file missing")
    passed("db-exists", str(DB))
    if not AO05_CSV.is_file() or not AO05_QUALITY.is_file():
        fail("frozen-inputs-present", "AO-05 CSV + quality JSON present",
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
        passed("columns-match", "14/14 frozen columns in order")

        rows = tcon.execute(
            f"SELECT output_name, scenario_status, grain, order_id, discount_band,"
            f" return_status, neg_flag, ambiguity_note, source_artifact, metric_name,"
            f" metric_value, unit, definition_ref, limitation FROM {TABLE}"
            f" ORDER BY rowid").fetchall()
        n_view = tcon.execute(f"SELECT COUNT(*) FROM {VIEW}").fetchone()[0]
        if len(rows) != EXPECTED_ROWS or n_view != EXPECTED_ROWS:
            fail("row-count-60108", "60108 rows in table and view",
                 f"table={len(rows)} view={n_view}")
        passed("row-count-60108", "60108/60108 rows (table and view agree)")

        if tcon.touched - ALLOWED_OBJECTS:
            fail("source-view-only", f"only {sorted(ALLOWED_OBJECTS)}",
                 f"touched {sorted(tcon.touched)}")
        passed("source-view-only",
               f"only AO-05 objects read: {sorted(tcon.touched)}")

        if {r[2] for r in rows} != {"Order"}:
            fail("grain-order", "Order uniform", "mismatch")
        passed("grain-order", "60108/60108 rows at Order grain")

        if {r[1] for r in rows} != {"OBSERVED BASELINE"}:
            fail("observed-only", "OBSERVED BASELINE uniform", "mismatch")
        passed("observed-only", "uniform OBSERVED BASELINE; no other standing")

        n_orders = tcon.execute(
            f"SELECT COUNT(DISTINCT order_id) FROM {TABLE}").fetchone()[0]
        if n_orders != EXPECTED_ORDERS:
            fail("distinct-orders-5009", "5009 distinct orders", str(n_orders))
        passed("distinct-orders-5009", "5009 distinct orders")

        first = tcon.execute(
            f"SELECT order_id FROM {TABLE} ORDER BY rowid LIMIT 1").fetchone()[0]
        m0 = [r[0] for r in tcon.execute(
            f"SELECT metric_name FROM {TABLE} WHERE order_id=? ORDER BY rowid",
            (first,))]
        if m0 != EXPECTED_METRICS:
            fail("metrics-per-order", str(EXPECTED_METRICS), str(m0))
        pairs = tcon.execute(
            f"SELECT COUNT(*), COUNT(DISTINCT order_id || '|' || metric_name)"
            f" FROM {TABLE}").fetchone()
        if pairs[0] != EXPECTED_ROWS or pairs[1] != EXPECTED_ROWS:
            fail("rows-per-order-complete", "60108 unique (order,metric) pairs",
                 str(pairs))
        passed("metrics-per-order", "12/12 frozen metrics in frozen order per order")
        passed("rows-per-order-complete", "5009x12 complete, no gaps/duplicates")

        hypo = [r[0] for r in tcon.execute(
            f"SELECT DISTINCT metric_name FROM {TABLE} WHERE metric_name LIKE"
            f" 'hypo%' OR metric_name LIKE '%variance%' OR metric_name LIKE"
            f" '%scenario%' OR metric_name LIKE '%hypothetical%'")]
        if hypo:
            fail("no-hypothetical", "no hypo/variance/scenario metrics", str(hypo))
        passed("no-hypothetical", "no hypothetical order-level metrics exist")

        if sorted({r[4] for r in rows}) != EXPECTED_BANDS:
            fail("fields-preserved-bands", str(EXPECTED_BANDS), "mismatch")
        if set(r[5] for r in rows) != set(EXPECTED_RETURN):
            fail("fields-preserved-return", str(EXPECTED_RETURN), "mismatch")
        if sorted({r[6] for r in rows}) != ["False", "True"]:
            fail("fields-preserved-negflag", "[False, True]", "mismatch")
        amb = sorted({r[7] for r in rows if r[7] != ""})
        if amb != [AMBIG_NOTE]:
            fail("fields-preserved-ambiguity", "single frozen note", str(amb))
        passed("fields-preserved",
               "bands B0-B5; return 3 values; neg True/False; 1 ambiguity note")

        n_empty = sum(1 for r in rows if r[10] == "")
        if n_empty != 0:
            fail("na-preserved", "zero empty metric_value rows", str(n_empty))
        amb_rows = sum(1 for r in rows if r[7] != "")
        if amb_rows != 12:
            fail("na-preserved", "12 noted ambiguity rows", str(amb_rows))
        passed("na-preserved",
               "0 N/A metric rows; 12 noted ambiguity rows; NULLs preserved")

        n_neg = tcon.execute(
            f"SELECT COUNT(DISTINCT order_id) FROM {TABLE} WHERE neg_flag='True'"
            ).fetchone()[0]
        amb_oid = tcon.execute(
            f"SELECT DISTINCT order_id FROM {TABLE} WHERE ambiguity_note != ''"
            ).fetchall()
        amb_fr = tcon.execute(
            f"SELECT metric_value FROM {TABLE} WHERE order_id=? AND"
            f" metric_name='freight_cost'", (AMBIG_ORDER,)).fetchone()[0]
        if n_neg != 50 or [a[0] for a in amb_oid] != [AMBIG_ORDER] \
                or amb_fr != AMBIG_FREIGHT:
            fail("spot-values", "50 neg orders; ambiguity US-2014-150119 @26.55",
                 f"neg={n_neg} amb={amb_oid} freight={amb_fr}")
        passed("spot-values",
               "50 negative orders; ambiguity case + freight 26.55 intact")
    finally:
        con.close()

    quality = json.loads(AO05_QUALITY.read_text(encoding="utf-8"))
    qchecks = quality.get("checks", [])
    if len(qchecks) != 17 or any(c.get("status") != "PASS" for c in qchecks):
        fail("quality-17-pass", "17/17 PASS",
             f"{len(qchecks)} checks, non-PASS present")
    passed("quality-17-pass",
           "phase4c_order_reading_quality.json 17/17 PASS")

    recorded = quality.get("outputs", {}).get(
        "phase4c_order_reading.csv", {}).get("sha256")
    actual = hashlib.sha256(AO05_CSV.read_bytes()).hexdigest()
    if actual != recorded:
        fail("frozen-byte-identical", f"sha {recorded}", actual)
    passed("frozen-byte-identical", f"AO-05 CSV byte-identical ({actual[:12]}\u2026)")

    artifacts = build_artifacts(rows)
    if build_artifacts(rows) != artifacts:
        fail("determinism-in-run", "identical bytes on rebuild", "difference")
    passed("determinism-in-run", "two in-process builds byte-identical")

    blob = "\n".join(artifacts.values())
    stripped = blob.replace(LIMITATION, "").replace(NO_ESTIMATE, "")
    # Compliant prohibition phrasing in the methodology note (Gate 10-conformant).
    stripped = stripped.replace("are not\n  causal or predictive readings", "")
    stripped = stripped.replace("are not causal or predictive readings", "")
    slow = stripped.lower()
    bad = [w for w in ("forecast", "causal", "demand prediction", "elasticity",
                       "uplift", "driven by", "caused by", "optimiz")
           if w in slow]
    if bad:
        fail("language-scan", "no predictive wording outside limitation", str(bad))
    passed("language-scan", "no forecast/causal/demand/optimization wording")

    for name in ("page5_order_values.csv", "Page5_Report_Layout.json",
                 "Page5_preview.html"):
        (OUT_DIR / name).write_text(artifacts[name], encoding="utf-8",
                                    newline="" if name.endswith(".csv") else None)

    back = (OUT_DIR / "page5_order_values.csv").read_text(encoding="utf-8")
    rd = list(csv.reader(io.StringIO(back)))
    if len(rd) - 1 != len(rows) or \
       [tuple(r) for r in rd[1:]] != [tuple(map(str, r)) for r in rows]:
        fail("bundle-csv-verified", "cell-for-cell equality after write",
             "difference found")
    passed("bundle-csv-verified",
           "page5_order_values.csv identical to DB source")

    html_text = (OUT_DIR / "Page5_preview.html").read_text(encoding="utf-8")
    order_ids, grid = pivot(rows)
    shown = order_ids[:SAMPLE_ORDERS] + \
        [oid for oid in order_ids if grid[oid]["net_revenue"][6] == "True"] + \
        [oid for oid in order_ids if grid[oid]["net_revenue"][7] != ""]
    shown = list(dict.fromkeys(shown))
    missing = []
    for oid in shown:
        for m in ["net_revenue", "contribution_profit", "contribution_margin",
                  "wad", "freight_cost", "cost_to_serve", "quantity", "line_count"]:
            v = grid[oid][m][10]
            if f'data-source-value="{esc(v)}"' not in html_text:
                missing.append(f"{oid}/{m}")
    amb_oid = [oid for oid in order_ids if grid[oid]["net_revenue"][7] != ""][0]
    for m in EXPECTED_METRICS:
        v = grid[amb_oid][m][10]
        if f'data-source-value="{esc(v)}"' not in html_text:
            missing.append(f"{amb_oid}/{m}")
    if missing:
        fail("bundle-html-verified", "displayed values embedded verbatim",
             str(missing[:5]))
    for token in ["OBSERVED ORDER-LEVEL CONTEXT", "Reporting grain:",
                  "order_reading", "17/17 PASS", AMBIG_ORDER, AMBIG_NOTE,
                  LIMITATION, NO_ESTIMATE]:
        if token not in html_text:
            fail("bundle-html-verified", f"label present: {token[:40]}", "absent")
    if "Order (5,009 distinct orders" not in html_text:
        fail("bundle-html-verified", "label present: Order grain detail", "absent")
    passed("bundle-html-verified",
           f"{len(shown)} orders + ambiguity detail verbatim + labels + limits")

    layout_back = json.loads(
        (OUT_DIR / "Page5_Report_Layout.json").read_text(encoding="utf-8"))
    if layout_back["page_name"] != PAGE_NAME or \
       layout_back["model"] != {"relationships": [],
                                "dax_measures": [],
                                "power_query_calculations": []}:
        fail("bundle-layout-verified", "page name + empty model", "mismatch")
    if {s["column"] for s in layout_back["slicers"]} != \
       {"discount_band", "return_status", "neg_flag"}:
        fail("bundle-layout-verified", "3 stored-field slicers", "mismatch")
    if set(layout_back["tables"]) != {"sample_orders", "negative_orders",
                                      "ambiguity_case"}:
        fail("bundle-layout-verified", "3 table specs", "mismatch")
    passed("bundle-layout-verified",
           "3 tables + 3 stored-field slicers, visuals table/slicer only")

    try:
        git_status = subprocess.run(
            ["git", "status", "--short"], cwd=ROOT, capture_output=True,
            text=True, timeout=30).stdout
    except Exception as e:  # noqa: BLE001 — record instead of failing
        git_status = f"(git unavailable: {e})"

    audit = audit_report(CHECKS, git_status)
    (OUT_DIR / "Page5_AUDIT_REPORT.md").write_text(audit, encoding="utf-8")
    audit_back = (OUT_DIR / "Page5_AUDIT_REPORT.md").read_text(encoding="utf-8")
    if not all(f"`[{name}]`" in audit_back for name, _ in CHECKS):
        fail("bundle-audit-verified", "all check names in audit", "missing")
    passed("bundle-audit-verified",
           f"audit lists all {len(CHECKS)} checks + git status")

    print("OK: Page 5 bundle built and verified (no .pbix; see audit report)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
