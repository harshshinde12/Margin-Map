# Cost-to-Serve Data Dictionary (Phase 2A — future fields, no values)

> Every field below is **specified, not populated**. No Phase 2 column exists
> in any CSV today. Conventions extend Phase 1: `modeled_*` = computed
> estimates, `assumed_*` = sourced/scenario inputs, frozen Phase 1 names
> unchanged. Grain abbreviations: **L** = order line (`row_id`), **O** =
> order (`order_id`), **C** = customer (`customer_id`), **P** = analytical
> product (`analytical_product_key`).

## Line-level modeled cost fields (grain L, one value per `row_id`)

| Field | Definition | Type | Source | Observed/Modeled | Calculation | Null behavior | Interpretation |
|---|---|---|---|---|---|---|---|
| `freight_cost` | **Observed Shipping Cost from Dataset 1-US** (`Global_Superstore2`, US segment), joined to the frozen Phase 1 line by composite signature (`Customer ID, Product ID, Sales, Quantity, Discount, Ship Mode, City, State`). US total 238,173.79; 0 nulls/zeros/negatives; line-grained (varies across all multi-line orders). **Not allocated. Not modeled.** In-file computation methodology unverified — observed field, methodology caveat. | currency | Dataset 1-US enrichment (future join; join audit 9,994/9,994) | **OBSERVED** | Direct carry-over of the joined line value — no arithmetic | NULL only with `PENDING_INPUT` (unmatched line — must be 0 lines per audit, else fail-loud); never 0-filled | What moving this line actually cost per the source file |
| `modeled_return_cost` | Expected handling cost of returns attributable to the line | currency | Future return events or scenario rates — **no authoritative feed today** | Modeled (scenario, **OFF by default**) | Event cost mapped to line, or rate × base per approved scenario design | 0 with `NOT_APPLICABLE`/scenario-OFF label until a scenario is approved ON; NULL only with `PENDING_INPUT` | Scenario-only until event data exists (see D2A-04) |
| `modeled_support_cost` | Post-sale assistance cost attributable to the line | currency | Future ticket data or scenario proxies — **no authoritative feed today, no default rate** | Modeled (scenario, **OFF by default**) | Ticket cost mapped to line/order, or proxy per approved scenario design | Same as return cost | Scenario-only until ticket data exists (see D2A-05) |
| `modeled_cost_to_serve` | Total operational/service cost of the line | currency | Sum of the three above | Modeled | `freight_cost + modeled_return_cost + modeled_support_cost`, exactly — never includes COGS | NULL if any applicable component is NULL (no partial sums presented as totals) | The serve-cost layer for this line |

## Contribution fields (grain L; aggregates by SUM, margins by SUM/SUM)

| Field | Definition | Type | Source | Observed/Modeled | Calculation | Null behavior | Interpretation |
|---|---|---|---|---|---|---|---|
| `modeled_contribution_profit` | Profit after product + serve costs | currency | Phase 1 frozen inputs + serve fields | Modeled | `net_revenue − modeled_cogs − modeled_cost_to_serve` (must equal `modeled_gross_profit − serve`; both checked) | NULL if any term NULL | Core Phase 2 profitability fact |
| `modeled_contribution_margin_pct` | Contribution per unit of Net Revenue | percent (plain number) | Derived | Modeled | `profit / net_revenue × 100`; **NULL if net_revenue = 0** | NULL, never 0-fill, never inf | Margin after everything modeled so far |

## Allocation driver fields (grain L; scenario-pool splits only — NOT freight)

Freight is joined, not split: no driver applies to `freight_cost`. The fields
below serve future return/support scenario pools exclusively.

| Field | Definition | Type | Source | Observed/Modeled | Null behavior | Interpretation |
|---|---|---|---|---|---|---|
| `driver_quantity_weight` | Line `quantity` reused as a scenario split weight | numeric | Observed (`quantity`) | Observed | Never NULL (source guarantees > 0) | Neutral unit-based share |
| `driver_revenue_weight` | Line `net_revenue` share basis (comparator only) | numeric | Observed (`sales`) | Observed | Never NULL (> 0 observed) | Value-based share (comparator only) |
| `driver_ship_mode` | Fulfilment method, analytical cut (not a freight driver — freight is observed) | string enum: Standard/Second/First/Same Day | Observed (`ship_mode`) | Observed | Never NULL | Reporting dimension for freight/cost cuts |
| `driver_region` | Region, analytical cut / reserved scenario modifier | string enum: 4 regions | Observed (`region`) | Observed | Never NULL | Reporting dimension; coarse zone proxy |
| `driver_weight_share` | Final normalized share applied to a scenario pool | decimal ∈ [0,1] | Modeled | Modeled | Sums to 1.0 per pool (asserted); pool with all-zero weights aborts, never silently equal-splits | The auditable split actually used |

