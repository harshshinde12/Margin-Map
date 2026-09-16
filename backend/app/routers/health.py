"""GET /api/health -- service and read-only database status."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import database, schemas

router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=schemas.HealthResponse, summary="Service health")
def health() -> schemas.HealthResponse:
    """Report API status and read-only database availability.

    Never exposes filesystem paths. Returns HTTP 500 (without internals)
    if the frozen database cannot be opened read-only.
    """
    try:
        con = database.get_connection()
    except Exception:
        raise HTTPException(status_code=500, detail="database unavailable")
    try:
        con.execute("SELECT 1").fetchone()
    except Exception:
        raise HTTPException(status_code=500, detail="database unavailable")
    finally:
        con.close()
    return schemas.HealthResponse(status="ok", database="connected", read_only=True)
