# MarginMap – Profitability & Cost-to-Serve Analytics

> Revenue growth can hide margin erosion when logistics, discounting, returns,
> and support costs are not allocated correctly.

MarginMap reveals **true profitability** across products, customers, channels,
and regions, and supports pricing, discount, portfolio, and cost-to-serve decisions.

## Objective

Build a transparent, reproducible profitability model on top of the Superstore
sales dataset, then extend it with cost-to-serve allocation, pricing/discount
analytics, and an executive cockpit.

## Current status — PHASE 1 FROZEN (2026-09-12, see `docs/PHASE_1_FREEZE.md`)

- [x] Environment + Git inspection
- [x] ZIP inspection (`archive.zip` → `Sample - Superstore.csv`)
- [x] Full dataset audit → see `docs/DATA_AUDIT.md`
- [x] Phase 1A — Financial definitions & KPI dictionary → see `docs/FINANCIAL_MODEL.md`, `docs/KPI_DICTIONARY.md`, `docs/DECISION_LOG.md`
- [x] Phase 1B — Data Foundation → `src/data/prepare_fact_sales.py` → `data/processed/fact_sales.csv` (9,994 rows, 25 cols) → see `docs/DATA_QUALITY_REPORT.md`
- [x] Phase 1C-1 — Analytical product grain → `src/data/analyze_product_grain.py` → `docs/PRODUCT_GRAIN_DECISION.md` (approved: product_id + product_name; source unmodified)
- [x] Phase 1C-2 — COGS architecture → `src/data/build_product_dimension.py` → `data/processed/dim_product.csv` (1,894 products) + COGS input template (**all values NULL / PENDING_SOURCE — no COGS fabricated**) → see `docs/COGS_MODEL.md`
- [x] Phase 1C-3 — Modeled COGS & financial foundation → `src/data/build_subcategory_benchmarks.py` → `data/processed/subcategory_margin_benchmarks.csv` (17 sub-categories, all sourced) + `src/data/apply_modeled_cogs.py` → `data/processed/product_cogs_assumptions.csv` (1,894 products) + `data/processed/fact_sales_cogs.csv` (9,994 rows, 35 cols) + sensitivity `data/processed/cogs_sensitivity.csv` → see `docs/SUBCATEGORY_BENCHMARK_METHODOLOGY.md`, `docs/MODELED_COGS_VALIDATION.md`, `docs/COGS_SENSITIVITY.md`
- [ ] Phase 1B+ – Data mapping & implementation (NOT STARTED)
- [ ] Phase 2 – Cost-to-Serve Model (NOT STARTED)
- [ ] Phase 3 – Pricing & Discount Analytics (NOT STARTED)
- [ ] Phase 4 – Executive Profitability Cockpit (NOT STARTED)

**PHASE 1 — FROZEN (2026-09-12). Financial foundation complete: definitions + fact table + product grain + modeled COGS on documented industry benchmarks (COGS is modeled, not actual; source Profit quarantined). No cost-to-serve modeling, no dashboard. Phase 2 has NOT started.**

## Phase 1C-3 note — COGS is MODELED, not actual (frozen 2026-09-12)

Phase 1C-3 implemented the modeled COGS and financial foundation on
sub-category-level industry benchmark gross margins (all 17 sub-categories
sourced; 15 documented category-level fallbacks, 2 sub-category-level;
assumptions documented per row; sensitivity ±5pp performed).

- COGS is **modeled** (analytical estimate, not historical accounting COGS).
- Benchmark gross margins are used; benchmark assumptions are documented
  (`docs/SUBCATEGORY_BENCHMARK_METHODOLOGY.md`).
- Source COGS does not exist in the public dataset.
- Source Profit remains quarantined and was not used for COGS.
- Modeled Gross Profit / Gross Margin are estimates (overall 34.97%,
  sensitivity band 29.97%–39.97%).
- Actual historical COGS has NOT been recovered; no freight/returns/support
  costs are modeled in this phase.

## Tech stack (planned)

- Python / Pandas – data processing & analytics
- SQL – data modeling & analytical queries
- Power BI – main business dashboard
- Git / GitHub – version control & portfolio presentation

No web framework in stage 1. Keep it understandable for a Business Analytics project.

## Dataset

- Source file (local only, git-ignored): `archive.zip` → `Sample - Superstore.csv`
- Rows: **9,994** · Columns: **21** · Orders: **5,009** · Date range: **2014-01-03 → 2017-12-30**
- Geography: United States only (4 regions, 49 states, 531 cities)
- Grain: **one row = one product line within an order** (avg ~2.0 lines/order)
- Key fields present: `Sales` (net of discount, proven), `Quantity`, `Discount`, `Profit` (formula UNKNOWN — do not use blindly)
- Key fields **missing**: COGS, freight/shipping cost, returns, support/service cost, channel, product weight, unit price/cost
- Encoding: `latin1` (not UTF-8). Full details in `docs/DATA_AUDIT.md`.

## Project structure

```text
Margin Map/
  archive.zip            # original source (local only, git-ignored) — DO NOT COMMIT
  README.md
  .gitignore
  docs/
    DATA_AUDIT.md        # Phase 0 audit findings (source of truth)
    FINANCIAL_MODEL.md   # Phase 1A approved formulas + controls
    KPI_DICTIONARY.md    # Phase 1A KPI definitions
    DECISION_LOG.md      # Phase 1A approved decisions
  data/                  # local working data, git-ignored (raw/ processed/ curated/)
  notebooks/             # exploratory analysis (Phase 1+)
  src/                   # reusable Python (Phase 1+)
  sql/                   # data modeling + analytical queries (Phase 1+)
  powerbi/               # Power BI cockpit (Phase 4)
```

## Reproducibility note

All audit numbers were derived directly from `archive.zip` with Pandas.
No synthetic data was generated. All five Phase 1 pipelines
(`prepare_fact_sales`, `analyze_product_grain`, `build_product_dimension`,
`build_subcategory_benchmarks`, `apply_modeled_cogs`) re-run deterministically
(byte-identical outputs, verified 2026-09-12).

## Next step (requires your confirmation)

Phase 2 (cost-to-serve: freight/returns/support allocation design) — not
started. See `docs/PHASE_1_FREEZE.md` for the frozen boundary and known
limitations.
