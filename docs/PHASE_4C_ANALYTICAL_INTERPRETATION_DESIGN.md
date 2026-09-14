# Phase 4C — Analytical Interpretation Design

> `DESIGN ONLY — DRAFT, NOT APPROVED, NOT FROZEN`
>
> No source data is modified, no frozen processed artifact is modified,
> no existing scenario-generation script is modified, no new scenario
> calculation is created, and no dashboard, UI, chart, or application is
> built by this document. Every figure discussed is either an observed
> historical fact, a derived reference, a modeled estimate conditional on
> the frozen benchmark structure, or hypothetical arithmetic sensitivity
> under stated assumptions. Nothing here is a forecast, a demand
> statement, evidence about what would have sold, a causal estimate, or a
> pricing recommendation.

## 1. Purpose

### 1.1 Purpose of this phase

This document designs how the existing frozen Margin Map outputs are to
be read and converted into business analysis, without computing anything
new. It answers the bounded question:

> What business questions can Margin Map responsibly answer using the
> existing baseline data and frozen discount-sensitivity scenarios?

Design authority: `README.md`; `docs/FINANCIAL_MODEL.md`;
`docs/KPI_DICTIONARY.md`; `docs/COGS_MODEL.md`;
`docs/COGS_DATA_DICTIONARY.md`; `docs/COST_TO_SERVE_MODEL.md`;
`docs/COST_TO_SERVE_DATA_DICTIONARY.md`;
`docs/PHASE_2B_DATA_MODEL.md`; `docs/PHASE_2B_CONTRIBUTION_MODEL.md`;
`docs/PHASE_2C_PROFITABILITY_ANALYSIS.md`;
`docs/PHASE_3A_DISCOUNT_PRICING_ARCHITECTURE.md`;
`docs/PHASE_3B_DISCOUNT_ANALYSIS.md`; `docs/PHASE_3B_DECISION_LOG.md`;
`docs/PHASE_3B_VALIDATION.md`; `docs/PHASE_3B_FREEZE.md`;
`docs/PHASE_4A_PRICING_SCENARIO_ARCHITECTURE.md`;
`docs/PHASE_4A_DECISION_LOG.md`;
`docs/PHASE_4A_ARCHITECTURE_VALIDATION.md`; `docs/PHASE_4A_FREEZE.md`;
`docs/PHASE_4B_DECISION_LOG.md`;
`docs/PHASE_4B_IMPLEMENTATION_CONTRACT.md`;
`docs/PHASE_4B_IMPLEMENTATION.md`; `docs/PHASE_4B_FREEZE.md`;
`docs/PHASE_4B_DESIGN_DISCOUNT_INCREASE.md`;
`docs/PHASE_4B_DISCOUNT_INCREASE_FREEZE.md`;
`docs/PHASE_4B_DESIGN_DISCOUNT_DECREASE.md`;
`docs/PHASE_4B_DISCOUNT_DECREASE_FREEZE.md`; the frozen quality JSON
files `data/processed/phase3b_quality_report.json`,
`data/processed/phase4b_scenario_quality.json`,
`data/processed/phase4b_scenario_increase_0.00_quality.json`, and
`data/processed/phase4b_scenario_decrease_0.00_quality.json`; and the
inspected schemas of `data/processed/fact_margin_map_phase2.csv`
(9,994 lines, 49 columns),
`data/processed/order_margin_map_phase2.csv` (5,009 orders, 10 columns),
and `data/processed/fact_sales_cogs.csv`. Project scripts were inspected
read-only to understand outputs only.

### 1.2 Four stages distinguished

| Stage | What it is | Where it lives | Standing in this document |
|---|---|---|---|
| Data preparation | Build of reproducible facts: source audit, product grain, modeled COGS from benchmarks, observed freight join, return-status crosswalk, order-level contribution authority, quarantines, determinism, hash protection | Phases 1–2 (frozen) | Cited as lineage, never restated or altered |
| Scenario generation | Closed-form restatement of frozen transactions under stated hypothetical discounts with stated assumptions held fixed; adds `hypothetical_*` and variance columns beside frozen baseline columns; enforces fail-loud validation | Phase 4B slices (frozen): uniform replacement at stated rate 0.10; discount increase identity at 0.00; discount decrease identity at 0.00 | Cited as source artifacts with their validation standing; no new scenario is specified |
| Analytical interpretation | Definition of what may be read from the frozen baseline and frozen scenario artifacts, at which grain, with which metric, under which wording, and with which limitation | This Phase 4C design (draft, not approved, not frozen) | The only work authorized by this document |
| Future presentation or dashboard work | Any table, visual, or business-facing display built from approved interpretations under Gate 10 display rules | Separately gated future work; not authorized here | Explicitly out of scope (§11); this document specifies interpretation only and designs no visual |

Interpretation consumes frozen outputs; it never recomputes them, never
re-bands them, never re-aggregates them by a different rule, and never
merges observed and hypothetical values into a single unexplained number.

## 2. Analytical Scope

This phase may analyze only the following, using existing frozen outputs.
Anything not listed here is out of scope (§11).

### 2.1 Baseline contribution and margin

Authoritative baseline contribution profit (565,116.9418) and
contribution margin (24.6002%, SUM/SUM) from
`order_margin_map_phase2.csv` and reconciled Phase 3B ORDER-basis rows.
Source artifact: `order_margin_map_phase2.csv`;
`data/processed/discount_band_summary.csv` (ORDER basis);
`data/processed/discount_order_summary.csv`;
`data/processed/discount_segment_summary.csv` (ORDER basis).
Interpretation is conditional on the modeled cost structure and on
return/support OFF. Zero means scenario-excluded, never actual cost.

### 2.2 Observed discount behavior

Recorded discount rates as stored (observed range [0, 0.80]; 12 discrete
values; zero NULLs), reconstructed gross revenue, discount amount,
weighted-average discount (WAD), and realization rate, as defined in
`FINANCIAL_MODEL.md` §4 and Phase 3A §3. Source artifacts: Phase 3B
summaries listed in §2.1 plus `discount_category_summary.csv`,
`discount_subcategory_summary.csv` (gross-only). Gross revenue and
discount amount are derived references, never observed list prices.

### 2.3 Discount-band comparisons

Descriptive comparisons across the frozen six-band structure
(B0 `d = 0`; B1 `(0, 0.15]`; B2 `(0.15, 0.25]`; B3 `(0.25, 0.35]`;
B4 `(0.35, 0.55]`; B5 `(0.55, 0.80]`) on the ORDER basis using baseline
order-WAD bands (D3B-03 rule), and LINE-basis companion rows where the
`basis` marker so states. Band counts are frozen: lines
B0 4,798 / B1 146 / B2 3,657 / B3 254 / B4 283 / B5 856; orders
B0 2,055 / B1 415 / B2 1,634 / B3 278 / B4 274 / B5 353. Comparisons are
descriptive associations, never measured effects (§6, §9).

### 2.4 Scenario contribution changes

Absolute hypothetical-minus-baseline contribution differences at TOTAL
and per baseline band, read from the frozen scenario CSVs:
`phase4b_scenario_uniform_0.10.csv` (verified instance: baseline
565,116.94 → hypothetical 660,523.18; variance +95,406.24; margin change
+1.03pp); `phase4b_scenario_increase_0.00.csv` (identity, variances
zero); `phase4b_scenario_decrease_0.00.csv` (identity, variances zero).
Each figure is arithmetic sensitivity under the stated assumptions
recorded on the row (§5).

### 2.5 Scenario contribution variance

Variance arithmetic as stored (`variance_contribution_profit`,
`margin_change_pp`), reconciled both ways per the quality evidence
(max gap ≤ 1e-9; freight variance exactly 0). Relative variance
(`Variance % = (Actual − Comparison) / Comparison × 100`) may be shown
only where the comparison (baseline) value is nonzero; where the
comparison is zero the relative form is NULL/blank and only the absolute
variance is reported (per `FINANCIAL_MODEL.md` §9). Margin changes are
reported in percentage points only.

### 2.6 Scenario revenue and cost components

Net-revenue change (`variance_net_revenue`), discount-amount change
(`variance_discount_amount`), COGS change (`variance_cogs`), gross-profit
change (`variance_gross_profit`), and freight / cost-to-serve variance
(`variance_freight`, `variance_cost_to_serve`, both zero by passthrough).
COGS is read under the frozen revenue-based rule
(`hypo_cogs = hypo_net × modeled_cogs_pct / 100`) with the constancy
disclosure (§5). Freight is read as observed passthrough (§5).

### 2.7 Order-level aggregation

Bottom-up order aggregation discipline: line hypotheticals roll to orders
by SUM; order freight is the authoritative joined value (which already
holds the 25.05 ambiguous-pair total; full affected-order freight 26.55
on order `US-2014-150119`); contribution reporting is authoritative at
order grain and above. Frozen scenario artifacts report at Order ×
Discount Band (6 band rows + TOTAL = 7 rows × 52 columns); they do not
contain order-level hypothetical rows and must not be disaggregated into
fabricated order-level hypotheticals (§8).

