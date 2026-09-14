# Phase 5 Display Scope and Conventions — Business-Facing Power BI Displays

```text
APPROVED FOR DISPLAY IMPLEMENTATION — NOT YET IMPLEMENTED
```

Gate 10 constrains the display phase but does not itself authorize any specific visual. Power BI implementation is authorized only under the approval recorded in §9. This is a planning and scope record only: no visual, dashboard, calculation, or output is built here, and no frozen artifact is altered.

## 1. Status

```text
OPENED FOR DISPLAY-SCOPE DEFINITION — NOT YET IMPLEMENTED
```

This document defines the approved display scope and binding conventions for the separately gated business-facing display phase. Gate 10 (approved 2026-09-13, `docs/PHASE_4B_DECISION_LOG.md`) constrains every future visual but authorizes none; each display below proceeds under the approval recorded in §9.

## 2. Objective

Define business-facing Power BI displays based exclusively on the frozen Phase 4C outputs (AO-01–AO-06), so decision-makers can read baseline performance, discount-band exposure, and discount-sensitivity arithmetic without misreading arithmetic as prediction. All displayed values come from frozen interpretation outputs; the display phase performs no analysis of its own.

## 3. Approved Source Outputs

| Source | Grain | Purpose | Limitation |
| ------ | ----- | ------- | ---------- |
| AO-01 baseline TOTAL summary (`phase4c_baseline_total.csv`, 20 rows; quality 18/18) | Overall TOTAL, order economics rolled up, authoritative | Single authoritative baseline reference for every other reading | Conditional on modeled COGS benchmarks; return/support OFF (excluded, not actual); freight methodology caveat carried |
| AO-02 contribution by discount band (`phase4c_band_contribution.csv`, 238 rows; quality 17/17) | Overall × discount band, ORDER basis authoritative with LINE-basis partial companions | Where baseline revenue, freight, and contribution sit across observed discount configurations | LINE rows partial (gap 200.0476) beside — never instead of — ORDER rows; descriptive comparison only |
| AO-03 TOTAL scenario comparison (`phase4c_scenario_comparison_total.csv`, 105 rows; quality 19/19) | Overall TOTAL per scenario instance (baseline / hypothetical / variance blocks) | Headline arithmetic sensitivity per frozen instance beside its identical-scope baseline | Identity slices zero by construction; nonzero universal shifts have no valid output; LINE detail not licensed |
| AO-04 contribution variance by baseline discount band (`phase4c_contribution_variance_by_band.csv`, 420 rows; quality 21/21) | Overall × baseline discount band, ORDER basis | How headline sensitivity distributes across baseline discount configurations | Baseline bands only, never re-banded; no incompatible grains; descriptive only |
| AO-05 observed order-level context (`phase4c_order_reading.csv`, 60,108 rows; quality 17/17) | Order (`order_id`), authoritative | Distributional context (WAD spread, negative orders, ambiguity case, volume) supporting — never replacing — band readings | Single observations; no hypothetical order-level detail exists or may be fabricated |
| AO-06 data-quality and eligibility summary (`phase4c_quality_summary.csv`, 125 rows; quality 9/9) | Artifact level per file, then TOTAL verdict | Eligibility gate: which artifacts may source interpretation | Arithmetic/lineage fitness only; no behavioral reading licensed |

## 4. Proposed Display Inventory

Display candidates (defined, not implemented). Each display must use its corresponding frozen output and must not mix incompatible grains:

1. Baseline profitability summary — from AO-01; one TOTAL view of revenue, COGS, gross/contribution profit and margins, WAD, volume, loss/cohort context, and NULL indicators.
2. Contribution by baseline discount band — from AO-02; ORDER-authoritative band view (B0–B5 + TOTAL) with LINE-partial companions kept in a separately labeled block.
3. TOTAL scenario comparison — from AO-03; per-instance baseline / hypothetical / variance blocks at TOTAL grain only.
4. Scenario variance allocation by baseline discount band — from AO-04; per-band variance view on baseline bands with separated layers.
5. Observed order-level context — from AO-05; distributional views (WAD spread, negative-order list, ambiguity case, volume) at order grain, observed values only.
6. Data-quality and eligibility summary — from AO-06; artifact eligibility table with check standing, plus the TOTAL verdict.

## 5. Binding Display Rules

All applicable Gate 10 requirements (binding on every visual, not advisory):

