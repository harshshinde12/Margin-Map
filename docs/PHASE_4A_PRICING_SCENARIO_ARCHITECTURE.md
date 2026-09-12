# Phase 4A — Pricing Scenario Architecture and Methodology Design

> Status: **ARCHITECTURE AND METHODOLOGY DESIGN ONLY.**
> No scenario calculations are implemented, no scenario outputs are created,
> no elasticity is estimated, no quantity-response assumptions or
> coefficients are introduced, no customer reactions are invented, no
> fixed-unit-cost COGS method is selected or implemented, and no dashboards
> are created in this phase. All structures below are specified for a future
> Phase 4B implementation subject to the approval gates in §12. Phases 1, 2,
> and 3 remain frozen and unchanged.

## 1. Scenario purpose

### 1.1 What a pricing scenario is intended to answer

A MarginMap pricing scenario answers a single bounded question: *if the
recorded discounts on a defined set of historical transactions had instead
been a stated set of hypothetical discounts, with all other stated inputs
held fixed, what would the resulting arithmetic revenue, modeled gross
profit, and — where licensed — contribution figures have been?* The output
is a conditional arithmetic restatement of history, not a prediction about
future transactions and not a measurement of customer behaviour.

### 1.2 Permitted and excluded uses

| Use | Standing in MarginMap | Basis |
|---|---|---|
| Arithmetic price/discount sensitivity | **Permitted** — the core scenario function (§§4, 8) | Closed-form arithmetic on frozen inputs under stated hypothetical discounts |
| Illustrative financial simulation | **Permitted** — strictly as labeled illustration (§11) | Constant-quantity arithmetic plus explicitly labeled assumption layers |
| Demand-response modeling | **Outside the current evidence base** — structure discussed only (§5) | Requires quantity-response evidence that does not exist in the dataset |
| Causal pricing evaluation | **Outside the current evidence base** — forbidden as a claim (§§5, 8, 11) | No controlled discount experiments; no isolated discount effect available |
| Optimization (optimal discounts, best policies) | **Outside the current evidence base** — forbidden (§11) | Optimization over an unidentified response surface would manufacture precision |

The permitted uses quantify *exposure* (how much revenue and modeled profit
sit under each discount configuration); they do not quantify *response*
(how quantities would move). That boundary is load-bearing for every later
section.

## 2. Scenario unit and grain

### 2.1 Candidate grains evaluated

| Grain | Assessment |
|---|---|
| Overall | Valid as a reporting rollup, but too coarse as the application grain — it cannot represent selective discount changes |
| Category | Reporting permitted (gross-only); not a contribution-reporting grain (authority map) |
| Sub-Category | Reporting permitted (gross-only); not a contribution-reporting grain |
| Product | Not recommended for contribution reporting (freight unattributable; Phase 2C/D3B-05 discipline carries over);discount mechanics at product level would strand serve costs |
| Customer | Contribution-authoritative bottom-up, but deferred as an initial reporting grain (decision below) — customer × band cells are thin (Phase 3B: 2,511/2,511 flagged) and scenario detail there would be arithmetic on arithmetic |
| Customer × Sub-Category | Rejected for scenarios — gross-only by construction with contribution explicitly NULL (Phase 2C appendix); both dimensions thin when crossed with bands |
| Order | **Recommended** — the only grain where discount mechanics, revenue, modeled COGS, observed freight, and authoritative contribution are jointly complete |

### 2.2 Recommended structure: line application, order aggregation

Discount mechanics live at line grain (the source `discount` field is a
line attribute), so a hypothetical discount is specified per line.
Aggregation is strictly bottom-up: line hypothetical values roll to the
order, and all contribution reporting is done at order grain and above.
No top-down allocation, no lateral re-allocation, and no freight allocation
below order grain without a separately approved method (none exists).

### 2.3 Initial reporting scope (locked)

Initial Phase 4B reporting is **order × discount-band and Segment ×
discount-band only**, on the ORDER basis (authoritative contribution).
Customer-level scenario reporting is structurally valid (bottom-up from
orders) but **deferred** to a later decision once the order/segment
machinery is validated. Category and Sub-Category scenario views, if built,
are gross-only companions with contribution NULL and the standard reason.
Product-level scenario contribution is not licensed under any initial
configuration.

