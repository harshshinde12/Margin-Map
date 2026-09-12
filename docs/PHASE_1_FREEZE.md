# Phase 1 Freeze

> Freeze audit executed 2026-09-12. Verdict: **PASS** (58/59 automated checks
> green; the single non-match is approved Phase 1B whitespace-stripping, see
> §13). All five Phase 1 pipelines re-ran byte-identical. No Git operations
> performed — checkpoint to be created separately by the project owner.

## 1. Freeze Status

**PHASE 1 — FROZEN**

Scope (§2): Phase 0 through Phase 1C-3. All six stages COMPLETE AND APPROVED:
Phase 0 (data audit), Phase 1A (financial definitions), Phase 1B (fact table +
data quality), Phase 1C-1 (analytical product grain), Phase 1C-2 (COGS
architecture), Phase 1C-3 (modeled COGS implementation, incl. review
correction on implied-unit semantics and source-URL traceability).

## 2. Scope

Phase 0 → Phase 1C-3 as above. Nothing from Phase 2 (freight, returns,
support, cost-to-serve, contribution profitability, customer profitability,
pricing scenarios, Power BI/Streamlit/dashboards) is implemented — verified by
repository-wide search (§12).

## 3. Data Foundation

- Source: `archive.zip` → `Sample - Superstore.csv` (9,994 rows × 21 cols,
  latin1, 0 nulls, 0 full duplicates; SHA-256 `574F496D…7D32`).
- Grain: **one row = one product line within an order** (`row_id` unique).
- `data/processed/fact_sales.csv`: **9,994 rows × 25 cols** (21 canonical +
  `net_revenue` alias + 3 flags); **5,009 orders**, 793 customers, **1,862
  source Product IDs** (1,850 names), sales **2,297,200.86**, quantity 37,873,
  discount ∈ [0, 0.8], ship ≥ order on all rows. Regenerates byte-identical
  via `src/data/prepare_fact_sales.py`.
- Analytical products: **1,894** `product_id + product_name` combinations
  (32 multi-name IDs / 337 rows preserved unmerged; 16 reverse-name cases
  documented).

## 4. Product Grain

**Product ID + Product Name** (Phase 1C-1, approved). Key:
`analytical_product_key = product_id + " || " + product_name` — unique
(1,894/1,894), non-null, deterministic (pure function, order-independent),
bidirectional (combo→key and key→combo both exactly-one, machine-asserted).
Source `product_id`/`product_name` retained byte-identical apart from approved
trailing-whitespace stripping on 3 names / 16 rows (§13).

## 5. Financial Definitions

Approved Phase 1A definitions, implemented consistently:
`Net Revenue = Sales`; `Gross Revenue = Sales / (1 − Discount)` (derived
reference; no Discount ≥ 1 observed); `Discount Amount = Gross − Net`;
`Modeled COGS = Net Revenue × Modeled COGS %` with `Modeled COGS % =
100 − benchmark %`; `Modeled Gross Profit = Net − Modeled COGS`;
`Modeled Gross Margin % = profit / Net × 100` (NULL if Net = 0; none
observed). Aggregation rule enforced: `SUM(profit)/SUM(revenue)×100`, never
averaged percentages. Source `Profit` is `source_profit_quarantined` —
reference only, used in zero COGS/profit computations (code-searched).

## 6. Modeled COGS Methodology

Benchmark gross margin → modeled COGS % → modeled COGS → modeled Gross Profit
→ modeled Gross Margin (§5 formulas). **COGS is modeled, not actual**: the
public dataset contains no procurement/manufacturing/supplier cost, so every
margin is an analytical estimate from documented industry benchmarks — never
historical accounting COGS, never derived from quarantined Profit.
`implied_modeled_cogs_per_unit` (= modeled COGS ÷ quantity, row level) is a
derived analytical reference that varies with price/discount; it is NOT a
physical unit cost and never drives COGS (structurally impossible in code +
runtime-asserted, max gap 4.5e-13).

## 7. Benchmark Coverage

**17 sub-categories**, 0 unresolved, 0 duplicates: **2 direct sub-category
evidence** cases (Accessories 35% via Logitech FY2025 43.1%; Copiers 30% via
Xerox Q3-2024 ~32.4%) and **15 documented category-level fallbacks**
(Furniture 40%, Office Supplies 38%, Machines/Phones 25%) with
`fallback_used=TRUE` and per-row rationale — category evidence never presented
as sub-category evidence. Confidence: 16 MEDIUM, 1 LOW (**Paper** — commodity-
pulp anchor contradicts range; priority candidate for procurement-cost
calibration).