## Freight provenance fields (grain L — the join audit trail)

| Field | Definition | Type | Allowed values | Null behavior | Interpretation |
|---|---|---|---|---|---|
| `freight_match_status` | Outcome of the composite-signature join for this line | string enum | `MATCHED_UNIQUE` (9,992 lines), `MATCHED_AMBIGUOUS` (rows 3406/3407), `UNMATCHED` (expected 0 — fail-loud if any) | Never NULL | Proves every line's freight lineage |
| `freight_ambiguity_flag` | Marks the single controlled ambiguity | boolean | `TRUE` only on Phase 1 rows 3406/3407 (order total 25.05 preserved at order level); `FALSE` elsewhere | Never NULL | Prevents silent line assignment of 21.59/3.46 |
| `freight_source` | Provenance pointer | string | `Dataset 1-US / Global_Superstore2 :: Shipping Cost` (+ file hash recorded at load) | Never NULL | Observed-field traceability |
| `freight_method` | How the line value was obtained | string enum | `OBSERVED_JOIN` (9,992 lines), `ORDER_LEVEL_AMBIGUOUS` (rows 3406/3407 until a defensible split exists) | Never NULL | Distinguishes joined values from ambiguity-held ones |

## Method & provenance fields (grain L, or per pool-period where noted)

| Field | Definition | Type | Allowed values | Null behavior | Interpretation |
|---|---|---|---|---|---|
| `allocation_method` | Which candidate produced this line's serve costs | string enum | `OBSERVED_JOIN` (freight), `F-Q`, `F-V`, `F-S`, `F-R`, `F-H` (withdrawn — historical only, see D2A-11), `R-A`, `R-B`, `S-A`, `S-B`, `S-C`, `NOT_APPLICABLE`, `PENDING_INPUT` (extend only by decision-log entry) | Never NULL once implementation exists | Tells the reader exactly which methodology each number came from |
| `cost_pool_id` | Identifier of the pool this line's share came from (per pool-period) | string | `<component>:<period>:<version>` pattern | NULL only for `NOT_APPLICABLE` rows | Pool-to-line traceability for reconciliation |
| `cost_source` | Provenance pointer for the pool's parameter | string | `ACTUAL_*` feed ref, `BENCHMARK_*` citation, or `SCENARIO_*` label | Never NULL for non-zero costs | Distinguishes observed bills from benchmarks from what-ifs |
| `assumption_note` | Human-readable why/how for this row's serve numbers | string | Free text + version ref | Mandatory for every non-actual row | Audit trail in plain language |
| `confidence` | Standing of the row's serve estimate | string enum | `HIGH` (observed feeds only), `MEDIUM`, `LOW` | Never NULL | Calibrates how hard a decision may lean on the number |
| `scenario_layer` | Whether the row's value belongs to base or a named what-if | string | `BASE`, or scenario name (e.g. `RETURNS_ON`) | Never NULL; default `BASE` | Keeps evidence-only and scenario views separable in BI |

**Return-data availability (explicit).** Authoritative MarginMap return data
is **unavailable**: no Returned status feed exists for the Phase 1 universe
(Dataset 2 Returns rejected — incompatible ID universe, order-level
`Yes`-only flags, no quantity/refund/date/reason/line detail). Therefore:
Returned status = unavailable as authoritative data; Refunded Revenue = not
available; Returned Quantity = not available; Return Processing Cost = modeled
scenario only, OFF by default. Support: modeled scenario only, OFF by
default, no numerical default rate.

## Reserved aggregate-view conventions (no stored fields — computed in BI/SQL)

Customer (`C`), product (`P`), order (`O`), region/segment/category/month
views are **queries over line fields**, not stored tables: costs/profits by
SUM, margins by SUM/SUM, entity counts by DISTINCT. If a future phase
materializes marts, they must carry the same field names with a documented
grain suffix and reconcile to line sums exactly.

## Naming & typing rules for implementation

- Money: source currency, full float precision in files (round on display).
- Percents: plain numbers (40 = 40%), matching Phase 1.
- IDs/keys/enums: strings, never numerics (`postal_code` precedent).
- Dates: ISO `YYYY-MM-DD`; datetimes only if a feed requires intraday grain.
- No field may be named `profit`, `margin`, `freight`, or `cost` without a
  `modeled_`/`assumed_`/`source_` prefix — with one deliberate exception:
  `freight_cost` carries no prefix precisely because it is OBSERVED, not
  modeled (prefix absence is the signal; the dictionary and `freight_source`
  make the status unmistakable). CSVs carry no types: consumers must
  re-assert dtypes on read, as in Phase 1.
