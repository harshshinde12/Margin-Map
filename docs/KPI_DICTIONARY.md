# MarginMap — KPI Dictionary (Phase 1A)

> Definitions-only. No implementation in this phase. Grain abbreviations:
> **L** = transaction line (`Row ID`), **O** = order (`Order ID`),
> **M** = month, **D** = any analysis dimension (Product ID, Customer ID,
> Region, Segment, Ship Mode, Category, Sub-Category). Source lineage per
> `FINANCIAL_MODEL.md`. Modeled inputs have no values in Phase 1A.

| KPI | Definition | Formula | Data Type | Source / Model | Grain | Used In | Caveats |
|---|---|---|---|---|---|---|---|
| Gross Revenue | Reference revenue before discount; reconstructed because no list-price field exists | `Sales / (1 − Discount)` | Currency | Source-derived (reconstructed reference) | L → sums to O/M/D | Waterfall top line; Discount Amount; Leakage | NOT observed list price — label as derived; NULL/blank if `Discount = 1`; Discount NULL/out-of-range = REQUIRES VALIDATION |
| Net Revenue | Authoritative revenue; source Sales already net of discount | `Sales` | Currency | Source-derived | L → sums to O/M/D | All profit & margin denominators; variances | Do NOT subtract Discount again — double-count |
| Discount Amount | Revenue reduction from recorded discount | `Gross Revenue − Net Revenue` (equiv. `Gross Revenue × Discount`) | Currency | Source-derived | L → sums | Waterfall; discount analytics | Revenue reduction, not profit loss |
| Discount % | Recorded discount rate | Source field `Discount` (decimal; ×100 display only) | Rate (decimal) | Source-derived | L | Discount analytics | Never ×100 inside calculations |
| COGS per Unit | Modeled product-level unit cost | Input (methodology TBD) — no value in Phase 1A | Currency/unit | Modeled (future) | Product ID | COGS | Requires methodology + assumption + validation before use |
| Total COGS | Product cost at line level | `Quantity × COGS per Unit` | Currency | Modeled (future) | L → sums | Gross Profit | Keep separate from Cost-to-Serve |
| Gross Profit | Profit after product cost only | `Net Revenue − COGS` | Currency | Modeled (future; needs COGS) | L → sums | Gross Margin %; variances | NOT Contribution Profit — excludes serve costs |
| Gross Margin % | Gross Profit per unit of Net Revenue | `Gross Profit / Net Revenue × 100`; NULL/blank if Net Revenue = 0 | Percent | Modeled (future) | L (compute on sums for aggregates, never average of %) | Portfolio/segment reporting; variances | Denominator is Net Revenue, never Gross; report margin change in pp |
| Freight Cost | Logistics cost for the line/order | Modeled input (driver/key TBD) — no rate in Phase 1A | Currency | Modeled (future) | L (allocated) | Cost-to-Serve | No source dollars; appears exactly once (direct XOR allocated) |
| Return Cost | Return-related cost | Modeled/scenario input — no value in Phase 1A | Currency | Modeled (future) | L (allocated) | Cost-to-Serve | No source returns; separate refunded revenue vs handling cost |
| Support Cost | Service/support cost | Modeled/scenario input — no value in Phase 1A | Currency | Modeled (future) | L (allocated) | Cost-to-Serve | No source support data |
| Total Cost-to-Serve | All operational/service costs | `Freight Cost + Return Cost + Support Cost` | Currency | Modeled (future) | L → sums | Contribution Profit | Excludes COGS by definition |
| Contribution Profit | Profit after product + serve costs | `Net Revenue − COGS − Freight Cost − Return Cost − Support Cost` (equiv. `Gross Profit − Total Cost-to-Serve`) | Currency | Modeled (future) | L → sums | Core MarginMap metric; variances | Both equivalent forms must reconcile |
| Contribution Margin % | Contribution per unit of Net Revenue | `Contribution Profit / Net Revenue × 100`; NULL/blank if Net Revenue = 0 | Percent | Modeled (future) | L (compute on sums for aggregates) | Executive decisions; risk flags | Denominator Net Revenue; change in pp |
| Discount Leakage | Revenue given up to discount | `Gross Revenue − Net Revenue` | Currency | Source-derived | L → sums | Pricing review | Same arithmetic as Discount Amount; framing differs — do not sum both |
| Revenue Variance | Absolute change in Net Revenue vs comparison period | `Actual − Comparison` (Net Revenue) | Currency | Source-derived | M/D | Monthly variance report | Define comparison (prior month/year) at implementation |
| Revenue Variance % | Relative change in Net Revenue | `(Actual − Comparison) / Comparison × 100`; NULL/blank if Comparison = 0 | Percent | Source-derived | M/D | Monthly variance report | Absolute variance still reported when Comparison = 0 |
| Gross Profit Variance | Absolute change in Gross Profit | `Actual − Comparison` (Gross Profit) | Currency | Modeled (future) | M/D | Monthly variance report | Needs COGS before computable |
| Gross Margin Change | Change in Gross Margin % | `Actual pp − Comparison pp` (percentage points) | Percentage points | Modeled (future) | M/D | Monthly variance report | Never label as "%" |
| Contribution Profit Variance | Absolute change in Contribution Profit | `Actual − Comparison` (Contribution Profit) | Currency | Modeled (future) | M/D | Monthly variance report | Needs full cost model |
| Contribution Margin Change | Change in Contribution Margin % | `Actual pp − Comparison pp` (percentage points) | Percentage points | Modeled (future) | M/D | Monthly variance report | Never label as "%" |
| Cost-to-Serve Variance | Absolute change in Total Cost-to-Serve | `Actual − Comparison` (Total Cost-to-Serve) | Currency | Modeled (future) | M/D | Monthly variance report | Reconcile allocations to period control total |

## Allocation terminology (for later phases — no rates selected)

- **Allocation Driver:** causal/relational factor linking a shared cost to lines
  (e.g. units shipped for freight) — must have a defensible relationship.
- **Allocation Key:** quantified driver share per line (shares sum to 1.0 per
  allocation period); the arithmetic that distributes the pool.
- **Direct Cost:** assignable straight to a line/customer/product when evidence
  supports it — no allocation needed.
- **Shared Cost:** pool that cannot be directly assigned; requires a methodology.
- **Allocated Cost:** resulting line-level amount after applying the key to the pool.
- **Allocation Period:** time window the pool total covers (e.g. month) — outputs
  must reconcile to the period control total.
- **Allocation Grain:** level costs are assigned at (MarginMap: transaction line
  `Row ID`, rolling up to order/customer/product).

## Dimension rules

Product ID = product key (Name = attribute). Customer ID = customer key (Name =
attribute). Category / Sub-Category / Region / Segment / Ship Mode are valid
dimensions. Ship Mode = shipping/logistics dimension, NOT channel. Channel =
documented limitation until a reliable source/method is established.