### 2.8 Quantity and order-volume context

Observed quantity (frozen total 37,873), line counts, order counts,
quantity per order, and quantity per line as co-occurrence context
beside financial measures. Quantities are reused bit-identical in every
scenario (quantity-constant check PASS in all three quality JSON files).
Band-level quantity contrasts compare different order compositions
(e.g. multi-line mixed B1 orders) and isolate no discount influence
(Phase 3B §4 reading).

### 2.9 Freight pass-through context

Observed freight (project total 238,173.79) passed through unchanged in
every scenario; ambiguous pair (2 lines, `US-2014-150119`) NULL and
flagged at line grain under all scenarios with the 25.05 pair total
entering only through order aggregation. Line-grain contribution is
partial by the stated gap (200.0476) beside — never instead of — the
authoritative order total. No freight allocation below order grain, no
imputation, no invented rate.

### 2.10 Quality and validation status

Validation standing travels with every reading: Phase 3B 16/16 PASS;
uniform-replacement 15/15 PASS; increase identity 22/22 PASS; decrease
identity 22/22 PASS; determinism (byte-identical reruns, SHA-256
recorded); frozen-input hash integrity (hashes in §10); quarantine
exclusion; OFF assertions; flag columns (`low_sample_flag`,
`ambiguity_note`, `negative_contribution_flag`, `N/A`-with-reason for
`fixed_unit_cost_view` and `demand_response_view`). No interpretation is
approved on an artifact whose checks do not pass.

## 3. Business Questions

A limited set of answerable questions follows. Each entry states the six
required fields. All questions are answerable from frozen artifacts only.
No question asks for a prediction about future transactions, a claim
about what a discount change would cause, a selection of best discounts,
an estimate of demand response, or any return/support/segmentation
modeling.

### BQ-01 — What is the baseline contribution position overall?

- Business question: What contribution profit and contribution margin did
  the observed transactions generate under the frozen modeled cost
  structure with return/support OFF?
- Required data or artifact: `order_margin_map_phase2.csv` (10 columns,
  5,009 orders); `discount_band_summary.csv` TOTAL row (ORDER basis);
  `phase3b_quality_report.json` (16/16 PASS).
- Required metric: `order_contribution_profit` SUM (565,116.9418);
  `order_contribution_margin_pct` SUM/SUM (24.6002%); companions: net
  revenue 2,297,200.86; modeled COGS 1,493,910.13; freight 238,173.79;
  quantity 37,873; order count 5,009; line count 9,994.
- Appropriate aggregation level: Overall TOTAL (order grain rolled up;
  authoritative).
- Expected interpretation: A single conditional baseline statement, e.g.
  "Observed transactions generated 565,116.94 contribution at 24.60%
  margin under frozen benchmarks with freight observed and
  return/support excluded." The margin is SUM/SUM; no averaging of
  percentages.
- Important limitation: All margins are conditional on the revenue-based
  modeled COGS structure; zero return/support means excluded, not
  actual; quarantined source Profit plays no role; freight methodology
  caveat from Phase 2 carries over.

### BQ-02 — How is baseline contribution distributed across observed discount bands?

- Business question: How do net revenue, freight, contribution profit,
  and contribution margin compare across the six frozen baseline
  order-WAD bands?
- Required data or artifact: `discount_band_summary.csv` ORDER-basis
  band rows (B0–B5) plus TOTAL; `phase3b_quality_report.json`.
- Required metric: Per band: net revenue (SUM), discount amount (SUM),
  WAD, realization rate, modeled gross profit/margin (conditional),
  freight (SUM), contribution profit (SUM), contribution margin
  (SUM/SUM), order/line counts, quantity, negative-contribution order
  counts. Frozen reference values per Phase 3B §4 (e.g. B0 220,993.53 at
  25.63% on 2,055 orders; B2 156,514.93 at 23.39% on 1,634 orders; B5
  15,361.88 at 24.82% on 353 orders; authoritative band margins span
  22.98%–26.42%).
- Appropriate aggregation level: Overall × discount band, ORDER basis
  (authoritative contribution).
- Expected interpretation: Descriptive share and level reading, e.g.
  "The no-discount band holds the largest observed contribution share
  (39.11% of baseline contribution on 37.54% of net revenue), followed
  by the standard-discount band; the deep-discount band holds 2.69% of
  net revenue and 2.72% of contribution at 29.34% realization." State the
  `basis` on every figure.
- Important limitation: Cross-band differences combine benchmark mix,
  freight incidence, and order composition; they are not attributed to
  the discount level; within-benchmark-group gross margins are constant
  across bands by model construction; no causal reading is licensed.

### BQ-03 — Where does profitable and unprofitable revenue sit in the baseline?

- Business question: How much baseline revenue and contribution sit in
  negative-contribution orders, and how are those orders distributed
  across bands?
- Required data or artifact: `discount_order_summary.csv` (5,009 rows,
  `negative_contribution_flag`); `discount_band_summary.csv` ORDER-basis
  `neg_contribution_orders` column (B0 14 / B1 3 / B2 24 / B3 1 / B4 3 /
  B5 5; TOTAL 50); customer summary for the zero-loss-customer context
  (0 of 793 negative, conditional on OFF baseline).
- Required metric: Count and share of negative-contribution orders;
  revenue and contribution attributable to those orders (SUM, not
  averaged); per-band negative-order counts.
- Appropriate aggregation level: Order grain for identification; Overall
  × band for distribution; customer TOTAL only for the disclosed
  aggregation context (no within-customer band comparison).
- Expected interpretation: Visibility statement preserving grain
  asymmetry, e.g. "50 orders are contribution-negative and remain summed
  into every aggregate; no customer total is negative under the OFF
  baseline because aggregation absorbs those orders." Line-grain
  negative counts (109 lines; 0 negative-gross-profit lines,
  structurally guaranteed) may be stated beside — never merged with —
  order counts.
- Important limitation: The zero-loss-customer observation is conditional
  on scenarios OFF and on freight-only serve costs; loss visibility
  awaits separately approved cost layers which do not exist; return
  status is filter context only and identifies no returned line.

### BQ-04 — What is the arithmetic sensitivity of contribution to a uniform 0.10 replacement?

- Business question: If recorded discounts on all valid lines had instead
  been 0.10 with quantity, modeled-COGS percentages, freight, and
  return/support held as stated, what would the arithmetic revenue,
  modeled gross profit, and contribution figures have been beside the
  baseline?
- Required data or artifact: `phase4b_scenario_uniform_0.10.csv`
  (7 rows × 52 columns; Order × Discount Band on baseline bands, ORDER
  basis); `phase4b_scenario_quality.json` (15/15 PASS; determinism and
  frozen-hash evidence).
- Required metric: TOTAL and per-baseline-band: `base_contrib` vs
  `hypo_contrib`; `variance_contribution_profit` (absolute); relative
  variance where baseline nonzero; `margin_change_pp`;
  `variance_net_revenue`; `variance_discount_amount`;
  `variance_cogs`; `variance_freight` (= 0);
  `variance_cost_to_serve` (= 0); `base_wad` vs `hypo_wad`; quantity
  (unchanged, 37,873). Verified TOTAL: baseline 565,116.94 →
  hypothetical 660,523.18 (variance +95,406.24, +1.03pp).
- Appropriate aggregation level: TOTAL for the headline sensitivity;
  baseline-band rows for exposure distribution; ORDER basis only.
- Expected interpretation: Conditional restatement, e.g. "Under stated
  rate 0.10 with constant quantity, frozen COGS percentages, freight
  passthrough, and return/support OFF, arithmetic contribution restates
  95,406.24 higher (+1.03pp) — a quantification of exposure under the
  stated discount configuration, not evidence about what would have
  sold." Baseline, hypothetical, and variance blocks are shown
  separately with the assumption labels on the reading.
- Important limitation: Constant-quantity label must survive on every
  figure; gross-margin-percentage constancy is a model consequence, not
  a cost finding; freight variance of zero reflects passthrough design,
  not a finding about movement costs; `fixed_unit_cost_view` and
  `demand_response_view` are `N/A` with reasons and must travel with the
  reading.

### BQ-05 — Do the zero-change identity scenarios reconcile to the baseline?

- Business question: Do the discount-increase 0.00 and discount-decrease
  0.00 slices reproduce the baseline exactly, confirming pipeline
  integrity?
- Required data or artifact:
  `phase4b_scenario_increase_0.00.csv` + its quality JSON (22/22 PASS);
  `phase4b_scenario_decrease_0.00.csv` + its quality JSON (22/22 PASS).
- Required metric: `variance_net_revenue` (= 0.0);
  `variance_contribution_profit` (= 0.0); COGS identity; freight both
  sides 238,173.79 with freight variance exactly 0; margin change 0.0pp;
  counts 9,994 lines / 5,009 orders / quantity 37,873; band counts
  B0=2055 | B1=415 | B2=1634 | B3=278 | B4=274 | B5=353.
