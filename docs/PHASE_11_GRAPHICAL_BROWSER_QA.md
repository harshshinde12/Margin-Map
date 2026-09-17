# Phase 11 Graphical Browser QA — Real Rendered Validation

## 1. Objective

Close the one verification gap left by Phase 10: validate the actually
rendered Margin Map product in a real graphical browser engine
(Blink), as a user would experience it — pixels, layout, interaction,
console, network, keyboard, tooltips, responsive behavior, and
displayed analytical values against the live API.

prior automated evidence (jsdom, HTTP, source inspection) was NOT
treated as a substitute for rendered validation in this phase.

## 2. Environment

- OS: Windows (win32), machine-local stack, 2026-09-17
- Backend: `cd backend` + `uvicorn app.main:app --reload` (also plain
  `python -m uvicorn app.main:app --port 8000`), verified
  `http://127.0.0.1:8000/api/health` ->
  `{"status":"ok","database":"connected","read_only":true}`
- Frontend: `cd frontend` + `npm run dev`, verified
  `http://localhost:3000/` 200, title "Margin Map — Profitability
  Intelligence" (note: Vite binds `localhost`; `127.0.0.1:3000`
  refused connections while `localhost:3000` served — local
  resolver/IPv6 binding quirk, no product impact)
- Browser: Google Chrome (system install,
  `C:\Program Files\Google\Chrome\Application\chrome.exe`), driven
  headless via Playwright 1.63.0 + `executable_path` (no Chromium
  download; the real Blink engine rendered every pixel). Screenshots
  captured per route/viewport and visually inspected in this phase.
- Console capture: Chrome DevTools console stream via Playwright CDP
  `console` + `pageerror` events on every navigation (the same
  message stream DevTools displays; the DevTools GUI window itself
  was not eyeballed — see §17).
- DB safety: `data/processed/marginmap.db` untouched — 17,211,392
  bytes, mtime 2026-09-14 23:48, read-only GET traffic only.

## 3. Viewports tested (real rendered layout, scrollW vs clientW measured)

| Viewport | scrollW == clientW | Sidebar | Notes |
|---|---|---|---|
| 1440 × 900 | yes, all 6 pages + 404 | fixed, active link highlighted | no overflow, no clipping |
| 1280 × 800 | yes (executive, orders) | fixed | same clean result |
| 1024 × 768 | yes (executive, orders) | fixed w=236, toggle present | desktop layout preserved |
| 768 × 1024 | yes (executive, orders) | off-canvas x=-236, hamburger | KPI 2-col wrap, filters stack |
| 600 × 900 | yes (executive, orders) | off-canvas x=-236, hamburger | filters stack, tables scroll internally |

Screenshots captured (and visually inspected): all six routes +
unknown route at 1440 × 900; executive + orders at 1280 × 800,
1024 × 768, 768 × 1024, 600 × 900; plus interaction shots (bands B5,
bands LINE basis, scenarios alt instance, orders empty state,
loading skeleton, error card, executive/variance tooltips,
mobile drawer open, post-fix production-build executive).

## 4. Page results (desktop 1440 × 900, visually inspected)

- Executive: PASS. Title/subtitle/chips, 9 KPI cards aligned
  ($2.30M, $803.3K, $565.1K, 24.6%, $238.2K, 5,009, 9,994, 80.2%,
  0.198), 6-bar horizontal chart (Contribution Profit teal), detail
  table. Clear baseline-profitability story.
- Discount Bands: PASS. Filter bar (Basis/Band/Metric + Reset),
  B0 $221.0K / B1 $79.9K / B2 $156.5K cards, B0–B5 + gray TOTAL
  reference chart, detail table. Metric switch changes bar heights;
  B5 isolates one band; LINE basis chip shows; Reset restores
  exactly (bar geometry identical before/after).
- Scenarios: PASS. Not-a-forecast caveat banner prominent,
  instance select (4 options), +$95,406.24 variance card,
  grouped baseline (navy) vs hypothetical (teal) chart with legend,
  instance switch re-renders chart, caveat persists.
- Variance: PASS. Zero baseline, B0/B1 red below zero, B2–B5 green
  above zero, TOTAL gray; metric switch re-renders; labels
  unclipped; table signs match bars (-$30,530.82 / -$3,248.80 /
  +$27,378.13).
- Orders: PASS. Header, 50-row default ("Rows 1–50"), Next ->
  "Rows 51–100" (first row changes), Previous restores, size 100 ->
  "Rows 1–100", B5 filter badge, order-grain rows
  (CA-2014-100006 wad 0.0…), no aggregation, table scrolls
  internally, viewport never overflows.
- Quality: PASS. 17 artifacts / 75 checks / ALL_SOURCES_ELIGIBLE
  verdict cards, "125 stored checks · mirrored verbatim · no scores
  computed" (no fake score), PASS badges, artifact filter 25 -> 3
  rows, Reset restores.
