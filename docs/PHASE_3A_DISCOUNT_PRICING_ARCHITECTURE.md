# Phase 3A — Discount Impact, Elasticity-lite, and Pricing Scenario Architecture

> Status: **ARCHITECTURE AND METHODOLOGY DESIGN ONLY.**
> No calculations are implemented, no analytical outputs are created,
> no pricing scenarios are activated, and no elasticity coefficients are
> estimated in this phase. All formulas below are specified for future
> implementation in Phase 3B. Phase 1 and Phase 2 remain frozen and unchanged
> (see `docs/PHASE_1_FREEZE.md`, `docs/PHASE_2_FREEZE.md`).
> Freeze date reference: 2026-09-12.

## 1. Purpose and scope

### 1.1 Purpose

Specify how MarginMap will measure discounts, compare profitability across
discount levels, describe observed discount–quantity relationships without
causal claims, and structure future What-if pricing scenarios — using only
frozen Phase 1 and Phase 2 inputs and respecting all established grain,
quarantine, and ambiguity controls.

### 1.2 In scope (design only)

- Canonical definitions for all discount measures and their denominators,
  guards, and aggregation rules.
- A reproducible discount-band structure anchored to the observed discount
  distribution.
- Descriptive discount-impact analysis designs at the appropriate grains
  (overall, Segment, Category, Sub-Category, Customer, Product).
- Rules for when authoritative order-level contribution metrics may be used
  and when analysis must remain gross-profit-only.
- An observational, descriptive elasticity-lite design with explicit
  non-causal boundaries.
- A default-OFF What-if scenario framework, including assumption governance
  and COGS handling.
- Validation and governance rules for future implementation.

### 1.3 Out of scope (explicitly not done in Phase 3A)

- No implementation in Python, SQL, or Power BI.
- No new CSV, JSON, table, or visual outputs.
- No activation of pricing or discount scenarios.
- No estimation of elasticity coefficients or demand parameters.
- No customer demand behaviour assumptions.
- No modification, regeneration, renaming, or overwrite of any Phase 1 or
  Phase 2 file, script, or frozen document.
- No Git operations.
- No use of the quarantined source `Profit` field in any computation.
- No causal statements about discounts causing quantity or profit changes.

## 2. Foundations reused (frozen, not redefined)

### 2.1 Financial definitions

Phase 1A definitions (`docs/FINANCIAL_MODEL.md`) are adopted verbatim:

- `Net Revenue = Sales` (authoritative; source Sales is already net of
  discount; no second discount subtraction).
- `Gross Revenue = Sales / (1 − Discount)` for Discount < 1; NULL/blank when
  Discount = 1. Derived reference only, never presented as observed list
  price.
- `Discount Amount = Gross Revenue − Net Revenue`
  (equivalent: `Gross Revenue × Discount`; the first form is primary because
  it reconciles Gross to Net).
- `Modeled COGS = Net Revenue × Modeled COGS %`, with
  `Modeled COGS % = 1 − benchmark gross margin %` (Phase 1C-3 revenue-based
  modeled methodology; analytical estimate, not historical accounting COGS).
- `Modeled Gross Profit = Net Revenue − Modeled COGS`.
- `Modeled Gross Margin % = Gross Profit / Net Revenue × 100`
  (NULL/blank when Net Revenue = 0; denominator always Net Revenue).
- `Contribution Profit = Net Revenue − Modeled COGS − Freight Cost
  − Return Processing Cost − Support Cost`
  (equivalent: `Gross Profit − Total Cost-to-Serve`, both forms reconciled).
- `Contribution Margin % = Contribution Profit / Net Revenue × 100`
  (NULL/blank when Net Revenue = 0).
- Return Processing Cost and Support Cost are specified scenario components
  and remain OFF (zero) in the baseline.
- Source `Profit` is quarantined and excluded from all computations.

### 2.2 Cost-to-serve and contribution baseline

Phase 2 (`docs/COST_TO_SERVE_MODEL.md`, `docs/PHASE_2B_CONTRIBUTION_MODEL.md`,
`docs/PHASE_2C_PROFITABILITY_ANALYSIS.md`) is adopted without change:

- Freight is the observed Shipping Cost from the Dataset 1-US enrichment,
  joined line-to-line (project total 238,173.79).
- The single ambiguous line pair (Phase 1 rows 3406/3407; candidate values
  21.59 and 3.46; invariant pair total 25.05; full affected-order freight
  26.55 including 1.50 of uniquely matched lines) remains NULL and flagged
  at line grain and resolved only at order grain. No line-level freight is
  fabricated for this pair.