- Appropriate aggregation level: TOTAL (reconciliation) with band-row
  confirmation (7 rows).
- Expected interpretation: Integrity confirmation only, e.g.
  "The 0.00 increase and 0.00 decrease slices restate the baseline
  bit-identically with zero variances — the pipeline-validation case
  passes; no economic sensitivity is measured by an identity run."
- Important limitation: Identity runs authorize no statement about
  nonzero increases or decreases; any positive universal pp increase
  breaches 0.80 on lines already at 0.80 (300 lines; the 0.05 increase
  fails by design with no valid output); any positive universal pp
  decrease breaches 0.00 on zero-discount mass (4,798 lines; the 0.05
  decrease fails by design with 4,798 violations and no valid output).
  Failed runs leave no valid CSV behind and must not be interpreted.

### BQ-06 — How do quantity and order volume co-occur with discount bands?

- Business question: What quantity per order, quantity per line, line
  counts, and order counts are observed within each baseline band,
  as compositional context for financial readings?
- Required data or artifact: `discount_band_summary.csv` (ORDER and LINE
  bases, kept separate); `discount_order_summary.csv` for order WAD
  median context (median 0.1607, mean 0.1606).
- Required metric: Per band: line count, order count, quantity (SUM),
  quantity per order, quantity per line (ORDER basis: 6.71 B0 / 12.18 B1
  / 6.69 B2 / 10.47 B3 / 10.26 B4 / 6.74 B5 against 7.56 overall; LINE
  basis: 6.91 B0 / 4.08 B1 / 5.68 B2 / 4.08 B3 / 4.22 B4 / 4.89 B5).
  Include the B1 composition note (415 B1 orders contain 1,324 lines,
  3.19 per order, predominantly zero- and 0.20-discount lines whose
  average falls in the low band).
- Appropriate aggregation level: Overall × band, with `basis` stated per
  figure; never mixed in one average.
- Expected interpretation: Compositional note, e.g. "B1 at order grain
  is predominantly multi-line mixed orders; band-level quantity
  contrasts therefore compare different order compositions." No discount
  influence is isolated.
- Important limitation: Quantity descriptives are co-occurrence only;
  thresholds and flag discipline apply; no response parameter is
  estimated and none may be inferred from these contrasts.

### BQ-07 — How does freight co-occur with discount bands at order grain?

- Business question: What observed freight sits under each baseline
  discount band, and how does it participate in the band contribution
  arithmetic?
- Required data or artifact: `discount_band_summary.csv` ORDER-basis
  freight column (B0 84,314.69 / B1 36,145.63 / B2 73,110.88 /
  B3 19,429.93 / B4 18,744.49 / B5 6,428.17; TOTAL 238,173.79);
  scenario variance columns confirming freight variance zero.
- Required metric: Freight SUM per band; freight per order (derived
  SUM/count for context only, labeled as such); contribution profit and
  margin beside freight on the same band row.
- Appropriate aggregation level: Overall × band, ORDER basis
  (authoritative); LINE-basis freight is partial and shown only with the
  gap stated.
- Expected interpretation: Joint-effect reading, e.g. "Band contribution
  reflects benchmark mix and observed freight jointly within the band."
  Scenario freight variance of zero is read as passthrough design.
- Important limitation: Freight methodology caveat from Phase 2 carries
  over (observed field, methodology unverified); ambiguous pair
  preserved (NULL/flagged at line grain; 25.05 via order aggregation
  only); no per-mode charge, handling cost, or ticket cost exists as a
  default.

### BQ-08 — What is the validation standing before any figure is used?

- Business question: Are the source artifacts, counts, reconciliations,
  bounds, flags, and determinism in the state this design requires
  before any analytical output is approved?
- Required data or artifact: The four quality JSON files (§2.10) with
  check IDs, expected/actual/status; CSV row counts (Phase 3B: 14 / 39 /
  19 / 69 / 3,304 / 5,009 / 5,925; Phase 4B: 7 rows × 52 columns each);
  frozen SHA-256 hashes (§10).
- Required metric: Pass/fail per check; row/order/quantity totals;
  reconciliation gaps against tolerances (dual-form ≤ 1e-6; variance ≤
  1e-9; source-total 0.05); bound conformance ([0, 1) observed /
  [0, 0.80] hypothetical); NULL preservation (2 NULLs); flag presence.
- Appropriate aggregation level: Artifact level (per file), then TOTAL
  row.
- Expected interpretation: Gate reading, e.g. "Artifact X passes N/N
  checks with counts reconciled and hashes matching — eligible as an
  interpretation source" or "Artifact Y fails — no interpretation is
  licensed from it." Unsupported metrics read as `N/A` with reason.
- Important limitation: Quality evidence validates arithmetic and
  lineage; it does not validate any behavioral, predictive, or causal
  reading — such readings remain forbidden regardless of check status.

## 4. Baseline Analysis

Baseline interpretation uses frozen Phase 1A definitions verbatim; no
new financial definition is introduced. Where a derived form is shown,
its lineage label travels with it.

### 4.1 Net sales

`Net Revenue = Sales` (authoritative revenue measure; source Sales
already reflects the recorded discount). Aggregate by SUM. Frozen TOTAL:
2,297,200.86 (stated as 2297200.8603 in full precision). Reconciles to
SUM(`sales`) exactly. Never subtract discount again. Never use gross
revenue as the revenue denominator for margins.

### 4.2 Cost of goods sold

Authoritative modeled COGS: `modeled_cogs = sales × modeled_cogs_pct /
100` per line, where `modeled_cogs_pct = 100 − benchmark_gross_margin_pct`
from `product_cogs_assumptions.csv` via the sub-category benchmark
structure (frozen Phase 1C-3). Frozen TOTAL: 1,493,910.13 (stated as
1493910.1285 in full precision). COGS is a product-cost layer kept
separate from cost-to-serve at all times. `implied_modeled_cogs_per_unit`
(`modeled_cogs / quantity`) is a derived reference that varies with
price/discount by construction; it is never presented as an actual
procurement cost and never drives COGS.

### 4.3 Contribution

`Contribution Profit = Net Revenue − COGS − Freight Cost − Return Cost
− Support Cost`, equivalently `Gross Profit − Total Cost-to-Serve`,
both forms reconciled. In the frozen baseline, return and support terms
are OFF (0): `order_cost_to_serve = order_freight + 0 + 0`;
`order_contribution_profit = order_revenue − order_cogs −
order_cost_to_serve`. Frozen authoritative TOTAL: 565,116.9418 (order
fact; ORDER-basis Phase 3B TOTAL identical within 0.05). Line-grain SUM
(564,916.89) trails by the stated 200.0476 gap — correct NULL
propagation for the ambiguous pair, reported beside the authoritative
total, never presented as the project total.

### 4.4 Contribution margin

`Contribution Margin % = Contribution Profit / Net Revenue × 100`
(SUM/SUM on aggregates; never an average of percentages). Frozen
authoritative overall: 24.6002% (reported as 24.60%). NULL/blank when
net revenue is zero (none observed, guard retained). Margin changes
reported in percentage points. Denominator is always net revenue, never
gross revenue.

### 4.5 Discount percentage

Source field `Discount` as decimal (0.20 = 20%); multiply by 100 for
display only, never inside calculations. Valid observed range [0, 1);
observed [0, 0.80]; zero NULLs. Aggregate intensity only as WAD
(`SUM(discount_amount) / SUM(gross_revenue)`, equivalently
`1 − SUM(net)/SUM(gross)`); never an arithmetic mean of rates. Frozen
overall WAD: 0.1979 (realization 80.21%).

### 4.6 Freight

Observed line Shipping Cost joined from Dataset 1-US (US total
238,173.79; 9,992 `MATCHED_UNIQUE`, 2 `MATCHED_AMBIGUOUS` on rows
3406/3407 in order `US-2014-150119`; never imputed; 25.05 pair total via
order aggregation only; full affected-order freight 26.55). At line
grain: `cost_to_serve = freight_cost_observed + 0 + 0` (NULL where
freight NULL). At order grain: authoritative `order_freight` joined,
never recomputed. Freight appears exactly once per line (direct join;
no allocation below order grain).

### 4.7 Order-level contribution

Authoritative contribution grain is the order built bottom-up from its
lines (`order_margin_map_phase2.csv`, one row per order; all orders
verified single-segment and single-customer so order-basis attribution
is clean). Per-order fields joined read-only: `order_revenue`,
`order_cogs`, `order_freight`, `order_cost_to_serve`,
`order_contribution_profit`, `order_contribution_margin_pct`, plus
line-derived rollups (order WAD, band, quantity, line count) and
`return_status` as filter context only. Fifty orders carry
`negative_contribution_flag = TRUE`; zero orders are gross-negative at
the modeled layer; the single UNKNOWN-return order (`CA-2015-102015`)
is never defaulted.

### 4.8 Discount-band comparisons

