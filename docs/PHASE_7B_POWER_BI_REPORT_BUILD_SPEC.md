# Phase 7B — Power BI Report Build Specification

```text
SPECIFICATION ONLY — NO .PBIX, NO VISUALS BUILT, NO CALCULATIONS ADDED
```

## 1. Status and Authority

This document is a complete, implementation-ready specification for building the Margin Map Power BI report in a later step. It performs no implementation: no `.pbix` is created, no visual is built, no DAX/Power Query calculation is added, and no frozen artifact is modified.

Binding sources (read in full before building):

* `docs/PHASE_5_DISPLAY_SCOPE_AND_CONVENTIONS.md` — approved display scope, inventory (§4), binding display rules (§5), grain/authority rules (§6), deferred views (§7), approval (§9).
* `docs/PHASE_6_SQL_DATA_LAYER.md` and `docs/PHASE_6_SQL_DATA_LAYER_FREEZE.md` — frozen SQL layer: six tables/views, row counts 20/238/105/420/60108/125, TEXT fidelity, rebuild/validate procedure.
* `docs/PHASE_7_POWER_BI_FOUNDATION.md` — verified connection foundation: source path `data/processed/marginmap.db`, ODBC Import method, no-relationship rule.
* `docs/PHASE_4C_AO-01_FREEZE.md` through `docs/PHASE_4C_AO-06_FREEZE.md` — per-output frozen scope, metric lists, validation evidence, confirmed values.
* `sql/views.sql` — the six thin read-only views (sole Power BI sources).
* Gate 10 (`docs/PHASE_4B_DECISION_LOG.md`, approved 2026-09-13) — binding on every visual; constrains but authorizes none.

SQLite inspection in this task was read-only (`mode=ro`). Metric lists below were verified against the live database on 2026-09-15 and match the AO freeze records.

## 2. Global Binding Rules (Every Page, No Exceptions)

1. **Observed vs hypothetical separation.** `OBSERVED BASELINE` and `HYPOTHETICAL_ARITHMETIC_SENSITIVITY` values are never merged into an unexplained number. On scenario pages, `baseline`, `hypothetical`, and `variance` blocks occupy distinct visual areas.
2. **Absolute vs margin-unit separation.** Currency/count variances and margin changes in percentage points are separate visuals or separate columns. Margin-point fields (`margin_change_pp`, `gross_margin_change_pp`) are labeled `pp`, never `%`.
3. **Identity labels on every page.** Scenario type (`scenario_id`), discount input form and value, reporting grain, validation status, and quality flags are visible — not hidden in tooltips alone.
4. **Unsupported values.** Empty `metric_value` renders as `N/A` with its row's reason (`definition_ref`/`limitation`), never zero-filled, never silently omitted.
5. **Profit-concept separation.** Gross profit, contribution profit, and discount-related revenue forgone (`discount_amount` / `variance_discount_amount`) are distinct rows/columns with `definition_ref` traceable. They are never netted into one "profit" number.
6. **Methodology assumptions visible wherever sensitivity appears** (and summarized on baseline pages): constant observed quantity; modeled COGS; freight passthrough; return-processing costs OFF; support costs OFF.
7. **Standing caveat.** Page 3 and Page 4 carry verbatim, on-canvas:

```text
Illustrative constant-quantity arithmetic sensitivity, not a forecast.
```

Pages 1, 2, 5, 6 carry the Phase 5 long-form caveat wherever a predictive or causal misreading is possible:

```text
Illustrative arithmetic sensitivity under stated assumptions; not a forecast, causal estimate, demand prediction, or optimized-pricing recommendation.
```

8. **Permitted wording only.** Descriptive phrases allowed: "illustrative constant-quantity scenario", "arithmetic change under the stated assumptions", "conditional illustration, not a forecast". Forecast / prediction / causal / optimal / best-policy / recommendation wording is prohibited except inside this prohibition.
9. **One view per visual.** Every visual reads from exactly one imported view. No merges, joins, appends, or cross-view measures.
10. **No model relationships.** The six imported tables stay disconnected (§10). No bridge, lookup, date, or selector table is modeled.
11. **No new logic.** No DAX measures that compute new analytics, no new scenarios, no re-banding, no forecasting, optimization, segmentation, recommendations, demand/elasticity analysis, or causal interpretation.
12. **Frozen artifacts read-only.** AO scripts, CSVs, quality JSONs, freeze documents, and the `.db` file itself are never written by the report. Refresh = rebuild `.db` via `python sql/load_data.py`, re-validate, then Refresh in Power BI.

## 3. Data Source and Import Contract (All Pages)

* Source: `data/processed/marginmap.db`, six ODBC Import queries, one per view, each `SELECT * FROM <view>` with all columns kept as **Text** (§10 of the foundation doc).
* Expected row counts (fail-loud on mismatch): `baseline_total` 20; `contribution_by_band` 238; `scenario_comparison_total` 105; `variance_by_band` 420; `order_reading` 60108; `quality_summary` 125.
* Import-time validation before building any page: the four spot values (`contribution_profit = 565116.9418299999`; uniform `variance_contribution_profit = 95406.2413300001`; B5 uniform `variance_contribution = 45401.369600000005`; `overall_eligibility = ALL_SOURCES_ELIGIBLE`) and N/A volumes (14 / 6 / 42 on AO-02 / AO-03 / AO-04).

---

## 4. Page 1 — Executive Profitability Overview

### Required content (task)
KPI cards; baseline revenue; gross profit where supported; contribution profit; contribution margin; quantity; order count; `OBSERVED BASELINE` label; source and grain information; methodology assumptions; limitations and quality status.

### 4.1. Fourteen build items

