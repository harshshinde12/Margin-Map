"""GET /api/quality -- AO-06 data-quality summary (read-only)."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from .. import database, schemas

router = APIRouter(tags=["Quality"])

TABLE = "ao06_quality_summary"
COLUMNS = (
    "output_name, scenario_status, grain, artifact, check_id, metric_name,"
    " metric_value, unit, status, expected, actual, source_artifact,"
    " definition_ref, limitation"
)
ALLOWED_FILTERS = {"artifact", "status", "check_id"}


@router.get(
    "/api/quality",
    response_model=schemas.QualityList,
    summary="AO-06 data-quality summary",
    description=(
        "Approved AO-06 quality rows mirrored verbatim from upstream "
        "evidence. No quality scores or percentages are computed here."
    ),
)
def list_quality(
    artifact: str | None = Query(
        default=None, description="Exact artifact, e.g. phase3b_quality_report.json."
    ),
    status: str | None = Query(default=None, description="Exact status, e.g. PASS."),
    check_id: str | None = Query(
        default=None, description="Exact check_id, e.g. overall."
    ),
) -> schemas.QualityList:
    """Return AO-06 rows matching the exact-match filters."""
    try:
        where, params = database.build_where(
            {"artifact": artifact, "status": status, "check_id": check_id},
            ALLOWED_FILTERS,
        )
        rows = database.fetch_all(
            f"SELECT {COLUMNS} FROM {TABLE}{where} ORDER BY rowid", params
        )
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="database query failed")
    return schemas.QualityList(
        data=[schemas.QualityCheck(**r) for r in rows], count=len(rows)
    )
