# Phase 4B Decision Log — Approved Pricing-Scenario Gate Decisions

> Standing: this log records the project-owner approval of the ten Phase 4B
> approval gates defined in Phase 4A (`docs/PHASE_4A_PRICING_SCENARIO_
> ARCHITECTURE.md` §12, `docs/PHASE_4A_DECISION_LOG.md` questions,
> `docs/PHASE_4A_FREEZE.md` §7). **All ten gates were approved by the
> project owner on 2026-09-13.** This approval authorizes the next
> design/implementation stage only after this documentation is reviewed and
> frozen. **Phase 4B has not been implemented** — no scenario calculations,
> scripts, outputs, or dashboards exist under this approval.
>
> Append-only within Phase 4B gate approval. Frozen Phase 1–4A records are
> cited, never edited. No scenario instance values, elasticity
> coefficients, quantity-response assumptions, cost rates, or costing
> methods are selected anywhere in this log.

## Analytical standing (applies to every gate below)

The approved work distinguishes five analytical categories that must never
be conflated:

1. **Observed historical analysis** — frozen Phase 1–3 facts and
   derivations (revenue, discounts, modeled gross profit, authoritative
   contribution). The evidence base; never restated by scenarios.
2. **Hypothetical arithmetic sensitivity** — the only approved scenario
   function: closed-form restatement of frozen transactions under stated
   hypothetical discounts with stated assumptions held fixed.
3. **Forecasting** — statements about what *will* occur. Not approved, not
   producible from this evidence.
4. **Causal inference** — statements about what a discount change *would
   cause*. Not approved, not producible from this evidence.
5. **Optimization** — selection of best or recommended prices/discounts.
   Not approved, not producible from this evidence.

## Gate 1 — Scenario grain — APPROVED

- **Approved decision:** apply pricing scenarios at **line level** and
  aggregate results bottom-up to the **order level**. Initial reporting
  scope is Order × Discount Band and Segment × Discount Band on the ORDER
  basis (authoritative contribution). Customer-level scenario reporting is
  deferred.
- **Rationale:** discount mechanics live at line grain while contribution
  is jointly complete only at order grain and above (Phase 2B.1 authority);
  the order/segment scope is the narrowest reporting set that answers the
  exposure question with authoritative numbers.
- **Implementation implications:** the future build specifies discounts per
  line, rolls hypothetical values to orders, and reports contribution only
  at licensed grains; category/sub-category views, if built, are gross-only
  companions; product-level scenario contribution is not licensed.
- **Deferred:** customer-level scenario reporting (separate future gate).

## Gate 2 — Discount input design — APPROVED

- **Approved decision:** **percentage-point discount change** is the
  primary input method. Relative percentage change and replacement discount
  are retained as explicitly labeled alternatives; exactly one form per
  scenario, reconciled to a stated hypothetical discount per line. All
  resulting discounts must remain within **0.00–0.80**. No clipping,
  extrapolation, or silent adjustment is permitted.
- **Rationale:** pp-change is unambiguous across the discrete observed mass
  points and auditable against band boundaries; the bound keeps every
  scenario inside observed pricing support.
- **Implementation implications:** the build records the chosen form on
  every output and aborts on any out-of-range, NULL, or ambiguous input.
- **Deferred:** final business values for any scenario instance (none
  chosen under this approval).

## Gate 3 — Quantity treatment — APPROVED

- **Approved decision:** use **constant observed quantity**. No
  demand-response modeling, no elasticity coefficients. Results must be
  described as hypothetical arithmetic sensitivity; results must not be
  described as forecasts or causal estimates.
- **Rationale:** the dataset contains no controlled discount experiments
  and no isolated discount effect; any response parameter would be
  invention. Constant quantity is labeled as an assumption, not a finding.
- **Implementation implications:** the build reuses observed quantities
  bit-identical (asserted) and labels every quantity-dependent figure as
  conditional on fixed quantities.
- **Deferred:** any non-constant quantity form (requires a separate
  evidence review under the Phase 4A §5.2 bar; nothing is pre-approved).

## Gate 4 — COGS treatment — APPROVED

- **Approved decision:** use the frozen **revenue-based modeled-COGS
  percentage** as the default scenario method: hypothetical modeled COGS =
  hypothetical net revenue × frozen modeled-COGS percentage. The
  fixed-unit-cost comparator is **not** implemented in the initial Phase 4B
  build. Derived implied unit costs must not be presented as verified
  actual procurement costs. The margin-constancy disclosure is preserved on
  every output using the default rule.
- **Rationale:** preserves benchmark discipline and states its mechanical
  consequence openly (margin percentage constant by construction; currency
  moves with revenue); the comparator stays available only under its
  activation conditions, which are not met.
- **Implementation implications:** the build recomputes COGS from
  hypothetical revenue under frozen percentages and carries the constancy
  statement on-output; no per-unit cost path is built.
- **Deferred:** comparator activation (requires an approved per-unit cost
  source; none exists).

## Gate 5 — Cost-to-serve treatment — APPROVED

- **Approved decision:** pass through observed freight unchanged; preserve
  ambiguous freight at line level (NULL and flagged; 25.05 pair total via
  order aggregation only); invent no freight allocations or cost rates; use
  complete observed freight where validly available at order aggregation.
  Return-processing cost remains **OFF**; support cost remains **OFF**.
  Return status may be used only as an observed filter or cohort flag. No
  unsupported cost assumptions are introduced.