Band comparisons read ORDER-basis authoritative rows with LINE-basis
companion rows labeled partial (`LINE_PARTIAL_EXCL_AMBIGUOUS`) beside —
never instead of — the ORDER rows. Category, sub-category, and product
cuts are gross-profit-only (contribution NULL with reason
`FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN`); their within-group gross
margins restate benchmark × mix by construction (Furniture 40.00% and
Office Supplies 38.00% in every occupied band; Technology bands move
only with sub-category mix) and are labeled accordingly. Office Supplies
has no observed lines in B3/B4 (structurally absent rows, not zeros);
sub-category file holds 52 occupied cells of 102 possible. Every
comparative sentence uses observed/associated-with/descriptive
language and carries the modeled-structure condition.

## 5. Scenario Analysis

All three comparisons below share the frozen mechanics: line
application (`d'` per line), closed-form hypothetical revenue holding
quantity constant, frozen modeled-COGS percentages, observed freight
passthrough, return/support OFF, bottom-up order aggregation, reporting
on baseline bands (never re-banded), six-block schema with
`hypothetical_*` naming, `N/A`-with-reason for unlicensed metrics, and
fail-loud validation. Every result is arithmetic sensitivity and must
not be presented as predicted customer or business behavior.

### 5.1 Baseline versus uniform replacement (stated rate 0.10)

- Absolute contribution variance: `variance_contribution_profit =
  hypo_contrib − base_contrib` per band and TOTAL; verified TOTAL
  +95,406.24 (660,523.18 − 565,116.94). Reconciled both ways (gap ≤
  1e-9).
- Relative contribution variance, where valid: `(hypo − base) / base ×
  100` per band and TOTAL, shown only where baseline contribution is
  nonzero; NULL/blank where baseline is zero (absolute variance still
  reported). Computed from frozen currency columns at read time; never
  averaged from percentages.
- Net-sales change: `variance_net_revenue` per band and TOTAL (SUM of
  line `gross × (1 − 0.10) − sales` rolled bottom-up).
- Discount change: observed `discount` vs `hypothetical_discount = 0.10`
  per line; WAD `base_wad` vs `hypo_wad` per band; discount-amount change
  `variance_discount_amount` (gross − hypo_net vs gross − sales).
- COGS treatment: `hypo_cogs(line) = hypo_net × modeled_cogs_pct / 100`
  using the frozen line percentage (never from order currency); order
  rollup reconciled to the authoritative order fact (gap 1.82e-12 in
  quality evidence). On-output constancy statement required: holding the
  benchmark fixed makes hypothetical gross-margin percentage constant by
  construction while currency moves with revenue.
- Freight treatment: observed freight carried unchanged per line (values
  identical, 2 NULLs, flags unchanged); `hypo_cts(order) =
  order_freight + 0 + 0`; `variance_freight = 0` exactly;
  `variance_cost_to_serve = 0` exactly.
- Quantity treatment: observed quantities reused bit-identical (line +
  order totals 37,873, asserted); every quantity-dependent figure labeled
  conditional on fixed quantities.
- Standing: arithmetic sensitivity under the stated assumptions recorded
  on the row (`CONSTANT_OBSERVED_QUANTITY`,
  `FROZEN_MODELED_COGS_PCT`, `OBSERVED_PASSTHROUGH`, `OFF`,
  `HYPOTHETICAL_ARITHMETIC_SENSITIVITY_NOT_A_FORECAST`). It is not a
  behavioral forecast, not evidence about what would have sold, not a
  causal estimate, and not a pricing recommendation.

### 5.2 Baseline versus discount increase (identity at 0.00)

- Absolute contribution variance: zero on every band and TOTAL
  (`variance_contribution_profit = 0.0`); baseline contribution
  565,116.9418 = hypothetical contribution.
- Relative contribution variance, where valid: 0% where baseline nonzero
  (identity arithmetic); NULL/blank only under the general zero-baseline
  rule (§2.5), not breached here.
- Net-sales change: zero (`variance_net_revenue = 0.0`; baseline net
  2,297,200.8603 = hypothetical net).
- Discount change: `d'(line) = round6(round6(d) + 0.00)`, so
  `hypo_wad = base_wad` per band; `variance_discount_amount = 0.0`.
- COGS treatment: same frozen-percentage rule as §5.1
  (`hypo_net × modeled_cogs_pct / 100`); baseline COGS 1,493,910.1285 =
  hypothetical COGS (identity); constancy disclosure still travels with
  the reading.
- Freight treatment: identical passthrough as §5.1; freight 238,173.79
  both sides; freight variance exactly 0.
- Quantity treatment: identical constancy as §5.1 (37,873 bit-identical).
- Standing: arithmetic identity sensitivity (pipeline-validation case),
  not a measurement of any increase effect. No nonzero universal
  increase has a valid output: the illustrative 0.05 increase fails
  loudly because 300 valid lines already at observed 0.80 would exceed
  the 0.80 bound — whole-run rejection with diagnostics, no clipping, no
  partial-subset execution, no CSV treated as valid. That failure is the
  designed bound behavior, not a defect, and authorizes no imputed
  sensitivity figure.

### 5.3 Baseline versus discount decrease (identity at 0.00)

- Absolute contribution variance: zero on every band and TOTAL
  (`variance_contribution_profit = 0.0`); baseline = hypothetical on all
  currency blocks.
- Relative contribution variance, where valid: 0% where baseline nonzero;
  NULL/blank only under the general zero-baseline rule.
- Net-sales change: zero (`variance_net_revenue = 0.0`).
- Discount change: `d'(line) = round6(round6(d) − 0.00)`, so
  `hypo_wad = base_wad`; `variance_discount_amount = 0.0`.
- COGS treatment: same frozen-percentage rule; baseline = hypothetical;
  constancy disclosure travels with the reading.
- Freight treatment: identical passthrough; freight variance exactly 0;
  ambiguous-pair NULL/flag preservation verified (PASS).
- Quantity treatment: identical constancy (37,873 bit-identical).
- Standing: arithmetic identity sensitivity (pipeline-validation case),
  not a measurement of any decrease effect. No positive universal
  decrease has a valid output: the illustrative 0.05 decrease fails
  loudly because 4,798 observed zero-discount lines would fall below
  0.00 (minimum `d' = −0.050000`) — whole-run rejection with violating
  counts and sample identifiers diagnostically, no CSV treated as valid.
  Failed runs leave only the 0.00 artifacts; no sensitivity figure may
  be imputed from a failed run or its diagnostic.

### 5.4 Shared reading discipline for all three comparisons

Hypothetical values are named as hypothetical everywhere
(`hypo_*`/`hypothetical_*` or equivalent unambiguous labeling); the
four layers (observed baseline; stated assumptions with input values;
hypothetical outputs; unsupported-assumption flags where applicable)
are never merged. Margins aggregate SUM/SUM with changes in percentage
points. Quarantined source Profit is referenced in zero computations.
Permitted wording is limited to forms such as "illustrative
constant-quantity scenario", "arithmetic change under the stated
assumptions", "modeled result conditional on the selected cost
structure", "observed baseline beside the hypothetical restatement",
and "conditional illustration, not a forecast". Any reading that could
invite a behavioral or predictive interpretation carries the standing
caveat on the reading itself.

## 6. Discount-Band Analysis

### 6.1 Band construction basis

Fixed, value-based intervals on the recorded discount rate, adopted
unchanged after passing all Phase 3A §4.4 gates (D3B-01): B0 `d = 0`
(4,798 lines; exact zero group preserved as the reference cohort); B1
`(0, 0.15]` (0.10, 0.15; 146 lines); B2 `(0.15, 0.25]` (0.20; 3,657
lines); B3 `(0.25, 0.35]` (0.30, 0.32; 254 lines); B4 `(0.35, 0.55]`
(0.40, 0.45, 0.50; 283 lines); B5 `(0.55, 0.80]` (0.60, 0.70, 0.80; 856
lines). Full observed range [0, 0.80] covered with no gaps and no
overlaps; no observed discrete value split across bands; 12 discrete
policy-like mass points pooled as documented so no overall band rests on
fewer than ~140 lines. Order bands use the single D3B-03 rule
(`order_wad = SUM(line discount_amount) / SUM(line gross_revenue)`,
banded with the same B0–B5 boundaries; all 5,009 orders exactly one
band). No quantile comparator was built (D3B-04).

### 6.2 Order-level versus line-level distinction

Line bands group lines by their own recorded discount; order-WAD bands
group orders by the revenue-weighted average of their lines' discounts.
The 415 B1 orders illustrate the difference: 1,324 lines (3.19 per
order), predominantly zero- and 0.20-discount lines whose average falls
in the low band; B3 orders likewise span line discounts 0.00–0.80.
ORDER-basis rows carry authoritative contribution (joined order freight
inclusive of the 25.05 pair total); LINE-basis rows carry explicitly
labeled partials beside — never instead of — ORDER rows, with the
200.0476 gap stated. The `basis` column must be honored in every reading;
  the two bases must never be mixed in one average.

