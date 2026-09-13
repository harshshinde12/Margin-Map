# Phase 4B — Discount Increase Scenario Freeze Review

> Status: **FROZEN — APPROVED**
>
> This slice is formally frozen by the owner decision recorded in §9.
> Every figure discussed below is hypothetical arithmetic sensitivity
> under stated assumptions. Nothing here is a forecast, a demand
> statement, evidence about what would have sold, a causal estimate,
> or a pricing recommendation.

## 1. Purpose

This document records the implementation and validation state of the
Phase 4B discount-increase scenario slice and the evidence on which the
owner froze it (§9). Design authority:
`docs/PHASE_4B_DESIGN_DISCOUNT_INCREASE.md`, the frozen Phase 4A
architecture, the approved Phase 4B gates, the implementation contract
(`docs/PHASE_4B_IMPLEMENTATION_CONTRACT.md`), and the frozen first slice
(`docs/PHASE_4B_IMPLEMENTATION.md`, `docs/PHASE_4B_FREEZE.md`).

## 2. Scope

- Uniform discount increase across all valid transaction lines:
  `hypothetical_discount = observed_discount + increase_percentage_points`.
- Percentage-point input convention: `--increase-pp 0.05` means an
  increase of 5 percentage points (decimal-fraction scale; display-scale
  values such as `5` are rejected).
- Quantity remains constant (observed quantities reused bit-identical).
- Modeled COGS percentage remains frozen (line-level `modeled_cogs_pct`;
  hypothetical COGS recomputed from hypothetical net revenue).
- Observed freight treatment is preserved, including ambiguous-freight
  handling (NULL and flagged at line level; pair total via order
  aggregation only).
- Return-processing and support adjustments remain disabled (OFF / zero).
- Results are aggregated bottom-up to the order level and reported at
  Order × Discount Band on the ORDER basis (baseline bands, plus TOTAL).
- No demand response, causal inference, forecasting, or optimization is
  included. Unsupported metrics are marked `N/A` with reasons, never
  estimated.

## 3. Implementation

Implementation file: `src/data/build_phase4b_increase_scenarios.py`
(standalone; the frozen uniform-replacement implementation is not
modified, imported, executed, or depended upon).

- Input validation: `--increase-pp` is a required visible CLI argument
  parsed as a float. Non-finite values fail the `increase-exists` gate;
  negative values fail the `increase-sign` gate (increase-only slice);
  values above `0.80` fail the `increase-bounds` gate, with a
  display-scale hint for values at or above `1.0`.
- Six-decimal discount rounding: the observed discount is rounded to six
  decimals (`discount_r`); the resulting discount is computed as
  `d_prime = observed_discount_rounded + increase` and rounded to six
  decimals before any downstream use.
- Discount bounds: every resulting `d_prime` must satisfy
  `0.00 <= d_prime <= 0.80`. Any violation fails the whole run via the
  `discount-bounds-per-line` gate, reporting offending `row_id`s, counts,
  and violating values.
- Fail-loud behavior and output gating: invalid inputs and invalid
  resulting discounts do not produce scenario outputs. There is no
  clipping, no dropped rows, and no partial-subset execution. Output
  files are written only after every validation check has passed, and
  frozen inputs are hash-checked before and after the run.

## 4. Outputs

Zero-increase validation artifacts:

- `data/processed/phase4b_scenario_increase_0.00.csv` (7 rows × 52
  columns: six Order × Discount Band rows plus TOTAL, per the quality
  report).
- `data/processed/phase4b_scenario_increase_0.00_quality.json`
  (validation evidence for the zero-increase run).

CSV outputs are generated artifacts and must not be treated as source
data. Frozen source and fact files are never written by the
implementation.

## 5. Validation results

The zero-increase run (`--increase-pp 0`) passed all `22/22` checks with
unique check IDs and zero failures, per
`data/processed/phase4b_scenario_increase_0.00_quality.json`.

- Inherited checks retained from the Gate 9 set and first slice:
  quarantine exclusion, input shapes, return/support OFF, observed
  discount range, ambiguity preservation, line hypotheticals, freight
  passthrough, order-band assignment, quantity constancy, COGS rollup
  reconciliation, baseline reconciliation, variance reconciliation,
  TOTAL reconciliation, metadata lineage, and frozen-input integrity.
- Seven discount-increase-specific checks, all `PASS`:
  `increase-exists`, `increase-sign`, `increase-bounds`,
  `discount-bounds-per-line`, `no-silent-exclusion`,
  `hypo-revenue-dual-additive`, `metadata-increase`.
- Validated scope: 9,994 valid transaction lines; 5,009 unique orders;
  total quantity 37,873.
