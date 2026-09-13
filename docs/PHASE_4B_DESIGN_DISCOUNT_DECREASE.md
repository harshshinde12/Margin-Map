# Phase 4B Design — Uniform Discount Decrease (Percentage-Point Input)

> Standing: **DESIGN ONLY — DRAFT, NOT APPROVED, NOT FROZEN.**
> No calculations are implemented, no scripts are created or modified, no
> outputs are produced, and no frozen Phase 1, 2, 3, 4A, or Phase 4B
> first-slice, increase-slice, or uniform-replacement artifact is altered
> by this document. Design authority: the frozen Phase 4A architecture
> (`docs/PHASE_4A_PRICING_SCENARIO_ARCHITECTURE.md`), the approved Phase
> 4B gates (`docs/PHASE_4B_DECISION_LOG.md`), the implementation contract
> (`docs/PHASE_4B_IMPLEMENTATION_CONTRACT.md`), the frozen first slice
> (`docs/PHASE_4B_IMPLEMENTATION.md`, `docs/PHASE_4B_FREEZE.md`), the
> increase design (`docs/PHASE_4B_DESIGN_DISCOUNT_INCREASE.md`), and the
> increase freeze review (`docs/PHASE_4B_DISCOUNT_INCREASE_FREEZE.md`).
>
> **Reading guide.** Every figure produced under this design would be
> hypothetical arithmetic sensitivity under stated assumptions (constant
> observed quantity, frozen modeled-COGS percentage, observed freight
> passthrough, return/support OFF). Nothing here is a forecast, a demand
> statement, evidence about what would have sold, a causal estimate, or a
> pricing recommendation.

## 1. Purpose and analytical standing

Specify the next Phase 4B scenario slice — a uniform discount
**decrease** applied as a single percentage-point decrement to every
valid transaction line — with unambiguous input, calculation, bounds,
rounding, output, validation, integration, and reproducibility rules,
before any build begins. This document resolves every open design point
so a future build has no silent choices.

The approved work distinguishes five analytical categories that must
never be conflated: observed historical analysis and hypothetical
arithmetic sensitivity (the only two permitted functions) versus
forecasting, causal inference, and optimization (all three forbidden —
no estimate, coefficient, or recommendation in this design may be read
as a prediction about future transactions, a claim about what a
discount change would cause, or a selection of best or recommended
discounts).

## 2. Exact scope of this slice

In scope for this slice only:

- One scenario type: **discount decrease** (Gate 6 active type),
  universal scope over all valid lines (9,994 lines; 5,009 orders);
  per-line `hypothetical_discount = observed_discount -
  decrease_percentage_points`.
- Line-level hypotheticals (§14) with constant observed quantity (§10),
  frozen revenue-based modeled-COGS percentage (§11), and observed
  freight passthrough (§12); return/support OFF (§13); bottom-up order
  aggregation (§15); **Order × Discount Band** reporting only, on the
  ORDER basis with baseline bands (§§16–17), TOTAL row included.
- Full six-block schema (§18): baseline, hypothetical
  (`hypothetical_*`), variance (pp margin changes), scenario metadata
  and lineage (§19), grain markers, validation/quality flags, and
  `N/A`-with-reason for unlicensed metrics (§20).

## 3. Explicit out-of-scope items

Explicitly not in this slice and not representable as available:
discount increase (frozen slice) and any further uniform-replacement
rate beyond the frozen 0.10 instance; relative-change input form;
Segment × Discount Band reporting of the decrease scenario (licensed by
Gate 1 but deferred for this slice, which reports Order × Band only);
customer-level reporting; segment-, category-, and product-specific
designs; any non-constant quantity form or response parameter;
forecasting, causal, demand-prediction, or optimization claims;
fixed-unit-cost comparator activation; return/support rate layers;
dashboards and Power BI; float tolerances beyond the inherited values;
exact column-layout refinements beyond the contract blocks. No other
scenario type is authorized for implementation by this document.

## 4. Input contract

- **Single scalar input, one form per scenario.** A required, visible
  CLI argument, e.g. `--decrease-pp <value>`, holding the uniform
  percentage-point decrement. Exactly one input form per scenario run;
  the chosen form is recorded on every output. No per-line,
  per-segment, or second parameter in this slice.
- **Canonical precision.** Stated values are given to two decimals
  (e.g. `0.05`). The full float is recorded in metadata; the scenario
  identifier and filenames carry the two-decimal rendering (see §24).

## 5. Decimal percentage-point convention