### 6.3 Why the bands must not be reconstructed differently

Band boundaries live as versioned constants proven by deterministic
re-execution (identical counts across runs) and by 16/16 Phase 3B checks
plus the order-band check inherited in every Phase 4B quality file
(B0=2055 | B1=415 | B2=1634 | B3=278 | B4=274 | B5=353). Scenario
reporting groups hypothetical values by baseline bands (frozen
`assign_band` boundaries unchanged; never re-banded by hypothetical
discounts) so the B0 reference cohort stays identifiable and
baseline-vs-scenario reconciliation stays exact. Any alternative
boundary, re-banding by `d'`, quantile cut, or per-reading regrouping
would break determinism, orphan the validation evidence, and strand the
flag and reconciliation discipline — it is therefore forbidden. A future
band change, if ever needed, requires its own documented approval and
re-validation; it must not enter as a silent reading choice.

### 6.4 Metrics that may be compared across bands

Across ORDER-basis bands: order/line counts, quantity (and quantity per
order as labeled context), gross revenue (SUM, derived), net revenue
(SUM), discount amount (SUM), WAD, realization rate, modeled gross
profit and gross margin (conditional), freight (SUM), cost-to-serve
(SUM), contribution profit (SUM), contribution margin (SUM/SUM),
negative-contribution order counts, and — for scenario readings —
hypothetical companions with absolute variances and pp margin changes.
Across LINE-basis bands: the same set with contribution explicitly
labeled partial. Across category/sub-category bands: gross-profit-only
measures with contribution NULL and the attributable-grain reason;
their margins are read as benchmark × mix restatement with the caveat
on the reading.

### 6.5 Small-volume or interpretation cautions

Every row carries `line_count` and `order_count` with
`low_sample_flag` under provisional thresholds 30 lines / 10 orders
(D3B-02; analytical thresholds, not statistical rules). Flag rates are
part of the reading: band file 0/14; segment file 0/39; category file
0/19 (2 cells structurally absent); sub-category file 10/69; customer
file 3,293/3,304 (782/793 TOTAL rows and 2,511/2,511 band rows flagged);
product file 5,925/5,925 (plus 93 `low_volume_flag` single-order
products). Thin cells are shown with flags, never suppressed or merged,
and described as arithmetic, not evidence. Comparative statements at
fully flagged grains (within-customer band detail; any product-level
discount comparison) are out of scope. Sparse discount values (0.10:
94; 0.15: 52; 0.32: 27; 0.45: 11 lines) must not be reported as
standalone segments.

### 6.6 Descriptive comparison versus causal explanation

