# Phase 3B — Observed Discount Impact Analysis

> Status: **IMPLEMENTATION — observed historical data only (descriptive).**
> Built by `src/data/build_phase3b_discount_analysis.py` → seven summary
> CSVs plus `phase3b_quality_report.json` (16/16 fail-loud checks pass;
> byte-identical across consecutive runs; frozen Phase 1/Phase 2 inputs
> byte-identical before and after). Design authority: the frozen Phase 3A
> architecture record; adoption decisions in `PHASE_3B_DECISION_LOG.md`;
> machine validation in `PHASE_3B_VALIDATION.md`.
>
> **Reading guide — what this analysis is and is not.** Every pattern below
> is a descriptive association observed in historical transactions,
> conditional on the modeled cost structure. Discount and quantity may each
> be affected by product, customer, category, time, and other unrecorded
> factors; the dataset contains no controlled discount experiments and no
> independently observed pre-discount price history. Nothing here estimates
> demand response, and no observed association is presented as proof that a
> discount level moved quantities, revenue, or profit.

## 1. Scope and standing

Phase 3B implements the observed-discount half of the Phase 3A design. It
measures historical discount levels and compares revenue, quantity, modeled
gross profitability and — only where analytically licensed — authoritative
contribution profitability across discount bands at overall, Segment,
Category, Sub-Category, Customer, order, and (flagged reference only)
Product grains. Out of scope, by mandate: elasticity estimation, pricing or
discount What-if scenarios, quantity-response assumptions, causal claims,
Power BI artifacts, and any change to frozen Phase 1/Phase 2 files,
scripts, or documents.

## 2. Measure lineage and file conventions

Each output distinguishes four labeled layers. Column names carry the layer
where the name alone could mislead; the decision log and this section carry
the rest. No column is ever described by the bare word "profit" or "margin"
without its layer.

| Layer | Meaning | Columns / markers |
|---|---|---|
| Observed historical | Directly in the frozen inputs | `sales` (= net revenue), `quantity`, `discount`, `segment`, `category`, `sub_category`, `customer_id`, `order_id`, `freight_cost_observed`, `return_status` (filter flag only) |
| Derived discount | Reconstructed from observed inputs under frozen formulas | `gross_revenue`, `discount_amount`, `wad`, `discount_amount_pct_of_gross`, `revenue_realization_rate`, `discount_band`, `order_wad` — derived reference values, never observed list prices |
| Modeled gross-profit | Phase 1 benchmark model reused read-only (analytical estimate, not accounting cost) | `modeled_cogs`, `modeled_gross_profit`, `modeled_gross_margin_pct` — conditional on the benchmark structure throughout |
| Authoritative contribution | Joined from `order_margin_map_phase2.csv`, never recomputed | `freight_cost`, `cost_to_serve`, `contribution_profit`, `contribution_margin_pct` on ORDER-basis rows, marked `AUTHORITATIVE_ORDER`; scenarios OFF |

Grain and authority markers on every summary row: `basis` (`ORDER` vs
`LINE`) on band/segment files; `row_type` (`*_TOTAL`, `*_BAND`) on
customer/product files and `TOTAL` band rows elsewhere;
`contribution_authority` (`AUTHORITATIVE_ORDER`,
`LINE_PARTIAL_EXCL_AMBIGUOUS`, `NOT_LICENSED_GROSS_ONLY` with
`null_reason = FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN`);
`low_sample_flag` (provisional 30-line / 10-order thresholds, D3B-02);
`low_volume_flag` (single-order products) on the product file;
`ambiguity_note` on the one affected order;
`negative_contribution_flag` per order. Association language throughout is
"observed", "associated with", "descriptive comparison", "historical
pattern", "conditional on the modeled cost structure".

## 3. Method (summary; full specification in the decision log and script)

- **Bands (D3B-01):** fixed B0 `d = 0` / B1 `(0, 0.15]` / B2 `(0.15, 0.25]` /
  B3 `(0.25, 0.35]` / B4 `(0.35, 0.55]` / B5 `(0.55, 0.80]`. All 9,994 lines
  assigned exactly one band (B0 4,798; B1 146; B2 3,657; B3 254; B4 283;
  B5 856); zero group exact; no observed value split; deterministic.
