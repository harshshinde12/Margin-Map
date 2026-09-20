"""Margin Map read-only backend API (Phase 8).

Presentation / access layer over the frozen Phase 6 SQLite database.
Reads approved analytical outputs (AO-01..AO-06) verbatim; computes nothing.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .routers import baseline, contribution, health, orders, quality, scenarios, variance

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = REPO_ROOT / "frontend" / "dist"
_HAS_DIST = (DIST_DIR / "index.html").is_file()


def _cors_origins() -> list[str]:
    raw = os.environ.get("BACKEND_CORS_ORIGINS", "")
    if raw.strip():
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


app = FastAPI(
    title="Margin Map API",
    description=(
        "Read-only presentation layer over the frozen Margin Map SQLite "
        "database (AO-01..AO-06). All endpoints SELECT pre-approved rows "
        "verbatim; no profitability metrics, scenarios, or quality scores "
        "are calculated here."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_to_400(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return HTTP 400 (not the default 422) for bad query parameters."""
    return JSONResponse(status_code=400, content={"detail": "invalid query parameter"})


@app.exception_handler(Exception)
async def unhandled_to_500(request: Request, exc: Exception) -> JSONResponse:
    """Never leak stack traces or filesystem internals."""
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


app.include_router(health.router)
app.include_router(baseline.router)
app.include_router(contribution.router)
app.include_router(scenarios.router)
app.include_router(variance.router)
app.include_router(orders.router)
app.include_router(quality.router)


if _HAS_DIST:
    _assets_dir = DIST_DIR / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/", include_in_schema=False, summary="Margin Map UI")
    def serve_root() -> FileResponse:
        """Serve the React production build (same-origin with /api)."""
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/{path:path}", include_in_schema=False, summary="SPA fallback")
    def spa_fallback(path: str) -> FileResponse:
        """Serve built static files; fall back to index.html for React routes.

        /api/*, /docs, /redoc and /openapi.json are never intercepted here:
        unknown API paths fall through to the default 404 handler.
        Unknown React routes serve index.html so the React 404 page renders.
        """
        if (
            path.startswith("api/")
            or path in ("api", "docs", "redoc", "openapi.json")
            or path.startswith("docs/")
        ):
            raise HTTPException(status_code=404, detail="not found")
        candidate = DIST_DIR / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
else:

    @app.get("/", tags=["Health"], summary="API root")
    def root() -> dict:
        """Minimal pointer to the interactive docs."""
        return {"service": "margin-map-api", "docs": "/docs"}
