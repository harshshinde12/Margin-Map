"""GET /api/orders -- AO-05 order-level readings (paginated, read-only).

Order grain is preserved: one row per (order_id, metric_name). Rows are
never aggregated and no summary metrics are computed here. Pagination is
mandatory so the 60k+ row table is never returned by default.
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import database, schemas
from ..dependencies import pagination

router = APIRouter(tags=["Orders"])

TABLE = "ao05_order_reading"
COLUMNS = (
    "output_name, scenario_status, grain, order_id, discount_band,"
    " return_status, neg_flag, ambiguity_note, source_artifact, metric_name,"
    " metric_value, unit, definition_ref, limitation"
)
ALLOWED_FILTERS = {
    "order_id",
    "discount_band",
    "return_status",
    "neg_flag",
    "metric_name",
}


@router.get(
    "/api/orders",
    response_model=schemas.OrdersPage,
    summary="AO-05 order-level readings",
    description=(
        "Approved AO-05 order-level rows at (order_id, metric_name) grain, "
        "read verbatim from SQLite with mandatory limit/offset pagination."
    ),
)
def list_orders(
    order_id: str | None = Query(default=None, description="Exact order_id."),
    discount_band: str | None = Query(
        default=None, description="Exact discount band, e.g. B0."
    ),
    return_status: str | None = Query(
        default=None, description="Exact return_status, e.g. NOT_RETURNED."
    ),
    neg_flag: str | None = Query(
        default=None, description="Exact neg_flag: True or False."
    ),
    metric_name: str | None = Query(
        default=None, description="Exact metric_name, e.g. contribution_profit."
    ),
    page: tuple[int, int] = Depends(pagination),
) -> schemas.OrdersPage:
    """Return one page of AO-05 rows in frozen file order."""
    limit, offset = page
    try:
        where, params = database.build_where(
            {
                "order_id": order_id,
                "discount_band": discount_band,
                "return_status": return_status,
                "neg_flag": neg_flag,
                "metric_name": metric_name,
            },
            ALLOWED_FILTERS,
        )
        total = database.fetch_count(f"SELECT COUNT(*) FROM {TABLE}{where}", params)
        rows = database.fetch_all(
            f"SELECT {COLUMNS} FROM {TABLE}{where} ORDER BY rowid LIMIT ? OFFSET ?",
            params + (limit, offset),
        )
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="database query failed")
    return schemas.OrdersPage(
        data=[schemas.OrderReading(**r) for r in rows],
        count=len(rows),
        limit=limit,
        offset=offset,
    )
