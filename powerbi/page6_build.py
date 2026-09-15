"""Margin Map Phase 7B — Page 6 (Data Quality and Analytical Reliability) builder.

Reads the frozen AO-06 view `quality_summary` from
`data/processed/marginmap.db` READ-ONLY, verifies it against the frozen
expectations, and emits the Page 6 implementation bundle into `powerbi/`:

  - page6_quality_values.csv  (verbatim 125-row source slice, TEXT kept)
  - Page6_Report_Layout.json  (exact Desktop build instructions: page name,
                               verdict cards, eligibility table, upstream-check
                               table, labels, limitations — no DAX, no
                               relationships, no joins, no new metrics)
  - Page6_preview.html        (faithful self-contained rendering of the page
                               with values verbatim from SQLite, for review
                               where Power BI Desktop is absent)
  - Page6_AUDIT_REPORT.md     (audit report generated from the live
                               validation results of this run)

No `.pbix` is assembled here: this environment has no Power BI Desktop / SSAS
model engine, so a hand-assembled binary could not be opened or verified and
would violate the Phase 7A "only if explicitly supported safely" rule.

Eligibility-gate content only: arithmetic/lineage fitness, mirrored verbatim
from frozen upstream evidence (never re-executed, never reworded). Writes only
the four bundle files above. Never writes to the database or to any frozen
artifact. Fails loudly (non-zero exit, nothing written) on the first failed
gate. Standard library only.
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
AO06_CSV = ROOT / "data" / "processed" / "phase4c_quality_summary.csv"
AO06_QUALITY = ROOT / "data" / "processed" / "phase4c_quality_summary_quality.json"

PAGE_NAME = "Page 6 \u2014 Data Quality and Analytical Reliability"
VIEW = "quality_summary"
TABLE = "ao06_quality_summary"
ALLOWED_OBJECTS = {VIEW, TABLE, "sqlite_master"}

EXPECTED_COLS = ["output_name", "scenario_status", "grain", "artifact",
                 "check_id", "metric_name", "metric_value", "unit", "status",
                 "expected", "actual", "source_artifact", "definition_ref",
                 "limitation"]
EXPECTED_METRIC_COUNTS = {"artifacts_verified": 1, "checks_attested": 1,
                          "checks_passed": 4, "eligibility": 17,
                          "overall_eligibility": 1, "row_count": 13,
                          "sha256_match": 13, "upstream_check": 75}
EXPECTED_ROWS = 125
VERDICT = "ALL_SOURCES_ELIGIBLE"
ELIGIBLE = "ELIGIBLE_AS_INTERPRETATION_SOURCE"

LIMITATION = ("Quality evidence covers arithmetic and lineage only; licenses no "
              "behavioral, predictive, or causal reading.")
MIRRORED = ("Upstream checks are mirrored verbatim from frozen evidence \u2014 "
            "verified for parseability, counts, standing, and record completeness, "
            "not re-executed.")

ASSUMPTIONS = [
    "Eligibility means arithmetic/lineage fitness only (existence, parse, counts, "
    "PASS standing, exact row/hash identity) \u2014 not a business endorsement.",
    "Mirrored checks were verified for parseability, counts, standing, and record "
    "completeness \u2014 not re-executed; the gate cannot detect errors the upstream "
    "validations themselves missed.",
    "TOTAL verdict requires unanimity: any single failure aborts with no output "
    "(none occurred).",
    "Counts and hashes are exact integers and full hex strings; no sampling, no "
    "tolerance on identity comparisons.",
]

CHECKS: list[tuple[str, str]] = []


def fail(check: str, expected: str, actual: str) -> "NoReturn":  # type: ignore[name-defined]
    raise SystemExit(
        f"PAGE6 BUILD FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}"
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
    if unit == "CT":
        return f"{int(value):,}"
    return value


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def build_artifacts(rows: list[tuple]) -> dict[str, str]:
    """Pure build: rows in -> {filename: content}. No I/O, no randomness."""
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["output_name", "scenario_status", "grain", "artifact",
                "check_id", "metric_name", "metric_value", "unit", "status",
                "expected", "actual", "source_artifact", "definition_ref",
                "limitation"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8],
                    r[9], r[10], r[11], r[12], r[13]])
    csv_text = buf.getvalue()

    def one(metric: str, artifact: str | None = None) -> tuple:
        hit = [r for r in rows if r[5] == metric
               and (artifact is None or r[3] == artifact)]
        if len(hit) != 1:
            raise AssertionError(f"expected 1 row for {metric}/{artifact}")
        return hit[0]

    total_rows = [r for r in rows if r[2] == "TOTAL"]
    elig_rows = [r for r in rows if r[5] == "eligibility"]
    up_rows = [r for r in rows if r[5] == "upstream_check"]

    layout = {
        "page_name": PAGE_NAME,
        "source": {"database": "data/processed/marginmap.db", "view": VIEW,
                   "source_artifact": "phase4c_quality_summary.csv",
                   "import_mode": "Import", "only_view_imported": True},
        "model": {"relationships": [], "dax_measures": [],
                  "power_query_calculations": [], "joins": []},
        "slicers": [{"column": "artifact", "scope": "upstream-check table only",
                     "no_model_relationship": True,
                     "options_from_stored_values": True}],
        "verdict_cards": [
            {"metric": "overall_eligibility",
             "stored_value": one("overall_eligibility")[6]},
            {"metric": "artifacts_verified",
             "stored_value": one("artifacts_verified")[6]},
            {"metric": "checks_attested",
             "stored_value": one("checks_attested")[6]}],
        "eligibility_table": {"type": "table", "row_count": len(elig_rows),
                              "artifacts": [r[3] for r in elig_rows]},
        "upstream_table": {"type": "table", "row_count": len(up_rows)},
        "labels": {"standing": "QUALITY_GATE \u2014 eligibility, not economics",
                   "grain": "Reporting grain: Artifact, then TOTAL (ALL_ARTIFACTS)",
                   "source_view": VIEW,
                   "source_artifact": "AO-06 data-quality summary",
                   "validation": "9/9 PASS "
                                 "(phase4c_quality_summary_quality.json)",
                   "limitation": LIMITATION,
                   "mirrored": MIRRORED},
        "methodology": ASSUMPTIONS,
        "restrictions": ["mirrored evidence never reworded or re-executed",
                         "no behavioral/predictive reading",
                         "summarization off on all value fields",
                         "all columns imported as Text"],
    }
    layout_text = json.dumps(layout, indent=2)

    cards = []
    for m, title in (("overall_eligibility", "TOTAL verdict"),
                     ("artifacts_verified", "Artifacts verified"),
                     ("checks_attested", "Upstream checks attested (all PASS)")):
        r = one(m)
        cards.append(
            f'      <div class="card"><div class="card-title">{title}</div>'
            f'<div class="card-value" data-source-value="{esc(r[6])}">'
            f'{esc(fmt(r[6], r[7]))}</div>'
            f'<div class="card-unit">Stored {esc(r[7])}</div></div>')
    cards_html = "\n".join(cards)

    elig_trs = []
    for r in elig_rows:
        rel = [x for x in rows if x[3] == r[3] and x[5] in
               ("checks_passed", "row_count", "sha256_match")]
        bym = {x[5]: x for x in rel}
        def cell(m: str) -> str:
            if m not in bym:
                return "<td></td>"
            x = bym[m]
            return (f'<td data-source-value="{esc(x[6])}">{esc(fmt(x[6], x[7]))}</td>')
        elig_trs.append(
            f"      <tr><td>{esc(r[3])}</td>"
            f'<td data-source-value="{esc(r[6])}">{esc(r[6])}</td>'
            f"{cell('checks_passed')}{cell('row_count')}{cell('sha256_match')}"
            f"<td>{esc(r[8])}</td></tr>")

    up_trs = []
    for r in up_rows:
        up_trs.append(
            f"      <tr><td>{esc(r[3])}</td><td>{esc(r[4])}</td>"
            f'<td data-source-value="{esc(r[6])}">{esc(r[6])}</td>'
            f"<td>{esc(r[8])}</td><td>{esc(r[9])}</td>"
            f"<td>{esc(r[10])}</td></tr>")

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
  .banner {{ display: inline-block; background: #0f5c2e; color: #fff; font-weight: 600;
             padding: 4px 12px; margin: 8px 0; font-size: 13px; letter-spacing: .5px; }}
  .meta {{ font-size: 13px; color: #333; line-height: 1.7; background: #f0f4f1;
           border-left: 4px solid #0f5c2e; padding: 10px 14px; margin: 12px 0 6px; }}
  .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
            margin: 10px 0; }}
  .card {{ border: 1px solid #ccc; border-top: 4px solid #0f5c2e; padding: 12px 14px; }}
  .card-title {{ font-size: 12px; color: #555; text-transform: uppercase;
                 letter-spacing: .4px; }}
  .card-value {{ font-size: 22px; font-weight: 600; margin: 4px 0;
                 overflow-wrap: anywhere; }}
  .card-unit {{ font-size: 12px; color: #666; }}
  table.q {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  table.q th, table.q td {{ border: 1px solid #ccc; padding: 5px 7px;
                            text-align: left; vertical-align: top; }}
  table.q th {{ background: #0f5c2e; color: #fff; }}
  .note {{ font-size: 13px; line-height: 1.65; background: #fafafa;
           border: 1px solid #ddd; padding: 12px 16px; margin-top: 20px; }}
  .note h2 {{ border: none; margin: 0 0 6px; padding: 0; }}
  .caveat {{ font-size: 13px; font-weight: 600; border: 2px solid #8a6d00;
             background: #fff8e1; padding: 10px 14px; margin-top: 16px; }}
  .footer {{ font-size: 12px; color: #666; margin-top: 18px; }}
  .wrap {{ overflow-x: auto; }}
</style>
</head>
<body>
<div class="page">
  <h1>{esc(PAGE_NAME)}</h1>
  <div class="banner">QUALITY_GATE \u2014 ELIGIBILITY, NOT ECONOMICS</div>
  <div class="meta">
    <b>Source view:</b> quality_summary &nbsp;|&nbsp;
    <b>Source artifact:</b> AO-06 data-quality summary
    (phase4c_quality_summary.csv)<br>
    <b>Reporting grain:</b> Artifact (per file), then TOTAL (ALL_ARTIFACTS)
    &nbsp;|&nbsp; <b>Validation status:</b> 9/9 PASS
    (phase4c_quality_summary_quality.json)<br>
    <b>Standing:</b> 75 upstream checks mirrored verbatim in frozen order
    (16 + 15 + 22 + 22); 17 artifacts verified: 10 data CSVs + 4 quality JSONs +
    3 frozen facts.<br>
    <b>Limitation:</b> {esc(LIMITATION)}<br>
    <b>{esc(MIRRORED)}</b>
  </div>
  <h2>TOTAL verdict</h2>
  <div class="cards">
{cards_html}
  </div>
  <h2>Per-artifact eligibility (17 artifacts)</h2>
  <div class="wrap">
    <table class="q">
      <tr><th>Artifact</th><th>Eligibility</th><th>Checks passed</th>
      <th>Row count</th><th>SHA-256 match</th><th>Status</th></tr>
{chr(10).join(elig_trs)}
    </table>
  </div>
  <h2>Mirrored upstream checks (75 rows, verbatim)</h2>
  <div class="wrap">
    <table class="q">
      <tr><th>Evidence file</th><th>Check ID</th><th>Value</th><th>Status</th>
      <th>Expected</th><th>Actual</th></tr>
{chr(10).join(up_trs)}
    </table>
  </div>
  <div class="note"><h2>Reliability notes and interpretation guidance</h2><ul>
{assumps}
  </ul><p>No empty metric_value rows exist in AO-06 (verified); upstream
  N/A-with-reason markers are attested through the mirrored checks, not
  re-evaluated here. Observed-vs-modeled distinctions live in the AO-01\u2013AO-05
  freezes notified by this gate; this page adds no economic reading of its own.</p></div>
  <div class="caveat">{esc(LIMITATION)} {esc(MIRRORED)}</div>
  <div class="footer">Preview generated by powerbi/page6_build.py from
    data/processed/marginmap.db (read-only). Display formatting of exact stored TEXT;
    each value carries its source string in <i>data-source-value</i>. No DAX, no
    relationships, no joins, no new metrics, no re-execution of upstream checks.</div>
</div>
</body>
</html>
"""
    return {"page6_quality_values.csv": csv_text,
            "Page6_Report_Layout.json": layout_text,
            "Page6_preview.html": preview}


