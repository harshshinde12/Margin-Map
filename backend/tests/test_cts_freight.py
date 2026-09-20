"""CTS/freight forensic tests (P1 remediation).

Locks the verified methodology:
- source completeness (US freight total),
- line-grain preservation (no multiplication),
- order-level uniqueness (deduped totals),
- no freight_order_total double-count in contribution,
- contribution identity revenue - COGS - freight,
- postal preservation (5-digit, 05408),
- returned/UNKNOWN freight retained as observed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

EXPECTED_FREIGHT = 238173.79
TOL = 0.05


def _db() -> Path:
    from app import database

    return database.resolve_db_path()


def _val(metric: str) -> float:
    con = sqlite3.connect(f"file:{_db()}?mode=ro", uri=True)
    try:
        return float(con.execute(
            "SELECT metric_value FROM ao01_baseline_total "
            "WHERE metric_name=?", (metric,)).fetchone()[0])
    finally:
        con.close()


def test_freight_total_reconciles():
    assert abs(_val("cost_to_serve") - EXPECTED_FREIGHT) < TOL


def test_contribution_identity():
    rev = _val("net_revenue")
    cogs = _val("modeled_cogs")
    cts = _val("cost_to_serve")
    contrib = _val("contribution_profit")
    assert abs(contrib - (rev - cogs - cts)) < TOL


def test_order_freight_unique_per_order():
    import pandas as pd

    order_csv = (Path(__file__).resolve().parents[2]
                 / "data" / "processed" / "order_margin_map_phase2.csv")
    if not order_csv.is_file():
        import pytest

        pytest.skip("order fact not shipped with API test env")
    o = pd.read_csv(order_csv, dtype=str)
    assert o["order_id"].nunique() == len(o) == 5009
    assert abs(pd.to_numeric(o["order_freight"]).sum() - EXPECTED_FREIGHT) < TOL


def test_line_freight_no_multiplication():
    import pandas as pd

    fact = (Path(__file__).resolve().parents[2]
            / "data" / "processed" / "fact_margin_map_phase2.csv")
    if not fact.is_file():
        import pytest

        pytest.skip("line fact not shipped with API test env")
    f = pd.read_csv(fact, usecols=["order_id", "freight_cost_observed",
                                   "freight_order_total"])
    line_sum = pd.to_numeric(f["freight_cost_observed"], errors="coerce").sum()
    # ambiguous NULL pair (25.05) is held at order level, not in line values
    assert abs(line_sum + 25.05 - EXPECTED_FREIGHT) < TOL
    # freight_order_total repeats per line: naive sum must exceed truth
    naive = pd.to_numeric(f["freight_order_total"], errors="coerce").sum()
    assert naive > EXPECTED_FREIGHT
    # deduped order totals reconcile exactly
    dedup = (f.drop_duplicates("order_id")["freight_order_total"]
             .pipe(pd.to_numeric).sum())
    assert abs(dedup - EXPECTED_FREIGHT) < TOL


def test_postal_preserved():
    import pandas as pd

    fact = (Path(__file__).resolve().parents[2]
            / "data" / "processed" / "fact_sales.csv")
    if not fact.is_file():
        import pytest

        pytest.skip("fact not shipped with API test env")
    p = pd.read_csv(fact, usecols=["postal_code"], dtype=str)["postal_code"]
    assert (p.str.len() == 5).all()
    assert int((p == "05408").sum()) == 11


def test_returned_freight_retained(client):
    body = client.get("/api/orders", params={
        "return_status": "YES", "metric_name": "freight_cost",
        "limit": 500, "offset": 0}).json()
    assert body["data"], "YES-order freight rows must be retained"
    assert all(r["return_status"] == "YES" for r in body["data"])
