# Phase 10 End-to-End QA — Independent Release Verification

## 1. Objective

Independently verify whether Margin Map is genuinely ready to present as a
professional portfolio project across five dimensions: technical
correctness, analytical correctness, end-to-end data fidelity, UI/UX
quality, and engineering/repository/release quality. Every check below was
executed in this phase; prior-phase results were not taken on trust.

## 2. Architecture tested

SOURCE DATA → SQL/SQLite analytical layer → frozen AO-01..AO-06 →
FastAPI read-only API (`:8000`) → React frontend (`:3000`) → user.
Power BI (`powerbi/`) used as the analytical cross-reference layer.

## 3. Repository audit (Steps 1–2)

- Correct repo (`Margin Map`, branch `main`), tree initially clean,
  commits `9d352f3` (P7) / `8d13e43` (P8) / `e4bbc3f` (P9) present and
  pushed. No commit created in this phase.
- `C:\Users\Harsh Shinde\.git` is an empty, commit-less home-directory
  repo with no project work in it — unrelated, no action taken.
- Inventory: `backend/` (13 app + 10 test files), `frontend/src` (32
  source/test files), `sql/`, `data/processed/marginmap.db` (17,211,392
  bytes), 63 docs, 6 Power BI page bundles + `.pbix`. Local-only caches
  (`__pycache__`, `.pytest_cache`, `node_modules/`, `dist/`) exist on disk
  but are ignored and untracked.

## 4. Backend validation (Steps 3–5)

- `python sql/validate_sql_outputs.py`: 13/13 PASS (6/6 tables+views,
  61,016 rows byte-identical, spot values, N/A rows, status labels,
  75-check mirror fidelity, 5,009 orders, B0–B5+TOTAL, frozen CSVs
  unchanged).
- DB fingerprint `b75c75f3…6272b` matches the frozen value; mtime
  2026-09-14 unchanged after all QA traffic (no writes).
- Backend suite: **41 passed, 0 failed, 0 skipped** (2 pre-existing
  upstream `httpx`/`starlette` deprecation warnings, cosmetic).

## 5. API contract validation (Step 6)

Live `/openapi.json` route inventory: exactly 8 GET routes
(`/`, 7 API groups) — no POST/PUT/DELETE anywhere. All five list
endpoints return the exact frozen key sets with 100% string values and
`count == len(data)`; orders envelope is exactly
`{data,count,limit,offset}`; health returns the exact 3-field shape.
Frontend `src/api/types.ts` matches every key set field-for-field.

## 6. Frontend validation (Steps 8–10)

- Static scan: zero `sqlite3`/`readFile`/SQL-write/`.db` references in
  `src/` (only a doc comment and test-mock field values mention
  SQLite/CSV strings); exactly one `fetch(` call site
  (`api/client.ts:45`); `VITE_API_BASE_URL` referenced only there.
- Suite: **21/21 passed** (4 files). `npm run build`: clean
  (`tsc -b` + Vite, `dist/` emitted, JS 671,613 B / CSS 10,505 B).
- `npm run lint` (oxlint): clean, no findings.
- `npm install` and `pip install -r backend/requirements.txt` rerun from
  docs: both succeed (0 vulnerabilities reported by npm).

## 7. Browser validation (Steps 11–13, 27)

- Documented startup verified for both servers: backend
  (`uvicorn app.main:app --reload` from `backend/`) serves `/api/health`,
  `/docs`, `/openapi.json`; frontend (`npm run dev`) serves `:3000`
  with correct title and root mount — 19/19 route+endpoint checks.
- All 7 SPA routes + `/` + unknown route return 200 with the app shell
  (unknown routes render the client-side 404 page — verified rendering
  "Page not found.").
- Live-backend render probes (temporary, removed after): all 6 pages
  render real values with zero React warnings and empty stderr —
  12/12 passed (render + filter/pagination/empty-state wiring).
- Loading skeleton and error-card+Retry probes: 2/2 passed.
- Live browser pixel rendering and devtools console: **NOT VERIFIED**
  (no graphical browser in this environment). Indirect evidence: empty
  stderr across 33 render-bearing tests, clean build, valid semantic HTML.

## 8. Analytical reconciliation (Steps 14–19, 28)

API-vs-SQL full comparison: AO-01 all 20 metrics identical; AO-02 five
key metrics × B0–B5+TOTAL identical; AO-03 all 3 instances × 35 rows
identical; AO-04 uniform variance block (77 rows) identical; AO-05 sample
records (`CA-2014-100006`/wad `0.0`, contribution `82.7325`) and a
100-row page slice identical; AO-06 all 125 rows identical as an ordered
multiset (the `frozen` check_id pair is documented frozen-source design).
**ALL FIDELITY CHECKS PASSED.**

## 9. Power BI cross-check (Step 29)

Headline values agree across React → API → SQL → SQLite → Power BI
extracts: net revenue `2297200.8603000003`, contribution
`565116.9418299999`, uniform variance `95406.2413300001`, B5 variance
`45401.369600000005`, order wad `0.0`, verdict `ALL_SOURCES_ELIGIBLE`.
No discrepancy found at any layer.

