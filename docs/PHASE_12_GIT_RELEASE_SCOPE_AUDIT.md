# Phase 12 — Git & Release Scope Audit

Final cleanup and release-scope audit after Phase 11 graphical browser QA.
No commit, push, reset, restore, checkout, or deletion was performed in this phase.
Power BI working-tree churn was left exactly as found.

## 1. Repository identity

- Working directory: `C:\Users\Harsh Shinde\Desktop\Margin Map`
- Repo root (`git rev-parse --show-toplevel`): `C:/Users/Harsh Shinde/Desktop/Margin Map`
- Git dir (`git rev-parse --absolute-git-dir`): `C:/Users/Harsh Shinde/Desktop/Margin Map/.git`
- Branch (`git branch --show-current`, `git branch -vv`): `main`, tracking `origin/main`, `e4bbc3f [origin/main] Add React analytics frontend`
- HEAD (`git rev-parse HEAD`, `git log --oneline -1 --decorate`): `e4bbc3f05b41c71ecbdd2135994f57701580c049`, `e4bbc3f (HEAD -> main, origin/main, origin/HEAD) Add React analytics frontend`
- Remotes (`git remote -v`): `origin https://github.com/harshshinde12/Margin-Map.git (fetch/push)`
- Unrelated directory `C:\Users\Harsh Shinde\.git` exists on disk but was never operated on. All commands ran with workdir `C:\Users\Harsh Shinde\Desktop\Margin Map` and resolved to `Margin Map/.git` above.
- Working tree: DIRTY (not clean). At audit start `git status --short`: 55 modified + 3 untracked. No staged changes. Creating this Phase 12 file adds a 4th untracked working paper (see §13 for inclusion decision).

## 2. HEAD and branch

- Branch: `main`, up to date with `origin/main`.
- HEAD: `e4bbc3f Add React analytics frontend`.
- No commit was created in Phase 10, Phase 11, or Phase 12. HEAD is unchanged from the Phase 10 baseline.

## 3. Previous release baseline

- `9d352f3 Finalize Power BI executive analytics report` — present.
- `8d13e43 Add FastAPI analytics backend` — present.
- `e4bbc3f Add React analytics frontend` — present (HEAD).
- `git log --oneline --decorate -10`: `e4bbc3f`, `8d13e43`, `9d352f3`, `84660bd`, `8646f09`, `729bba8`, `0ae1efb`, `f53ca73`, `10cbd26`, `9e6c90e`.
- `git diff 9d352f3...HEAD --stat`: 77 files, ~8313 insertions (backend API + React frontend added on top of the Power BI release). No modification in this range; it is the committed baseline.
- `git diff --stat` (worktree vs HEAD): 55 files changed, 160 insertions, 615 deletions. Deletions are dominated by Power BI churn (see §6).
- `git diff --name-status`: all entries `M` (no adds/deletes in tracked tree).
- `git ls-files --others --exclude-standard` at audit start: exactly 3 untracked files (the Phase 10/11 docs). No other untracked source files. This Phase 12 file itself becomes the 4th untracked file on creation.

## 4. Working-tree status

- Modified (tracked): 55 files = 2 frontend + 53 powerbi (50 visuals + 3 report/semantic-model settings files). Full list in §5.
- Untracked at audit start: 3 files = `docs/PHASE_10_END_TO_END_QA.md`, `docs/FINAL_RELEASE_CHECKLIST.md`, `docs/PHASE_11_GRAPHICAL_BROWSER_QA.md`. This Phase 12 audit file is a 4th untracked working paper; see §13 for inclusion decision.
- Staged: none.
- Post-validation `git status --short` (before creating this file) is identical to pre-validation status. `npm run build` emitted `frontend/dist/` but `dist/` is git-ignored and did not change tracked status.

## 5. Full change classification

Legend: RELEASE-SCOPE = intended final commit. PRE-EXISTING = local churn predating Phase 11, must remain untouched. ENVIRONMENTAL = machine/view-state noise.

