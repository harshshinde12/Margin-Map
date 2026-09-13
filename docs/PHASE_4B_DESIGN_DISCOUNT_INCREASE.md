# Phase 4B Design — Uniform Discount Increase (Percentage-Point Input)

> Standing: **APPROVED FOR IMPLEMENTATION — NOT YET FROZEN.**
> No calculations are implemented, no scripts are created or modified, no
> outputs are produced, and no frozen Phase 1, 2, 3, 4A, or Phase 4B first-slice
> artifact is altered by this document. Design authority: the frozen Phase 4A
> architecture (`docs/PHASE_4A_PRICING_SCENARIO_ARCHITECTURE.md`), the approved
> Phase 4B gates (`docs/PHASE_4B_DECISION_LOG.md`), the implementation contract
> (`docs/PHASE_4B_IMPLEMENTATION_CONTRACT.md`), and the frozen first slice
> (`docs/PHASE_4B_IMPLEMENTATION.md`, `docs/PHASE_4B_FREEZE.md`).
>
> **Reading guide.** Every figure produced under this design would be
> hypothetical arithmetic sensitivity under stated assumptions (constant
> observed quantity, frozen modeled-COGS percentage, observed freight
> passthrough, return/support OFF). Nothing here is a forecast, a demand
> statement, evidence about what would have sold, a causal estimate, or a
> pricing recommendation.

## 1. Purpose

Specify the next Phase 4B scenario slice — a uniform discount **increase**
applied as a single percentage-point increment to every valid transaction
line — with unambiguous input, calculation, bounds, rounding, output,
validation, integration, and reproducibility rules, before any build begins.
Resolves the twelve open points listed in §3–§11 so a future build has no
silent choices.

## 2. Scope

In scope for this slice only:

- One scenario type: **discount increase** (Gate 6 active type), universal
  scope over all valid lines; per-line
  `hypothetical_discount = observed_discount + increase_percentage_points`.
- Line-level hypotheticals with constant quantity, frozen revenue-based
  modeled-COGS percentage, and observed freight passthrough; return/support
  OFF; bottom-up order aggregation; **Order × Discount Band** reporting only,
  on the ORDER basis with baseline bands (D3B-03 rule), TOTAL row included.
- Full six-block schema: baseline, hypothetical (`hypothetical_*`), variance
  (pp margin changes), scenario metadata, grain markers, validation/quality
  flags, and `N/A`-with-reason for unlicensed metrics.

Out of scope (see §10): everything else, including any change to the frozen
uniform-replacement implementation.

## 3. Input contract

- **Single scalar input, one form per scenario.** A required, visible CLI
  argument, e.g. `--increase-pp <value>`, holding the uniform
  percentage-point increment. Exactly one input form per scenario run; the
  chosen form is recorded on every output. No per-line, per-segment, or
  second parameter in this slice.
- **Decimal scale (decision 2).** The increase is supplied as a **decimal
  fraction of 1**, on the same scale as the frozen `discount` field:
  `0.05` means +5 percentage points. Display-scale values (e.g. `5` for
  “5%”) are **not** accepted and fail the range check below — there is no
  percent-sign parsing and no 0–100 scale.
- **Zero permitted (decision 5).** `0.00` is valid. It is the identity
  sensitivity (`hypothetical = observed`, variances zero) and is retained as
  a pipeline-validation case. It runs the full validation and output path;
  it is not a bypass.
- **Negatives rejected (decision 6).** Any value `< 0` fails at argument
  parsing even if every resulting `d'` would remain within bounds, because a
  negative increment is the separately gated **discount decrease** type and
  must not enter under an increase identifier.
- **Canonical precision.** Approved instance values are stated to two
  decimals (e.g. `0.05`). The full float is recorded in metadata; the
  scenario identifier and filenames carry the two-decimal rendering (see §7).

## 4. Calculation contract

Frozen Phase 1A definitions restated, quantity `q` held constant throughout;
`d` = observed discount, `Δ` = stated increase, `d'` = hypothetical discount:

```text
gross(line)        = sales / (1 - d)              [d in [0, 1), proven]
d'(line)           = d + Δ
hypo_net(line)     = gross * (1 - d')
                     = sales * (1 - d') / (1 - d)  (dual form, reconciled)
hypo_disc_amt      = gross - hypo_net
hypo_cogs(line)    = hypo_net * modeled_cogs_pct / 100   (frozen line pct)
hypo_cts(order)    = authoritative order_freight + 0 + 0 (return/support OFF)
hypo_contrib(order)= SUM(hypo_net) - SUM(hypo_cogs) - order_freight
band(order)        = baseline observed order-WAD band (frozen assign_band)
variance           = hypothetical - baseline       (reconciled both ways)
margin change      = hypo_margin_pp - base_margin_pp   (SUM/SUM; pp units)
```

