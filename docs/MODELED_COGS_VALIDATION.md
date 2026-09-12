# Modeled COGS Validation (Phase 1C-3)

> All figures below are the actual outputs of `src/data/apply_modeled_cogs.py`
> (run 2026-09-11). Every profit/margin value is **MODELED from industry
> benchmarks — not historical accounting COGS**. Full float precision is kept
> in the CSVs; display here is rounded to 2dp.

## 1. Financial reconciliation (overall)

| Metric | Value |
|---|---|
| Total Net Revenue (= Sales) | 2,297,200.86 |
| Total Quantity | 37,873 |
| Total Modeled COGS | 1,493,910.13 |
| Total Modeled Gross Profit | 803,290.73 |
| Overall Modeled Gross Margin % | 34.97% |
| Products (analytical) | 1,894 |
| Transactions (rows) | 9,994 |
| Orders | 5,009 |

Checks (tolerance ±0.05 unless stated):

- Total Modeled Gross Profit = Total Net Revenue − Total Modeled COGS:
  803,290.73 = 2,297,200.86 − 1,493,910.13 ✅ (Δ 0.00)
- Overall Modeled Gross Margin % = SUM(profit)/SUM(revenue)×100 = 34.97% ✅
  (computed from sums per §16 — never an average of row percentages)
- Row-level identity: modeled margin == benchmark on all 9,994 rows
  (max gap < 1e-6) ✅
- Zero-sales rows: 0; NULL modeled margins: 0; division-by-zero: none ✅

## 2. Sub-category reconciliation (all 17)

`modeled_gross_margin_pct = SUM(profit)/SUM(revenue)×100` per sub-category.
Each reconciles exactly to its assigned benchmark (rounding only).

| sub_category | net_revenue | quantity | benchmark % | COGS % | modeled_cogs | modeled_gross_profit | modeled margin % | level | confidence |
|---|---|---|---|---|---|---|---|---|---|
| Accessories | 167,380.32 | 2,976 | 35 | 65 | 108,797.21 | 58,583.11 | 35.00 | SUB_CATEGORY | MEDIUM |
| Appliances | 107,532.16 | 1,729 | 38 | 62 | 66,669.94 | 40,862.22 | 38.00 | CATEGORY | MEDIUM |
| Art | 27,118.79 | 3,000 | 38 | 62 | 16,813.65 | 10,305.14 | 38.00 | CATEGORY | MEDIUM |
| Binders | 203,412.73 | 5,974 | 38 | 62 | 126,115.89 | 77,296.84 | 38.00 | CATEGORY | MEDIUM |
| Bookcases | 114,880.00 | 868 | 40 | 60 | 68,928.00 | 45,952.00 | 40.00 | CATEGORY | MEDIUM |
| Chairs | 328,449.10 | 2,356 | 40 | 60 | 197,069.46 | 131,379.64 | 40.00 | CATEGORY | MEDIUM |
| Copiers | 149,528.03 | 234 | 30 | 70 | 104,669.62 | 44,858.41 | 30.00 | SUB_CATEGORY | MEDIUM |
| Envelopes | 16,476.40 | 906 | 38 | 62 | 10,215.37 | 6,261.03 | 38.00 | CATEGORY | MEDIUM |
| Fasteners | 3,024.28 | 914 | 38 | 62 | 1,875.05 | 1,149.23 | 38.00 | CATEGORY | MEDIUM |
| Furnishings | 91,705.16 | 3,563 | 40 | 60 | 55,023.10 | 36,682.07 | 40.00 | CATEGORY | MEDIUM |
| Labels | 12,486.31 | 1,400 | 38 | 62 | 7,741.51 | 4,744.80 | 38.00 | CATEGORY | MEDIUM |
| Machines | 189,238.63 | 440 | 25 | 75 | 141,928.97 | 47,309.66 | 25.00 | CATEGORY | MEDIUM |
| Paper | 78,479.21 | 5,178 | 38 | 62 | 48,657.11 | 29,822.10 | 38.00 | CATEGORY | LOW |
| Phones | 330,007.05 | 3,289 | 25 | 75 | 247,505.29 | 82,501.76 | 25.00 | CATEGORY | MEDIUM |
| Storage | 223,843.61 | 3,158 | 38 | 62 | 138,783.04 | 85,060.57 | 38.00 | CATEGORY | MEDIUM |
| Supplies | 46,673.54 | 647 | 38 | 62 | 28,937.59 | 17,735.94 | 38.00 | CATEGORY | MEDIUM |
| Tables | 206,965.53 | 1,241 | 40 | 60 | 124,179.32 | 82,786.21 | 40.00 | CATEGORY | MEDIUM |

## 3. Product-grain reconciliation (§19)

- Each of the 1,894 `analytical_product_key` values maps to exactly one
  `product_id`, `product_name`, `sub_category`, `benchmark_gross_margin_pct`,
  and `modeled_cogs_pct` (machine-asserted; 0 violations).
- No product receives multiple benchmark rates; no fact row receives multiple
  COGS rates (fact→assumption join is validated many-to-one; output = 9,994
  rows, `row_id` set identical to input).
- Status split: 160 products `MODELED_SUBCATEGORY` (Accessories/Copiers),
  1,734 `MODELED_CATEGORY`.

## 4. Implied per-unit semantics (correction-review limitation)

The model estimates COGS as a percentage of net revenue using industry
benchmark gross margins. The authoritative modeled COGS is always
`Net Revenue × Modeled COGS %` — it is never calculated as
`Quantity × implied unit cost` anywhere in the pipeline.

`implied_modeled_cogs_per_unit` is therefore explicitly defined as:

> "An implied analytical value equal to modeled COGS divided by observed
> quantity. It is derived from the revenue-based modeled COGS assumption and
> is NOT an actual physical unit cost."

Consequences, all machine-validated:

- At fact row level: `implied_modeled_cogs_per_unit = modeled_cogs /
  quantity` exactly (max gap 2.3e-13). Because it inherits the row's
  transaction price and discount, it varies across rows of the same product
  and must not be interpreted as a stable procurement/manufacturing cost per
  physical unit.
- At product level (`product_cogs_assumptions.csv`): the retained implied
  value is a derived reference (`product revenue × COGS % / product
  quantity`); the authoritative product-level information is
  key/sub-category/benchmark/COGS %/status/source/level/confidence.
- No validation expects `Quantity × implied unit` to equal authoritative
  COGS at row level — that equality is not the financial model definition.
  Consumers must aggregate `modeled_cogs`, never rebuild COGS from the
  implied unit.

## 5. Source preservation

- `fact_sales.csv` SHA-256 before and after: identical
  (`d7478eb5…c7e3261ee2`); row count still 9,994; `product_id`,
  `product_name`, `sales`, `quantity`, `discount`, and
  `source_profit_quarantined` bit-identical in the enriched output.
- `source_profit_quarantined` was not read for COGS (carried through
  untouched); no field named `profit`/`gross_profit`/`margin` without the
  `modeled_` prefix was created.
- Repeated execution produces byte-identical outputs (verified by hash
  comparison across two consecutive runs).
