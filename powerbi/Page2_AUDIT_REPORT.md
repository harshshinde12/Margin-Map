# Phase 7B Page 2 — Implementation Audit Report

## 1. Implementation status

Page 2 — Discount-Band Contribution Analysis is implemented as a verified, deterministic bundle built by `powerbi/page2_build.py`. All ten required documents were read before building; no conflicts were found (238-row scope, ORDER-authoritative / LINE-partial separation, 200.0476 gap, 14 N/A rows, 17/17 standing, labels, and caveats agree across Phase 5, Gate 10 records, the AO-02 freeze, the Phase 7A foundation, and the 7B build spec).

## 2. Environment limitation

Power BI Desktop is unavailable on this machine (no `PBIDesktop.exe`, no Power BI Desktop install directory), so no `.pbix` binary was created or fabricated, per the task boundary and the Phase 7A safety rule. `Page2_Report_Layout.json` is the complete Desktop build instruction; `Page2_preview.html` renders the page with verbatim SQLite values for review.

## 3. Exact files created

```text
powerbi/page2_build.py
powerbi/page2_contribution_values.csv  (ignored, *.csv policy; regenerable)
powerbi/Page2_Report_Layout.json
powerbi/Page2_preview.html
powerbi/Page2_AUDIT_REPORT.md  (this file)
```

## 4. Page name

```text
Page 2 — Discount-Band Contribution Analysis
```

## 5. Imported source view

`contribution_by_band` from `data/processed/marginmap.db` (Import, all columns Text). The builder asserts via query tracking that no other view or table was read.

## 6. Source artifact and quality evidence

- Source artifact: `phase4c_band_contribution.csv` (238 rows), byte-identical to the SHA-256 recorded in its quality JSON (verified this run).
- Frozen quality evidence: `phase4c_band_contribution_quality.json`, 17/17 checks PASS (all statuses PASS, verified this run).
- SQL layer re-validation: `python sql/validate_sql_outputs.py` 13/13 PASS.

## 7. Grain and basis authority

- Grain: `Overall × discount band` (uniform across all 238 rows).
- ORDER basis: authoritative (119 rows: B0–B5 + TOTAL × 17 metrics).
- LINE basis: partial companion `LINE_PARTIAL_EXCL_AMBIGUOUS` (119 rows), gap 200.0476 to ORDER TOTAL, shown in a separately labeled section only.
- Status: `OBSERVED BASELINE` throughout; no hypothetical content.

## 8. Visuals included

- ORDER section: clustered bar chart of stored `contribution_profit` by band (B0–B5 bars + visually separated TOTAL cross-check bar) and a full 17-metric × 7-band matrix with the TOTAL column separated.
- LINE section: separately headed companion table (same matrix shape, partial values only, gap note attached).
- Text: metadata strip, N/A-reasons footnote, methodology/limitations note, standing-caveat box.
- No pie/line/forecast/AI/decomposition visuals; no waterfall.

## 9. Metrics/fields displayed

All 17 frozen metrics per block: `net_revenue`, `gross_revenue`, `discount_amount` (revenue forgone), `wad`, `revenue_realization_rate`, `modeled_gross_profit`, `modeled_gross_margin_pct`, `freight_cost`, `cost_to_serve`, `contribution_profit`, `contribution_margin_pct`, `quantity`, `order_count`, `line_count`, `neg_contribution_orders`, `low_sample_flag`, `neg_contribution_lines`. AO-02 carries no standalone `modeled_cogs` row (verified); none was fabricated — COGS treatment is carried via the modeled gross rows and the methodology note.

## 10. N/A handling

Exactly 14 empty-`metric_value` rows (verified set): the 7 LINE-block `neg_contribution_orders` rows and the 7 ORDER-block `neg_contribution_lines` rows. Each renders as `N/A *` with its exact frozen reason (`definition_ref` + `limitation`) in the footnote and hover title. Never zero-filled, never dropped.

## 11. Formatting and labeling decisions

- Display formatting only; every stored string embedded verbatim (`data-source-value`) and round-trip verified; formatting reversible to source.
- CUR → `$X,XXX.XX`; PCT (stored percent numbers) → `X.XX%`; DEC → `0.XXXX`; CT → integers; Flag/Label text verbatim; empty → `N/A`.
- Visible labels: `OBSERVED BASELINE — CONTRIBUTION-BAND ANALYSIS`; `ORDER — AUTHORITATIVE` / `LINE — PARTIAL`; grain; source view and artifact; `17/17 PASS`; TOTAL separated; gross-vs-contribution-vs-forgone rule; assumptions; the §6 standing caveat.

## 12. Gate 10 compliance

All 15 task §6 items PASS: observed-baseline labeling; grain shown; source view + artifact shown; ORDER authoritative; LINE partial; 17/17 shown; flags and limitations shown; ORDER/LINE separated; TOTAL separated; N/A with reasons; profit concepts distinguished; assumptions shown; no forecast/causal/demand/optimization language (verified by scan of the bundle for prohibited terms); no deferred views or unsupported metrics; frozen artifacts read-only.

