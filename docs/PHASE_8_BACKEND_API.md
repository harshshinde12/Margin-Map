# Phase 8 Backend API — Read-Only Access Layer over Frozen Analytical Outputs

## 1. Objective

Build a production-style read-only backend API that exposes the already
approved analytical outputs (AO-01–AO-06) through a clean REST interface,
as the presentation / access layer between the frozen SQLite database and
the future React frontend. No analytical logic is recreated, no metric is
recomputed, and no frozen output is modified.

## 2. Architecture

```text
Frozen analytical outputs (Phase 4C CSVs, AO-01..AO-06)
        ↓  Phase 6 loader (sql/load_data.py)
SQLite database (data/processed/marginmap.db)
        ↓  Phase 8 backend (parameterized SELECT only)
FastAPI backend (backend/)
        ↓  JSON over HTTP
Future React frontend (later phase)
```

## 3. Backend structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, CORS, error handlers, router wiring
│   ├── database.py        # read-only connection + parameterized SELECT helpers
│   ├── schemas.py         # Pydantic response models (all TEXT fields -> str)
│   ├── dependencies.py    # limit/offset validation (HTTP 400 contract)
│   └── routers/
│       ├── __init__.py
│       ├── health.py      # GET /api/health
│       ├── baseline.py    # GET /api/baseline      (AO-01)
│       ├── contribution.py# GET /api/contribution  (AO-02)
│       ├── scenarios.py   # GET /api/scenarios     (AO-03)
│       ├── variance.py    # GET /api/variance      (AO-04)
│       ├── orders.py      # GET /api/orders        (AO-05, paginated)
│       └── quality.py     # GET /api/quality       (AO-06)
├── tests/                 # pytest suite (41 tests)
├── requirements.txt
├── README.md
└── .gitignore
```

`variance.py` is an addition to the recommended file list (which named six
routers for seven endpoint groups); it keeps one router per endpoint group.

## 4. Database source

`data/processed/marginmap.db` (Phase 6), read in `mode=ro` with
`PRAGMA query_only=ON`:

| Table | Rows | Grain | API endpoint |
| ----- | ---: | ----- | ------------ |
| `ao01_baseline_total` | 20 | TOTAL | `/api/baseline` |
| `ao02_band_contribution` | 238 | Overall × band (ORDER authoritative + LINE partial) | `/api/contribution` |
| `ao03_scenario_comparison` | 105 | Overall TOTAL per scenario instance | `/api/scenarios` |
| `ao04_band_variance` | 420 | Overall × band per scenario instance | `/api/variance` |
| `ao05_order_reading` | 60,108 | Order (`order_id`, 5,009 orders) | `/api/orders` |
| `ao06_quality_summary` | 125 | Artifact, then TOTAL verdict | `/api/quality` |

All columns are TEXT; API schemas keep them as `str` (empty-string N/A
markers, flag strings, and label values pass through verbatim). Reads use
`ORDER BY rowid` to preserve frozen file order.

## 5. Endpoint catalog

| Endpoint | Filters | Response |
| -------- | ------- | -------- |
| `GET /api/health` | — | `{status, database, read_only}` |
| `GET /api/baseline` | `metric_name` | `{data: BaselineMetric[], count}` |
| `GET /api/contribution` | `band`, `metric_name`, `scenario_status`, `basis` | `{data: ContributionRecord[], count}` |
| `GET /api/scenarios` | `scenario_status`, `metric_name`, `scenario_id`, `block` | `{data: ScenarioRecord[], count}` |
| `GET /api/variance` | `band`, `scenario_status`, `metric_name`, `scenario_id`, `block` | `{data: VarianceRecord[], count}` |
| `GET /api/orders` | `order_id`, `discount_band`, `return_status`, `neg_flag`, `metric_name`, `limit`, `offset` | `{data: OrderReading[], count, limit, offset}` |
| `GET /api/quality` | `artifact`, `status`, `check_id` | `{data: QualityCheck[], count}` |

`basis` (contribution), `scenario_id`/`block` (scenarios, variance) are
documented passthrough filters beyond the minimum spec set; they only
narrow the same verbatim `SELECT` and add no new logic.

## 6. Request parameters

- All string filters are exact-match (`=`), parameterized, and optional.
  Unknown values return empty `data`, never an error and never a
  reinterpretation.
- `limit` default 50, must be 1–500; `offset` default 0, must be >= 0.
  Violations return HTTP 400 with a JSON detail message (a dedicated
  validation handler maps query-parameter errors to 400 instead of the
  FastAPI default 422).
- Unknown routes return HTTP 404 JSON; unexpected failures return HTTP 500
  JSON. No stack traces or filesystem paths are ever exposed.

## 7. Response structure

- List endpoints: `{"data": [...], "count": N}`.
- Orders: `{"data": [...], "count": N, "limit": L, "offset": O}`
  (`count` = rows in this page).
- Health: `{"status": "ok", "database": "connected", "read_only": true}`.

## 8. Analytical fidelity rules

1. Expose, never recompute: each endpoint selects its frozen table's
   columns verbatim; there are no formulas, aggregations, thresholds,
   forecasts, or quality scores anywhere in `backend/`.
2. Units, limitations, definition refs, scenario statuses, and N/A
   empty-string markers are preserved field-for-field.
3. Scenario rows keep the frozen `HYPOTHETICAL_ARITHMETIC_SENSITIVITY`
   status; documentation and route descriptions call them arithmetic
   sensitivity outputs, never forecasts.
4. Order grain (`order_id`, `metric_name`) is never aggregated.
5. Fidelity is enforced by tests: unfiltered API counts equal SQL counts
   (20/238/105/420/125 + paged AO-05), and spot records match SQLite on
   `metric_name`/`metric_value`/`unit`/`limitation` (AO-01 contribution
   profit `565116.9418299999`; AO-03 uniform variance `95406.2413300001`;
   AO-04 uniform B5 variance `45401.369600000005`; AO-06 verdict
   `ALL_SOURCES_ELIGIBLE`).

## 9. Read-only guarantee

- `database.get_connection()` uses `file:...?mode=ro` + `PRAGMA query_only=ON`.
- Codebase scan: no `INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/`CREATE`
  executes anywhere under `backend/app/` (only `SELECT`).
