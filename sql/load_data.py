"""Margin Map Phase 6 — load frozen Phase 4C outputs into SQLite.

Reads the six frozen AO CSVs read-only, verifies each file's bytes
against the SHA-256 recorded in its own quality JSON (chain-of-custody),
then rebuilds the database deterministically: fresh file, schema first,
rows in frozen file order, views last. No frozen file is written.

Usage:
    python sql/load_data.py [--processed-dir DIR] [--db PATH]

The default database path is data/processed/marginmap.db. The database
is a local rebuildable artifact: regenerate it any time with this
script; do not treat it as a frozen source.
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
SQL_DIR = ROOT / "sql"
DEFAULT_DB = PROCESSED / "marginmap.db"

# (csv, quality json, table) — the six frozen Phase 4C outputs, in AO order.
SOURCES: tuple[tuple[str, str, str], ...] = (
    ("phase4c_baseline_total.csv", "phase4c_baseline_total_quality.json",
     "ao01_baseline_total"),
    ("phase4c_band_contribution.csv", "phase4c_band_contribution_quality.json",
     "ao02_band_contribution"),
    ("phase4c_scenario_comparison_total.csv",
     "phase4c_scenario_comparison_total_quality.json", "ao03_scenario_comparison"),
    ("phase4c_contribution_variance_by_band.csv",
     "phase4c_contribution_variance_by_band_quality.json", "ao04_band_variance"),
    ("phase4c_order_reading.csv", "phase4c_order_reading_quality.json",
     "ao05_order_reading"),
    ("phase4c_quality_summary.csv", "phase4c_quality_summary_quality.json",
     "ao06_quality_summary"),
)


def fail(check: str, expected: str, actual: str) -> "NoReturn":
    raise SystemExit(
        f"LOAD FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}"
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 6: load frozen AO CSVs into SQLite.")
    p.add_argument("--processed-dir", type=Path, default=PROCESSED)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    proc, db_path = args.processed_dir, args.db

    # ---- 1. chain-of-custody: every CSV verified before loading ---------------
    staged: list[tuple[str, list[str], list[list[str]]]] = []
    for csv_name, json_name, table in SOURCES:
        csv_path, json_path = proc / csv_name, proc / json_name
        if not csv_path.is_file():
            fail("inputs-exist", f"{csv_name} present", "file missing")
        if not json_path.is_file():
            fail("inputs-exist", f"{json_name} present", "file missing")
        try:
            quality = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            fail("evidence-parse", f"{json_name} valid JSON", f"parse error: {e}")
        recorded = quality.get("outputs", {}).get(csv_name, {}).get("sha256")
        digest = sha256(csv_path)
        if digest != recorded:
            fail("quality-chain", f"{csv_name} sha {recorded}", digest)
        checks = quality.get("checks", [])
        if any(c.get("status") != "PASS" for c in checks):
            bad = [c.get("id") for c in checks if c.get("status") != "PASS"]
            fail("upstream-standing", f"all {json_name} checks PASS",
                 f"non-PASS: {bad}")
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            data_rows = [row for row in reader]
        if any(len(r) != len(header) for r in data_rows):
            fail("csv-shape", f"{csv_name} uniform width {len(header)}",
                 "ragged row found")
        staged.append((table, header, data_rows))

    # ---- 2. rebuild database deterministically ----------------------------------
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
        for table, header, data_rows in staged:
            table_cols = [r[1] for r in con.execute(
                f"PRAGMA table_info({table})")]
            if table_cols != header:
                con.close()
                fail("schema-match",
                     f"{table} columns {table_cols}", f"CSV header {header}")
            con.executemany(
                f"INSERT INTO {table} ({', '.join(header)}) "
                f"VALUES ({', '.join('?' * len(header))})", data_rows)
        con.executescript((SQL_DIR / "views.sql").read_text(encoding="utf-8"))
        con.commit()
    finally:
        con.close()
    print(f"OK: loaded {sum(len(d) for _, _, d in staged)} rows into {db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