## 3. Discount input design

### 3.1 Representation of a hypothetical discount

Each in-scope line carries two values that must never be merged:

- `observed_discount` — the frozen source value, preserved bit-identical
  and always reported beside the hypothetical.
- `hypothetical_discount` (`d'`) — the analyst-entered scenario value for
  that line, with author, date, rationale, and scenario identifier recorded
  per the assumption-governance pattern (§10).

### 3.2 Change specification forms

Two equivalent specification forms are permitted; a scenario uses exactly
one, stated on the output:

- **Percentage-point change (primary):** `d' = d + Δpp` (e.g. −5pp / +5pp).
  Primary because it is unambiguous across the discrete observed mass
  points (0.00, 0.20) and directly auditable against band boundaries.
- **Relative change:** `d' = d × (1 + r)` (e.g. −25% of current discount).
  Permitted as an alternative form; both forms must reconcile to the same
  stated `d'` per line, and the chosen form is recorded — two competing
  input readings must never coexist in one output.

A **uniform discount replacement** (`d' = u` for all in-scope lines) is a
limiting case of either form and is specified the same way.

### 3.3 Valid range and edge handling

- Valid hypothetical range: **`0 ≤ d' ≤ 0.80`**, capped at the observed
  maximum. Discounts above observed support would be extrapolation beyond
  all recorded pricing behaviour and are out of scope — no extrapolation
  machinery is architected in this phase.
- `d' = 1` is forbidden (division-by-zero in gross reconstruction); any
  `d' ≥ 1`, negative `d'`, or NULL `d'` aborts the scenario loudly. The
  observed-data guard (`Discount = 1` → NULL gross) is retained and
  mirrored for hypotheticals.
- **Zero-discount observations** (`d = 0`) participate normally: a scenario
  may introduce a first discount on them (pp-change from zero is well
  defined) or leave them at zero; the B0 reference group from Phase 3B is
  the natural baseline cohort and must remain identifiable in outputs.
- **Near-upper-bound observations** (e.g. `d = 0.80` lines): pp-increases
  that would breach 0.80 are rejected per line with a counted exclusion,
  never silently clipped — clipping would fabricate a discount the analyst
  did not enter. Excluded lines are reported with the exclusion count.
- **Scope selectivity:** a scenario applies to an explicit scope (uniform,
  segment-specific, category-specific, product-specific — see §9);
  out-of-scope lines pass through at observed values with
  `d' = d` recorded, so baseline-vs-scenario reconciliation (§10) is exact.

No final business values (which pp changes, which scopes) are chosen here;
any illustrative numbers appearing in future proposals are pending approval
and labeled as such.

## 4. Revenue recalculation

### 4.1 Four quantities that must stay distinct

| Quantity | Definition | Standing |
|---|---|---|
| Observed net revenue | Frozen `sales` (authoritative) | Observed historical fact |
| Reconstructed gross revenue | `sales / (1 − d)` (derived reference, Phase 1A) | Derived reference, never an observed list price |
| Discount amount | Gross − Net (revenue forgone, not profit loss) | Derived reference |
| Hypothetical net revenue | `gross_revenue × (1 − d')`, equivalently `sales × (1 − d') / (1 − d)` | **Hypothetical scenario value** — exists only inside the named scenario |

### 4.2 Constant-quantity arithmetic

Hypothetical revenue is computable in closed form **holding quantity
constant**: the reconstructed gross revenue per line is held fixed while
the hypothetical discount rate varies, so

```text
hypothetical_net(line) = gross_revenue(line) × (1 − d'(line))
hypothetical_discount_amount(line) = gross_revenue(line) − hypothetical_net(line)
```

This is valid arithmetic because gross revenue is, by construction, the
discount-free reference from which both the observed and the hypothetical
net are derived. Its result is labeled a **constant-quantity arithmetic
scenario** — a restatement of what the same transactions would have yielded
at different discount rates with quantities unchanged. It is not a
forecast, not a demand statement, and not evidence about what would have
sold: any quantity movement is a separate assumption layer (§5), never
implicit in the arithmetic.