Band readings describe historical patterns observed in transactions
conditional on the modeled cost structure (association language:
"observed", "associated with", "descriptive comparison", "historical
pattern"). Discount and quantity may each be affected by product,
customer, category, time, and other unrecorded factors; the dataset
contains no controlled discount experiments and no independently
observed pre-discount price history. No band contrast — however large —
is presented as proof that a discount level moved quantities, revenue,
or profit. Correlation-style summaries, if ever shown, are descriptive
association measures over confounded observational data with sample
sizes stated, never response parameters.

## 7. Metric Dictionary

Only metrics supported by existing project definitions and frozen outputs
appear below. Grain abbreviations: L = transaction line (`row_id`);
O = order (`order_id`); B = discount band; T = TOTAL. Units: CUR =
source currency (full float in files, rounded on display); DEC = decimal
rate; PP = percentage points; CT = count.

| Metric name | Definition | Formula or source | Grain | Unit | Interpretation | Limitation |
|---|---|---|---|---|---|---|
| Net revenue (Net sales) | Authoritative revenue; source Sales already net of discount | `Sales` (`FINANCIAL_MODEL.md` §4.1); SUM on aggregates | L → O/B/T | CUR | Historical revenue fact; denominator for all margins | Do not subtract discount again; never replace with gross |
| Gross revenue | Reference revenue before discount; reconstructed (no list-price field exists) | `sales / (1 − discount)`; NULL/blank if discount = 1; SUM on aggregates | L → O/B/T | CUR | Derived reference from which observed and hypothetical nets are both derived | Never presented as observed list price; label as derived |
| Discount amount | Revenue reduction associated with the recorded discount | `gross − net` (equiv. `gross × discount`; first form primary); SUM | L → O/B/T | CUR | Revenue forgone, not profit loss | Do not sum with Discount Leakage as an independent addend; profit effect passes through the waterfall |
| Discount % (recorded rate) | Recorded discount on the line as stored | Source field `discount` (decimal; ×100 display only) | L | DEC | Recorded pricing fact per line | Valid [0, 1); NULL/outside aborts; never average arithmetically |
| Weighted-average discount (WAD) | Revenue-weighted mean discount for an aggregate | `SUM(discount_amount) / SUM(gross)` (equiv. `1 − SUM(net)/SUM(gross)`; reconciled) | O/B/T | DEC | Discount intensity preserving revenue meaning | Never an arithmetic mean of rates; NULL/blank when aggregate gross is 0 |
| Discount amount as % of gross | Share of reference revenue absorbed by discount | `SUM(discount_amount) / SUM(gross) × 100` | O/B/T | % | Numerically identical to WAD × 100 for the same aggregate | Never summed with WAD or presented as an independent addend |
| Revenue realization rate | Share of reference revenue retained after discount | `SUM(net) / SUM(gross) × 100` (equiv. `100 − discount % of gross`) | O/B/T | % | Complement of discount absorption (e.g. 29.34% in B5) | NULL/blank when aggregate gross is 0 |
| Quantity | Observed units sold | Source field `quantity`; SUM; frozen total 37,873 | L → O/B/T | CT | Volume co-occurrence context | Reused bit-identical in scenarios; band contrasts compare compositions, isolate no influence |
| Quantity per order | Observed basket-size context for a band or TOTAL | `SUM(quantity) / DISTINCT order_id` within the cell (ORDER basis per Phase 3B §4; e.g. 6.71 B0 / 12.18 B1 / 6.69 B2 / 10.47 B3 / 10.26 B4 / 6.74 B5 against 7.56 overall) | O/B/T (ratio reported at band or TOTAL) | CT per order | Compositional context beside financial measures; B1 contrast flags multi-line mixed orders | Co-occurrence only; compares different order compositions; never a response measure; `basis` stated, never mixed across bases |
| Quantity per line | Observed line-size context for a band or TOTAL | `SUM(quantity) / COUNT row_id` within the cell (LINE basis per Phase 3B §4; e.g. 6.91 B0 / 4.08 B1 / 5.68 B2 / 4.08 B3 / 4.22 B4 / 4.89 B5) | L/B/T (ratio reported at band or TOTAL) | CT per line | Compositional context beside financial measures | Co-occurrence only; never a response measure; `basis` stated, never mixed across bases |
| Freight per order | Observed freight context per order for a band or TOTAL | `SUM(freight) / DISTINCT order_id` within the cell, labeled as derived context only | O/B/T (ratio reported at band or TOTAL) | CUR per order | Freight co-occurrence beside band contribution | Derived context, not a stored fact; freight methodology caveat carried; LINE-basis freight is partial (gap stated) |
| Order count / Line count | Distinct orders / lines in the cell | `DISTINCT order_id` / `COUNT row_id` | B/T | CT | Sample-size companion on every row | Part of the output, not an appendix; drives `low_sample_flag` |
| Modeled COGS | Product-cost estimate under frozen benchmarks | `sales × modeled_cogs_pct / 100` (baseline); `hypo_net × modeled_cogs_pct / 100` (hypothetical); SUM | L → O/B/T | CUR | Analytical estimate conditional on benchmark structure | Not historical accounting COGS; never treated as fixed unit cost |
| Modeled COGS % | Frozen product rate from benchmark structure | `100 − benchmark_gross_margin_pct` (`product_cogs_assumptions.csv`) | L (product rate) | % | Rate that travels read-only into scenarios | Margin-percentage constancy under this rule is arithmetic consequence, not a cost finding |
| Modeled gross profit | Profit after product cost only | `net − modeled_cogs`; `hypo_net − hypo_cogs` (hypothetical); SUM | L → O/B/T | CUR | Modeled layer above serve costs | Excludes serve costs; not contribution |
| Modeled gross margin % | Gross profit per unit of net revenue | `gross_profit / net × 100` (SUM/SUM); NULL/blank if net = 0 | O/B/T (sums) | % | Conditional margin restating benchmark × mix | Within-benchmark-group constancy across bands is by construction |
| Freight cost (observed) | Line Shipping Cost joined from Dataset 1-US | Direct carry-over of joined line value; US total 238,173.79 | L → O/B/T | CUR | Observed movement signal with methodology caveat | 2 lines NULL/flagged (ambiguity control); no allocation below order grain; no invented rates |
| Cost-to-serve | Total operational/service cost in the frozen baseline | `freight + 0 + 0` (return/support OFF); NULL if freight NULL; SUM | L → O/B/T | CUR | Freight-loaded serve layer under current settings | Zero means scenario-excluded, never actual cost |
| Contribution profit | Profit after product + serve costs | `net − modeled_cogs − cost_to_serve` (equiv. `gross_profit − serve`; both reconciled); SUM; authoritative at O and above | L (partial) / O/B/T (authoritative) | CUR | Core MarginMap profitability fact (baseline 565,116.9418) | Line SUM trails authoritative total by 200.0476 (held-at-order economics); customer TOTAL conditional on OFF baseline |
| Contribution margin % | Contribution per unit of net revenue | `contribution / net × 100` (SUM/SUM); NULL/blank if net = 0 | O/B/T (sums) | % | Executive margin after everything modeled so far (24.6002%) | Denominator net, never gross; changes in PP |
| Hypothetical net revenue | Scenario net under stated `d'` with quantity held fixed | `gross × (1 − d')` (equiv. `sales × (1 − d') / (1 − d)`; dual reconciled ≤ 1e-6) | L → O/B/T | CUR | Scenario-only value existing inside the named scenario | Exists only beside its baseline with assumption labels; never merged |
| Hypothetical discount amount | Scenario revenue forgone under `d'` | `gross − hypo_net`; SUM | L → O/B/T | CUR | Scenario discount absorption | Same hypothetical discipline as hypo net |
| Hypothetical COGS | Scenario product cost under frozen percentages | `hypo_net × modeled_cogs_pct / 100`; SUM | L → O/B/T | CUR | Scenario cost under default rule with constancy disclosure | Never worded as fixed-unit-cost behavior |
| Hypothetical contribution | Scenario waterfall on hypothetical inputs | `SUM(hypo_net) − SUM(hypo_cogs) − order_freight` per order; SUM above | O/B/T | CUR | Arithmetic scenario profit beside its baseline | Sole producible scenario profit claim; forecast and causal-impact readings forbidden |
| Absolute contribution variance | Hypothetical minus baseline contribution | `hypo_contrib − base_contrib`; reconciled both ways (≤ 1e-9) | B/T | CUR | Exposure difference under the stated configuration | Conditional illustration, not a measured effect |
| Relative contribution variance | Absolute variance scaled by baseline | `(hypo − base) / base × 100`; NULL/blank if base = 0 | B/T | % | Scale context for the absolute move | Shown only where baseline nonzero; never averaged |
| Margin change (contribution / gross) | Difference of SUM/SUM margins | `hypo_margin_pp − base_margin_pp` | B/T | PP | Margin restatement in percentage points | Never labeled "%"; never averaged from percentages |
| Negative-contribution flags/counts | Identification of loss observations where licensed | `negative_contribution_flag` per order; `neg_base_orders` / `neg_hypo_orders` per band; 50 / 109 / 0 at O/L/customer baseline | O/B | CT | Loss visibility preserved without averaging away | Product/category/sub-category negative-contribution counts NULL (not licensed) |
| Low-sample flag | Provisional thin-cell marker | TRUE when `line_count < 30` OR `order_count < 10` (D3B-02) | Every summary row | Flag | Reading posture: flagged cells are arithmetic, not evidence | Provisional analytical thresholds, not statistical rules; travel into any reuse |
| Unsupported-metric markers | Explicit unavailability with reason | `fixed_unit_cost_view = N/A (COMPARATOR_NOT_IN_INITIAL_BUILD)`; `demand_response_view = N/A (RESPONSE_NOT_ESTIMATED)` | Every scenario row | Label | Prevents silent omission or invention | Never estimated, never 0-filled, shown with reason |

No other metric (including any return-rate, handling-cost,
ticket-cost, response-coefficient, elasticity, or optimal-discount
measure) is defined here because none exists in frozen evidence.

## 8. Analytical Output Specification

Future analytical outputs are specified here without being implemented.
Each entry carries the ten required fields. No output is built by this
document. Unsupported constructs are marked as such rather than forced.

### AO-01 — Baseline performance summary

- Output name: Baseline performance summary (TOTAL).
- Business purpose: State the single authoritative baseline against which
  every band reading and every scenario variance is referenced.
- Source artifact: `order_margin_map_phase2.csv`;
  `discount_band_summary.csv` TOTAL row (ORDER basis);
  `phase3b_quality_report.json` (16/16 PASS).
- Grain: Overall TOTAL (order grain rolled up; authoritative).
- Dimensions: None (single TOTAL row; scenario layers OFF stated).
- Measures: Net revenue, modeled COGS, gross profit/margin (conditional),
  freight, cost-to-serve, contribution profit/margin, WAD, realization
  rate, quantity, order/line counts, negative-order count (50).
- Required filters, if any: None; return status shown only as cohort
  context where the frozen order file provides it (YES 296 / UNKNOWN 1 /
  remainder NOT_RETURNED), never as an adjustment.
- Expected insight: The conditional baseline in one place
  (2,297,200.86 / 1,493,910.13 / 238,173.79 / 565,116.94 at 24.60%,
  WAD 0.1979, quantity 37,873) with lineage and OFF labels.
- Validation requirement: TOTAL reconciles to the order fact within 0.05;
  counts 9,994 / 5,009 / 37,873; quarantine exclusion; OFF assertions;
  hash match; determinism on record.
- Known limitation: Conditional on benchmarks; freight caveat carried;
  zero return/support means excluded; quarantined Profit excluded.

### AO-02 — Contribution by discount band (observed)

- Output name: Contribution by discount band (observed, ORDER basis).
- Business purpose: Show where baseline revenue, freight, and
  contribution sit across observed discount configurations.
- Source artifact: `discount_band_summary.csv` ORDER-basis band rows
  (B0–B5) plus TOTAL; `phase3b_quality_report.json`.
- Grain: Overall × discount band, ORDER basis (authoritative); LINE-basis
  companion rows specified as a separate labeled block, never merged.
- Dimensions: Baseline band (B0–B5 + TOTAL) with `basis` marker.
- Measures: Per band: net/gross revenue, discount amount, WAD,
  realization, modeled gross profit/margin, freight, cost-to-serve,
  contribution profit/margin, quantity, order/line counts,
  negative-order counts, `low_sample_flag`, `ambiguity_note` where
  applicable.
- Required filters, if any: None; bands are baseline order-WAD bands only.
- Expected insight: Exposure distribution reading per BQ-02/BQ-03 (B0 and
  B2 dominance; narrow 22.98%–26.42% authoritative margin span as joint
  benchmark × freight effect; 50 negative orders distributed B0 14 / B2
  24 / others as stored).
- Validation requirement: Band rows reconcile to TOTAL; band order counts
  sum to 5,009; ORDER TOTAL equals 565,116.9418; LINE partial gap stated
  (200.0476); no averaging of percentages; flags preserved.
- Known limitation: Descriptive only; benchmark-constancy and composition
  caveats on the reading; no causal attribution.

### AO-03 — Scenario comparison (TOTAL: baseline beside hypothetical)

- Output name: Scenario comparison at TOTAL.
- Business purpose: State the headline arithmetic sensitivity for each
  frozen scenario instance beside the identical-scope baseline.
- Source artifact: `phase4b_scenario_uniform_0.10.csv` + its quality JSON
  `phase4b_scenario_quality.json` (15/15 PASS) for the uniform instance;
  `phase4b_scenario_increase_0.00.csv` + its quality JSON
  `phase4b_scenario_increase_0.00_quality.json` (22/22 PASS) for the
  increase identity instance; `phase4b_scenario_decrease_0.00.csv` + its
  quality JSON `phase4b_scenario_decrease_0.00_quality.json` (22/22 PASS)
  for the decrease identity instance. No other scenario artifact is a
  source for this output.
- Grain: Overall TOTAL (order economics rolled up; authoritative).
- Dimensions: Scenario instance (`uniform_replace_0.10`;
  `discount_increase_pp_0.00`; `discount_decrease_pp_0.00`), each shown
  as three separated blocks: baseline, hypothetical, variance.
- Measures: TOTAL baseline versus hypothetical: net revenue, discount
  amount, modeled COGS, gross profit/margin (conditional), freight,
  cost-to-serve, contribution profit/margin, WAD, absolute variances
  (`variance_net_revenue`, `variance_discount_amount`, `variance_cogs`,
  `variance_gross_profit`, `variance_contribution_profit`), relative
  variance where baseline nonzero, margin changes in PP
  (`margin_change_pp`, `gross_margin_change_pp`), quantity (37,873),
  order/line counts, `low_sample_flag`, `N/A`-with-reason markers.
- Required filters, if any: None; scope is all valid lines for every
  instance; no re-banding.
- Expected insight: Headline sensitivity per instance beside its baseline
  (uniform 0.10: baseline 565,116.94 → hypothetical 660,523.18, variance
  +95,406.24, +1.03pp; both identity instances: variances zero) — read
  strictly as arithmetic under the stated assumptions.
- Validation requirement: TOTAL variances reconcile both ways (≤ 1e-9);
  freight variance exactly 0; counts 9,994 / 5,009 / 37,873; TOTAL
  reconciles to the order fact within 0.05; scenario identifiers, input
  forms, and assumption labels consistent with filenames; flags and `N/A`
  reasons preserved.
- Known limitation: Identity slices show zero variance by construction
  (integrity, not economics); nonzero universal pp shifts have no valid
  output and must not appear here; LINE-basis scenario detail is not
  licensed.

### AO-04 — Contribution variance by discount band

- Output name: Contribution variance by discount band.
- Business purpose: Show how the headline scenario sensitivity is
  distributed across the existing baseline discount configurations.
- Source artifact: `phase4b_scenario_uniform_0.10.csv` + its quality JSON
  `phase4b_scenario_quality.json` (15/15 PASS) for band-level variance;
  `phase4b_scenario_increase_0.00.csv` + its quality JSON (22/22 PASS)
  and `phase4b_scenario_decrease_0.00.csv` + its quality JSON (22/22
  PASS) as zero-variance band confirmation for the identity instances.
- Grain: Overall × discount band, ORDER basis (authoritative).
- Dimensions: Baseline discount band (B0–B5 + TOTAL, baseline
  order-WAD assignment) with `basis = ORDER` marker; scenario instance
  as in AO-03.
- Measures: Per baseline band: `base_contrib` versus `hypo_contrib`,
  `variance_contribution_profit` (absolute), relative variance where
  baseline nonzero, `margin_change_pp`, `variance_net_revenue`,
  `variance_discount_amount`, `variance_cogs`, `variance_freight` (= 0),
  `variance_cost_to_serve` (= 0), `base_wad` versus `hypo_wad`,
  quantity, order/line counts, negative-order counts
  (`neg_base_orders`, `neg_hypo_orders`), `low_sample_flag`,
  `N/A`-with-reason markers.
- Required filters, if any: None; bands are baseline bands; no re-banding.
- Expected insight: Exposure-concentration reading, e.g. which baseline
  bands contribute most to the uniform-0.10 variance and which bands show
  zero or small moves — read strictly as arithmetic under the stated
  assumptions. The authoritative basis is the existing baseline
  discount-band assignment; the output must not reconstruct or re-band
  orders.
- Validation requirement: Per-band variances reconcile both ways
  (≤ 1e-9); freight variance exactly 0 per band; counts per band match
  frozen band counts (B0=2055 | B1=415 | B2=1634 | B3=278 | B4=274 |
  B5=353); band rows sum to TOTAL; margin changes in PP; flags and `N/A`
  reasons preserved per row.
- Known limitation: Baseline and hypothetical values remain clearly
  separated (never merged); band-level scenario variance must not be
  inferred from incompatible grains (no LINE-basis scenario detail, no
  disaggregation of band rows into fabricated order-level hypotheticals,
  no gross-only grains); identity slices show zero variance by
  construction; nonzero universal pp shifts have no valid band output and
  must not appear here. The output is descriptive arithmetic sensitivity,
  not causal or predictive analysis.

### AO-05 — Order-level reading (observed baseline only)

- Output name: Order-level baseline reading.
- Business purpose: Preserve order-level visibility (WAD distribution,
  negative-contribution orders, ambiguity-affected order, quantity and
  line-count context) that band aggregates average over.
- Source artifact: `discount_order_summary.csv` (5,009 rows,
  authoritative contribution joined with line-derived discount rollup);
  `phase3b_quality_report.json`.
- Grain: Order (`order_id`, one row per order; authoritative).
- Dimensions: Baseline order-WAD band; return status (filter context
  only); line count; `negative_contribution_flag`; `ambiguity_note`.
- Measures: Order WAD, realization, net/gross revenue, modeled gross
  profit/margin, freight, cost-to-serve, contribution profit/margin,
  quantity, line count.
- Required filters, if any: None for the full reading; return-status
  cohorts (YES / NOT_RETURNED / UNKNOWN) permitted as side-by-side
  filter views with the line-identification limitation stated; UNKNOWN
  never defaulted.
- Expected insight: Distributional context (WAD median 0.1607, mean
  0.1606; 50 flagged negative orders preserved with identifiers; single
  ambiguity-noted order with full-order freight 26.55) supporting — never
  replacing — band readings.
- Validation requirement: Order revenue/COGS rollups match the order fact
  (≤ 1e-6); margins SUM/SUM-consistent (≤ 1e-6); exactly one band per
  order; exactly one ambiguity-noted order; single-segment/single-customer
  attribution verified.
- Known limitation: Single observations carry no per-row sample flag
  meaning beyond the documented FALSE convention; hypothetical
  order-level scenario detail is not present in frozen artifacts and must
  not be fabricated by disaggregating band rows.

### AO-06 — Data-quality summary

- Output name: Data-quality summary.
- Business purpose: Record the eligibility of every source artifact
  before any business reading is approved.
- Source artifact: `phase3b_quality_report.json`;
  `phase4b_scenario_quality.json`;
  `phase4b_scenario_increase_0.00_quality.json`;
  `phase4b_scenario_decrease_0.00_quality.json`; CSV row counts and
  SHA-256 values (§10).
- Grain: Artifact level (per file), then TOTAL row.
- Dimensions: Check identifier (`id`), status, expected/actual.
- Measures: Pass counts (16/16; 15/15; 22/22; 22/22); row/order/quantity
  totals; reconciliation gaps vs tolerances; bound conformance;
  NULL preservation (exactly 2 NULLs); flag presence; hash matches;
  determinism evidence.
- Required filters, if any: None.
- Expected insight: Eligibility gate per BQ-08 — which artifacts may
  source interpretation and which may not — with unsupported metrics
  listed as `N/A` with reasons.
- Validation requirement: Unique check IDs with zero duplicates; every
  record carries `id`, `description`, `expected`, `actual`, `status`;
  frozen-input hashes byte-identical before/after; consecutive runs
  byte-identical (SHA-256-compared); no timestamps or randomness.
- Known limitation: Quality evidence covers arithmetic and lineage only;
  it licenses no behavioral, predictive, or causal reading.

No customer-level scenario table, no segment-specific scenario table, no
category/product scenario table, and no visual is specified here, because
no frozen artifact supports them as scenario outputs.

## 9. Interpretation Rules

Binding on every future reading, table, and narrative built from frozen
Margin Map outputs:

1. Do not equate correlation with causation. Band contrasts, quantity
   co-occurrence, and margin spans are descriptive associations over
   confounded observational data.
2. Do not call arithmetic scenarios forecasts. Permitted standing is
   "illustrative constant-quantity scenario", "arithmetic change under
   the stated assumptions", "modeled result conditional on the selected
   cost structure", "observed baseline beside the hypothetical
   restatement", "conditional illustration, not a forecast".
3. Do not claim that discount changes cause observed outcomes. Phrasing
   such as "the discount caused …" is forbidden unless separately
   validated (none validated). Customer response, demand movement, and
   what would have sold are never stated.
4. Do not compare incompatible grains. ORDER-basis authoritative rows and
   LINE-basis partial rows are never mixed in one average; category /
   sub-category / product gross-only rows never carry contribution; order
   detail is never inferred from band aggregates.
5. Do not hide NULLs or invalid records. The two ambiguous lines stay
   NULL and flagged at line grain; zero-revenue hypothetical margins stay
   NULL/blank, never 0-filled; structurally absent band cells stay
   absent, never zero-filled; the single UNKNOWN-return order stays
   UNKNOWN.
6. Do not mix baseline and hypothetical values without clear labels.
   Baseline, assumption, hypothetical-output, and unsupported-flag layers
   travel separately with `hypothetical_*` naming, scenario identifiers,
   input forms/values, scope, grain markers, and assumption versions on
   every reading.
7. Do not infer customer response, demand elasticity, or future sales.
   No elasticity is estimated here; no response coefficient exists;
   quantity is held constant by assumption (labeled as such, not as a
   finding); `demand_response_view` remains `N/A` with reason on every
   scenario row.
8. Always disclose the scenario assumptions. Every scenario figure shows:
   constant observed quantity (37,873); frozen modeled-COGS percentages
   with the margin-constancy consequence; observed freight passthrough
   (variance 0); return/support OFF (zero = excluded); bounds [0, 0.80]
   with no clipping or silent exclusion; baseline-band grouping; and the
   `N/A` reasons for unlicensed views.
9. Preserve the distinction between observed and hypothetical values.
   Observed net revenue is the frozen `sales` fact; reconstructed gross
   is a derived reference, never an observed list price; discount amount
   is revenue forgone, not profit loss; hypothetical nets exist only
   inside their named scenario; quarantined source Profit enters zero
   computations.

Any visual whose reading could invite a behavioral or predictive
interpretation carries the standing caveat on the visual itself, not only
in accompanying text.

## 10. Validation Requirements

What must be checked before future analytical outputs are approved (tied
to the frozen Gate 9 / contract check discipline; tolerances from frozen
evidence):

1. Source-artifact identity. File names, scenario identifiers
   (`uniform_replace_0.10`; `discount_increase_pp_0.00`;
   `discount_decrease_pp_0.00`), input forms (`replacement_rate`;
   `increase_pp`; `decrease_pp`), stated values, scope
   (`all_valid_lines`), and reporting grain (Order × Discount Band,
   ORDER basis, baseline bands) recorded and consistent with filenames;
   any identifier residue from another slice fails.
2. Row and order counts. 9,994 lines / 5,009 orders in scope; Phase 3B
   CSV counts 14 / 39 / 19 / 69 / 3,304 / 5,009 / 5,925; Phase 4B CSVs
   7 rows × 52 columns; band counts B0=2055 | B1=415 | B2=1634 | B3=278
   | B4=274 | B5=353; scoped counts equal frozen totals
   (`no-silent-exclusion`).
3. Quantity reconciliation. Line + order + TOTAL quantity 37,873,
   bit-identical reuse asserted, never transformed.
4. Baseline reconciliation. TOTAL revenue 2,297,200.86 (2297200.8603),
   COGS 1,493,910.13 (1493910.1285), freight 238,173.79, contribution
   565,116.9418 within 0.05 of the Phase 2 facts; order COGS rollup gap
   ≤ 1e-6 (observed 1.82e-12); COGS-percentage identity gap ≤ 1e-6
   (observed 4.55e-13); gross dual gap ≤ 1e-6 (observed 1.82e-12).
5. Scenario reconciliation. Hypothetical dual forms reconciled (gap ≤
   1e-6; observed 9.09e-13); variances reconciled both ways (gap ≤ 1e-9);
   freight variance exactly 0; TOTAL row reconciles; identity slices show
   zero variances exactly.
6. Discount bounds. Observed discounts within [0, 1) with zero NULLs
   (observed [0, 0.80]); every hypothetical `d'` within [0.00, 0.80] on
   the 6-decimal stored value; stated inputs within [0.00, 0.80] on the
   decimal-fraction scale (display-scale values rejected); any breach
   fails the whole run with diagnostics and no valid output (no clipping,
   no extrapolation, no silent correction, no partial-subset execution).
7. Band totals. Band rows sum to TOTAL; no observed value split; B0 holds
   exactly the zero-discount sets (4,798 lines; 2,055 orders); WAD dual
   form reconciled (observed 5.55e-17); single order-band rule applied.
8. NULL preservation. Exactly 2 NULL freights (rows 3406/3407,
   `US-2014-150119`) with flags unchanged; 25.05 pair total via order
   aggregation only (full-order 26.55); zero-revenue margins NULL/blank;
   absent band cells absent (Office Supplies B3/B4; 50/102 sub-category
   cells).
9. Deterministic output checks. Identical frozen inputs plus identical
   versioned configuration reproduce byte-identical artifacts
   (SHA-256-compared; e.g. uniform CSV
   `6771a5f2ec4eb1584a7965768766e329c4e80f1b3ae805992c9ff65a7b9da2d1`;
   increase 0.00 CSV
   `10fb41f207c7cc011d3fbfe5bdbaec0bbfdc0be4e53cf39f3a0bf7ce087c9560`;
   decrease 0.00 CSV
   `8089d3b22c4e82cd2c31ba59b2fb1ababd91ccf5816dda419e4f4ea3c359636d`);
   no timestamps, no randomness; sorted band keys (B0–B5, TOTAL);
   versioned constants.
10. Frozen-artifact hash protection. Pre-/post-run SHA-256 identical for
    `fact_sales_cogs.csv`
    (`4d8de717486b323ffb656d13c94fd6bd94f8e61d1a93ea339a602ab5303b9988`),
    `fact_margin_map_phase2.csv`
    (`4c471feeda642e5ecbd2263782b4fc0f1655962f6c6488bdfe47886df2f01cb1`),
    `order_margin_map_phase2.csv`
    (`ae6c349c9995747f2fef91cf1db6b940a73d99d6b2fede5ff3dff918f429d267`),
    plus frozen scenario artifacts listed in §10 item 9, the uniform-replacement
    quality JSON (`phase4b_scenario_quality.json`)
    (`4e3c4d8a9e3a8b127ee1f4522f505cc9bafaa2682173712d68fc84915855047b`)
    and the increase
    quality JSON
    (`52c9938394667dad4b8c29baefc282d84bb5f53450b1a9bb608dc559e4dcf7bf`)
    and decrease quality JSON
    (`bbde89e48a1360e5e0f11c81ac05344fb4d1739993e8564f5886da18b31e107c`);
    any drift aborts.
11. Grain consistency. Contribution read as authoritative only at order
    grain and above; below-order-grain contribution NULL with reason
    `FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN`; ORDER vs LINE bases
    never mixed; no freight allocation below order grain; no product
    contribution attribution.
12. Metric-definition consistency. Every figure traces to §7 with the
    frozen formula, denominator, and lineage label intact; SUM/SUM
    margins with PP changes; WAD gross-weighted; quarantine excluded;
    OFF labels intact; `N/A`-with-reason present for
    `fixed_unit_cost_view` (`COMPARATOR_NOT_IN_INITIAL_BUILD`) and
    `demand_response_view` (`RESPONSE_NOT_ESTIMATED`); claim-exclusion
    wording present.

A failed check identifies the issue and blocks the output from valid
status. Failed scenario runs (out-of-bound `d'`, non-numeric or missing
inputs) produce diagnostics only, never valid outputs.

## 11. Out of Scope

Explicitly excluded from this design and from any work authorized by it:

1. Dashboard implementation (any table, visual, or business-facing
   display beyond the specified future-output definitions).
2. UI design (layout, interaction, formatting, or display conventions
   beyond binding Gate 10 constraints, which are cited, not extended).
3. Forecasting (statements about what will occur under any discount).
4. Optimization (selection of best, recommended, or optimal discounts or
   policies).
5. Causal inference (claims that an observed or hypothetical discount
   difference caused a quantity, revenue, or profit difference).
6. Elasticity estimation (any response coefficient or demand parameter;
   descriptive quantity indexes, if ever proposed, require separate
   approval and remain non-causal).
7. Customer segmentation (grouping or targeting of customers beyond the
   frozen observed customer summary, whose within-customer band detail is
   fully flagged arithmetic and supports no comparative statement).
8. Returns modeling (any refunded-revenue adjustment or return-cost rate;
   return status remains filter/cohort context only with UNKNOWN never
   defaulted).
9. Support-cost modeling (any ticket-cost or proxy rate; support remains
   OFF with zero meaning excluded).
10. New scenario types (any scope, input form, bound, rounding, or
    assumption beyond the three frozen slices; segment-, category-, and
    product-specific scenarios remain deferred; fixed-unit-cost
    comparator remains unbuilt with no per-unit source).
11. Changes to frozen artifacts (no modification, regeneration, renaming,
    overwriting, re-banding, re-aggregation, or hash-breaking of any
    Phase 1–4B data file, script, schema, or frozen document).
12. Automated recommendations (any suggested action, pricing decision, or
    operational instruction derived from baseline or scenario figures).

Deferred items must not be implemented, partially supported, or
represented as available. Prohibited phrases (including affirmations of
forecasting, prediction of response, causal attribution, optimality, or
best-policy selection) occur in this document solely inside prohibitions.

## 12. Approval Gate

> `DESIGN ONLY — DRAFT, NOT APPROVED, NOT FROZEN`

No implementation may begin under this document. Approval requires
explicit owner decisions confirming each of the following, after review
of this record against the frozen authorities cited in §1.1:

1. Design review — the twelve sections cover purpose, scope, questions,
   baseline, scenarios, bands, metrics, outputs, rules, validation,
   exclusions, and gates with no silent choice left to implementation.
2. Metric-definition review — every metric in §§3–8 traces to §7 and to a
   frozen definition with formula, grain, unit, and limitation intact;
   no undefined or redefined metric remains.
3. Grain review — ORDER-basis authority, LINE-basis partial discipline,
   gross-only discipline below order grain, baseline-band grouping, and
   the no-disaggregation rule for 7-row scenario artifacts are confirmed.
4. Source-artifact review — each proposed output in §8 names a frozen
   source artifact and grain; identity-slice limits and the absence of
   valid nonzero universal-shift outputs are acknowledged; failed runs
   are confirmed to authorize no figure.
5. Scope review — §11 exclusions are accepted; no dashboard, forecast,
   optimization, causal, elasticity, segmentation, returns/support, new
   scenario, frozen-artifact change, or recommendation work is smuggled
   in as interpretation.
6. Validation-plan review — the §10 check set (counts, reconciliations,
   bounds, bands, NULLs, determinism, hashes, grain, metric consistency)
   with the stated tolerances is adopted as the fail-loud gate for any
   future analytical output; any departure requires a new documented
   approval before it is built.

Until all six reviews pass with recorded owner approval, this document
remains a draft. No analytical output is approved, no display work is
authorized, and no frozen artifact changes standing.

`DESIGN ONLY — DRAFT, NOT APPROVED, NOT FROZEN`