## 10. Filter testing (Steps 15–20)

Every filter exercised live: basis/band/metric + reset (bands);
instance switch (scenarios); metric switch (variance); Apply/Reset,
impossible-value empty state + Clear Filters, page-size change
(orders); artifact filter + verdict hide/show + reset (quality).
Unknown values return empty data; no stale data, no wrong-dataset
effects, no percentage averaging (values are displayed per stored unit;
charts group single-unit metrics only).

## 11. Pagination testing (Step 18)

Default 50 (`Rows 1–50`), Next → `Rows 51–100`, Previous restores,
page-size 100 → `Rows 1–100`, server cap 500 verified live
(`limit=501` → 400). UI never claims the page count is the dataset
total; order grain preserved; no order-derived KPIs exist.

## 12. Failure-state testing (Steps 21–23)

Loading: skeletons (KPI/chart/table) render while fetches pend and are
replaced by data. Error: dead API renders "Unable to load analytical
data." + Retry, no Traceback, layout intact. Empty: impossible filter
renders "No records found." + Clear Filters — visually distinct from
errors. Malformed requests (`limit=0/abc/501`, `offset=-1`, unknown
routes/metrics, encoded injection and `DROP TABLE` probes): clean
400/404/empty responses, no crash, no mutation, no leaked paths.

## 13. Responsive testing (Step 24)

Verified by stylesheet + markup inspection: breakpoints at 1180/900/600
px, off-canvas sidebar with toggle + scrim, wrapping KPI grids,
horizontal table scroll containers, no page-level overflow sources.
**Actual rendered widths NOT VERIFIED** (no graphical browser) — the
rules are present and consistent; pixel confirmation is deferred to a
browser pass.

## 14. Accessibility testing (Step 26)

14 semantic/ARIA usages verified (`nav`, `aside`, `header`, `table` with
scoped `th`, labeled controls, `role=status/img/alert`, live regions on
filters/pager); native buttons/selects (keyboard-operable by
construction); `:focus-visible` outlines on all interactive elements;
polarity never color-only (signs, badges, labels accompany color).
**Live keyboard walkthrough NOT VERIFIED** (no browser); code-level
baseline passes.

## 15. Security/hygiene testing (Steps 7, 31)

Parameterized SQL only (allowlisted columns, bound values); injection
and DDL probes return 0 rows; POST → 405; CORS echoes only
`localhost:3000`/`127.0.0.1:3000`, denies other origins. Tracked tree
contains no `.env`, secrets, keys, machine paths, `node_modules`,
`dist`, caches, or `.db`; `.env.example` holds only the local API URL.
`.gitignore` coverage confirmed (`git status --ignored`).

## 16. Dependency review (Step 32)

Backend (5): `fastapi`/`uvicorn`/`pydantic` runtime, `pytest`/`httpx`
tests — all used, ranges reasonable. Frontend: `react`/`react-dom`/
`react-router-dom`/`recharts` — all used; dev/test toolchain all wired
to scripts. `oxlint` lint passes. Observation (no action):
`@testing-library/user-event` is installed but tests use `fireEvent` —
harmless standard companion, no churn justified.

## 17. Performance sanity check (Step 33)

No material risks: per-request short-lived read-only connections;
orders `COUNT(*)` + keyset page in SQL; charts ≤ 8 points; tables capped
(500 server / 25 client for quality); no polling; one 339-byte favicon
as the only image asset; quality page's second 125-row fetch is small
and documented. Deferred: bundle code-splitting (~672 KB, Recharts
dominated) — informational warning only.

## 18. Defects found

**Zero product defects.** All failures encountered during QA were bugs
in throwaway probe scripts (wrong `limit=` expectation, unencoded URLs,
console codepage handling, ambiguous test selectors, single-resolver
mock, dict-key collision on the documented AO-06 duplicate) — each
diagnosed, and product behavior confirmed correct in every case.

## 19. Fixes applied

None — no product file was modified in this phase (tree verified
identical to the frozen commits before documentation was added).

## 20. Final regression results

Post-final-state rerun: backend **41/41**, frontend **21/21**, build
clean, DB fingerprint unchanged (`b75c75f3…6272b`), working tree clean
except the two new Phase 10 documents.

## 21. Known limitations

- Live browser pixel rendering, devtools console, keyboard walkthrough,
  and rendered responsive widths are NOT VERIFIED here (no graphical
  browser); indirect evidence is strong but a browser pass is recommended
  before public demo.
- Unreferenced 5 KB `frontend/public/icons.svg` template leftover kept
  as-is (LOW, inert, no action per minimal-scope rule).
- `@testing-library/user-event` unused (LOW, no action).
- Bundle ~672 KB without code-splitting (informational).

## 22. Final release assessment

**PASS.** The product is technically correct, analytically faithful
(end-to-end identical from SQLite to screen and Power BI), robust to
malformed/hostile input, and documented reproducibly — every documented
command was re-executed verbatim in this phase. Recommended follow-up
(non-blocking): one graphical-browser pass for pixels/console/widths.