- Validation covered: quantity preservation, discount bounds, revenue
  reconstruction (dual-form), COGS reconciliation, freight preservation,
  bottom-up order-level aggregation, baseline discount-band assignment
  (`B0=2055 | B1=415 | B2=1634 | B3=278 | B4=274 | B5=353`),
  metadata and scenario identity
  (`discount_increase` / `increase_pp` / `discount_increase_pp_0.00` /
  `all_valid_lines`), deterministic output, and quarantine exclusion of
  the quarantined Profit field.

## 6. Invalid-input and fail-loud tests

The following tests were performed and failed as intended without
producing invalid outputs:

- Negative increase: `--increase-pp -0.05` (rejected as the wrong slice
  type).
- Display-scale input: `--increase-pp 5` (rejected by the
  increase-bounds gate).
- Excessive increase: `--increase-pp 0.95` (rejected by the
  increase-bounds gate).
- Non-numeric input (rejected before any scenario computation).
- Positive increase of `0.05`, which fails because 300 valid lines
  already have an observed discount of `0.80`, so the resulting discount
  would exceed the allowed upper bound.

The implementation does not clip discounts, silently drop rows, or
produce partial results. Failed runs report diagnostics (including
offending `row_id`s, counts, and violating values) and leave no output
treated as valid.

## 7. Determinism and protection

Verified SHA-256 hashes from the existing validation evidence:

- Zero-increase CSV
  (`data/processed/phase4b_scenario_increase_0.00.csv`):
  `10fb41f207c7cc011d3fbfe5bdbaec0bbfdc0be4e53cf39f3a0bf7ce087c9560`
- Zero-increase quality JSON
  (`data/processed/phase4b_scenario_increase_0.00_quality.json`):
  `52c9938394667dad4b8c29baefc282d84bb5f53450b1a9bb608dc559e4dcf7bf`

Consecutive runs of the same valid input reproduce byte-identical
artifacts (SHA-256-compared); there are no timestamps, no randomness,
and band keys are deterministically ordered.

Previously frozen artifacts were checked and remained unchanged, per
`docs/PHASE_4B_FREEZE.md`:

- `data/processed/fact_sales_cogs.csv`
  `4d8de717486b323ffb656d13c94fd6bd94f8e61d1a93ea339a602ab5303b9988`
- `data/processed/fact_margin_map_phase2.csv`
  `4c471feeda642e5ecbd2263782b4fc0f1655962f6c6488bdfe47886df2f01cb1`
- `data/processed/order_margin_map_phase2.csv`
  `ae6c349c9995747f2fef91cf1db6b940a73d99d6b2fede5ff3dff918f429d267`
- `data/processed/phase4b_scenario_uniform_0.10.csv`
  `6771a5f2ec4eb1584a7965768766e329c4e80f1b3ae805992c9ff65a7b9da2d1`
- `data/processed/phase4b_scenario_quality.json`
  `4e3c4d8a9e3a8b127ee1f4522f505cc9bafaa2682173712d68fc84915855047b`

## 8. Known non-blocking observations

- The design document (`docs/PHASE_4B_DESIGN_DISCOUNT_INCREASE.md`) states
  `APPROVED FOR IMPLEMENTATION — NOT YET FROZEN`; this freeze record
  completes the slice freeze, decided by the owner in §9.
- Some invalid command-line inputs exit through standard argument
  parsing rather than a custom validation check, but they still fail
  safely without producing outputs.
- The `0.05` example cannot succeed on the current dataset because some
  lines are already at the maximum allowed discount; this is the
  designed fail-loud behavior, not a defect.
- The quality JSON provides validation evidence; detailed financial
  totals remain available in the CSV output.

## 9. Freeze decision

- `Decision: FROZEN — APPROVED`
- The Discount Increase Scenario design
  (`docs/PHASE_4B_DESIGN_DISCOUNT_INCREASE.md`) was approved for
  implementation.
- The implementation
  (`src/data/build_phase4b_increase_scenarios.py`) and the validation
  evidence
  (`data/processed/phase4b_scenario_increase_0.00_quality.json`) were
  reviewed against the design, the implementation contract, and the
  frozen first slice.
- The zero-increase validation passed all `22/22` checks with unique
  check IDs and zero failures.
- The required fail-loud behavior was verified: invalid inputs and
  out-of-bounds resulting discounts fail loudly without producing valid
  outputs, with no clipping, silent row drops, or partial-subset
  execution.
- The Discount Increase Scenario slice is formally frozen. The frozen
  scope and assumptions in §§2–5 must be preserved.
- Future changes must be handled as a new version or a new controlled
  slice, not as edits to this frozen record.
- This freeze does not convert the scenario into a forecast, causal
  estimate, demand prediction, or pricing recommendation. All figures
  remain hypothetical arithmetic sensitivity under the stated
  assumptions.