| Path | Status | Classification | Why | Action |
|------|--------|----------------|-----|--------|
| `frontend/src/components/layout/AppShell.tsx` | M | RELEASE-SCOPE | Phase 11 Escape-to-close drawer fix (+13/-2). Verified §9. | Include in final commit |
| `frontend/src/test/routing.test.tsx` | M | RELEASE-SCOPE | Phase 11 regression test `closes the navigation drawer on Escape` (+12/-1). Verified §9. | Include in final commit |
| `docs/PHASE_10_END_TO_END_QA.md` | ?? | RELEASE-SCOPE | Phase 10 independent QA record. Verified §7; historical claims honest. | Include in final commit |
| `docs/FINAL_RELEASE_CHECKLIST.md` | ?? | RELEASE-SCOPE | Release checklist (Phase 10 + Phase 11 appendix). Verified §7/§13; one wording caveat, no silent rewrite done. | Include in final commit (see §13 caveat before commit) |
| `docs/PHASE_11_GRAPHICAL_BROWSER_QA.md` | ?? | RELEASE-SCOPE | Phase 11 Blink/Chrome rendered validation + fix record. Verified §8. | Include in final commit |
| `powerbi/MarginMap_Phase7B_Final_FIXED.Report/.pbi/localSettings.json` | M | ENVIRONMENTAL | Only `securityBindingsSignature` rotated (DPAPI machine/user blob). No model/report semantics. | EXCLUDE, leave untouched |
| `powerbi/MarginMap_Phase7B_Final_FIXED.SemanticModel/.pbi/localSettings.json` | M | ENVIRONMENTAL | Only `securityBindingsSignature` rotated. `SemanticModel/definition/` diff is empty (zero TMDL change). | EXCLUDE, leave untouched |
| `powerbi/MarginMap_Phase7B_Final_FIXED.Report/definition/pages/pages.json` | M | ENVIRONMENTAL | Only `activePageName` changed `c73938ae200cbc11291b` -> `cc7b2933a690bece708a` (last-open page view state). | EXCLUDE, leave untouched |
| 50× `powerbi/.../definition/pages/*/visuals/*/visual.json` (see list below) | M | PRE-EXISTING | Power BI Desktop re-save churn. No query/DAX/TMDL change (see §6). Timestamps all `2026-09-17 16:56:17`, predating the Phase 11 fix (`17:01:24`); Phase 11 §20 already noted them as pre-existing and untouched. | EXCLUDE, leave untouched |

Power BI visual files (all PRE-EXISTING, same mechanism):

