# Phase 4C AO-05 Freeze — Order-Level Reading

`FROZEN — APPROVED`

AO-05 is frozen, based on the completed validation (`17/17 checks passed`). This document records the approved reference state and introduces no new analytical logic.

## 1. Objective

AO-05 preserves order-level visibility that band aggregates can hide, including:

* WAD distribution (per-order revenue-weighted discount context).
* Negative-contribution orders (50 flagged orders preserved with identifiers).
* Ambiguity-affected orders (the single held-at-order freight case).
* Quantity context (per-order units).
* Line-count context (per-order line composition).

This is **observed baseline only**. It supports but does not replace band-level analysis, and it does not fabricate hypothetical order-level detail — no scenario values exist at order grain in any frozen artifact, and none are constructed here.

## 2. Frozen Scope

* Grain: order (`order_id`, one row per order; authoritative).
* Baseline-only observation (`OBSERVED BASELINE` on all 60,108 rows).
* 5,009 unique orders (order set identical to the authoritative order fact).
* ORDER economic authority (all rows `AUTHORITATIVE_ORDER`).
* Existing baseline discount-band labels (B0–B5 carried per order; bands assigned, never recomputed).
* No hypothetical order-level scenario detail.
* No customer, product, region, segment, or time-period aggregation (customer/segment travel as single non-null attributes per order row for attribution context only).
* No causal inference, optimization, recommendations, or dashboard logic.

## 3. Frozen Output

* Output file: `data/processed/phase4c_order_reading.csv`
* The CSV is generated and ignored by the repository's `*.csv` policy (present on disk, absent from version control).
* Output shape: 60,108 rows × 14 columns.
* Structure: 5,009 orders × 12 metrics.
* All rows are `OBSERVED BASELINE` and `Order` grain.
* Output is ordered by unique `order_id` (file order of the frozen source; `order_id` uniqueness asserted).
* Exact column names (read from the actual CSV header):
  `output_name,scenario_status,grain,order_id,discount_band,return_status,neg_flag,ambiguity_note,source_artifact,metric_name,metric_value,unit,definition_ref,limitation`
* Dimension columns per row: `discount_band`, `return_status` (filter context), `neg_flag`, `ambiguity_note` (populated on the 12 metric rows of the single affected order, empty elsewhere with NULLs preserved, never defaulted).

## 4. Analytical Content

Actual fields and logic implemented in `src/data/build_phase4c_order_reading.py` (inspected):

