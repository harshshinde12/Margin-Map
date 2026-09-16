"""Analytical-fidelity tests (Phase 8).

For each endpoint: API row count == SQL source row count (unfiltered),
and representative records match the SQLite source field-for-field
(metric_name / metric_value / unit / limitation). No silent transforms.
"""

from __future__ import annotations

import sqlite3

import pytest

TABLE_OF = {
    "baseline": "ao01_baseline_total",
    "contribution": "ao02_band_contribution",
    "scenarios": "ao03_scenario_comparison",
    "variance": "ao04_band_variance",
    "quality": "ao06_quality_summary",
}

EXPECTED_TOTALS = {
    "baseline": 20,
    "contribution": 238,
    "scenarios": 105,
    "variance": 420,
    "quality": 125,
}


def _direct(table: str, where: str = "", params: tuple = ()):
    from app import database

    db = database.resolve_db_path()
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(f"SELECT * FROM {table}{where}", params)]
    finally:
        con.close()


@pytest.mark.parametrize("endpoint,table", list(TABLE_OF.items()))
def test_unfiltered_count_matches_sql(client, endpoint, table):
    api = client.get(f"/api/{endpoint}").json()
    sql = _direct(table)
    assert api["count"] == len(sql) == EXPECTED_TOTALS[endpoint]


def test_orders_filtered_count_matches_sql(client):
    api = client.get(
        "/api/orders", params={"discount_band": "B0", "limit": 500}
    ).json()
    sql = _direct("ao05_order_reading", " WHERE discount_band = ?", ("B0",))
    assert api["count"] == min(500, len(sql))
    assert len(sql) > 500  # filter is genuinely selective


def test_fidelity_spot_values(client):
    # AO-01 contribution profit
    row = client.get("/api/baseline", params={"metric_name": "contribution_profit"}).json()["data"][0]
    sql = _direct("ao01_baseline_total", " WHERE metric_name = ?", ("contribution_profit",))[0]
    for f in ("metric_name", "metric_value", "unit", "limitation"):
        assert row[f] == sql[f]
    assert row["metric_value"] == "565116.9418299999"

    # AO-02 sample: ORDER/B0/net_revenue
    api_rows = client.get(
        "/api/contribution",
        params={"band": "B0", "metric_name": "net_revenue"},
    ).json()["data"]
    sql_rows = _direct(
        "ao02_band_contribution", " WHERE band = ? AND metric_name = ?", ("B0", "net_revenue")
    )
    assert len(api_rows) == len(sql_rows) >= 1
    for f in ("metric_name", "metric_value", "unit", "limitation"):
        assert api_rows[0][f] == sql_rows[0][f]

    # AO-03 uniform variance
    api_rows = client.get(
        "/api/scenarios",
        params={"scenario_id": "uniform_replace_0.10", "block": "variance",
                "metric_name": "variance_contribution_profit"},
    ).json()["data"]
    assert len(api_rows) >= 1
    assert api_rows[0]["metric_value"] == "95406.2413300001"

    # AO-04 uniform B5 variance
    api_rows = client.get(
        "/api/variance",
        params={"scenario_id": "uniform_replace_0.10", "band": "B5",
                "block": "variance", "metric_name": "variance_contribution"},
    ).json()["data"]
    assert len(api_rows) == 1
    assert api_rows[0]["metric_value"] == "45401.369600000005"

    # AO-05 sample order row passthrough
    api_rows = client.get(
        "/api/orders",
        params={"order_id": "CA-2014-100006", "metric_name": "wad", "limit": 5},
    ).json()["data"]
    assert len(api_rows) == 1
    sql_rows = _direct(
        "ao05_order_reading", " WHERE order_id = ? AND metric_name = ?",
        ("CA-2014-100006", "wad"),
    )
    for f in ("metric_name", "metric_value", "unit", "limitation", "discount_band"):
        assert api_rows[0][f] == sql_rows[0][f]

    # AO-06 overall eligibility verdict
    api_rows = client.get(
        "/api/quality",
        params={"artifact": "ALL_ARTIFACTS", "check_id": "overall"},
    ).json()["data"]
    assert any(r["metric_value"] == "ALL_SOURCES_ELIGIBLE" for r in api_rows)
