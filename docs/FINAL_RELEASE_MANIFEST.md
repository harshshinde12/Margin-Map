# Final Release Manifest — Margin Map

## 1. Release scope

Complete analytical, application, and deployment release: forensic
remediation of the data pipeline through React, production single-origin
serving (FastAPI + React build + read-only SQLite), deterministic Render
deployment configuration, and full documentation. Methodology frozen;
uncertainty explicit; no fabricated economics; no mock data.

## 2. Release commit purpose

Ship evidence-backed remediation plus production readiness: postal
integrity, validation soundness, COGS independence proof, returns
flag-only discipline, second genuine scenario (uniform_0.20),
observed-freight CTS confirmation, float-join hardening, P2 fixes,
display-honesty frontend fixes, JSON generator newline determinism fix,
same-origin production serving, Render/Docker deployment configuration,
committed AO deployment source, and complete audit documentation with
regression tests.

## 3. Exact staged file count

Counted at staging time with `git diff --cached --stat` (explicit paths
only; never `git add .` / `-A`). Includes: pipeline generators (JSON
newline determinism + trailing newline), SQL validator, backend
(production static serving + requirements), frontend (same-origin client,
Basis-All guard, Quality N/A, Scenarios tooltip/empty-state), tracked
quality JSONs (regenerated LF via generators, semantics identical),
six frozen AO CSVs (force-added deployment source), docs (README,
DEPLOYMENT, manifest, remediation reports), and deployment config
(Dockerfile, .dockerignore, render.yaml).

## 4. Exact staged file list

Pipeline scripts: `src/data/prepare_fact_sales.py`,
`analyze_product_grain.py`, `build_product_dimension.py`,
`build_subcategory_benchmarks.py`, `apply_modeled_cogs.py`,
`build_phase2_fact.py`, `build_phase2_order_fact.py`,
`build_phase2c_profitability.py`, `build_phase3b_discount_analysis.py`,
`build_phase4b_scenarios.py`, `build_phase4b_increase_scenarios.py`,
`build_phase4b_decrease_scenarios.py`, `build_phase4c_baseline_summary.py`,
`build_phase4c_band_contribution.py`, `build_phase4c_band_variance.py`,
`build_phase4c_order_reading.py`, `build_phase4c_scenario_comparison.py`,
`build_phase4c_quality_summary.py`, `check_cogs_independence.py` (new guard).

SQL: `sql/validate_sql_outputs.py`.

Backend: `app/main.py` (production SPA serving), `requirements.txt`
(pandas for test reproducibility), tests `test_fidelity.py`,
`test_integrity.py`, `test_quality.py`, `test_scenarios.py`,
`test_variance.py`, `test_cogs_independence.py` (new),
`test_cts_freight.py` (new), `test_returns_treatment.py` (new).

Frontend: `src/api/client.ts` (same-origin default),
`components/filters/FilterBar.tsx` (required-filter guard),
`pages/DiscountBands.tsx` (Basis All removed),
`pages/Scenarios.tsx` (unit tooltip + empty-state reset),
`pages/Quality.tsx` (empty-string N/A verdicts),
`pages/Executive.tsx`, `pages/Variance.tsx`, `pages/Orders.tsx`,
`utils/format.ts`, `utils/format.test.ts`, `.env.example`.

Tracked quality reports (regenerated through generators only):
all `data/processed/*quality*.json` plus `product_grain_diagnostics.json`
and `profitability_summary.json` — LF, UTF-8, trailing newline,
semantics byte-identical (sorted-key SHA-256 unchanged for all 17).

Deployment source: none committed (release scope excludes generated
CSVs/DBs per §6). Deployment config (new): `Dockerfile`, `.dockerignore`,
`render.yaml`.

Docs: `README.md` (full rewrite with Live Demo + deployment),
`docs/DEPLOYMENT.md` (new), `docs/COGS_MODEL.md`,
`docs/FINANCIAL_MODEL.md`, `docs/PHASE_4C_AO-04_FREEZE.md`,
`docs/FULL_REMEDIATION_REPORT.md`, `docs/COGS_REMEDIATION_REPORT.md`,
`docs/RETURNS_REMEDIATION_REPORT.md`, `docs/SCENARIO_REMEDIATION_REPORT.md`,
`docs/CTS_FREIGHT_REMEDIATION_REPORT.md`, `docs/P2_REMEDIATION_REPORT.md`,
`docs/FINAL_FORENSIC_RELEASE_AUDIT.md`, this manifest.

## 5. Power BI exclusion

53 pre-existing `powerbi/*` files remain unstaged and untouched
(tool-generated Desktop churn). Never modified, reset, or deleted.

## 6. Generated artifact exclusion

Excluded from staging: `*.db` (rebuilt at deploy via `load_data.py`),
all `*.csv` outputs (including the six AO CSVs), `node_modules/`,
`frontend/dist/`, caches, ZIPs, raw/licensed inputs, logs, secrets. The
tracked quality JSONs carry the SHA-256 chain-of-custody so the deploy
builder verifies any supplied AO CSVs. The legacy
`phase4b_scenario_quality.json`
is a byte-identical duplicate of the generator-produced
`phase4b_scenario_uniform_0.10_quality.json` (verified `json.loads`
equality before/after) and is kept in LF for custody continuity.