- Contribution is authoritative at order level in
  `data/processed/order_margin_map_phase2.csv` (5,009 orders; baseline
  Contribution Profit 565,116.9418; Contribution Margin 24.6002% SUM/SUM,
  scenarios OFF).
- Return status is observed at order level only (296 YES orders, 1 UNKNOWN
  order `CA-2015-102015`, remainder NOT_RETURNED under the documented
  completeness assumption). It is a filter flag; it does not identify which
  product lines within an order were returned.
- Product, sub-category, and customer × sub-category views are gross-profit
  views; no product-level freight attribution exists and no product-level
  contribution metric is licensed.

### 2.3 Source tables and schemas (as inspected)

Phase 3A designs read the following frozen files read-only. Column lists
below are the inspected schemas and the binding input contract.

**`data/processed/fact_sales_cogs.csv`** — 9,994 rows × 35 columns, line
grain (`row_id` unique):

`row_id`, `order_id`, `order_date`, `ship_date`, `ship_mode`,
`customer_id`, `customer_name`, `segment`, `country`, `city`, `state`,
`postal_code`, `region`, `product_id`, `category`, `sub_category`,
`product_name`, `sales`, `quantity`, `discount`,
`source_profit_quarantined`, `net_revenue`, `is_missing_postal_code`,
`has_product_name_conflict`, `has_implied_unit_price_issue`,
`analytical_product_key`, `benchmark_gross_margin_pct`, `modeled_cogs_pct`,
`implied_modeled_cogs_per_unit`, `modeled_cogs`, `modeled_gross_profit`,
`modeled_gross_margin_pct`, `cogs_status`, `benchmark_level`,
`benchmark_confidence`.

**`data/processed/fact_margin_map_phase2.csv`** — 9,994 rows × 49 columns,
line grain; the 35 Phase 1 columns above retained in order plus 14
Phase 2 columns:

`freight_cost_observed`, `freight_join_status`, `freight_ambiguity_flag`,
`freight_order_total` (informational per line — do not sum),
`return_status`, `return_status_source`, `return_crosswalk_flag`,
`return_processing_scenario_enabled`, `return_processing_cost_scenario`,
`support_scenario_enabled`, `support_cost_scenario`, `cost_to_serve`,
`contribution_profit`, `contribution_margin_pct`.

Observed Phase 2 control values (read-only inspection): `freight_join_status`
is `MATCHED_UNIQUE` on 9,992 lines and `MATCHED_AMBIGUOUS` on 2 lines;
`freight_ambiguity_flag = TRUE` on exactly those 2 lines with NULL
`freight_cost_observed` (and consequently NULL `cost_to_serve` /
`contribution_*`); `return_status` is `YES` on 800 lines (296 orders),
`UNKNOWN` on 6 lines (1 order), `NOT_RETURNED` on 9,188 lines;
both scenario cost columns are 0 with their `_enabled` flags FALSE.

**`data/processed/order_margin_map_phase2.csv`** — 5,009 rows × 10 columns,
order grain; authoritative for contribution aggregation:

`order_id`, `order_revenue`, `order_cogs`, `order_freight`,
`order_return_status`, `order_return_processing_cost_scenario`,
`order_support_cost_scenario`, `order_cost_to_serve`,
`order_contribution_profit`, `order_contribution_margin_pct`.

Consequence for design: the order fact carries no `discount`, `quantity`,
`segment`, `category`, `sub_category`, `customer_id`, or product key.
Any order-level discount, quantity, or dimensional attribute used in Phase 3B
must therefore be derived by joining or rolling up the line fact under the
rules in §§5–6, never by assuming columns that are not present.

## 3. Discount measurement

### 3.1 Canonical definitions

All discount measures below are defined at transaction-line grain unless
stated otherwise. Aggregates are pure sums of lines except where a weighted
average is specified. Margin-percentage averaging is forbidden; margins are
always computed on sums (SUM/SUM).