- `06965a84d02b0b86bb7b/visuals/27d6ddf045ea0648b021/visual.json`
- `06965a84d02b0b86bb7b/visuals/300c22417039c0d35987/visual.json`
- `06965a84d02b0b86bb7b/visuals/8e4c6c5fbcebe3dc5634/visual.json`
- `06965a84d02b0b86bb7b/visuals/aa010000000000000014/visual.json`
- `06965a84d02b0b86bb7b/visuals/aa010000000000000015/visual.json`
- `06965a84d02b0b86bb7b/visuals/bb020000000000000001/visual.json`
- `06965a84d02b0b86bb7b/visuals/d52e3f7a9b1c54e6f7a8/visual.json`
- `8e4da095a1d408807544/visuals/9184dcab03249c59998c/visual.json`
- `8e4da095a1d408807544/visuals/973bf0a952ccecec3c9c/visual.json`
- `8e4da095a1d408807544/visuals/aa010000000000000016/visual.json`
- `8e4da095a1d408807544/visuals/aa010000000000000017/visual.json`
- `8e4da095a1d408807544/visuals/bb020000000000000002/visual.json`
- `8e4da095a1d408807544/visuals/d24d103452a8e30e0652/visual.json`
- `8e4da095a1d408807544/visuals/e0e939ff05ae16761884/visual.json`
- `c73938ae200cbc11291b/visuals/88f664841d97a4c75605/visual.json`
- `c73938ae200cbc11291b/visuals/aa010000000000000001/visual.json`
- `c73938ae200cbc11291b/visuals/aa010000000000000002/visual.json`
- `c73938ae200cbc11291b/visuals/aa010000000000000003/visual.json`
- `c73938ae200cbc11291b/visuals/aa010000000000000004/visual.json`
- `c73938ae200cbc11291b/visuals/aa010000000000000011/visual.json`
- `c73938ae200cbc11291b/visuals/aa010000000000000012/visual.json`
- `c73938ae200cbc11291b/visuals/aa010000000000000013/visual.json`
- `c73938ae200cbc11291b/visuals/bb020000000000000004/visual.json`
- `c73938ae200cbc11291b/visuals/c41d2e6f8a0b43d5e6f7/visual.json`
- `c73938ae200cbc11291b/visuals/fad2b732a0916250aa5c/visual.json`
- `cc7b2933a690bece708a/visuals/1201429c2070080308b8/visual.json`
- `cc7b2933a690bece708a/visuals/455e4470a0d605ba2e4b/visual.json`
- `cc7b2933a690bece708a/visuals/9879c98b62400d9204e8/visual.json`
- `cc7b2933a690bece708a/visuals/a411455d556ec6979429/visual.json`
- `cc7b2933a690bece708a/visuals/aa010000000000000005/visual.json`
- `cc7b2933a690bece708a/visuals/aa010000000000000006/visual.json`
- `cc7b2933a690bece708a/visuals/aa010000000000000020/visual.json`
- `cc7b2933a690bece708a/visuals/aa010000000000000021/visual.json`
- `cc7b2933a690bece708a/visuals/aa010000000000000022/visual.json`
- `e12915057dd3636955d5/visuals/437afcf801d51d005db5/visual.json`
- `e12915057dd3636955d5/visuals/53d2270d0a6762c01902/visual.json`
- `e12915057dd3636955d5/visuals/69bdbf104b4a4088dd2e/visual.json`
- `e12915057dd3636955d5/visuals/88b0ecbc66a1c3608105/visual.json`
- `e12915057dd3636955d5/visuals/aa010000000000000007/visual.json`
- `e12915057dd3636955d5/visuals/aa010000000000000008/visual.json`
- `e12915057dd3636955d5/visuals/aa010000000000000023/visual.json`
- `e12915057dd3636955d5/visuals/aa010000000000000024/visual.json`
- `e12915057dd3636955d5/visuals/aa010000000000000025/visual.json`
- `e98e05930e4d356b94e3/visuals/16b385a08b4973049944/visual.json`
- `e98e05930e4d356b94e3/visuals/62b9eadb00e5b2566456/visual.json`
- `e98e05930e4d356b94e3/visuals/a55f409e3e6d692c0930/visual.json`
- `e98e05930e4d356b94e3/visuals/aa010000000000000018/visual.json`
- `e98e05930e4d356b94e3/visuals/aa010000000000000019/visual.json`
- `e98e05930e4d356b94e3/visuals/bb020000000000000003/visual.json`
- `e98e05930e4d356b94e3/visuals/e63f4a8b0c2d65f7a8b9/visual.json`

(All paths prefixed with `powerbi/MarginMap_Phase7B_Final_FIXED.Report/definition/pages/`.)

No GENERATED, UNEXPECTED, or UNKNOWN items were found. No deletions. `backend/`, `sql/`, `data/`, `scripts/`, `src/` have zero worktree diffs.

## 6. Power BI churn investigation

Method: `git diff -- powerbi/` saved (1550 lines, 62,330 bytes) and parsed. `SemanticModel/definition/` diff is empty. `Report/definition/` diff touches only the 50 visuals + `pages.json`.

Findings:

1. Which files: 53 files (§5). No `.tmdl`, no `database.tmdl`, `model.tmdl`, `relationships.tmdl`, table definitions, `diagramLayout.json`, `.pbism`, `.platform`, or `.pbix` changes.
2. What changed:
   - `z` + `tabOrder` renumbered in all 50 visuals (e.g. 1500->5000, 1000->3000, 2000->5000). `x/y/width/height` identical (verified on sampled card visual: only `z`/`tabOrder` differ).
   - Key-order-only `width` line moves (same value, different line position from JSON key reordering).
   - `filterConfig.filters[]` blocks REMOVED in 14 files (30 filter entries total). Every removed entry contains only `name` + `field.{Column|Measure}.{Expression.SourceRef.Entity, Property}` + `type` (`Categorical`/`Advanced`) with no filter condition, values, or operator. These are inert default placeholders Power BI Desktop strips on save. No `filterConfig` was added.
   - `drillFilterOtherVisuals: true` preserved in all cases; in 4 files it moved one nesting level (comma placement) with identical value.
   - `securityBindingsSignature` rotated in both `.pbi/localSettings.json` files (DPAPI blob, machine/user-specific).
   - `activePageName` changed (last-viewed page pointer).
