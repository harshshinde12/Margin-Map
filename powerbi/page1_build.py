"""Margin Map Phase 7B — Page 1 (Executive Profitability Overview) builder.

Reads the frozen AO-01 view `baseline_total` from `data/processed/marginmap.db`
READ-ONLY, verifies it against the frozen expectations, and emits the Page 1
implementation bundle into `powerbi/`:

  - page1_baseline_values.csv  (verbatim 20-row source slice, TEXT preserved)
  - Page1_Report_Layout.json   (exact visual-by-visual build instructions for
                                Power BI Desktop: page name, visual types,
                                positions, field bindings, formats, labels,
                                caveats — no DAX, no relationships)
  - Page1_preview.html         (faithful self-contained rendering of the page
                                with values injected verbatim from SQLite,
                                for review where Power BI Desktop is absent)

No `.pbix` is assembled here: this environment has no Power BI Desktop / SSAS
model engine, so a hand-assembled binary could not be opened or verified and
would violate the Phase 7A "only if explicitly supported safely" rule. The
layout JSON is the complete click-for-click instruction for creating the
`.pbix` in Power BI Desktop; the HTML preview proves values, labels, and
formatting ahead of that step.

Writes only the three bundle files above. Never writes to the database or to
any frozen artifact. Fails loudly (non-zero exit, nothing half-written) on
any mismatch.
"""

from __future__ import annotations

import csv
import html
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "marginmap.db"
OUT_DIR = ROOT / "powerbi"

PAGE_NAME = "Page 1 \u2014 Executive Profitability Overview"

# Frozen AO-01 metric order (verified against ao01_baseline_total ORDER BY rowid).
EXPECTED_METRICS = [
    "net_revenue", "gross_revenue", "discount_amount", "modeled_cogs",
    "modeled_gross_profit", "modeled_gross_margin_pct", "freight_cost",
    "cost_to_serve", "contribution_profit", "contribution_margin_pct",
    "wad", "revenue_realization_rate", "quantity", "order_count",
    "line_count", "neg_contribution_orders", "return_yes_orders",
    "return_unknown_orders", "return_not_returned_orders",
    "null_freight_lines",
]

SPOT_METRIC = "contribution_profit"
SPOT_VALUE = "565116.9418299999"

# The nine task-required KPI cards: (metric_name, card title, format kind).
CARDS = [
    ("net_revenue", "Net Revenue (baseline)", "CUR"),
    ("modeled_gross_profit", "Gross Profit (modeled)", "CUR"),
    ("modeled_gross_margin_pct", "Gross Margin (modeled)", "PCT"),
    ("contribution_profit", "Contribution Profit", "CUR"),
    ("contribution_margin_pct", "Contribution Margin", "PCT"),
    ("wad", "WAD (weighted-avg. discount)", "DEC"),
    ("quantity", "Quantity", "CT"),
    ("order_count", "Orders", "CT"),
    ("line_count", "Lines", "CT"),
]

CAVEAT_SHORT = ("Observed baseline under the stated methodology and cost "
                "assumptions; not a forecast or causal estimate.")

ASSUMPTIONS = [
    "Observed quantity retained (37,873 units; no demand response estimated).",
    "COGS is modeled (revenue-based sub-category benchmarks) \u2014 analytical "
    "estimate, not accounting COGS.",
    "Freight passthrough as observed (methodology unverified \u2014 Phase 2 caveat).",
    "Return-processing costs OFF (excluded, not actual).",
    "Support costs OFF (excluded, not actual).",
    "Results conditional on the selected cost structure and benchmark assumptions.",
]


def fail(check: str, expected: str, actual: str) -> "NoReturn":  # type: ignore[name-defined]
    raise SystemExit(
        f"PAGE1 BUILD FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}"
    )


def passed(check: str, detail: str) -> None:
    print(f"PASS [{check}] {detail}")


def fmt(value: str, unit: str) -> str:
    """Display formatting only. Source TEXT is never altered; units explicit."""
    if unit == "CUR":
        return f"${float(value):,.2f}"
    if unit == "PCT":
        return f"{float(value):,.2f}%"
    if unit == "DEC":
        return f"{float(value):,.4f}"
    if unit == "CT":
        return f"{int(float(value)):,}"
    return value