| Measure | Definition | Formula | Denominator / weight | Guards and lineage |
|---|---|---|---|---|
| Discount Rate | Recorded discount on the line, as stored | Source field `discount` (decimal; ×100 for display only) | — | Source-derived. Valid range [0, 1). NULL or outside-range values fail loudly in implementation; no silent default. |
| Gross Revenue | Reference revenue before discount; reconstructed because no list-price field exists | `sales / (1 − discount)` | — | Source-derived reference. NULL/blank when `discount = 1`. Label as derived wherever shown. |
| Net Revenue | Authoritative revenue | `sales` | — | Source-derived. Must reconcile to `sales` exactly. Never subtract discount again. |
| Discount Amount | Revenue reduction associated with the recorded discount | `gross_revenue − net_revenue` (equiv. `gross_revenue × discount`; first form primary) | — | Source-derived. Must reconcile to Gross minus Net. Revenue reduction, not profit loss (§3.2). |
| Discount Band | Assigned discount group for the line (§4) | Deterministic mapping from Discount Rate to a fixed band label | — | Every line assigned exactly one band; bands cover the full observed range [0, 0.8]; zero-discount group preserved. |
| Weighted Average Discount (WAD) | Revenue-weighted mean discount for any aggregate | `SUM(discount_amount) / SUM(gross_revenue)` over the aggregate | Weight: gross revenue | Never an arithmetic mean of Discount Rate. Equivalent form `1 − SUM(net_revenue)/SUM(gross_revenue)` must reconcile. NULL/blank when aggregate gross revenue is 0. |
| Discount Amount as % of Gross Revenue | Share of reference revenue absorbed by discount | `SUM(discount_amount) / SUM(gross_revenue) × 100` | Denominator: gross revenue | Numerically identical to WAD × 100 for the same aggregate; the two labels must never be summed or presented as independent addends. Report margin-type changes in percentage points. |
| Revenue realization rate | Share of reference revenue retained after discount | `SUM(net_revenue) / SUM(gross_revenue) × 100` (equiv. `100 − Discount Amount % of Gross`) | Denominator: gross revenue | Complement of the preceding measure. NULL/blank when aggregate gross revenue is 0. |

### 3.2 Discount Amount is not automatically profit loss

Discount Amount measures revenue forgone relative to reconstructed Gross
Revenue. Its translation into profit depends on the cost structure that the
discounted revenue must still cover:

- Modeled COGS in the current baseline scales with Net Revenue by
  construction (§8.3), so a discount that lowers Net Revenue simultaneously
  lowers modeled COGS in the arithmetic — the gross-profit effect is
  mediated by the benchmark margin, not equal to the Discount Amount.
- Freight is observed and independent of the discount arithmetic; a
  discounted order still carries its full observed freight.
- Return and support scenario layers, when enabled in future, add further
  costs that are unaffected by the discount definition itself.

Accordingly, Discount Amount (and Discount Leakage, which shares its
arithmetic under a different framing — the two must never be summed) shall
be described as revenue reduction or revenue forgone, and any profit
statement must pass through the contribution waterfall with the applicable
cost layers stated.

### 3.3 Aggregation and display rules

- Currency measures (Gross Revenue, Net Revenue, Discount Amount, Gross
  Profit, Cost-to-Serve, Contribution Profit) aggregate by SUM.
- Rates aggregate only as weighted measures (WAD by gross revenue; margins
  by net revenue, SUM/SUM). Averaging line or order percentages is
  forbidden.
- Margin and discount-rate changes over time or across groups are reported
  in percentage points, never as "%" shorthand.
- Gross Revenue and Discount Amount are labeled derived wherever shown.
- Contribution percentages use Net Revenue as denominator, never Gross
  Revenue.

## 4. Discount band design

### 4.1 Observed discount distribution (read-only inspection)

The discount field was inspected read-only in the frozen line fact to inform
band design. No output files were created. Findings:

- Range observed: [0, 0.8]. No `discount = 1` and no NULL observed; guards
  for both remain mandatory in implementation.
- The field takes exactly 12 discrete values (policy-like mass points, not
  a continuous distribution):

| Discount | Lines | Share of 9,994 |
|---|---:|---:|
| 0.00 | 4,798 | 48.01% |
| 0.10 | 94 | 0.94% |
| 0.15 | 52 | 0.52% |
| 0.20 | 3,657 | 36.59% |
| 0.30 | 227 | 2.27% |
| 0.32 | 27 | 0.27% |
| 0.40 | 206 | 2.06% |
| 0.45 | 11 | 0.11% |
| 0.50 | 66 | 0.66% |
| 0.60 | 138 | 1.38% |
| 0.70 | 418 | 4.18% |
| 0.80 | 300 | 3.00% |

- Two mass points dominate (0.00 and 0.20 jointly 84.60% of lines).
- Four values are sparse (0.15: 52 lines; 0.32: 27 lines; 0.45: 11 lines;
  0.10: 94 lines) and must not be reported as standalone segments without
  sample-size warnings.

### 4.2 Band type: fixed, value-based (quantile-based rejected as primary)

Bands are **fixed, value-based intervals** defined on Discount Rate. A
quantile-based banding is rejected as the primary structure because:

- Discounts are discrete policy-like values; quantile cut-points would split
  identical discount values across adjacent bands and merge economically
  distinct discount levels, obscuring the policy meaning the analysis exists
  to reveal.
