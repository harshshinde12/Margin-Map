# Phase 4B Implementation Contract — Discount Scenario Analysis

> Standing: this contract binds the future Phase 4B build to the
> owner-approved gate decisions (`docs/PHASE_4B_DECISION_LOG.md`,
> `docs/PHASE_4B_APPROVAL_SUMMARY.md`, `docs/PHASE_4B_APPROVAL_VALIDATION.md`)
> and the frozen Phase 4A architecture. It resolves the invalid-discount
> handling rule and corrects the validation-gate numbering from the
> implementation-readiness inspection. Specification only — no
> implementation code, calculations, or outputs are authorized by this
> document beyond what the gates already permit.

## 1. Approved implementation scope

Line-level application of three scenario types only — discount increase,
discount decrease, uniform discount replacement — with bottom-up
aggregation to order level and initial reporting at Order × Discount Band
and Segment × Discount Band. Constant observed quantity; frozen
revenue-based modeled-COGS percentage; observed freight passthrough;
return/support OFF. Every figure is hypothetical arithmetic sensitivity
under stated assumptions — never a forecast, causal estimate, demand
statement, or pricing recommendation.

## 2. Frozen inputs and read-only dependencies

- `data/processed/fact_margin_map_phase2.csv` (49 cols, 9,994 lines):
  `sales`, `quantity`, `discount`, `net_revenue`, `modeled_cogs_pct`,
  `freight_cost_observed`, `freight_ambiguity_flag`, `freight_join_status`,
  `return_status`, OFF scenario flags. `source_profit_quarantined` is
  excluded from working frames (established `usecols` pattern).
- `data/processed/order_margin_map_phase2.csv` (10 cols, 5,009 orders):
  authoritative `order_freight`, `order_cost_to_serve`,
  `order_contribution_*` for joining (never recomputed) and baseline
  reconciliation (revenue 2,297,200.86; COGS 1,493,910.13; freight
  238,173.79; contribution 565,116.9418).
- Frozen formulas and proven idioms reused by copy (never by import or
  edit): gross reconstruction, WAD dual-form check, `assign_band`
  boundaries, fail-loud `fail()` + `sha256()` + quality-JSON pattern.
- `discount_order_summary.csv` may serve as a cross-check only — never as
  the COGS-percentage source (it carries currency, not the rate).

## 3. First implementation slice

One uniform replacement scenario at a single stated in-scope rate:
line-level `d'` → hypothetical net/COGS with freight passthrough →
bottom-up order aggregation → Order × Band output with the six schema
blocks, N/A reasons, full Gate 9 check suite, and quality JSON;
byte-determinism verified across two runs. Segment reporting, remaining
scenario types, and all displays follow only in later slices.

## 4. Required output structure

New ignored artifact(s) containing exactly: (a) scenario metadata
(identifier, type, input form and values, scope, assumption versions,
author/date); (b) baseline metrics; (c) hypothetical metrics prefixed
`hypothetical_*`; (d) variances with percentage-point margin changes;
(e) reporting-grain markers (`basis`, band, ORDERLens); (f) validation and
quality flags including `low_sample_flag`, `ambiguity_note`, and
N/A-with-reason marking for unlicensed metrics (notably
below-order-grain contribution). Unsupported metrics are marked
unavailable with a reason — never estimated, never silently omitted.

## 5. Invalid discount handling contract

The approved rule is restated without ambiguity. Three cases that must
never be conflated:

- **Valid scenario applied to an eligible scope.** Every computed `d'`
  lies within [0.00, 0.80]. Lines outside the scenario's declared scope
  pass through with `d' = d` (observed values preserved bit-identical).
  Passthrough is legitimate scope design, fully reconciled — it is not an
  exclusion of any kind.
- **Invalid scenario containing out-of-range values.** If any computed
  `d'` falls below 0.00 or above 0.80 (including near-bound overflows such
  as a pp-increase on a `d = 0.80` line), the scenario definition itself
  is invalid. The run **fails validation loudly and produces no output
  treated as valid**. There is no partial execution on a "valid subset":
  dropping offending lines to make a scenario pass is silent exclusion and
  is forbidden. Clipping, extrapolation, and silent correction are likewise
  forbidden.
- **Diagnostic reporting of affected records.** A failed run may — and
  should — report the offending record identifiers and counts (e.g.
  affected `row_id`s, per-band counts, the violating values) in its
  failure diagnostic so the input can be corrected and resubmitted. This
  diagnostic accompanies rejection; it never converts an invalid scenario
  into a valid one.

This supersedes the readiness report's "counted per-line bound
exclusions" phrasing: invalid records are never described as ordinary
exclusions from a valid scenario.

## 6. Mandatory validation contract

The build enforces the fifteen Gate 9 checks fail-loud, in dependency
order: (1) input existence and frozen hashes before/after; (2) discount
bounds on every `d'` with §5 failure semantics; (3) quarantine exclusion;
(4) constant observed quantity (bit-identical reuse asserted);
(5) hypothetical revenue formula with dual-form reconciliation;
(6) frozen modeled-COGS percentage with SUM/SUM margins;
(7) freight passthrough totals; (8) ambiguous-pair NULL/flag preservation
with order-total reconciliation; (9) return/support OFF assertions;
(10) baseline reconciliation to the Phase 2 facts within documented
tolerance; (11) variance arithmetic reconciliation both ways;
(12) percentage-point margin changes; (13) unsupported-metric N/A marking;
(14) metadata/lineage completeness and claim-exclusion wording;
(15) byte-identical determinism across reruns. Any failure identifies the
issue and blocks the output from valid status.

## 7. Explicitly deferred scope

Customer-level scenario reporting; segment-, category-, and
product-specific scenario designs; any non-constant quantity form or
response parameter; fixed-unit-cost comparator activation; all scenario
instance values; float tolerances (set at build); exact column layout
details; dashboard conventions beyond the binding Gate 10 constraints.
Deferred items must not be implemented, partially supported, or
represented as available.

## 8. Integration restrictions

New standalone module only (frozen scripts expose no library API).
Off-limits: editing, importing logic from, or executing any of the nine
frozen `src/data/` scripts; writing to any frozen filename; renaming or
moving frozen files; flipping any `*_scenario_enabled` flag in place;
deriving COGS percentages from currency summaries; allocating freight
below order grain; reading the quarantined Profit column into any working
frame. Frozen inputs are hashed before and after every run; any drift
aborts.

## 9. Gate-numbering correction

The readiness report's validation-matrix heading "Gate 19 requirement" is
a numbering error. The approved structure contains ten gates (Gate 1–10);
the mandatory validation checks are **Gate 9**. All references in this
contract use the corrected numbering, and the fifteen checks in §6 are the
Gate 9 set from the approved Gate 9 decision. No eleventh-through-nineteenth
gate exists.

## 10. Implementation readiness decision

**READY, CONDITIONAL.** The build may proceed to the §3 first slice only:
all inputs, formulas, patterns, and checks it needs already exist in
frozen, proven form; the two open specification points are closed by §§5
and 9 of this contract; residual risks (absent test framework, new
config/metadata schema, new-module authorship) are process risks owned by
the build's own review, not blockers. Any departure from §§1–8 — broader
grains, wider bounds, response assumptions, comparator activation, new
scenario types — requires a new documented approval before it is built.
