"""GET /api/variance -- AO-04 variance by discount band (read-only)."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from .. import database, schemas

router = APIRouter(tags=["Variance"])

TABLE = "ao04_band_variance"
COLUMNS = (
    "output_name, scenario_status, grain, scenario_id, band, block,"
    " source_artifact, metric_name, metric_value, unit, definition_ref, limitation"
)
ALLOWED_FILTERS = {"band", "scenario_status", "metric_name", "scenario_id", "block"}


@router.get(
    "/api/variance",
    response_model=schemas.VarianceList,
    summary="AO-04 variance by discount band",
    description=(
        "Approved AO-04 band-variance rows, read verbatim from SQLite. "
        "No thresholds or variance logic are invented here."
    ),
)
def list_variance(
    band: str | None = Query(default=None, description="Exact band, e.g. B5 or TOTAL."),
    scenario_status: str | None = Query(
        default=None, description="Exact scenario_status."
    ),
    metric_name: str | None = Query(
        default=None,
        description="Exact metric_name, e.g. variance_contribution.",
    ),
    scenario_id: str | None = Query(
        default=None, description="Exact scenario_id, e.g. uniform_replace_0.10."
    ),
    block: str | None = Query(
        default=None,
        description="Exact block: baseline, hypothetical, or variance.",
    ),
) -> schemas.VarianceList:
    """Return AO-04 rows matching the exact-match filters."""
    try:
        where, params = database.build_where(
            {
                "band": band,
                "scenario_status": scenario_status,
                "metric_name": metric_name,
                "scenario_id": scenario_id,
                "block": block,
            },
            ALLOWED_FILTERS,
        )
        rows = database.fetch_all(
            f"SELECT {COLUMNS} FROM {TABLE}{where} ORDER BY rowid", params
        )
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="database query failed")
    return schemas.VarianceList(
        data=[schemas.VarianceRecord(**r) for r in rows], count=len(rows)
    )
