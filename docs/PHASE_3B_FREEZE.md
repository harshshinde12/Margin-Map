# Phase 3B Freeze — Observed Discount Impact Analysis

> Freeze audit executed 2026-09-12. Verdict: **PASS** — all audit checks
> green across phase boundary, output integrity, machine validation,
> frozen-input protection, documentation consistency, and working-tree
> review. No issue required repair; nothing was changed during the audit.
> No commit, reset, restore, cleanup, or push was performed — the formal
> freeze designation is recorded by this document and takes effect on owner
> approval.

## 1. Title and status

**PHASE 3B — OBSERVED DISCOUNT IMPACT ANALYSIS — COMPLETE, READY TO FREEZE.**

Phase 3B implements the observed-historical half of the frozen Phase 3A
architecture (`docs/PHASE_3A_DISCOUNT_PRICING_ARCHITECTURE.md` and
companions): reproducible descriptive analysis of discount levels and their
relationship with revenue, quantity, modeled gross profitability and —
only where analytically licensed — authoritative contribution
profitability. Design adoptions are recorded in
`docs/PHASE_3B_DECISION_LOG.md` (D3B-01–D3B-06); machine validation in
`docs/PHASE_3B_VALIDATION.md` and
`data/processed/phase3b_quality_report.json` (16/16 checks PASS).

## 2. Completion date

**2026-09-12** (audit and freeze-document date; implementation completed
and determinism-verified prior to this audit).

## 3. Scope

Observed historical discount analysis and descriptive associations only, at
overall, Segment, Category, Sub-Category, Customer, order, and (flagged
reference only) Product grains. Explicitly out of scope and absent from
this phase: pricing or discount What-if scenarios, elasticity
coefficients, quantity-response assumptions, fixed-unit-cost COGS,
causal inference, optimal-discount or pricing-policy recommendations, and
Power BI artifacts. The audit confirmed each of these remains absent from
the script, all seven outputs, the quality report, and all three Phase 3B
documents (prohibited phrases occur nowhere except inside explicit
prohibitions).

## 4. Implemented analytical components

Built by `src/data/build_phase3b_discount_analysis.py` (frozen inputs
read-only; fail-loud validation; deterministic):

- Line-level derived discount measures under frozen Phase 1A formulas: Net
  Revenue = Sales; Gross Revenue = Sales / (1 − Discount) with the
  Discount = 1 guard; Discount Amount = Gross − Net (dual-form reconciled);
  revenue realization rate; discount band; modeled gross profit/margin
  carried read-only from Phase 1.
- Fixed six-band structure (D3B-01): B0 `d = 0`; B1 `(0, 0.15]`;
  B2 `(0.15, 0.25]`; B3 `(0.25, 0.35]`; B4 `(0.35, 0.55]`;
  B5 `(0.55, 0.80]` — all 9,994 lines exactly one band (B0 4,798; B1 146;
  B2 3,657; B3 254; B4 283; B5 856); zero group exact; no value split.
- Order-level rollups under the single order-WAD rule (D3B-03): all 5,009
  orders exactly one band (B0 2,055; B1 415; B2 1,634; B3 278; B4 274;
  B5 353); all orders verified single-segment and single-customer before
  attribution. No quantile comparator (D3B-04).
- Authoritative contribution joined from `order_margin_map_phase2.csv` and
  used at order grain and above (D3B-06); category, sub-category, and
  product outputs gross-profit-only with NULL freight/contribution and
  reason `FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN`; LINE-basis companion
  rows explicitly labeled partial beside — never instead of — ORDER-basis
  authoritative rows (stated gap 200.0476).
- Ambiguous freight pair preserved: rows 3406/3407 NULL and flagged at line
  grain, never imputed; 25.05 pair total held at order `US-2014-150119`
  (full-order freight 26.55), flagged on exactly 1/5,009 order rows.
- Provisional sample thresholds 30 lines / 10 orders (D3B-02, analytical
  thresholds, not statistical rules): every row carries counts and
  `low_sample_flag`; thin cells shown with flags, never suppressed.
- Negative-profit visibility: 0 negative-gross-profit lines; 109
  negative-contribution lines; 50 negative-contribution orders preserved
  with flags; 0 negative-contribution customers (conditional on the
  scenarios-OFF baseline).

## 5. Output inventory

