# Margin Map Backend API (Phase 8)

## 1. Purpose

Read-only presentation / access layer over the frozen Margin Map analytical
outputs. The backend exposes AO-01–AO-06 (already approved, stored in SQLite
by Phase 6) through a clean REST interface for the future React frontend.
It computes nothing: every endpoint is a parameterized `SELECT` whose rows
are returned verbatim.

## 2. Architecture

```text
Frozen Phase 4C outputs (AO-01..AO-06 CSVs)
        ↓  (sql/load_data.py, Phase 6 -- not part of this backend)
data/processed/marginmap.db  (SQLite, read-only source)
        ↓  (parameterized SELECT, mode=ro + PRAGMA query_only=ON)
FastAPI backend (this directory)
        ↓  (JSON over HTTP)
Future React frontend
```

## 3. Requirements

- Python 3.10+ (built and tested on 3.14.7)
- Dependencies in `requirements.txt`: `fastapi`, `uvicorn`, `pydantic`
  (plus `pytest`, `httpx` for the test suite)
- The frozen database at `data/processed/marginmap.db` (rebuild with
  `python sql/load_data.py` from the repository root if absent; never
  committed to Git)

## 4. Installation

From the repository root:

```text
pip install -r backend/requirements.txt
```

## 5. Run command

Start from the **`backend/`** directory (documented startup location):

```text
cd backend
uvicorn app.main:app --reload
```

The database path is resolved relative to the repository structure
(`backend/../data/processed/marginmap.db`), so the API also works when
started from the repository root as `uvicorn backend.app.main:app` only if
`backend/` is on the Python path -- prefer the command above. Override with
`MARGINMAP_DB=/path/to/marginmap.db` if needed. CORS origins default to
`http://localhost:3000` and `http://127.0.0.1:3000`; override with
`BACKEND_CORS_ORIGINS=http://localhost:3000,https://example.com`.

## 6. API endpoints

| Method | Path | Source | Description |
| ------ | ---- | ------ | ----------- |
| GET | `/api/health` | — | Service + read-only DB status |
| GET | `/api/baseline` | AO-01 | Baseline TOTAL metrics (20 rows) |
| GET | `/api/contribution` | AO-02 | Contribution by discount band (238 rows) |
| GET | `/api/scenarios` | AO-03 | Scenario sensitivity at TOTAL (105 rows) |
| GET | `/api/variance` | AO-04 | Variance by discount band (420 rows) |
| GET | `/api/orders` | AO-05 | Order-level readings, paginated (60,108 rows) |
| GET | `/api/quality` | AO-06 | Data-quality summary (125 rows) |

## 7. Example requests

```text
GET /api/health
GET /api/baseline?metric_name=net_revenue
GET /api/contribution?band=B2
GET /api/contribution?metric_name=contribution_profit
GET /api/scenarios?scenario_status=HYPOTHETICAL_ARITHMETIC_SENSITIVITY
GET /api/variance?band=B5&scenario_id=uniform_replace_0.10
GET /api/orders?limit=50&offset=0
GET /api/orders?discount_band=B0&neg_flag=True&limit=50
GET /api/quality?status=PASS
GET /api/quality?artifact=ALL_ARTIFACTS
```

List endpoints return `{"data": [...], "count": N}`; orders returns
`{"data": [...], "count": N, "limit": L, "offset": O}`. Unknown filter
values return empty `data` (not an error). Invalid `limit`/`offset`
returns HTTP 400 with a JSON detail message; no stack traces are exposed.

## 8. Pagination

Only `/api/orders` is paginated (the 60k+ row table is never returned by
default). Defaults `limit=50, offset=0`; `limit` must be 1–500,
`offset` >= 0. Filters are applied in SQL (`WHERE` + `LIMIT`/`OFFSET`),
so pages reflect frozen file order (`ORDER BY rowid`).

## 9. Database source

`data/processed/marginmap.db`, tables `ao01_baseline_total`,
`ao02_band_contribution`, `ao03_scenario_comparison`,
`ao04_band_variance`, `ao05_order_reading`, `ao06_quality_summary`
(one per frozen AO; all columns TEXT). The backend reads these tables
directly with `ORDER BY rowid` to preserve frozen file order.

## 10. Read-only design

- Connections open with `file:...?mode=ro` plus `PRAGMA query_only=ON`.
- Only `SELECT` statements exist in the codebase (verified by scan).
- All user input travels as bound parameters; filter column names come
  from hardcoded allowlists, never from user input.
- No arbitrary-SQL, filesystem, or write endpoint exists.

## 11. Testing

From `backend/`:

```text
python -m pytest tests -q
```

41 tests: endpoint availability, field presence, filter behavior,
pagination/limit enforcement, database immutability (SHA-256 + size +
mtime + row counts before/after reads), and analytical fidelity
(API counts and spot values vs. direct SQL).

## 12. Swagger docs location

With the server running:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