The decrease is supplied as a **decimal fraction of 1**, on the same
scale as the frozen `discount` field: `0.05` means a decrease of 5
percentage points (e.g. `--decrease-pp 0.05`). Display-scale values
(e.g. `5` for “5pp”) are **not** accepted and fail the range check —
there is no percent-sign parsing and no 0–100 scale.

## 6. Treatment of zero and negative inputs

- **Zero permitted.** `0.00` is valid. It is the identity sensitivity
  (`hypothetical = observed`, variances zero) and is retained as a
  pipeline-validation case. It runs the full validation and output
  path; it is not a bypass.
- **Negatives rejected.** Any value `< 0` fails at argument parsing even
  if every resulting `d'` would remain within bounds, because a negative
  decrement is the frozen **discount increase** type and must not enter
  under a decrease identifier.

## 7. Hypothetical discount formula

Frozen Phase 1A definitions restated, quantity `q` held constant
throughout; `d` = observed discount, `Δ` = stated decrease,
`d'` = hypothetical discount:

```text
d'(line) = d - Δ
```

## 8. Discount rounding rules

Observed discount reused via the frozen idiom
(`discount_r = discount.round(6)`); `d' = discount_r - Δ` computed in
full float then **rounded to 6 decimals** before the bound check and
before any downstream use. Bound checks apply to the rounded value so
binary-float residue cannot fail a mathematically in-bound case nor
pass an out-of-bound one. Stored `hypothetical_discount` is the
6-decimal value.

## 9. Discount-bound rules

- **Permitted range.** Every resulting `d'` must satisfy
  `0.00 ≤ d' ≤ 0.80` (Gates 2/7). The stated `Δ` must satisfy
  `0.00 ≤ Δ ≤ 0.80`; anything else fails at parsing.
- **Fail-loud, whole-run rejection.** If **any** computed `d'` falls
  below 0.00 or above 0.80 — including near-bound underflow such as
  `Δ = 0.05` on a `d = 0.00` line — the scenario definition is invalid.
  The run **fails validation loudly and produces no output treated as
  valid**: no CSV, no partial-subset execution, no clipping, no
  extrapolation, no silent correction, and no dropping of offending
  lines to make the scenario pass. Dropping offending lines is silent
  exclusion and is forbidden (contract §5; Gate 7).
- **Diagnostic, not partial output.** A failed run may — and should —
  report the offending record identifiers and counts (affected
  `row_id`s, per-band counts, violating values, minimum `d'`) in its
  failure diagnostic so the input can be corrected and resubmitted. The
  diagnostic accompanies rejection; it never converts an invalid
  scenario into a valid one.
- **Count preservation.** A valid run accounts for all 9,994 lines and
  5,009 orders in scope; output TOTAL reconciles to the frozen baseline
  (revenue 2,297,200.86; COGS 1,493,910.13; freight 238,173.79;
  contribution 565,116.9418) within the documented tolerance.

## 10. Constant observed quantity treatment

Hypothetical revenue is computed holding quantity fixed at observed
values. Quantities are reused bit-identical (asserted, total 37,873 —
never assigned, inferred, or recalculated); every quantity-dependent
figure is labeled conditional on fixed quantities. No demand-response
modeling and no elasticity coefficients are introduced anywhere in this
slice.

## 11. Frozen modeled-COGS treatment

Default scenario COGS recomputed as hypothetical net revenue × frozen
line-level modeled-COGS percentage (`modeled_cogs_pct`, never derived
from order currency), with the baseline identity (`modeled_cogs == net
× pct/100`) asserted first. The mechanical consequence — gross margin
percentage constant by construction while currency moves with revenue —
is disclosed on every output. The fixed-unit-cost comparator is not
activated (no approved per-unit source exists). Implied unit costs are
never presented as actual procurement costs.

## 12. Observed freight passthrough

Observed freight passes through unchanged per line (values
bit-identical to load, NULLs preserved). The ambiguous freight pair (2
lines, `US-2014-150119`) stays NULL and flagged at line grain under all
scenarios; the 25.05 pair total enters only through authoritative
order-grain aggregation. No freight allocation below order grain, no
imputation, and no invented freight rates.

## 13. Return and support treatment

Return-processing cost remains **OFF** and support cost remains
**OFF** (zero means scenario-excluded, never actual cost) in every
baseline and hypothetical figure. Return status may be used only as an
observed filter or cohort flag. No return/support rate layer is
introduced in this slice.

## 14. Line-level calculations

Per valid transaction line, reusing frozen Phase 1A definitions (gross
is a derived reference, never an observed list price):

```text
gross(line)        = sales / (1 - d)              [d in [0, 1), proven]
d'(line)           = round6(round6(d) - Δ)
hypo_net(line)     = gross * (1 - d')
                     = sales * (1 - d') / (1 - d)  (dual form, reconciled)
hypo_disc_amt      = gross - hypo_net
hypo_cogs(line)    = hypo_net * modeled_cogs_pct / 100   (frozen line pct)
```

