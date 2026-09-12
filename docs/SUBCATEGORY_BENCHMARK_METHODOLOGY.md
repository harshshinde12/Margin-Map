# Sub-Category Benchmark Methodology (Phase 1C-3)

> **Modeled COGS is an analytical estimate, not historical accounting COGS.**
> The source dataset contains no actual COGS; every margin in this phase is
> MODELLED from documented industry benchmarks. Builder:
> `src/data/build_subcategory_benchmarks.py` → authoritative input
> `data/processed/subcategory_margin_benchmarks.csv` (17 rows) + coverage
> report `data/processed/benchmark_quality_report.json`. Researched 2026-09-11.

## 1. Purpose

Why benchmark gross margins are being used: the public Superstore dataset has
no product-cost signal of any kind (see §2), yet gross-profit analysis requires
a COGS term (`Gross Profit = Net Revenue − COGS`). The approved fallback is a
**modeled COGS** derived from **sub-category-level industry benchmark gross
margins**: each sub-category is assigned a documented benchmark margin, and
modeled COGS follows from the identity
`Benchmark Gross Margin % = 1 − Modeled COGS % of Net Revenue`, i.e.
`Modeled COGS = Net Revenue × (1 − Benchmark Gross Margin %)`.
Benchmarks give directional, comparable product/category economics — never
audited product costs.

## 2. Why actual COGS is unavailable

`Sample - Superstore.csv` (inside `archive.zip`, 9,994 rows) records what a
reseller's order system captures: `Sales` (net of discount), `Quantity`,
`Discount`, `Product ID / Name / Category / Sub-Category`, and a `Profit`
field of unknown formula. It contains **no actual COGS**: no unit cost,
procurement/manufacturing/supplier cost, and no freight, return, or support
dollars. The `Profit` field is therefore `source_profit_quarantined` — kept
for reference, **never used in any calculation, and in particular never used
as `COGS = Sales − Profit`**. With no cost anchor, any COGS in this phase is
by construction a labeled assumption.

## 3. Benchmark methodology

How industry benchmarks are mapped to the 17 Superstore sub-categories:

1. The owner-researched ranges (Furniture ~35–45%, Office Supplies ~30–45%,
   Technology core ~20–30% with accessories higher) were treated as **inputs
   requiring documentation, not as approved values**.
2. Each range was corroborated against citable public evidence (table below);
   the selected central is a whole-percent value inside the documented range.
3. The mapping is recorded per sub-category in
   `subcategory_margin_benchmarks.csv` with full source metadata; the
   per-row `methodology_note` states exactly which evidence supports the row
   and which adjacent anchors were recorded as caveats rather than anchors.
4. No category percentage is copied across sub-categories silently: all 15
   rows without sub-category-specific evidence carry `benchmark_level =
   CATEGORY`, `fallback_used = TRUE`, and a note saying so (§6).

| Sub-category | Sel | Range | Level | Primary evidence (see CSV for URLs/dates) |
|---|---|---|---|---|
| Bookcases, Chairs, Furnishings, Tables | 40% | 35–45% | CATEGORY | MillerKnoll FY2024 39.1%; HNI FY2024 40.9%; CSIMarket Furniture & Fixtures TTM 35.49%; Damodaran Furn/Home Furnishings 30.28% (below-range anchor) |
| Appliances, Art, Binders, Envelopes, Fasteners, Labels, Paper, Storage, Supplies | 38% | 30–45% | CATEGORY | Damodaran Office Equipment & Services 41.43%; Retail (Special Lines) 35.30% / (Distributors) 30.57%; ODP Corp FY2024 reseller ~20.7% incl. occupancy (below-range channel caveat) |
| Accessories | 35% | 30–40% | SUB_CATEGORY | Logitech FY2025 GAAP 43.1% (accessories maker); Damodaran Computers/Peripherals 38.36% — central set below manufacturer levels for reseller positioning |
| Copiers | 30% | 25–35% | SUB_CATEGORY | Xerox Q3 2024 total 32.4% (equipment 28.5%, post-sale 33.5%); FY2024 ~31.5% GAAP / ~32.3% adjusted (2025 excluded: Lexmark distortion) |
| Machines, Phones | 25% | 20–30% | CATEGORY | Damodaran Electronics (General) 26.76%; Best Buy FY2025 22.6% (reseller); Telecom Equipment 58.1% explicitly rejected (network gear, not handsets) |

## 4. Source hierarchy

