# Cost-to-Serve Model — Architecture & Methodology (Phase 2A, design only)

> Status: **DESIGN ONLY — no rates, no estimates, no implementation.**
> This document specifies *how* cost-to-serve will be modeled once inputs
> exist. It creates zero numerical cost assumptions. Phase 1 is frozen
> (`docs/PHASE_1_FREEZE.md`) and unchanged: Net Revenue = Sales, analytical
> product grain = Product ID + Product Name, authoritative modeled COGS =
> Net Revenue × modeled COGS %, source Profit quarantined. All terminology
> below extends Phase 1 (`docs/FINANCIAL_MODEL.md`, `docs/KPI_DICTIONARY.md`);
> nothing here redefines it.

## 1. Cost-to-Serve definition

**Cost-to-Serve** is the operational/service cost of selling and servicing a
line, order, customer, or product — everything between Gross Profit and
Contribution Profit. It comprises exactly three components, kept separate
from each other and from COGS at all times:

```text
Cost-to-Serve = Freight Cost + Return Cost + Support Cost
```

Approved high-level formulas (from Phase 1A, restated with Phase 1 prefixes):

```text
Contribution Profit    = Net Revenue − Modeled COGS − Freight Cost
                         − Return Cost − Support Cost
                       = Modeled Gross Profit − Total Cost-to-Serve
Contribution Margin %  = Contribution Profit / Net Revenue × 100
                         (NULL/blank if Net Revenue = 0)
```

COGS is a *product* cost; cost-to-serve is the cost of *moving, taking back,
and supporting* what was sold. The two layers must never be merged, and no
component may appear twice (see §10).

## 2. Component definitions

### 2.1 Freight cost definition — OBSERVED (no allocation model required)

Freight Cost is the **observed Shipping Cost from the approved Dataset 1-US
enrichment source** (`Dataset 1 Apoorva.zip` → `Global_Superstore2.csv`,
US segment), joined to frozen Phase 1 transactions by composite signature.
No freight allocation model is required because Shipping Cost is directly
available at transaction-line grain.

- **Source/provenance:** Dataset 1-US / Global_Superstore2, `Shipping Cost`
  column (float, source currency). Candidate file held in project root;
  frozen Phase 1 files untouched — enrichment is a future join, not yet built.
- **Observed vs modeled:** OBSERVED field with unverified in-file methodology
  (its original computation from carrier bills vs internal formula is
  undocumented — tier: observed field, methodology caveat recorded, never
  presented as audited carrier cost).
- **Line-level availability:** present on all 9,994 US lines; varies across
  all 2,471 multi-line orders, so it is genuinely line-grained — line
  summation does not double-count any order total.
- **Totals/quality:** US total **238,173.79**; 0 nulls, 0 zeros, 0 negatives;
  range 0.01–933.57, median 5.10.
- **Compatibility evidence:** 9,994/9,994 composite-signature matches, 0
  unmatched either side; sales, quantity, discount distribution, customers,
  products, ship/region/segment counts all reconcile exactly
  (`docs/PHASE_2_DATA_COMPATIBILITY_REPORT.md` §4).
- **Composite matching mechanism:** (`Customer ID, Product ID, Sales,
  Quantity, Discount, Ship Mode, City, State`) — direct Order ID matching
  rejected (recoded IDs, 0% intersection); Product Name excluded from the key
  (coarser labels on 197 rows in Dataset 1; frozen Phase 1 names canonical).

**Single row-level ambiguity (material, controlled).** Composite key
(`LB-16795`, `FUR-CH-10002965`, 281.372 × 2 @ 0.3, Standard, Columbus OH)
matches two Phase 1 rows (3406/3407) and two Dataset 1 rows (34702 →
Shipping Cost **21.59**; 34703 → **3.46**). Individual line-level freight
cannot be uniquely assigned — random assignment is forbidden. The
order-level total is invariant (**21.59 + 3.46 = 25.05**), so aggregate
order/customer/product freight remains reliable. Future implementation must
either (1) retain an ambiguity flag with order-level freight treatment, or
(2) apply a documented deterministic split only if a defensible basis
becomes available. No split is invented here. This is the ONLY ambiguous key.

