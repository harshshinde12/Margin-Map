# Margin Map — Full Remediation Report

## 1. Executive Summary

Forensic audit of RAW → AO → SQLite → API → React → Power BI found the pipeline
mathematically sound at its core (row preservation, revenue reconciliation,
SUM/SUM margins, fail-loud gates) but with real defects: a postal-code
zero-loss bug, validation/identifier-check weaknesses, unit-unaware charts,
N/A zero-filling, grain-mixing filter options, misleading scenario/WAD labels,
and documentation that hid uncertainty. FIXED items below were corrected with
evidence and revalidated end-to-end. Structural limitations that cannot be fixed
without new source data (modeled-COGS circularity, uniform-pp scenario bounds,
returns-as-context, ±5pp band width, Power BI Desktop modeling risks) are
documented as KNOWN LIMITATIONS, not patched over. No Power BI Desktop churn
file was touched. NO COMMIT, NO PUSH.

Status: **PASS WITH LIMITATIONS**.

## 2. Baseline

- HEAD `dad0f24`, branch `main`, origin/main in sync.
- 53 pre-existing unstaged Power BI Desktop churn files verified identical to the
  Phase 12 record (137 insertions / 613 deletions signature) before any work.
- DB before: SHA-256 `b75c75f3…6272b`, 17,211,392 bytes, rows
  20/238/105/420/60108/125. Backend 41/41, frontend 22/22, build clean.
- AO CSV hashes recorded before rebuild (band_contribution `fb568bd3…`,
  baseline `6782330a…`, variance `43bc0b6c…`, order `0966d89e…`,
  scenario `7d808870…`, quality `eeace146…`).

## 3. Data Lineage

| Layer | Artifact | Source | Grain | Produced By | Consumed By |
|------|----------|--------|-------|-------------|-------------|
| Raw | `archive.zip` → `Sample - Superstore.csv` (9,994×21, latin1) | Superstore US slice | order line | external | `prepare_fact_sales.py` |
| Clean | `fact_sales.csv` (9,994×25) | raw | line (`row_id`) | `prepare_fact_sales.py` | dimension, benchmarks, cogs |
| Dimension | `dim_product.csv` (1,894) | fact | product combo | `build_product_dimension.py` | cogs join |
| Benchmarks | `subcategory_margin_benchmarks.csv` (17) | fact + industry refs | sub-category | `build_subcategory_benchmarks.py` | cogs join |
| Modeled | `fact_sales_cogs.csv` (9,994) | fact+dim+bench | line | `apply_modeled_cogs.py` | phase 2 |
| Cost-to-serve | `fact_margin_map_phase2.csv` (9,994) | cogs + Shipping Cost join + returns flags | line | `build_phase2_fact.py` | order fact, 2C, 3B, 4B/C |
| Order | `order_margin_map_phase2.csv` (5,009) | phase-2 line | order | `build_phase2_order_fact.py` | 3B, 4B/C |
| Analysis | `discount_*_summary.csv`, `phase4b_*.csv` | phase-2 | band/scenario | `build_phase3b_*`, `build_phase4b_*` | phase 4C |
| AO | `phase4c_*.csv` (20/238/105/420/60108/125) | phase 2/3B/4B | TOTAL/band/scenario/order/check | `build_phase4c_*` | SQLite, API, React, Power BI |
| SQLite | `marginmap.db` | AO CSVs | AO grains | `sql/load_data.py` | API |
| API | FastAPI read-only GET | SQLite views | AO grains | `backend/app` | React |
| React | 6 pages | API JSON strings | display | `frontend/src` | user |
| Power BI | PBIP (CSV-partitioned) | `pageN_*_values.csv` from AO | report grains | `pageN_build.py` + Desktop | stakeholder |

Undocumented/duplicated: freight exact-float join duplicated per script without
shared tolerance helper; WAD/band helpers re-implemented per script (identical
logic, no single import); `basis` discipline enforced by convention only.

## 4. Raw Data Findings