- 404: PASS. Unknown route renders "Page not found." card + "Back
  to Executive", shell/navigation intact, no blank page, no errors.

## 5. Navigation (real clicks)

All six nav items clicked: correct URL, `aria-current="page"` on
the active link only, shell preserved, content rendered, zero
page errors. Browser back/forward verified
(orders <-> quality) with correct state.

## 6. Loading / error / empty states (real rendered)

- Loading: API delayed 1.5 s via route delay -> skeleton cards
  detected in DOM and screenshotted, layout stable, replaced by
  data (NET REVENUE present). PASS.
- Error: backend-origin requests aborted -> "Unable to load
  analytical data." + safe message ("Unable to reach the Margin Map
  API. Start the backend and retry.") + Retry button, sidebar shows
  "API unreachable", shell intact, no Traceback. Retry after
  restoring backend recovers to data. PASS. Console showed only the
  expected `net::ERR_FAILED` resource errors caused by the
  intentional abort. (One blank-screen capture during testing was a
  harness artifact — the abort pattern `**/api/**` also matched
  Vite's `/src/api/client.ts` module so React never mounted; after
  scoping the abort to the backend origin, the genuine error card
  rendered. Not a product defect.)
- Empty: impossible order id -> "No records found." card, visually
  distinct from the error card; Clear Filters restores Rows 1–50.
  PASS.

## 7. Tooltips (real hovers)

- Executive Net Revenue bar: "Value : $2,297,200.86", positioned
  x=895 w=151 inside 1440 viewport, readable, no clipping. PASS.
- Variance B0 (negative): "Variance · Contribution : -$30,530.82".
  PASS.
- Variance B2 (positive): "Variance · Contribution : $27,378.13".
  PASS. (Screenshot shows the standard Recharts hover backdrop
  behind the active bar — chart-library behavior, not a defect.)

## 8. Network (browser-observed)

React -> `http://127.0.0.1:8000/api/*` exclusively (health,
baseline, contribution, scenarios, variance, orders, quality; all
HTTP 200). Filter parameters transmitted in query strings
(`scenario_id`, `block`, `metric_name`, `limit`, `offset`). No
React -> SQLite traffic possible (only HTTP). No failed requests
outside the intentional error-state abort. PASS.

## 9. Console

Zero `pageerror` events across all routes, viewports, filter,
pagination, error, recovery, tooltip, keyboard, and mobile-drawer
sequences. Zero console errors/warnings except: Vite dev HMR
"connecting/connected" debug lines, the React DevTools suggestion
(dev-only, expected under `npm run dev`), and the intentional
`net::ERR_FAILED` lines during error-state simulation. No React
warnings. Production-build page (`vite preview`) likewise zero
page errors. PASS (captured via the CDP console stream; the
DevTools GUI window was not manually eyeballed — §17).

## 10. Keyboard walkthrough (real key events)

Tab order from page top: 01 Executive -> 02 Discount Bands -> 03
Scenarios -> 04 Variance -> 05 Orders -> 06 Data Quality, each with
a visible `solid/2px` focus outline, then chart region, then cycle
(no trap — focus wraps cleanly). Enter activates the Orders Next
pager (Rows 51–100). Arrow keys operate the Variance metric select
(chart updates). No keyboard trap anywhere. One gap found and
fixed: Escape did not close the mobile drawer (§12).

## 11. Mobile drawer (600 × 900, real clicks + keys)

Closed x=-236; hamburger opens x=0 with visible scrim
(opacity 1/visible/clickable); nav link navigates and auto-closes;
scrim click closes. Post-fix, Escape also closes (verified
openedX=0 -> afterEscapeX=-236). PASS.

## 12. Defects found

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | LOW | Mobile off-canvas drawer had no Escape-to-close handler (toggle, scrim, nav-click all worked; no trap, toggle keyboard-reachable) | FIXED: 9-line `useEffect` keydown handler in `AppShell.tsx` + regression test |
| 2 | NO ISSUE | First smoke screenshot showed an empty Executive chart | Harness artifact: `--virtual-time-budget` froze Recharts animation at width 0; re-render with settle wait shows all 6 bars (widths 876.8/216.3/… measured in DOM) |
| 3 | NO ISSUE | Blank white capture during error-state probing | Harness artifact: over-broad abort pattern killed Vite's client module; correctly-scoped abort renders the genuine error card |
| 4 | NO ISSUE | Preview build on :4173 showed "API unreachable" | Expected: backend CORS allows only :3000 origins per documented config; with a temporary CORS allowance the production bundle renders fully (pixel-identical to dev) |

No CRITICAL / HIGH / MEDIUM defects. No analytical, SQL, or API
defects. Cosmetic/visual review found no overlaps, clipping,
truncation, inconsistent heights, or density problems on any page
at any tested width.