| File | Rows | Grain / basis | Audit finding |
|---|---:|---|---|
| `data/processed/discount_band_summary.csv` | 14 | Overall × band, ORDER authoritative + LINE partial | Counts verified; TOTAL reconciles to baseline |
| `data/processed/discount_segment_summary.csv` | 39 | Segment × band, dual basis + totals | 18 + 18 + 3; fully reconciled |
| `data/processed/discount_category_summary.csv` | 19 | Category × band, gross-only | 16 occupied + 3 totals; Office Supplies B3/B4 structurally absent; contribution NULL |
| `data/processed/discount_subcategory_summary.csv` | 69 | Sub-category × band, gross-only | 52/102 occupied + 17 totals; 10 flagged; contribution NULL |
| `data/processed/discount_customer_summary.csv` | 3,304 | 793 TOTAL + 2,511 occupied band rows, authoritative | Customer totals reconcile; 3,293/3,304 rows flagged as disclosed |
| `data/processed/discount_order_summary.csv` | 5,009 | One row per order, authoritative + rollup | 50 negative flags; 1 ambiguity note; WAD median 0.1607 |
| `data/processed/discount_product_summary.csv` | 5,925 | 1,894 TOTAL + 4,031 band rows, gross-only reference | 5,925/5,925 flagged; 93 low-volume flags; contribution NULL |
| `data/processed/phase3b_quality_report.json` | — | 16/16 checks, config, hashes | All PASS; per-file SHA-256 recorded |

All seven CSV row counts match the documented counts and the quality
report exactly (read-back verified); recorded per-file hashes match the
files on disk. The CSVs are git-ignored (`*.csv` in `.gitignore`) — expected
repository hygiene; the quality report, script, and documents are the
committed record. `.gitignore` was not modified.

## 6. Validation summary

The quality report records 16/16 PASS: quarantined-Profit exclusion; input
shapes with Phase 1 sales+COGS cross-check; scenarios OFF on both facts;
discount range [0, 1) with observed [0, 0.8] and zero NULLs; ambiguity
scope (2 lines, one order); Net = Sales exact (gap 0.00); Discount Amount
dual reconciliation (1.82e-12); complete line-band assignment; clean
order dimensions (5,009/5,009); complete order-WAD assignment; contribution
reconciliation to baseline (565,116.9418 / 238,173.79); stated line-partial
gap (200.0476); customer reconciliation (793 customers); product sparsity
fully flagged; frozen inputs byte-identical before/after; WAD dual
reconciliation (5.55e-17) with no averaging of rates. Determinism was
additionally verified by byte-comparison across consecutive runs (7/7
identical). No check was waived and none failed.

## 7. Frozen-input hash protection

SHA-256 recomputed during this audit, identical to the hashes recorded in
`PHASE_3B_VALIDATION.md` and the quality report, and unchanged by the
audit (read-only access throughout):

- `data/processed/fact_sales_cogs.csv`
  `4d8de717486b323ffb656d13c94fd6bd94f8e61d1a93ea339a602ab5303b9988`
- `data/processed/fact_margin_map_phase2.csv`
  `4c471feeda642e5ecbd2263782b4fc0f1655962f6c6488bdfe47886df2f01cb1`
- `data/processed/order_margin_map_phase2.csv`
  `ae6c349c9995747f2fef91cf1db6b940a73d99d6b2fede5ff3dff918f429d267`

## 8. Key decisions

D3B-01 bands adopted unchanged after passing all Phase 3A §4.4 gates;
D3B-02 provisional 30/10 thresholds with flag-not-suppress discipline and
fully disclosed heavy flagging at fine grains; D3B-03 single order-WAD
band rule; D3B-04 no quantile comparator (not needed for validation);
D3B-05 product × band file created as a fully flagged reference with
documented sparsity justification (mean 5.28 lines per product; all 4,031
cells below thresholds); D3B-06 order-level contribution authority with
below-order-grain NULL discipline and ambiguity preservation. No decision
in this phase selects a scenario, elasticity, quantity-response, or costing
assumption of any kind.

## 9. Known limitations

Margins are conditional on the revenue-based modeled COGS structure
(within-benchmark-group gross margins constant across bands by
construction); freight is observed under the carried Phase 2 methodology
caveat with line-grain contribution partial; return status is order-level
filter context only with one UNKNOWN order never defaulted; return/support
layers OFF so the zero-loss-customer observation is baseline-conditional;
customer × band detail is arithmetic throughout and product detail is
reference-only (both fully flagged); band-quantity patterns compare
different order compositions (notably multi-line mixed B1 orders) and
isolate no discount influence.

## 10. Standing statements

- The results are descriptive historical associations observed in
  transactions, not estimates of demand response.
- All modeled margins are conditional on the modeled COGS structure.
- No causal conclusions are permitted on these outputs; the non-causal
  reading guide in `PHASE_3B_DISCOUNT_ANALYSIS.md` travels with every reuse.
- Pricing scenarios and elasticity modeling were not started.
- **Phase 3B is complete and ready to freeze** on owner approval of this
  document.

## 11. Git checkpoint status

At audit time the working tree is clean (no modified tracked files, no
untracked files remaining): Phase 1 and Phase 2 remain as frozen and
committed, and the Phase 3A architecture record, Phase 3B script, outputs
record, and Phase 3B documents are carried in commit `9b44952` ("Add Phase
3A architecture and Phase 3B discount analysis"). This document,
`docs/PHASE_3B_FREEZE.md`, is the new freeze record prepared by the audit;
no new freeze commit is claimed by the audit itself — committing it is an
owner action. No Git operations of any kind were performed during the audit.

**PHASE 3B FROZEN** (effective on owner approval of this record).

Freeze date: **2026-09-12.**