- **Rationale:** inherits the exact Phase 2 ambiguity and scenario
  discipline that keeps baseline totals reconcilable; extends the
  D2A-04/05/11 controls into the hypothetical context.
- **Implementation implications:** the build asserts OFF/zero scenario
  costs, refuses any imputation of the ambiguous pair, and confines return
  status to filtering.
- **Deferred:** any future return/support rate layer (separate sourcing
  decision; permitted families only).

## Gate 6 — Scenario types — APPROVED

- **Approved decision:** initially support only (1) discount increase,
  (2) discount decrease, and (3) uniform discount replacement. Segment-,
  category-, and product-specific scenarios are deferred and must not be
  implemented or represented as available functionality. (Deferred
  scenario *scoping* does not remove Segment × Band *reporting* of the
  approved uniform/increase/decrease scenarios.)
- **Rationale:** a bounded initial taxonomy keeps every instance
  validatable against the same guardrails; scoped discount designs wait
  until the core machinery is proven.
- **Implementation implications:** the build accepts only the three active
  types; deferred types are rejected, not partially supported.
- **Deferred:** segment-specific, category-specific, and product-specific
  scenarios.

## Gate 7 — Discount bounds — APPROVED

- **Approved decision:** permitted hypothetical discount range **0.00–0.80**.
  Values below 0.00 or above 0.80 are invalid. Invalid scenarios must fail
  validation clearly. No clipping, extrapolation, or silent correction is
  permitted.
- **Rationale:** keeps all hypotheticals inside observed pricing support;
  exclusions are counted and reported rather than hidden.
- **Implementation implications:** bound checks are fail-loud build
  requirements. Any out-of-range scenario input causes scenario validation
  to fail clearly. Invalid lines must not be clipped, adjusted, or silently
  excluded from a scenario treated as valid; affected records and counts
  must be reported diagnostically.
- **Deferred:** none at this gate.

## Gate 8 — Output schema — APPROVED

- **Approved decision:** the future scenario output must contain scenario
  metadata, baseline metrics, hypothetical metrics, variance metrics,
  reporting-grain information, and validation/quality flags. Unsupported
  metrics must be explicitly marked unavailable with a reason — never
  estimated and never silently omitted.
- **Rationale:** assumption-layer separation (baseline / assumptions /
  outputs / unsupported flags) is what keeps hypotheticals auditable and
  prevents merged, unexplained numbers.
- **Implementation implications:** the build emits the six schema blocks
  with `N/A`-with-reason marking for unlicensed metrics (notably
  below-order-grain contribution).
- **Deferred:** exact column naming and layout (finalized at build review).

## Gate 9 — Validation thresholds — APPROVED

- **Approved decision:** the future implementation must include mandatory
  fail-loud validation covering discount bounds; no clipping,
  extrapolation, or silent adjustment; constant observed quantity; the
  approved hypothetical revenue formula; the frozen modeled-COGS
  percentage; freight passthrough; ambiguous freight handling; return and
  support costs remaining OFF; baseline reconciliation to frozen Phase 2
  facts; mathematical reconciliation of variance calculations; margin
  changes in percentage points; explicit handling of unsupported metrics;
  scenario metadata and assumption lineage; exclusion of forecast, causal,
  and optimization claims; and deterministic repeated runs. A failed
  validation must clearly identify the issue and prevent the output from
  being treated as valid.
- **Rationale:** machine-enforced validation is the Phase 1–3 project
  culture, and scenarios are the highest invention-risk surface yet.
- **Implementation implications:** the build implements every check above
  as a blocking gate with diagnostic messages; tolerances documented from
  float behaviour at build time.
- **Deferred:** tolerance values (set at build, documented then).

## Gate 10 — Dashboard display rules — APPROVED

- **Approved decision:** future displays must label results as hypothetical
  scenario analysis; show baseline, hypothetical, and variance values
  separately; show absolute changes and margin changes in percentage
  points; display scenario type, discount input, reporting grain,
  validation status, and quality flags; mark unsupported metrics as `N/A`
  with explanation; distinguish gross profit, contribution profit, and
  discount-related revenue forgone; display the key methodology assumptions
  (constant observed quantity; modeled COGS; freight passthrough;
  return-processing and support costs OFF); avoid implying forecasts,
  causal effects, demand predictions, or optimized pricing; keep deferred
  scenario views unavailable unless separately approved.
- **Rationale:** display rules are where arithmetic is most easily misread
  as prediction — the wording and separation regime from Phase 4A §11 is
  therefore binding on any visual, not advisory.
- **Implementation implications:** no dashboard or visual is authorized by
  this approval; these rules constrain a separately gated future display
  phase.
- **Deferred:** all dashboard conventions beyond the binding constraints
  above.

## Approval record

All ten gates above were **approved by the project owner on 2026-09-13**
against the frozen Phase 4A architecture. This approval authorizes the next
design/implementation stage only after this documentation is reviewed and
frozen. It does not implement Phase 4B, select scenario instance values, or
activate any scenario, response, costing, or display functionality.
