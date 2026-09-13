# Phase 4B Approval Summary — Pricing-Scenario Gate Decisions

> All ten Phase 4B approval gates were **approved by the project owner on
> 2026-09-13** against the frozen Phase 4A architecture
> (`docs/PHASE_4A_PRICING_SCENARIO_ARCHITECTURE.md`,
> `docs/PHASE_4A_DECISION_LOG.md`, `docs/PHASE_4A_ARCHITECTURE_VALIDATION.md`,
> `docs/PHASE_4A_FREEZE.md`). Full records: `docs/PHASE_4B_DECISION_LOG.md`;
> consistency checks: `docs/PHASE_4B_APPROVAL_VALIDATION.md`. **No scenario
> calculations or outputs have been created** — this approval authorizes the
> next design/implementation stage only after this documentation is reviewed
> and frozen.

## Purpose

Resolve the ten open gates left pending by the Phase 4A freeze so that a
future Phase 4B build has unambiguous, owner-approved boundaries: what the
scenario module may compute (hypothetical arithmetic sensitivity under
stated assumptions), at which grains, within which bounds, under which
cost treatments, and under which validation and display rules — and what
remains explicitly out of scope.

## Gate decisions

| Gate | Final decision |
|---|---|
| 1. Scenario grain | Line-level application, bottom-up order aggregation; reporting Order × Discount Band and Segment × Discount Band; customer-level deferred |
| 2. Discount input design | Percentage-point change primary; relative and replacement forms labeled alternatives; range 0.00–0.80; no clipping/extrapolation/silent adjustment |
| 3. Quantity treatment | Constant observed quantity; hypothetical arithmetic sensitivity only; no forecasts or causal estimates |
| 4. COGS treatment | Frozen revenue-based modeled-COGS percentage as default, with margin-constancy disclosure; fixed-unit-cost comparator not in initial build; implied unit costs never presented as actual procurement costs |
| 5. Cost-to-serve treatment | Observed freight passthrough unchanged; ambiguous freight preserved at line level; no invented rates; order-level complete freight where valid; return/support OFF; return status filter/cohort flag only |
| 6. Scenario types | Active: discount increase, discount decrease, uniform replacement. Deferred: segment-, category-, product-specific scenarios |
| 7. Discount bounds | 0.00–0.80; values outside invalid with clear validation failure; no clipping, extrapolation, or silent correction |
| 8. Output schema | Metadata, baseline, hypothetical, variance, grain, and validation/quality flags; unsupported metrics marked unavailable with reason |
| 9. Validation thresholds | Fifteen mandatory fail-loud checks (bounds, no silent adjustment, constant quantity, revenue formula, COGS percentage, freight passthrough, ambiguity handling, OFF costs, baseline and variance reconciliation, percentage-point margins, unsupported-metric handling, metadata lineage, claim exclusion, determinism); failures block validity |
| 10. Dashboard display rules | Hypothetical labeling; separated baseline/hypothetical/variance; percentage-point margin changes; methodology assumptions shown; `N/A`-with-reason marking; no forecast, causal, demand-prediction, or optimized-pricing implications; deferred views unavailable |

## Deferred scope

Customer-level scenario reporting; segment-, category-, and
product-specific scenario designs; any non-constant quantity form (separate
evidence review required); fixed-unit-cost comparator activation (no
per-unit source exists); all scenario instance values; float tolerances;
exact output column layout; dashboard conventions beyond the binding
constraints. Deferred items must not be implemented or represented as
available.

## Mandatory limitations

Results are hypothetical arithmetic sensitivity under stated assumptions —
conditional illustrations, not forecasts, measurements of response, causal
estimates, or pricing recommendations. All modeled margins remain
conditional on the modeled COGS structure. The quarantined source Profit
field is excluded from all scenario computations. Frozen Phase 1–4A
artifacts are untouched by this approval.

## Conditions for beginning implementation

Phase 4B implementation may begin only after this approval documentation
(decision log, approval summary, approval validation) is reviewed and
frozen. The build must then implement exactly the approved scope above,
with every Gate 9 check enforced fail-loud and every Gate 10 display rule
binding on any visual. Any departure — broader grains, wider bounds,
response assumptions, comparator activation, or new scenario types —
requires a new documented approval before it is built.