1. **Purpose.** State the single authoritative baseline TOTAL against which every band reading and scenario variance is referenced. One-screen executive reference; no band, scenario, or order analysis.
2. **Approved source view.** `baseline_total` only (AO-01).
3. **Exact grain.** `TOTAL` — overall TOTAL, order economics rolled up, authoritative. All 20 rows carry `scenario_status = OBSERVED BASELINE`, `grain = TOTAL`.
4. **Source authority.** `output_name = Baseline performance summary (TOTAL)`; per-row `source_artifact` spans `order_margin_map_phase2.csv` and `fact_margin_map_phase2.csv` (cross-check / NULL-preservation notes on applicable rows). Quality standing: 18/18 checks PASS (`phase4c_baseline_total_quality.json`).
5. **Allowed fields.** Exactly the 20 frozen `metric_name` values, verified in the database (frozen order):
   `net_revenue` (CUR), `gross_revenue` (CUR), `discount_amount` (CUR, revenue forgone — not profit loss), `modeled_cogs` (CUR), `modeled_gross_profit` (CUR), `modeled_gross_margin_pct` (PCT), `freight_cost` (CUR), `cost_to_serve` (CUR, equals freight; return/support OFF), `contribution_profit` (CUR), `contribution_margin_pct` (PCT), `wad` (DEC), `revenue_realization_rate` (PCT), `quantity` (CT), `order_count` (CT), `line_count` (CT), `neg_contribution_orders` (CT), `return_yes_orders` (CT), `return_unknown_orders` (CT), `return_not_returned_orders` (CT), `null_freight_lines` (CT).
   Confirmed headline values (exact output precision): net revenue `2297200.8603000003`; modeled COGS `1493910.1284699999`; modeled gross profit `803290.7318300004`; gross margin `34.96824094542153`%; freight `238173.78999999998`; contribution profit `565116.9418299999`; contribution margin `24.600240736293262`%; WAD `0.19788653436077944`; quantity 37,873; orders 5,009; lines 9,994; negative orders 50; return cohorts 296 / 1 / 4,712; NULL-freight lines 2.
6. **Proposed visuals.**
   * Row of **card** visuals for KPIs: Net Revenue; Modeled Gross Profit + Gross Margin; Contribution Profit + Contribution Margin; Quantity; Order Count.
   * One **matrix or table** visual listing all 20 metrics with columns Metric | Value | Unit | Limitation (full baseline record, including WAD, realization, discount amount, loss/cohort context, NULL-freight indicator).
   * One **text box** for assumptions/limitations/quality (§4.8–4.10). No bar/line chart required on this page; an optional bar of the profit waterfall is **not approved** (would net distinct profit concepts) — do not add it.
7. **Required filters/slicers.** None. Page shows the full 20-row TOTAL set with no slicer. (A slicer would imply a comparison dimension that does not exist at single-TOTAL baseline.)
8. **Required labels.** `OBSERVED BASELINE` banner; grain label `TOTAL — order economics rolled up (authoritative)`; per-card `source_artifact` or a single source line naming both source files; `definition_ref` available per metric (matrix column or drill-through tooltip text, never tooltip-only for the headline cards).
9. **Required caveats.** Methodology assumptions block (constant observed quantity; modeled COGS — analytical estimate, not accounting COGS; freight passthrough; return-processing OFF; support OFF) plus the long-form standing caveat (§2.7). Return/support exclusion stated as exclusion, not as zero actual cost.
10. **Quality indicators.** "AO-01 validation 18/18 PASS" badge with quality-file name; NULL-freight indicator (2 lines, held at order, never imputed); single UNKNOWN return order `CA-2015-102015` retained note; negative-order count 50 (matches band TOTAL cross-check).
11. **N/A handling.** AO-01 has **zero** N/A rows (verified: no empty `metric_value`). No `N/A` symbol appears on this page. If a future rebuild introduces one, render as `N/A` with reason — never zero-fill.
12. **Fields/views that must not be combined.** No AO-02–AO-06 field on this page. Within the page: do not net `modeled_gross_profit` with `contribution_profit`; do not present `discount_amount` as a profit loss; do not average PCT/DEC rows; do not sum the 20 rows into a total (rows are distinct metrics, not addends).
13. **Power BI measures required.** None.
14. **Direct vs presentation calculation.** Every card/table value is a **direct imported value** (single-row lookup of one `metric_name` displayed as Text with display formatting only). Permitted presentation operations only: selecting the row by `metric_name`, numeric display formatting, and showing the paired `unit`/`limitation`. No DAX aggregation (no SUM/AVERAGE — summing distinct metrics or averaging percentages is forbidden).

---

## 5. Page 2 — Discount-Band Contribution Analysis

### Required content (task)
Discount-band table or chart; baseline contribution; contribution margin; revenue; COGS; freight; cost-to-serve; ORDER versus LINE basis; `N/A` handling; band and TOTAL treatment; quality flags and source-artifact labels.

### 5.1. Fourteen build items