* Baseline, hypothetical, and variance values must be separated (distinct blocks/areas; never merged into unexplained numbers).
* Absolute changes and margin changes in percentage points must be shown separately (margin changes never labeled `%`).
* Scenario type must be visible (`uniform_replace_0.10` / `discount_increase_pp_0.00` / `discount_decrease_pp_0.00`).
* Discount input must be visible (stated rate / pp change with input form).
* Reporting grain must be visible (TOTAL, Overall × band with ORDER/LINE basis markers, or Order).
* Validation status and quality flags must be visible (check standing, `low_sample_flag`, ambiguity/negative markers).
* Unsupported metrics must appear as `N/A` with an explanation (never zero-filled, never omitted silently).
* Gross profit, contribution profit, and discount-related revenue forgone must remain distinct.
* Methodology assumptions must be visible:
  * constant observed quantity;
  * modeled COGS;
  * freight passthrough;
  * return-processing costs OFF;
  * support costs OFF.
* The standing caveat must be visible wherever a predictive or causal misreading is possible:

  ```text
  Illustrative arithmetic sensitivity under stated assumptions; not a forecast, causal estimate, demand prediction, or optimized-pricing recommendation.
  ```

* Permitted descriptive wording only ("illustrative constant-quantity scenario", "arithmetic change under the stated assumptions", "conditional illustration, not a forecast"); prohibited wording (forecast/prediction/causal/optimal/best-policy claims) must not appear except inside this prohibition.
* Deferred views remain unavailable unless separately approved.

## 6. Grain and Authority Rules

* ORDER-authoritative economics (order fact and ORDER-basis rows): the only licensed basis for contribution headlines, scenario variances, and TOTAL statements.
* LINE-partial economics (LINE-basis rows, gap 200.0476 to the authoritative total): shown only in separately labeled companion blocks, never averaged with ORDER rows.
* Gross-only or other limited measures (category/sub-category/product cuts; `N/A`-marked views): shown only where licensed, with the attributable-grain reason visible.
* Observed baseline values (`OBSERVED BASELINE`): historical/modeled facts under return/support OFF.
* Hypothetical arithmetic sensitivity values (`HYPOTHETICAL_ARITHMETIC_SENSITIVITY`): scenario-only values existing inside their named instance and assumption set.

No visual may imply that a partial or incompatible grain is equivalent to the authoritative order-level result.

## 7. Deferred and Prohibited Views

Explicitly deferred or prohibited in this phase:

* Customer segmentation.
* Product/category-specific scenario views.
* Customer-level hypothetical detail (no such frozen artifact exists; fabrication forbidden).
* New scenario types.
* Re-banding (hypothetical or otherwise).
* Forecasting.
* Causal claims.
* Elasticity or demand analysis.
* Optimization.
* Pricing recommendations.
* Unsupported calculations (any computation not present in the frozen outputs).
* Any modification of frozen artifacts (all display sources stay read-only).

## 8. Implementation Readiness Checklist

Before Power BI work begins, all of the following must hold:

* [x] Display scope is approved.
* [x] Display inventory is approved.
* [x] Required labels are approved.
* [x] Caveat wording is approved.
* [x] Grain and authority rules are approved.
* [x] Deferred views remain blocked.
* [x] Frozen source files will be used read-only.
* [x] No new analytical outputs are required.

All boxes are checked per the §9 approval below; implementation may proceed strictly within the approved scope.

## 9. Decision Required

```text
Display-phase decision:

APPROVED — OPTION 1

The proposed display scope and conventions are approved without modification.

The approved scope includes only displays based on the frozen Phase 4C AO-01–AO-06 outputs.

The following requirements are binding on every display:

- Baseline, hypothetical, and variance values remain separate.
- Absolute changes and margin changes in percentage points are shown separately.
- Scenario type, discount input, reporting grain, validation status, and quality flags are visible.
- Unsupported metrics are displayed as N/A with explicit reasons.
- Gross profit, contribution profit, and discount-related revenue forgone remain distinct.
- Methodology assumptions are displayed.
- The standing “illustrative arithmetic sensitivity, not a forecast” caveat is shown wherever required.
- Deferred and prohibited views remain unavailable.
- Frozen Phase 4C artifacts are read-only and must not be modified.
```

Recorded per explicit project-owner approval of Option 1 (approve without modification). Power BI implementation may proceed strictly within this approved scope; any departure requires a new documented approval.