Canonical source `archive.zip`/`Sample - Superstore.csv` confirmed (9,994 rows,
sales 2,297,200.86, profit-quarantined 286,397.02). Zero nulls/blanks. Grain is
VALID order-line (Row ID PK; 5,009 orders, avg ~2 lines; max 14). One true
near-duplicate pair (rows 3406/3407) retained (UNKNOWN-freight evidence).
`Product Name` unsafe as key (1,862 IDs vs 1,850 names, 32 multi-name IDs,
FUR-BO-10002213 dual-product collision, OFF-PA-10001970 dual-price ID).
Postal codes mixed 5-digit/4-digit in raw text. Decoy sources
(`sample_-_superstore.xls`, Global zips) excluded with evidence.

## 5. Cleaning Findings

FIXED: postal zero-loss (`str(int)` → `zfill(5)`; 449 4-digit → 0; `05408`
recovered on 11 rows); null/blank counter `|` → `+`; dimension combo check now
tuple-membership; key-separator collision guard added.
NOT A DEFECT / LIMITATION: 3406/3407 retained; implied-price flag stays narrow
by design (general conflict flag exists separately).

## 6. Grain Findings

INTENTIONAL DESIGN: line fact (`row_id`), order fact (5,009), customer/product
cuts, AO grains as frozen. No m:m amplification in shipped joins (freight
9,994/9,994 exact). Returns crosswalk set-based check noted as weak but
currently passing; left as LIMITATION (no data to strengthen).

## 7. Revenue Model Findings

No double-discount, no sign errors, gross-vs-net dual reconciled ≤1e-6.
FIXED (display only): WAD now 4dp with unit (`0.1979 DEC`).

## 8. Profitability Findings

All margins SUM/SUM, never averaged percentages (verified). Zero-revenue NULL
guards are dead code (no such rows; validator would abort) — documented as
LIMITATION, not changed (changing abort semantics risks masking future bad
input).

## 9. Modeled COGS Findings

KNOWN LIMITATION (P0, cannot fix without real cost data): implemented method is
the revenue-percentage rule the methodology doc itself rejects as circular
(row margins equal benchmarks by construction). 15/17 benchmarks are category
fallbacks; Paper 38% contradicts its 17.14% anchor by ~21pp. Rankings restate
assumptions × mix. Remediation: README now carries the ±5pp band next to every
headline; COGS stays labeled MODELED; no fake precision added.

## 10. Cost-to-Serve Findings

Baseline is freight-observed + returns/support OFF (excluded, not zero).
FIXED docs: README + FINANCIAL_MODEL §7 now state OFF semantics and point to
`COST_TO_SERVE_MODEL.md`. Freight exact-float join and `freight_order_total`
do-not-sum field left as LIMITATIONS (brittle but currently exact).

## 11. Discount Band Findings

Boundaries verified inclusive-upper/exclusive-lower with round(6); every
eligible row classified exactly once; totals reconcile. FIXED (display):
charts no longer zero-fill N/A; y-axes unit-aware. Boundary-flip sensitivity
documented as LIMITATION.

## 12. Scenario Findings

INTENTIONAL DESIGN + FIXED labels: ±0.00pp runs are identity controls (zero
variance by construction); universal pp-shifts beyond bounds fail loud by
design, so only 0.00 identities ship. React labels dropped the contradictory
`±` (`Discount increase 0.00 pp (identity control)`). Not-a-forecast caveats
retained and verified rendered.

## 13. AO Output Findings

Row counts recomputed plausible (14×17=238, 3×35=105, 3×7×20=420,
5,009×12=60,108, 75+47+3=125); uniqueness holds on documented grains;
cross-AO numerics reconcile (gaps ≤1.2e-10 except documented 200.05
LINE-partial difference). Metric names not conformed across AOs and repr-vs-
rounded strings require CAST+tolerance joins — documented LIMITATIONS, not
renamed (renaming would break API/Power BI contracts).

## 14. SQLite Findings

Rebuilt via `sql/load_data.py`; `validate_sql_outputs.py` 13/13 PASS.
TEXT-NOT-NULL byte preservation, no PK/FK, `ORDER BY rowid`, page-scoped
semantics retained as INTENTIONAL DESIGN (changing schema would break
fidelity). No manual row edits.

## 15. API Findings

Transport-only confirmed (no analytics, string passthrough, verbatim
precision). `/api/orders` page-scoped `count` and narrow filter surfaces
documented as LIMITATIONS (changing envelopes would break the frontend
contract mid-remediation).

## 16. React Findings

