# Returns Data Compatibility Report

> Investigation only. Candidate file read from a temp copy; the original was
> not modified. No frozen Phase 1 file touched; no return costs computed; no
> rates invented; no git operations.

## 1. Candidate Dataset

- **Filename:** `sample_-_superstore.xls` (3,422,208 bytes, project root)
- **Workbook sheets:** `Orders` · `People` · `Returns`
- **Source structure:**
  - `Orders`: 10,194 rows × 21 cols (US Superstore layout with renamed
    geo columns `Country/Region`, `State/Province`; native datetimes;
    Order IDs `US-2023-103800` / `CA-2023-…`, 5,111 unique; dates
    2023-01-03 → 2026-12-30; sales 2,326,534.35). A newer, larger variant
    of the Superstore universe (+200 rows / +29,333.49 sales vs MarginMap).
  - `People`: 4 × 2 (regional managers — irrelevant).
  - `Returns`: 296 rows × 2 cols (`Order ID`, `Returned`); 0 nulls; 0
    duplicate rows; IDs `US-2023-100762`-style, years 2023–2026
    (53/61/77/105), prefixes all `US`.

## 2. Returns Table Profile

- **Rows:** 296. **Unique Order IDs:** 296 (no duplicates — nothing to drop).
- **Columns:** `Order ID` (string), `Returned` (string).
- **Grain:** one row per returned **order** (all 296 IDs resolve inside the
  workbook's own Orders; returned orders there span 1–13 lines, so the flag
  cannot be line-attributed).
- **Duplicates:** none.
- **Returned values:** `Yes` × 296 only — no `No` rows exist.
- **Unavailable in table:** quantity, refund amount, return date, return
  reason, processing cost, line detail — none present.

## 3. MarginMap Compatibility

| Metric | Result |
|---|---|
| Candidate return rows | 296 |
| Candidate unique Order IDs | 296 |
| MarginMap unique Order IDs | 5,009 |
| Exact Order ID matches | **0** (different ID scheme AND different era) |
| Match rate (direct) | **0.00%** |
| Candidate-only IDs | 296 |
| MarginMap-only IDs | 5,009 |
| Deterministic crosswalk matches (§4) | **296 / 296** |
| Crosswalk match rate | **100%** (conditional, see §4) |

## 4. Join Feasibility

Direct join: **not feasible** (0% exact-ID overlap — different scheme
`US-2023-…` vs `CA-2016-…`, different era 2023–26 vs 2014–17). A silent or
naive join would attach zero rows or wrong rows.

Evidence-based deterministic crosswalk (validated, not guessed):

1. Returns `Order ID` → candidate `Orders.Order ID`: exact match, 296/296.
2. Candidate order → MarginMap order by **numeric suffix**, which is unique
   on the MarginMap side (5,009 suffixes → 5,009 orders, zero collisions):
   296/296 Returns rows resolve to exactly one MarginMap order.
3. Year relation on all 296 pairs is uniformly **+9 years**
   (2023→2014 … 2026→2017, zero exceptions) — asserted per row at load.
4. Full line-set verification (Customer, Product, Sales, Quantity, Discount
   per line): **295/296 exact**; the single delta is a 1-cent serialization
   difference (244.61 vs 244.62) on an otherwise identical order.
5. The 2 superficially ambiguous suffixes (shared by 2–3 candidate orders)
   resolve deterministically: the Returns-referenced candidate order is in
   each case the exact line-set twin of the single MarginMap order
   (e.g. 321.55 ≈ 321.552 vs the 32.70 decoy).

Join rules if approved: left join MarginMap orders → crosswalk on suffix
with the +9 year assertion fail-loud per row; `Returned = Yes` only for the
296 mapped orders; exactly **one** MarginMap order (`CA-2015-102015`, suffix
absent from the candidate universe) must remain **NULL/unknown**, never
`No`; all other absences may be treated as Not Returned only under the
completeness caveat (§5). Grain stays order-level — the flag must never be
pushed to lines.

## 5. Return Information Available

Observed: order-level Returned indicator (Yes) for 296 mapped orders, with
the deterministic crosswalk above. Unavailable: returned quantity, refunded
revenue, return date, return reason, processing cost, line-level attribution,
and status for 1 unmappable order. Absence semantics: `No` is licensed only
for mapped-universe absences under the assumption the candidate Returns
table is complete for its universe (stated caveat, not proven fact); the
candidate universe itself differs (+200 rows), so cross-era completeness
cannot be asserted absolutely.

## 6. Decision

**CONDITIONALLY APPROVED — REQUIRES SPECIFIC JOIN HANDLING**

The Returns table is a different-version Superstore artifact (verdict B on
the file as a whole), but its 296 flags attach deterministically and
transactionally-verified to MarginMap orders through the §4 crosswalk —
usable as an **observed order-level return indicator only**, under the join
rules, NULL rule, and caveats above. Any deviation (year-relation breach,
suffix collision, line-set mismatch beyond rounding) must fail the load,
not warn it.

## 7. Recommended Next Step

Approve the §4 crosswalk rules (including the `CA-2015-102015` NULL rule and
order-level-only restriction) as the sole licensed path for observed return
status; keep return processing cost as a modeled, OFF-by-default scenario
with no rate; do not extend this approval to any other cross-file join.