- **Order bands (D3B-03):** single rule — order WAD band. All 5,009 orders
  assigned exactly one band (B0 2,055; B1 415; B2 1,634; B3 278; B4 274;
  B5 353). All orders verified single-segment and single-customer, so
  order-basis attribution is clean. No quantile comparator (D3B-04).
- **Contribution (D3B-06):** authoritative at order grain and above;
  product/category/sub-category gross-profit-only (NULL contribution);
  ambiguous pair never imputed (NULL + flagged at line grain; 25.05 pair
  total held at order `US-2014-150119`, flagged in the order file).
- **Reconciliation:** ORDER TOTAL contribution 565,116.94 at 24.6002%
  equals the frozen Phase 2 baseline exactly; LINE partial trails it by the
  stated 200.05 gap; segment, customer, band, and order files all reconcile
  to the same baseline.

## 4. Overall × discount band (authoritative, ORDER basis)

| Band | Orders | Net revenue | Discount amount | WAD | Realization | Gross margin¹ | Freight | Contribution | Contrib. margin¹ | Neg-contrib orders |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 — No discount | 2,055 | 862,202.39 | 0.00 | 0.0000 | 100.00% | 35.41% | 84,314.69 | 220,993.53 | 25.63% | 14 |
| B1 — Low | 415 | 328,153.86 | 25,655.84 | 0.0725 | 92.75% | 35.38% | 36,145.63 | 79,940.04 | 24.36% | 3 |
| B2 — Standard | 1,634 | 669,040.97 | 163,026.43 | 0.1959 | 80.41% | 34.32% | 73,110.88 | 156,514.93 | 23.39% | 24 |
| B3 — Elevated | 278 | 172,284.09 | 73,601.50 | 0.2993 | 70.07% | 37.70% | 19,429.93 | 45,515.82 | 26.42% | 1 |
| B4 — High | 274 | 203,630.91 | 155,420.06 | 0.4329 | 56.71% | 32.18% | 18,744.49 | 46,790.74 | 22.98% | 3 |
| B5 — Deep | 353 | 61,888.64 | 149,030.35 | 0.7066 | 29.34% | 35.21% | 6,428.17 | 15,361.88 | 24.82% | 5 |
| TOTAL | 5,009 | 2,297,200.86 | 566,734.18 | 0.1979 | 80.21% | 34.97% | 238,173.79 | 565,116.94 | 24.60% | 50 |

¹ Conditional on the modeled cost structure (§13).

Descriptive reading, in historical-pattern terms: the no-discount band
holds the largest observed contribution share (39.11% of baseline
contribution on 37.54% of net revenue), followed by the standard-discount
band (27.70% of contribution on 29.13% of revenue); the deep-discount band
holds 2.69% of net revenue and 2.72% of contribution at a 29.34%
realization rate. Authoritative contribution margins across bands span
22.98%–26.42% — a narrow observed range that reflects the joint effect of
benchmark mix and observed freight within each band, not a measured
discount effect. The LINE-basis companion rows (file `basis = LINE`) show
the same ordering at 24.59% overall partial margin with zero
negative-gross-profit lines and 109 negative-contribution lines; the 200.05
gap to the authoritative total is the documented held-at-order economics,
not missing data.

Quantity descriptives are reported strictly as co-occurrence. Quantity per
order (ORDER basis) is observed at 6.71 (B0), 12.18 (B1), 6.69 (B2), 10.47
(B3), 10.26 (B4), 6.74 (B5) against 7.56 overall — while quantity per line
(LINE basis) is observed at 6.91 (B0), 4.08 (B1), 5.68 (B2), 4.08 (B3),
4.22 (B4), 4.89 (B5). The B1 contrast is compositional on its face: the 415
B1 orders contain 1,324 lines (3.19 per order), of which 799 lines carry
zero discount and 387 carry standard 0.20 discount — B1 at order grain is
predominantly multi-line mixed orders whose average falls in the low band.
B3 orders likewise span line discounts from 0.00 to 0.80. Band-level
quantity comparisons therefore compare different order compositions, and
are presented as such — they do not isolate any discount influence.

## 5. Segment × discount band (authoritative, ORDER basis)

Segment ORDER totals are observed close together: Consumer 24.76%
contribution margin (WAD 0.2026; 2,586 orders), Corporate 24.60% (WAD
0.1827; 1,514 orders), Home Office 24.16% (WAD 0.2094; 909 orders) — a
descriptive comparison across segments whose WADs differ by at most 2.7
percentage points.

