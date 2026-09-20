"""Margin Map Phase 6 — validate the SQL data layer against frozen sources.

Every check reads the database and the frozen AO CSVs/quality JSONs
read-only and fails loudly on the first mismatch. Nothing is written
except the PASS summary printed to stdout.

Usage:
    python sql/validate_sql_outputs.py [--processed-dir DIR] [--db PATH]

Checks (unique IDs, deterministic ORDER BY rowid throughout):
    db-exists, tables-exist, views-exist, columns-match, row-counts,
    content-equal, spot-values, na-preserved, status-labels,
    order-coverage, band-coverage, frozen-unchanged.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEFAULT_DB = PROCESSED / "marginmap.db"

TABLES: tuple[tuple[str, str, str, int], ...] = (
    # (csv, quality json, table, expected rows)
    ("phase4c_baseline_total.csv", "phase4c_baseline_total_quality.json",
     "ao01_baseline_total", 20),
    ("phase4c_band_contribution.csv", "phase4c_band_contribution_quality.json",
     "ao02_band_contribution", 238),
    ("phase4c_scenario_comparison_total.csv",
     "phase4c_scenario_comparison_total_quality.json", "ao03_scenario_comparison", 140),
    ("phase4c_contribution_variance_by_band.csv",
     "phase4c_contribution_variance_by_band_quality.json", "ao04_band_variance", 560),
    ("phase4c_order_reading.csv", "phase4c_order_reading_quality.json",
     "ao05_order_reading", 60108),
    ("phase4c_quality_summary.csv", "phase4c_quality_summary_quality.json",
     "ao06_quality_summary", 145),
)

VIEWS = ("baseline_total", "contribution_by_band", "scenario_comparison_total",
         "variance_by_band", "order_reading", "quality_summary")

# (table, where-clause, metric, expected value) — key frozen figures.
SPOTS: tuple[tuple[str, str, str, str], ...] = (
    ("ao01_baseline_total", "metric_name='contribution_profit'",
     "contribution_profit", "565116.9418299999"),
    ("ao03_scenario_comparison",
     "scenario_id='uniform_replace_0.10' AND block='variance' "
     "AND metric_name='variance_contribution_profit'",
     "uniform variance", "95406.2413300001"),
    ("ao04_band_variance",
     "scenario_id='uniform_replace_0.10' AND band='B5' AND block='variance' "
     "AND metric_name='variance_contribution'",
     "uniform B5 variance", "45401.369600000005"),
    ("ao06_quality_summary",
     "grain='TOTAL' AND metric_name='overall_eligibility'",
     "overall eligibility", "ALL_SOURCES_ELIGIBLE"),
)

# Expected empty-value (N/A) row counts per table.
NA_EXPECTED = {"ao02_band_contribution": 14, "ao03_scenario_comparison": 8,
               "ao04_band_variance": 56}


def fail(check: str, expected: str, actual: str) -> "NoReturn":
    raise SystemExit(
        f"VALIDATION FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}"
    )


def passed(check: str, detail: str) -> None:
    print(f"PASS [{check}] {detail}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 6: validate SQL data layer.")
    p.add_argument("--processed-dir", type=Path, default=PROCESSED)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    return p.parse_args(argv)


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        return next(reader), [row for row in reader]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    proc, db_path = args.processed_dir, args.db

    if not db_path.is_file():
        fail("db-exists", f"database at {db_path}", "file missing")
    passed("db-exists", str(db_path))
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        have_tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        have_views = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='view'")}
        for _, _, table, _ in TABLES:
            if table not in have_tables:
                fail("tables-exist", f"table {table}", "missing")
        passed("tables-exist", "6/6 tables present")
        view_base = {"baseline_total": "ao01_baseline_total",
                     "contribution_by_band": "ao02_band_contribution",
                     "scenario_comparison_total": "ao03_scenario_comparison",
                     "variance_by_band": "ao04_band_variance",
                     "order_reading": "ao05_order_reading",
                     "quality_summary": "ao06_quality_summary"}
        for view in VIEWS:
            if view not in have_views:
                fail("views-exist", f"view {view}", "missing")
            n_view = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
            n_base = con.execute(
                f"SELECT COUNT(*) FROM {view_base[view]}").fetchone()[0]
            if n_view != n_base:
                fail("views-exist", f"view {view} matches {view_base[view]}",
                     f"view={n_view} base={n_base}")
        passed("views-exist", "6/6 views present with full row coverage")

        for csv_name, json_name, table, expected_rows in TABLES:
            header, data_rows = read_csv_rows(proc / csv_name)
            table_cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
            if table_cols != header:
                fail("columns-match", f"{table} columns {table_cols}",
                     f"CSV header {header}")
            db_rows = con.execute(
                f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            if len(db_rows) != expected_rows or len(data_rows) != expected_rows:
                fail("row-counts",
                     f"{table}/{csv_name} {expected_rows} rows",
                     f"db={len(db_rows)} csv={len(data_rows)}")
            if [list(map(str, r)) for r in db_rows] != data_rows:
                fail("content-equal", f"{table} byte-identical content to {csv_name}",
                     "cell mismatch found")
        passed("columns-match", "6/6 headers match CSVs")
        passed("row-counts", "20/238/140/560/60108/145 in db and CSVs")
        passed("content-equal", "all 61,211 rows identical to frozen CSVs")

        for table, where, label, expected in SPOTS:
            actual = con.execute(
                f"SELECT metric_value FROM {table} WHERE {where}").fetchone()[0]
            if actual != expected:
                fail("spot-values", f"{label} {expected}", repr(actual))
        passed("spot-values", "AO-01 contrib / AO-03 uniform var / AO-04 B5 var / AO-06 verdict match")

        for table, expected_na in NA_EXPECTED.items():
            n_na = con.execute(
                f"SELECT COUNT(*) FROM {table} WHERE metric_value=''").fetchone()[0]
            if n_na != expected_na:
                fail("na-preserved", f"{table} {expected_na} empty N/A rows", str(n_na))
        passed("na-preserved", "14/8/56 empty N/A rows with reasons intact")

        statuses = {r[0] for r in con.execute(
            "SELECT DISTINCT scenario_status FROM ao03_scenario_comparison")}
        if statuses != {"OBSERVED BASELINE", "HYPOTHETICAL_ARITHMETIC_SENSITIVITY"}:
            fail("status-labels", "baseline/hypothetical separation", repr(statuses))
        passed("status-labels", "observed/hypothetical layers separate")

        mirror = {"phase3b_quality_report.json": 16,
                  "phase4b_scenario_uniform_0.10_quality.json": 15,
                  "phase4b_scenario_uniform_0.20_quality.json": 15,
                  "phase4b_scenario_increase_0.00_quality.json": 22,
                  "phase4b_scenario_decrease_0.00_quality.json": 22}
        for artifact, expected_n in mirror.items():
            got = con.execute(
                "SELECT check_id FROM ao06_quality_summary WHERE artifact=? "
                "AND metric_name='upstream_check' ORDER BY rowid", (artifact,)).fetchall()
            want = [c.get("id") for c in json.loads(
                (proc / artifact).read_text(encoding="utf-8")).get("checks", [])]
            if [r[0] for r in got] != want or len(got) != expected_n:
                fail("mirror-fidelity", f"{artifact} mirrors {expected_n} upstream checks",
                     f"{len(got)} rows mirrored")
        passed("mirror-fidelity", "90 upstream checks mirrored verbatim in order")

        n_orders = con.execute(
            "SELECT COUNT(DISTINCT order_id) FROM ao05_order_reading").fetchone()[0]
        if n_orders != 5009:
            fail("order-coverage", "5009 distinct orders", str(n_orders))
        bands = con.execute(
            "SELECT DISTINCT band FROM ao04_band_variance ORDER BY band").fetchall()
        if [b[0] for b in bands] != ["B0", "B1", "B2", "B3", "B4", "B5", "TOTAL"]:
            fail("band-coverage", "B0-B5 + TOTAL", repr(bands))
        passed("order-coverage", "5009 distinct orders")
        passed("band-coverage", "B0-B5 + TOTAL, no other bands")

        for csv_name, json_name, _, _ in TABLES:
            quality = json.loads((proc / json_name).read_text(encoding="utf-8"))
            recorded = quality.get("outputs", {}).get(csv_name, {}).get("sha256")
            if sha256(proc / csv_name) != recorded:
                fail("frozen-unchanged", f"{csv_name} recorded sha", "bytes differ")
        passed("frozen-unchanged", "6/6 AO CSVs byte-identical to quality records")
    finally:
        con.close()
    print("OK: all Phase 6 SQL validation checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
