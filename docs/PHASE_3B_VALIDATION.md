# Phase 3B Validation (implementation checks with evidence)

> Method: machine validation inside `src/data/build_phase3b_discount_analysis.py`
> (16/16 fail-loud checks PASS, recorded with values in
> `data/processed/phase3b_quality_report.json`) plus independent read-back
> verification of the written artifacts (row counts, reconciliation,
> determinism across consecutive runs, frozen-input hashes before/after).
> Each check cites the implementing decision or architecture rule.

## Results

- [x] **Discount calculations.** Net Revenue equals Sales on every line
  (max gap 0.00); Gross Revenue guarded for Discount = 1 (no such lines;
  guard exercised in code); Discount Amount equals Gross − Net with the
  dual form (`Gross × Discount`) reconciled to 1.82e-12; realization rate
  `Net/Gross × 100` on every aggregate; WAD is gross-revenue-weighted with
  the dual form (`1 − Net/Gross`) reconciled to 5.55e-17 — no arithmetic
  averaging of rates anywhere (architecture §3; D3B-01).
- [x] **Discount range.** All 9,994 discounts within [0, 1), observed range
  [0, 0.8]; zero NULLs; any NULL/outside value would abort (architecture
  §9.1).
- [x] **Band assignment.** All 9,994 lines exactly one band (B0 4,798 /
  B1 146 / B2 3,657 / B3 254 / B4 283 / B5 856); B0 exactly the
  zero-discount set; no observed value split across bands; band counts sum
  to 9,994; deterministic constants in versioned script (D3B-01).
- [x] **Order-band assignment.** All 5,009 orders exactly one WAD band
  (B0 2,055 / B1 415 / B2 1,634 / B3 278 / B4 274 / B5 353), derived purely
  from line data under the single D3B-03 rule; all orders verified
  single-segment and single-customer before attribution.
- [x] **Contribution integrity.** ORDER TOTAL 565,116.9418 / 24.6002%
  equals the frozen Phase 2 baseline exactly (tolerance 0.05); segment
  ORDER totals, customer totals (793 customers), and band ORDER totals all
  reconcile to the same baseline; order revenue/COGS rollups match the
  order fact to 1e-6; order margins recomputed SUM/SUM consistent to 1e-6
  (D3B-06; 2B.1 authority).
- [x] **Ambiguity preservation.** Exactly 2 flagged lines (NULL freight) in
  the single order `US-2014-150119`; nothing imputed; LINE partial trails
  the authoritative total by the stated 200.0476 gap; the affected order
  row carries the pair note with full-order freight 26.55 (verified on
  read-back: 1/5,009 order rows noted) (D3B-06).
- [x] **Below-order-grain discipline.** Category, sub-category, and product
  outputs carry NULL freight/cost-to-serve/contribution with reason
  `FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN`; product-level freight
  attribution absent everywhere (D3B-06).
- [x] **Data integrity.** 9,994 lines / 5,009 orders / unique row IDs;
  Phase 1 cross-check (row set, per-row sales and COGS) identical;
  quarantined Profit never loaded into any working frame and absent from
  all seven outputs (asserted in-script); scenarios OFF asserted on both
  input facts (all flags FALSE, all scenario costs 0); no elasticity
  estimation, no scenarios, no quantity-response assumptions exist in code
  or outputs.
- [x] **Determinism.** Two consecutive runs produce byte-identical CSVs
  (7/7 files, byte-compared) with identical row counts (14 / 39 / 19 / 69 /
  3,304 / 5,009 / 5,925); band definitions and thresholds live in script
  constants; quality report records per-file SHA-256.
- [x] **Frozen-artifact protection.** SHA-256 before/after the run:
  `fact_sales_cogs.csv 4d8de717…9988`, `fact_margin_map_phase2.csv
  4c471fee…01cb`, `order_margin_map_phase2.csv ae6c349c…429d` — all
  byte-identical; no Phase 1/Phase 2 file, script, or frozen document
  modified, regenerated, renamed, or overwritten; no Git operations
  performed.
- [x] **Reporting language.** Outputs and documents use observed /
  associated-with / descriptive-comparison / historical-pattern /
  conditional-on-modeled-structure language; the non-causal reading guide
  heads the analysis document; "caused higher sales", "increased demand",
  "elasticity", "optimal discount", and "best pricing policy" appear
  nowhere except in prohibitions.

## Design risks carried forward (not failures)

1. Customer × band (100% flagged) and product (100% flagged) grains cannot
   support comparative statements — the flags, not the values, are the
   message at those grains (D3B-02, D3B-05).
2. Within-benchmark-group gross margins are invariant across bands by
   construction — any future reader tempted to compare them is referred to
   §6/§13 of the analysis document.
3. Order-basis and line-basis band rows answer different questions (order
   economics vs line composition, e.g. B1) — the `basis` column must be
   honored in any reuse; the two bases must never be mixed in one average.

**IMPLEMENTATION VALIDATED — PHASE 3B READY FOR REVIEW.** No scenarios were
activated; no elasticity or quantity-response values were introduced. Phase
3B stops here — pricing scenarios and elasticity modeling are not started.