## 13. Exact validation check names and results

- `[db-exists]` PASS — C:\Users\Harsh Shinde\Desktop\Margin Map\data\processed\marginmap.db
- `[view-exists]` PASS — contribution_by_band present
- `[columns-match]` PASS — 11/11 frozen columns in order
- `[row-count-238]` PASS — 238/238 rows (table and view agree)
- `[source-view-only]` PASS — only AO-02 objects read: ['ao02_band_contribution', 'contribution_by_band', 'sqlite_master']
- `[band-order]` PASS — B0,B1,B2,B3,B4,B5,TOTAL in rowid order, both bases
- `[basis-separation]` PASS — ORDER 119 + LINE 119, never blended
- `[total-row-placement]` PASS — TOTAL block present with 17 metric rows in each basis
- `[metric-set]` PASS — 17/17 frozen metrics in frozen order per block
- `[standing-grain]` PASS — uniform OBSERVED BASELINE at band grain
- `[spot-values]` PASS — ORDER TOTAL 565116.94183; LINE gap 200.0476
- `[na-preserved]` PASS — 14/14 N/A rows with frozen reasons intact
- `[quality-standing]` PASS — phase4c_band_contribution_quality.json 17/17 PASS
- `[frozen-byte-identical]` PASS — AO-02 CSV byte-identical (fb568bd33ae4…)
- `[determinism-in-run]` PASS — two in-process builds byte-identical
- `[language-scan]` PASS — no forecast/causal/demand/optimization wording
- `[bundle-csv-verified]` PASS — page2_contribution_values.csv identical to DB source
- `[bundle-html-verified]` PASS — 224 stored values verbatim + 14 N/A + labels + caveat
- `[bundle-layout-verified]` PASS — layout: ORDER/LINE sections, matrix+bar+table, no DAX, no rels
- `[bundle-audit-verified]` PASS — asserted post-write by the builder: this file lists every check name above plus live git status (see console output for the PASS line).

## 14. Frozen-artifact protection

Database opened read-only (`mode=ro`) throughout; loader never re-executed; no manual DB edits. No Phase 4C script, CSV, quality JSON, or freeze document modified. `phase4c_band_contribution.csv` re-hashed byte-identical this run; SQL-layer `frozen-unchanged` 6/6.

## 15. Determinism and failure behavior

- Directly tested: this run built every artifact twice in-process and asserted byte equality before writing (`determinism-in-run`); written files are re-read and compared (`bundle-*-verified`). Re-running the script must reproduce identical bytes (verified by the operator via a second execution).
- Code-inspection: single-view-only query tracking; presentation-only formatting/filtering (reversible `fmt`); fail-loud `fail()` before any write.
- Inherited: AO-02 frozen 17/17 validation and SQL-layer 13/13 validation are reused as standing evidence, not re-executed logic.

## 16. Exact Git status

```text
?? docs/PHASE_7B_POWER_BI_REPORT_BUILD_SPEC.md
?? powerbi/MarginMap_Phase7B.pbix
?? powerbi/Page1_AUDIT_REPORT.md
?? powerbi/Page1_Report_Layout.json
?? powerbi/Page1_preview.html
?? powerbi/Page2_AUDIT_REPORT.md
?? powerbi/Page2_Report_Layout.json
?? powerbi/Page2_preview.html
?? powerbi/Page3_AUDIT_REPORT.md
?? powerbi/Page3_Report_Layout.json
?? powerbi/Page3_preview.html
?? powerbi/Page4_AUDIT_REPORT.md
?? powerbi/Page4_Report_Layout.json
?? powerbi/Page4_preview.html
?? powerbi/Page5_AUDIT_REPORT.md
?? powerbi/Page5_Report_Layout.json
?? powerbi/Page5_preview.html
?? powerbi/Page6_AUDIT_REPORT.md
?? powerbi/Page6_Report_Layout.json
?? powerbi/Page6_preview.html
?? powerbi/page1_build.py
?? powerbi/page2_build.py
?? powerbi/page3_build.py
?? powerbi/page4_build.py
?? powerbi/page5_build.py
?? powerbi/page6_build.py
```

## 17. Files to commit later

```text
powerbi/page2_build.py
powerbi/Page2_Report_Layout.json
powerbi/Page2_preview.html
powerbi/Page2_AUDIT_REPORT.md
```

(The CSV stays ignored under `*.csv`; regenerable via the builder.)

## 18. No commit or push

Confirmed. No `git add`, `commit`, or `push` executed; Page 3 not begun.

## 19. Blocking and non-blocking issues

- Blocking: none.
- Non-blocking: no `.pbix` binary (environment has no Power BI Desktop; layout JSON + preview provided instead, same as Page 1). Prohibited-term scan is a literal-substring check (documented limit).
