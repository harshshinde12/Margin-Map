# Phase 8 Backend API — Audit Report

| CHECK | RESULT | EVIDENCE |
| ----- | ------ | -------- |
| Project structure | PASS | `backend/app/{main,database,schemas,dependencies}.py`, 7 routers, `backend/tests/` (10 files), `requirements.txt`, `README.md`, `.gitignore` all present |
| Endpoint availability | PASS | Live Uvicorn sweep: `/api/health`, `/baseline`, `/contribution`, `/scenarios`, `/variance`, `/orders`, `/quality` all 200; `/docs`, `/redoc`, `/openapi.json` all 200 |
| Schema validation | PASS | Pydantic models mirror frozen TEXT columns per table; field-presence tests assert full column sets; `ORDER BY rowid` preserves frozen order |
| Filter validation | PASS | Exact-match parameterized filters on allowlisted columns; unknown values return empty `data` (verified); `limit` 1–500 / `offset` >= 0 enforced with HTTP 400 (verified `limit=501`, `limit=0` → 400) |
| Pagination | PASS | `/api/orders` defaults `limit=50/offset=0`, pages differ, `LIMIT/OFFSET` applied in SQL; `limit=500/offset=60000` exercised live without incident |
| Database immutability | PASS | SHA-256 `b75c75f3…6272b`, 17,211,392 bytes, mtime unchanged, counts 20/238/105/420/60108/125 identical before/after pytest suite + live HTTP sweep |
| Analytical fidelity | PASS | Unfiltered API counts equal SQL counts for all 6 AOs; spot values match (`565116.9418299999`, `95406.2413300001`, `45401.369600000005`, `ALL_SOURCES_ELIGIBLE`); N/A strings, units, limitations, scenario terminology preserved |
| Test results | PASS | `python -m pytest tests -q` → **41 passed** (3 health + 5 baseline + 5 contribution + 5 scenarios + 4 variance + 7 orders + 4 quality + 1 integrity + 7 fidelity) |
| Documentation | PASS | `backend/README.md` (12 required sections), `docs/PHASE_8_BACKEND_API.md`, this audit, freeze record all written |
| Security baseline | PASS | Parameterized SQL only; injection probe (`' OR '1'='1`) returned 0 rows; no arbitrary-SQL/filesystem/write endpoint; no `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE` executes in `backend/app/`; 404/500 are clean JSON without traces; CORS restricted to local dev origins (GET only) |

No check failed. No failure was hidden; the two deviations from the letter
of the spec are documented here: (1) `variance.py` added as a seventh router
file since the recommended list named six files for seven endpoint groups;
(2) passthrough `basis`/`scenario_id`/`block` filters offered alongside the
minimum filter sets (same verbatim SELECT, narrowing only).
