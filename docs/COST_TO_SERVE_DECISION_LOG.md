# Cost-to-Serve Decision Log (Phase 2A)

> Append-only within Phase 2. New decisions take the next `D2A-NN` number and
> reference what they supersede. Phase 1 decisions (`docs/DECISION_LOG.md`,
> frozen) are cited, never edited. No numerical rates are selected anywhere
> in this log — method *families* are evaluated and shortlisted only.

## D2A-01 — Allocation grain is the order line (`row_id`)

- **Decision:** all serve costs terminate at the Phase 1 line grain; every
  aggregate is a pure sum of lines.
- **Alternatives:** order-level modeling without line split (rejected: cannot
  join revenue/COGS at order level without inventing line mixes);
  customer-level pools (rejected: no customer-level cost source exists).
- **Rationale:** the line is the only grain where all model terms are jointly
  observed; preserves the frozen grain and keeps every rollup additive.
- **Unresolved:** none (grain locked).

## D2A-02 — Hierarchy: pools split top-down once; aggregates build bottom-up

- **Decision:** order/event pools → driver-weighted line shares (sum to 1.0)
  → summation to order/customer/product/geography/time. No lateral
  re-allocation, no aggregate-modeled push-downs.
- **Alternatives:** top-down customer profitability targets (rejected:
  requires customer pools that do not exist).
- **Rationale:** guarantees pool reconciliation and prevents silent
  cross-subsidy between customers/products.
- **Unresolved:** pool period grain if freight bills arrive monthly (default:
  order-event pools; monthly pooling reserved — needs owner sign-off when
  data arrives).

## D2A-03 — Freight: hybrid ship-mode/quantity (F-H) leads evaluation

> **SUPERSEDED by D2A-11** (observed Dataset 1-US Shipping Cost joined, not
> allocated). Retained below as the pre-evidence audit trail — the F-H/F-Q/
> F-V/F-R/F-S candidacy is closed, not open.

- **Decision (method shortlist, NOT rate selection):** evaluate F-H first
  (ship-mode-differentiated order pool split by quantity), with F-Q
  (quantity-only) as the naivety baseline and F-V (value-based) as a
  comparator. F-R (region) reserved as a possible modifier, not a primary.
- **Alternatives considered:** F-Q alone (rejected as primary: ignores
  mode/weight heterogeneity across 4 ship modes and 14-line orders); F-V
  alone (rejected as primary: revenue-proportional cost compresses the margin
  dispersion the project exists to reveal); F-R alone (rejected: 4 regions,
  no origin warehouse — causal link too weak).
- **Rationale:** F-S uses the only observed logistics signal (`ship_mode`);
  quantity split is neutral and auditable; comparators expose method risk.
- **Rejected:** inventing per-mode charges from judgment in this phase.
- **Unresolved (needs owner approval):** final method choice; per-mode charge
  sourcing plan (carrier benchmarks vs future bills); within-order split
  confirmation.

## D2A-04 — Returns: event-data target (R-A); scenarios only until then

- **Decision:** return cost enters authoritatively only via a future return
  event feed (R-A). Until then, rate-based expectations (R-B) are permitted
  **solely as labeled, default-OFF scenario layers**; pattern-inferred
  proxies (R-C) are rejected entirely.
- **Alternatives considered:** R-B as base case (rejected: assigns costs to
  non-returning customers — a category expectation wearing event clothing);
  R-C (rejected: zero return signal exists, so any proxy fabricates events).
- **Rationale:** returns without events is the highest fabrication-risk area
  in Phase 2; the architecture must make invention structurally difficult.
- **Unresolved:** return-rate benchmark sourcing standard (mirror Phase 1C-3
  discipline?); refunded-revenue adjustment mechanics when events arrive.

## D2A-05 — Support: ticket-data target (S-A); proxies are scenario-only

- **Decision:** authoritative support cost requires future ticket/contact data
  (S-A). Order-frequency (S-B) and complexity-class (S-C) proxies are
  scenario-layer only, with S-B's loyalty-punishing bias stated on every
  output; intensity proxy (S-D) unbuildable today.
