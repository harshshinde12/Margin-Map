# Phase 3A Architecture Validation (design checks, no estimates)

> Method: static verification of the Phase 3A design against frozen Phase 1
> and Phase 2 contracts, the inspected file schemas, and the Phase 3A
> mandate (architecture only; no implementation, no outputs, no scenarios,
> no elasticity coefficients, no frozen-artifact changes, no Git
> operations). **No calculations were implemented and no analytical outputs
> were generated** — there is nothing to reconcile numerically, so every
> check below is structural (definitions, lineage, grain, controls, and
> evidence that the discount distribution was inspected before banding).
> Each check cites the architecture section that implements the requirement.

## Results

- [x] **Frozen foundations reused verbatim.** Net Revenue = Sales;
  Gross Revenue = Sales / (1 − Discount) with the Discount = 1 guard;
  Discount Amount = Gross − Net; revenue-based modeled COGS; Gross and
  Contribution waterfall with NULL-on-zero-revenue guards; quarantined
  source Profit excluded from all computations (architecture §2.1).
  No definition redefined; no Phase 1 document altered.
- [x] **Contribution baseline and ambiguity preserved.** Order-level
  authority (`order_margin_map_phase2.csv`, 5,009 orders; 565,116.9418 /
  24.6002% scenarios-OFF); the 21.59/3.46 pair remains NULL and flagged at
  line grain with the 25.05 pair total (26.55 at full-order level) entering
  only via the order fact; no line-level freight fabricated; return status
  confined to filter/cohort use with UNKNOWN retained; return/support
  scenarios OFF (architecture §§2.2, 6.2–6.3; decisions D3A-07, D3A-08).
- [x] **Schemas cited as inspected, not assumed.** The 35-column line-COGS
  schema, the 49-column Phase 2 line schema (14 appended columns named),
  and the 10-column order schema are recorded from direct inspection, and
  the design explicitly derives order-level discount/quantity/dimensional
  attributes by rollup because the order fact does not carry them
  (architecture §2.3). No absent column is assumed present.
- [x] **Discount measurement complete and guarded.** All eight required
  measures defined with formulas, denominators/weights, and guards; WAD on
  gross revenue with dual-form reconciliation; margins on net revenue with
  percentage-averaging forbidden; margin changes in percentage points;
  Gross/Discount Amount labeled derived; Discount Leakage double-count
  barred; Discount Amount documented as revenue reduction, not profit loss,
  with the COGS-construction and freight reasoning stated (architecture
  §3; decisions D3A-02, D3A-03).
- [x] **Band design informed by the actual distribution.** The discount
  field was inspected read-only (12 discrete values, range [0, 0.8], counts
  tabled; no Discount = 1 or NULL observed, guards nevertheless mandatory).
  The zero group is preserved exactly; six fixed value-based bands are
  proposed as candidates covering the full observed range with no gaps,
  overlaps, or split discrete values; sparse values pooled with disclosure;
  quantile-primary banding rejected with reasons and confined to an
  optional comparator; six-step band validation specified including
  coverage, uniqueness, value integrity, sparse disclosure, and stability
  (architecture §4; decisions D3A-04–D3A-06).
- [x] **No excessive segmentation; no hidden sparse groups.** Six bands
  total (12-per-value rejected; coarse 3-way rejected with reasons); every
  band reports constituent values and counts; band × dimension cells carry
  counts and `low_sample_flag` discipline and remain visible when thin
  (architecture §§4.3–4.4, 5.4; decision D3A-06).
- [x] **Impact analysis designed at the right grains with level-correct
  metrics.** Overall, Segment, Category, Sub-Category, Customer, and Product
  grains specified with units, dimensions, and profit basis; per-group
  measure set covers counts, quantity, gross/net/discount/WAD, licensed
  profit metrics, negative-profit visibility, and sample warnings;
  line/order/customer/product/sub-category metric discipline fixed
  (order WAD derived by rollup under one stated band rule; `return_status`
  and `freight_order_total` never summed; sub-category benchmark
  restatement caveat; customer multi-band duplication stated);
  minimum-sample thresholds with flag-not-suppress handling and
  `low_volume_flag` retention (architecture §5; decisions D3A-06, D3A-07).
