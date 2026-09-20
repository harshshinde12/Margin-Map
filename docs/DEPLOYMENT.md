# Margin Map — Deployment Guide

## 1. Architecture

```text
Browser
  ↓  ONE public HTTPS URL (Render web service)
FastAPI (uvicorn, production, no --reload)
  ├── /api/*          → read-only SQLite (AO-01..AO-06, mode=ro + query_only)
  ├── /assets/*       → React production static assets
  └── /* (SPA)        → frontend/dist/index.html (React Router handles pages)
         ↓
  SQLite marginmap.db (rebuilt at deploy time, read-only at runtime)
```

One origin serves UI and API. The production React build uses
same-origin `/api` (no `VITE_API_BASE_URL`), so there is no localhost
dependency and no browser CORS hop.

## 2. Local development (two origins)

```text
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload        # http://127.0.0.1:8000
```

```text
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

`frontend/.env.example` documents `VITE_API_BASE_URL=http://127.0.0.1:8000`
for dev. Port 3000 is in the backend's default CORS origins.

## 3. Production architecture

- `backend/app/main.py` detects `frontend/dist/index.html`. When present
  it mounts `/assets` and serves the SPA (root + fallback); `/api/*`,
  `/docs`, `/redoc`, `/openapi.json` are never intercepted. When absent
  (dev checkout before `npm run build`), `GET /` keeps its API pointer.
- `frontend/src/api/client.ts`: empty/unset `VITE_API_BASE_URL` means
  same-origin. Production builds set nothing; dev sets the loopback URL.
- The database is opened `mode=ro` with `PRAGMA query_only=ON`. Only
  parameterized `SELECT` exists in `backend/app/`.

## 4. Build process (as run on the host)

```text
pip install -r backend/requirements.txt
cd frontend && npm ci && npm run build && cd ..
python sql/load_data.py            # chain-of-custody verified rebuild
python sql/validate_sql_outputs.py # 61,211 rows, spot values, N/A, mirrors
```

`Dockerfile` runs exactly these steps. `render.yaml` deploys that image.

## 5. Backend startup (production)

```text
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}
```

Requirements: bind `0.0.0.0`, use `$PORT`, no `--reload`, `/api/health`
must return `{"status":"ok","database":"connected","read_only":true}`.
Missing database fails safely as HTTP 500 `database unavailable`
(no paths or stack traces).

## 6. Frontend build

```text
cd frontend
npm ci
npm run build    # tsc -b + vite build → frontend/dist/ (git-ignored)
```

Verify the bundle contains no loopback API: search `dist/assets/*.js`
for `127.0.0.1:8000` (must be absent; the only `localhost` strings are
bundler/router internals). `index.html` must reference `/assets/`.

## 7. SQLite strategy

- `data/processed/marginmap.db` (~16 MB) is **not committed** (root
  `.gitignore` keeps `*.db` ignored; release scope also excludes it).
- The six frozen AO CSVs (`phase4c_*.csv`, ~13 MB total) are likewise
  **not committed** (release scope excludes generated CSVs).
- Raw inputs (`*.zip`, `sample_-_superstore.xls`, `data/raw/`) stay
  ignored (licensed/large, local only).
- The tracked quality JSONs (`data/processed/*quality*.json`) ARE
  committed and carry the SHA-256 chain-of-custody for every AO CSV.
- At image build time `python sql/load_data.py` verifies each AO CSV's
  bytes against the SHA-256 recorded in its tracked quality JSON and
  rebuilds the database deterministically (fresh file, schema, frozen
  row order, views). Any mismatch fails the build loudly.
- Therefore build the production image where the pipeline outputs exist
  (recommended: `docker build` locally after running the pipeline, then
  push the image and deploy Render from the image), or supply the six AO
  CSVs to the hosted builder by your own explicit action. Never commit
  them as part of this release.
- At runtime the database is read-only. Never make it writable, never
  require visitors to upload data.

## 8. Environment variables

| Variable | Dev | Production |
|---|---|---|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | unset/empty (same-origin) |
| `BACKEND_CORS_ORIGINS` | default localhost:3000 | empty (same-origin needs none) |
| `MARGINMAP_DB` | unset (repo default) | unset (image default) |
| `PORT` | n/a | injected by host |