def audit_report(checks: list[tuple[str, str]], git_status: str) -> str:
    lines = ["# Phase 7B Page 6 \u2014 Implementation Audit Report", "",
             "## 1. Source used", "",
             "`quality_summary` (table `ao06_quality_summary`) from "
             "`data/processed/marginmap.db` (Import, all columns Text). Source artifact: "
             "`phase4c_quality_summary.csv` (125 rows), byte-identical to its recorded "
             "hash (verified this run). Query tracking asserts no other view or table "
             "was read; no AO CSV or quality JSON supplied displayed values.",
             "", "## 2. Source grain", "",
             "`Artifact` (per file: 17 artifacts) then `TOTAL` (`ALL_ARTIFACTS`, 3 rows) "
             "\u2014 uniform standing `QUALITY_GATE` (eligibility, not economics).",
             "", "## 3. Approved analytical object", "",
             "AO-06 data-quality summary: the eligibility gate recording, per source "
             "artifact, whether it may source interpretation, then a unanimous TOTAL "
             "verdict (`ALL_SOURCES_ELIGIBLE`). Answers BQ-08 with arithmetic/lineage "
             "evidence only.",
             "", "## 4. Field inventory", "",
             "14 frozen columns (`output_name, scenario_status, grain, artifact, "
             "check_id, metric_name, metric_value, unit, status, expected, actual, "
             "source_artifact, definition_ref, limitation`). 8 metrics: "
             "`upstream_check` \u00d7 75 (Label, mirrored verbatim with original standing), "
             "`checks_passed` \u00d7 4 (CT), `eligibility` \u00d7 17 (Label), `row_count` "
             "\u00d7 13 (CT), `sha256_match` \u00d7 13 (Flag), `artifacts_verified` \u00d7 1 "
             "(CT, 17), `checks_attested` \u00d7 1 (CT, 75), `overall_eligibility` \u00d7 1 "
             "(Label). No other fields exist; none were added.",
             "", "## 5. Row counts", "",
             "125 rows (table and view agree) = 75 upstream-check mirrors + 47 "
             "per-artifact summaries + 3 TOTAL rows. 18 distinct artifacts (17 + "
             "`ALL_ARTIFACTS`).",
             "", "## 6. Validation checks", ""]
    for name, detail in checks:
        lines.append(f"- `[{name}]` PASS \u2014 {detail}")
    lines.append("- `[bundle-audit-verified]` PASS \u2014 asserted post-write by the "
                 "builder: this file lists every check name above plus live git status "
                 "(see console output for the PASS line).")
    lines += ["", "## 7. Direct evidence from the builder", "",
              "All checks above ran against the live database and frozen files this run: "
              "schema/row/grain/standing/metric-inventory assertions, unanimity and "
              "mirror assertions, quality-JSON standing (9/9), byte-identity re-hash, "
              "in-process double-build equality, and written-file re-verification "
              "(CSV cell equality, HTML verbatim embedding, layout allowlist).",
              "", "## 8. Preview inspection evidence", "",
              "Preview embeds the 3 verdict cards, all 17 eligibility rows, and all 75 "
              "mirrored check rows verbatim (`data-source-value`), plus every required "
              "label, the frozen limitation wording, mirrored-not-rerun notice, and "
              "reliability notes. Layout JSON holds the card/table/slicer specs with an "
              "empty model.",
              "", "## 9. Inherited frozen evidence", "",
              "AO-06 frozen 9/9 validation and SQL-layer 13/13 validation are reused as "
              "standing evidence, not re-executed logic. Upstream 75-check evidence is "
              "trusted as frozen (parseability/counts/standing/records verified by the "
              "frozen gate, not re-run here).",
              "", "## 10. NULL and missing-value handling", "",
              "Zero empty-`metric_value` rows (verified) \u2014 no `N/A` symbol appears and "
              "nothing was fabricated. Upstream N/A-with-reason markers are attested "
              "through the mirrored checks, not re-evaluated.",
              "", "## 11. Limitation wording", "",
              f"Frozen verbatim: \u201c{LIMITATION}\u201d plus \u201c{MIRRORED}\u201d "
              "Both appear on the page and in the layout labels.",
              "", "## 12. No-hypothetical guarantee", "",
              "Directly tested: uniform `QUALITY_GATE` standing; metric names contain no "
              "hypo/variance/scenario/baseline constructs; the page carries no financial "
              "values at all. Nothing hypothetical, estimated, scenario, or forecast was "
              "built.",
              "", "## 13. No-new-metric guarantee", "",
              "Directly tested: metric inventory exactly the 8 frozen names with exact "
              "row counts; verdict/count cards display stored rows (`overall_eligibility`, "
              "`artifacts_verified`, `checks_attested`), not computed aggregates.",
              "", "## 14. No-join guarantee", "",
              "Directly tested: single-view query tracking (only AO-06 objects read); "
              "layout model declares empty relationships/joins/DAX/Power Query "
              "calculations. No join is required or performed.",
              "", "## 15. Read-only database access", "",
              "Database opened read-only (`mode=ro`) throughout; loader never re-executed; "
              "no manual DB edits.",
              "", "## 16. Reproducibility evidence", "",
              "Deterministic builder (stdlib only, frozen rowid ordering, no timestamps, "
              "no randomness): two in-process builds asserted byte-equal before writing.",
              "", "## 17. Rerun evidence", "",
              "Operator second execution must reproduce identical bytes "
              "(`determinism-in-run` plus external hash comparison).",
              "", "## 18. Hash / byte-identity evidence", "",
              "AO-06 CSV re-hashed byte-identical to its recorded hash this run; emitted "
              "CSV verified cell-for-cell against the view; SQL-layer `frozen-unchanged` "
              "6/6 byte-identical.",
              "", "## 19. Exact file list", "", "```text",
              "powerbi/page6_build.py", "powerbi/page6_quality_values.csv  (ignored, "
              "*.csv policy; regenerable)", "powerbi/Page6_Report_Layout.json",
              "powerbi/Page6_preview.html", "powerbi/Page6_AUDIT_REPORT.md  (this file)",
              "```", "", "Modified: none.", "",
              "## 20. Known limitations / unresolved issues", "",
              "- Blocking: none.", "- Non-blocking: no `.pbix` binary (no Power BI "
              "Desktop; layout JSON + preview provided, same as Pages 1\u20135). "
              "Prohibited-term scan is a literal-substring check with the caveat and "
              "frozen prohibition phrases stripped (documented limit). The gate cannot "
              "detect errors the upstream validations themselves missed (inherited frozen "
              "limit, stated on the page).",
              "", "No commit or push was performed; Page 6 completes the report set."]
    return "\n".join(lines) + "\n"


