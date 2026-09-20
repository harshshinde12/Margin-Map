"""Database-immutability test (Phase 8).

Snapshots the frozen database (SHA-256, size, mtime, row counts),
exercises every read endpoint (including paginated order reads), then
asserts the database is byte-identical. The API opens SQLite in
read-only mode, so any write would fail loudly before this test could.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

TABLES = (
    "ao01_baseline_total",
    "ao02_band_contribution",
    "ao03_scenario_comparison",
    "ao04_band_variance",
    "ao05_order_reading",
    "ao06_quality_summary",
)

EXPECTED_COUNTS = {
    "ao01_baseline_total": 20,
    "ao02_band_contribution": 238,
    "ao03_scenario_comparison": 140,
    "ao04_band_variance": 560,
    "ao05_order_reading": 60108,
    "ao06_quality_summary": 145,
}


def _db_path() -> Path:
    from app import database

    return database.resolve_db_path()


def _snapshot() -> dict:
    db = _db_path()
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        counts = {
            t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES
        }
    finally:
        con.close()
    stat = db.stat()
    return {
        "sha256": hashlib.sha256(db.read_bytes()).hexdigest(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "counts": counts,
    }


def test_database_unchanged_by_api_reads(client):
    before = _snapshot()

    # Exercise every endpoint, including filters and paginated order reads.
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/baseline").status_code == 200
    assert client.get("/api/baseline", params={"metric_name": "net_revenue"}).status_code == 200
    assert client.get("/api/contribution", params={"band": "B2"}).status_code == 200
    assert client.get("/api/scenarios").status_code == 200
    assert client.get("/api/variance", params={"band": "B5"}).status_code == 200
    assert client.get("/api/orders", params={"limit": 50, "offset": 0}).status_code == 200
    assert client.get("/api/orders", params={"limit": 500, "offset": 60000}).status_code == 200
    assert client.get("/api/quality", params={"status": "PASS"}).status_code == 200

    after = _snapshot()
    assert after["sha256"] == before["sha256"]
    assert after["size"] == before["size"]
    assert after["mtime_ns"] == before["mtime_ns"]
    assert after["counts"] == before["counts"] == EXPECTED_COUNTS