Source: frozen line fact `data/processed/fact_margin_map_phase2.csv`
(9,994 lines) for `sales`, `quantity`, `discount`, `net_revenue`,
`modeled_cogs_pct`, `freight_cost_observed`, flags, and OFF markers;
authoritative `order_freight`, `order_cost_to_serve`,
`order_contribution_*` joined from `data/processed/order_margin_map_phase2.csv`
(5,009 orders), never recomputed. `source_profit_quarantined` is never
loaded. Gross is a derived reference, never an observed list price.

## 5. Bounds and failure behavior

- **Permitted range.** Every resulting `d'` must satisfy
  `0.00 ≤ d' ≤ 0.80` (Gates 2/7). The stated `Δ` must satisfy
  `0.00 ≤ Δ ≤ 0.80`; anything else fails at parsing.
- **Fail-loud, whole-run rejection (decisions 4, 10).** If **any** computed
  `d'` falls below 0.00 or above 0.80 — including near-bound overflow such as
  `Δ = 0.05` on a `d = 0.80` line — the scenario definition is invalid. The
  run **fails validation loudly and produces no output treated as valid**:
  no CSV, no partial-subset execution, no clipping, no extrapolation, no
  silent correction, and no dropping of offending lines to make the scenario
  pass. Dropping offending lines is silent exclusion and is forbidden
  (contract §5; Gate 7).
- **Diagnostic, not partial output.** A failed run may — and should — report
  the offending record identifiers and counts (affected `row_id`s, per-band
  counts, violating values, maximum `d'`) in its failure diagnostic so the
  input can be corrected and resubmitted. The diagnostic accompanies
  rejection; it never converts an invalid scenario into a valid one.
- **Count preservation.** A valid run accounts for all 9,994 lines and 5,009
  orders in scope; output TOTAL reconciles to the frozen baseline
  (revenue 2,297,200.86; COGS 1,493,910.13; freight 238,173.79;
  contribution 565,116.9418) within the documented tolerance.

## 6. Rounding rules (decision 3)

- **Discounts:** observed discount reused via the frozen idiom
  (`discount_r = discount.round(6)`); `d' = discount_r + Δ` computed in full
  float then **rounded to 6 decimals** before the bound check and before any
  downstream use. Bound checks apply to the rounded value so binary-float
  residue (e.g. `0.8000000001`) cannot fail a mathematically in-bound case
  nor pass an out-of-bound one. Stored `hypothetical_discount` is the
  6-decimal value.
- **Currency:** no line-level cents rounding; hypotheticals, aggregations,
  and variances use full double precision. Reconciliation tolerances follow
  the first slice: dual-form gaps ≤ 1e-6; variance gaps ≤ 1e-9; freight
  variance exactly 0; source-total reconciliation tolerance 0.05.
- **Margins:** SUM/SUM only; averaging percentages forbidden; margin changes
  in percentage points. Band assignment uses the frozen `assign_band`
  boundaries unchanged. Zero-revenue hypothetical margin is NULL/blank, never
  0-filled.

## 7. Output contract

- **Schema.** Same six blocks as the first slice (contract §4): (a) scenario
  metadata; (b) baseline metrics; (c) hypothetical metrics (`hypothetical_*`);
  (d) variances with pp margin changes; (e) grain markers (`basis = ORDER`,
  baseline `band`); (f) validation/quality flags including `low_sample_flag`
  (30-line / 10-order provisional thresholds), `ambiguity_note`, and
  `N/A`-with-reason for unlicensed metrics (`fixed_unit_cost_view`,
  `demand_response_view`). Unsupported metrics are marked unavailable with a
  reason — never estimated, never silently omitted.
- **Scenario naming (decision 7).** `scenario_type = discount_increase`
  (distinct from `uniform_replacement`); `input_form = increase_pp`;
  `scenario_id = discount_increase_pp_<Δ:.2f>` (e.g.
  `discount_increase_pp_0.05`); `stated_increase_pp` carries the full input
  float; `scope = all_valid_lines`; standing
  `HYPOTHETICAL_ARITHMETIC_SENSITIVITY_NOT_A_FORECAST`; assumption labels
  `CONSTANT_OBSERVED_QUANTITY`, `FROZEN_MODELED_COGS_PCT`,
  `OBSERVED_PASSTHROUGH`, `OFF` — same vocabulary as the first slice.
- **Filenames (decision 8).** New ignored artifacts only, never overwriting
  frozen files:
  `data/processed/phase4b_scenario_increase_<Δ:.2f>.csv` (e.g.
  `phase4b_scenario_increase_0.05.csv`) plus
  `data/processed/phase4b_scenario_increase_<Δ:.2f>_quality.json`.
  The suffixed quality filename preserves the frozen first-slice
  `phase4b_scenario_quality.json` byte-identical. Rate and increase
  namespaces do not collide.

