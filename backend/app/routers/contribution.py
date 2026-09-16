"""GET /api/contribution -- AO-02 discount-band contribution (read-only)."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from .. import database, schemas

router = APIRouter(tags=["Contribution"])

TABLE = "ao02_band_contribution"
COLUMNS = (
    "output_name, scenario_status, grain, basis, band, source_artifact,"
    " metric_name, metric_value, unit, definition_ref, limitation"
)
ALLOWED_FILTERS = {"band", "metric_name", "scenario_status", "basis"}


@router.get(
    "/api/contribution",
    response_model=schemas.ContributionList,
    summary="AO-02 contribution by discount band",
    description=(
        "Approved AO-02 band-contribution rows, read verbatim from SQLite. "
        "ORDER-basis rows are authoritative; LINE-basis rows are partial "
        "companions (see limitation text). No calculations are performed."
    ),
)
def list_contribution(
    band: str | None = Query(default=None, description="Exact band, e.g. B2 or TOTAL."),
    metric_name: str | None = Query(
        default=None, description="Exact metric_name, e.g. contribution_profit."
    ),
    scenario_status: str | None = Query(
        default=None, description="Exact scenario_status, e.g. OBSERVED BASELINE."
    ),
    basis: str | None = Query(
        default=None, description="Exact basis: ORDER (authoritative) or LINE (partial)."
    ),
) -> schemas.ContributionList:
    """Return AO-02 rows matching the exact-match filters."""
    try:
        where, params = database.build_where(
            {
                "band": band,
                "metric_name": metric_name,
                "scenario_status": scenario_status,
                "basis": basis,
            },
            ALLOWED_FILTERS,
        )
        rows = database.fetch_all(
            f"SELECT {COLUMNS} FROM {TABLE}{where} ORDER BY rowid", params
        )
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="database query failed")
    return schemas.ContributionList(
        data=[schemas.ContributionRecord(**r) for r in rows], count=len(rows)
    )