1. **Purpose.** Show where baseline revenue, freight, and contribution sit across observed discount configurations (B0–B5 + TOTAL), ORDER-authoritative, with LINE-partial companions kept visibly separate.
2. **Approved source view.** `contribution_by_band` only (AO-02).
3. **Exact grain.** `Overall x discount band` with `basis` ∈ `ORDER` (authoritative) / `LINE` (partial companion). Blocks: ORDER B0–B5 + TOTAL, then LINE B0–B5 + TOTAL (14 blocks × 17 metric rows = 238 rows). All rows `OBSERVED BASELINE`.
4. **Source authority.** `output_name = Contribution by discount band (observed, ORDER basis)`; `source_artifact = discount_band_summary.csv`. Quality standing: 17/17 PASS. LINE gap of record: ORDER TOTAL minus LINE partial TOTAL = 200.0476 contribution (display with the LINE companion block).
5. **Allowed fields.** Exactly the 17 frozen `metric_name` values per block (verified): `net_revenue`, `gross_revenue`, `discount_amount`, `modeled_gross_profit`, `modeled_gross_margin_pct`, `freight_cost`, `cost_to_serve`, `contribution_profit`, `contribution_margin_pct`, `wad`, `revenue_realization_rate`, `quantity`, `order_count`, `line_count`, `low_sample_flag`, `neg_contribution_orders`, `neg_contribution_lines`.
   **COGS honesty note:** AO-02 carries **no standalone `modeled_cogs` metric row** (verified in data). The task's "COGS" item is therefore satisfied only via `modeled_gross_profit`/`modeled_gross_margin_pct` (net of modeled COGS) with the limitation text stating COGS treatment — do **not** fabricate a COGS row or derive one. (Standalone modeled COGS lives on Page 1 / AO-01.)
   Frozen distributions of record: ORDER counts B0 2055 / B1 415 / B2 1634 / B3 278 / B4 274 / B5 353 (TOTAL 5,009); negative ORDER distribution 14 / 3 / 24 / 1 / 3 / 5 / TOTAL 50; LINE TOTAL negatives 109 kept strictly on LINE grain.
6. **Proposed visuals.**
   * One **matrix** (bands B0–B5 + TOTAL as columns; metrics as rows) bound to `basis = ORDER` — the authoritative band view.
   * One **clustered bar chart** of ORDER `contribution_profit` by band (B0–B5 + TOTAL) for the headline shape.
   * One separately titled **table** for the LINE-partial companion (`basis = LINE`), headed `LINE-partial companion — not authoritative (gap 200.0476 to ORDER TOTAL)`.
   * `low_sample_flag` shown as its own row/column, never as a filter that hides bands.
7. **Required filters/slicers.** One `basis` slicer or, preferably, two pre-filtered visuals (ORDER visual filtered `basis = ORDER`; LINE visual filtered `basis = LINE`). No band slicer that hides TOTAL: B0–B5 and TOTAL stay visible together so the TOTAL cross-check is always readable. No metric-averaging aggregation.
8. **Required labels.** `OBSERVED BASELINE` banner; grain label `Overall × discount band`; basis markers `ORDER — authoritative` / `LINE — partial companion` on the respective visuals; `source_artifact = discount_band_summary.csv`; band-axis note "bands are observed discount configurations".
9. **Required caveats.** Assumptions block (same five as §2.6, short form acceptable here with pointer to Page 1 for full text); LINE-gap note (200.0476); long-form standing caveat (§2.7) on the page footer.
10. **Quality indicators.** "AO-02 validation 17/17 PASS"; `low_sample_flag` values per band; negative-distribution reconciliation note (ORDER TOTAL 50 = order-fact count 50); ORDER TOTAL contribution 565,116.94 cross-check line.
11. **N/A handling.** Exactly 14 empty-`metric_value` rows (verified): the 7 LINE-block `neg_contribution_orders` rows and the 7 ORDER-block `neg_contribution_lines` rows, each with reason text (`N/A at LINE partial grain (not licensed)…` / `N/A at ORDER authoritative grain (detail rows)…`). Render these cells as `N/A` with a reason footnote/tooltip showing the row's `limitation`. Never zero-fill, never drop the row.
12. **Fields/views that must not be combined.** Never average or blend ORDER and LINE rows (no combined "average contribution"); never sum ORDER + LINE; never import AO-01/AO-03/AO-04/AO-05/AO-06 fields into this page's visuals; never average PCT/DEC metrics across bands (margins/WAD are SUM/SUM in source — display stored row values only).
13. **Power BI measures required.** None.
14. **Direct vs presentation calculation.** All values are **direct imported values** (one stored row per basis × band × metric). Permitted presentation operations only: filtering to `basis`/`band`, pivoting metrics to matrix columns, empty→`N/A` display substitution, numeric formatting. No DAX SUM/AVERAGE/DIVIDE — any cross-band total shown must be the stored `TOTAL` row, never a client-side sum.

---

## 6. Page 3 — Scenario Sensitivity — TOTAL

### Required content (task)
Separate baseline, hypothetical, and variance sections; scenario selector or clearly separated scenario blocks; scenario type; discount input; absolute variance; percentage-point margin change; validation status; quality flags; visible standing caveat `Illustrative constant-quantity arithmetic sensitivity, not a forecast.` No unexplained baseline+hypothetical totals.

### 6.1. Fourteen build items

1. **Purpose.** Read headline arithmetic sensitivity per frozen scenario instance beside its identical-scope baseline at TOTAL grain — descriptive sensitivity allocation, not causal attribution.
2. **Approved source view.** `scenario_comparison_total` only (AO-03).
3. **Exact grain.** `Overall TOTAL` per (`scenario_id`, `block`). Instances: `uniform_replace_0.10` (uniform replacement, rate 0.10), `discount_increase_pp_0.00` (identity control, +0.00 pp), `discount_decrease_pp_0.00` (identity control, −0.00 pp). Blocks: `baseline` (13 rows, `OBSERVED BASELINE`), `hypothetical` (9 rows, `HYPOTHETICAL_ARITHMETIC_SENSITIVITY`), `variance` (13 rows incl. N/A markers). 3 × 3 × rows = 105 rows.
4. **Source authority.** `output_name = Scenario comparison at TOTAL`; `source_artifact` per instance ∈ `phase4b_scenario_uniform_0.10.csv` / `phase4b_scenario_increase_0.00.csv` / `phase4b_scenario_decrease_0.00.csv`. Quality standing: 19/19 PASS. Identity (`0.00`) instances are pipeline-integrity controls — all currency variances, both margin changes, and relative variance exactly `0.0`; they measure no economic sensitivity.
5. **Allowed fields.** Per block as verified:
   * Baseline (13): `net_revenue`, `discount_amount`, `modeled_cogs`, `gross_profit`, `gross_margin`, `freight_cost`, `cost_to_serve`, `contribution_profit`, `contribution_margin`, `wad`, `quantity`, `order_count`, `line_count`.
   * Hypothetical (9): `net_revenue`, `discount_amount`, `modeled_cogs`, `gross_profit`, `gross_margin`, `contribution_profit`, `contribution_margin`, `cost_to_serve`, `wad`.
   * Variance (13): `variance_net_revenue`, `variance_discount_amount`, `variance_modeled_cogs`, `variance_gross_profit`, `variance_contribution_profit`, `variance_freight` (= 0.0 passthrough), `variance_cost_to_serve` (= 0.0), `relative_contribution_variance` (PCT), `margin_change_pp` (PP), `gross_margin_change_pp` (PP), `low_sample_flag` (Flag), `demand_response_view` (N/A), `fixed_unit_cost_view` (N/A).
   Confirmed uniform headlines: hypothetical contribution `660523.1831600001`; variance `+95406.2413300001`; margin change `+1.0258519545365985` pp; gross-margin change `−0.1018009440449532` pp; relative variance `16.882566114731784`%; revenue variance `+280340.6757000005`.