Source: frozen line fact `data/processed/fact_margin_map_phase2.csv`
(9,994 lines) for `sales`, `quantity`, `discount`, `net_revenue`,
`modeled_cogs_pct`, `freight_cost_observed`, flags, and OFF markers.
`source_profit_quarantined` is never loaded.

## 15. Bottom-up order aggregation

Line hypotheticals roll strictly bottom-up to orders (sums of line
hypotheticals; no top-down allocation, no lateral re-allocation):

```text
hypo_cts(order)    = authoritative order_freight + 0 + 0 (return/support OFF)
hypo_contrib(order)= SUM(hypo_net) - SUM(hypo_cogs) - order_freight
```

Freight enters only via the authoritative order fact
(`data/processed/order_margin_map_phase2.csv`, 5,009 orders — joined,
never recomputed). Margins aggregate SUM/SUM; averaging percentages is
forbidden; margin changes reported in percentage points; zero-revenue
hypothetical margin is NULL/blank, never 0-filled. Variances equal
hypothetical minus baseline, reconciled both ways.

## 16. Order × Discount Band reporting

Reporting is **Order × Discount Band only**, on the ORDER basis, with
baseline, hypothetical, and variance blocks side by side (6 band rows +
TOTAL = 7 rows). Segment × Band, customer-level, category, and
product-level scenario reporting are deferred and must not be built or
represented as available under this slice.

## 17. Baseline-band assignment rules

Each order is assigned exactly one band from its **baseline observed**
order-WAD band (D3B-03 rule) using the frozen `assign_band` boundaries
unchanged (B0 `d = 0` / B1 `(0, 0.15]` / B2 `(0.15, 0.25]` / B3
`(0.25, 0.35]` / B4 `(0.35, 0.55]` / B5 `(0.55, 0.80]`), so the B0
reference cohort stays identifiable. Hypothetical values are reported
beside — never re-banded by — the baseline band.

## 18. Full output schema

Same six blocks as the frozen slices (contract §4): (a) scenario
metadata and lineage (§19); (b) baseline metrics; (c) hypothetical
metrics (`hypothetical_*`); (d) variances with pp margin changes; (e)
grain markers (`basis = ORDER`, baseline `band`); (f) validation and
quality flags including `low_sample_flag` (30-line / 10-order
provisional thresholds), `ambiguity_note`, and `N/A`-with-reason for
unlicensed metrics (§20). Unsupported metrics are marked unavailable
with a reason — never estimated, never silently omitted. Currency uses
full double precision (no line-level cents rounding); reconciliation
tolerances follow the frozen slices: dual-form gaps ≤ 1e-6; variance
gaps ≤ 1e-9; freight variance exactly 0; source-total reconciliation
tolerance 0.05.

## 19. Scenario metadata and lineage

`scenario_type = discount_decrease` (distinct from
`uniform_replacement` and `discount_increase`); `input_form =
decrease_pp`; `scenario_id = discount_decrease_pp_<Δ:.2f>` (e.g.
`discount_decrease_pp_0.05`); `stated_decrease_pp` carries the full
input float; `scope = all_valid_lines`; standing
`HYPOTHETICAL_ARITHMETIC_SENSITIVITY_NOT_A_FORECAST`; assumption labels
`CONSTANT_OBSERVED_QUANTITY`, `FROZEN_MODELED_COGS_PCT`,
`OBSERVED_PASSTHROUGH`, `OFF` — the same vocabulary as the frozen
slices. Every output carries identifier, type, input form and values,
scope, assumption versions, and reporting grain; any
`uniform_replacement` or `discount_increase` residue fails validation.

## 20. Unsupported metrics and `N/A` reasons

`fixed_unit_cost_view = N/A` (`COMPARATOR_NOT_IN_INITIAL_BUILD`) and
`demand_response_view = N/A` (`RESPONSE_NOT_ESTIMATED`) on every row,
matching the frozen slices. Below-order-grain contribution and any
other unlicensed metric is likewise `N/A` with an explicit reason —
never estimated and never silently omitted.

## 21. Fail-loud validation requirements

The fifteen Gate 9 checks from the contract (§6) apply unchanged, plus
the following decrease-specific fail-loud gates (dependency order at
parse/load):

1. `decrease-exists` — `--decrease-pp` present and numeric;
   missing/NULL/non-numeric aborts before any I/O.
2. `decrease-sign` — `Δ ≥ 0`; negatives rejected as the wrong slice
   type (a negative decrement is the frozen discount-increase type).