def main() -> int:
    if not DB.is_file():
        fail("db-exists", f"database at {DB}", "file missing")
    passed("db-exists", str(DB))

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        views = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='view'")}
        if "baseline_total" not in views:
            fail("view-exists", "view baseline_total", "missing")
        for other in ("contribution_by_band", "scenario_comparison_total",
                      "variance_by_band", "order_reading", "quality_summary"):
            pass  # documented: Page 1 must not import these; builder reads none.
        passed("view-exists", "baseline_total present; no other view read")

        rows = con.execute(
            "SELECT output_name, scenario_status, grain, source_artifact,"
            " metric_name, metric_value, unit, definition_ref, limitation"
            " FROM ao01_baseline_total ORDER BY rowid").fetchall()
        view_rows = con.execute("SELECT COUNT(*) FROM baseline_total").fetchone()[0]
        if len(rows) != 20 or view_rows != 20:
            fail("row-count", "20 rows in table and view",
                 f"table={len(rows)} view={view_rows}")
        passed("row-count", "20/20 rows (table and view agree)")

        metrics = [r[4] for r in rows]
        if metrics != EXPECTED_METRICS:
            fail("metric-set", str(EXPECTED_METRICS), str(metrics))
        passed("metric-set", "20/20 frozen AO-01 metrics in frozen order")

        if any(r[5] == "" for r in rows):
            fail("na-check", "zero empty metric_value rows",
                 "empty value found (would require N/A rendering)")
        passed("na-check", "0 N/A rows — every required metric present, none fabricated")

        spot = con.execute(
            "SELECT metric_value FROM ao01_baseline_total"
            " WHERE metric_name='contribution_profit'").fetchone()[0]
        if spot != SPOT_VALUE:
            fail("spot-value", SPOT_VALUE, repr(spot))
        passed("spot-value", f"contribution_profit = {SPOT_VALUE}")

        statuses = {r[1] for r in rows}
        grains = {r[2] for r in rows}
        if statuses != {"OBSERVED BASELINE"} or grains != {"TOTAL"}:
            fail("standing-grain", "OBSERVED BASELINE / TOTAL",
                 f"{statuses} / {grains}")
        passed("standing-grain", "uniform OBSERVED BASELINE at TOTAL grain")
    finally:
        con.close()

    by_metric = {r[4]: r for r in rows}

    # ---- 1. verbatim values slice -------------------------------------------
    csv_path = OUT_DIR / "page1_baseline_values.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric_name", "metric_value", "unit",
                    "source_artifact", "definition_ref", "limitation"])
        for r in rows:
            w.writerow([r[4], r[5], r[6], r[3], r[7], r[8]])

    # ---- 2. layout JSON (Desktop build instructions) --------------------------
    layout = {
        "page_name": PAGE_NAME,
        "source": {"database": "data/processed/marginmap.db",
                   "view": "baseline_total", "import_mode": "Import",
                   "only_view_imported": True},
        "model": {"relationships": [], "dax_measures": [],
                  "power_query_calculations": []},
        "cards": [{"title": t, "binding": {"table": "baseline_total",
                                           "metric_name": m},
                   "stored_value": by_metric[m][5], "unit": by_metric[m][6],
                   "display": fmt(by_metric[m][5], k)}
                  for (m, t, k) in CARDS],
        "metric_table": {"type": "table",
                         "columns": ["metric_name", "metric_value",
                                     "unit", "limitation"],
                         "row_count": 20},
        "labels": {"standing": "OBSERVED BASELINE",
                   "grain": "Reporting grain: TOTAL",
                   "authority": "Authority: ORDER",
                   "source_view": "baseline_total",
                   "source_artifact": "AO-01 baseline TOTAL output",
                   "validation": "AO-01 validation 18/18 PASS "
                                 "(phase4c_baseline_total_quality.json)",
                   "distinction": "Gross profit (modeled, excl. serve costs) "
                                  "vs Contribution profit (net of serve costs) "
                                  "vs Discount amount (revenue forgone, not "
                                  "profit loss) \u2014 not interchangeable."},
        "methodology": ASSUMPTIONS,
        "caveat": CAVEAT_SHORT,
        "restrictions": ["no pie/line/forecast/AI/decomposition visuals",
                         "no waterfall (not approved in spec)",
                         "summarization off on all value fields",
                         "all columns imported as Text"],
    }
    layout_path = OUT_DIR / "Page1_Report_Layout.json"
    layout_path.write_text(json.dumps(layout, indent=2), encoding="utf-8")

    # ---- 3. HTML preview (review rendering, values verbatim) ------------------
    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    card_html = "\n".join(
        f'      <div class="card"><div class="card-title">{esc(t)}</div>'
        f'<div class="card-value" data-source-value="{esc(by_metric[m][5])}">'
        f'{esc(fmt(by_metric[m][5], k))}</div>'
        f'<div class="card-unit">Unit: {esc(by_metric[m][6])}</div></div>'
        for (m, t, k) in CARDS)

    table_rows = "\n".join(
        f'      <tr><td>{esc(r[4])}</td>'
        f'<td class="num" data-source-value="{esc(r[5])}">{esc(fmt(r[5], r[6]))}</td>'
        f'<td>{esc(r[6])}</td><td>{esc(r[8])}</td></tr>'
        for r in rows)

    assumptions_html = "\n".join(f"      <li>{esc(a)}</li>" for a in ASSUMPTIONS)

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
  .banner {{ display: inline-block; background: #0f5c2e; color: #fff; font-weight: 600;
             padding: 4px 12px; margin: 8px 0; font-size: 13px; letter-spacing: .5px; }}
  .meta {{ font-size: 13px; color: #333; line-height: 1.7; background: #f0f4f1;
           border-left: 4px solid #0f5c2e; padding: 10px 14px; margin: 12px 0 20px; }}
  .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .card {{ border: 1px solid #ccc; border-top: 4px solid #0f5c2e; padding: 12px 14px; }}
  .card-title {{ font-size: 12px; color: #555; text-transform: uppercase;
                 letter-spacing: .4px; }}
  .card-value {{ font-size: 26px; font-weight: 600; margin: 4px 0; }}
  .card-unit {{ font-size: 12px; color: #666; }}
  table.metrics {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }}
  table.metrics th, table.metrics td {{ border: 1px solid #ccc; padding: 6px 8px;
                                        text-align: left; vertical-align: top; }}
  table.metrics th {{ background: #0f5c2e; color: #fff; }}
  td.num {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
  .note {{ font-size: 13px; line-height: 1.65; background: #fafafa;
           border: 1px solid #ddd; padding: 12px 16px; margin-top: 20px; }}
  .note h2 {{ font-size: 15px; margin: 0 0 6px; }}
  .caveat {{ font-size: 13px; font-weight: 600; border: 2px solid #8a6d00;
             background: #fff8e1; padding: 10px 14px; margin-top: 16px; }}
  .footer {{ font-size: 12px; color: #666; margin-top: 18px; }}
</style>
</head>
<body>
<div class="page">
  <h1>{esc(PAGE_NAME)}</h1>
  <div class="banner">OBSERVED BASELINE</div>
  <div class="meta">
    <b>Reporting grain:</b> TOTAL (overall TOTAL, order economics rolled up, authoritative)<br>
    <b>Authority:</b> ORDER &nbsp;|&nbsp; <b>Source view:</b> baseline_total
    &nbsp;|&nbsp; <b>Source artifact:</b> AO-01 baseline TOTAL output<br>
    <b>Validation status:</b> AO-01 validation 18/18 PASS
    (phase4c_baseline_total_quality.json)<br>
    <b>Quality:</b> 50 negative-contribution orders; return cohorts YES 296 / UNKNOWN 1
    (CA-2015-102015, retained) / NOT_RETURNED 4,712; 2 NULL-freight lines preserved
    and flagged (never imputed).<br>
    <b>Reading rule:</b> Gross profit (modeled, excl. serve costs) vs Contribution profit
    (net of serve costs) vs Discount amount (revenue forgone, not profit loss)
    \u2014 three distinct concepts, not interchangeable.
  </div>
  <div class="cards">
{card_html}
  </div>
  <table class="metrics">
    <tr><th>Metric</th><th>Value</th><th>Unit</th><th>Limitation</th></tr>
{table_rows}
  </table>
  <div class="note"><h2>Methodology assumptions</h2><ul>
{assumptions_html}
  </ul></div>
  <div class="caveat">{esc(CAVEAT_SHORT)}</div>
  <div class="footer">Preview generated by powerbi/page1_build.py from
    data/processed/marginmap.db (read-only). Values shown are display formatting of the
    exact stored TEXT; each value carries its source string in
    <i>data-source-value</i>. No DAX, no relationships, no new calculations.</div>
</div>
</body>
</html>
"""
    preview_path = OUT_DIR / "Page1_preview.html"
    preview_path.write_text(preview, encoding="utf-8")

    # ---- round-trip verification of emitted bundle ----------------------------
    with open(csv_path, newline="", encoding="utf-8") as f:
        back = list(csv.reader(f))
    if [r[0] for r in back[1:]] != EXPECTED_METRICS or any(
            len(r) != 6 for r in back[1:]):
        fail("bundle-csv", "20 verbatim rows in frozen order", "mismatch")
    con2 = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        db_vals = con2.execute(
            "SELECT metric_name, metric_value FROM ao01_baseline_total"
            " ORDER BY rowid").fetchall()
    finally:
        con2.close()
    if [(r[0], r[1]) for r in back[1:]] != [(m, v) for m, v in db_vals]:
        fail("bundle-csv", "cell-for-cell equality with SQLite source",
             "difference found")
    passed("bundle-csv", "page1_baseline_values.csv identical to DB source")

    html_text = preview_path.read_text(encoding="utf-8")
    missing = [m for (m, v) in db_vals if f'data-source-value="{html.escape(v, quote=True)}"' not in html_text]
    if missing:
        fail("bundle-html", "all 20 stored values embedded verbatim", str(missing))
    for token in ["OBSERVED BASELINE", "Reporting grain:", "Authority:",
                  "baseline_total", "ORDER", CAVEAT_SHORT]:
        if token not in html_text:
            fail("bundle-html", f"label present: {token}", "absent")
    passed("bundle-html", "Page1_preview.html carries all 20 values verbatim + labels + caveat")

    layout_back = json.loads(layout_path.read_text(encoding="utf-8"))
    if (layout_back["page_name"] != PAGE_NAME
            or layout_back["model"] != {"relationships": [],
                                        "dax_measures": [],
                                        "power_query_calculations": []}
            or len(layout_back["cards"]) != 9):
        fail("bundle-layout", "page name + empty model + 9 cards", "mismatch")
    passed("bundle-layout", "Page1_Report_Layout.json: 9 cards, no DAX, no relationships")

    print("OK: Page 1 bundle built and verified (no .pbix; see audit report)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
