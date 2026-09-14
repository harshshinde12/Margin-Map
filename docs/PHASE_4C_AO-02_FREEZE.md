# Phase 4C AO-02 Freeze

`FROZEN — APPROVED`

## 1. Freeze Status

* AO: AO-02 — Contribution by discount band (observed, ORDER basis).
* Status: `FROZEN — APPROVED`
* Objective: state where baseline revenue, freight, and contribution sit across observed discount configurations, per the approved Phase 4C analytical interpretation design.
* Baseline/scenario status: `OBSERVED BASELINE`
* Grain: Overall × discount band.
* ORDER basis: authoritative.
* LINE basis: separate partial companion (labeled partials beside — never instead of — the ORDER rows).
* Audit decision: `APPROVED FOR AO-02 FREEZE` (formal audit completed with no blocking issues).

## 2. Approved Scope

AO-02 provides:

* Baseline revenue, freight, and contribution by observed discount band.
* ORDER-basis authoritative results (B0–B5 plus TOTAL).
* LINE-basis partial companions (B0–B5 plus TOTAL, marked `LINE_PARTIAL_EXCL_AMBIGUOUS`).
* Explicit basis markers on every row.
* Metric and limitation metadata on every row (unit, definition reference, limitation, source artifact).

Explicitly not included:

* AO-03 through AO-06.
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

## 3. Frozen Implementation

* Implementation path: `src/data/build_phase4c_band_contribution.py` (standalone; reads frozen inputs read-only; writes new files only after all validations pass).
* Output paths:
  * `data/processed/phase4c_band_contribution.csv` (238 metric rows × 11 columns).
  * `data/processed/phase4c_band_contribution_quality.json` (17/17 checks PASS).
* The CSV is ignored under the existing `*.csv` policy and must not be tracked, while the quality JSON is committable validation evidence.

## 4. Source Artifacts

| Artifact | Full SHA-256 | Rows | Role |
| -------- | ------------ | ---: | ---- |
| `discount_band_summary.csv` | `ad8f7e571c76f295bde3cb119bca4b7ff56c7b3e1734869ebf60f8d7e3c236eb` | 14 | Primary source (ORDER band rows B0–B5 plus TOTAL; LINE companions) |
| `order_margin_map_phase2.csv` | `ae6c349c9995747f2fef91cf1db6b940a73d99d6b2fede5ff3dff918f429d267` | 5,009 | Independent TOTAL cross-check (authoritative contribution) |
| `fact_margin_map_phase2.csv` | `4c471feeda642e5ecbd2263782b4fc0f1655962f6c6488bdfe47886df2f01cb1` | 9,994 | Independent count/quantity cross-check |
| `fact_sales_cogs.csv` | `4d8de717486b323ffb656d13c94fd6bd94f8e61d1a93ea339a602ab5303b9988` | 9,994 | Frozen reference (never read by AO-02; confirmed unchanged) |

State that:

* Frozen hashes were independently verified character-for-character against the actual files and all prior freeze records.
* Frozen inputs remain unchanged (hashes identical before and after implementation and audit).
* Inputs are opened read-only; the implementation never writes to a frozen path.
* AO-02 outputs use new filenames and cannot overwrite frozen inputs.

## 5. Output Structure

* 238 output rows (14 basis×band blocks × 17 metric rows).
* 11 columns: `output_name, scenario_status, grain, basis, band, source_artifact, metric_name, metric_value, unit, definition_ref, limitation`.
* 14 basis×band blocks (ORDER B0–B5 + TOTAL; LINE B0–B5 + TOTAL).
* ORDER block before LINE block.
* B0→B5→TOTAL ordering within each block.
* Fixed metric ordering within each block.
* 17 metric rows per basis×band block (16 measures plus one explicit N/A counterpart row per block).
* Explicit N/A rows with reasons (7 LINE `neg_contribution_orders` rows; 7 ORDER `neg_contribution_lines` rows; empty value, never zero-filled).
* No duplicate or missing rows; no basis or grain mixing (verified: 17 distinct metrics per block, uniform status `OBSERVED BASELINE`, uniform grain `Overall x discount band`).

## 6. Validation Evidence

* 17/17 quality checks passed, zero failing.
* Full list of validation check IDs: `inputs-exist`, `frozen-inputs`, `quarantine`, `inputs`, `band-schema`, `band-coverage`, `authority`, `flags`, `band-totals-reconcile`, `authoritative-total`, `line-gap`, `margins-recomputed`, `wad-recomputed`, `negatives`, `order-fact-crosscheck`, `band-counts`, `grain-consistency` (all IDs unique; every PASS supported by code or independently verified evidence).
* ORDER totals and band-count results: ORDER detail counts partition 5,009 unique orders (B0 2055 / B1 415 / B2 1634 / B3 278 / B4 274 / B5 353); ORDER TOTAL contribution 565,116.94183 equals the frozen baseline (±0.05); revenue, freight, and quantity cross-checked against the order/line facts.
* LINE partial contribution gap: ORDER TOTAL minus LINE partial TOTAL = 200.0475999999 (expected 200.0476 ± 0.05).
* Negative-contribution distributions: ORDER B0 14 / B1 3 / B2 24 / B3 1 / B4 3 / B5 5 / TOTAL 50, confirmed against the order-fact count of 50; LINE TOTAL 109 kept strictly on its own grain.
* Margin and WAD recomputation: all margins recomputed SUM/SUM on net revenue and all WADs recomputed gross-weighted per row (gaps ≤ 1e-6 on all 14 rows); gross margin uses `modeled_gross_profit / net_revenue`; percentages never averaged.
* Fact cross-checks: order-fact contribution/revenue/freight/quantity/counts match ORDER TOTAL; flags all FALSE as stored; neg-count NULL discipline enforced on detail rows.
* Output SHA-256 hash: `phase4c_band_contribution.csv` = `fb568bd33ae4dd7b2ea5aff490eba1a72a2ea80b6366b6dc56fcd8866636953a` (matches the quality JSON `outputs` block; independently recomputed).

Independently audited evidence (recomputed from frozen files without re-executing the implementation): source hashes and row counts; the CSV/output-hash match; band values, gap, distributions, margins, WAD, flags, and counts. Implementation-reported evidence (structurally supported by the inspected code): byte-identical reruns and loud missing-file/wrong-file failures with no partial output.

## 7. Known Non-Blocking Notes

1. `phase3b_quality_report.json` is documented as a source/reference artifact but is not parsed at runtime; its relevant freeze record was independently checked.
2. A wrong-schema CLI override can fail at the frozen-hash gate before reaching the deeper schema gate; this is defensive behavior and does not affect the frozen-input execution.

## 8. Audit and Freeze Decision

* Formal audit completed (`APPROVED FOR AO-02 FREEZE`).
* No blocking issues found.
* AO-02 is approved for freezing.
* This document records the freeze status.
* AO-02 may now be committed and pushed after a final Git review.

## 9. Git and Artifact Policy

* Do not track the ignored CSV (`data/processed/phase4c_band_contribution.csv` stays ignored under `*.csv`).
* Track the AO-02 implementation script (`src/data/build_phase4c_band_contribution.py`).
* Track the AO-02 quality JSON (`data/processed/phase4c_band_contribution_quality.json`).
* Track this freeze document (`docs/PHASE_4C_AO-02_FREEZE.md`).
* Do not modify AO-01 files.
* Do not modify the approved design document.
* Do not modify frozen source artifacts.
