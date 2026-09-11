# MarginMap – Profitability & Cost-to-Serve Analytics

> Revenue growth can hide margin erosion when logistics, discounting, returns,
> and support costs are not allocated correctly.

MarginMap reveals **true profitability** across products, customers, channels,
and regions, and supports pricing, discount, portfolio, and cost-to-serve decisions.

## Objective

Build a transparent, reproducible profitability model on top of the Superstore
sales dataset, then extend it with cost-to-serve allocation, pricing/discount
analytics, and an executive cockpit.

## Current status — Phase 1A / Financial Definitions & KPI Dictionary (COMPLETE, awaiting confirmation)

- [x] Environment + Git inspection
- [x] ZIP inspection (`archive.zip` → `Sample - Superstore.csv`)
- [x] Full dataset audit → see `docs/DATA_AUDIT.md`
- [x] Phase 1A — Financial definitions & KPI dictionary → see `docs/FINANCIAL_MODEL.md`, `docs/KPI_DICTIONARY.md`, `docs/DECISION_LOG.md`
- [x] Phase 1B — Data Foundation → `src/data/prepare_fact_sales.py` → `data/processed/fact_sales.csv` (9,994 rows, 25 cols) → see `docs/DATA_QUALITY_REPORT.md`
- [x] Phase 1C-1 — Analytical product grain investigation → `src/data/analyze_product_grain.py` → `docs/PRODUCT_GRAIN_DECISION.md` (recommendation: product_id + product_name; source unmodified; PENDING REVIEW)
- [ ] Phase 1C-2 (NOT STARTED — pending 1C-1 review)
- [ ] Phase 1B+ – Data mapping & implementation (NOT STARTED)
- [ ] Phase 2 – Cost-to-Serve Model (NOT STARTED)
- [ ] Phase 3 – Pricing & Discount Analytics (NOT STARTED)
- [ ] Phase 4 – Executive Profitability Cockpit (NOT STARTED)

**Phase 1B status: COMPLETED / READY FOR REVIEW (definitions + foundation only — no cost modeling, no dashboard). Phase 1 as a whole is NOT finished; Phase 1C still required. Stopping here — do not start Phase 1C until confirmed.**

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
No synthetic data was generated. No Phase 1 formulas were implemented yet.

## Next step (requires your confirmation)

Decide how to handle missing cost fields (freight, returns, support, COGS)
and the ambiguous `Profit` field before any modeling. See
`docs/DATA_AUDIT.md` § Gaps and § Open questions.
