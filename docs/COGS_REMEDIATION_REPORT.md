# COGS Methodology Remediation

## 1. Problem

Audit flag L-01/P0: the revenue-percentage COGS rule makes row modeled margin
equal the benchmark by construction, so product/subcategory rankings restate
the assumption × revenue mix rather than independent cost discovery. The
implementation needed proof that COGS does not depend on observed Profit,
explicit assumption schema, and claim discipline.

## 2. Existing Method

`modeled_cogs_pct = 100 − benchmark_gross_margin_pct` (17 external sub-category
benchmarks); `modeled_cogs = Net Revenue × modeled_cogs_pct / 100`;
`modeled_gross_profit = Net Revenue − modeled_cogs`;
`modeled_gross_margin_% = profit / revenue × 100`. Implied per-unit values are
derived references only, never drivers.

## 3. Proof of Circularity

Precise finding: NOT dependency-circular (COGS ← Profit is absent — code never
reads `source_profit_quarantined` for COGS; quarantine enforced and now
machine-checked). It IS assumption-restating: `row-margin-identity` check
asserts modeled margin == benchmark ±1e-6, so within-group margins carry zero
independent cost information. Example: Binders line Sales 100.00 at benchmark
38% → COGS 62.00, profit 38.00 regardless of whether quarantined Profit says
5.00 or −20.00 (∂COGS/∂Profit = 0). 15/17 benchmarks are CATEGORY fallbacks
with identical centrals; Paper 38% contradicts its 17.14% pulp anchor.

## 4. Candidate Alternatives

A. Product-level cost data — NONE EXISTS in raw/secondary/processed (raw has
only Sales/Quantity/Discount/Profit; Global zips add Market/Shipping/Order
Priority, no cost). REJECTED (would invent data).
B. Subcategory external margin benchmarks — SELECTED (provenance below).
C. Category external benchmarks — accepted as documented fallback within B.
D. Published industry benchmarks — the source type used in B (Damodaran,
MillerKnoll, HNI, Logitech, Xerox, Best Buy, CSIMarket).
E. Freight/shipping as COGS proxy — REJECTED (freight is cost-to-serve, already
allocated separately; category mismatch).

## 5. Selected Method

Retain external-benchmark revenue-percentage COGS (the only non-fabricated
option) with hardened independence proof, explicit assumption schema, and
honest claim limits. No nicer-numbers tuning: benchmark values UNCHANGED.

## 6. Independent Data / Benchmark Source

`subcategory_margin_benchmarks.csv` (17 rows): Damodaran Margins by Sector
(Jan 2026, stern.nyu.edu), MillerKnoll FY2024 (39.1%), HNI FY2024 (40.9%),
Logitech FY2025 (43.1%), Xerox Q3 2024 (32.4%), Best Buy FY2025 (22.6%),
CSIMarket Furniture & Fixtures (35.49%). Retrieval 2026-09-11 per
`SUBCATEGORY_BENCHMARK_METHODOLOGY.md`. Grain: sub-category (2 rows) +
category fallback (15 rows, `fallback_used=TRUE`). Coverage 17/17, no NULLs.
Independent of observed Profit (no profit column in benchmark build; static
checker enforces).

## 7. Mapping Method

`dim_product` (1,894 analytical keys) ⨝ benchmarks on `sub_category`
(`many_to_one` validated) → one rate per key → enriched fact (`many_to_one`).
No orphans, no duplicates, no m:m. Verified: 1,894/1,894 unique.

## 8. Assumptions

Benchmarks are ASSUMPTIONS (dated, sourced, confidence HIGH/MEDIUM/LOW),
not observed costs. Product values are assumption allocations. ±5pp
sensitivity is band-width only and does not cover the 10–21pp
reseller-vs-manufacturer dispersion (documented).

## 9. Implementation

- `apply_modeled_cogs.py`: new columns `cogs_rate`, `cogs_amount_basis`,
  `cogs_source_year`, `cogs_method`, `assumption_status`; runtime
  circularity guard (fails if dim/bench carry Profit or assumptions do).
- New `src/data/check_cogs_independence.py` (static + artifact guard).
- `docs/COGS_MODEL.md` §15 independence proof.
- `backend/tests/test_cogs_independence.py` (3 tests).

## 10. Before vs After

Benchmark values identical → COGS values identical by design:
revenue 2,297,200.86, COGS 1,493,910.13, gross profit 803,290.73, margin
34.97%, sensitivity TOTAL 29.97/34.97/39.97. What changed: schema (+5
columns), proof, guards, docs. Assumption file 12 → 17 columns.

## 11. Analytical Impact

None numerically; honesty improved. Rankings must be read as
assumption × mix (only Technology spread + cross-tier gaps informative).

## 12. Affected AOs

NONE — all 6 AO CSV hashes identical after rebuild.

## 13. SQLite Impact

Rebuilt via `load_data.py` (hash moves only via postal-fix quality rows from
the prior pass, not this task); `validate_sql_outputs.py` PASS; counts
20/238/105/420/60108/125.

## 14. API Impact

None — string passthrough verified; new backend tests pass.

## 15. React Impact

None required — values unchanged; MODELED labeling already present.

## 16. Power BI Impact

None — no AO change. 53 pre-existing Desktop churn files untouched.

## 17. Validation

- `check_cogs_independence.py` PASS; applier circularity guard PASS.
- Coverage 1,894/1,894; rates in (0,1); reconciliation profit == rev − COGS.
- Backend 44/44; frontend 23/23; lint clean; build clean; SQL 13/13.
- Sensitivity monotonic 29.97 < 34.97 < 39.97.

## 18. Limitations

Assumption-restatement; fallback granularity; Paper LOW confidence; ±5pp
narrowness; no product-level cost discovery possible without real cost data.

## 19. Reproducibility

`build_subcategory_benchmarks.py` → `apply_modeled_cogs.py` →
`check_cogs_independence.py` → downstream chain → `load_data.py` →
`validate_sql_outputs.py`. All fail-loud, no manual edits.

## 20. Remaining Risks

Future benchmark edits need provenance updates; AO-05 lacks `modeled_cogs`
rows for standalone recomputation; PBIP absolute CSV paths predate this task.
