"""GET /api/baseline -- AO-01 baseline TOTAL metrics (read-only passthrough)."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from .. import database, schemas

router = APIRouter(tags=["Baseline"])

TABLE = "ao01_baseline_total"
COLUMNS = (
    "output_name, scenario_status, grain, source_artifact, metric_name,"
    " metric_value, unit, definition_ref, limitation"
)
ALLOWED_FILTERS = {"metric_name"}


@router.get(
    "/api/baseline",
    response_model=schemas.BaselineList,
    summary="AO-01 baseline metrics",
    description=(
        "Approved AO-01 baseline TOTAL metrics, read verbatim from the "
        "frozen SQLite table. No metrics are calculated here."
    ),
)
def list_baseline(
    metric_name: str | None = Query(
        default=None, description="Exact metric_name to return (e.g. net_revenue)."
    ),
) -> schemas.BaselineList:
    """Return AO-01 rows, optionally filtered to one metric_name."""
    try:
        where, params = database.build_where(
            {"metric_name": metric_name}, ALLOWED_FILTERS
        )
        rows = database.fetch_all(
            f"SELECT {COLUMNS} FROM {TABLE}{where} ORDER BY rowid", params
        )
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="database query failed")
    return schemas.BaselineList(
        data=[schemas.BaselineMetric(**r) for r in rows], count=len(rows)
    )
