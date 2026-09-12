# Phase 2 Freeze

> Freeze audit executed 2026-09-12. Verdict: **PASS** — 40/40 quantitative
> checks green, reproducibility byte-identical across reruns, and Phase 1
> remained byte-identical throughout. The Phase 2 working checkpoint
> (2929bcd, 2026-09-12) was established prior to the freeze audit. This
> document records the validated Phase 2 freeze state.

## Scope

Phase 2A (cost-to-serve architecture), Phase 2B (transaction fact +
order-level contribution model, including 2B.1 correction), and Phase 2C
(customer, margin-risk, product, and sub-category profitability analysis).

## Financial Baseline

Revenue **2,297,200.8603** · COGS **1,493,910.1285** · Freight **238,173.79**
· Cost-to-Serve 238,148.74 at line grain (25.05 held at order level) ·
Contribution Profit **565,116.9418** · Contribution Margin **24.6002%**
(SUM/SUM; scenarios OFF).

Formulas:
- Cost-to-Serve = Freight + Return Processing Cost + Support Cost
- Contribution Profit = Revenue − COGS − Cost-to-Serve
- Margin = Contribution Profit / Revenue
- Margin is NULL when Revenue = 0

## Observed Data

- **Freight:** observed Shipping Cost from Dataset 1-US, joined to the
  Phase 1 transaction universe (9,994/9,994 rows). Line-grained, with a US
  total of 238,173.79. Source methodology remains subject to the documented
  compatibility caveat.
- **Return Status:** observed order-level YES for 296 orders through a
  validated suffix crosswalk with year-offset consistency and line-set
  verification. Remaining orders are classified as NOT_RETURNED under the
  documented completeness assumption, with `CA-2015-102015` retained as
  UNKNOWN rather than defaulted.

## Modeled Components

COGS uses the frozen Phase 1 benchmark model and is reused without
modification. No new modeled costs were introduced in Phase 2.

## Scenario Components

Return Processing Cost and Support Cost are specified as scenario components
and remain **OFF / zero** in the baseline because no authoritative rates
exist. Zero values indicate exclusion from the baseline, not observed
actual costs.

## Key Analytical Outputs

- `fact_margin_map_phase2.csv` — 9,994 lines × 49
- `order_margin_map_phase2.csv` — 5,009 orders; authoritative for
  contribution aggregation
- `customer_profitability.csv` — 793 customers
- `customer_margin_risk.csv` — median-based quadrants; 30
  HIGH_REVENUE_LOW_CONTRIBUTION customers; 0 loss-making customers in the
  baseline
- `product_profitability.csv` — 1,894 products; gross-profit analysis with
  93 single-order products flagged
- `subcategory_profitability.csv` — 17 sub-categories; gross-profit analysis
- `customer_subcategory_profitability.csv` — 6,002 customer-sub-category
  combinations; gross-profit analysis with contribution explicitly NULL

## Known Limitations

- Return status is available only at order level; quantity, refund amount,
  return date, reason, and return cost are unavailable.
- One order contains an ambiguous line-level freight pairing (rows 3406/3407).
  Freight remains NULL and flagged at line grain; the 25.05 freight total is
  retained at order level. Their 225.10 gross profit is excluded from the
  line-level contribution sum.
- Product and sub-category views do not contain product-level freight
  attribution and are therefore presented on a gross-profit basis.
- Return Processing Cost and Support Cost are OFF in the baseline. The
  zero-loss-customer finding is therefore conditional on the baseline cost
  configuration.
- Source Profit from the original dataset remains quarantined and is excluded
  from all computations.

## Validation

- 40/40 quantitative checks passed across the line fact, order fact,
  profitability outputs, and business sanity checks. Reconciliations and
  ambiguity calculations were verified.
- Ambiguous freight mathematics verified:
  21.59 + 3.46 = 25.05; the complete affected order freight is 26.55,
  including 1.50 from uniquely matched lines.
- Reproducibility confirmed: all three Phase 2 pipelines re-ran successfully,
  with all Phase 2 outputs and selected Phase 1 reference files remaining
  byte-identical by SHA-256.
- Phase 1 freeze hashes remain unchanged, with the quarantined source Profit
  excluded from all calculations.
- Repository validation confirmed the Phase 2 checkpoint is present, external
  workbooks are not tracked, no nested repositories exist, and no temporary,
  debug, stale, or duplicate artifacts were identified.
- `notebooks/`, `sql/`, and `powerbi/` remain placeholder directories pending
  subsequent implementation.

## Freeze Status

**PHASE 2 FROZEN**

Freeze date: 2026-09-12.