FIXED: unit-aware tooltips/axes (Bands + Variance); N/A excluded from charts
(tables still show N/A); Basis fixed to ORDER/LINE (no All-bases blending);
scenario/metric selects fixed to single values; WAD 4dp + unit + exact-value
title; `wad`→`WAD` label map; Quality values formatted by unit; Quality header
badge derived from data. Pagination page-scoped `count` kept as LIMITATION
(no API total available).

## 17. Power BI Findings

No intentional PBIP change (AO metrics byte-identical, so none required).
Pre-existing 53-file Desktop churn preserved untouched. Documented risks for a
future Desktop pass if AO ever changes: auto-detected metric_name
relationship, `Sum(metric_value)` cards, metric slicer, AO05 double-type
coercion, hard-coded measure scopes, absolute CSV-partition paths,
cross-page sync defaults, N/A handling.

## 18. Documentation Findings

FIXED: README headlines carry ±5pp bands + dispersion caveat; CTS OFF
semantics; FINANCIAL_MODEL §7 supersession note pointing to COST_TO_SERVE.
Remaining blurred `Actual`/variance language noted as LIMITATION.

## 19. Complete Issue Register

Supersedes prior lists. Severities rescored post-fix.

| ID | Severity | Layer | Problem | Root Cause | Evidence | Fix | Downstream Impact | Status |
|----|----------|-------|---------|------------|----------|-----|-------------------|--------|
| F-01 | P2 | clean | Postal leading-zero loss (449 4-digit, `05408`→`5408`) | `str(int(float))` coercion | `prepare_fact_sales.py:127`; fact 449×4-digit, 0×`05408` before | `zfill(5)` digit-pad | fact + cogs + phase2 line postal only; AO metrics identical | FIXED |
| F-02 | P3 | clean | Null/blank counter `\|` misreports | bitwise OR on ints | `prepare_fact_sales.py:176` | `+` | QA counts correct | FIXED |
| F-03 | P2 | dim | Combo check validated id/name independently | `in` on separate sets | `build_product_dimension.py:127-129` | tuple-membership in fact combos | key-integrity claim now sound | FIXED |
| F-04 | P3 | dim | Key separator collision unchecked | pure f-string | `build_product_dimension.py:35` | fail-loud guard | latent ambiguity closed | FIXED |
| R-01 | P1 | react | Tooltip/axis ignored unit (`$` for %/pp) | hard-coded currency | `DiscountBands.tsx:233-237`, `Variance.tsx:172-175` | `formatByUnit` + unit-aware axes | correct display | FIXED |
| R-02 | P1 | react | N/A zero-filled in charts (`??0`) | no null filter | `DiscountBands.tsx:65`, `Variance.tsx:61` | exclude nulls from charts | N/A no longer plotted as 0 | FIXED |
| R-03 | P1 | react | Basis `All` blended ORDER+LINE grains | `allLabel` + dropped param | `DiscountBands.tsx:137`, `client.ts:34-40` | basis fixed ORDER/LINE | authoritative grain enforced | FIXED |
| R-04 | P2 | react | WAD `0.198` no unit, 3dp | `formatDecimal` default + no unit | `Executive.tsx:159`, `format.ts:78` | 4dp + `WAD ·` label + unit sub + title | `0.1979 DEC` | FIXED |
| R-05 | P2 | react | `Wad` label; 3 names for one metric | generic humanizer | `format.ts:107`, `Orders.tsx:95` | `wad`→`WAD` map | consistent | FIXED |
| R-06 | P2 | react | `±0.00pp` implies movement in identity controls | contradictory label | `Scenarios.tsx:29-30`, `Variance.tsx:29-30` | `0.00 pp (identity control)` | honest | FIXED |
| R-07 | P2 | react | Quality values unformatted; hard-coded PASS badge | raw render + static badge | `Quality.tsx:72,110` | `formatByUnit` + derived badge | correct/robust | FIXED |
| R-08 | P3 | react | Scenario/metric `Select` empty option fetched all | `allLabel` | `Scenarios.tsx:146`, `Variance.tsx:129,137` | removed | single-value discipline | FIXED |
| D-01 | P2 | docs | Headlines hid ±5pp uncertainty; CTS OFF blurred; freight note stale | point-only copy | `README.md:68-73`, `FINANCIAL_MODEL.md:109` | bands + OFF semantics + supersession note | honest | FIXED |
| L-01 | P0 | model | COGS circular (margins restate benchmarks) | revenue-percentage rule | `COGS_MODEL.md:64-65` vs `apply_modeled_cogs.py:187` | none possible w/o cost data | rankings carry zero independent cost info | KNOWN LIMITATION |
| L-02 | P1 | model | Uniform pp-shifts self-defeating beyond 0.00 | universal scope + fail-loud bounds | `build_phase4b_*` bounds; masses at 0.00/0.80 | none (design) | scenario space under-covered | KNOWN LIMITATION |
| L-03 | P1 | model | Returns retained in revenue (no refund leg) | flag-only semantics | `build_phase2_fact.py:270-271` | none (no refund data) | contribution overstates up to 5.9% order-profit | KNOWN LIMITATION |
| L-04 | P1 | model | ±5pp band narrower than 10–21pp evidence gaps | un-derived range | `COGS_SENSITIVITY.md:64-67` | documented, not widened silently | robustness overstated if band misread | KNOWN LIMITATION |
| L-05 | P2 | sql/api/pbi | TEXT schema, page-scoped counts, PBIP modeling risks | intentional contracts | `schema.sql`, `orders.py:72`, PBIP TMDL | documented, not rebuilt | join/aggregate discipline required | KNOWN LIMITATION |