Authoritative contribution margin by segment × band:

| Segment | B0 | B1 | B2 | B3 | B4 | B5 | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Consumer | 25.94% | 24.42% | 23.65% | 26.85% | 22.43% | 24.87% | 24.76% |
| Corporate | 25.59% | 24.70% | 23.16% | 25.78% | 22.79% | 26.57% | 24.60% |
| Home Office | 24.86% | 23.74% | 23.03% | 26.25% | 24.48% | 22.35% | 24.16% |

The elevated-discount band shows the highest observed margin within each
segment (26.85 / 25.78 / 26.25%), while the lowest observed cell differs by
segment (B4 in Consumer and Corporate; B5 in Home Office). These are
within-segment historical patterns; cross-band differences combine
benchmark mix, freight incidence, and order composition, and are not
attributed to the discount level. All 39 segment rows (18 ORDER band cells
+ 18 LINE band cells + 3 ORDER totals) carry counts and flags; no segment
cell breaches the provisional thresholds except where noted in-file.

## 6. Category × discount band (gross-profit-only, LINE basis)

Category totals: Furniture 40.00% modeled gross margin (WAD 0.1998; 2,121
lines); Office Supplies 38.00% (WAD 0.1995; 6,026 lines); Technology 27.90%
(WAD 0.1948; 1,847 lines). Category WADs are observed nearly identical
(0.195–0.200) — discount intensity, as revenue-weighted, does not separate
the three categories in this sample.

Two structural facts dominate this cut and both are stated on the output.
First, Furniture reads 40.00% and Office Supplies 38.00% in *every*
occupied band by construction of the revenue-based benchmark model — these
cells restate assumption × mix and must not be read as a discovery about
discounts. Second, Technology band margins (29.02 / 25.00 / 27.45 / 25.00 /
25.78 / 25.00%) move only with the sub-category mix inside each band
(Accessories 35% vs Copiers 30% vs Machines/Phones 25%), for the same
reason. Office Supplies has no observed lines in B3 or B4 (2 of 18 band
cells unoccupied — a compositional fact about where Office Supplies
discounts fall, preserved as absent rows rather than zeros). Contribution
is NULL throughout with the attributable-grain reason.

## 7. Sub-Category × discount band (gross-profit-only, LINE basis)

Observed WAD spreads widely across sub-categories while margins equal
benchmarks by construction: Binders 0.3868, Machines 0.3431, Tables 0.2547,
Bookcases 0.2246, Phones 0.1663, Chairs 0.1660, Appliances 0.1532,
Furnishings 0.1475, Copiers 0.1448, Fasteners 0.0903, Envelopes 0.0818, Art
0.0774, Supplies 0.0749, Paper 0.0746, Storage 0.0686, Accessories 0.0682,
Labels 0.0610. The file holds 52 occupied band cells of 102 possible (sparse
pairings absent, not zero-filled) plus 17 sub-category TOTALs; 10 band cells
carry `low_sample_flag` and remain visible with flags. All 17 TOTAL rows
pass the provisional thresholds. Sub-category margins restate benchmark ×
mix and are labeled accordingly; contribution is NULL with reason.

## 8. Customer summaries (authoritative, order basis)