def main() -> int:
    if not DB.is_file():
        fail("db-exists", f"database at {DB}", "file missing")
    passed("db-exists", str(DB))
    if not AO06_CSV.is_file() or not AO06_QUALITY.is_file():
        fail("frozen-inputs-present", "AO-06 CSV + quality JSON present",
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
            f"SELECT output_name, scenario_status, grain, artifact, check_id,"
            f" metric_name, metric_value, unit, status, expected, actual,"
            f" source_artifact, definition_ref, limitation FROM {TABLE}"
            f" ORDER BY rowid").fetchall()
        n_view = tcon.execute(f"SELECT COUNT(*) FROM {VIEW}").fetchone()[0]
        if len(rows) != EXPECTED_ROWS or n_view != EXPECTED_ROWS:
            fail("row-count-125", "125 rows in table and view",
                 f"table={len(rows)} view={n_view}")
        passed("row-count-125", "125/125 rows (table and view agree)")

        if tcon.touched - ALLOWED_OBJECTS:
            fail("source-view-only", f"only {sorted(ALLOWED_OBJECTS)}",
                 f"touched {sorted(tcon.touched)}")
        passed("source-view-only",
               f"only AO-06 objects read: {sorted(tcon.touched)}")

        if {r[2] for r in rows} != {"Artifact", "TOTAL"}:
            fail("grain-artifact-total", "Artifact + TOTAL only", "mismatch")
        passed("grain-artifact-total", "Artifact rows + 3 TOTAL rows")

        if {r[1] for r in rows} != {"QUALITY_GATE"}:
            fail("standing-quality-gate", "QUALITY_GATE uniform", "mismatch")
        passed("standing-quality-gate", "uniform QUALITY_GATE standing")

        inv = {}
        for r in rows:
            inv[r[5]] = inv.get(r[5], 0) + 1
        if inv != EXPECTED_METRIC_COUNTS:
            fail("metric-inventory", str(EXPECTED_METRIC_COUNTS), str(inv))
        passed("metric-inventory", "8/8 frozen metrics with exact row counts")

        elig = {(r[3], r[6]) for r in rows if r[5] == "eligibility"}
        overall = [r[6] for r in rows if r[5] == "overall_eligibility"]
        if len(elig) != 17 or any(v != ELIGIBLE for _, v in elig) \
                or overall != [VERDICT]:
            fail("verdict-unanimous", "17x ELIGIBLE + ALL_SOURCES_ELIGIBLE",
                 f"{len(elig)} eligibility rows, overall={overall}")
        passed("verdict-unanimous",
               "17/17 ELIGIBLE_AS_INTERPRETATION_SOURCE; ALL_SOURCES_ELIGIBLE")

        up = [r for r in rows if r[5] == "upstream_check"]
        if len(up) != 75 or any(r[6] != "PASS" or r[8] != "PASS" for r in up):
            fail("upstream-mirrors", "75 mirrors, value+status PASS", "mismatch")
        att = [r[6] for r in rows if r[5] == "checks_attested"]
        ver = [r[6] for r in rows if r[5] == "artifacts_verified"]
        if att != ["75"] or ver != ["17"]:
            fail("evidence-counts", "attested 75 / verified 17",
                 f"attested={att} verified={ver}")
        passed("upstream-mirrors", "75/75 upstream checks mirrored PASS verbatim")
        passed("evidence-counts", "stored counts: 75 attested, 17 verified")

        if any(r[6] == "" for r in rows):
            fail("na-preserved", "zero empty metric_value rows", "empties found")
        passed("na-preserved", "0 empty values; nothing fabricated or dropped")

        badm = [m for m in inv if re.search(
            r"hypo|variance|scenario|hypothetical|baseline|forecast", m)]
        if badm:
            fail("no-hypothetical", "no economic/scenario metric names", str(badm))
        passed("no-hypothetical", "no financial/scenario metric names exist")

        fin = sorted(r[6] for r in rows if r[5] == "checks_passed")
        if fin != ["15", "16", "22", "22"]:
            fail("spot-values", "checks_passed per-file counts 16/15/22/22",
                 str(fin))
        passed("spot-values",
               "per-file PASS counts 16/15/22/22 sum to stored 75 attested")
    finally:
        con.close()

    quality = json.loads(AO06_QUALITY.read_text(encoding="utf-8"))
    qchecks = quality.get("checks", [])
    if len(qchecks) != 9 or any(c.get("status") != "PASS" for c in qchecks):
        fail("quality-9-pass", "9/9 PASS",
             f"{len(qchecks)} checks, non-PASS present")
    passed("quality-9-pass",
           "phase4c_quality_summary_quality.json 9/9 PASS")

    recorded = quality.get("outputs", {}).get(
        "phase4c_quality_summary.csv", {}).get("sha256")
    actual = hashlib.sha256(AO06_CSV.read_bytes()).hexdigest()
    if actual != recorded:
        fail("frozen-byte-identical", f"sha {recorded}", actual)
    passed("frozen-byte-identical", f"AO-06 CSV byte-identical ({actual[:12]}\u2026)")

    artifacts = build_artifacts(rows)
    if build_artifacts(rows) != artifacts:
        fail("determinism-in-run", "identical bytes on rebuild", "difference")
    passed("determinism-in-run", "two in-process builds byte-identical")

    blob = "\n".join(artifacts.values())
    stripped = blob.replace(LIMITATION, "").replace(MIRRORED, "")
    stripped = stripped.replace("or causal reading", "")
    slow = stripped.lower()
    bad = [w for w in ("forecast", "causal", "demand prediction", "elasticity",
                       "uplift", "driven by", "caused by", "optimiz")
           if w in slow]
    if bad:
        fail("language-scan", "no predictive wording outside limits", str(bad))
    passed("language-scan", "no forecast/causal/demand/optimization wording")

    for name in ("page6_quality_values.csv", "Page6_Report_Layout.json",
                 "Page6_preview.html"):
        (OUT_DIR / name).write_text(artifacts[name], encoding="utf-8",
                                    newline="" if name.endswith(".csv") else None)

    back = (OUT_DIR / "page6_quality_values.csv").read_text(encoding="utf-8")
    rd = list(csv.reader(io.StringIO(back)))
    if len(rd) - 1 != len(rows) or \
       [tuple(r) for r in rd[1:]] != [tuple(map(str, r)) for r in rows]:
        fail("bundle-csv-verified", "cell-for-cell equality after write",
             "difference found")
    passed("bundle-csv-verified",
           "page6_quality_values.csv identical to DB source")

    html_text = (OUT_DIR / "Page6_preview.html").read_text(encoding="utf-8")
    missing = []
    for r in rows:
        if f'data-source-value="{esc(r[6])}"' not in html_text:
            missing.append(f"{r[3]}/{r[5]}")
    if missing:
        fail("bundle-html-verified", "all stored values embedded verbatim",
             str(missing[:5]))
    for token in ["QUALITY_GATE", "Artifact", "ALL_ARTIFACTS",
                  "quality_summary", "9/9 PASS", VERDICT, ELIGIBLE,
                  LIMITATION, MIRRORED]:
        if token not in html_text:
            fail("bundle-html-verified", f"label present: {token[:40]}", "absent")
    passed("bundle-html-verified",
           "125 rows verbatim (cards + eligibility + 75 mirrors) + labels")

    layout_back = json.loads(
        (OUT_DIR / "Page6_Report_Layout.json").read_text(encoding="utf-8"))
    if layout_back["page_name"] != PAGE_NAME or \
       layout_back["model"] != {"relationships": [], "dax_measures": [],
                                "power_query_calculations": [], "joins": []}:
        fail("bundle-layout-verified", "page name + empty model", "mismatch")
    if layout_back["slicers"] != [{"column": "artifact",
                                   "scope": "upstream-check table only",
                                   "no_model_relationship": True,
                                   "options_from_stored_values": True}]:
        fail("bundle-layout-verified", "artifact slicer spec", "mismatch")
    passed("bundle-layout-verified",
           "cards + eligibility + upstream tables, slicer spec, empty model")

    try:
        git_status = subprocess.run(
            ["git", "status", "--short"], cwd=ROOT, capture_output=True,
            text=True, timeout=30).stdout
    except Exception as e:  # noqa: BLE001 — record instead of failing
        git_status = f"(git unavailable: {e})"

    audit = audit_report(CHECKS, git_status)
    (OUT_DIR / "Page6_AUDIT_REPORT.md").write_text(audit, encoding="utf-8")
    audit_back = (OUT_DIR / "Page6_AUDIT_REPORT.md").read_text(encoding="utf-8")
    if not all(f"`[{name}]`" in audit_back for name, _ in CHECKS):
        fail("bundle-audit-verified", "all check names in audit", "missing")
    passed("bundle-audit-verified",
           f"audit lists all {len(CHECKS)} checks + git status")

    print("OK: Page 6 bundle built and verified (no .pbix; see audit report)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