## 5. Quantity-response framework

### 5.1 Approaches surveyed (none selected, none implemented)

| Approach | Description | Standing |
|---|---|---|
| Constant quantity | Quantities held at observed values; §4 arithmetic only | **The only active assumption in any initial scenario** — and it is labeled as an assumption, not a finding |
| Manually supplied user assumption | Analyst-entered response (e.g. stated % quantity move per band) | Future only; enters solely as a labeled, versioned, unsupported assumption with sensitivity bands, never as a default |
| Externally sourced response assumption | Response parameter from published or procured evidence with cited provenance | Future only; requires the COGS-benchmark discipline (source, date, applicability, confidence) before use |
| Statistically estimated response | Coefficient estimated from the MarginMap observational data | **Blocked**: the dataset lacks experiments and reliable pre-discount price history; confounded association cannot be promoted to a response parameter (Phase 3A §7 carries over intact) |
| Elasticity-based response | True price elasticity of demand applied to scenarios | **Blocked**: no elasticity exists for this data; inventing or importing one as if estimated here is fabrication |

### 5.2 Minimum evidence and validation bar for activation

Quantity response beyond constant-quantity may be activated only when all
of the following hold: (a) the response form and every numerical value is
entered or sourced with author, date, rationale, and version; (b) values
without empirical support carry `UNSUPPORTED_ASSUMPTION` on every output;
(c) results ship as bands over the assumption's uncertainty range, never
point estimates alone; (d) the constant-quantity arithmetic is always
reported first and separately as the assumption-free reference; (e) no
output words the response as observed, measured, or causal. Until then, all
scenario contribution deltas are conditional illustrations under fixed
quantities.

## 6. COGS treatment

### 6.1 Consequence of the revenue-based modeled COGS

Current COGS is modeled as `Net Revenue × modeled COGS %` (Phase 1C-3
benchmarks), so any scenario that moves net revenue moves modeled COGS
mechanically: holding the benchmark fixed makes the scenario gross margin
*percentage* constant by construction while gross profit *currency* moves
with revenue. This is an arithmetic consequence of the model, not a finding
about supplier or unit-cost behaviour, and every output using the default
rule must state that constancy on the output.

### 6.2 Specified treatment (no method selected)

- **Default scenario COGS rule:** recompute as
  `hypothetical Net Revenue × frozen modeled COGS %` (same benchmark
  percentages as baseline). The current benchmark model is never presented
  as a true fixed unit cost, and profit deltas under this rule are never
  worded as if unit costs were held constant in economic reality.
- **Gated fixed-unit-cost comparator:** a comparator that holds per-unit
  cost constant while revenue moves may be specified only after a per-unit
  cost source with methodology, provenance, and validation is approved
  through the COGS governance pattern. Activation conditions: approved
  source exists; comparator reported beside — never substituted for — the
  default rule; versioned and labeled; `implied_modeled_cogs_per_unit`
  explicitly disqualified for this role (it varies with price/discount by
  construction). No such source exists today; no comparator is built.
- **Actual product cost data:** if observed procurement or manufacturing
  costs arrive keyed to the analytical product grain with effective dating,
  they replace the modeled input per key under the Phase 1C-2 input
  contract — they never sit beside it. This is a data-arrival path, not a
  Phase 4B build item.
- **Multiple cost-method views:** when more than one licensed COGS view
  exists, outputs show them side by side with the method labeled per view;
  their difference is reported as method sensitivity, not error.

## 7. Cost-to-serve treatment

- **Observed freight** passes through each scenario unchanged per line,
  exactly as joined (project total 238,173.79). Scenarios re-price revenue;
  they do not re-price movement — any future freight re-specification needs
  its own documented rule and is not architected here.
- **Ambiguous freight pair** (rows 3406/3407): NULL and flagged at line
  grain under all scenarios; the 25.05 pair total (26.55 at full-order
  level) enters only through order-grain aggregation. No scenario may
  impute, split, or pro-rate the 21.59/3.46 candidate values.