- `test_integrity.py` snapshots SHA-256 + size + mtime + per-table counts,
  exercises every endpoint, and asserts byte-identity afterward.
- Observed integrity: SHA-256
  `b75c75f3f2b102b45874eccdc04d73d1e8bc99816933b1bb7e9957d17366272b`,
  size 17,211,392 bytes, counts 20/238/105/420/60108/125 — unchanged.

## 10. Testing strategy

`python -m pytest tests -q` from `backend/` — 41 tests:

- Health (3): 200, database connected, read-only flag.
- Baseline (5), contribution (5), scenarios (5), variance (4),
  orders (7), quality (4): availability, row counts, field presence,
  filter behavior, pagination, limit enforcement, offset, terminology.
- Integrity (1): byte-identity across a full endpoint sweep.
- Fidelity (7): count equality per endpoint + representative
  field-for-field spot checks against direct SQL.
- Plus live validation: Uvicorn launched locally; every endpoint, `/docs`,
  `/redoc`, error cases (400/404), and a SQL-injection probe exercised
  over real HTTP with the database verified unchanged afterward.

## 11. Known limitations

- String-typed passthrough: numeric-looking values stay strings by design
  (fidelity over convenience); clients cast if needed.
- Exact-match filters only; no search, sorting options, or range queries.
- Orders `count` is the page size, not the filtered total (a separate
  `COUNT(*)` is run but only the page is returned; the total is not
  exposed in the current envelope).
- CORS allows only local dev origins by default; no authentication (both
  deferred to a later phase per spec).
- `httpx`/`starlette` deprecation warning in test output (upstream
  packaging notice; no functional impact).

## 12. Future integration point with React

The React app (later phase) reads JSON from these seven `GET` endpoints
(typically via `http://localhost:8000` with CORS origin
`http://localhost:3000`), paginating `/api/orders` and using the list
filters for band/scenario/quality views. The OpenAPI contract at
`/openapi.json` (Swagger `/docs`, ReDoc `/redoc`) is the integration
reference. No backend change is needed for read-only display work.
