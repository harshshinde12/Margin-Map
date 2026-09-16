# Phase 9 React Frontend — Presentation & Interaction Layer

## 1. Objective

Build a polished, production-style React frontend for the frozen Margin Map
analytics system — a finance/profitability analytics product presentable in
a portfolio, interview, or case-study demo. The frontend is strictly the
presentation and interaction layer: it reads the Phase 8 FastAPI endpoints
and displays their values verbatim.

## 2. Architecture

```text
SQLite (frozen AO-01..AO-06)
        ↓  parameterized SELECT (Phase 8)
FastAPI backend :8000  (single source of truth)
        ↓  JSON over HTTP (GET only)
React frontend :3000  (this phase — displays only)
```

Non-negotiables enforced: no direct SQLite access, no CSV reading, no SQL
recreation in React, no duplicated formulas, no invented KPIs/thresholds/
forecasts/causal claims, no backend logic changes. Verified by source scan
(only documentation comments mention SQLite/CSV; test mocks mirror API
field values without reading files).

## 3. Frontend stack

React 19, TypeScript, Vite 8, React Router 7, Recharts 3, hand-authored CSS
design system (`src/styles/global.css`), Vitest + Testing Library + jsdom.
No UI kit, no state-management library, no animation library.

## 4. Page structure

- `/` → redirect `/executive`
- `/executive` — AO-01: 5 primary KPI cards (Net Revenue, Modeled Gross
  Profit, Contribution Profit, Contribution Margin, Cost to Serve) rendered
  only when present in the response; 4 context KPIs (orders, lines,
  realization, WAD); horizontal currency bar chart of stored CUR metrics;
  full 20-row detail table with definitions/limitations.
- `/discount-bands` — AO-02: basis/band/metric filters with reset and
  active-filter chips; per-band bar chart with gray TOTAL reference bar;
  KPI spotlights; long-format detail table with TOTAL pinned.
- `/scenarios` — AO-03: instance selector; grouped baseline-vs-hypothetical
  bars over metrics present in both blocks with CUR unit (data-driven
  intersection, 6 metrics for uniform_0.10); stored variance-block table;
  standing caveat strip ("not a forecast…").
- `/variance` — AO-04: instance + variance-metric selectors; diverging
  green/red diverging bars with zero reference line and gray TOTAL;
  band detail table with signed currency.
- `/orders` — AO-05: Apply/Reset filter model (order ID, band, return,
  neg flag, metric), 50/100/250/500 page sizes, prev/next pager, sticky
  headers, unit-aware formatting, neg-flag and ambiguity rendering. No
  aggregate KPIs derived from order rows.
- `/quality` — AO-06: verdict cards from `ALL_ARTIFACTS` rows (17
  artifacts, 75 checks, `ALL_SOURCES_ELIGIBLE`); artifact/status filters
  (options from an unfiltered fetch so selection never collapses the
  dropdown); 125-row table with status badges and 25-per-page pager.
- `*` — professional 404 with a return link.

## 5. API integration

`src/api/client.ts` is the only module that calls `fetch`; base URL from
`VITE_API_BASE_URL` (default `http://127.0.0.1:8000`, `.env.example`
provided). Network failures, HTTP 400/404/5xx, and JSON parse failures map
to typed `ApiError`s with user-safe messages. `src/api/types.ts` mirrors
the Phase 8 Pydantic schemas (all analytical fields `string`).
`src/hooks/useApi.ts` provides loading/error/retry state while keeping
layout mounted for skeleton stability.

## 6. Component architecture

```text
src/
├── api/          client.ts, types.ts
├── hooks/        useApi.ts
├── utils/        format.ts (+ tests)
├── components/
│   ├── layout/   AppShell (sidebar + API status + mobile nav), PageHeader
│   ├── kpi/      KpiCard
│   ├── charts/   ChartCard, theme.ts (shared palette)
│   ├── tables/   DataTable (sticky headers, numeric alignment, TOTAL rows),
│   │             Pagination
│   ├── filters/  FilterBar (SelectField, TextField)
│   ├── common/   StatusBadge
│   └── states/   LoadingSkeleton, ErrorState, EmptyState
├── pages/        Executive, DiscountBands, Scenarios, Variance,
│                 Orders, Quality, NotFound
├── styles/       global.css (tokens, shell, cards, tables, responsive)
└── test/         setup.ts, routing.test.tsx
```

No page duplicates UI logic; tables, pagination, filters, and states are
fully shared.

## 7. Design system

Deep navy/charcoal sidebar (`#101c2e`), muted blue primary (`#2563a8`),
restrained teal emphasis (`#0f766e`), light neutral app background,
subtle gray borders, tabular numerals for financial values. Semantics are
global: green = positive, red = negative, amber = warning/quality,
blue/teal = analytical emphasis. Typography hierarchy runs application
title → page title → lede → section heading → KPI value/label → chart
title → table header/value → helper text. Interactions are restrained
(hover states, active nav, 120 ms transitions, shimmer skeletons); no
gradients, shadows-for-show, 3D, or motion for its own sake.

## 8. Validation

- `npm run build` — `tsc -b` + Vite production bundle: clean
  (`dist/` ~672 KB minified JS incl. Recharts; chunk-size notice only).
- `npm test` — 21/21 passing (formatting, client, components, routing).
- Fidelity sweep against the live backend — 19/19: baseline count and
  headline values, ORDER row counts, B0–B5+TOTAL bands, 35 scenario rows
  per instance, 3 blocks, grouped-chart metric availability, stored
  variance values (`95406.2413300001`, B5 `45401.369600000005`), order
  pagination (50 default / 500 max), quality verdicts (17/75/eligible).
- Production preview serves `index.html` + favicon correctly (200).
- Responsive: sidebar collapses under 900 px, KPI grids wrap, tables
  scroll horizontally, no page-level horizontal overflow.

## 9. Known limitations

Scenario option lists are fixed to the three validated instances;
orders `count` is page-scoped (backend envelope); bundle ~672 KB;
Recharts needs nonzero container size; dev server pinned to port 3000 to
match backend default CORS (preview/other origins need
`BACKEND_CORS_ORIGINS`).

## 10. Local startup

Backend (repo root): `pip install -r backend/requirements.txt`,
`cd backend`, `uvicorn app.main:app --reload` → `:8000`.
Frontend (`frontend/`): `npm install`, `npm run dev` → `:3000`.