## 8. Validation additions (decision 10)

The fifteen Gate 9 checks from the contract (§6) apply unchanged, plus the
following increase-specific fail-loud gates (dependency order at parse/load):

1. `increase-exists` — `--increase-pp` present and numeric; missing/NULL/
   non-numeric aborts before any I/O.
2. `increase-sign` — `Δ ≥ 0`; negatives rejected as wrong slice type.
3. `increase-bounds` — `Δ ≤ 0.80`; display-scale values (e.g. `5`) fail here
   with a scale-hint diagnostic.
4. `discount-bounds-per-line` — every rounded `d'` in [0.00, 0.80] with §5
   whole-run failure semantics; offending `row_id`s, counts, and maximum
   `d'` reported diagnostically.
5. `no-silent-exclusion` — scoped line/order counts equal frozen totals
   (9,994 / 5,009); any dropped or clipped line fails.
6. `hypo-revenue-dual-additive` — `hypo_net` reconciled between
   `gross * (1 - d')` and `sales * (1 - d') / (1 - d)` (gap ≤ 1e-6).
7. `metadata-increase` — `scenario_type`, `input_form`, `scenario_id`,
   `stated_increase_pp`, scope, and standing present and consistent with the
   filename; any `uniform_replacement` residue fails.

All other checks — quarantine exclusion, constant quantity (bit-identical,
total 37,873), COGS-percentage identity and rollup, freight passthrough with
ambiguous-pair NULL/flag preservation (2 lines, `US-2014-150119`; 25.05 via
order aggregation only), return/support OFF, baseline and variance
reconciliation, pp margins, N/A marking, claim-exclusion wording, frozen-hash
integrity — are inherited unchanged. Any failure identifies the issue and
blocks valid status.

## 9. Integration approach (decision 9)

**New standalone module; reuse by copy, never by modification (decision 9).**
Example path: `src/data/build_phase4b_increase_scenarios.py` exposing
`--increase-pp` (never `--rate`). Frozen scripts expose no library API, so
proven idioms — gross reconstruction, WAD dual-form check, `assign_band`
boundaries, `fail()` + `sha256()` + quality-JSON pattern, authoritative
order join — are copied verbatim, never imported, edited, or executed from
the frozen `src/data/` set. Off-limits per contract §8: editing or importing
the uniform-replacement script, writing to any frozen filename, renaming or
moving frozen files, flipping any `*_scenario_enabled` flag in place,
deriving COGS percentages from currency summaries, allocating freight below
order grain, or loading the quarantined Profit column. Frozen inputs are
hashed before and after every run; any drift aborts.

## 10. Deferred scope (decision 12)

Explicitly not in this slice and not representable as available: discount
decrease (separate future slice under its own identifier); relative-change
input form; any further uniform-replacement rate beyond the frozen 0.10
instance; Segment × Discount Band reporting of the increase scenario
(licensed by Gate 1 but deferred for this slice, which reports Order × Band
only); customer-level reporting; segment-, category-, and product-specific
designs; any non-constant quantity form or response parameter; forecasting,
causal, demand-prediction, or optimization claims; fixed-unit-cost comparator
activation; return/support rate layers; dashboards and Power BI; float
tolerances beyond the inherited values; exact column-layout refinements
beyond the contract blocks.

## 11. Reproducibility requirements (decision 11)

Identical frozen inputs plus identical stated `Δ` reproduce byte-identical
CSV and quality-JSON artifacts across consecutive runs (SHA-256-compared, as
in the first slice). No timestamps, no randomness; sorted band keys
(B0–B5, TOTAL); versioned constants; input hashes recorded in the quality
report; frozen inputs byte-identical before and after. Reproduction command
(from the project root, on frozen inputs):

```text
python src/data/build_phase4b_increase_scenarios.py --increase-pp 0.05
```

Expected: Order × Band rows + TOTAL → the §7 CSV plus its quality JSON, all
checks PASS, byte-identical reruns. Any `Δ` whose `d'` breaches [0.00, 0.80]
fails loudly with no valid output.

## 12. Approval status

**APPROVED FOR IMPLEMENTATION — NOT YET FROZEN.** This document specifies the increase
slice; it authorizes the build of this slice only, selects no instance value beyond the
illustrative `0.05` examples above, and changes no frozen artifact. The slice itself
is not yet frozen. Any departure — broader grains, wider bounds, response assumptions,
comparator activation, new scenario types, or silent-exclusion handling —
requires a new documented approval before it is built.
