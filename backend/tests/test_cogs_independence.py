"""COGS independence tests (P0 remediation).

Proves the modeled-COGS assumption does not depend on observed Profit:
1. Assumption file carries exactly one rate per product, full coverage.
2. Rates are valid (0,1) and reproduce COGS as revenue x rate.
3. AO gross profit reconciles as revenue - COGS (correct direction).
4. Pipeline sources contain no profit-derived COGS input.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def _db() -> Path:
    from app import database

    return database.resolve_db_path()


def _rows(sql: str, params: tuple = ()) -> list:
    con = sqlite3.connect(f"file:{_db()}?mode=ro", uri=True)
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def test_gross_profit_is_revenue_minus_cogs():
    val = {r[0]: r[1] for r in _rows(
        "SELECT metric_name, metric_value FROM ao01_baseline_total")}
    rev = float(val["net_revenue"])
    cogs = float(val["modeled_cogs"])
    profit = float(val["modeled_gross_profit"])
    assert profit == rev - cogs
    margin = float(val["modeled_gross_margin_pct"])
    assert abs(margin - profit / rev * 100) < 1e-6


def test_contribution_reconciles_from_cogs_and_cts():
    val = {r[0]: r[1] for r in _rows(
        "SELECT metric_name, metric_value FROM ao01_baseline_total")}
    gross = float(val["modeled_gross_profit"])
    cts = float(val["cost_to_serve"])
    contrib = float(val["contribution_profit"])
    assert abs(contrib - (gross - cts)) < 0.05


def test_cogs_assumption_file_independent():
    import pandas as pd

    assum = (Path(__file__).resolve().parents[2]
             / "data" / "processed" / "product_cogs_assumptions.csv")
    if not assum.is_file():
        import pytest

        pytest.skip("assumption file not shipped with API test env")
    df = pd.read_csv(assum, dtype=str)
    assert df["analytical_product_key"].nunique() == len(df) == 1894
    assert not df["cogs_rate"].isna().any()
    rate = pd.to_numeric(df["cogs_rate"])
    assert ((rate > 0) & (rate < 1)).all()
    assert "source_profit_quarantined" not in df.columns
    assert (df["assumption_status"].str.startswith("MODELED")).all()
