# CTS / Freight Remediation Report

## 1. Executive finding

Methodology SOUND with one latent hardening fix. Freight is observed
line-grain Shipping Cost joined line-to-line with exact reconciliation at
every layer (238,173.79). No double-counting occurs in any shipped path;
`freight_order_total` is informational and never summed. Postal handling
verified correct post-fix. Decision: B/C — sound, minor hardening applied.

## 2. CTS definition

Cost-to-serve = OBSERVED line freight + return-handling OFF (0, excluded) +
support OFF (0, excluded). OFF means excluded, never zero cost. No packaging,
labor, payment, service, or warehousing components exist — explicitly
excluded, documented in `COST_TO_SERVE_MODEL.md`. The project does not claim
complete CTS; no "complete cost-to-serve" language found anywhere.

## 3. Freight source

`Dataset 1 Apoorva.zip` → `Global_Superstore2.csv`, `Market == "US"` segment:
9,994 rows, `Shipping Cost` float64, 0 null / 0 zero / 0 negative in US
(2 zeros exist only outside US), range 0.01–933.57, mean 26.38, 10,037
distinct values, total 238,173.79. Monetary meaning: per-row fulfillment
shipping cost (methodology caveat: carrier methodology unverified, recorded
in model docs). `sample_-_superstore.xls` has NO Shipping Cost column
(proven by fail-loud KeyError on first attempt; documented correction).

## 4. Freight grain

LINE-grain in source: 2,471 multi-line orders carry distinct per-row freight
(e.g. CA-2011-100090: 32.08 + 12.97 = 45.05). Mapping preserves per-line
values 1:1 (9,994/9,994 exact signature matches + 1 ambiguous key held NULL
at line, total preserved at order). NO allocation is performed or needed —
allocation candidates were evaluated and withdrawn (would fabricate).

## 5. Join architecture

Composite signature (Customer ID, Product ID, Sales, Quantity, Discount, Ship
Mode, City, State) exact merge: 9,994/9,994 matched, 0 unmatched, exactly one
ambiguous key (rows 3406/3407, pair total 25.05, order total 26.55).
Exact-float risk: REAL but currently passing with dual-form reconciliation
(≤1e-6) and fail-loud gates; documented as brittleness (any float
re-serialization breaks loudly, never silently). Postal code correctly
EXCLUDED from the key.

## 6. Postal-code audit

Post-fix state verified: 9,994/9,994 five-digit (raw had 438 four-digit),
`05408` recovered on 11 rows, 631 distinct (matches raw), 0 null. Join key
excludes postal; state/region untouched (49 states, 4 regions). Postal
changes do not affect freight joins or regional analysis. No further change.

## 7. freight_order_total audit

Created in `build_phase2_fact.py:173` (per-order deduped sum mapped to lines),
stored per line, documented DO NOT SUM. Sole code consumer
(`build_phase2_order_fact.py:91`) correctly dedupes by order_id. AO/SQL/API/
React/Power BI never reference the column.

## 8. Double-counting test

`SUM(freight_order_total)` over lines = 719,883.26 (≈3× truth) — hazard
confirmed REAL as a trap, but NOT TRIGGERED: contribution uses
`freight_cost_observed`; order fact cross-checks against deduped totals
(±1e-6). Concrete example CA-2011-100090: lines carry 32.08/12.97 with
repeated 45.05; contribution sums 32.08+12.97, never 45.05×2.

## 9. Reconciliation table

| Source | Grain | Rows | Orders | Freight Total | Δ vs raw | Status |
|---|---|---|---|---|---|---|
| D1-US Shipping Cost | line | 9,994 | 5,009 | 238,173.79 | +0.00 | PASS |
| fact line freight (NaN-skip) | line | 9,992 | 5,009 | 238,148.74 | −25.05 (held at order) | PASS |
| Ambiguous NULL pair | order | 2 | 1 | 25.05 | — | PASS |
| Line + ambiguous | total | 9,994 | 5,009 | 238,173.79 | +0.00 | PASS |
| Order fact order_freight | order | 5,009 | 5,009 | 238,173.79 | +0.00 | PASS |
| AO-01 cost_to_serve | TOTAL | 1 | 5,009 | 238,173.79 | +0.00 | PASS |
| AO-02 ORDER CTS TOTAL row | band | 1 | 5,009 | 238,173.79 | +0.00 | PASS |

