# Phase 4C AO-03 Freeze — Scenario Comparison

`FROZEN — APPROVED`

AO-03 is frozen. The freeze applies to the approved scenario-comparison artifact (`data/processed/phase4c_scenario_comparison_total.csv`) and its validation evidence (`data/processed/phase4c_scenario_comparison_total_quality.json`). This document records the approved state and does not introduce new analytical logic.

## 1. Objective

AO-03 places baseline, hypothetical, and variance results side by side for the three approved scenario instances using identical overall scope and authoritative order-level economics. Each instance is shown as three separated blocks — `baseline`, `hypothetical`, `variance` — so the headline arithmetic sensitivity of every frozen scenario can be read against the same baseline without mixing observed and hypothetical values.

## 2. Frozen Scope

* Grain: overall `TOTAL` (order economics rolled up; authoritative).
* Economic authority: order-level economics.
* Scenario comparison only (baseline beside hypothetical with variances).
* No customer, product, region, segment, or time-period slicing.
* No band-level detail (band variance is AO-04, not built here).
* No causal interpretation.
* No optimization or recommendation logic.
* No new scenario generation.
* No dashboard or presentation layer.

## 3. Frozen Scenario Instances

| Scenario instance           | Purpose                             |
| --------------------------- | ----------------------------------- |
| `uniform_replace_0.10`      | Uniform replacement scenario        |
| `discount_increase_pp_0.00` | Discount-increase identity scenario |
| `discount_decrease_pp_0.00` | Discount-decrease identity scenario |

The two `0.00` scenarios are identity controls and should produce zero variance. Their zero variances confirm pipeline integrity; they measure no economic sensitivity.

## 4. Frozen Output Structure

* Output file: `data/processed/phase4c_scenario_comparison_total.csv`
* Output grain: 3 scenario instances × 3 blocks × 35 rows = 105 rows.
* Number of columns: 11.
* Blocks:
  * `baseline` (13 rows per instance; `OBSERVED BASELINE` standing)
  * `hypothetical` (9 rows per instance; `HYPOTHETICAL_ARITHMETIC_SENSITIVITY` standing)
  * `variance` (13 rows per instance, including computed relative variance, both percentage-point changes, flag, and both N/A markers)
* Exact column names (read from the actual CSV header):
  `output_name,scenario_status,grain,scenario_id,block,source_artifact,metric_name,metric_value,unit,definition_ref,limitation`
* Fixed ordering: instances uniform → increase → decrease; blocks baseline → hypothetical → variance; fixed metric order within each block. No duplicate (scenario, block, metric) combinations; TOTAL grain only.

## 5. Frozen Analytical Rules

Exact logic implemented in `src/data/build_phase4c_scenario_comparison.py` (inspected, not restated from memory):

* Baseline values: stored TOTAL baseline columns from each scenario CSV (`base_net`, `base_disc`, `base_cogs`, `base_gross_profit`, `base_gross_margin`, `base_freight`, `base_cts`, `base_contrib`, `base_contrib_margin`, `base_wad`) plus stored counts (`quantity`, `order_count`, `line_count`); asserted identical across all three instances and equal to the frozen baseline.
* Hypothetical values: stored TOTAL hypothetical columns (`hypo_net`, `hypo_disc`, `hypo_cogs`, `hypo_gross_profit`, `hypo_gross_margin`, `hypo_cts`, `hypo_contrib`, `hypo_contrib_margin`, `hypo_wad`) under the stated assumptions recorded on each row (constant observed quantity, frozen modeled-COGS percentage, observed freight passthrough, return/support OFF).
* Variance values: stored variance columns asserted equal to hypothetical minus baseline with gaps ≤ 1e-9 (`variance_net_revenue`, `variance_discount_amount`, `variance_cogs`, `variance_gross_profit`, `variance_contribution_profit`).
* Revenue variance: `hypo_net − base_net` (uniform: 280,340.6757000005).
* Cost variance: `hypo_cogs − base_cogs` for modeled COGS; freight and cost-to-serve variances exactly `0.0` by passthrough design with `hypo_cts` equal to base freight.
* Contribution variance: `hypo_contrib − base_contrib` (uniform: 95,406.2413300001).
* Contribution-margin change: `hypo_contrib_margin − base_contrib_margin` in percentage points (uniform: 1.0258519545365985); gross-margin change analogously (uniform: −0.1018009440449532); both recomputed with gaps ≤ 1e-9. Relative contribution variance is computed as variance/baseline × 100 (uniform: 16.882566114731784) and is NULL/blank where the baseline is zero.
* Identity-scenario expectations: all currency variances, both margin changes, and the computed relative variance are exactly `0.0` for both `0.00` instances.

