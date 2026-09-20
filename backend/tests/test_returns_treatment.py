"""Returns/flag treatment tests (P1 remediation).

Locks OUTCOME C: return information is an order-level OBSERVED flag only.
- 296 YES orders / 800 lines / 1 UNKNOWN order (grain: order, not line).
- YES-order values are RETAINED as observed (no refund/reversal modeled).
- No refund/credit/reversal columns exist in the API contract.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def _db() -> Path:
    from app import database

    return database.resolve_db_path()


def test_return_grain_is_order_level():
    con = sqlite3.connect(f"file:{_db()}?mode=ro", uri=True)
    try:
        yes_orders = con.execute(
            "SELECT COUNT(DISTINCT order_id) FROM ao05_order_reading "
            "WHERE return_status = 'YES'").fetchone()[0]
        total_orders = con.execute(
            "SELECT COUNT(DISTINCT order_id) FROM ao05_order_reading").fetchone()[0]
        statuses = {r[0] for r in con.execute(
            "SELECT DISTINCT return_status FROM ao05_order_reading").fetchall()}
    finally:
        con.close()
    assert yes_orders == 296
    assert total_orders == 5009
    assert statuses <= {"YES", "NOT_RETURNED", "UNKNOWN"}


def test_returned_order_values_retained_not_reversed(client):
    res = client.get("/api/orders", params={
        "return_status": "YES", "metric_name": "net_revenue",
        "limit": 500, "offset": 0})
    assert res.status_code == 200
    body = res.json()
    assert body["data"], "expected retained YES-order rows"
    vals = [float(r["metric_value"]) for r in body["data"] if r["metric_value"] != ""]
    assert vals and all(v >= 0 for v in vals)
    assert sum(vals) > 0, "YES revenue must be retained, not zeroed"
    assert all(r["return_status"] == "YES" for r in body["data"])


def test_no_refund_columns_in_contract(client):
    res = client.get("/api/orders", params={"limit": 1, "offset": 0})
    assert res.status_code == 200
    row = res.json()["data"][0]
    for col in ("refund_amount", "returned_amount", "return_amount",
                "credit", "reversal", "returned_quantity"):
        assert col not in row, f"fabricated refund column leaked: {col}"