No secrets exist. Never put secrets in `VITE_*` (client-visible).

## 9. Render configuration

`render.yaml` (Docker runtime, branch `main`, `autoDeploy: true`):

- Service `margin-map`, plan `free`, `dockerfilePath: ./Dockerfile`.
- `healthCheckPath: /api/health`.
- `Dockerfile` installs Python deps, builds the frontend, rebuilds and
  validates the database, and starts uvicorn on `$PORT`.

## 10. Health check

`GET /api/health` → 200 `{"status":"ok",...}`. Render polls it;
a missing/unreadable database yields 500 `database unavailable`.

## 11. Deployment steps (dashboard, ~10 minutes)

1. Push `main` to GitHub (commit first; this task leaves the tree
   staged but uncommitted).
2. Recommended (keeps generated data out of Git): build and push the
   image locally, where the pipeline outputs exist:
   ```text
   python sql/load_data.py
   python sql/validate_sql_outputs.py
   docker build -t <you>/margin-map:latest .
   docker push <you>/margin-map:latest
   ```
   Then Render dashboard → New → Web Service → Deploy from Docker
   image → `<you>/margin-map:latest`. Set health check `/api/health`.
3. Alternative: Render → New → Web Service → select the `Margin Map`
   repo (uses `render.yaml`/Dockerfile). Supply the six AO CSVs to the
   build context by your own explicit action first, otherwise
   `load_data.py` fails loudly by design.
4. Watch logs for: `npm run build` success, `OK: loaded 61211
   rows`, `OK: all Phase 6 SQL validation checks passed`,
   `Uvicorn running on ...`.
5. Note the issued URL (`https://<service>.onrender.com`). Record it in
   `README.md` Live Demo only after verifying step 6.
6. Smoke test the public URL (section 15 of the release task): all six
   pages + unknown route return the UI; all seven `/api/*` endpoints
   return real data; scenario `uniform_replace_0.20` returns 35 rows;
   no localhost requests; no console errors.

## 12. Custom domain steps

Render dashboard → service → Settings → Custom Domains → add domain →
set the shown DNS CNAME → wait for certificate issuance. No code change
(the app is origin-agnostic; same-origin `/api` follows the domain).

## 13. Continuous deployment

`render.yaml` pins `branch: main` with `autoDeploy: true`:

```text
GitHub push to main → Render build (Dockerfile) → health check →
production deployment → public URL
```

Confirm "Auto-Deploy: On" on the service after first deploy. Do not
claim activation until the dashboard shows it.

## 14. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Build fails in `load_data.py [quality-chain]` | An AO CSV drifted from its quality JSON; never hand-edit outputs — regenerate through `src/data/*` + Phase 4C scripts, re-run `validate_sql_outputs.py`. |
| `/api/health` 500 `database unavailable` | `marginmap.db` missing/unreadable; check build logs for the `loaded 61211 rows` line. |
| UI loads but data never appears | Frontend built with a loopback `VITE_API_BASE_URL`; rebuild with it unset (production default). |
| `404` on `/api/*` in production | SPA fallback intercepting API — update `backend/app/main.py` (this repo already guards `api/`, `docs`, `openapi.json`). |
| Blank Quality verdict cards | Fixed: verdicts use `\|\| 'N/A'` so empty strings render N/A. |
| Mixed ORDER/LINE chart | Fixed: Basis filter no longer offers All (`allowAll={false}`). |

## 15. Free-tier limitations

The `free` plan sleeps after inactivity (cold start on next visit).
Public deployment is live, but the free service may sleep after
inactivity and require a cold start. This is a hosting-plan property,
not an application defect: whenever the service is running, the full
dashboard, filters, scenarios, pagination, charts, orders, and quality
views work against the real analytical database.

## 16. Production uptime considerations

For genuinely non-sleeping availability, use a non-sleeping paid
web-service instance (Render dashboard → service → Instance Type).
No application change is needed; the same image and health check apply.
Do not claim 24/7 always-on behavior while on a sleeping/free plan.
