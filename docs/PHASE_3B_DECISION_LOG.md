# Phase 3B Decision Log — Observed Discount Impact Analysis

> Append-only within Phase 3B. New decisions take the next `D3B-NN` number.
> Phase 3A documents (`PHASE_3A_DISCOUNT_PRICING_ARCHITECTURE.md`,
> `PHASE_3A_DECISION_LOG.md`, frozen as the approved architecture record),
> Phase 1 decisions (`docs/DECISION_LOG.md`, frozen) and Phase 2A decisions
> (`docs/COST_TO_SERVE_DECISION_LOG.md`, frozen) are cited, never edited.
> No elasticity coefficients, scenario assumptions, or quantity-response
> assumptions are selected anywhere in this log.

## D3B-01 — Six-band structure adopted as specified (validation passed)

- **Decision:** adopt the Phase 3A candidate bands unchanged:
  B0 `d = 0`; B1 `0 < d <= 0.15`; B2 `0.15 < d <= 0.25`;
  B3 `0.25 < d <= 0.35`; B4 `0.35 < d <= 0.55`; B5 `0.55 < d <= 0.80`.
- **Evidence (machine-asserted in-script):** 12 discrete discount values in
  [0, 0.8], no NULL, none outside [0, 1); all 9,994 lines assigned exactly
  one band; B0 holds exactly the 4,798 zero-discount lines; no observed
  value split across bands; line counts B0 4,798 / B1 146 / B2 3,657 /
  B3 254 / B4 283 / B5 856.
- **Alternatives:** amending boundaries (rejected: no gaps, overlaps, or
  split values found — no defect to repair).
- **Rationale:** the candidate passed every Phase 3A §4.4 validation gate,
  so silent alteration would have been unjustified.
- **Unresolved:** none.

## D3B-02 — Provisional sample-size thresholds: 30 lines / 10 orders

- **Decision:** implement `minimum_line_count = 30` and
  `minimum_order_count = 10` exactly as provisionally specified, recorded in
  script configuration and in `phase3b_quality_report.json`. A row is flagged
  (`low_sample_flag = TRUE`) when either count is below its threshold. Cells
  are never suppressed or merged.
- **Status of the numbers:** provisional analytical thresholds, not
  universal statistical rules. They encode a conservative reading posture
  (flag thin cells as arithmetic, not evidence), not a significance claim.
- **Observed consequence (disclosed, not repaired):** the thresholds flag
  heavily at fine grains — 2,511/2,511 customer × band rows, 782/793
  customer TOTAL rows, 5,925/5,925 product rows, 10/52 occupied
  sub-category × band cells. This is reported as a finding about the limits
  of fine-grain discount inference, not as a defect in the thresholds.
- **Alternatives:** lowering thresholds per grain until flags "look better"
  (rejected: that would hide thin evidence rather than disclose it).
- **Unresolved:** whether future phases keep these values (owner review).

## D3B-03 — Order band by order weighted-average discount (single rule)

- **Decision:** the one order-band rule is
  `order_wad = SUM(line discount_amount) / SUM(line gross_revenue)` over the
  order's lines, banded with the same fixed B0–B5 boundaries. No competing
  rule (e.g. dominant-line band) is implemented anywhere.
- **Evidence:** all 5,009 orders receive exactly one band (B0 2,055 /
  B1 415 / B2 1,634 / B3 278 / B4 274 / B5 353); order WAD is derived purely
  from line data (no invented order discount); all 5,009 orders verified
  single-segment and single-customer, so segment/customer attribution of
  order-basis rows is clean.
- **Rationale:** WAD preserves the revenue meaning of mixed-discount orders
  (e.g. the 415 B1 orders contain 1,324 lines, mostly zero- and
  standard-discount lines whose average falls in the low band).
- **Unresolved:** none.

## D3B-04 — No quantile comparator built

- **Decision:** the quantile comparator is not built. It was not necessary
  for validation: the fixed bands passed coverage, uniqueness, value
  integrity, and reconciliation gates on their own.
- **Rationale:** per the brief, the fixed six-band structure is the primary
  design; an unneeded comparator would add surface without evidence value.
- **Unresolved:** none (a comparator may be proposed again in a later phase
  if a concrete validation need arises).

## D3B-05 — Product × band file created as a flagged reference (sparsity justification)

- **Decision:** create `discount_product_summary.csv` with PRODUCT_TOTAL
  (1,894) plus PRODUCT_BAND rows (4,031 occupied cells), gross-profit-only,
  with `low_sample_flag` on 5,925/5,925 rows and `low_volume_flag` retained
  for the 93 single-order products. The file is labeled descriptive
  reference only and excluded from comparative statements.
- **Sparsity analysis (the justification):** products average 5.28 lines
  (median 5, maximum 15); mean 2.13 bands spanned per product; all 4,031
  occupied product × band cells fall below the provisional thresholds. No
  product-level discount comparison can therefore be presented as evidence —
  but a fully flagged reference preserves machine-readable band detail for
  the higher-volume products and keeps the grain set complete.
- **Alternatives:** omitting the file (rejected: the brief permits
  product × band when sparsity is clearly flagged, and flagging is fully
  implemented; omission would leave the product grain uncovered without
  adding rigor).
- **Unresolved:** none.

## D3B-06 — Contribution authority implemented as designed

- **Decision:** authoritative order-level contribution (joined from
  `order_margin_map_phase2.csv`, never recomputed) is used on ORDER-basis
  band/segment rows, customer TOTAL and CUSTOMER_BAND rows (customer orders
  in band, bottom-up), and order rows. Category, sub-category, and product
  outputs carry NULL freight/contribution with reason
  `FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN`. LINE-basis band/segment rows
  carry explicitly labeled partials (`LINE_PARTIAL_EXCL_AMBIGUOUS`) beside —
  never instead of — the authoritative ORDER rows, with the 200.0476 gap
  stated. The ambiguous pair (rows 3406/3407, order `US-2014-150119`) is
  never imputed; the affected order carries
  `ORDER_CONTAINS_AMBIGUOUS_PAIR_25P05_HELD_AT_ORDER`.
- **Evidence:** ORDER TOTAL contribution 565,116.9418 reconciles exactly to
  the frozen Phase 2 baseline; segment ORDER totals, customer totals, and
  band ORDER totals all reconcile to the same baseline.
- **Unresolved:** none.

## Questions answered in this phase (no longer pending)

1. ~~Band adoption~~ — adopted unchanged (D3B-01).
2. ~~Threshold values~~ — 30 lines / 10 orders, provisional (D3B-02).
3. ~~Order-band rule~~ — order WAD band, single rule (D3B-03).
4. ~~Quantile comparator~~ — not built (D3B-04).
5. Scenario quantity-response assumptions — untouched; no scenarios exist in
   Phase 3B (still deferred).
6. Fixed-unit-cost COGS comparator — not developed (still not approved).
7. Display conventions — column-lineage and labeling rules recorded in
   `PHASE_3B_DISCOUNT_ANALYSIS.md` §2; visual conventions remain deferred.