- **Alternatives considered:** S-B as base (rejected: perverse incentives —
  best customers look most expensive); S-C as base (rejected: classification
  itself unsourced).
- **Rationale:** same fabrication discipline as returns; support without
  contact records is opinion, not measurement.
- **Unresolved:** ticket↔order/customer linkage design; cost-per-ticket
  sourcing.

## D2A-06 — Contribution formulas restated with guards (no change in meaning)

- **Decision:** adopt Phase 1A formulas verbatim with `modeled_` prefixes and
  mandatory NULL-on-zero-revenue guards:
  `Contribution Profit = Net − COGS − Freight − Return − Support`;
  `Contribution Margin % = profit / Net × 100` (NULL if Net = 0).
- **Alternatives:** none (frozen formula restatement, not a new decision).
- **Rationale:** continuity with the approved waterfall; prefix discipline
  from the 1C-3 correction.
- **Unresolved:** none.

## D2A-07 — Double-counting controls carried over and extended

- **Decision:** six controls (§10 of the model doc): COGS-once, freight-once-
  per-line (allocated XOR direct, loader-rejected if both), revenue-vs-cost
  separation for returns, no COGS↔serve leakage, no re-netted discounts,
  extended Profit quarantine.
- **Alternatives:** trusting implementation care without load-time assertions
  (rejected: Phase 1 culture is fail-loud validation).
- **Rationale:** allocation architectures fail silently at exactly these
  seams; each control maps to a future machine check.
- **Unresolved:** tolerance values for pool reconciliation (set at
  implementation from float behavior, documented then).

## D2A-08 — Four-tier evidence labeling (observed / modeled / benchmark / future)

- **Decision:** every Phase 2 field and output carries its tier; tiers travel
  into BI labels; scenarios never presented as base, models never with
  observed confidence.
- **Alternatives:** two-tier observed/modeled only (rejected: hides the
  benchmark-vs-scenario distinction the portfolio reader needs).
- **Rationale:** extends the Phase 1 actual-vs-modeled discipline that the
  1C-3 correction hardened.
- **Unresolved:** BI display conventions (deferred to dashboard phase).

## D2A-09 — Triple-layer sensitivity is a ship requirement

- **Decision:** parameter bands + method comparators + scope on/off layers,
  with evidence-only contribution always reported first; robustness standard
  inherited from Phase 1C-3 (survive all layers or called fragile).
- **Alternatives:** point-estimate reporting with a footnote (rejected:
  repeats the false-precision failure mode Phase 1 was built to avoid).
- **Rationale:** serve costs are 100% assumption-driven at launch —
  uncertainty *is* the headline, not an appendix.
- **Unresolved:** band widths (set at sourcing time per input).

## D2A-10 — BI/mart compatibility by construction

- **Decision:** line-grain fact + existing frozen keys (`row_id`, `order_id`,
  `customer_id`, `analytical_product_key`) + specified field names = the BI
  contract; aggregates stay as queries, marts (if any) reconcile to line
  sums exactly.
- **Alternatives:** pre-aggregated customer/product tables as primary
  outputs (rejected: breaks drill-through and hides method seams).
- **Rationale:** keeps every dashboard number traceable to a line and a
  method.
- **Unresolved:** none at architecture level.

## D2A-11 — Freight allocation modeling superseded by observed Shipping Cost

- **Decision:** use observed Shipping Cost from Dataset 1-US instead of any
  modeled freight allocation. Freight is joined line-to-line by composite
  signature — not allocated, not modeled.
- **Rationale:** the compatibility investigation established a 100%
  composite-signature transaction match to the frozen Phase 1 universe.
- **Evidence:** 9,994/9,994 rows matched, 0 unmatched either side; sales,
  quantity, discount distribution, customers, products, ship/region/segment
  counts reconcile exactly (`docs/PHASE_2_DATA_COMPATIBILITY_REPORT.md` §4).
