# COGS Model (Phase 1C-2 — Architecture & Assumption Framework)

> Architecture only. **No numerical COGS values exist in this phase** — the input
> template holds 1,894 NULLs with status `PENDING_SOURCE`, and no methodology
> has been selected. Source Profit remains quarantined; COGS must never be
> derived from it.

## 1. Purpose

Design the COGS modeling foundation so a future COGS dataset or approved
assumption set can be plugged in without redesigning the data model: the
analytical product dimension, the input contract, the source/assumption
governance, the methodology requirements, and the validation rules.

## 2. Current Data Availability

The source dataset (`Sample - Superstore.csv`) contains **no actual COGS**:
no purchase, manufacturing, supplier, or inventory cost; no unit cost; no
freight/return/support dollars. Available product signals are `product_id`,
`product_name`, `category`, `sub_category`, `quantity`, `sales`, `discount`
(net revenue only). Anything called "COGS" before a real source arrives is a
labeled assumption, never history.

## 3. Approved Analytical Product Grain

`Product ID + Product Name` (Phase 1C-1, approved): 1,862 IDs → **1,894 unique
combos** (32 IDs × 2 names; 337 rows, 4.24% of sales). Name alone is unsafe
(16 generic names span 2–10 IDs); Category/Sub-Category are fully consistent
per ID and per combo, hence safe attributes.

## 4. Analytical Product Key

`analytical_product_key = product_id + " || " + product_name`
(e.g. `FUR-BO-10002213 || DMI Eclipse Executive Suite Bookcases`).
Deterministic pure function of the combo; order-independent (built from sorted
unique combos); stable across runs; human-readable; no UUIDs, no row numbers.
Validated bidirectional: combo → exactly one key, key → exactly one combo
(1,894 unique keys, 0 nulls). It coexists with — never replaces — `product_id`;
source values are byte-identical to the fact table.

## 5. Future COGS Input Structure

`data/processed/product_cogs_input_template.csv` (1,894 rows) is the contract
any future COGS source must satisfy: `analytical_product_key, product_id,
product_name, cogs_per_unit, cogs_status, cogs_source, effective_start_date,
effective_end_date, assumption_note`. Today: `cogs_per_unit` all NULL,
`cogs_status = PENDING_SOURCE` on all rows, source/dates blank, note stating
values are intentionally blank. A future loader must reject unknown keys,
duplicate active keys, and non-positive unit costs (see `COGS_DATA_DICTIONARY.md`).

## 6. COGS Source Hierarchy

Preferred order — each row labeled so actuals and models never mix:

1. **Actual transaction/product cost** (procurement/vendor feed keyed to the
   analytical key; effective-dated). Preferred whenever it exists.
2. **Standard cost** (approved BOM/standard-cost table; version + owner required).
3. **Documented management assumption** (signed, dated, per-product; lowest
   standing among product-level options).
4. **Sub-category modeled assumption** (fallback; pooled rate with stated method).
5. **Category modeled assumption** (last resort; coarse — margin analysis at
   product level becomes indicative only).

Percentage-of-revenue "COGS" is **not accepted** as a cost input: it is circular
with the margin it claims to explain. `ACTUAL_*` vs `MODELED_*`/`ASSUMED_*`
statuses must be visually and programmatically distinct downstream.

## 7. Candidate Methodologies

| Method | Needs | Usefulness / Accuracy | Risks / Maintenance |
|---|---|---|---|
| A. Product-level actual | Vendor/procurement feed + key mapping | Highest; true gross margins | Mapping upkeep; coverage gaps; effective-date handling |
| B. Product-level standard | Approved standard-cost table | Stable, comparable periods; variance analysis possible | Staleness; needs periodic re-approval; hides true volatility |
| C. Category-level modeled | Category rate + method doc | Cheap; fine for directional portfolio cuts | Smears within-category differences; weak at product/customer grain |
| D. Sub-category-level modeled | Sub-category rates (17 groups) | Better than C; matches observed margin dispersion (Labels +44% vs Tables −9% in quarantined profit) | Still hides product spread; needs per-group justification |
| E. Percentage-of-revenue | Nothing (rejected) | None for costing — circular | Fabricates precision; corrupts pricing decisions |
| F. Hybrid (actual where covered, modeled fallback) | Coverage map + per-row status | Pragmatic; honest about uneven evidence | Must enforce status discipline or actuals/modeled silently mix |

No rate is selected; each method lists the evidence that must precede selection.

## 8. Recommended Future Approach

- **If actual cost data becomes available:** Method A (product-level actual,
  effective-dated), backfilled by B where standards exist, each row status-
  labeled. This is the only path to defensible product/customer margins.
- **If actual cost data is unavailable:** Method F with D-level fallback
  (sub-category modeled, documented method + confidence), all rows marked
  `MODELED_*`, product-level margins explicitly labeled indicative.
- **Current dataset verdict:** insufficient for a final methodology decision —
  no cost signal of any kind exists. This is stated deliberately instead of
  manufacturing a rate. Awaiting owner decision on sourcing before any numbers.