3. `decrease-bounds` — `Δ ≤ 0.80`; display-scale values (e.g. `5`)
   fail here with a scale-hint diagnostic.
4. `discount-bounds-per-line` — every rounded `d'` in [0.00, 0.80]
   with §9 whole-run failure semantics; offending `row_id`s, counts,
   and minimum `d'` reported diagnostically.
5. `no-silent-exclusion` — scoped line/order counts equal frozen totals
   (9,994 / 5,009); any dropped or clipped line fails.
6. `hypo-revenue-dual-subtractive` — `hypo_net` reconciled between
   `gross * (1 - d')` and `sales * (1 - d') / (1 - d)` (gap ≤ 1e-6).
7. `metadata-decrease` — `scenario_type`, `input_form`,
   `scenario_id`, `stated_decrease_pp`, scope, and standing present and
   consistent with the filename; any `uniform_replacement` or
   `discount_increase` residue fails.

All other checks — quarantine exclusion, constant quantity
(bit-identical, total 37,873), COGS-percentage identity and rollup,
freight passthrough with ambiguous-pair NULL/flag preservation (2
lines, `US-2014-150119`; 25.05 via order aggregation only),
return/support OFF, baseline and variance reconciliation, pp margins,
N/A marking, claim-exclusion wording, frozen-hash integrity — are
inherited unchanged. Any failure identifies the issue and blocks valid
status. Note the lower-bound consequence of this slice: observed
zero-discount lines (B0 mass) breach `0.00` under any positive `Δ`, so
such scenarios fail loudly by design rather than passing on a partial
subset.

## 22. Deterministic output requirements

Identical frozen inputs plus identical stated `Δ` reproduce
byte-identical CSV and quality-JSON artifacts across consecutive runs
(SHA-256-compared, as in the frozen slices). No timestamps, no
randomness; sorted band keys (B0–B5, TOTAL); versioned constants; input
hashes recorded in the quality report; frozen inputs byte-identical
before and after. Reproduction command (from the project root, on
frozen inputs, once approved and built):

```text
python src/data/build_phase4b_decrease_scenarios.py --decrease-pp 0.00
```

Expected: Order × Band rows + TOTAL → the §24 CSV plus its quality
JSON, all checks PASS, byte-identical reruns. Any `Δ` whose `d'`
breaches [0.00, 0.80] fails loudly with no valid output.

## 23. Frozen-artifact protection

New standalone module only (frozen scripts expose no library API);
proven idioms — gross reconstruction, WAD dual-form check,
`assign_band` boundaries, `fail()` + `sha256()` + quality-JSON pattern,
authoritative order join — are copied verbatim, never imported, edited,
or executed from the frozen `src/data/` set. Off-limits per contract
§8: editing or importing the uniform-replacement or
discount-increase scripts, writing to any frozen filename, renaming or
moving frozen files, flipping any `*_scenario_enabled` flag in place,
deriving COGS percentages from currency summaries, allocating freight
below order grain, or loading the quarantined Profit column. Frozen
inputs are hashed before and after every run; any drift aborts. No
Phase 1–4A data file, script, schema, report, log, or freeze document —
and no frozen Phase 4B slice — is modified, regenerated, renamed, or
overwritten by work under this design.

## 24. Output naming convention

**New generated artifacts only; no frozen artifact may be overwritten.**
The CSV follows the project’s existing Git policy and remains ignored
by `.gitignore`, while the quality JSON remains committable validation
evidence because it is not ignored.
The CSV is generated as:
`data/processed/phase4b_scenario_decrease_<Δ:.2f>.csv`
For example:
`data/processed/phase4b_scenario_decrease_0.05.csv`
The quality JSON is generated alongside the CSV as:
`data/processed/phase4b_scenario_decrease_<Δ:.2f>_quality.json`
For example:
`data/processed/phase4b_scenario_decrease_0.05_quality.json`
The suffixed quality filename preserves the frozen
`phase4b_scenario_quality.json` and every frozen increase-slice
artifact byte-identical. Rate, increase, and decrease namespaces do not
collide.

## 25. Approval and freeze requirements

**DRAFT — NOT APPROVED, NOT FROZEN.** This document specifies the
decrease slice; it authorizes no build, selects no instance value
beyond the illustrative `0.05` examples above, and changes no frozen
artifact. A build may proceed only after explicit project-owner
approval of this record, and the slice is frozen only by a separate
explicit freeze decision with its own validation evidence. Any
departure — broader grains, wider bounds, response assumptions,
comparator activation, new scenario types, or silent-exclusion handling
— requires a new documented approval before it is built.