- The distribution is heavily bi-modal (0.00 / 0.20); quantiles would
  over-partition the mass points and under-represent the sparse tail.

A quantile cut may be retained in Phase 3B solely as a sensitivity
comparator (reported alongside, never replacing, the fixed bands), subject
to owner approval.

### 4.3 Proposed candidate band structure

The following fixed bands are **proposed for Phase 3B validation** (candidate
structure, informed by §4.1; final adoption requires the validation in §4.4
and owner approval). Intervals are stated as (lower, upper] except for the
zero group, which is exact. Each observed discrete value maps to exactly one
band; no value is split.

| Band (candidate label) | Interval | Observed values contained | Lines (observed) |
|---|---|---|---:|
| B0 — No discount | `d = 0` | 0.00 | 4,798 |
| B1 — Low discount | `0 < d ≤ 0.15` | 0.10, 0.15 | 146 |
| B2 — Standard discount | `0.15 < d ≤ 0.25` | 0.20 | 3,657 |
| B3 — Elevated discount | `0.25 < d ≤ 0.35` | 0.30, 0.32 | 254 |
| B4 — High discount | `0.35 < d ≤ 0.55` | 0.40, 0.45, 0.50 | 283 |
| B5 — Deep discount | `0.55 < d ≤ 0.80` | 0.60, 0.70, 0.80 | 856 |

Design properties:

- The zero-discount group is preserved exactly as its own band (reference
  group for all comparisons).
- Six bands total: fine enough to separate the observed tail, coarse enough
  to avoid excessive segmentation and single-value micro-segments.
- Full observed range [0, 0.8] is covered with no gaps and no overlaps.
- Sparse values (0.10/0.15, 0.32, 0.45) are pooled with their value-nearest
  neighbours so that no band rests on fewer than ~140 lines at overall
  grain, while the pooling is disclosed (this table) rather than hidden.
- Any `discount = 1`, NULL, or outside-[0,1) value falls into no band and
  triggers the fail-loud guard (§9); bands are never extended silently to
  absorb invalid values.

### 4.4 Band validation (required in Phase 3B before adoption)

1. **Coverage and uniqueness:** every line with valid discount assigned to
   exactly one band; band line counts sum to 9,994; zero invalid assignments.
2. **Zero preservation:** B0 contains exactly the 4,798 zero-discount lines,
   no more, no fewer.
3. **Value integrity:** no observed discrete discount value is split across
   two bands.
4. **Sparse-group disclosure:** each band reports its line count, order
   count, and constituent discount values; bands or band × dimension cells
   below the minimum sample threshold (§5.4) carry a `low_sample_flag` and
   are described as arithmetic, not evidence.
5. **Stability check:** band definitions are constants in code or
   configuration under version control; re-running the assignment on the
   frozen fact reproduces identical band counts deterministically.
6. **Comparator (optional, owner-approved):** if a quantile banding is built
   as a sensitivity comparator, both structures must reconcile to the same
   totals and their differences reported as method sensitivity, not error.

## 5. Discount impact analysis design

### 5.1 Analytical grains

Descriptive discount-impact analyses are designed at the following grains.
Each grain states its counting unit and its authoritative profit basis (§6).

| Grain | Unit | Dimensions | Profit basis |
|---|---|---|---|
| Overall | All 9,994 lines / 5,009 orders | — (single row plus per-band breakdown) | Authoritative order-level contribution for totals; line-level gross for band detail subject to §6 |
| Segment | 3 segments (Consumer 5,191 lines; Corporate 3,020; Home Office 1,783) | `segment` (line attribute; order-level segment derived only where the order is single-segment, else reported as mixed per rule in §5.3) | Order-level contribution where orders are attributable; otherwise gross-profit with the limitation stated |
| Category | 3 categories (Furniture 2,121; Office Supplies 6,026; Technology 1,847) | `category` (fully consistent per product; safe attribute) | Gross-profit basis (§6.3); contribution not licensed at this grain |
| Sub-Category | 17 sub-categories (smallest: Copiers 68 lines; Machines 115) | `sub_category` (fully consistent per product; safe attribute) | Gross-profit basis; contribution not licensed |
| Customer | 793 customers | `customer_id` (verified 1:1 with name; clean rollup key) | Authoritative order-level contribution (bottom-up from orders) |
| Product | 1,894 analytical products (`product_id + product_name`) | `analytical_product_key` | Gross-profit basis with `low_volume_flag` discipline (Phase 2C: 93 single-order products flagged); contribution not licensed |