## 8. Financial Reconciliation

Net Revenue **2,297,200.86** · Modeled COGS **1,493,910.13** · Modeled Gross
Profit **803,290.73** · Overall Modeled Gross Margin **34.97%**
(profit = rev − COGS Δ 0.00; margin from sums). All 17 sub-category margins
reconcile exactly to their benchmarks (max dev 0.00). Row-level modeled margin
== benchmark on all 9,994 rows.

## 9. Sensitivity Analysis

Benchmark ±5pp (clipped [0,100], bounds never hit), revenue-based only
(`cogs_sensitivity.csv`, 17 + TOTAL). TOTAL band **29.97% / 34.97% / 39.97%**;
profit $688k–$918k. **Robust**: top-tier vs bottom-tier separation;
Phones/Machines lowest pool; overall low-to-mid-30s band. **Fragile
(explicitly not claimed)**: Furniture-vs-Office ordering (2pp gap);
Accessories-vs-Copiers gap. See `docs/COGS_SENSITIVITY.md` §2.

## 10. Source Preservation

`archive.zip` untouched; inner CSV shape/totals verified (9,994 × 21; sales
2,297,200.86; profit 286,397.02). `fact_sales.csv` regenerates byte-identical
(SHA-256 `d7478eb5…e3261ee2` before/after every run). `dim_product.csv`
likewise stable. No source file modified during audit or any phase.

## 11. Known Limitations

- Modeled COGS is not historical accounting COGS; all margins are estimates.
- 15/17 benchmarks are category-level fallbacks (labeled, not hidden).
- ±5pp sensitivity bounds assumption width, not structural bias.
- Reseller/manufacturer/channel mismatch: pure-reseller margins (ODP ~20.7%,
  Best Buy ~22.6%) sit below selected benchmarks (recorded as caveats).
- Implied per-unit value is not a true physical unit cost.
- No actual procurement/manufacturing costs exist in the public dataset.
- 2024–2026 anchors applied to 2014–2017 sales (structural levels, not period
  costs; no effective-dating).
- Minor doc-lineage notes (LOW/INFO, no model impact): Phase 1A generic
  `Quantity × unit` phrasing vs revenue-based implementation; 1C-2 §6
  percentage-of-revenue rejection vs benchmark-derived method (owner-selected
  Method D/F path per 1C-2 §8); D05 product-key wording superseded by 1C-1
  grain; 3 source names carry stripped trailing spaces (16 rows).

## 12. Phase 2 Boundary

NOT implemented (verified — only definitional mentions in Phase 0/1A docs and
roadmap text): freight allocation, return cost, support cost, total
cost-to-serve, contribution profit/margin, customer profitability, pricing
scenario engine, Power BI dashboard, Streamlit app, executive cockpit. The only
scenarios in the repo are the Phase 1C-3 COGS ±5pp sensitivity. `notebooks/`,
`sql/`, `powerbi/` contain `.gitkeep` only.

## 13. Freeze Validation

- 59-check quantitative audit: **58 PASS**; 1 non-match = `product_name`
  trailing-space strip on 3 names / 16 rows — approved Phase 1B cleaning
  (`DATA_QUALITY_REPORT.md` §22 "whitespace stripped"), documented,
  join-consistent (dim + keys derive from stripped fact; 0 unknown keys).
  Classified INFORMATIONAL, not a defect.
- Reproducibility: all 5 pipelines (`prepare_fact_sales`,
  `analyze_product_grain`, `build_product_dimension`,
  `build_subcategory_benchmarks`, `apply_modeled_cogs`) re-ran green; all 13
  processed artefacts byte-identical before/after (SHA-256 compared).
- Quarantine: `source_profit_quarantined` used in zero cost/profit
  computations (full `src/` search). Boundary: no Phase 2 code. Determinism:
  consecutive-run hash comparison, no diff.
- Failure drill: pipeline fail-loud guards exercised by design (invalid-input
  paths raise `VALIDATION FAILED` with expected-vs-actual).

## 14. Freeze Date

**2026-09-12.** Git checkpoint to be created separately by the project owner;
no commit/push/branch/config changes were made during this audit.