6. **Proposed visuals.**
   * Three clearly separated **sections** on one page (or three bookmarked views): A. Baseline **table** (13 rows for the selected instance); B. Hypothetical **table** (9 rows, headed `HYPOTHETICAL — <scenario_id>`); C. Variance block: **cards** for absolute `variance_contribution_profit` and `variance_net_revenue`, plus a separate **card/table** pair for `margin_change_pp` and `gross_margin_change_pp` labeled `percentage points`, plus a small table for the remaining variance rows.
   * One **slicer** on `scenario_id` (single-select, bound to this page's table only) OR three pre-built scenario blocks with no slicer. Either is compliant; a slicer is preferred for usability provided §6.12 holds.
7. **Required filters/slicers.** `scenario_id` slicer (if used): single-select, applies to Page 3 visuals only (visual-level filter on this page's table — not a model relationship, not synced to other pages). `block` must **not** be offered as a mixer slicer; blocks are fixed sections, never user-mergeable.
8. **Required labels.** Per section: `scenario_id` + input form (`replacement_rate 0.10` vs `increase_pp 0.00` vs `decrease_pp 0.00`); `scenario_status` per block; grain `Overall TOTAL (authoritative order economics)`; units on every value (CUR / PP / PCT kept distinct); identity-instance note "control — zero variance by construction" on the two `0.00` selections.
9. **Required caveats.** The task's standing caveat verbatim and prominent on this page:

```text
Illustrative constant-quantity arithmetic sensitivity, not a forecast.
```

plus the five methodology assumptions (constant observed quantity; modeled COGS; freight passthrough; return OFF; support OFF). Freight/CTS variances exactly 0.0 by passthrough design — label as design, not finding.
10. **Quality indicators.** "AO-03 validation 19/19 PASS"; `low_sample_flag` from the variance block shown beside the variance cards; baseline-identity note (baselines identical across instances and equal to frozen baseline).
11. **N/A handling.** Exactly 6 empty rows (verified): `demand_response_view` (`N/A: RESPONSE_NOT_ESTIMATED`) and `fixed_unit_cost_view` (`N/A: COMPARATOR_NOT_IN_INITIAL_BUILD`) in each instance's variance block, each with `Marked unavailable with reason; never estimated`. Show as a two-row `N/A` table with reasons. Never zero-fill, never omit.
12. **Fields/views that must not be combined.** Never add baseline + hypothetical into an "unexplained total"; never show a variance without its sibling baseline and hypothetical sections; never mix `margin_change_pp` (pp) with `relative_contribution_variance` (percent) in one number; never pull band/order/quality rows (AO-02/AO-04/AO-05/AO-06) into these visuals; never compare across `scenario_id` values in one aggregated number (identity controls must not be averaged with the uniform scenario).
13. **Power BI measures required.** None.
14. **Direct vs presentation calculation.** All values are **direct imported values**. Permitted presentation operations only: filtering to one `scenario_id` × `block`, empty→`N/A` substitution, numeric formatting, and section layout. No variance DAX (variances are stored rows — recomputing hypo−base in DAX is prohibited duplication of frozen logic).

---

## 7. Page 4 — Scenario Sensitivity by Discount Band

### Required content (task)
Fixed baseline discount bands; no re-banding; baseline, hypothetical, and variance separation; absolute contribution variance; relative variance; percentage-point margin change; `N/A` reasons; TOTAL reconciliation; scenario and grain labels.

### 7.1. Fourteen build items

1. **Purpose.** Distribute headline sensitivity across existing baseline discount configurations (ORDER WAD bands) without recalculating bands under scenarios.
2. **Approved source view.** `variance_by_band` only (AO-04).
3. **Exact grain.** `Overall x discount band` per (`scenario_id`, `band`, `block`): 3 instances × 7 bands (B0–B5 + TOTAL, fixed baseline ORDER-WAD assignment) × block rows (baseline 6 + hypothetical 3 + variance 11 = 20 per band) = 420 rows. Baseline block `OBSERVED BASELINE`; hypothetical/variance blocks `HYPOTHETICAL_ARITHMETIC_SENSITIVITY`.
4. **Source authority.** `output_name = Contribution variance by discount band`; same three Phase 4B scenario CSVs as AO-03. Quality standing: 21/21 PASS. ORDER basis asserted on every row; band order B0→B5→TOTAL fixed.
5. **Allowed fields.** Per block as verified:
   * Baseline (6): `base_contribution` (CUR), `base_wad` (DEC), `quantity` (CT), `order_count` (CT), `line_count` (CT), `neg_base_orders` (CT).
   * Hypothetical (3): `hypo_contribution` (CUR), `hypo_wad` (DEC), `neg_hypo_orders` (CT).
   * Variance (11): `variance_contribution` (CUR — absolute contribution variance), `variance_net_revenue`, `variance_discount_amount`, `variance_cogs`, `variance_freight` (= 0.0), `variance_cost_to_serve` (= 0.0), `relative_contribution_variance` (PCT), `margin_change_pp` (PP), `low_sample_flag` (Flag), `demand_response_view` (N/A), `fixed_unit_cost_view` (N/A).
   Confirmed uniform records: B5 baseline `15361.8792` → hypo `60763.24880000001` → variance `+45401.369600000005` (+295.5457%, +7.18798 pp); B0 variance `−30530.82247`; bands reconcile to TOTAL variance `+95406.2413300001` (within 0.05). Identity instances zero throughout.
6. **Proposed visuals.**
   * One **matrix**: bands B0–B5 + TOTAL as columns; variance rows (`variance_contribution`, `relative_contribution_variance`, `margin_change_pp`) as three separate row groups — absolute, relative, and pp never share one scale.
   * One **clustered bar chart** of `variance_contribution` by band (uniform instance) for allocation shape, data-labeled in currency.
   * Two small companion **tables**: baseline block (`base_contribution`, `base_wad`, counts) and hypothetical block (`hypo_contribution`, `hypo_wad`, `neg_hypo_orders`), same band columns.
   * One **TOTAL reconciliation strip** (cards or a TOTAL column callout): sum-of-bands vs stored TOTAL note.
7. **Required filters/slicers.** `scenario_id` page-level slicer (single-select, this page only) and/or `block`-section layout fixed by design. No band slicer that hides TOTAL; no basis slicer (this view is ORDER-only by construction).
8. **Required labels.** `scenario_id` + input form; grain `Overall × baseline discount band (ORDER)`; band note "fixed baseline bands — never re-banded"; block/status labels per section; units (CUR vs PCT vs pp) on every visual; B5-largest-movement note only with the descriptive phrasing of record (no causal claim).
9. **Required caveats.** Task standing caveat verbatim (§2.7 short form) plus five assumptions; freight/CTS variances 0.0 by passthrough design; negative counts (`neg_base_orders` 14/3/24/1/3/5/50; uniform hypo TOTAL 46) carried without re-attribution.
10. **Quality indicators.** "AO-04 validation 21/21 PASS"; per-band `low_sample_flag`; band→TOTAL reconciliation check (bands sum to TOTAL within 0.05); freight-zero assertion (0.0 × 21 band rows).
11. **N/A handling.** Exactly 42 empty rows (verified): `demand_response_view` and `fixed_unit_cost_view` in every (instance × band) variance block with the same two reasons as Page 3. Show as a footnoted `N/A` line with reasons, or a collapsed two-row table per selected instance. Never zero-fill.
12. **Fields/views that must not be combined.** No re-banding under any circumstance (no regrouping by hypo values, no custom band DAX); no LINE-basis or order-level rows mixed in (no AO-02 LINE rows, no AO-05 rows); no cross-`scenario_id` aggregation; no merging of `variance_contribution` (CUR) with `relative_contribution_variance` (PCT) or `margin_change_pp` (pp) into one visual scale; no causal attribution language ("driven by", "caused by", "elasticity").
13. **Power BI measures required.** None.
14. **Direct vs presentation calculation.** All values are **direct imported values**. Permitted presentation operations only: filtering to one `scenario_id`, matrix pivoting of stored rows, empty→`N/A` substitution, formatting. The TOTAL reconciliation strip displays the stored TOTAL row beside the band rows with the frozen tolerance note — it must not compute a client-side band sum as a competing total.

---

## 8. Page 5 — Order-Level Observed Context

### Required content (task)
Observed order-level table; WAD; contribution; revenue; COGS; freight; cost-to-serve; negative-contribution flag; return status; ambiguity note; quantity and line-count context. Hypothetical order-level detail explicitly prohibited.

### 8.1. Fourteen build items

1. **Purpose.** Preserve order-level visibility that band aggregates hide (WAD spread, 50 negative orders, one ambiguity case, volume) as context supporting — never replacing — band readings. Observed baseline only.
2. **Approved source view.** `order_reading` only (AO-05).
3. **Exact grain.** `Order` — one row per (`order_id`, `metric_name`): 5,009 orders × 12 metrics = 60,108 rows. All rows `OBSERVED BASELINE`, `AUTHORITATIVE_ORDER`. Bands carried per order (B0 2055 / B1 415 / B2 1634 / B3 278 / B4 274 / B5 353) as assigned labels, never recomputed.
4. **Source authority.** `output_name = Order-level baseline reading`; `source_artifact = discount_order_summary.csv` (order set identical to authoritative order fact). Quality standing: 17/17 PASS.
5. **Allowed fields.** Exactly the 12 frozen per-order metrics (verified): `net_revenue` (CUR), `gross_revenue` (CUR), `modeled_gross_profit` (CUR), `modeled_gross_margin` (PCT), `freight_cost` (CUR), `cost_to_serve` (CUR, = freight, return/support OFF), `contribution_profit` (CUR), `contribution_margin` (PCT, per-order recomputed, never averaged), `wad` (DEC, per-order recomputed, never averaged), `revenue_realization_rate` (PCT), `quantity` (CT), `line_count` (CT); plus dimensions `discount_band`, `return_status` (YES 296 / UNKNOWN 1 / NOT_RETURNED 4712), `neg_flag` (True on exactly 50 orders, 0 mismatches vs contribution sign), `ambiguity_note` (populated on the 12 rows of `US-2014-150119`: `ORDER_CONTAINS_AMBIGUOUS_PAIR_25P05_HELD_AT_ORDER`, freight 26.55; empty elsewhere with NULLs preserved).
   **COGS honesty note:** AO-05 emits **no standalone COGS metric row** (verified; COGS enters only implicitly through gross-profit reconciliation per the AO-05 freeze). The task's "COGS" item is therefore satisfied by `modeled_gross_profit`/`modeled_gross_margin` with that limitation stated — do **not** fabricate or derive a per-order COGS column.
6. **Proposed visuals.**
   * One **table** (paginated, top-N with explicit "showing top N of 5,009" label): Order | Band | Net Revenue | Contribution | Contrib. Margin | WAD | Freight | CTS | Qty | Lines | Neg flag | Return status | Ambiguity note.
   * One **negative-contribution table** pre-filtered `neg_flag = True` (50 orders) with the same columns.
   * One **ambiguity callout card/table** for `US-2014-150119` showing its note text and freight.
   * Optional **histogram/bar of WAD spread** binned at display level from the stored per-order `wad` values (display binning of one frozen column is permitted presentation; no new metric).
7. **Required filters/slicers.** `discount_band`, `return_status`, and `neg_flag` slicers allowed (attribute filters within the single order table only). Default state shows all orders with the row-window label. No scenario/blocks slicers exist at this grain — none may be added.
8. **Required labels.** `OBSERVED BASELINE` banner; grain `Order (5,009 orders)`; authority `AUTHORITATIVE_ORDER`; band labels marked "assigned baseline band (not recomputed)"; column units; prohibition note "no hypothetical values exist at order grain".
9. **Required caveats.** Single-observation warning ("one order is one observation — distributional context only; supports, never replaces, band readings"); assumptions pointer (full text on Page 1); long-form standing caveat (§2.7) in the footer.
10. **Quality indicators.** "AO-05 validation 17/17 PASS"; neg-flag agreement (50 flagged, 0 mismatches); UNKNOWN return order `CA-2015-102015` never defaulted; NULL-preservation note for ambiguity/return fields.
11. **N/A handling.** AO-05 has **zero** empty-`metric_value` rows (verified). Empty `ambiguity_note` on unaffected orders is a preserved NULL dimension, not an `N/A` metric — display as blank with the column's meaning labeled, not as `N/A`. Do not invent hypothetical-order N/A rows.
12. **Fields/views that must not be combined.** **Hypothetical order-level detail is prohibited** — no scenario/hypothetical/variance columns may be constructed at order grain (none exist in any frozen artifact; fabrication forbidden). No AO-01/AO-02/AO-03/AO-04/AO-06 fields in these visuals; no averaging of per-order margins/WAD into a "page average" (order rows are observations — the authoritative totals live on Pages 1–2); no customer/product/region/segment aggregation (customer/segment travel as single attributes per order row for attribution context only, per the AO-05 freeze).
13. **Power BI measures required.** None. (If the WAD-spread histogram needs bin counts, the histogram visual's built-in count of displayed rows is permitted presentation; no stored DAX measure.)
14. **Direct vs presentation calculation.** All cells are **direct imported values** (one stored row per order × metric). Permitted presentation operations only: attribute filtering, sorting, top-N windowing with honest labeling, and display-level binning of the stored `wad` column for the spread visual. No per-order recomputation in DAX (margins/WAD are stored recomputed values).

---

## 9. Page 6 — Data Quality and Eligibility

### Required content (task)
Artifact eligibility; validation status; check counts; row-count evidence; hash-match evidence; `ELIGIBLE_AS_INTERPRETATION_SOURCE`; `ALL_SOURCES_ELIGIBLE`; limitations of arithmetic and lineage-only evidence.

### 9.1. Fourteen build items

1. **Purpose.** Eligibility gate: which artifacts may source interpretation, then the unanimous TOTAL verdict. Arithmetic/lineage fitness only — licenses no behavioral, predictive, or causal reading.
2. **Approved source view.** `quality_summary` only (AO-06).
3. **Exact grain.** `Artifact` (per-file rows) then `TOTAL` (`ALL_ARTIFACTS`) verdict rows: 125 rows = 75 upstream-check mirrors + 47 per-artifact summaries + 3 TOTAL rows. All rows `scenario_status = QUALITY_GATE` (eligibility, not economics).
4. **Source authority.** `output_name = Data-quality summary`; mirrored evidence: `phase3b_quality_report.json` (16 checks), `phase4b_scenario_quality.json` (15), `phase4b_scenario_increase_0.00_quality.json` (22), `phase4b_scenario_decrease_0.00_quality.json` (22) — 75 upstream checks mirrored verbatim in frozen order — plus `Section 10 records` / `this gate` rows for facts and the TOTAL verdict. 17 artifacts verified: 10 data CSVs + 4 quality JSONs + 3 frozen facts (9,994 / 5,009 / 9,994). Quality standing: 9/9 PASS.
5. **Allowed fields.** Exactly the 8 frozen `metric_name` values (verified): `upstream_check` (Label — one row per mirrored check with `check_id`, `status`, `expected`, `actual`), `checks_attested` (CT), `checks_passed` (CT), `row_count` (CT), `sha256_match` (Flag), `eligibility` (Label = `ELIGIBLE_AS_INTERPRETATION_SOURCE` per artifact, 17/17), `overall_eligibility` (Label = `ALL_SOURCES_ELIGIBLE`), `artifacts_verified` (CT). Note the frozen Phase 3B reused check ID (`frozen` twice) is carried verbatim, not "fixed".
6. **Proposed visuals.**
   * One **table/matrix** of per-artifact eligibility: Artifact | Checks (passed/attested) | Row count | SHA-256 match | Eligibility — one row per artifact (17 verdict rows).
   * One **TOTAL verdict card**: `ALL_SOURCES_ELIGIBLE` (unanimous gate).
   * One **check-detail table** (the 75 `upstream_check` mirror rows: Artifact | Check ID | Status | Expected | Actual) with search/sort; `check_id` shown verbatim.
   * One **text box** for the lineage-only limitation (§9.9).
7. **Required filters/slicers.** One `artifact` slicer or search on the check-detail table only (never filters the verdict card — the TOTAL verdict stays visible). No grain-mixing slicers.
8. **Required labels.** `QUALITY_GATE — eligibility, not economics` banner; grain labels `Artifact` / `TOTAL (ALL_ARTIFACTS)`; per-artifact verdict `ELIGIBLE_AS_INTERPRETATION_SOURCE`; TOTAL verdict `ALL_SOURCES_ELIGIBLE`; evidence-file names per row group.
9. **Required caveats.** Lineage-only limitation, verbatim in spirit: "Eligibility means arithmetic/lineage fitness only (existence, parse, counts, PASS standing, row/hash identity). It is not a business endorsement and licenses no behavioral, predictive, or causal reading. Mirrored checks were verified for parseability, counts, standing, and record completeness — not re-executed; the gate cannot detect errors the upstream validations themselves missed."
10. **Quality indicators.** "AO-06 validation 9/9 PASS"; 75/75 upstream checks attested PASS (16+15+22+22); 10/10 CSV row+hash exact; 3/3 fact row+hash exact (Section 10 records); unanimity rule (any single failure would abort — none occurred).
11. **N/A handling.** AO-06 has **zero** empty-`metric_value` rows (verified). Upstream `N/A`-with-reason markers are attested through the mirrored checks, not re-evaluated here. No `N/A` symbol on the verdict visuals.
12. **Fields/views that must not be combined.** No financial rows from AO-01–AO-05 on this page; `QUALITY_GATE` rows must never be joined or cross-filtered with economic grains; `check_id` values must not be deduplicated/"cleaned" (the Phase 3B reuse is frozen evidence).
13. **Power BI measures required.** None.
14. **Direct vs presentation calculation.** All cells are **direct imported values** (mirrored evidence + recorded counts/flags/verdicts). Permitted presentation operations only: filtering the check-detail table by `artifact`, sorting, and verdict-card selection of the `overall_eligibility` row. No pass-rate DAX (counts are stored; recomputing rates is prohibited new logic).

---

## 10. Power BI Implementation Guidance

### 10.1. Visual-type assignment

| Page | Visual | Type |
| ---- | ------ | ---- |
| 1 | KPI cards (revenue, gross, contribution, margins, qty, orders) | **Card** (one metric per card) |
| 1 | Full 20-metric record | **Matrix or Table** (Metric \| Value \| Unit \| Limitation) |
| 1 | Assumptions/limits/quality | **Text box** |
| 2 | ORDER band view | **Matrix** (metrics × B0–B5+TOTAL) |
| 2 | ORDER contribution shape | **Clustered bar chart** (band axis, currency values) |
| 2 | LINE companion | **Table** (separately headed, partial-labeled) |
| 3 | Baseline / hypothetical blocks | **Table** per block |
| 3 | Absolute variances | **Cards** (currency) |
| 3 | Margin-point changes | **Cards/Table** labeled `pp` |
| 3 | Scenario choice | **Slicer** on `scenario_id` (single-select, page-only) or three fixed blocks |
| 4 | Band variances | **Matrix** (three row groups: CUR / PCT / pp) + **clustered bar chart** (`variance_contribution` by band) |
| 4 | Baseline / hypothetical companions | **Tables** |
| 4 | TOTAL reconciliation | **Cards** or TOTAL-column callout |
| 5 | Order context | **Table** (paginated, top-N labeled) + **Table** (neg-flagged 50) + **Card/Table** (ambiguity case) |
| 5 | WAD spread | **Histogram/column chart** of stored per-order `wad` (display binning only) |
| 5 | Attribute narrowing | **Slicers** on `discount_band`, `return_status`, `neg_flag` (page-only) |
| 6 | Eligibility + checks | **Tables/Matrix** + **Card** (TOTAL verdict) + **Text box** (limitation) |

No line charts (no time dimension exists), no pie/donut charts (parts-of-whole would misstate non-additive rows), no KPI-trend visuals, no decomposition/AI visuals, no custom visuals requiring external logic.

### 10.2. Fields imported directly

All of them. Every page displays stored TEXT values from its single view: `metric_name` selects the row, `metric_value` is the displayed value, and `unit`, `limitation`, `definition_ref`, `scenario_status`, `grain`, `basis`/`band`/`block`/`scenario_id`/`order_id`/`discount_band`/`return_status`/`neg_flag`/`ambiguity_note`/`artifact`/`check_id`/`status`/`expected`/`actual`/`source_artifact`/`output_name` supply labels, units, reasons, and traceability. No hidden columns may be dropped at import (reasons and limitations travel with values).

### 10.3. Relationships that must not be created

None — zero relationships. The six tables stay disconnected with cross-filtering disabled between them (and, within scenario pages, blocks are fixed sections rather than cross-filtering dimensions). Rationale (§8 of the foundation doc, binding): TOTAL vs Overall×band vs per-instance blocks vs Order vs Artifact grains are incompatible; ORDER vs LINE bases must not blend; `OBSERVED BASELINE` vs `HYPOTHETICAL_ARITHMETIC_SENSITIVITY` vs `QUALITY_GATE` standings must not cross-filter. Any relationship would let one slicer silently mix grains the freezes forbid. A future relationship needs separate documented approval — none granted here.

### 10.4. Disconnected selector table

Not needed and not authorized as a model object. Scenario choice on Pages 3–4 uses a **visual-level slicer on the page's own `scenario_id` column** (single-select, page-only, no sync across pages, no relationship), or fixed pre-built blocks with no slicer at all. Do not build a standalone scenario dimension table: it would duplicate frozen identifiers and invite cross-page filtering across incompatible grains.

### 10.5. Preserving text-based N/A values

Keep every `metric_value` column as **Text** from import through display. Empty string is the frozen N/A marker: configure those visuals to render empty as the literal `N/A` (via the row's presence in a table/matrix with conditional display text, or a card showing `N/A` when the looked-up value is empty) and always pair it with the row's `definition_ref`/`limitation` reason. Never allow Power BI to coerce empty to null-blank-zero, never enable "show items with no data" tricks that invent rows, and never apply a visual-level filter that removes empty values.

### 10.6. Displaying validation and quality flags

Flags are data, not formatting: `low_sample_flag`, `neg_flag`, `return_status`, `ambiguity_note`, per-check `status`, `sha256_match`, and each row's `limitation` appear as their own columns/cards/badges with frozen text verbatim. Validation standings (18/18, 17/17, 19/19, 21/21, 17/17, 9/9) appear as text badges naming the quality file. The Page 6 verdict card shows `ALL_SOURCES_ELIGIBLE` only when the stored TOTAL row says so (no conditional DAX — select the row).

### 10.7. Preventing accidental mixing of incompatible grains

* One table per visual, enforced at build time (each visual's fields come from a single query).
* Page-level filters, never model relationships; slicers set to affect only their own page's visuals.
* Matrix rows are stored metric rows, never DAX aggregations; the stored `TOTAL` row is displayed, never a client-side total.
* Percentage/pp columns are display-only text from stored rows; "do not summarize" (summarization off) on every value field so Power BI cannot sum or average them.
* Build-time acceptance per page: with any slicer combination, every visible number must still show its grain/basis/block/scenario label, and no visual may show fields from two views.

### 10.8. Keeping the report usable and professional

* Page order 1→6 follows the decision journey (headline → bands → sensitivity → allocation → order context → trust gate); each page opens with a one-line purpose strip and closes with a caveat footer so any exported page stands alone.
* Consistent layout: left = headline cards, center = primary matrix/table, right or bottom = reasons/flags/assumptions text. Identical number formatting per unit class (CUR 2 dp; PCT with `%`; pp with `pp`; DEC 4 dp; CT integers) — formatting only, values untouched.
* Page 5 defaults to a bounded top-N window with an honest count label (60,108 rows cannot be usefully rendered at once); full detail remains available through sort/filter, not through aggregation.
* Performance: Import mode, six lean text tables; no DirectQuery; no bidirectional filters; no calculated columns.

## 11. Gate 10 Compliance Statement (Binding Checklist)

Every page of this specification enforces each Gate 10 requirement:

* [x] Observed baseline and hypothetical values separated (§2.1; Pages 3–4 block sections; Pages 1–2, 5 baseline-only with banners).
* [x] Absolute changes and percentage-point changes separate (§2.2; Pages 3–4 CUR vs pp vs PCT visuals).
* [x] Scenario type, discount input, grain, validation status, and quality flags visible (§§4–9 item 8 + item 10 on every page).
* [x] Unsupported values as `N/A` with reasons (§§5.1.11, 6.1.11, 7.1.11; zero-N/A pages state so explicitly).
* [x] Gross profit, contribution profit, and discount-related revenue forgone distinct (§2.5; Pages 1–4 field lists).
* [x] Methodology assumptions visible (§2.6; every page items 9).
* [x] Constant observed quantity stated (assumption blocks, Pages 1/3/4).
* [x] Modeled COGS stated as analytical estimate (assumption blocks; AO-02/AO-05 honesty notes where no standalone COGS row exists).
* [x] Freight passthrough stated (assumption blocks; freight/CTS 0.0-variance design notes Pages 3–4).
* [x] Return-processing and support costs stated as OFF (assumption blocks on every page).
* [x] No forecast, causal, demand-prediction, or optimized-pricing interpretation (§2.8; prohibitions §§7.1.12, 8.1.12, and §12).
* [x] Deferred scenario views remain unavailable (§12 prohibition list; no deferred page specified).
* [x] Frozen artifacts remain read-only (§2.12; §13).

## 12. Prohibited Content (Not Specified, Not Allowed to Add at Build)

Customer segmentation; product/category/region/segment scenario views; customer-level hypothetical detail; new scenario types or input values; re-banding (any regrouping of bands, including by hypothetical values); forecasting; causal claims ("driven by", "caused by", "uplift", "elasticity"); demand or response estimation; optimization; pricing recommendations; Nue/derived metrics (no ROI, no payback, no price-elasticity, no "adjusted contribution"); DAX measures computing analytics; Power Query merges/joins/appends/groups across views; model relationships; disconnected dimension/bridge tables; line/pie/AI visuals implying trends or shares the freezes do not license; any edit to frozen scripts, CSVs, JSONs, freeze docs, or the `.db`.

## 13. Change Boundary and Artifact Protection

* No AO-01–AO-06 script, CSV, quality JSON, freeze document, or Phase 5/6/7A document was modified in this task.
* The SQLite database was opened read-only for metric/N/A verification only; it was not rebuilt, patched, or hand-edited.
* No `.pbix`, visual, measure, or calculation was created.
* This specification (`docs/PHASE_7B_POWER_BI_REPORT_BUILD_SPEC.md`) is the only file added in this task. No commit or push was performed.

## 14. Build Acceptance Checklist (For the Later .pbix Step)

1. Six pages in §§4–9 order with the exact names used here.
2. Each visual traces to one view; row counts per table match §3.
3. Spot values and N/A volumes re-confirmed after import.
4. Every page shows its §(item 8) labels, §(item 9) caveats, and §(item 10) quality indicators simultaneously (no tooltip-only compliance).
5. Summarization off on all value fields; no relationships in the model; slicers page-local.
6. Export/print test: each page standalone-compliant (purpose strip + caveat footer present on every page).