**Superseded:** the previous freight candidate methods (quantity baseline
F-Q, hybrid ship-mode/quantity F-H, value comparator F-V, region modifier
F-R, ship-mode pool F-S) are withdrawn — real Shipping Cost exists, so
freight is joined, not allocated. They remain recorded in the decision log
as evaluated-and-superseded, not as options.

### 2.2 Return cost definition

The cost *caused by* a return event: reverse logistics, inspection,
restocking or disposal, and associated handling. Refunded *revenue* is a
separate concept from return *cost* (see §10.5). The source dataset contains
no return flag, no return table, and no restocking record; therefore return
cost has **no observed anchor** and can only enter as a future-data module or
a explicitly labeled scenario layer (see §5.2).

### 2.3 Support/service cost definition

The cost of post-sale customer assistance attributable to a line, order, or
customer: contact handling, ticket resolution, and technical support effort.
The source dataset contains no ticket, contact, or service record; like
returns, it has **no observed anchor** and enters only via future data or a
labeled scenario layer (see §5.3).

## 3. Analytical cuts

### 3.1 Cost-to-Serve per order line

The **allocation grain** (§6): every cost component lands on `row_id` exactly
once. Line-level cost-to-serve = line freight + line return cost + line
support cost. All reporting is built by summing lines — never by modeling
directly at aggregate level and pushing numbers down.

### 3.2 Cost-to-Serve per order

Order cost-to-serve = SUM of its lines' cost-to-serve. Where a cost is
naturally order-shaped (freight), the approved direction is *order pool →
line split by driver weight → re-sum to order*, so the order total equals the
pool by construction (control-total reconciliation, §9). With 5,009 orders
(2,538 single-line, 2,471 multi-line, max 14 lines), the split rule is
material, not cosmetic.

### 3.3 Cost-to-Serve per customer

Customer cost-to-serve = SUM over all lines of that `customer_id` (793
customers; ID↔name verified 1:1, so `customer_id` is a clean rollup key).
Customer-level pools are **forbidden**: no customer-level cost source exists,
so costs may only reach customers bottom-up from lines. Any future
customer-specific charge (e.g. a key-account team cost) must arrive as its own
documented pool with its own key — never as an adjustment to line costs.

### 3.4 Cost-to-Serve per product

Product cost-to-serve = SUM over all lines of that `analytical_product_key`
(1,894 products, frozen grain). Same bottom-up rule as customers: no
product-level pools without documented source, key, and reconciliation.

## 4. Allocation grain

**One row = one product line within an order (`row_id`)** — inherited
unchanged from Phase 1. Rationale: it is the only grain at which revenue,
COGS, quantity, discount, ship mode, and dates are jointly observed, so it is
the only grain where `Contribution Profit = Net − COGS − serve costs` can be
computed without inventing joint distributions. Allocations therefore always
terminate at lines; every aggregate (order, customer, product, region,
segment, category, month) is a pure sum of lines plus the SUM/SUM margin rule
(§9).

## 5. Allocation drivers — candidate evaluation

Notation: `w(i)` = driver weight of line `i` within its order; line share =
`w(i) / Σw(order)`. No symbols below carry numerical values — they are
placeholders for future approved inputs.

### 5.1 Freight — observed, not allocated (candidates superseded)

The §2.1 finding (observed line-level Shipping Cost, 100% composite match)
supersedes allocation design for freight. The candidate evaluation below is
retained as the audit trail of what was considered and why each is withdrawn;
**none of these methods is to be implemented for freight.**

| Candidate | Verdict after evidence |
|---|---|
| **F-Q. Quantity-based split** | Withdrawn — would fabricate what is observed. |
| **F-V. Order-value-based split** | Withdrawn — same, plus its margin-compressing bias. |
| **F-S. Ship-mode-differentiated pool** | Withdrawn as a pool method — `ship_mode` remains a useful *analytical* cut for freight reporting, not an allocation driver. |
| **F-R. Region-based** | Withdrawn — same; region remains a reporting dimension. |
| **F-H. Hybrid** | Withdrawn — the shortlist it led is closed by evidence. |