Preferred evidence, in order; each row uses the highest level actually found:

1. **Direct sub-category evidence** — a published margin for the sub-category
   product itself (achieved for Accessories/Logitech and Copiers/Xerox only).
2. **Closely matching product/category evidence** — e.g. contract-furniture
   makers for Furniture; office-equipment and specialty-retail aggregates for
   Office Supplies; electronics aggregates and electronics resellers for
   Technology.
3. **Category-level evidence** — applied with `benchmark_level = CATEGORY`,
   `fallback_used = TRUE` (15 of 17 rows).
4. **Documented fallback** — owner-researched range + public corroboration as
   above. There is deliberately **no level-5 "unsupported" row**: had any
   sub-category lacked adequate sourcing it would have been left NULL/LOW and
   reported unresolved (0 such rows; see quality report).

Adjacent-but-rejected anchors (Damodaran Paper/Forest 17.14% commodity pulp
for Paper; Telecom Equipment 58.1% for Phones; Machinery 37.5% for Machines;
ODP ~20.7% distressed-retail) are named in the row notes so a reviewer can see
what was considered and why it was not used as the anchor.

## 5. Central-value selection

How a benchmark range becomes a selected central assumption:

- The central is always a **whole percent inside the documented range**
  (`low <= selected <= high` is machine-validated); no false precision
  (never 41.37% from a 35–45% range).
- Furniture 40% = owner central, corroborated at the top by MillerKnoll 39.1%
  and HNI 40.9%, with industry aggregates (35.5%/30.3%) anchoring the low end.
- Office Supplies 38% = owner central, bracketed by Damodaran 41.4% above
  and 35.3%/30.6% retail aggregates at/below.
- Accessories 35% = judgmental midpoint between core-tech levels and
  brand-manufacturer levels (43.1%/38–39%), discounted for reseller
  positioning per the owner input that accessories run higher.
- Copiers 30% = top of the core-tech range, rounded just below Xerox
  31.5–32.4% for reseller positioning.
- Machines/Phones 25% = midpoint of the 20–30% core-tech range, corroborated
  by Damodaran 26.8% and Best Buy 22.6%.
- Original source terminology is preserved verbatim in `source_name`
  (e.g. "gross profit %", "gross margin TTM", "gross margin – GAAP").

## 6. Fallback handling

How category-level evidence is handled: any row whose evidence does not name
the sub-category product gets `benchmark_level = CATEGORY` and
`fallback_used = TRUE`, and its `methodology_note` opens with
"Category-level evidence only … applied as documented fallback." All four
Furniture, all nine Office Supplies, Machines, and Phones rows (15 total) are
labeled this way. Downstream, these rows carry `cogs_status =
MODELED_CATEGORY` (vs `MODELED_SUBCATEGORY` for Accessories/Copiers) so
actuals and models — and strong vs fallback models — never mix silently.

## 7. Confidence

- **HIGH** — reserved for audited product-level actuals; **not used in this
  phase** (no actuals exist).
- **MEDIUM** (16 rows) — central inside a documented range with at least one
  citable public anchor in/near the range.
- **LOW** (1 row: Paper) — the only product-specific anchor (commodity pulp
  17.14%) contradicts the applied range, so the row is flagged for priority
  calibration against real procurement costs even though it is resolved.
- **Unresolved (NULL + LOW)** — the prescribed state for unsourceable rows;
  0 rows are in this state. Nothing was fabricated for completeness.

## 8. Limitations

- **Modeled COGS is an analytical estimate and not historical accounting
  COGS.** No modeled margin may be presented as observed profitability.
- Reseller-vs-manufacturer gap: most anchors are manufacturer/industry
  margins; a reseller's true buy cost is unobserved. Pure-reseller margins
  (ODP ~20.7%, Best Buy ~22.6%) sit below the selected benchmarks and are
  recorded as caveats — if Superstore's true economics resemble a distressed
  reseller more than category averages, modeled margins overstate reality.
- Within-sub-category spread is hidden: one rate covers all products in the
  sub-category (e.g. a $2 label and a $200 machine share nothing but the
  method). Product-level modeled margins are indicative only.
- Evidence is time-mismatched (2024–2026 anchors applied to 2014–2017 sales);
  treated as structural margin levels, not period costs. No inflation or
  effective-dating adjustment is attempted.
- Sensitivity ±5pp (see `docs/COGS_SENSITIVITY.md`) bounds the assumption
  risk; conclusions that do not survive it must not be reported as robust.