- **Important exception:** one composite-key ambiguity prevents unique
  row-level assignment for two lines (Phase 1 rows 3406/3407 ↔ Dataset 1
  rows 34702/34703 at 21.59 and 3.46).
- **Resolution:** do not randomly assign line values. Preserve the invariant
  order-level freight total of 25.05, flag both rows (`freight_ambiguity_flag
  = TRUE`, `freight_method = ORDER_LEVEL_AMBIGUOUS`), and aggregate freight
  from the order total for that order. No deterministic split is invented.
- **Also recorded:** direct Order ID matching rejected (recoded IDs, 0%
  intersection — different formats do not mean different transactions, but
  IDs cannot be the join); composite signature approved as the enrichment
  mechanism (Product Name excluded — coarser labels on 197 rows); Dataset 2
  Returns rejected (incompatible ID universe, 0/1,970 matches; order-level
  `Yes`-only with no quantity/refund/date/reason — return status stays
  non-authoritative, processing cost scenario-OFF).
- **Supersedes:** D2A-03's F-H evaluation shortlist (record retained above
  for audit trail; methods withdrawn, not deleted from history).
- **Unresolved:** nothing on freight method — closed by evidence. Remaining
  owner approvals: R-B/S-B/S-C scenario build-vs-defer; pool period grain
  for monthly-arriving inputs; return-rate sourcing standard.

## D2A-12 — Phase 2B implementation choices (scenarios OFF baseline)

- **Decision:** build `fact_margin_map_phase2.csv` with observed freight +
  crosswalked return status; NULL (not split, not zero) line freight on the
  ambiguous pair with order total preserved via `freight_order_total`;
  return/support scenarios 0/FALSE; contribution NULL-propagating.
- **Rationale:** only representation that refuses to invent the 21.59/3.46
  assignment while keeping every total reconcilable; NULLs force downstream
  consumers to confront the 2-line gap instead of inheriting a hidden choice.
- **Also recorded:** brief's freight file pointer corrected on evidence
  (workbook Orders sheet has no Shipping Cost column; Dataset 1-US used —
  join total matches expected to the cent); summed contribution therefore
  excludes 225.10 ambiguous-line gross profit (order-level view unaffected).
- **Unresolved:** none for the baseline — scenario activation decisions
  remain future owner approvals.

## D2A-13 — Order grain authoritative for contribution (2B.1 correction)

- **Decision:** `order_margin_map_phase2.csv` (5,009 orders) is the
  authoritative aggregation for overall/order/customer-level contribution;
  the ambiguous pair total (25.05) is applied at order level only, never
  split to lines 3406/3407 (still NULL + flagged in the line fact).
- **Rationale:** line SUM understated project contribution by 200.0476
  through correct-but-undesirable NULL propagation; order freight is fully
  known (26.55 incl. 1.50 unique lines — cross-checked both paths).
  Expected baseline 565,116.9418 / 24.60% reproduced exactly.
- **Boundary set:** product-level contribution explicitly NOT licensed by
  this correction — needs its own attribution decision.
- **Unresolved:** none for 2B.1.

## Data limitations acknowledged (not solved) in this phase

No freight dollars, no return events, no tickets, no channel, no weight, no
origin warehouse; 2,471 multi-line orders force a split rule; ship mode and
region are coarse; reseller-vs-manufacturer channel caveat from Phase 1
carries into any revenue-scaled reasoning. Each limitation maps to a
FUTURE-DATA requirement or a labeled scenario — none is papered over.

## Questions requiring owner approval

1. ~~Final freight method selection (F-H vs alternatives) and per-mode charge
   sourcing plan.~~ **RESOLVED by D2A-11** (observed Shipping Cost; no
   allocation, no charges to source).
2. Whether R-B/S-B/S-C scenario layers should be built at all in
   implementation, or deferred until event data exists.
3. Pool period grain if freight inputs arrive monthly rather than per order.
4. Return-rate benchmark sourcing standard and refunded-revenue mechanics.