Prior audit theater/low items (sparsity check both-PASS, `fillna(1)`, `min_count=0`,
set-based crosswalk, filename truncation, exact-float checks, freeze brittleness)
remain as documented LIMITATIONS; none affected shipped values.

## 20. Changes Implemented

Upstream: `prepare_fact_sales.py` (postal, counter), `build_product_dimension.py`
(combo check, separator guard), 5× Phase 4C frozen-hash updates (fact gate only).
Frontend: `format.ts` (DEC 4dp, WAD map), `Executive/DiscountBands/Scenarios/
Variance/Quality` (above), `format.test.ts` (+2 tests). Docs: `README.md`,
`docs/FINANCIAL_MODEL.md`. No API, SQL schema, AO grain, or PBIP intentional
changes.

## 21. Before vs After Metrics

- Postal: 449 4-digit → 0; `05408` 0 → 11 rows; rows 9,994 and sales total
  2,297,200.86 unchanged.
- AO metrics: 5/6 byte-identical; quality_summary only hash-record rows changed.
- DB: `b75c75f3…` → `8441f767…`, same size 17,211,392, same row counts.
- WAD display `0.198` → `0.1979 DEC`; Orders `Wad` → `WAD`; scenarios
  `±0.00 pp` → `0.00 pp (identity control)`.

## 22. Downstream Artifacts Regenerated

fact_sales → dim/benchmarks → cogs/sensitivity → phase2 line/order/2C →
phase3B → phase4B (0.10, +0.00, −0.00) → phase4C (6 AOs) → SQLite rebuild.
Power BI intentionally NOT regenerated (AO metrics identical; churn preserved).

## 23. Test Results

- Backend 41/41 (2 pre-existing warnings). Frontend 23/23 (22 + 1 new DEC/WAD).
  Lint clean. Build clean (chunk-size informational only). SQL validation 13/13.

## 24. Graphical QA Results

Real Chrome/Blink via Playwright, dev stack: 7 routes (6 pages + 404) zero
pageerrors; WAD `0.1979` rendered; `WAD` label in Orders; identity-control
labels rendered, no `±`; mobile drawer Escape open→closed; executive sweep zero
errors. Screenshots not persisted (read-only traffic + ad-hoc run).

## 25. Remaining Limitations

L-01…L-05 above; plus: single UNKNOWN return retained; 2 NULL-freight lines
held at order; 50 ORDER-only negative lines; boundary-flip band sensitivity;
no touch/SR/multi-browser pass; bundle ~672KB.

## 26. Resume-Level Technical Summary

Reproducible US-Superstore profitability stack (9,994 lines → 5,009 orders):
observed revenue $2.30M, modeled COGS $1.49M (benchmark-driven, ±5pp
sensitivity), freight-observed CTS, 20/238/105/420/60,108/125 frozen AOs in
SQLite, read-only FastAPI (41 tests), React (23 tests) with unit-honest
formatting, Power BI cross-check. Remediation fixed data-integrity (ZIP codes),
validation soundness, and display honesty without inventing costs or forecasts.