## 13. Fix applied (defect #1 only)

- `frontend/src/components/layout/AppShell.tsx` (+13/-2): Escape
  keydown listener registered while the drawer is open; closes on
  Escape; listener removed on close/unmount. No analytical, SQL,
  API, or styling changes.
- `frontend/src/test/routing.test.tsx` (+12/-1): new test "closes
  the navigation drawer on Escape".
- Re-verified: frontend suite 22/22 (was 21/21 + 1 new), `npm run
  lint` clean, `npm run build` clean, backend suite 41/41, live
  browser post-fix Escape check PASS (0 -> -236), desktop smoke
  unaffected, zero page errors.

## 14. Post-fix regression (final state)

- Backend: 41 passed, 0 failed (2 pre-existing cosmetic
  `httpx`/`starlette` deprecation warnings, unchanged).
- Frontend: 22 passed, 0 failed (4 files).
- Production build: `tsc -b` + Vite clean; `dist/` served via
  `vite preview` and graphically verified (Executive renders with
  live data, zero page errors).
- API smoke: `/api/health` ok/connected/read-only; spot checks §15.
- DB: size + mtime unchanged (frozen).
- Graphical re-checks repeated post-fix: drawer Escape, desktop
  executive render, console clean.

## 15. Analytical display spot check (displayed vs live API)

| Display | API source of truth | Match |
|---|---|---|
| Exec tooltip Net Revenue $2,297,200.86 | baseline net_revenue 2297200.8603000003 | yes |
| KPI $565.1K contribution | contribution_profit 565116.9418299999 | yes |
| Scenarios +$95,406.24 | hypo 660523.1831600001 − baseline 565116.94183 = 95406.24 | yes |
| Variance TOTAL (gray bar scale ~$95K) | variance TOTAL 95406.2413300001 | yes |
| Variance B5 bar (~$45K) | B5 45401.369600000005 | yes |
| Variance B0 tooltip/table -$30,530.82 | B0 -30530.822469999985 | yes |
| Variance B2 tooltip/table +$27,378.13 | (table row, matches bar) | yes |
| Orders CA-2014-100006 wad 0.0, contrib $82.73 | order row wad "0.0", first page | yes |
| Quality 17 / 75 / ALL_SOURCES_ELIGIBLE / 125 rows | 17 `eligibility` rows, 75 `upstream_check` rows, `overall_eligibility` row, 125 rows, all PASS | yes |

## 16. Performance feel (observational, no optimization)

Navigation instant; filter response < ~1 s; chart animation
smooth; pagination immediate; drawer transition smooth; loading
skeleton shows only under induced latency (no flashing in normal
use). No user-visible performance problem. The ~672 KB bundle
warning (Recharts-dominated) remains informational per Phase 10.

## 17. NOT VERIFIED items (honest gaps)

- DevTools GUI eyeball: console stream captured programmatically
  via CDP (identical message source), but nobody stared at the
  DevTools window on a physical monitor.
- Physical-monitor color/contrast eyeball and touch interaction on
  a real handset (layout verified at handset widths in Blink;
  pointer touch itself not exercised).
- Screen-reader pass (semantic/ARIA baseline was Phase 10 verified;
  unchanged since — only an Escape handler was added).
- Multi-browser rendering beyond Chromium/Blink (Firefox/WebKit
  not installed here). No browser-specific APIs are used
  (React + Recharts + standard CSS), so risk is minimal.

## 18. Visual consistency

Sidebar, header, titles, card radius/borders/shadows, spacing,
typography, chart containers, tables, filter controls, status
colors (green PASS/positive, red negative, gray TOTAL/neutral,
teal hypothetical/contribution accent, navy baseline), and button
styles are consistent across all six pages + 404 at all widths.
No component deviates from the design system. No changes made.

## 19. Release-readiness assessment

Yes — Margin Map can be confidently demonstrated to a recruiter,
interviewer, or business stakeholder. Evidence: every page renders
correctly with live data in a real browser engine at desktop,
tablet, and mobile widths with zero overflow, zero console/page
errors, working navigation/filters/pagination/states/tooltips/
keyboard/drawer, API-faithful displayed values, and a clean
post-fix regression (41/41 + 22/22 + build). The single LOW defect
found was fixed minimally and re-verified live.

## 20. Files modified in this phase

- `frontend/src/components/layout/AppShell.tsx` (Escape fix)
- `frontend/src/test/routing.test.tsx` (Escape regression test)
- `docs/PHASE_11_GRAPHICAL_BROWSER_QA.md` (this document)
- `docs/FINAL_RELEASE_CHECKLIST.md` (Phase 11 results appended)

NO commit. NO push. Pre-existing workspace modifications under
`powerbi/` (local Power BI Desktop churn) were not touched.
