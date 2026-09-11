# MarginMap — Data Quality Report (Phase 1B)

> Pipeline: `src/data/prepare_fact_sales.py` (run from project root).
> Output: `data/processed/fact_sales.csv` + `data/processed/data_quality_report.json`.
> Source: `archive.zip` → `Sample - Superstore.csv` (read-only, never modified).
> All numbers below are the actual observed run results, not estimates.

## 1. Purpose

Prove that the Phase 1B fact table is a complete, typed, faithful derivation of
the source CSV — no rows lost, no values invented, every anomaly flagged rather
than silently fixed — so later phases (COGS, cost-to-serve, pricing) build on a
trusted foundation.

## 2. Source dataset

- `archive.zip` (project root, unmodified) → exactly one CSV:
  `Sample - Superstore.csv` (2,287,806 bytes uncompressed).
- Pipeline fails loudly if the archive is missing, the CSV is missing, extra
  CSVs create ambiguity, or any of the 21 expected columns is missing/extra.

## 3. Source encoding

- `latin1`, as established in Phase 0. UTF-8 read fails (`0xa0` byte).
- Script hard-codes `encoding="latin1"`; decode failure aborts with the error.

## 4. Fact-table grain

- **One row = one product line within an order**, keyed by `row_id`.
- NOT aggregated by `Order ID`: 5,009 unique orders → 2,538 single-line orders
  + 2,471 multi-line orders (avg ~2.0 lines/order). Multi-line orders expected.

## 5. Row count

- Source rows: **9,994**. Fact rows: **9,994**. Zero rows added, removed, or merged.

## 6. Column count

- Source: 21 columns. Fact: **25 columns** = 21 canonical renames + 1 approved
  alias (`net_revenue`) + 3 boolean flags. No source column dropped
  (`Profit` retained as `source_profit_quarantined`). No modeled cost columns.

## 7. Data types

| Column | Type in pipeline | Note |
|---|---|---|
| `row_id` | Int64 | unique, non-null |
| `order_id`, `customer_id`, `product_id`, names, city, state | string (stripped) | IDs/keys as text |
| `ship_mode`, `segment`, `country`, `region`, `category`, `sub_category` | string | low-cardinality dims kept as text for CSV transparency |
| `order_date`, `ship_date` | datetime (ISO `YYYY-MM-DD` in CSV) | explicit `%m/%d/%Y` parse |
| `postal_code` | **string** | never numeric, never zero-filled |
| `sales`, `discount`, `source_profit_quarantined`, `net_revenue` | float64 | |
| `quantity` | Int64 | |
| 3 flag columns | bool | |

CSV transparency note: CSVs carry no types, so a naive `pd.read_csv` infers
`postal_code` as int64 (all values are plain digits, no missing). Consumers
**must read `postal_code` as string** (`dtype={"postal_code": str}`) and keep
it as text in Power BI/SQL. In-pipeline dtype is string; nothing was lost.

## 8. Missing values

- **0 missing in every column** — confirmed independently (source had 0 nulls;
  cleaning introduced 0 nulls: numerics coerced with failure-on-NaN, dates with
  failure-on-NaT).
- `postal_code`: 0 missing (see §13 for the "11 missing" discrepancy note).

## 9. Duplicate analysis

- Fully-duplicate rows: **0**. `row_id`: 9,994 unique / 9,994 rows, 0 nulls.
- Duplicate `Order ID` values (4,985 extra lines over 5,009 orders) are line-item
  grain, not a defect.

## 10. Key validation

- `order_id`, `customer_id`, `product_id`: 0 null/blank (fail-loud checks).
- `Customer ID` ⟷ `Customer Name`: 1:1 (793 ↔ 793, consistent with Phase 0).
- Product key = `product_id` (1,862 unique). `product_name` is attribute only —
  it is NOT unique (1,850 names; 32 IDs map to 2 names each, §14).

## 11. Date validation

- Parse: explicit `format="%m/%d/%Y"` (no blind inference). 0 unparseable in
  either column (any NaT would abort).
- Range: order `2014-01-03 → 2017-12-30`; ship `2014-01-07 → 2018-01-05`.
- Rule `ship_date >= order_date`: **0 violations** (any violation aborts).

## 12. Numeric validation

- `sales`, `quantity`, `discount`, `source_profit_quarantined`: 0 null/non-numeric,
  0 infinite (all fail-loud).
- Range rules — all pass, 0 violations:
  `Sales >= 0` (0 negative, 0 zero) · `Quantity > 0` (range 1–14, total 37,873) ·
  `Discount >= 0` · `Discount < 1` (12 distinct values: 0.0 ×4,798; 0.2 ×3,657;
  0.7 ×418; 0.8 ×300; 0.3 ×227; 0.4 ×206; 0.6 ×138; 0.1 ×94; 0.5 ×66; 0.15 ×52;
  0.32 ×27; 0.45 ×11 — identical to Phase 0).
- `source_profit_quarantined`: 65 zeros; negatives preserved as observed
  (no deletion, no capping).

## 13. Postal Code validation

- Stored as **string**; missing preserved as null (never 0, never inferred).
- Missing: **0 of 9,994 (0.000%)**.
- Discrepancy note: the Phase 1B brief stated "Phase 0 found 11 missing Postal
  Code values." Phase 0 actually reported **0 missing**, and this phase
  independently confirms **0 missing** (`Postal Code` non-null in all 9,994
  source rows). The "11" premise is not supported by the data. No action taken;
  no rows touched.

