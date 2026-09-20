# Returns / Refund Treatment Remediation

## 1. Problem

Audit ISS-03/L-03 (P1): 296 orders flagged returned, yet their revenue is
retained in profitability. The refund/reversal leg was never implemented —
correctly or not, this had to be proven from evidence rather than assumed.

## 2. Source Return Data

- Freight universe: `Dataset 1 Apoorva.zip` → `Global_Superstore2.csv` US
  segment (9,994 rows, `Shipping Cost` present; join audit total 238,173.79).
- Returns universe: `sample_-_superstore.xls` → `Returns` sheet: 296 rows ×
  2 cols (`Order ID`, `Returned`), all values `Yes`. No `No` rows, no dates,
  no quantities, no amounts, no reasons, no credit/debit fields.
- Raw canonical CSV (`archive.zip`) contains NO return columns at all.
- Repository-wide search for `refund_amount|returned_amount|return_amount|
  credit_note|quantity_returned|refund_date|return_date` returns zero files.
  No negative-sales or cancellation rows exist (0 negative sales, 0 zero
  sales, 0 non-positive quantities in fact).

## 3. Return Grain

Order-level ONLY (verdict E-evidence):
- `Returns.Order ID` is an order header key (296 unique IDs, one row each).
- Crosswalk (`build_phase2_fact.py:189-242`) maps via order-suffix +9-year
  assertion + per-order line-set verification (295 exact + 1 one-cent
  tolerance) to 296 MarginMap orders + 1 unmappable UNKNOWN
  (`CA-2015-102015`, never defaulted).
- Flag repeats per line (`return_status` on all 9,994 lines) but meaning is
  order-level: 296 YES orders = 800 lines; 4,712 NOT_RETURNED; 1 UNKNOWN.
- 206/296 YES orders (70%) are multi-line (mean 2.70, max 14). The flag
  cannot identify WHICH lines/quantities were returned.

## 4. Returned-Order Profile

| Metric | YES (296 orders) | Share of project |
|---|---|---|
| Lines | 800 | 8.0% |
| Revenue | 180,504.28 | 7.86% |
| COGS (modeled) | 117,948.71 | 7.90% |
| Freight (line, NaN-skipped) | 19,660.10 | 8.25% |
| Contribution (NaN-skipped) | 42,895.47 | 7.60% of LINE total |
| Quantity | 3,053 | 8.06% |
| Quarantined obs. profit | 23,232.36 | 8.11% |
| Multi-line orders | 206 (70%) | — |
| Single-line orders | 90 (30%) | — |
| Lines w/ negative modeled contrib | 12 | — |

No partial quantities, no mixed returned/non-returned lines within an order
are identifiable — the source never splits an order.

## 5. Refund Evidence

NONE. No monetary refund, credit note, reversal amount, refund date, or
returned-quantity field exists in any repository dataset (raw, secondary,
processed, or backup). Full-order reversal would therefore be an assumption,
not an observation.

## 6. Candidate Treatments

| Model | Required | Available | Verdict |
|---|---|---|---|
| A. Flag only (current) | order IDs | 296 verified + 1 UNKNOWN | SUPPORTED |
| B. Full-order reversal | per-order refund = 100% proof | none | REJECTED (fabrication) |
| C. Line-level reversal | line mapping | none (70% multi-line ambiguous) | REJECTED |
| D. Quantity partial | returned qty | none | REJECTED |
| E. Actual refund amount | refund field | none | REJECTED |

## 7. Selected Treatment

OUTCOME C: retain flag-only (Model A). `return_status` stays an OBSERVED
order-level flag for filtering/cohorts; values retained as observed; no
revenue/COGS/freight reversal modeled.

## 8. Assumptions

- YES ⇒ order had ≥1 returned line (which lines unknown).
- NOT_RETURNED ⇒ absence from candidate Returns (completeness caveat
  documented in `RETURNS_DATA_COMPATIBILITY_REPORT.md`).
- UNKNOWN (`CA-2015-102015`) retained, never defaulted.

## 9. Implementation

- No pipeline value change (correct outcome needs no new fields; adding
  `refund_amount` with zero evidence would invite misuse).
- `frontend/src/pages/Orders.tsx`: explicit caveat — flag observed,
  no refund/reversal modeled.
- `backend/tests/test_returns_treatment.py`: grain (296/5,009/statuses),
  retention (YES revenue > 0, statuses preserved via API), no refund
  columns in contract.

## 10. Before vs After

Values UNCHANGED by design (any change would be fabrication):
revenue 2,297,200.86, contribution (LINE) 564,916.89, YES revenue retained
180,504.28. Hypothetical full-reversal illustration ONLY (NOT implemented):
revenue −180,504.28 → 2,116,696.58; COGS −117,948.71; freight −19,660.10
(line-matched); contribution −42,895.47 → ~522,021 (LINE). Labeled
ASSUMPTION; requires 100%-refund + freight-recovery + zero-residual proofs
that do not exist.

## 11. AO Impact

NONE — no AO rebuilt (values identical). AO-05 already carries
`return_status` per row as flag context; AO-01..04/06 unaffected.

## 12. Cost-to-Serve Impact

NONE — freight retained as observed fulfillment cost (fulfillment happened
regardless of later return). Return-handling leg stays OFF/0 (excluded, not
zero cost), per `COST_TO_SERVE_MODEL.md` separation of refund (revenue
adjustment) vs handling cost (serve cost).

## 13. SQLite Impact

NONE — no rebuild (no output change). Counts 20/238/105/420/60108/125.

## 14. API Impact

NONE — contract unchanged; `return_status` filter already exposed and
verified by new tests.

## 15. React Impact

One labeling fix: Orders caveat (above). No value, filter, or layout change.

## 16. Power BI Impact

NONE — no AO change. 53 pre-existing Desktop churn files untouched.

## 17. Validation

- New: 3 backend tests PASS (grain/retention/no-refund-columns).
- Existing: backend 47/47, frontend 23/23, lint clean, build clean,
  SQL validation PASS, independence checker PASS.
- Determinism: no pipeline edits to values; raw untouched.

## 18. Limitations

Order-level flag cannot support line refunds; NOT_RETURNED rests on
candidate completeness; UNKNOWN retained; multi-line ambiguity (206 orders)
quantified above; freight/COGS recovery economics unanswerable from data.

## 19. Reproducibility

`build_phase2_fact.py` crosswalk (fail-loud) + new tests. No manual steps.

## 20. Remaining Risks

A future reviewer may still misread retained YES revenue as "profit after
returns" — mitigated by the Orders caveat, AO limitation fields, and this
report. Any future refund feed must be event-grained (order/line + amount +
date) before modeling.