Product-level band × product cells are expected to be extremely sparse and
are therefore descriptive reference only, subject to §5.4. Customer-level
band analysis aggregates each customer's lines or orders within each band;
customers with activity in multiple bands appear in each applicable band
row with the duplication stated (band rows at customer grain do not sum to
the customer total unless de-duplication logic is specified and validated).

### 5.2 Measures per group

For each grain × band cell (and each grain total), the future
implementation shall compute the descriptive set below. Currency measures
are SUMs; rates are weighted measures on sums:

- Observation counts: line count; order count (distinct `order_id`);
  customer / product counts where the grain requires them.
- Volume: quantity (SUM).
- Revenue: gross revenue (SUM, derived); net revenue (SUM; reconciles to
  Sales); discount amount (SUM; reconciles to Gross minus Net).
- Discount intensity: weighted average discount (SUM(Discount Amount) /
  SUM(Gross Revenue)); Discount Amount as % of Gross; revenue realization
  rate (§3.1).
- Profitability (basis per §6): gross profit (SUM) and gross margin
  (SUM/SUM on net revenue) wherever line revenue and modeled COGS are
  available; contribution profit (SUM) and contribution margin (SUM/SUM)
  only where §6 licenses order-level contribution.
- Negative-profit observations: count and share of lines (or orders at
  order grain and above) with negative gross profit / negative contribution,
  plus the revenue and profit attributable to those observations. (Baseline
  expectation from Phase 2C: zero negative-gross-profit products and zero
  negative-contribution customers under scenarios-OFF; 50
  contribution-negative orders exist — the design must preserve visibility
  of this grain asymmetry rather than averaging it away.)
- Sample-size warnings: `low_sample_flag` per §5.4 on every small cell.

### 5.3 Level-specific metric discipline

- **Line-level metrics** use observed line fields directly (`sales`,
  `quantity`, `discount`, `net_revenue`, `modeled_cogs`,
  `modeled_gross_profit`, `freight_cost_observed` where non-NULL).
- **Order-level metrics** use the authoritative order fact for revenue,
  COGS, freight, cost-to-serve, contribution profit, and margin. Order-level
  discount intensity is derived, not observed: order WAD =
  `SUM(line discount_amount) / SUM(line gross_revenue)` over the order's
  lines (equivalently `1 − order_revenue / order_gross_revenue`), and the
  order's band assignment rule (e.g. order WAD band vs dominant-line band)
  must be specified once in Phase 3B and applied consistently — two
  competing order-band rules must never coexist in one output.
