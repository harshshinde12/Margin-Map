# Phase 4A Decision Log — Pricing Scenario Architecture

> Append-only within Phase 4A. New decisions take the next `D4A-NN` number
> and reference what they supersede or extend. Phase 1 decisions
> (`docs/DECISION_LOG.md`, frozen), Phase 2A decisions
> (`docs/COST_TO_SERVE_DECISION_LOG.md`, frozen), Phase 3A decisions
> (`docs/PHASE_3A_DECISION_LOG.md`, frozen), and Phase 3B decisions
> (`docs/PHASE_3B_DECISION_LOG.md`, frozen) are cited, never edited. No
> scenario values, elasticity coefficients, quantity-response assumptions,
> or costing methods are selected anywhere in this log.

## D4A-01 — Scenario purpose restricted to arithmetic sensitivity and labeled illustration

- **Decision:** permit arithmetic price/discount sensitivity and
  illustrative financial simulation; declare demand-response modeling,
  causal pricing evaluation, and optimization outside the current evidence
  base (architecture §1).
- **Alternatives:** allowing "directional demand commentary" alongside
  arithmetic (rejected: commentary without an identified response is causal
  language wearing descriptive clothing).
- **Rationale:** scenarios quantify exposure (revenue/profit sitting under
  each discount configuration), never response; the boundary keeps every
  later section honest.
- **Unresolved:** none at definition level.

## D4A-02 — Line-level application with order-grain aggregation and reporting

- **Decision:** hypothetical discounts specified per line (where the source
  field lives), aggregated strictly bottom-up; authoritative contribution
  reporting at order grain and above only (architecture §2).
- **Alternatives:** order-level discount specification without a line rule
  (rejected: invents line mixes the data does not contain); top-down
  allocation of scenario effects (rejected: breaks pool reconciliation
  discipline from Phase 2A).
- **Rationale:** the only grain where discount mechanics, revenue, modeled
  COGS, observed freight, and contribution are jointly complete is the
  order built from its lines — the Phase 2B.1 authority result, extended.
- **Unresolved:** none for the mechanism; reporting scope gated separately
  (D4A-03).

## D4A-03 — Initial reporting scope: order and segment only

- **Decision:** initial Phase 4B reporting covers order × discount-band and
  Segment × discount-band on the ORDER basis. Customer-level scenario
  reporting — structurally valid bottom-up — is deferred to a later
  decision; category/sub-category scenario views, if built, are gross-only
  companions; product-level scenario contribution is not licensed.
- **Alternatives:** including customer TOTAL scenarios initially (rejected
  for now: customer × band cells are fully flagged in Phase 3B and scenario
  detail there would stack assumption on thin evidence).
- **Rationale:** narrowest scope that still answers the exposure question
  with authoritative numbers; broader grains unlock only after the core
  machinery is validated.
- **Unresolved:** customer-level gating decision (owner approval, §12.1).

## D4A-04 — Discount input design: pp-change primary, range capped at observed support

- **Decision:** percentage-point change as the primary specification form
  (relative change permitted as a stated alternative; replacement as a
  limiting case); one form per scenario, reconciled to a stated `d'` per
  line. Valid hypothetical range [0, 0.80] — capped at the observed maximum
  with no extrapolation machinery; `d' ≥ 1`, negative, or NULL aborts;
  over-bound pp-increases excluded per line with counts (never clipped);
  out-of-scope lines pass through at observed values (architecture §3).
- **Alternatives:** allowing hypotheticals above 0.80 with warnings
  (rejected at this gate: extrapolation beyond all recorded pricing
  behaviour adds risk without a business case on record); silent clipping
  to bounds (rejected: fabricates analyst intent).
- **Rationale:** pp-change is unambiguous across the discrete mass points
  and auditable against band boundaries; the cap keeps every scenario
  inside observed pricing support.
- **Unresolved:** final business values for any scenario instance (pending
  approval; none chosen here).

## D4A-05 — Constant-quantity arithmetic as the only active quantity assumption

- **Decision:** hypothetical revenue computed holding quantity fixed
  (`hypothetical_net = gross × (1 − d')`), labeled a constant-quantity
  arithmetic scenario — never a forecast. The five quantity-response
  approaches are surveyed with none selected; statistical/elasticity
  estimation stays blocked on the Phase 3A §7 grounds; any future
  non-constant assumption must clear the §5.2 evidence bar (entered/sourced
  with provenance, unsupported flag, uncertainty bands, constant-quantity
  reference reported first).
- **Alternatives:** embedding a provisional response default so scenarios
  "move quantities" (rejected: any default would be invention presented as
  knowledge — the D3A-10 rationale, reaffirmed).
- **Rationale:** the arithmetic is closed-form and auditable; everything
  beyond it is assumption requiring its own evidence review.
- **Unresolved:** form and bounds of any future quantity assumption (owner
  evidence review, §12.3).

