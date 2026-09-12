# Phase 3A Decision Log — Discount, Elasticity-lite, and Pricing Scenario Architecture

> Append-only within Phase 3A. New decisions take the next `D3A-NN` number
> and reference what they supersede or extend. Phase 1 decisions
> (`docs/DECISION_LOG.md`, frozen) and Phase 2A decisions
> (`docs/COST_TO_SERVE_DECISION_LOG.md`, frozen) are cited, never edited.
> No numerical rates, elasticity coefficients, or scenario assumptions are
> selected anywhere in this log — method families and structures are
> specified for future validation only.

## D3A-01 — Phase 1/Phase 2 foundations adopted unchanged

- **Decision:** Phase 3A reuses all frozen definitions verbatim
  (`FINANCIAL_MODEL.md` waterfall; `KPI_DICTIONARY.md` lineage and
  denominators; Phase 1C-3 revenue-based modeled COGS; Phase 2B order-level
  contribution authority; Phase 2C gross-vs-contribution grain discipline).
  Nothing is redefined.
- **Alternatives:** restating formulas with Phase 3 prefixes (rejected:
  gratuitous relabeling would break traceability to the frozen waterfall).
- **Rationale:** a single auditable financial logic across phases; Phase 3A
  adds measurement and scenario structure, not new profit definitions.
- **Unresolved:** none.

## D3A-02 — Discount measurement set locked to eight canonical measures

- **Decision:** Discount Rate, Gross Revenue, Net Revenue, Discount Amount,
  Discount Band, Weighted Average Discount, Discount Amount as % of Gross
  Revenue, and Revenue realization rate, with the formulas, denominators,
  weights, and guards specified in the architecture (§3.1).
- **Alternatives:** adding a standalone "Discount Leakage" KPI alongside
  Discount Amount (rejected: identical arithmetic under a different framing
  — both retained as labels, never summed or double-presented).
- **Rationale:** closes the denominator ambiguity before any analysis
  (WAD on gross revenue; margins on net revenue; realization as complement).
- **Unresolved:** none at definition level; implementation thresholds
  deferred to D3A-10 questions.

## D3A-03 — Discount Amount is revenue reduction, not profit loss

- **Decision:** Discount Amount is documented as revenue forgone relative to
  reconstructed Gross Revenue; any profit statement must pass through the
  contribution waterfall with the applicable COGS and serve-cost layers
  stated (architecture §3.2).
- **Alternatives:** treating Discount Amount as margin erosion directly
  (rejected: ignores the revenue-scaled COGS construction and the
  discount-independent freight layer, and would misstate profit effects).
- **Rationale:** preserves the Phase 1A framing and prevents the most likely
  misreading of discount tables.
- **Unresolved:** none.

## D3A-04 — Fixed value-based bands as the primary structure; quantiles rejected as primary

- **Decision:** discount bands are fixed, value-based intervals. A
  quantile-based banding is rejected as the primary structure because the
  discount field is discrete and policy-like (12 mass points; 0.00 and 0.20
  jointly 84.60% of lines) and quantile cuts would split identical discount
  values and merge economically distinct levels. A quantile cut may serve at
  most as an owner-approved sensitivity comparator.
- **Alternatives considered:** quantile-primary banding (rejected per above);
  continuous-discount regression without banding (rejected: the discreteness
  and the sparse tail make banded description the auditable first step;
  model-based approaches, if ever proposed, require separate approval).
- **Rationale:** bands must preserve the policy meaning the analysis exists
  to reveal and keep every line's assignment reproducible from a constant.
- **Unresolved:** whether the quantile comparator is built in Phase 3B
  (owner approval required).

## D3A-05 — Zero-discount group preserved; six-band candidate informed by the observed distribution

- **Decision:** the zero-discount group (4,798 lines at d = 0) is preserved
  exactly as its own reference band. The remaining range is partitioned into
  five fixed bands (B1–B5) pooling value-nearest sparse values so that no
  band rests on fewer than ~140 lines at overall grain, covering the full
  observed [0, 0.8] with no gaps, overlaps, or split discrete values
  (candidate table in architecture §4.3).