Original evaluation (advantages/limitations/required-data per candidate) is
preserved in `docs/COST_TO_SERVE_DECISION_LOG.md` D2A-03 history and
`data/processed/cost_to_serve_schema.json` version notes. Allocation
machinery (§6 pools, §9 pool reconciliation) now applies **only** to future
return/support scenario layers — freight joins line-to-line with the
ambiguity control in §2.1.

### 5.2 Return candidates

| Candidate | Advantages | Limitations / bias risk | Defensible? | Required data |
|---|---|---|---|---|
| **R-A. Actual return data, if later supplied** | Only causally clean option: real events, real costs, real revenue adjustments | Dataset currently has none; needs event grain + refund-vs-cost separation | **Yes — the target state** | Return event feed keyed to order/line + cost per event type |
| **R-B. Product/category return-rate assumptions** | Usable without event data; category rates are externally benchmarkable (same discipline as Phase 1C-3) | Rate × revenue is an expectation, not an event: assigns return cost to customers who never returned; flatters/penalizes whole categories uniformly | Scenario-layer only until calibrated; never authoritative | Sourced return-rate table + handling-cost table, both versioned |
| **R-C. Customer/order-based proxy** (e.g. infer returns from order patterns) | Needs no new data | **Fabrication risk**: the dataset contains zero return signal, so any proxy invents events — highest bias risk in this phase | **No — rejected** for any authoritative or customer-facing use | N/A (rejected) |

### 5.3 Support candidates

| Candidate | Advantages | Limitations / bias risk | Defensible? | Required data |
|---|---|---|---|---|
| **S-A. Actual service/ticket data, if later supplied** | Causally clean; enables genuine service-intensity analysis | None exists; needs ticket↔order/customer linkage design | **Yes — the target state** | Ticket feed with customer/order keys + cost-per-ticket |
| **S-B. Order-frequency proxy** (cost per order/contact assumption) | Simple; uses observed order counts | **Perverse bias**: punishes loyal high-frequency customers — exactly the customers the business wants; confuses buying with needing help | Scenario-layer only, with the bias stated on every output | Cost-per-order assumption (sourced, versioned) |
| **S-C. Product/category complexity proxy** | Directionally plausible (machines/phones plausibly need more support than fasteners) | Complexity classification is itself an assumption needing external validation; uniform within category | Scenario-layer only | Complexity mapping + per-class cost, both sourced |
| **S-D. Customer/service-intensity proxy** | Would capture real heterogeneity | No intensity signal exists in the dataset — unbuildable today without invention | No until data exists | Service-intensity source (future) |

### 5.4 What "defensible" means in this project

A candidate is defensible iff: (i) every input is observed, sourced-
benchmarked, or explicitly labeled assumption — never inferred from silence;
(ii) its bias direction is stated in writing before results are read; (iii) a
comparator method exists so conclusions can be checked, not just produced;
(iv) it reconciles to control totals. Freight now clears this bar by a
stronger route — direct observation (§2.1) — so its allocation candidacy is
closed. Remaining open candidacies: R-A/S-A as targets; R-B/S-B/S-C as
labeled scenarios only; F-V comparators, R-C, S-D, F-R-as-primary stay
rejected (see decision log D2A-03–D2A-05, D2A-11).

## 6. Allocation hierarchy

```text
Freight: Dataset 1-US Shipping Cost joined line-to-line (§2.1;
         ambiguity-controlled — NOT a pool, NOT allocated)
Future return/support pools (event-shaped; scenario layers, OFF by default)
        ↓  driver-weighted split, shares sum to 1.0 per pool
LINE (row_id) — the only grain where costs are stored
        ↓  pure summation (no further modeling)
order / customer / product / region / segment / category / month
        ↓  SUM(profit)/SUM(revenue) margins
```

