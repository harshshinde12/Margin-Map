# Phase 4C AO-04 Freeze — Contribution Variance by Baseline Discount Band

`FROZEN — APPROVED`

AO-04 is frozen. The implementation passed its formal validation (21/21 checks). This document records the approved reference state — the output artifact and its validation evidence — and introduces no new analytical logic.

## 1. Objective

AO-04 distributes the headline scenario sensitivity across the existing baseline discount configurations. Baseline discount bands are used only as existing baseline configurations: the bands are not recalculated or re-banded under the scenarios. The analysis uses the ORDER basis. Baseline and hypothetical values are kept separate (distinct blocks and standing labels). Incompatible grains are not mixed (no LINE-basis scenario detail, no disaggregation into order-level hypotheticals). The output is descriptive sensitivity allocation, not causal attribution.

## 2. Frozen Scope

* Grain: baseline discount band (Overall × discount band).
* Economic basis: ORDER (authoritative; baseline order-WAD bands).
* Bands: B0, B1, B2, B3, B4, B5, TOTAL (existing baseline order-WAD assignment).
* Overall scenario instances:
  * `uniform_replace_0.10`
  * `discount_increase_pp_0.00`
  * `discount_decrease_pp_0.00`
* Baseline bands are never re-banded under hypothetical values.
* No customer, product, region, segment, or time-period analysis.
* No optimization, recommendation, or causal inference.
* No new scenario generation.

## 3. Scenario Instances

| Scenario instance           | Purpose                                                     |
| --------------------------- | ----------------------------------------------------------- |
| `uniform_replace_0.10`      | Uniform replacement scenario (`replacement_rate` 0.10)      |
| `discount_increase_pp_0.00` | Discount-increase identity scenario (`increase_pp` 0.00)    |
| `discount_decrease_pp_0.00` | Discount-decrease identity scenario (`decrease_pp` 0.00)    |

The two `0.00` scenarios are identity controls and are expected to have zero variance throughout. Their zero variances confirm pipeline integrity; they measure no economic sensitivity.

## 4. Frozen Output

* Output file: `data/processed/phase4c_contribution_variance_by_band.csv`
* The CSV is generated and ignored under the repository's `*.csv` policy (it does not appear in version control).
* Output shape: 420 rows × 12 columns.
* Structure: 3 scenario instances × 7 baseline bands × 20 metrics (6 baseline-block + 3 hypothetical-block + 11 variance-block rows per band).
* There are 42 explicit `N/A` rows with documented reasons (empty value, never zero-filled).
* There are 420/420 unique `(scenario instance, band, block, metric)` combinations; no duplicates, no gaps.
* Exact column names (read from the actual CSV header):
  `output_name,scenario_status,grain,scenario_id,band,block,source_artifact,metric_name,metric_value,unit,definition_ref,limitation`
* Fixed ordering: instances uniform → increase → decrease; bands B0 → B5 → TOTAL; blocks baseline → hypothetical → variance; fixed metric order. Statuses: `OBSERVED BASELINE` (baseline block) and `HYPOTHETICAL_ARITHMETIC_SENSITIVITY` (hypothetical/variance blocks).

## 5. Analytical Rules

Exact rules implemented in `src/data/build_phase4c_band_variance.py` (inspected):

* Baseline values are obtained from the stored baseline columns of each scenario CSV TOTAL and band rows (`base_contrib`, `base_wad`, `quantity`, `order_count`, `line_count`, `neg_base_orders`); asserted identical across instances where applicable and equal to frozen values.
* Hypothetical values are obtained from the stored hypothetical columns (`hypo_contrib`, `hypo_wad`, `neg_hypo_orders`) under the stated assumptions recorded on every row (constant observed quantity, frozen modeled-COGS percentage, observed freight passthrough, return/support OFF).
* Variance is calculated as hypothetical minus baseline and asserted equal to the stored variance columns with gaps ≤ 1e-9 (`variance_net_revenue`, `variance_discount_amount`, `variance_cogs`, `variance_contribution_profit`).
* Relative variance is handled as variance/baseline × 100, computed by the script, NULL/blank where the baseline is zero (no zero-baseline band occurs; the rule is implemented regardless).
* Percentage-point margin change is calculated as hypothetical margin minus baseline margin (`margin_change_pp`), asserted equal to the stored value with gaps ≤ 1e-9.
* Baseline bands remain fixed: the script asserts `basis == ORDER` on every row, asserts band order B0 → B5 → TOTAL, and performs no regrouping or re-banding.
* `N/A` values are represented as empty `metric_value` with an explicit reason in `definition_ref`/`limitation` (never zero-filled): `neg_contribution_orders` is N/A on LINE-free scope (not applicable here — this output is ORDER-only); within this output, the counterpart discipline from AO-02 is preserved by construction since only ORDER-basis scenario detail exists.
* Negative baseline contribution values are handled by preserving stored counts: baseline negative-order counts (`neg_base_orders`) and hypothetical negative-order counts (`neg_hypo_orders`) are carried per band as non-negative integers; no imputation or re-attribution is performed.
* Freight is treated as observed passthrough: freight and cost-to-serve variances are asserted exactly `0.0` on all 21 band rows.
* Band-level results reconcile to the overall total: per-instance band sums equal TOTAL for counts and currency variances within 0.05.

## 6. Validation Evidence