- **Return status** remains a filter/cohort flag with order-level meaning;
  the single UNKNOWN order is never defaulted; no refunded-revenue
  adjustment is embedded in any scenario (refunded revenue vs handling cost
  separation from Phase 1A D08 carries over).
- **Return processing cost and support cost** remain OFF (zero) in every
  scenario baseline. Zero means scenario-excluded, never actual cost. They
  may enter a scenario only as separately approved, labeled, versioned rate
  layers (R-B/S-B/S-C families at most; R-C/S-D remain rejected), reported
  beside the OFF baseline — never merged into it silently.
- **No invented costs:** no per-mode freight charge, handling cost,
  ticket cost, or response parameter exists as a default or hidden constant
  in any scenario design.

## 8. Contribution calculation

### 8.1 Arithmetic relationships (frozen waterfall, hypothetical inputs)

```text
hypothetical_cost_to_serve = freight_observed + return_scenario + support_scenario
hypothetical_contribution_profit =
    hypothetical_net_revenue − scenario_COGS − hypothetical_cost_to_serve
hypothetical_contribution_margin_pct =
    hypothetical_contribution_profit / hypothetical_net_revenue × 100
    (NULL/blank when hypothetical net revenue = 0; denominator always net)
```

Equivalence `hypothetical gross profit − hypothetical serve costs` must
reconcile both ways, exactly as in the baseline. Margins aggregate SUM/SUM;
averaging percentages is forbidden; margin changes reported in percentage
points.

### 8.2 Three claim levels (only the first is producible)

| Claim level | Meaning | Permitted? |
|---|---|---|
| Arithmetic scenario contribution | The waterfall recomputed on hypothetical revenue under stated, labeled assumptions | **Yes** — the sole scenario profit output, always beside its baseline |
| Forecast contribution | What contribution *will be* under the hypothetical discounts | **No** — requires demand and cost foresight the project does not have |
| Causal business impact | What the discount change *would cause* in profit | **No** — requires identification that observational data cannot supply |

Every scenario profit figure is therefore presented as arithmetic under
assumptions, with the assumption layers itemized (§10) — never as a
prediction or a measured effect.

## 9. Scenario types

A controlled taxonomy of future scenario *structures*. Each type defines
scope + input form only; no scenario is activated and no values are
assigned in this phase:

1. **Discount increase** — positive pp change on a defined scope.
2. **Discount decrease** — negative pp change on a defined scope (including
   partial or full discount removal, floored at `d' = 0`).
3. **Uniform discount replacement** — all in-scope lines set to a single
   stated rate within [0, 0.80].
4. **Segment-specific discount** — distinct pp changes or replacements per
   Segment (Consumer / Corporate / Home Office), each stated separately.
5. **Category-specific discount** — distinct changes per Category; reporting
   gross-only below order grain per the authority map.
6. **Product-specific discount** — distinct changes per analytical product
   or product set; order-grain contribution reporting only (no product
   contribution attribution); thin-coverage products carry the Phase 3B
   flag discipline.

Cross-type combinations (e.g. segment × category scope) are representable
as scoped instances of the above, not as new types, and each instance
carries one scenario identifier with its full assumption record.

## 10. Guardrails and validation

A future implementation must enforce each safeguard fail-loud before any
scenario output is released:

1. **Discount bounds:** every `d'` within [0, 0.80]; NULL, negative, or
   > 0.80 values abort (no silent clip, no silent default); `d' = 1`
   impossible by the same rule.
2. **No negative revenue:** hypothetical net revenue ≥ 0 on every line;
   any negative aborts (structural impossibility, not a scenario result).
3. **Quantity non-negativity:** quantities ≥ 0 throughout; constant-quantity
   scenarios reuse observed quantities bit-identical (asserted, not
   assumed).
4. **Zero-revenue treatment:** hypothetical margin % NULL/blank when
   hypothetical net revenue is 0; never divide by zero, never 0-fill.
5. **Observed-value preservation:** observed discount, sales, quantity, and
   all frozen inputs carried through bit-identical beside hypotheticals;
   scenarios add columns/rows, never overwrite.