- **Alternatives considered:** one band per discrete value, i.e. 12 bands
  (rejected: excessive segmentation; four values have ≤ 94 lines and would
  produce uninterpretable band × dimension cells); a coarse
  zero/low/high split (rejected: hides the deep-discount tail at 0.60–0.80
  where 856 lines sit).
- **Rationale:** balances transparency (pooling disclosed value-by-value)
  against interpretability (six bands including the zero reference).
- **Evidence:** read-only inspection of `discount` in the frozen line fact
  (12 values with counts recorded in architecture §4.1); no output files
  created, no frozen files changed.
- **Unresolved:** final adoption of the candidate requires Phase 3B band
  validation (coverage, uniqueness, value integrity, stability) and owner
  approval; amended boundaries remain possible at that gate.

## D3A-06 — Sparse groups disclosed and flagged, never hidden or suppressed

- **Decision:** every band and every band × dimension cell reports its line
  count, order count, and constituent discount values; cells below the
  approved minimum-sample threshold carry `low_sample_flag = TRUE` and are
  described as arithmetic only. Thin cells remain visible with flags rather
  than being suppressed or silently merged. Single-order products retain the
  Phase 2C `low_volume_flag` discipline in all discount cuts.
- **Alternatives:** suppressing small cells (rejected: hides where evidence
  is thin); silently merging small cells post hoc (rejected: irreproducible
  and unauditable).
- **Rationale:** extends the Phase 1/Phase 2 fail-loud and labeling culture
  to the discount analysis, where the sparse tail (0.10/0.15/0.32/0.45) and
  small sub-categories would otherwise invite over-interpretation.
- **Unresolved:** threshold values (set in Phase 3B with owner approval).

## D3A-07 — Grain authority: order-level contribution where licensed, gross-profit-only elsewhere

- **Decision:** overall, order-level, and customer-level analyses use
  authoritative order-level contribution (bottom-up from
  `order_margin_map_phase2.csv`); line-level band detail is a partial view
  reported with the stated reconciliation gap; Segment-level contribution
  only for the attributable subset under a single stated mixed-order rule;
  Category, Sub-Category, Product, and Customer × Sub-Category analyses are
  gross-profit-only with freight/contribution explicitly NULL and reasoned
  (architecture §6.1). Extends D2A-13 and the Phase 2C grain-honesty
  appendix.
- **Alternatives:** allocating the 25.05 ambiguous freight to product or
  sub-category views to enable "full" contribution everywhere (rejected:
  no attribution rule exists; any split would be invention, forbidden by
  D2A-11/D2A-13).
- **Rationale:** keeps every contribution number traceable to complete
  order economics and prevents product/sub-category contribution figures
  that the data cannot support.
- **Unresolved:** the order-band assignment rule where order-level banding
  is used (one rule specified once in Phase 3B; owner approval required);
  any future product-attribution rule (separate decision, not in Phase 3A).

## D3A-08 — Ambiguous freight and return-status controls carried into discount analysis

- **Decision:** lines 3406/3407 remain NULL-freight, flagged, and unassigned
  in all Phase 3B discount work; the 25.05 pair total enters only via the
  order fact with reconciliation stated. Return status is a filter/cohort
  flag only (order-level meaning; UNKNOWN retained, never defaulted); return
  and support scenario layers remain OFF in every baseline discount view.
- **Alternatives:** none (restatement of binding Phase 2 controls in the
  discount context, not a new choice).
- **Rationale:** the discount analysis inherits the exact ambiguity and
  scenario discipline that keeps Phase 2 totals reconcilable.
- **Unresolved:** none.

## D3A-09 — Elasticity-lite is observational and descriptive; causal estimation refused

- **Decision:** Phase 3A specifies an elasticity-lite design limited to
  banded quantity-per-line, quantity-per-order, order-frequency, and
  within-cut Segment/Category/Sub-Category comparisons with sample
  thresholds, plus descriptive response indicators (e.g. band quantity
  index vs a reference band; rank association with sample size) that are
  labeled as descriptive indicators, never as elasticity. Causal
  price-elasticity estimation is explicitly out of scope: no experiments,
  no reliable pre-discount unit-price history, and multiple unrecorded
  confounders are documented; any band–quantity association must not be
  worded as proof that discounts caused quantity changes. Structural demand
  regressions reported as elasticities are forbidden.