- **Customer-level metrics** roll up authoritative order-level contribution
  (SUM of the customer's orders) plus line-derived discount intensity;
  customer WAD is gross-revenue-weighted across the customer's lines.
- **Product-level and sub-category-level metrics** are gross-profit-only
  (SUM of line modeled gross profit; SUM/SUM gross margin) with volume and
  discount-intensity companions. No freight, cost-to-serve, or contribution
  column is populated at these grains.
- **Sub-category-level margins** restate benchmark × mix by construction
  (Phase 2C §7); outputs at this grain must carry that caveat rather than
  presenting benchmark restatement as discovery.
- Dimensional attributes that repeat per line for filtering only (notably
  `return_status`, and the informational `freight_order_total`) are never
  summed; `freight_order_total` in particular is a do-not-sum field.

### 5.4 Minimum sample-size thresholds and sparse-group handling

- Every reported cell carries its line count and order count alongside the
  financial measures; counts are part of the output, not an appendix.
- A minimum-sample rule is enforced before interpretation: cells below the
  approved threshold (threshold value to be set in Phase 3B with owner
  approval; applicable separately to line counts and order counts) carry a
  `low_sample_flag = TRUE` and are described as arithmetic only, not as
  evidence of a discount effect. The flag travels into any downstream
  table or visual.
- Sparse discount values (§4.1) and small sub-categories (notably Copiers,
  Machines, Supplies, Fasteners) are expected to breach thresholds in
  band × dimension cells; the design requires these cells to remain visible
  with flags rather than being suppressed or silently merged, so that
  readers see where evidence is thin.
- Single-order products (`low_volume_flag` per Phase 2C discipline) retain
  their flag in any discount cut; their band-level margins are arithmetic,
  not evidence.

## 6. Contribution-margin treatment

### 6.1 Authority map

| Analysis | Revenue / COGS source | Freight treatment | Contribution permitted? |
|---|---|---|---|
| Overall totals | Order fact (authoritative) | Order freight incl. 25.05 pair total | Yes — authoritative overall contribution and margin |
| Order-level and order-band analysis | Order fact | Order freight (26.55 on the affected order) | Yes — authoritative |
| Customer-level and customer × band analysis | Customer rollup of authoritative order fact | Bottom-up from orders (complete order economics) | Yes — authoritative (Phase 2C discipline) |
| Line-level band detail (overall / segment cuts) | Line fact (`net_revenue`, `modeled_cogs`, `modeled_gross_profit`) | Line `freight_cost_observed` where non-NULL; ambiguous pair excluded (NULL, flagged) | Line-level contribution is a partial view: it excludes the 25.05 pair total and its 225.10 gross profit. Report alongside the authoritative order-level total with the gap stated; never present the line sum as the project total |
| Segment-level contribution | Attributable only where orders are wholly within one segment | Bottom-up from attributable orders | Only for the attributable subset with the mixed-order rule stated (§5.3); otherwise gross-profit with limitation stated |
| Category / Sub-Category analysis | Line fact (revenue, modeled COGS, gross profit) | No product-level freight attribution exists | No — gross-profit-only; freight and contribution columns explicitly NULL with reason `FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN` (Phase 2C discipline) |
| Product-level analysis | Line fact (revenue, modeled COGS, gross profit) | Same as above | No — gross-profit-only; any future product attribution requires a separate documented attribution decision and must never be inferred from the order-level treatment |
| Customer × sub-category analysis | Line fact (gross-profit-only per Phase 2C) | Not attributable | No — gross-profit-only; contribution explicitly NULL |

### 6.2 Ambiguous-freight rule (binding on all Phase 3B work)

Lines 3406/3407 retain NULL `freight_cost_observed`, NULL `cost_to_serve`,
and NULL `contribution_*` with `freight_ambiguity_flag = TRUE` and
`freight_join_status = MATCHED_AMBIGUOUS` in the line fact. No analysis may
impute, split, or pro-rate the 21.59 / 3.46 candidate values to either row.
The 25.05 pair total (26.55 at full-order level) enters only through the
order fact. Any line-grain contribution sum must be accompanied by the
reconciliation to the authoritative order-level total.

### 6.3 Return-status and scenario-component rules

- `return_status` (line-repeated, order-level meaning) is a **filter and
  cohort flag only**. Discount-impact tables may present RETURNED-order vs
  NOT_RETURNED-order cohorts side by side, but must state that the flag
  does not identify which lines were returned and that no refunded-revenue
  or return-cost adjustment is embedded in the baseline.
- The single UNKNOWN order is retained as UNKNOWN and never defaulted into
  either cohort.
- Return Processing Cost and Support Cost remain **OFF (zero)** in every
  baseline discount analysis. Zero means scenario-excluded, never actual
  cost. Any scenario-ON view is a separately labeled scenario output under
  §8, reported alongside — never replacing — the baseline.

## 7. Elasticity-lite architecture (observational, descriptive, non-causal)

### 7.1 Standing declaration (binding language for all outputs)

The elasticity-lite analysis is an **observational, descriptive summary of
how quantity and discount co-occur in historical transactions. It is not
causal price-elasticity estimation.** Specifically:

- Discount and quantity may each be affected by product, customer, category,
  seasonality and time, sales effort, stock availability, competition, and
  other unrecorded factors; the dataset does not isolate the discount
  effect from these confounders.
- The dataset lacks controlled experiments (no randomized discount
  assignment) and lacks reliable pre-discount unit-price history for causal
  inference (Gross Revenue is reconstructed from Net Revenue and Discount,
  not independently observed; implied unit values vary with price and
  discount and are not stable unit costs).
- Observed relationships — including any positive association between
  higher discount bands and higher quantities — **must not be interpreted
  as proof that discounts caused quantity increases**, and must not be
  worded as causal in tables, visuals, or narrative.

Every elasticity-lite output carries this declaration or a cited reference
to it; any visual whose reading invites a causal interpretation carries the
caveat on the visual itself, not only in accompanying text.

### 7.2 Candidate descriptive inputs (no coefficients estimated in Phase 3A)

The future implementation may describe, per discount band (overall and
within Segment / Category / Sub-Category cuts where sample permits):

- Quantity per line (mean and median; medians alongside means because
  quantity is small-integer and skewed).
- Quantity per order (SUM(quantity) / distinct orders in the cell).
- Order frequency: distinct orders per customer, and share of customers
  ordering in each band, to separate basket-size effects from
  purchase-frequency effects.
- Segment-level and category / sub-category comparisons of the above, to
  expose composition effects (e.g. a band that looks quantity-responsive
  overall but merely over-represents a high-quantity category).
- Time cuts (year / month) as contextual companions where they clarify
  composition, without attributing time trends to discounts.

Minimum sample thresholds (§5.4) apply to every elasticity-lite cell;
small cells are flagged and excluded from comparative statements.

### 7.3 Descriptive response indicators (not elasticity)

No true elasticity is estimated. If Phase 3B proposes a band-to-band
quantity indicator, it shall be specified and labeled strictly as a
**descriptive response indicator**, for example:

```text
Descriptive quantity index (band B vs reference band B0),
within a fixed Segment × Category cut:
  Q_index = (mean quantity per order in B) / (mean quantity per order in B0)
```

with the mandatory companions: cell counts for both bands, the WAD of each
band, the confounder disclaimer (§7.1), and — where computed — a rank
correlation between band-ordered discount intensity and quantity reported
as an observed association with its sample size, never as an elasticity or
as evidence of causation. Correlation, if shown, is a descriptive
association measure over confounded observational data.

The following are forbidden: labeling any indicator "elasticity" or "price
elasticity of demand"; presenting an indicator as a demand parameter
suitable for optimization without a separately approved causal model;
fitting log-log or other structural demand regressions and reporting their
coefficients as elasticities; and pooling across segments, categories, or
time periods without showing the within-cut breakdowns that reveal
composition effects.

## 8. Pricing and discount scenario architecture (designed, kept OFF)

### 8.1 Standing

A future What-if scenario framework is **designed in this phase and kept
OFF**. No scenario is activated, no scenario output is produced, and no
numerical quantity-response assumption is selected in Phase 3A. All controls
below are specification for Phase 3B implementation, where scenarios default
to OFF and baseline outputs are always reported first and separately.

### 8.2 Scenario controls (specification)

A scenario definition comprises analyst-entered assumptions only; nothing in
this list is inferred from the data:

- Discount change in percentage points applied to in-scope lines (e.g. −5pp
  / +5pp) or an explicit target discount rate per band.
- Gross price adjustment rule: whether reconstructed Gross Revenue per line
  is held constant (discount change flows fully to Net Revenue) or adjusted
  by an entered percentage, stated per scenario.
- Assumed quantity response: an entered assumption about how quantity moves
  under the scenario (no value selected in Phase 3A; §8.4 governs the
  permitted forms).
- Scope selector: Segment / Category / Sub-Category / band subset to which
  the scenario applies; out-of-scope lines pass through at baseline values.
- Scenario scope grain: line-level application with bottom-up aggregation
  (scenarios apply to lines, aggregates re-sum; no aggregate-level scenario
  pushed down).
- Baseline-versus-scenario comparison: every scenario output is presented
  beside the frozen-baseline counterpart computed on identical scope and
  grain, with absolute variances and margin changes in percentage points.

### 8.3 COGS handling in scenarios (binding)

Because current COGS is modeled as a percentage of Net Revenue
(`modeled_cogs = Net Revenue × modeled COGS %`), scenario arithmetic must
handle COGS explicitly and honestly:

- **Default scenario COGS rule:** recompute scenario COGS as
  `scenario Net Revenue × frozen modeled COGS %` (same benchmark percentages
  as the baseline). This preserves benchmark discipline and makes the
  mechanical consequence transparent: holding the benchmark fixed means the
  scenario gross margin *percentage* is constant by construction and only
  gross profit *currency* moves with revenue. Outputs using this rule must
  state that constancy on the output — it is an arithmetic consequence of
  the revenue-based model, not a finding about cost behaviour.
- **Prohibited presentation:** the current benchmark model must never be
  presented as a true fixed unit cost, and scenario profit deltas computed
  under the default rule must never be worded as if suppliers or unit costs
  were held constant in economic reality.
- **Fixed-unit-cost alternative:** a scenario that holds per-unit cost
  constant while revenue moves (the economically natural pricing-scenario
  assumption) requires observed or approved per-unit costs, which do not
  exist in the current dataset (`implied_modeled_cogs_per_unit` is a derived
  analytical reference that varies with price/discount — §2.1 — and must
  never serve as the fixed unit cost). This alternative is therefore
  **not permitted as a base scenario** until a per-unit cost source with
  methodology, provenance, and validation is approved through the COGS
  governance pattern. If later approved, it must be versioned, labeled, and
  reported as a comparator against the default rule, never silently
  substituted for it.
- Freight in scenarios: observed line freight passes through unchanged
  unless a scenario explicitly re-specifies freight handling with its own
  documented rule; the ambiguous pair remains NULL/flagged at line grain
  under all scenarios. Return/support scenario layers remain OFF unless a
  scenario explicitly enables a labeled, versioned rate.

### 8.4 Assumption governance

Every scenario output distinguishes four labeled layers that must never be
merged into a single unexplained number:

1. **Observed baseline metrics** — frozen-input values on the scenario scope
   (revenue, COGS, freight, contribution under scenarios-OFF).
2. **Analyst-entered assumptions** — the discount change, price rule,
   quantity-response assumption, and scope, each with author, date, and
   rationale recorded.
3. **Scenario outputs** — recomputed revenue, COGS (per §8.3 rule stated),
   profit, and margin under the entered assumptions.
4. **Unsupported-assumption flag** — any assumption without empirical or
   sourced support (in particular every quantity-response assumption until a
   causal basis exists) is labeled `UNSUPPORTED_ASSUMPTION` on the output;
   scenario profit deltas built on unsupported assumptions are labeled
   conditional illustrations, never forecasts or recommendations.

No numerical quantity-response assumption is selected in Phase 3A; selecting,
bounding, or sourcing such assumptions is deferred to Phase 3B proposal with
owner approval, and any implemented assumption ships with sensitivity bands
(§9) rather than a point estimate alone.

## 9. Validation and governance (requirements for Phase 3B implementation)

The future implementation must satisfy each rule below; violation fails the
build loudly before any output is released:

1. **Discount range:** every `discount` value consumed is within [0, 1).
   NULL, negative, or ≥ 1 values abort the run; no silent default or
   silent band assignment.
2. **Gross Revenue guard:** `discount = 1` yields NULL/blank Gross Revenue
   and Discount Amount (never divide by zero); affected lines are excluded
   from WAD denominators with the exclusion counted and reported.
3. **Net Revenue reconciliation:** SUM(`net_revenue`) equals SUM(`sales`)
   exactly (tolerance documented from float behaviour); any gap fails.
4. **Discount Amount reconciliation:** SUM(`discount_amount`) equals
   SUM(`gross_revenue`) − SUM(`net_revenue`) exactly, and aggregate WAD
   computed both as `SUM(discount_amount)/SUM(gross_revenue)` and as
   `1 − SUM(net)/SUM(gross)` reconciles; Discount Amount and Discount
   Leakage are never summed together.
5. **Weighted-average discipline:** WAD uses gross-revenue weights; margins
   use SUM/SUM on net revenue; no averaging of percentages at any grain.
6. **Contribution authority:** overall, order-level, and customer-level
   contribution reconcile to `order_margin_map_phase2.csv` exactly
   (inclusive of the 25.05 pair treatment); line-grain contribution sums
   reconcile to the order total plus the stated 25.05-held-at-order gap;
   product / sub-category / customer × sub-category outputs carry NULL
   freight/contribution with the attributable-grain reason.
7. **Ambiguity preservation:** lines 3406/3407 remain NULL-freight, flagged,
   and unassigned in every Phase 3B input read; any output that silently
   assigns 21.59/3.46 fails validation.
8. **Scenario defaults:** all pricing/discount scenarios default to OFF;
   baseline outputs are produced and reported with scenarios disabled before
   any scenario-ON view; scenario-ON outputs carry assumption labels and
   the unsupported-assumption flag where applicable.
9. **No invented coefficients:** no elasticity coefficient, demand
   parameter, quantity-response rate, return rate, handling cost, or ticket
   cost exists as a default or hidden constant; every non-observed input is
   entered, sourced or explicitly labeled unsupported, versioned, and shown
   on the output.
10. **No causal claims:** no table, visual, or narrative states or implies
    that an observed discount–quantity association proves causation; the
    §7.1 declaration (or cited reference) accompanies every elasticity-lite
    and scenario output, on the visual where misreading is likely.
11. **Deterministic reruns:** identical frozen inputs plus identical
    configuration reproduce byte-identical outputs (hash-compared); band
    definitions, thresholds, and scenario assumptions live in versioned
    configuration, never in unrecorded manual steps.
12. **Frozen-artifact protection:** no Phase 1 or Phase 2 data file, script,
    or frozen document is modified, regenerated, renamed, or overwritten by
    Phase 3B work; pre- and post-run hash checks on the frozen set are part
    of the build; the quarantined source Profit field is referenced in zero
    computations.

## 10. Phase boundary and handover

Phase 3A ends with the three design documents (this architecture, the
decision log, and the architecture validation). Phase 3B (implementation)
may begin only after owner approval of:

- the candidate band structure (§4.3) or an amended alternative;
- the minimum sample-size thresholds (§5.4);
- the order-band assignment rule where order-level banding is used (§5.3);
- whether a quantile comparator is built (§4.2);
- the permitted form and bounds of scenario quantity-response assumptions
  (§8.4) — no values are approved in Phase 3A;
- whether any fixed-unit-cost COGS comparator may be developed once a
  cost source exists (§8.3) — not approved in Phase 3A.

Until those approvals, no Phase 3B build starts and no interim calculations
are produced.