793 customer TOTAL rows plus 2,511 occupied customer × band rows (3,304 rows
total). Customer WAD is observed with median 0.1624 (mean 0.1777, range
0.0000–0.7394). Customer contribution margin is observed with median
25.74% (mean 24.73%, minimum 0.32%) — zero negative-contribution customers
in the baseline, consistent with the Phase 2C structural finding (positive
benchmark margins on every line; observed freight never exceeding a
customer's gross profit), conditional on scenarios remaining OFF. The 50
negative-contribution orders are preserved at order grain and distributed
across their customers' totals rather than averaged away.

Discount-band activity per customer: 35 customers active in 1 band, 182 in
2, 280 in 3, 219 in 4, 66 in 5, 11 in all 6. Primary band (by gross
revenue) is observed as B0 for 256 customers and B2 for 255, then B1 (88),
B4 (83), B3 (68), B5 (43). Flag disclosure: 782/793 TOTAL rows and
2,511/2,511 band rows fall below the provisional thresholds — i.e.,
within-customer band detail is arithmetic throughout, and even customer
totals are thin for most accounts (mean 12.6 lines per customer). The flags
are the finding: customer-level discount inference in this sample rests on
small cell sizes, stated row by row.

## 9. Order summaries (authoritative, 5,009 rows)

One row per order joining authoritative contribution with the line-derived
discount rollup: order WAD (median 0.1607, mean 0.1606), order band,
realization rate, modeled gross profit/margin, freight, cost-to-serve,
contribution and margin, return status (filter context only), line count,
and quantity. Fifty orders carry `negative_contribution_flag = TRUE`;
zero orders are gross-negative at the modeled layer. Order
`US-2014-150119` carries
`ambiguity_note = ORDER_CONTAINS_AMBIGUOUS_PAIR_25P05_HELD_AT_ORDER` with
full-order freight 26.55; its two ambiguous lines remain NULL and flagged
in the frozen line fact, untouched.

## 10. Product summaries (flagged reference only, gross-profit-only)

1,894 PRODUCT_TOTAL rows plus 4,031 occupied PRODUCT_BAND rows (5,925 rows
total), all carrying `low_sample_flag = TRUE`, with `low_volume_flag`
retained on the 93 single-order products. Products average 5.28 lines
(median 5, maximum 15) and span a mean of 2.13 bands — no product-level
discount comparison in this file meets the provisional thresholds, so the
file is a descriptive reference for higher-volume-product lookup, excluded
from comparative statements. Contribution is NULL with reason throughout.

## 11. Negative-profit visibility (where the grain permits)

- Line grain: 0 negative-gross-profit lines (structurally guaranteed under
  positive benchmark margins); 109 negative-contribution lines (B0 44, B2
  46, B5 11, B4 6, B3 2, B1 0), excluding the two NULL ambiguous lines.
- Order grain: 50 negative-contribution orders (B0 14, B2 24, B5 5, B1 3,
  B4 3, B3 1), preserved with flags in the order file and summed (not
  averaged) into every aggregate.
- Customer grain: 0 negative-contribution customers; the 50 negative orders
  are absorbed in aggregation and remain visible only via the
  `neg_contribution_orders` counts.
- Product / category / sub-category grains: negative-gross counts reported
  (all zero at product level, minimum modeled gross profit 0.62 carried
  from Phase 2C); negative-contribution counts NULL (not licensed).

## 12. Sample-size disclosure

Every output row carries `line_count` and `order_count` with
`low_sample_flag`. Flag rates: band file 0/14; segment file 0/39; category
file 0/19 (2 cells structurally absent); sub-category file 10/69; customer
file 3,293/3,304; order file not applicable per-row (single observations;
flag column present and FALSE with documented meaning); product file
5,925/5,925. Thin cells are shown with flags, never suppressed or merged.

## 13. Limitations (binding on any reuse)

1. All margins are conditional on the modeled cost structure: benchmark
   COGS scales with net revenue, so within-benchmark-group gross margins
   are constant across bands by construction (§6); scenario-style
   fixed-unit-cost reasoning is not licensed on these numbers.
2. Freight is observed with an unverified in-file methodology (Phase 2
   compatibility caveat carried forward); the ambiguous pair treatment is
   exact but leaves line-grain contribution partial.
3. Return status is order-level filter context only; no refunded-revenue or
   return-cost adjustment is embedded; the one UNKNOWN order is never
   defaulted.
4. Return/support scenario layers are OFF; zero means excluded, not actual.
   The zero-loss-customer observation is conditional on this baseline.
5. Fine grains are thin (customer × band fully flagged; product fully
   flagged) — comparative statements at those grains are out of scope.
6. No causal, elasticity, optimality, or policy language is licensed on
   these outputs; the reading guide above travels with every reuse.

## 14. File inventory and handover

New files (this phase only): `discount_band_summary.csv` (14 rows),
`discount_segment_summary.csv` (39), `discount_category_summary.csv` (19),
`discount_subcategory_summary.csv` (69), `discount_customer_summary.csv`
(3,304), `discount_order_summary.csv` (5,009),
`discount_product_summary.csv` (5,925), `phase3b_quality_report.json`;
script `src/data/build_phase3b_discount_analysis.py`; documents
`PHASE_3B_DISCOUNT_ANALYSIS.md` (this file), `PHASE_3B_DECISION_LOG.md`,
`PHASE_3B_VALIDATION.md`. Phase 3B ends here; pricing scenarios and
elasticity modeling are not started.