Rules: freight arrives observed per line (join, with the §2.1 ambiguity
flag where applicable); scenario pools split top-down exactly once;
aggregates build bottom-up always;
no lateral re-allocation between aggregates (never move cost from one
customer to another to "balance"); no aggregate-level modeling pushed down.
Customer and product receive costs **only** via their lines.

## 7. Aggregation rules

- Costs and profits aggregate by **SUM** at every level (line → order →
  customer / product / region / segment / category / month / total).
- Margins aggregate as **SUM(Contribution Profit) / SUM(Net Revenue) × 100**
  — the Phase 1 §16 rule extended. Averaging row/order/customer margin
  percentages is forbidden (verified by the same class of check used in
  Phase 1C-3).
- Counts are distinct where entities are counted (orders, customers,
  products); sums where money or units move (revenue, costs, quantity).
- Discount-amount, gross-revenue, and quarantine rules from Phase 1A carry
  over unchanged.

## 8. NULL/zero handling

| Case | Rule |
|---|---|
| `Net Revenue = 0` | Contribution Margin % = NULL/blank (never divide by zero). None observed in source, but the guard is mandatory in code. |
| Cost component inapplicable to a line | Store **0 with method `NOT_APPLICABLE`** (e.g. a scenario that excludes a category) — never NULL, so sums stay meaningful and intent stays visible. |
| Cost component applicable but input missing | **NULL with method `PENDING_INPUT`** and fail-loud pipeline behavior: no silent zero-fill, no silent mean-fill. Aggregates over incomplete inputs must be labeled partial or blocked. |
| All driver weights zero within a pool | Undefined split — **fail loudly** (do not fall back to equal split silently; equal split requires its own documented method selection). |
| `Discount = 1` / nulls / non-positive quantity | Phase 1B/1C-3 guards already cover the observed data (none occur); any future input violating them aborts before allocation. |
| Margin change over time | Percentage points, never "%" (Phase 1A rule). |

## 9. Reconciliation & control totals

Each future allocation run must prove, not assert:

1. **Pool reconciliation** (scenario layers only — freight has no pool):
   Σ allocated lines == pool total per pool per period
   (tolerance documented in implementation; exact in exact arithmetic).
   Freight reconciles instead by join audit: 9,994/9,994 matched lines,
   line freight sum == US total 238,173.79, ambiguous order total == 25.05.
2. **Waterfall reconciliation**: `Contribution Profit = Net − COGS − serve`
   at line level, and identically `= Gross Profit − serve`; totals reconcile
   both ways.
3. **Margin reconciliation**: overall margin == SUM/SUM; per-group margins
   recomputed from sums, never averaged.
4. **Grain reconciliation**: row count and `row_id` set identical to the
   Phase 1 enriched fact (9,994); no rows lost, duplicated, or reordered
   silently.
5. **Method reconciliation**: two comparator methods on the same pool must
   both reconcile to the pool — their *difference* is the reported method
   uncertainty, not an error to hide.

## 10. Double-counting controls

1. **COGS appears exactly once**: it enters via frozen `modeled_cogs` and no
   serve-cost pool may contain product cost. Any future actual-COGS feed
   replaces the modeled input per key — it never adds beside it.
2. **Freight appears exactly once per line**: as the joined observed line
   charge (§2.1). A future directly-billed freight feed would replace the
   Dataset 1 value per line — never add beside it. Scenario-pool freight
   methods are withdrawn, so the allocated-XOR-direct conflict cannot arise
   for freight; the XOR rule remains in force for any future return/support
   pool that could duplicate a directly observed charge.
3. **Return revenue vs return cost**: refunded revenue (a revenue adjustment,
   relevant only if return events arrive) and handling cost (a serve cost)
   are separate fields with separate rules; netting them into one number is
   forbidden.
4. **No serve cost inside COGS, no COGS inside serve**: enforced by field
   lineage (serve fields derive only from serve pools + drivers, never from
   `modeled_cogs` or `implied_modeled_cogs_per_unit`).