* Revenue: stored per-order `net_revenue` carried as metric `net_revenue` (CUR); order rollup asserted equal to the order-fact `order_revenue` sum with gaps ≤ 1e-6.
* COGS: stored per-order `modeled_cogs` used for rollup validation against the order fact (≤ 1e-6); carried implicitly through gross-profit reconciliation, not emitted as a standalone metric row (the design's 12 measures exclude it).
* Freight: stored per-order `freight_cost` carried as metric `freight_cost` (CUR); order rollup asserted equal to the order-fact freight sum (≤ 1e-6).
* CTS: stored per-order `cost_to_serve` carried as metric `cost_to_serve` (CUR); equals freight under return/support OFF (zero means excluded).
* Contribution: stored per-order `contribution_profit` carried as metric `contribution_profit` (CUR); order rollup asserted equal to the order-fact sum (≤ 1e-6); authoritative order grain.
* Contribution margin: stored per-order `contribution_margin_pct` carried as metric `contribution_margin` (PCT) after per-order recomputation (`contribution ÷ net × 100`, gaps ≤ 1e-6 on all 5,009 orders; never averaged).
* WAD: stored per-order `wad` carried as metric `wad` (DEC) after per-order recomputation (`discount ÷ gross`, gaps ≤ 1e-6); gross-weighted by construction, never an arithmetic mean.
* Quantity: stored per-order `quantity` carried as metric `quantity` (CT); volume context only.
* Line count: stored per-order `line_count` carried as metric `line_count` (CT); sample-size companion.
* Negative-contribution flag: stored `negative_contribution_flag` carried as the `neg_flag` dimension; asserted TRUE on exactly 50 orders and exactly where `contribution_profit < 0` (0 mismatches across all 5,009 orders).
* Return status: stored `order_return_status` carried as the `return_status` dimension (filter context only); cohorts YES 296 / UNKNOWN 1 / NOT_RETURNED 4,712; the single UNKNOWN order is `CA-2015-102015`, never defaulted.
* Ambiguity note: stored `ambiguity_note` carried as the `ambiguity_note` dimension; populated only for `US-2014-150119` (`ORDER_CONTAINS_AMBIGUOUS_PAIR_25P05_HELD_AT_ORDER`, full-order freight 26.55); NULL preserved on all other rows.
* Discount band: stored `discount_band` carried as the `discount_band` dimension; exactly one non-null frozen band per order with the frozen distribution (B0 2055 / B1 415 / B2 1634 / B3 278 / B4 274 / B5 353).

## 5. Important Baseline Findings

Only results supported by the output and quality JSON:

* 5,009 unique orders (order set identical to the authoritative order fact).
* Discount-band coverage:
  * B0: 2,055
  * B1: 415
  * B2: 1,634
  * B3: 278
  * B4: 274
  * B5: 353
* Exactly 50 negative-contribution orders.
* Negative flag agrees with contribution sign for all orders (50 flagged; 0 mismatches).
* One ambiguity-affected order: `US-2014-150119`.
* The ambiguity note is carried across that order's 12 metric rows.
* Return cohorts:
  * `YES`: 296
  * `UNKNOWN`: 1
  * `NOT_RETURNED`: 4,712

## 6. Validation Evidence

* Quality artifact: `data/processed/phase4c_order_reading_quality.json`
* Validation result: `17/17 checks passed`, all check IDs unique, all statuses PASS.
* Actual check names: `inputs-exist` (input existence), `frozen-inputs` (frozen-input protection), `upstream-standing` (Phase 3B 16 checks all PASS), `quarantine` (no quarantined-Profit column), `inputs` (input order coverage: 5,009 unique orders, sets match fact), `order-schema` (22 required columns), `band-coverage` (exactly one frozen band per order), `authority` (all `AUTHORITATIVE_ORDER`), `flags` (all FALSE convention), `rollups` (revenue/COGS/freight/CTS/contribution gaps ≤ 1e-6), `margins-recomputed` (0 mismatches × 5,009), `wad-recomputed` (WAD/realization, 0 mismatches × 5,009), `negatives` (negative-contribution identification: 50 flags, 0 mismatches), `ambiguity` (ambiguity handling: sole noted order, note text, freight 26.55), `attribution` (attribution fields: non-null customer/segment per row), `return-cohorts` (296/1/4712 with UNKNOWN never defaulted), `grain` (order grain only; no hypothetical/scenario columns).
* Recorded upstream note: the frozen Phase 3B quality record carries 16 checks with one reused ID; upstream standing requires all 16 PASS (met), while uniqueness is asserted for AO-05's own 17 checks.
* Output metadata: 60,108 rows with the recorded SHA-256 matching the actual CSV byte-for-byte.

## 7. Determinism and Failure Behavior

Actual evidence (as implemented and tested):

* Byte-identical consecutive runs (CSV `0966d89e616f66bad5e59a50b0b87d0637e13e23761117d419d31c1c625d0437`; quality JSON `4567ebc8cecc0006a2bc53d52015c43ce904abec4571a2e8ade666df326d0fc4`).
* Missing-input failure: nonexistent inputs fail `VALIDATION FAILED [inputs-exist]` with exit 1 and nothing written.
* Frozen-input hash mismatch failure: wrong files fail `VALIDATION FAILED [frozen-inputs]` with exit 1 and nothing written.
* No output written when validation fails: outputs are written only after every check passes; failed runs leave no partial or misleading output.
* Validation gates run before output writes (existence → hashes → upstream standing → load → schema → coverage → reconciliation → emission).

## 8. Input and Artifact Protection

* Earlier AO-01–AO-04 artifacts were not modified (implementation, outputs, and freeze records all unchanged).
* Frozen source and fact inputs remained unchanged (hashes identical before and after: `discount_order_summary.csv 17389c40…`, `order_margin_map_phase2.csv ae6c349c…`, `fact_margin_map_phase2.csv 4c471fee…`).
* No hypothetical order-level data was introduced (grain gate rejects any `hypo_`/`hypothetical`/`scenario_`/`variance_` columns).
* The generated CSV remains ignored (`*.csv` policy).
* The quality JSON is the tracked validation evidence artifact.

## 9. Change Boundary

AO-05 explicitly excludes:

* Scenario-level order simulation.
* Hypothetical order-level outputs.
* New discount bands.
* Re-banding.
* Dashboard or visualization work.
* Recommendations.
* Optimization.
* Causal claims.
* Changes to AO-01 through AO-04.
* AO-06 implementation.
* Changes to upstream scenario generators, source data, or frozen artifacts.

## 10. Freeze Decision

* AO-05 is approved for freeze.
* The implementation passed 17/17 checks.
* The CSV (`data/processed/phase4c_order_reading.csv`, 60,108 rows × 14 columns) and quality JSON (`data/processed/phase4c_order_reading_quality.json`) represent the approved AO-05 reference state.
* Future modifications require separate scope, validation, and documentation.