3. Caused by Desktop open/save: yes. Signature rotation + `activePageName` + `z`/`tabOrder` renumber + inert `filterConfig` stripping + JSON key reordering is the standard PBIP re-save signature. Files share one mtime (`2026-09-17 16:56:17`), consistent with a single Desktop save.
4. Timestamp/metadata/formatting vs semantic: position values unchanged except z-order; no `visualType`, `query`, `dataRoles`, `objects` (except comma move), `title`, data source, or binding changes. Added-key histogram: `z` (50), `tabOrder` (50), `width` (26, same-value reorder), `drillFilterOtherVisuals` (4, same-value move), signatures/activePage. Removed-key histogram is the same plus the 30 inert filter entries.
5. DAX/TMDL/visuals/layout/sources/queries/model/relationships/measures/visual properties:
   - DAX: none. The single `Measure` string in the diff is a removed inert filter field referencing `_MM_Band_Value` (`Advanced`, no condition), not a model measure.
   - TMDL/model/relationships/tables/cultures: zero diff in `SemanticModel/definition/`.
   - Queries: zero added/removed `query` lines across the whole powerbi diff.
   - Visual properties: only z-order/tab-order; no type, title, or data-role change.
6. Present before Phase 11: yes. Power BI mtimes (`16:56:17`) predate the Phase 11 code fix (`AppShell.tsx 17:01:24`, `routing.test.tsx 17:01:45`, Phase 11 docs `17:06`). Phase 11 §20 explicitly records pre-existing `powerbi/` churn left untouched.
7. Part of committed Phase 7 release: no. They are uncommitted working-tree mutations of Phase 7-committed files (`9d352f3`, `84660bd` lineage).
8. Including them would introduce unrelated changes: yes. 615 deletions (mostly inert placeholders) plus z-order renumbering would pollute the final commit, obscure the 25-line Escape fix, and risk misreading as a semantic report change. No evidence links any Power BI hunk to Phase 11 (Phase 11 touched only React + docs).

Disposition: DO NOT stage, restore, delete, or edit. Left exactly as found. Classification: PRE-EXISTING (visuals) / ENVIRONMENTAL (settings/view state). Not release scope.

## 7. Phase 10 documentation verification

- `docs/PHASE_10_END_TO_END_QA.md` (206 lines) describes an independent re-execution across backend, API, frontend, browser-probe, fidelity, Power BI cross-check, filters, pagination, failure states, responsive (stylesheet-only), accessibility (code baseline), security, dependencies, and performance.
- Honesty checks: responsive rendered widths, live pixel rendering, devtools console, and live keyboard walkthrough are explicitly marked NOT VERIFIED with browser pass deferred. No PASS is claimed for unexecuted rendered checks. Test counts (backend 41/41, frontend 21/21 at Phase 10 time), build sizes, DB fingerprint abbreviation, and row counts match re-verified values (§10/§11). §19 `None — no product file was modified in this phase` is historically accurate for Phase 10 (the Escape fix came later in Phase 11 and is documented there). §20 `clean except the two new Phase 10 documents` was accurate at Phase 10 time; it is now superseded by Phase 11 + powerbi churn and must not be read as current status.
- No silent rewrite was performed. No factual correction was required beyond noting the above time-bound wording.

## 8. Phase 11 documentation verification