## D4A-06 — COGS: modeled-rule default plus a gated comparator structure

- **Decision:** default scenario COGS recomputed as hypothetical net ×
  frozen modeled COGS % with the margin-constancy consequence stated on
  every output; benchmark model never presented as fixed unit cost. A
  fixed-unit-cost comparator is architected as structure only — activation
  conditions, beside-not-instead reporting, versioning, and the explicit
  disqualification of `implied_modeled_cogs_per_unit` — with no method
  selected and nothing built. Actual-cost arrival follows the Phase 1C-2
  input contract as a data path, not a build item (architecture §6).
- **Alternatives:** deferring all fixed-unit-cost discussion (rejected:
  the comparator question would otherwise return undecided at every future
  gate; specifying conditions now bounds it safely); selecting a
  fixed-unit-cost method now (rejected: no per-unit source exists).
- **Rationale:** prevents the revenue-based model from silently posing as
  unit economics while keeping the economically natural comparator
  available under strict conditions.
- **Unresolved:** comparator activation (requires an approved per-unit
  source — none exists); §12.4 confirmation.

## D4A-07 — Cost-to-serve passthrough with OFF defaults preserved

- **Decision:** observed freight passes through unchanged; ambiguous pair
  stays NULL/flagged at line grain under all scenarios (25.05 via order
  aggregation only); return status remains filter-only with UNKNOWN never
  defaulted; return/support scenario costs stay OFF (zero = excluded) and
  may enter only as separately approved labeled rate layers from the
  permitted families (R-B/S-B/S-C at most; R-C/S-D remain rejected); no
  invented costs anywhere (architecture §7).
- **Alternatives:** re-specifying freight handling per scenario (rejected:
  scenarios re-price revenue, not movement — no rule exists for the latter).
- **Rationale:** inherits the exact Phase 2 ambiguity and scenario
  discipline that keeps baseline totals reconcilable; extends D2A-04/05/11
  into the hypothetical context.
- **Unresolved:** §12.5 confirmation; any future return/support rate layer
  needs its own sourcing decision.

## D4A-08 — Three-level contribution claim separation

- **Decision:** scenario profit reported solely as arithmetic scenario
  contribution (frozen waterfall on hypothetical inputs, dual-reconciled,
  SUM/SUM); forecast contribution and causal business impact explicitly
  forbidden as claims (architecture §8).
- **Alternatives:** none (restatement of the purpose boundary at the profit
  layer, not a new choice).
- **Rationale:** the waterfall arithmetic is valid under assumptions; what
  *will be* or *would be caused* is not knowable from this evidence.
- **Unresolved:** none.

## D4A-09 — Six-type scenario taxonomy without values or activation

- **Decision:** adopt the controlled taxonomy (discount increase; discount
  decrease; uniform replacement; segment-, category-, product-specific)
  as structures only — scope plus input form per type, cross-type
  combinations as scoped instances, one identifier with full assumption
  record per instance. No scenario activated, no values assigned
  (architecture §9).
- **Alternatives:** a free-form scenario builder (rejected: unbounded scope
  defeats validation and labeling discipline).
- **Rationale:** bounded taxonomy keeps every future instance validatable
  against the same guardrails and wording rules.
- **Unresolved:** taxonomy adoption/narrowing/extension and all instance
  values (§12.6).

## D4A-10 — Guardrails, labeling, and wording locked as build requirements

- **Decision:** the §10 eleven-point guardrail set (bounds, non-negativity,
  zero-revenue NULLs, observed preservation, baseline reconciliation,
  quarantine exclusion, no invented costs, assumption-layer labels,
  determinism, frozen protection) and the §11 wording regime (hypothetical
  naming, tier labeling, permitted vs prohibited phrasing with on-visual
  caveats) are specified as fail-loud requirements for any future build.
- **Alternatives:** guidelines instead of fail-loud gates (rejected: Phase
  1–3 culture is machine-enforced validation, and scenarios are the
  highest invention-risk surface yet).
- **Rationale:** makes over-claiming and silent assumption structurally
  difficult rather than merely discouraged.
- **Unresolved:** tolerances from float behaviour (set at build);
  dashboard display conventions (deferred; §12.10).

## Questions requiring owner approval (Phase 4B gates, architecture §12)

1. Scenario grain confirmation (incl. separately gated customer level).
2. Discount input design confirmation (forms retained/dropped; bound).
3. Quantity treatment (constant-quantity initial; any non-constant form).
4. COGS treatment (default rule; comparator conditions).
5. Cost-to-serve treatment (passthrough; OFF defaults).
6. Scenario types (adopt/narrow/extend; no instance values yet).
7. Discount bounds confirmation (incl. no-clip rule).
8. Output schema approval.
9. Validation thresholds adoption.
10. Dashboard display rules (deferred; causation/prediction ban recorded).