- **Alternatives considered:** estimating log-log or similar demand
  regressions on the observational data (rejected: identification conditions
  absent; would present confounded association as a demand parameter);
  pooling across segments/categories/time without within-cut breakdowns
  (rejected: hides composition effects).
- **Rationale:** the dataset supports honest description of co-occurrence,
  not identification of a causal discount effect; the design makes
  over-claiming structurally difficult.
- **Unresolved:** none in Phase 3A (no coefficients exist to approve).

## D3A-10 — Pricing scenario framework designed but kept OFF; no quantity-response values selected

- **Decision:** the What-if framework (discount-pp change, gross-price rule,
  assumed quantity response, scope selector, line-level application with
  bottom-up aggregation, baseline-vs-scenario comparison) is specified with
  scenarios defaulting to OFF, baselines always reported first and
  separately, and every scenario output carrying the four labeled layers
  (observed baseline; analyst-entered assumptions with author/date/
  rationale; scenario outputs; unsupported-assumption flag). No numerical
  quantity-response assumption is selected in Phase 3A.
- **Alternatives:** embedding a default quantity-response assumption so
  scenarios "run out of the box" (rejected: any such default would be
  invention presented as knowledge).
- **Rationale:** scenarios are conditional illustrations built on entered
  assumptions, not forecasts; the OFF default and layering keep the evidence
  distinguishable from the assumption.
- **Unresolved:** permitted form and bounds of quantity-response assumptions;
  threshold and comparator choices — all deferred to Phase 3B proposal with
  owner approval.

## D3A-11 — Scenario COGS defaults to benchmark recomputation; fixed-unit-cost path not permitted as base

- **Decision:** scenario COGS defaults to `scenario Net Revenue × frozen
  modeled COGS %`, with the mechanical consequence (gross margin %
  constant by construction; only currency moves) stated on every output
  using this rule. The current benchmark model is never presented as a true
  fixed unit cost. A fixed-unit-cost scenario alternative is not permitted
  as a base scenario until an observed or approved per-unit cost source with
  methodology, provenance, and validation exists (`implied_modeled_cogs_per_unit`
  is explicitly disqualified for this role because it varies with
  price/discount by construction).
- **Alternatives considered:** holding implied per-unit COGS constant in
  scenarios (rejected: circular — the implied value is derived from the
  revenue it would then pretend to explain independently of revenue).
- **Rationale:** prevents the revenue-based modeled COGS from silently
  posing as physical unit economics in pricing analysis.
- **Unresolved:** whether a fixed-unit-cost comparator may be developed once
  a cost source exists (separate future approval, not granted in Phase 3A).

## D3A-12 — Phase 3A creates no outputs and changes no frozen artifacts

- **Decision:** Phase 3A delivers three design documents only (architecture,
  this log, validation). No scripts are written or modified, no analytical
  outputs are created, no scenarios are activated, and no Phase 1/Phase 2
  data, script, or frozen document is modified, regenerated, renamed, or
  overwritten.
- **Rationale:** architecture-before-implementation sequencing with hash
  protection on the frozen set.
- **Unresolved:** none.

## Questions requiring owner approval (before Phase 3B implementation)

1. Adoption of the candidate six-band structure (§4.3 / D3A-05) or an
   amended alternative.
2. Minimum sample-size thresholds for line counts and order counts (D3A-06).
3. The single order-band assignment rule where order-level banding is used
   (D3A-07).
4. Whether a quantile banding comparator is built (D3A-04).
5. Permitted form, bounds, and sensitivity treatment of scenario
   quantity-response assumptions (D3A-10).
6. Whether any fixed-unit-cost COGS comparator may be developed once a cost
   source exists (D3A-11) — not approved in Phase 3A.
7. Display and labeling conventions for band, elasticity-lite, and scenario
   outputs in downstream tables and visuals (structure specified; visual
   conventions deferred).
