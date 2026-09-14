# Phase 4C AO-01 Freeze — Baseline TOTAL Performance Summary

`FROZEN — APPROVED`

## 1. Freeze Status

* AO: AO-01 — Baseline TOTAL Performance Summary.
* Status: `FROZEN — APPROVED`
* Objective: state the single authoritative baseline against which every band reading and every scenario variance is referenced, per the approved Phase 4C analytical interpretation design.
* Baseline/scenario status: `OBSERVED BASELINE`
* Grain: Overall TOTAL (order grain rolled up; authoritative).
* Audit decision: `APPROVED FOR AO-02` (formal audit completed with no blocking issues; the decision label authorizes the next slice and presupposes AO-01's own standing).

## 2. Objective

AO-01's exact purpose is the baseline total summary: to state the single authoritative baseline — net revenue, modeled COGS, gross profit/margin, freight, cost-to-serve, contribution profit/margin, discount intensity, volume, and loss/cohort context at Overall TOTAL — against which every band reading and every scenario variance is referenced. It establishes the overall baseline reference for later Phase 4C analysis (AO-02 band distribution, AO-03 scenario comparison, AO-04 band variance) without itself performing any band, scenario, or order-level analysis.

## 3. Approved Scope

AO-01 provides:

* The single authoritative baseline TOTAL (net revenue, modeled COGS, gross profit/margin, freight, cost-to-serve, contribution profit/margin, WAD, realization rate, quantity, order/line counts, negative-order count, return-status cohort context, NULL-freight indicator).
* Order-grain authoritative economics rolled up to one TOTAL row set (20 metric rows).
* Metric and limitation metadata on every row (unit, definition reference, limitation, source artifact).

Explicitly not included:

* AO-02 through AO-06.
* Discount-band analysis.
* Scenario comparisons.
* Discount increase/decrease modeling.
* Order-detail outputs.
* Dashboards/UI/charts.
* Forecasting.
* Optimization.
* Causal analysis.
* Recommendations.
* Return-policy modeling.
* Support-cost modeling.
* Quarantined Profit data (excluded by construction; never loaded).

## 4. Frozen Implementation

* Implementation path: `src/data/build_phase4c_baseline_summary.py` (standalone; reads frozen inputs read-only; writes new files only after all validations pass).
* Output paths:
  * `data/processed/phase4c_baseline_total.csv` (20 metric rows × 9 columns).
  * `data/processed/phase4c_baseline_total_quality.json` (18/18 checks PASS).
* The CSV is ignored under the existing `*.csv` policy and must not be tracked, while the quality JSON is committable validation evidence.

## 5. Source Artifacts

| Artifact | Full SHA-256 | Rows | Role |
| -------- | ------------ | ---: | ---- |
| `order_margin_map_phase2.csv` | `ae6c349c9995747f2fef91cf1db6b940a73d99d6b2fede5ff3dff918f429d267` | 5,009 | Primary source (authoritative contribution, revenue, COGS, freight, return cohorts) |
| `fact_margin_map_phase2.csv` | `4c471feeda642e5ecbd2263782b4fc0f1655962f6c6488bdfe47886df2f01cb1` | 9,994 | Gross/WAD/discount recomputation, quantity, NULL-freight evidence, COGS identity |
| `discount_band_summary.csv` | `ad8f7e571c76f295bde3cb119bca4b7ff56c7b3e1734869ebf60f8d7e3c236eb` | 14 | Independent ORDER TOTAL cross-check only |
| `fact_sales_cogs.csv` | `4d8de717486b323ffb656d13c94fd6bd94f8e61d1a93ea339a602ab5303b9988` | 9,994 | Frozen reference (never read by AO-01; confirmed unchanged) |

State that:

* Frozen hashes were independently verified character-for-character against the actual files and all prior freeze records.
* Frozen inputs remain unchanged (hashes identical before and after implementation and audit).
* Inputs are opened read-only; the implementation never writes to a frozen path.
* AO-01 outputs use new filenames and cannot overwrite frozen inputs.

## 6. Output Structure

* 20 output rows (20 metrics at Overall TOTAL grain).
* 9 columns: `output_name,scenario_status,grain,source_artifact,metric_name,metric_value,unit,definition_ref,limitation`.
* Fixed metric ordering; uniform status `OBSERVED BASELINE`; uniform grain `TOTAL`.
* Every row carries its source artifact, unit, definition reference, and limitation; return-status cohorts are counts with filter-only limitations; the NULL-freight indicator carries the ambiguity-control limitation.
* No duplicate or missing rows; no grain mixing (authoritative order economics only; line-fact values enter solely as recomputation and cross-check inputs, never as competing totals).

## 7. Analytical Rules

Actual rules implemented in `src/data/build_phase4c_baseline_summary.py` (inspected):

* Metric definitions follow the frozen Phase 1A financial model verbatim (no redefinition): net revenue equals source Sales (authoritative; discount already applied); gross revenue is the derived reference `sales / (1 − discount)`; discount amount is gross minus net (revenue forgone, not profit loss); modeled COGS is `sales × modeled_cogs_pct / 100` per line under the frozen Phase 1C-3 revenue-based rule; gross profit is net minus COGS; cost-to-serve is freight plus zero plus zero (return/support OFF); contribution profit is net minus COGS minus cost-to-serve, equivalently gross profit minus serve costs (both forms reconciled at the authoritative order grain).
* Formulas: WAD is `SUM(discount_amount) / SUM(gross_revenue)` with the dual form `1 − SUM(net)/SUM(gross)` reconciled (observed dual gap 2.78e-17); realization is `SUM(net)/SUM(gross) × 100`; contribution margin and gross margin are SUM/SUM on net revenue with NULL/blank guards where net is zero (none observed); margin changes are not applicable at single-TOTAL baseline (no comparison dimension).
* Revenue, COGS, freight, CTS, contribution: authoritative sums from the order fact, each reconciled within 0.05 of the frozen records, with line-fact identity (`modeled_cogs == sales × pct/100`, max gap 4.55e-13) and ORDER TOTAL cross-checks.
* Margins: SUM/SUM on net revenue (denominator net, never gross), recomputed within 1e-6.
* Quantity (37,873), orders (5,009 DISTINCT), lines (9,994 COUNT) carried as exact sample-size companions.
* Baseline and authority rules: authoritative order-grain TOTAL is primary; line-fact values enter solely as recomputation and cross-check inputs, never as competing totals; the band TOTAL row is an independent cross-check, never a driver.
* Reconciliation rules: source totals within 0.05; identity/dual gaps ≤ 1e-6; SUM/SUM margins within 1e-6; band TOTAL agreement on net/gross/discount/freight/contribution/WAD/margin; negative-order count agreement between order-fact count and band TOTAL (50 = 50).
* Null and `N/A` handling: exactly 2 NULL freight lines preserved and flagged (never imputed; 25.05 pair total via order aggregation only); zero-revenue margin guards retained (untriggered); single UNKNOWN return order (`CA-2015-102015`) retained and never defaulted; unlicensed views do not occur at TOTAL grain, so no `N/A` metric rows are needed (unlike band/scenario slices).

## 8. Validation Evidence

* 18/18 quality checks passed, zero failing.
* Full list of validation check IDs: `inputs-exist`, `frozen-inputs`, `quarantine`, `inputs`, `scenarios-off`, `discount-range`, `quantity-total`, `revenue-reconcile`, `cogs-reconcile`, `freight-reconcile`, `contribution-reconcile`, `margin-reconcile`, `wad-reconcile`, `band-total-crosscheck`, `negatives`, `return-cohorts`, `ambiguity`, `grain-consistency` (all IDs unique; every PASS supported by code or independently verified evidence).
* Schema checks: frozen input shapes (9,994 lines / 5,009 unique orders); quarantine exclusion asserted at load and in-frame; return/support OFF asserted (all flags FALSE, all scenario costs 0); observed discounts within [0, 1) with zero NULLs.
* Grain checks: authoritative order-grain TOTAL primary with line-fact recomputation beside — never instead of — the authoritative sums; no line partials mixed into totals.
* Arithmetic checks: net revenue, COGS (with per-line percentage identity, gap 4.55e-13), freight, and contribution reconcile within 0.05; SUM/SUM margin reconciles within 1e-6; WAD dual-form reconciles (gap 2.78e-17) with value 0.197887 ± 1e-6; ORDER TOTAL cross-check matches on net/gross/discount/freight/contribution/WAD/margin.
* Reconciliation checks: 50 negative-contribution orders counted from the order fact and matched to the band TOTAL; return cohorts YES 296 / UNKNOWN 1 / NOT_RETURNED 4,712 summing to 5,009 with UNKNOWN never defaulted; exactly 2 NULL freight lines in the single ambiguous order preserved and flagged.
* Identifier and source-protection checks: frozen SHA-256 asserted before loading; quarantine column present-but-excluded; fail-loud gates with no partial output on any breach.
* Output SHA-256 hash: `phase4c_baseline_total.csv` = `6782330a066722fa020ddad741e452a317588b30468d381df715bd32848e1bc5` (matches the quality JSON `outputs` block; independently recomputed).

Independently audited evidence (recomputed from frozen files without re-executing the implementation): source hashes and row counts; the CSV/output-hash match; all TOTAL values, gaps, distributions, margins, WAD, flags, and counts. Implementation-reported evidence (structurally supported by the inspected code): byte-identical reruns and loud missing-file/wrong-file failures with no partial output.

## 9. Known Non-Blocking Notes

1. Metric values are emitted at full float `repr` precision (e.g. `2297200.8603000003`); exact and deterministic, but less readable than frozen-record rounding. Reconciliation is unaffected.
2. A wrong-input run fails at the earliest applicable gate (existence, then frozen-hash) before reaching deeper checks; this is defensive behavior and does not affect the frozen-input execution.

## 10. Determinism and Failure Behavior

Only the evidence actually available is documented (no direct testing was performed during this documentation task; nothing was re-executed):

* Determinism: fixed metric ordering, `repr()` numeric formatting, no timestamps, no randomness, and no environment-dependent values by construction (code inspection); byte-identical consecutive reruns as reported in the implementation report and stated in the quality artifact's determinism record.
* Failure behavior: missing files fail `[inputs-exist]`, hash mismatches fail `[frozen-inputs]`, and any failed check raises `VALIDATION FAILED` with no output written (code inspection of the fail-loud gates plus implementation-reported missing/wrong-file tests); outputs are written only after every check passes.
* No stronger claims are made than this evidence supports.

## 11. Artifact Protection

* AO-01 implementation and evidence were already committed and pushed (implementation and quality JSON carried in the earlier AO-01 commit; this record completes the frozen set).
* Later AO-02 through AO-06 artifacts (code, outputs, and freeze records) were not modified.
* Precise hash-verification wording: frozen input bytes verified against recorded freeze hashes before loading; the recorded output hash matches the actual CSV byte-for-byte (independently recomputed); no hash is claimed without a recorded reference.

## 12. Change Boundary

Explicitly excluded from this freeze: later AOs (AO-02 through AO-06 as new work — all already frozen separately), dashboards, visualizations, recommendations, optimization, causal claims, new scenario types, new business dimensions, and any change to AO-01 inputs, code, or evidence beyond this documentation record.

## 13. Git and Artifact Policy
* Do not track the ignored CSV (`data/processed/phase4c_baseline_total.csv` stays ignored under `*.csv`).
* Track the AO-01 implementation script (`src/data/build_phase4c_baseline_summary.py`).
* Track the AO-01 quality JSON (`data/processed/phase4c_baseline_total_quality.json`).
* Track this freeze document (`docs/PHASE_4C_AO-01_FREEZE.md`).
* Do not modify AO-02 through AO-06 files.
* Do not modify the approved design document.
* Do not modify frozen source artifacts.

## 14. Confirmed Baseline Results

Only values supported by the AO-01 output and quality JSON (exact output precision; rounded forms in parentheses):

* Net revenue `2297200.8603000003` (2,297,200.86); gross revenue `2863935.04`; discount amount `566734.1797000002`.
* Modeled COGS `1493910.1284699999` (1,493,910.13); modeled gross profit `803290.7318300004`; modeled gross margin `34.96824094542153`% (34.97%).
* Freight cost `238173.78999999998` (238,173.79); cost-to-serve identical (return/support OFF).
* Contribution profit `565116.9418299999` (565,116.94); contribution margin `24.600240736293262`% (24.60%).
* WAD `0.19788653436077944` (0.1979); realization `80.21134656392206`% (80.21%).
* Quantity 37,873; order count 5,009; line count 9,994; negative-contribution orders 50; return cohorts YES 296 / UNKNOWN 1 / NOT_RETURNED 4,712; NULL-freight lines 2.

## 15. Freeze Decision

* AO-01 is approved for freeze based on the existing implementation, formal audit (`APPROVED FOR AO-02`, no blocking issues), and 18/18 validation evidence.
* The implementation (`src/data/build_phase4c_baseline_summary.py`), output (`data/processed/phase4c_baseline_total.csv`, 20 rows × 9 columns), and validation evidence (`data/processed/phase4c_baseline_total_quality.json`) constitute the frozen AO-01 reference state.
* The generated CSV remains ignored according to repository policy.
* Any future change must be separately scoped, validated, and documented.