- [x] **Contribution treatment explicit.** Authority map licenses
  order-level contribution for overall/order/customer cuts, treats
  line-level band detail as a stated partial with reconciliation gap,
  conditions Segment-level contribution on a single mixed-order rule, and
  holds Category/Sub-Category/Product/Customer × Sub-Category to
  gross-profit-only with NULL freight/contribution and reason
  (architecture §6.1; decision D3A-07).
- [x] **Elasticity-lite is non-causal by construction.** Standing
  non-causal declaration required on every output (confounders, no
  experiments, no reliable pre-discount unit-price history, association ≠
  causation, on-visual caveats); inputs limited to banded quantity,
  frequency, and within-cut comparisons with thresholds; any response
  formula labeled a descriptive indicator with mandatory companions;
  "elasticity" labeling, demand-parameter presentation, structural demand
  regressions as elasticities, and unstratified pooling all forbidden
  (architecture §7; decision D3A-09).
- [x] **Scenario framework designed and OFF.** Controls specified
  (discount-pp change, gross-price rule, assumed quantity response, scope
  selector, line-level application, baseline-vs-scenario comparison);
  nothing activated and no quantity-response values selected in Phase 3A;
  observed/assumption/output/unsupported layers separated with the
  unsupported flag; baselines first and separately; OFF default
  (architecture §§8.1–8.2, 8.4; decision D3A-10).
- [x] **Scenario COGS handled without misrepresenting the benchmark model.**
  Default rule recomputes `scenario Net × frozen modeled COGS %` with the
  constant-margin-% consequence stated on-output; benchmark model never
  presented as fixed unit cost; fixed-unit-cost alternative barred as base
  until an approved per-unit source exists, with implied per-unit COGS
  explicitly disqualified (architecture §8.3; decision D3A-11).
- [x] **Twelve-rule validation gate specified for Phase 3B.** Discount
  range, Gross guard, Net and Discount Amount reconciliations, weighting
  discipline, contribution authority with ambiguity preservation, scenario
  defaults, no invented coefficients, no causal claims, deterministic
  reruns in versioned configuration, and frozen-artifact hash protection
  with Profit quarantine (architecture §9).
- [x] **No invented numbers.** No elasticity coefficients, demand
  parameters, quantity-response rates, return/support rates, per-mode
  charges, or scenario values created anywhere in the three documents; the
  only figures quoted are read-only inspected evidence (discount value
  counts; schema shapes; frozen Phase 1/Phase 2 totals) cited to justify
  structure, never as new analytical outputs.
- [x] **No frozen artifacts changed; no implementation started.** No Phase 1
  or Phase 2 data file, script, or frozen document modified, regenerated,
  renamed, or overwritten; no new scripts, CSVs, JSON, tables, visuals, or
  scenario outputs created; no Git operations performed
  (decision D3A-12; handover §10).

## Design risks carried forward (not failures)

1. Band × dimension cells in the sparse tail and small sub-categories will
   breach sample thresholds by design — reviewers must read flagged cells
   as arithmetic, not evidence (D3A-06).
2. Line-grain band contribution sums will trail the authoritative
   order-level totals by the documented ambiguity gap — every line-grain
   view must carry its reconciliation (D3A-07, D3A-08).
3. Sub-category margins restate benchmark × mix by construction — readers
   must not mistake them for discoveries (§5.3).
4. Scenario profit deltas, when eventually built, will be conditional
   illustrations on unsupported quantity assumptions until a causal basis
   exists — the unsupported flag and sensitivity bands are load-bearing
   (D3A-10).
5. The revenue-based COGS construction bounds what pricing scenarios can
   honestly show about unit economics until a per-unit cost source is
   approved (D3A-11).

**ARCHITECTURE VALIDATED — PHASE 3A READY FOR REVIEW** (pending owner
decisions in `PHASE_3A_DECISION_LOG.md`, final section).
