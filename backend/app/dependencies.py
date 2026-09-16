"""Shared FastAPI dependencies (Phase 8)."""

from __future__ import annotations

from fastapi import HTTPException, Query

MAX_LIMIT = 500


def pagination(
    limit: int = Query(50, description="Max rows to return (1-500)."),
    offset: int = Query(0, description="Rows to skip (>= 0)."),
) -> tuple[int, int]:
    """Validate ``limit``/``offset`` and return them.

    Raises HTTP 400 (not the default 422) for out-of-range values so the
    API surface matches the Phase 8 error-handling contract.
    """
    if limit < 1 or limit > MAX_LIMIT:
        raise HTTPException(
            status_code=400, detail=f"limit must be between 1 and {MAX_LIMIT}"
        )
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")
    return limit, offset