## 10. Observed vs modeled distinction

Freight: OBSERVED (field-level, methodology caveat). Return/support: OFF
(scenario pools, excluded). COGS: MODELED (external benchmarks).profit:
DERIVED. Labels verified across README, model docs, AO limitation fields,
and UI badges.

## 11. Order vs line treatment

Mixed-grain by design and correct: line-native values at line grain; order
sums at order grain; TOTAL at AO-01; baseline bands at AO-02/04. No
allocation invented. `min_count` hardening (below) preserves NULL semantics
for a future fully-ambiguous order.

## 12. Contribution identity

`contribution = revenue − COGS − freight − 0 − 0` holds: TOTAL
(565,116.94 = 2,297,200.86 − 1,493,910.13 − 238,173.79); order-level max gap
1.8e-12; band-level reconciled by pipeline gates.

## 13. Returns interaction

YES-return freight (19,660.10) retained as observed fulfillment cost;
UNKNOWN order freight fully observed (6 lines, order total 13.42). No refund,
recovery, or handling leg modeled — Returns contract preserved.

## 14. Scenario interaction

Unchanged: hypo CTS = observed order freight passthrough (variance exactly
0, gated); new uniform_0.20 instance inherits the same treatment. Scenario
contract preserved.

## 15. Edge-case results

Zero freight: 0 in US (none to handle). Missing: exactly 2 ambiguous NULL
lines, flagged, never imputed. Negatives: 0 freight; 50 negative-contribution
orders (legitimate economics). Freight>revenue: 0 orders. Max freight order
CA-2015-124891 (1,288.99 on 3,419.87 revenue). Multi-line: 2,471 orders with
distinct per-line freight, all preserved. All bands/regions covered.

## 16. Root cause(s)

No material defect found. One latent issue: `sum(min_count=0)` converts a
hypothetical all-NaN freight group to 0 instead of NULL (masked today —
ambiguous order has 2 valued lines). Exact-float join brittleness and the
`freight_order_total` trap are documented risks, not active bugs.

## 17. Remediation performed

`build_phase2_order_fact.py:82`: `min_count=0` → `min_count=1` (all-NaN →
NULL instead of wrong-zero). Output byte-identical today (hash `ae6c349c…`
unchanged) — proof it was latent, not active. No AO/SQL/API/React/Power BI
changes required (nothing downstream shifts by even 1e-9).

## 18. Before/after metrics

Order fact hash, freight total, contribution, and all AO hashes identical
before/after. Only added: 6 regression tests.

## 19. Validation results

- Backend 55/55 (49 + 6 new CTS tests), frontend 23/23, lint clean, build
  clean, SQL 13/13 PASS, independence checker PASS.
- Browser (real Chrome/Blink): 7 routes zero pageerrors.

## 20. Remaining limitations

Exact-float join brittleness (fail-loud, not fail-safe); `freight_order_total`
remains a documented trap for future authors; carrier methodology unverified;
no return-handling/freight-recovery economics (no data); fully-ambiguous
future order now yields NULL contribution by design (correct but untested in
production data).

## 21. Final methodology decision

B (sound; documentation already correct) + C (minor latent hardening
applied). Data supports observed-freight CTS as shipped; nothing claimed
beyond it.

## 22. Reproducibility instructions

`build_phase2_fact.py` → `build_phase2_order_fact.py` (cross-checked) →
downstream chain → `load_data.py` → `validate_sql_outputs.py` →
`pytest backend/tests/test_cts_freight.py`. All fail-loud, deterministic.