* Quality artifact: `data/processed/phase4c_contribution_variance_by_band_quality.json`
* Validation result: `21/21 checks passed`, all check IDs unique, all statuses PASS.
* Actual validation check names, grouped logically:
  * Inputs and evidence: `inputs-exist`, `quality-status` (15/15 + 22/22 + 22/22, unique IDs, all PASS), `quality-chain` (CSV bytes match recorded hashes), `fact-chain` (recorded fact hashes match freeze records).
  * Identity and schema: `identifiers`, `input-forms`, `shapes` (7 rows × 52 columns × 3 files), `band-schema`, `quarantine` (no quarantined-Profit column).
  * Grain, labels, flags: `grain` (ORDER basis, baseline bands, band order), `assumption-labels`, `na-markers`, `flags` (all FALSE).
  * Counts and negatives: `counts-per-band` (frozen order counts and quantities per band × 3), `negatives` (baseline distribution plus valid hypo counts).
  * Reconciliation: `band-totals-reconcile` (bands sum to TOTAL × 3), `baseline-identical` (TOTAL baselines identical), `baseline-frozen` (TOTAL equals 565,116.9418), `variance-reconcile` (4 pairs × 7 bands × 3 instances, gaps ≤ 1e-9), `freight-zero` (0.0 × 21 band rows), `margin-pp` (7 bands × 3 instances, gaps ≤ 1e-9).
* Determinism and failure behavior are recorded in the quality artifact (fixed ordering/formatting, no timestamps/randomness; loud `VALIDATION FAILED` gates with no partial output) as implemented; rerun and failure-test evidence is as reported in the implementation report and audit.

## 7. Confirmed Results

Only values supported by the actual output and quality artifact (exact output precision; rounded forms in parentheses):

* Uniform scenario B5:
  * Baseline contribution `15361.8792` (approximately `15,361.88`).
  * Hypothetical contribution `60763.24880000001` (approximately `60,763.25`).
  * Variance `45401.369600000005` (approximately `+45,401.37`).
  * Relative variance `295.5456751671372` percent (approximately `+295.55%`).
  * Margin change `7.18798060226743` percentage points (approximately `+7.188 percentage points`).
* B5 is the largest positive band movement under the uniform scenario.
* Uniform scenario B0 contribution variance is `-30,530.82` (approximately `−30,530.82`; stored `-30530.82247`).
* Band variances reconcile to the overall TOTAL variance of `95406.2413300001` (approximately `+95,406.24`).
* Both identity scenarios have zero variance throughout (all currency variances, both margin changes, and relative variance exactly `0.0` on every band row).
* The negative-baseline contribution distribution is preserved, with the reported distribution: `14/3/24/1/3/5/50`. Interpretation as documented: these are the stored baseline negative-order counts per ORDER band (B0 14, B1 24 carrying the largest share, B5 5, TOTAL 50); hypothetical negative-order counts are carried alongside (uniform TOTAL 46) without re-attribution.

## 8. Input Artifact Protection

Upstream artifacts used by AO-04 (six files: three scenario CSVs plus three scenario quality JSONs) with the protection checks performed:

* Existence, frozen content hashes (CSV bytes equal the hashes recorded in their quality JSON evidence), and shapes asserted before loading.
* Upstream quality evidence parsed and verified (exact check counts, unique IDs, all PASS, identifiers, recorded fact hashes matching freeze records).
* Baseline values protected against unintended changes (identity across instances plus equality to frozen baseline values).
* Existing baseline band definitions preserved (ORDER basis asserted on every row; B0 → B5 → TOTAL order asserted; no regrouping).
* Frozen upstream artifacts were not modified (hashes identical before and after; inputs opened read-only; outputs use new filenames incapable of overwriting frozen paths).
* Only what the validation evidence supports is claimed: CSV hashes are verified against the hashes recorded inside their own quality JSON evidence, and JSON evidence is verified by parsing counts, identifiers, and recorded fact hashes. No hash list covering the JSON files themselves is invented.

## 9. Determinism and Failure Behavior

Actual evidence:

* Consecutive runs producing byte-identical output and quality artifacts (CSV `43bc0b6c98c19485d283a7f5076bc5faa4f2c0a082755c2749df26dd415c6d84`; quality JSON `a3f05b08d4a0837faaee5db7620f64acf28dae534a89c8a291bb8189c2cce955`), as reported in the implementation report.
* Missing-input failure behavior: nonexistent inputs fail `VALIDATION FAILED [inputs-exist]` with exit 1 and nothing written, as reported.
* Tampered-input or broken-quality-chain failure behavior: modified content fails `VALIDATION FAILED [quality-chain]` with exit 1 and no output directory created, as reported (any content change breaks the chain before use).
* Output suppression when validation fails: outputs are written only after every check passes; failed runs leave no partial or misleading output.
* Gate-order behavior/limitation reported by the implementation audit: a wrong-schema input via CLI override fails at the frozen-hash gate before reaching the deeper schema gate; the schema gate still executes and passes on frozen inputs. No stronger claims are made than this evidence supports.

## 10. Change Boundary

AO-04 does not include:

* New discount bands.
* Re-banding hypothetical orders.
* New scenario types.
* New business dimensions.
* Dashboard development.
* Visualizations.
* Recommendations.
* Optimization.
* Causal claims.
* Changes to AO-01.
* Changes to AO-02.
* Changes to AO-03.
* Changes to upstream scenario generators.
* Changes to frozen source artifacts.

## 11. Freeze Decision

* AO-04 is approved for freeze.
* The implementation passed 21/21 validation checks.
* The output (`data/processed/phase4c_contribution_variance_by_band.csv`, 420 rows × 12 columns) and quality artifact (`data/processed/phase4c_contribution_variance_by_band_quality.json`) are the approved reference state.
* The generated CSV remains ignored according to repository policy (`*.csv`).
* Any future change must be separately scoped, validated, and documented.
