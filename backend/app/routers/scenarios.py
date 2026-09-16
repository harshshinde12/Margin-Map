"""GET /api/scenarios -- AO-03 scenario sensitivity (read-only).

Terminology preserved: rows with scenario_status
``HYPOTHETICAL_ARITHMETIC_SENSITIVITY`` are arithmetic sensitivity
outputs under stated assumptions, not forecasts.
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from .. import database, schemas

router = APIRouter(tags=["Scenarios"])

TABLE = "ao03_scenario_comparison"
COLUMNS = (
    "output_name, scenario_status, grain, scenario_id, block, source_artifact,"
    " metric_name, metric_value, unit, definition_ref, limitation"
)
ALLOWED_FILTERS = {"scenario_status", "metric_name", "scenario_id", "block"}


@router.get(
    "/api/scenarios",
    response_model=schemas.ScenarioList,
    summary="AO-03 scenario sensitivity at TOTAL",
    description=(
        "Approved AO-03 scenario-comparison rows (baseline / hypothetical / "
        "variance blocks), read verbatim from SQLite. Scenario differences "
        "are NOT computed here; hypothetical values are arithmetic "
        "sensitivity outputs, not forecasts."
    ),
)
def list_scenarios(
    scenario_status: str | None = Query(
        default=None,
        description="Exact scenario_status, e.g. HYPOTHETICAL_ARITHMETIC_SENSITIVITY.",
    ),
    metric_name: str | None = Query(
        default=None, description="Exact metric_name, e.g. contribution_profit."
    ),
    scenario_id: str | None = Query(
        default=None, description="Exact scenario_id, e.g. uniform_replace_0.10."
    ),
    block: str | None = Query(
        default=None,
        description="Exact block: baseline, hypothetical, or variance.",
    ),
) -> schemas.ScenarioList:
    """Return AO-03 rows matching the exact-match filters."""
    try:
        where, params = database.build_where(
            {
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
    return schemas.ScenarioList(
        data=[schemas.ScenarioRecord(**r) for r in rows], count=len(rows)
    )