## 6. Validation Evidence

* Quality artifact: `data/processed/phase4c_scenario_comparison_total_quality.json`
* Validation result: `19/19 checks passed`, all check IDs unique, all statuses PASS.
* Actual check names: `inputs-exist`, `quality-status`, `quality-chain`, `fact-chain`, `identifiers`, `input-forms`, `shapes`, `band-schema`, `quarantine`, `assumption-labels`, `na-markers`, `counts`, `baseline-identical`, `baseline-frozen`, `variance-reconcile`, `freight-zero`, `margin-pp`, `headline`, `grain`.
* Output row count: `105`; output column count: `11`.
* Three scenario instances were validated (identifiers, input forms and stated values, scope, basis, standing, assumption labels, N/A markers, counts).
* Baseline, hypothetical, and variance blocks were validated (baseline identity across instances and equality to frozen values; variance and margin-change reconciliation both ways; headline figures).
* Reconciliation and arithmetic checks passed (currency gaps ≤ 1e-9; totals within 0.05; counts exact).
* Deterministic output checks passed: fixed instance/block/metric ordering, `repr()` numeric formatting, no timestamps, no randomness, no environment-dependent values; the recorded output hash matches the actual CSV byte-for-byte.

## 7. Key Confirmed Results

Only results supported by the AO-03 output and audit report:

* Uniform replacement hypothetical contribution: `660523.1831600001` (approximately `660,523.183`).
* Uniform replacement contribution variance: `95406.2413300001` (approximately `+95,406.241`).
* Uniform replacement contribution-margin change: `1.0258519545365985` (approximately `+1.0259 percentage points`).
* Uniform replacement relative contribution variance: `16.882566114731784` percent.
* Both identity scenarios have zero variance (all currency variances, both margin changes, and relative variance exactly `0.0`).

## 8. Input Artifact Protection

Six upstream AO-03 input artifacts:

* `data/processed/phase4b_scenario_uniform_0.10.csv` (7 rows × 52 columns)
* `data/processed/phase4b_scenario_quality.json` (15/15 checks PASS)
* `data/processed/phase4b_scenario_increase_0.00.csv` (7 rows × 52 columns)
* `data/processed/phase4b_scenario_increase_0.00_quality.json` (22/22 checks PASS)
* `data/processed/phase4b_scenario_decrease_0.00.csv` (7 rows × 52 columns)
* `data/processed/phase4b_scenario_decrease_0.00_quality.json` (22/22 checks PASS)

Precisely:

* The three scenario CSV files were hash-verified against their quality JSON output records (byte-identical SHA-256 match before loading).
* The three quality JSON files were independently parsed; their validation evidence, identifiers, fact hashes, and metadata were verified (exact check counts with unique IDs, all PASS; scenario identifiers, input forms, scope, and assumption labels confirmed; recorded fact hashes match the frozen records).
* No claim is made that all six files are byte-identical to a single freeze-hash list: the three CSV hashes are verified against the hashes recorded inside their own quality JSON evidence, and the three JSON files are verified by parsing their contents, counts, identifiers, and recorded fact hashes. No freeze-hash list covering the JSON files themselves exists in the repository, and none is invented here.

## 9. Reproducibility and Failure Behavior

Only what the implementation and audit support:

* The AO-03 script is deterministic (fixed ordering and formatting; consecutive runs byte-identical).
* The output and quality artifact can be regenerated from the frozen inputs with the same command.
* Validation failures are surfaced as loud `VALIDATION FAILED [check-id]` exits rather than silently accepted; outputs are written only after every check passes, so failed runs leave no partial or misleading output.
* Existing upstream validation gates are respected (frozen quality evidence must be all-PASS with exact check counts before any value is used; chain-of-custody hashes must match before loading).
* No stronger guarantees are claimed: rerun and failure evidence is as tested and audited, and any future input change fails loudly instead of producing adjusted output.

## 10. Change Boundary

This freeze does not include:

* New scenario types.
* New business dimensions.
* Dashboard development.
* Visualizations.
* Recommendations.
* Optimization.
* Causal claims.
* Changes to AO-01 or AO-02.
* Changes to the upstream scenario generators.
* Changes to frozen source artifacts.

## 11. Freeze Decision

* AO-03 is approved for freeze.
* The implementation (`src/data/build_phase4c_scenario_comparison.py`) and validation evidence (`data/processed/phase4c_scenario_comparison_total_quality.json`) passed the formal audit (`APPROVED FOR AO-03 FREEZE`, no blocking issues).
* The frozen artifact (`data/processed/phase4c_scenario_comparison_total.csv`, 105 rows × 11 columns) is now the reference point for any future work.
* Any future modification must be treated as a new, explicitly scoped change.
