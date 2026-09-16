# Margin Map Frontend — Profitability Intelligence (Phase 9)

Read-only React presentation layer for the Margin Map analytics product.
It consumes the Phase 8 FastAPI backend exclusively; the API/SQLite
analytical outputs remain the single source of truth.

## Stack

- React 19 + TypeScript + Vite 8
- React Router 7 (client-side routing)
- Recharts 3 (bar/column visuals only — no pies, no 3D, no dual axes)
- Vitest + Testing Library + jsdom (test suite)
- Hand-authored design system in `src/styles/global.css` (no UI kit)

## Pages

| Route | Source | Content |
| ----- | ------ | ------- |
| `/executive` | `GET /api/baseline` | KPI cards, baseline currency chart, 20-row detail table |
| `/discount-bands` | `GET /api/contribution` | Band chart with TOTAL reference, filter chips, detail table |
| `/scenarios` | `GET /api/scenarios` | Baseline-vs-hypothetical grouped bars, stored variance table |
| `/variance` | `GET /api/variance` | Diverging variance bars, band detail table |
| `/orders` | `GET /api/orders` | Paginated order-grain grid (default 50, max 500) |
| `/quality` | `GET /api/quality` | Eligibility verdict cards, 125-row check table |

`/` redirects to `/executive`; unknown routes render a 404 page.

## Prerequisites

- Node.js 20+ and npm
- The Phase 8 backend running (see "Start the backend" below)

## Installation

From `frontend/`:

```text
npm install
```

Copy the example environment file if you need a non-default API address:

```text
copy .env.example .env
```

`VITE_API_BASE_URL` defaults to `http://127.0.0.1:8000`.

## Start the backend

From the repository root (one terminal):

```text
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000` with docs at `/docs`.

## Start the frontend

From `frontend/` (second terminal):

```text
npm run dev
```

Open `http://localhost:3000`. Port 3000 is configured deliberately: it is
in the backend's default CORS origins, so no backend changes are needed.
To serve another origin, set `BACKEND_CORS_ORIGINS` when starting Uvicorn.

## Production build

```text
npm run build
npm run preview
```

`tsc -b` type-checks before bundling; the build emits `dist/`.

## Tests

```text
npm test
```

21 tests across 4 files: display formatting/N-A conventions, API client
(URL building, filter serialization, network/HTTP/JSON error mapping),
core components (KPI, error/empty states, badges, pagination), and routing
(redirect, 404, navigation, backend-value rendering with mocked fetch).

## Architecture notes

- `src/api/` — centralized client (`client.ts`) and backend-mirroring
  types (`types.ts`). No other module calls `fetch`.
- `src/hooks/useApi.ts` — loading/error/retry fetch hook; layout stays
  mounted so skeletons preserve page stability.
- `src/utils/format.ts` — display-only formatting (currency, percent,
  counts, unit dispatch, frozen empty-string → "N/A"). Parsing a single
  stored value for presentation is not analysis; no metric is derived.
- `src/components/` — layout, navigation, KPI, charts, tables, filters,
  and loading/error/empty states shared by all six pages.
- The frontend never touches SQLite or CSVs and contains no profitability
  formulas, thresholds, forecasts, or quality scores.

## Known limitations

- Scenario/instance option lists are fixed to the three validated
  instances; new backend instances would need a frontend option update.
- Orders `count` reflects the returned page, not the filtered total
  (backend envelope behavior).
- Production bundle is ~672 KB minified (Recharts included); acceptable
  for this portfolio scope, code-splitting deferred.
- Charts render placeholders in zero-size containers (e.g. hidden tabs)
  until resized — standard Recharts behavior.
