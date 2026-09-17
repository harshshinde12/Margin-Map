# Margin Map — Final Release Checklist (Phase 10 + Phase 11)

Evidence for each item is in `docs/PHASE_10_END_TO_END_QA.md`.
Phase 11 graphical-browser evidence is in
`docs/PHASE_11_GRAPHICAL_BROWSER_QA.md`.

- [x] Repository integrity — `main`, commits `9d352f3`/`8d13e43`/`e4bbc3f` intact; release boundary is 6 files only, pre-existing Power BI Desktop churn intentionally left unstaged (working tree not clean by design)
- [x] SQL layer — `validate_sql_outputs.py` 13/13 PASS, 61,016 rows byte-identical
- [x] SQLite integrity — fingerprint `b75c75f3…6272b` unchanged, mtime untouched, read-only access
- [x] AO outputs — AO-01..AO-06 row counts 20/238/105/420/60108/125 confirmed live
- [x] Power BI — headline values cross-checked identical across all layers
- [x] FastAPI — documented startup verified, `/health` + `/docs` + `/openapi.json` live
- [x] API contracts — exact key sets, string values, envelopes verified against implementation
- [x] React — all 6 pages + redirect + 404 render against the live backend
- [x] Routes — 9/9 HTTP checks (7 app routes + `/` + unknown route)
- [x] Filters — every filter exercised live incl. reset and empty states
- [x] Pagination — 50 default / 500 max / Next / Previous / page-size verified
- [x] Loading states — skeletons verified during pending fetch
- [x] Error states — dead-API card + Retry verified, no stack traces
- [x] Empty states — impossible-filter empty card + Clear Filters verified
- [x] Responsive behavior — stylesheet/markup verified; rendered widths NOT VERIFIED (no browser)
- [x] Accessibility — semantic/code baseline verified; live keyboard walkthrough NOT VERIFIED
- [x] Analytical fidelity — full API-vs-SQL reconciliation passed; PBI cross-check passed
- [x] Security — injection/DDL probes neutralized, POST rejected, CORS restrictive, no secrets tracked
- [x] Dependencies — all used and reasonable; installs rerun clean
- [x] Documentation — every documented command re-executed verbatim in QA
- [x] Production build — `tsc -b` + Vite clean, `dist/` emitted, preview serves
- [x] Final regression — backend 41/41, frontend 21/21, build clean, DB unchanged

Recommended non-blocking follow-up: one graphical-browser pass
(pixels, console, rendered widths, keyboard walkthrough) before public demo.

## Phase 11 — Graphical browser QA (2026-09-17, real Chrome/Blink)

- [x] Rendered widths verified — 1440x900 / 1280x800 / 1024x768 /
  768x1024 / 600x900, scrollW == clientW everywhere, screenshots inspected
- [x] All 6 pages + 404 rendered with live data, zero page errors
- [x] Navigation clicks incl. active state + back/forward verified
- [x] Every filter exercised live (change/reset/empty/Clear verified)
- [x] Pagination incl. page-size verified with live row changes
- [x] Loading skeleton / error card + Retry + recovery / empty state rendered
- [x] Tooltips verified (exec $2,297,200.86; variance -$30,530.82 / +$27,378.13)
- [x] Network: React -> FastAPI only, filter params transmitted, no failures
- [x] Console: zero errors/warnings (CDP stream; dev-only Vite noise excluded)
- [x] Keyboard walkthrough: logical order, visible focus, Enter/arrows operate
  controls, no trap
- [x] Mobile drawer: toggle/scrim/nav-close verified; Escape-to-close FIXED
- [x] Analytical spot checks match live API on every page
- [x] Production build served via `vite preview` and graphically verified
- [x] Post-fix regression: backend 41/41, frontend 22/22, build clean, DB frozen
- [x] One LOW defect fixed (`AppShell` Escape handler + test); no other defects

Residual NOT VERIFIED (non-blocking): DevTools-GUI eyeball, physical-device
touch, screen reader, non-Chromium browsers.