- `docs/PHASE_11_GRAPHICAL_BROWSER_QA.md` (265 lines) records real Blink rendering via system Chrome driven headless by Playwright 1.63.0 + `executable_path`, `npm run dev` + `uvicorn`, CDP console/pageerror capture, screenshots per route/viewport with visual inspection, and production `vite preview` verification.
- Coverage verified present: desktop (1440×900, 1280×800, 1024×768), tablet (768×1024), mobile (600×900) with `scrollW == clientW`; all 6 pages + 404; nav clicks + active state + back/forward; every filter + reset/empty/Clear; pagination + page-size; loading skeleton (induced latency); error card + Retry + recovery (with harness-artifact note); empty state; tooltips (exec $2,297,200.86; variance -$30,530.82 / +$27,378.13); network (React->FastAPI only, params transmitted); console (zero pageerrors; dev-only Vite/React-DevTools noise and intentional abort `ERR_FAILED` disclosed); keyboard order/focus/Enter/arrows + Escape gap; mobile drawer toggle/scrim/nav-close + post-fix Escape (`0 -> -236`); analytical spot checks per page; responsive/accessibility findings; defect table (1 LOW fixed + 3 harness NO ISSUE); fix diff summary; post-fix regression (41/41 + 22/22 + build + DB frozen); NOT VERIFIED residuals (DevTools-GUI eyeball, physical touch, screen reader, non-Chromium) kept explicit.
- No inflated PASS found. `NOT VERIFIED` items remain clearly marked. File list in §20 (2 code files + this doc + checklist appendix) is accurate; it correctly omits the Phase 10 doc it did not modify.

## 9. Escape-to-close code verification

- `frontend/src/components/layout/AppShell.tsx` diff: `useEffect` import added; effect registers `window keydown` only while `open` is true, closes on `event.key === 'Escape'`, removes the listener on close/unmount (`return () => window.removeEventListener`). Dependency `[open]` only; handler uses stable `setOpen(false)`, no stale state.
- `frontend/src/test/routing.test.tsx` diff: imports `fireEvent`; new test opens the drawer via `Toggle navigation`, asserts `aside.sidebar.open` present, fires `keyDown(window, {key:'Escape'})`, asserts `aside.sidebar.open` gone.
- Behavior: drawer closes via toggle, scrim click, nav click (pre-existing `setOpen(false)` paths) plus new Escape path. No change to desktop sidebar rendering, routing, data fetching, or styling. Listener is absent when closed and cleaned up on unmount; no duplicate-listener or leak path. Accessibility improves (keyboard dismissal); focus outline and semantic landmarks untouched.
- Re-verified live in Phase 11 post-fix check and again here by the passing regression test (§10).

## 10. Automated regression results (Phase 12 re-run, no dependency changes)