## 14. Product ID / Product Name consistency

- 32 of 1,862 Product IDs (1.7%) map to **2 distinct names each**, covering
  **337 rows**. Full list in `data_quality_report.json`
  (`stats.product_ids_multi_name_list`).
- Range: near-variants (`OFF-PA-10001970` → `Xerox 1881` vs `Xerox 1908`) up to
  entirely different products (`TEC-AC-10003832` → Imation flash drive vs
  Logitech speakerphone). This is a source-data limitation for product-level
  analysis, not a cleaning error. **Preserved as-is; flagged** via
  `has_product_name_conflict`.

## 15. Implied unit-price diagnostic (diagnostic ONLY, not an official metric)

- `implied_unit = sales / (quantity × (1 − discount))`, computed where
  `quantity > 0` and `discount < 1` (all 9,994 rows qualify).
- 32 Product IDs show >1 distinct implied unit price (rounded to cents) —
  **exactly the same 32 IDs as the name-conflict set** (§14). Consistent with
  ID reuse across distinct products rather than price drift.

## 16. FUR-BO-10002213 investigation

- **Confirmed, preserved, flagged — not modified, averaged, or removed.**
- 10 rows split across two products sharing one ID:
  - `DMI Eclipse Executive Suite Bookcases` — 6 rows, implied unit **500.98**
    (row_ids 2116, 5919, 6536, 9396, 9584, 9650).
  - `Sauder Forest Hills Library, Woodland Oak Finish` — 4 rows, implied unit
    **140.98** (row_ids 2472, 2809, 5080, 8713).
- Because both name AND price differ, this is an ID collision, not a price
  change. Row-level flag `has_implied_unit_price_issue` marks these 10 rows;
  the other 31 collided IDs are covered by `has_product_name_conflict` (§18).

## 17. Source Profit quarantine

"The source Profit field is preserved for reference but quarantined because its
original calculation methodology has not been established."
- Kept as `source_profit_quarantined` (deliberately NOT named `profit`, to avoid
  implying it is the official MarginMap metric). Total 286,397.0217 matches
  audit (§20). Never used in any calculation — the pipeline computes nothing
  from it (in particular, never `COGS = Sales − Profit`).

## 18. Financial fields available

- `sales` (source) + `net_revenue` alias (`net_revenue = sales` exactly —
  verified `True` on all 9,994 rows; documented alias, not a calculation).
- `quantity`, `discount`, dates, all order/customer/product/geo dimensions,
  quarantined profit for reference.

## 19. Fields intentionally NOT created

COGS, COGS per unit, Gross Profit/Margin, Freight, Return, Support,
Total Cost-to-Serve, Contribution Profit/Margin, elasticity/scenario outputs.
`data_quality_report.json` records `"modeled_fields_created": []`. Any future
modeled field requires methodology + assumption + validation (per Phase 1A).

## 20. Reconciliation results (tolerance ±0.05)

| Check | Source/audit | Fact table | Result |
|---|---|---|---|
| Rows | 9,994 | 9,994 | ✅ match |
| Unique `row_id` | 9,994 | 9,994 | ✅ |
| Unique orders | 5,009 | 5,009 | ✅ |
| Unique customers | 793 | 793 | ✅ |
| Unique products | 1,862 | 1,862 | ✅ |
| Sales total | 2,297,200.86 | 2,297,200.8603 | ✅ (Δ 0.0003) |
| Quantity total | 37,873 | 37,873 | ✅ |
| Quarantined profit total | 286,397.02 | 286,397.0217 | ✅ (Δ 0.0017) |
| Discount distribution | 12 values as §12 | identical | ✅ |
| Written-CSV re-read (rows, unique `row_id`) | — | 9,994 / 9,994 | ✅ |

Deltas are float-serialization rounding only. Any breach of tolerance aborts
the pipeline; none occurred.

## 21. Data-quality flags (booleans — values never altered)

| Flag | Rows True | Meaning |
|---|---|---|
| `is_missing_postal_code` | 0 | none missing; kept for future-source robustness |
| `has_product_name_conflict` | 337 | row's `product_id` maps to 2 names (32 IDs) |
| `has_implied_unit_price_issue` | 10 | the confirmed `FUR-BO-10002213` collision |

## 22. Remaining limitations

1. 32 collided Product IDs (§14) limit product-level purity — aggregate by
   `product_id` with the conflict flag in mind; never key by name.
2. `postal_code` needs string-typing at every consumer (§7 note).
3. No COGS/freight/returns/support/channel/weight — unchanged from Phase 0;
   explicitly out of scope until later phases.
4. `Country` is constant (US); `source_profit_quarantined` formula unknown.

## 23. Phase 1B conclusion

- **FIXED DURING CLEANING:** column names → snake_case; whitespace stripped;
  explicit dtypes; `postal_code` → string; dates → datetime (ISO); alias
  `net_revenue = sales`. All lossless, all reproducible.
- **FLAGGED / PRESERVED:** 32 multi-name Product IDs (337 rows), FUR-BO-10002213
  collision (10 rows), negative/zero quarantined-profit values, discount-heavy
  rows. Nothing deleted, nothing overwritten.
- **REQUIRES FUTURE MODELING:** COGS, freight, returns, support, allocations,
  contribution metrics — absent by design.
- Verdict: **READY FOR REVIEW.** Reproduce with `python src/data/prepare_fact_sales.py`.