## 9. Assumption Governance

Every future COGS row (non-actual) must carry: owner/source, assumption date,
effective period, methodology reference, status/confidence, business reason,
and version history (append-only log; supersede, never overwrite). Template
columns `cogs_source`, `effective_*_date`, `assumption_note` plus the future
change log implement this. Actuals carry source-system lineage instead.

## 10. Effective-Dated Cost Considerations

Costs move (supplier changes, inflation, the 2014–2017 window spans sourcing
shifts), so the grain must support `analytical_product_key + effective period`,
not one timeless value. The template's `effective_start_date/_end_date` reserves
this; Phase 1C-2 implements no SCD logic — only the requirement and the columns
(no overlapping active periods per key; open-ended current row allowed).

## 11. Financial Calculation Interface

Locked Phase 1A definitions (unchanged): `COGS = Quantity × COGS per Unit`;
`Gross Profit = Net Revenue − COGS`;
`Gross Margin % = Gross Profit / Net Revenue × 100` (NULL if Net Revenue = 0).
Future loader joins template → fact on `analytical_product_key` filtered to the
effective date, then applies these formulas. No Gross Profit/Margin is computed
in this phase (all COGS NULL by design).

## 12. Limitations

No cost source in hand; no methodology selected; effective-date logic
unspecified beyond the reserved columns; 32 collided IDs will need two
independent unit costs each (their keys exist — values do not); generic-name
reverses stay per-ID (conservative). Any margin shown before COGS sourcing is
revenue/discount analysis, not profitability.

## 13. Phase Status

**PHASE 1C-2 COMPLETE — APPROVED.** Frozen as part of Phase 1 on 2026-09-12
(see `docs/PHASE_1_FREEZE.md`).

## 14. Phase 1C-3 Addendum — revenue-based modeled COGS & implied unit semantics

(Added in the Phase 1C-3 review correction. Phase 1C-2 architecture above is
unchanged; the `product_cogs_input_template.csv` contract — including its
`cogs_per_unit` column for *future actual* unit-cost inputs — is untouched.)

- The implemented modeled-COGS methodology estimates COGS as a percentage of
  net revenue using industry benchmark gross margins
  (`subcategory_margin_benchmarks.csv`): authoritative
  `modeled_cogs = Net Revenue × modeled COGS %`, with
  `modeled COGS % = 1 − benchmark gross margin %`. See
  `docs/SUBCATEGORY_BENCHMARK_METHODOLOGY.md`.
- Because the model is revenue-based, any per-unit value derived from it may
  change with transaction price and discount. It must not be interpreted as a
  stable procurement/manufacturing cost per physical unit.
- The derived field is therefore named `implied_modeled_cogs_per_unit`
  (in `product_cogs_assumptions.csv` and `fact_sales_cogs.csv`) and defined
  as "an implied analytical value equal to modeled COGS divided by observed
  quantity … NOT an actual physical unit cost." It never drives modeled COGS:
  at row level `implied = modeled_cogs / quantity`; authoritative COGS is
  always `Net Revenue × modeled COGS %`.
- This is deliberately distinct from the template's `cogs_per_unit`, which
  reserves a slot for a future *observed* unit cost. The two must never be
  conflated: one is an input awaiting actuals, the other a derived
  analytical reference.

## 15. Independence proof (P0 remediation) — why this method is NOT circular

Dependency graph (allowed direction only):

  external benchmark (Damodaran / MillerKnoll / HNI / Logitech / Xerox /
  Best Buy / CSIMarket, dated, per sub-category)
      → modeled COGS % = 100 − benchmark %
      → modeled COGS = Net Revenue × modeled COGS %
      → modeled gross profit / margin (DERIVED)

Observed `Profit` is quarantined (`source_profit_quarantined`): carried through
untouched, never read by `build_subcategory_benchmarks.py` or
`apply_modeled_cogs.py`. Machine check: `src/data/check_cogs_independence.py`
fails loudly if any COGS assignment ever reads a profit field.

Numerical proof (Binders line, benchmark 38% → COGS % 62%):

  Sales = 100.00 → modeled COGS = 62.00 → modeled profit = 38.00 (margin 38%).
  Whether the quarantined source Profit says 5.00, 38.00, or −20.00, the
  modeled outputs are unchanged: ∂(modeled COGS)/∂(observed Profit) = 0.

What IS true and is disclosed (not hidden): row modeled margin equals the
benchmark by construction (`row-margin-identity` check ±1e-6), so within-group
rankings restate the assumption × revenue mix, not independent cost discovery.
15/17 benchmarks are CATEGORY fallbacks (identical centrals); only Technology
spread and cross-tier gaps carry information. Product-level values are
assumption allocations, labeled `MODELED_*` with `cogs_rate`, `cogs_method`,
`cogs_source_year`, and `assumption_status` columns. Rankings must never be
presented as cost-evidence without this caveat.