5. **No double discount subtraction**: Phase 1A D01/D02 carry over — serve
   allocation bases use Net Revenue as observed, never re-net it.
6. **Quarantine extends**: `source_profit_quarantined` must not enter any
   serve-cost, contribution, or calibration computation. (Diagnostic
   comparison of modeled vs quarantined margins stays permitted as analysis,
   never as input.)

## 11. Observed vs modeled data distinction

Four evidence tiers, labeled on every future field and output:

| Tier | Meaning | Examples in this project | Labeling |
|---|---|---|---|
| **OBSERVED** | Directly in the source or frozen Phase 1 derivation | `ship_mode`, `region`, `quantity`, `sales`, `order_id`, `customer_id`, frozen `modeled_cogs` (frozen = fixed input, not re-estimated) | `source_*` / frozen Phase 1 names as-is |
| **MODELED** | Computed by approved, documented arithmetic from observed + assumed inputs | Future line freight shares, contribution profit/margin | `modeled_*` prefix (Phase 1 convention extended) |
| **BENCHMARK assumption** | Externally sourced rate/parameter with cited provenance (Phase 1C-3 discipline) | Future per-mode freight charges, return rates, cost-per-ticket | `assumed_*` inputs + `cogs_source`-style provenance columns |
| **FUTURE DATA requirement** | Real data that would replace assumptions | Return event feed, ticket feed, actual freight bills, actual COGS feed | Tracked in the decision log (§13); never simulated into existence |

Rule: a field's tier travels with it into Power BI labels and documentation.
A modeled number is never presented with observed-number confidence, and a
scenario number is never presented as the base case.

## 12. Assumptions governance

Every future non-observed input row carries: owner/source, assumption date,
effective period, methodology reference, status/confidence, business reason,
and append-only version history (supersede, never overwrite) — the Phase 1C-2
governance pattern extended from COGS to serve costs. Additional serve-
specific requirements: allocation method identifier per line (`F-H`, `R-B`,
…), driver snapshot (weights used), pool identifier + period, and comparator-
method outputs retained alongside base outputs so method uncertainty is
auditable. Statuses reuse the frozen enum style: `ACTUAL_*` (observed feeds),
`BENCHMARK_*` (sourced rates), `SCENARIO_*` (labeled what-ifs),
`PENDING_INPUT` (declared gaps) — actuals, benchmarks, and scenarios never
share a label.

## 13. Sensitivity-analysis requirements

Future implementation must ship with three sensitivity layers (design
requirement, not optional reporting):

1. **Parameter sensitivity**: each numerical assumption varied over its
   documented uncertainty band (bands set at sourcing time, same discipline
   as the ±5pp COGS analysis) — reported as profit/margin bands, never point
   estimates alone.
2. **Method sensitivity**: base method vs at least one comparator — now
   applying to return/support scenario designs (freight has no method
   uncertainty beyond the single flagged ambiguous order, reported with and
   without order-level treatment) — customer
   and product rankings must be shown under both; conclusions that flip are
   reported as fragile.
3. **Scope sensitivity**: with/without each scenario layer (returns on/off,
   support on/off) so the reader sees what the *evidence* says versus what
   the *scenarios* add. The evidence-only contribution view is always
   reported first.

Robustness standard (from Phase 1C-3): no profitability conclusion is
reported as robust unless it survives all three layers; tier separations may
be claimed only where bands do not overlap under asymmetric error.

## 14. Open design points (no numbers selected)

- Return rates/handling costs, support unit costs: unsourced by design in
  this phase (see decision log for sourcing plan). Freight is observed
  (§2.1) — no freight charges remain to be sourced.
- Scenario designs for R-B/S-B/S-C (build vs defer until event data):
  requires owner approval (see decision-log questions).
- Period grain for pools (order-event vs monthly pools): order-event pools
  are the default (§6); monthly pooling reserved for future freight-bill
  inputs that arrive aggregated. (Observed line freight needs no pooling.)
- Power BI field naming/display conventions: deferred to the dashboard
  phase; the dictionary (§12 artifact) reserves canonical names now.
