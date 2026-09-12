# COGS Data Dictionary (Phase 1C-2)

> Files are UTF-8. `product_name` preserves source text verbatim, including
> source encoding artifacts (e.g. non-breaking spaces from the latin1 origin) —
> never "clean" names to match keys. CSVs carry no types: read IDs, names, and
> `postal_code`-like text as string downstream.

## dim_product.csv (1,894 rows — analytical product dimension)

| Field | Business meaning | Data type | Status | Null? | Key role |
|---|---|---|---|---|---|
| `analytical_product_key` | Deterministic grain key: `product_id + " \|\| " + product_name` | string | Derived (pure function, documented in `COGS_MODEL.md` §4) | No | Primary key (unique, 1,894/1,894) |
| `product_id` | Source Product ID, byte-identical to fact | string | Source-derived | No | Part of natural grain; traceability |
| `product_name` | Source Product Name, byte-identical to fact | string | Source-derived | No | Part of natural grain; display label |
| `category` | Source Category (single-valued per combo, validated) | string | Source-derived | No | Descriptive attribute / rollup |
| `sub_category` | Source Sub-Category (single-valued per combo, validated) | string | Source-derived | No | Descriptive attribute / rollup |

## product_cogs_input_template.csv (1,894 rows — future input contract)

| Field | Business meaning | Data type | Status | Null? | Key role / rule |
|---|---|---|---|---|---|
| `analytical_product_key` | Join key to `dim_product` | string | Derived | No | Must exist in dim; duplicates with overlapping effective periods rejected by future loader |
| `product_id` | Source Product ID (carried for readability) | string | Source-derived | No | Must agree with dim row for the key |
| `product_name` | Source Product Name (carried for readability) | string | Source-derived | No | Must agree with dim row for the key |
| `cogs_per_unit` | Future unit cost in source currency | numeric | **Pending (all NULL)** | Yes (today: all NULL) | Future: must be > 0 when populated; NULL means "no cost yet", never 0 |
| `cogs_status` | Lifecycle label of the row | string (enum) | Governance | No | Today: all `PENDING_SOURCE`. Future: `ACTUAL_*` vs `MODELED_*`/`ASSUMED_*`/`STANDARD_*` — actuals and models never share a label |
| `cogs_source` | Origin system/owner/table reference | string | Governance | Yes (today: all NULL) | Mandatory before any non-pending row is accepted |
| `effective_start_date` | First date the unit cost applies (ISO) | date | Governance | Yes (today: all NULL) | Required once a cost is set; reserves time-varying costs |
| `effective_end_date` | Last date the cost applies; blank = current | date | Governance | Yes | Must be ≥ start date when both set |
| `assumption_note` | Why/how this row exists | string | Governance | Yes | Mandatory for modeled/assumed rows; today carries the pending notice |

Status enum (reserved; only `PENDING_SOURCE` is used in this phase):
`PENDING_SOURCE`, `ACTUAL_VENDOR`, `ACTUAL_PROCUREMENT`, `STANDARD_APPROVED`,
`ASSUMED_MANAGEMENT`, `MODELED_SUBCATEGORY`, `MODELED_CATEGORY`, `RETIRED`.

## Phase 1C-3 modeled-output fields (authoritative: revenue-based modeled COGS)

> Naming rule: nothing derived from the revenue-based model may carry a bare
> unit-cost name. The template's `cogs_per_unit` (above) reserves a slot for a
> future *observed* unit-cost input; `implied_modeled_cogs_per_unit` (below) is
> a *derived analytical reference*. The two must never be conflated.

### product_cogs_assumptions.csv (1,894 rows — one per analytical product)

| Field | Business meaning | Status |
|---|---|---|
| `analytical_product_key` | Join key to `dim_product` | Derived |
| `product_id` / `product_name` | Source values, byte-identical (readability) | Source-derived |
| `sub_category` | Source sub-category (rollup/lookup) | Source-derived |
| `benchmark_gross_margin_pct` | Selected benchmark from `subcategory_margin_benchmarks.csv` | Modeled assumption |
| `modeled_cogs_pct` | `100 − benchmark %` — the authoritative product rate | Modeled assumption |
| `implied_modeled_cogs_per_unit` | DERIVED reference: product modeled COGS ÷ product quantity. Varies with price/discount mix; NOT a physical unit cost; never drives COGS | Derived |
| `cogs_status` | `MODELED_SUBCATEGORY` (Accessories/Copiers) or `MODELED_CATEGORY` (fallbacks) | Governance |
| `cogs_source` | Trace pointer `subcategory_margin_benchmarks.csv:<sub>:<%>:<level>` | Governance |
| `benchmark_level` / `confidence` | `SUB_CATEGORY` vs `CATEGORY` fallback; `HIGH` unused, `MEDIUM`/`LOW` | Governance |
| `assumption_note` | Methodology + explicit implied-unit definition | Governance |

### fact_sales_cogs.csv modeled columns (9,994 rows — appended after all 25 source columns)

| Field | Business meaning | Status |
|---|---|---|
| `analytical_product_key` | Product grain key (`product_id + " \|\| " + product_name`) | Derived |
| `benchmark_gross_margin_pct` / `modeled_cogs_pct` | Row's benchmark and COGS rate (from its sub-category) | Modeled assumption |
| `modeled_cogs` | AUTHORITATIVE: `sales × modeled_cogs_pct / 100` | Modeled |
| `implied_modeled_cogs_per_unit` | DERIVED ONLY: `modeled_cogs / quantity` per row — NOT a unit cost | Derived |
| `modeled_gross_profit` | `sales − modeled_cogs` | Modeled |
| `modeled_gross_margin_pct` | `profit / sales × 100` (NULL if sales = 0; none observed) | Modeled |
| `cogs_status` / `benchmark_level` / `benchmark_confidence` | Row's modeling lineage labels | Governance |