- Backend (`python -m pytest -q` from `backend/`): **41 passed, 0 failed**, 2 pre-existing cosmetic warnings (`httpx`/`starlette` deprecation, `anyio` BlockingPortal alias). Matches Phase 10/11.
- Frontend (`npm run test -- --reporter=verbose` from `frontend/`): **22 passed, 0 failed, 4 files** (client 5, format 8, components 5, routing 4 incl. new Escape test). Matches Phase 11 post-fix expectation (Phase 10's 21/21 + 1).
- Lint (`npm run lint`, oxlint): clean, no findings.
- Build (`npm run build`, `tsc -b` + Vite): clean. `dist/index.html 0.49 kB`, `dist/assets/index-YgrqtCEo.css 10.50 kB`, `dist/assets/index-BQUIpBMc.js 671.77 kB` (+~0.16 kB vs Phase 10 from the Escape handler, expected). Only warning is the pre-existing >500 kB chunk informational (Recharts-dominated, already noted in Phase 10/11; no action).
- No dependency versions were changed to make tests pass.

## 11. Database integrity verification

- Before validation: SHA-256 `b75c75f3f2b102b45874eccdc04d73d1e8bc99816933b1bb7e9957d17366272b`, size `17,211,392` bytes, mtime `2026-09-14 23:48:02.206044`.
- After validation (backend suite + frontend suite + lint + build): identical hash, size, and mtime. No write occurred.
- Note: the task brief prints a 63-char truncated fingerprint (`...66272`); the full 64-char SHA-256 ends `...66272b`. Phase 10's abbreviation `b75c75f3…6272b` matches the full value.
- Row counts (read-only): `ao01_baseline_total` 20, `ao02_band_contribution` 238, `ao03_scenario_comparison` 105, `ao04_band_variance` 420, `ao05_order_reading` 60108, `ao06_quality_summary` 125. Matches expected `20 / 238 / 105 / 420 / 60,108 / 125`.
- Verdict: database immutable. No STOP condition triggered.

## 12. Generated-file hygiene

- `git ls-files --others --exclude-standard`: only the 3 release-scope docs. No stray untracked source, screenshot, log, coverage, or OS file.
- `git status --ignored --short` confirms correctly ignored: `.pytest_cache/`, `backend/.pytest_cache/`, `backend/app/__pycache__/`, `backend/app/routers/__pycache__/`, `backend/tests/__pycache__/`, `data/processed/*` (incl. `marginmap.db` via `*.db`), `frontend/dist/`, `frontend/node_modules/`, `powerbi/page*_values.csv`, `sample_-_superstore.xls`, plus root `*.zip` (`archive.zip`, `Dataset 1/2`).
- Tracked tree contains only `frontend/.env.example` (`VITE_API_BASE_URL=http://127.0.0.1:8000`, no secrets). No `.env` file exists. No `node_modules`, `dist`, `__pycache__`, `.pytest_cache`, `.venv`, local DB, ZIP, screenshot, or browser artifact is tracked.
- Recursive search for `*.png/*.jpg/*.log/*.tmp` in the repo root returned none. `frontend/dist/` exists from the verification build but is ignored per `frontend/.gitignore`.
- No `.gitignore` change is needed. No legitimate artifact was deleted.

## 13. Final release scope

Exact files that SHOULD be in the eventual final commit (staged selectively, not `git add -A`):

1. `frontend/src/components/layout/AppShell.tsx`
2. `frontend/src/test/routing.test.tsx`
3. `docs/PHASE_10_END_TO_END_QA.md`
4. `docs/FINAL_RELEASE_CHECKLIST.md`
5. `docs/PHASE_11_GRAPHICAL_BROWSER_QA.md`

This Phase 12 audit file (`docs/PHASE_12_GIT_RELEASE_SCOPE_AUDIT.md`) is a working-paper record of the staging boundary. Whether to include it in the final commit is a user decision; the 5 files above are the required release scope either way. Nothing was staged in this phase.

## 14. Explicit excluded / pre-existing changes

- All 53 `powerbi/*` modified files listed in §5: EXCLUDED. Reason: unrelated pre-existing Desktop churn + environmental settings/view state, zero TMDL/DAX/query change, predates Phase 11, would pollute the release diff. Leave untouched; do not restore, stage, or commit.
- Ignored artifacts (§12): never stage.
- No other exclusions. No accidental analytical/API/SQL/DAX change was found.

## 15. Remaining risks / gaps

1. `docs/FINAL_RELEASE_CHECKLIST.md` line 7 currently reads `clean tree` as a checked item. The tree is dirty (55 modified incl. pre-existing powerbi churn + 3 untracked). The line was accurate as a Phase 10 baseline statement but is stale as a current-state claim. Before commit, reword to the staging boundary (e.g. `clean except the 5 release-scope files; 53 powerbi churn files intentionally unstaged`) and re-check `git status` at staging time. Do not claim `committed/pushed/clean` until true. No edit was made in this phase to avoid rewriting history without approval.
2. Residual NOT VERIFIED items carried forward from Phase 11 (non-blocking): DevTools-GUI eyeball, physical-device touch, screen reader, non-Chromium browsers. Risk minimal (standard React + Recharts + CSS, no browser-specific APIs).
3. Pre-existing informational items (no action): `frontend/public/icons.svg` 5 KB leftover, unused `@testing-library/user-event`, ~672 kB bundle without code-splitting.
4. Power BI churn will reappear every time Desktop opens the PBIP. Consider documenting `activePageName`/`securityBindingsSignature`/`filterConfig` stripping as expected local noise so future audits do not re-investigate.

## 16. Recommendation for next step

Ready for `Final staging + commit review` with selective staging of exactly the 5 files in §13 (plus an explicit user decision on this Phase 12 file). Suggested pre-commit: fix the checklist `clean tree` wording per §15.1, run `git status --short`, `git diff --cached --stat`, and `git diff --cached` review, then commit with a message describing Phase 10 QA + Phase 11 rendered QA + Escape fix. Do NOT include any `powerbi/*` hunk. Do NOT push until the user explicitly requests it.

*End of Phase 12 audit. Release is NOT marked complete; this establishes the evidence-based staging boundary only.*