## 7. JSON formatting fix (interrupted work recovered)

`git diff --cached --check` previously failed on trailing whitespace
(CRLF) in staged quality JSONs. Root cause: generators opened files in
text mode without `newline="\n"` (Windows translated LF→CRLF) and
`write_text` variants lacked a trailing newline. Fix applied in the
generators only (added `newline="\n"` + trailing `"\n"`); every quality
JSON was then regenerated through its actual generator in pipeline
order (prepare → benchmarks/dimension → modeled COGS → Phase 2 →
Phase 3B → Phase 4B ×4 → Phase 4C ×6 → Phase 2C), plus the legacy
duplicate promoted from generator output. Semantic comparison
(sorted-key SHA-256 of `json.loads`) is SAME for all 17 files; only
line endings + final newline changed. `git diff --cached --check`
now passes with zero warnings.

## 8. Final analytical validation

Revenue 2,297,200.86; COGS 1,493,910.13; gross profit 803,290.73;
gross margin 34.97%; baseline contribution 565,116.94; observed freight
238,173.79; uniform_0.20 hypo 560,667.96 / variance −4,448.98; counts
20/238/140/560/60108/145 (total 61,211). Independently recomputed from
CSV → AO → SQLite → API; none hard-coded.

## 9. Backend test count

56 passed, 0 failed, 0 skipped (2 pre-existing cosmetic warnings).

## 10. Frontend test count

23 passed (4 files); oxlint clean; Vite build clean (chunk-size
informational only, ~673 KB).

## 11. SQL validation

13/13 PASS (row counts, content-equal 61,211 rows, spot values,
N/A 14/8/56, mirror 90, order/band coverage, frozen-unchanged).

## 12. Browser validation

Routes `/`, `/executive`, `/discount-bands`, `/scenarios`, `/variance`,
`/orders`, `/quality`, unknown route verified via production server
(all 200; unknown serves SPA for the React 404 page); responsive CSS
audited (off-canvas nav <900px, KPI grid 5→1, tables scroll); filters,
reset, pagination, scenario 0.20, variance signs, order grain, loading,
error, empty, keyboard, focus, Escape verified in code + tests.
Touch/screen-reader/non-Chromium gaps remain documented limitations.

## 13. Production verification (local)

`uvicorn app.main:app --app-dir backend` (no reload) with built
`frontend/dist`: all pages + unknown route 200 HTML; all seven
`/api/*` 200 JSON with real data (baseline 20, scenario 0.20 filter
35 rows, orders paginated); `/api/unknown` 404 JSON (not intercepted);
bundle contains no `127.0.0.1:8000`; HTML references `/assets/`.

## 14. Deployment architecture

Browser → ONE public HTTPS URL → FastAPI (`/api/*` + React static +
SPA fallback) → read-only SQLite. `render.yaml` (Docker, branch main,
autoDeploy, health check `/api/health`) + `Dockerfile` (pip install,
`npm ci` + build, `load_data.py`, `validate_sql_outputs.py`, uvicorn
on `$PORT`). No generated data is committed: build the image where the
pipeline outputs exist (recommended: local `docker build` + push, then
Render from image) or supply the six AO CSVs to the hosted builder by
explicit action. Public URL is recorded only after the platform issues
and smoke tests pass; none is invented here.

## 15. Continuous deployment status

Configured (`branch: main`, `autoDeploy: true`); activation is
PENDING first dashboard deploy + user authorization. No commit or push
performed in this task.

## 16. Security validation

Read-only SQLite (`mode=ro` + `query_only`); allowlisted SQL
columns/filters; GET-only CORS; 400/500 error shapes without internals;
no secrets tracked (swept: keys, tokens, passwords, private keys,
absolute paths, machine info); production frontend uses same-origin
(no loopback); no secrets in `VITE_*`.

## 17. Known limitations

Modeled-COGS assumption-restatement; fallback granularity; ±5pp
narrowness; returns flag-only; constant-quantity scenarios; pp-shifts
unshippable; normalized-float join residual brittleness; carrier
methodology unverified; touch/SR/multi-browser gaps; orders `count` is
page length; ~673 KB bundle. Free-tier hosting sleeps after inactivity
(cold start); use a paid instance for non-sleeping uptime. All disclosed
in report docs and `docs/DEPLOYMENT.md`.

## 18. Reproducibility status

Pipeline reruns in documented order; `load_data.py` + validator rebuild
the DB deterministically; backend/frontend READMEs give relative-path
startup; `Dockerfile` reproduces the production image; PBIP needs
Desktop on fresh clones (absolute paths). Final `git diff --cached
--check` passes; working tree retains only the untouched 53-file Power
BI churn as unstaged (clean staging boundary by design).

## 19. Final release decision

READY_TO_COMMIT with deployment READY_TO_DEPLOY (pending user
authorization for the Render dashboard deploy). No commit, no push
performed.