6. **Baseline-vs-scenario reconciliation:** every scenario output presented
   beside the frozen-baseline counterpart on identical scope and grain,
   with absolute variances and margin changes in percentage points; scope
   exclusions counted and reported.
7. **Quarantine exclusion:** `source_profit_quarantined` referenced in zero
   scenario computations (load-time assertion, as in Phase 3B).
8. **No invented costs:** every non-observed scenario input entered,
   sourced, or explicitly labeled unsupported, versioned, and shown on the
   output; hidden defaults forbidden.
9. **Clear scenario labels:** assumption layers separated on every output —
   observed baseline; analyst-entered assumptions (author/date/rationale);
   scenario outputs; unsupported-assumption flag where applicable — reusing
   the `scenario_layer` separation discipline (BASE vs named scenario).
10. **Deterministic outputs:** identical frozen inputs plus identical
    versioned configuration reproduce byte-identical scenario artifacts;
    band definitions, scopes, input values, and assumption versions live in
    versioned configuration, never in manual steps.
11. **Frozen-artifact protection:** no Phase 1–3 data file, script, or
    frozen document modified, regenerated, renamed, or overwritten by
    scenario work; pre-/post-run hash checks on the frozen set are part of
    any future build.

## 11. Reporting and interpretation

### 11.1 Labeling

Hypothetical values are named as hypothetical everywhere they appear
(`hypothetical_*` naming or equivalent unambiguous labeling); derived,
modeled, observed, and hypothetical layers are never merged into a single
unexplained number. The four evidence tiers (OBSERVED / MODELED /
BENCHMARK_ASSUMPTION / FUTURE_DATA, extended with analyst-entered
hypotheticals as a labeled fifth input class) travel with every field into
tables and any future visuals.

### 11.2 Permitted wording (illustrative, non-exhaustive)

- "illustrative constant-quantity scenario";
- "arithmetic change under the stated assumptions";
- "modeled result conditional on the selected cost structure";
- "observed baseline beside the hypothetical restatement";
- "conditional illustration, not a forecast".

### 11.3 Prohibited wording unless separately validated (none validated)

- "the discount caused …";
- "customers will buy more …";
- "expected demand increase …";
- "optimal discount …";
- "best pricing policy …";
- "predicted customer response …".

Any visual whose reading could invite a causal or predictive interpretation
carries the standing caveat on the visual itself, not only in accompanying
text — the Phase 3A §7 discipline extended to scenarios.

## 12. Approval gates

Phase 4B implementation may begin only after owner approval of each item;
until then no scenario build starts and no interim calculations are produced:

1. **Scenario grain** — order-application/order-reporting confirmed (this
   document recommends §2.2–2.3; customer-level reporting separately gated).
2. **Discount input design** — pp-change primary confirmed; relative form
   and replacement form retained or dropped; [0, 0.80] bound confirmed.
3. **Quantity treatment** — constant-quantity as the initial assumption
   confirmed; any non-constant assumption requires its own evidence review
   under §5.2.
4. **COGS treatment** — default modeled-COGS rule confirmed; gated
   comparator conditions (§6.2) confirmed or struck.
5. **Cost-to-serve treatment** — freight passthrough, ambiguity
   preservation, and return/support OFF-default confirmed (§7).
6. **Scenario types** — taxonomy adopted, narrowed, or extended (§9); no
   instance values approved at this gate.
7. **Valid discount bounds** — [0, 0.80] confirmed, including the no-clip
   exclusion rule (§3.3).
8. **Output schema** — hypothetical/baseline column conventions, grain
   markers, assumption-layer fields, and flag columns approved.
9. **Validation thresholds** — the §10 guardrail set adopted as fail-loud
   build requirements, with tolerances documented from float behaviour.
10. **Dashboard display rules** — deferred in full to the dashboard phase;
    this gate records only that no scenario visual may imply causation or
    prediction, per §11.3.

Phase 4A ends with the three design documents (this architecture, the
decision log, and the architecture validation). No Phase 4B build starts
before the gates above are decided.
