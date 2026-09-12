# Phase 2 Data Compatibility Report (investigation only — no modeling, no merges)

> Read-only investigation over frozen Phase 1 outputs and two candidate
> enrichment ZIPs in the project root. No frozen file was modified; no merged
> dataset was created; no cost rates were invented. Probes ran from temp
> scripts outside the project; only this report is a new persistent artifact.

## 1. Executive conclusion

- **Dataset 1 → Outcome A: sufficiently compatible.** Its US segment
  (`Market == US`, 9,994 rows) is the same transaction universe as frozen
  Phase 1, verified by 100% composite-signature matching plus exact totals on
  every comparable field. Documented transformations (year shift, recoded
  Order/Row IDs, coarser product names on 197 rows) are understood and do not
  block a future join. It **can be used as a Phase 2 enrichment source** for
  Shipping Cost, subject to the join key (§4) and grain finding (§10).
- **Returns → Outcome B: cannot be reliably joined.** Dataset 2's Returns
  sheet uses a structurally incompatible Order ID scheme (0/1,970 direct
  matches, 0/20 sample, 0/174 US-specific, 0 after serial-stripping). It
  belongs to Dataset 2's own Orders universe (100% match there). Returns
  **must remain unavailable for authoritative return analysis** against the
  Phase 1 universe until a validated crosswalk exists — none does today.

## 2. Dataset 1 overview

`Dataset 1 Apoorva.zip` → `Global_Superstore2.csv` (latin1, 12,089,916 bytes;
`.xlsx` twin not needed). Shape **51,290 × 24**: the 21 Phase 1 source
columns plus `Market`, `Shipping Cost`, `Order Priority`. Zero nulls except
`Postal Code` (41,296, all non-US). Markets: APAC 11,002 · LATAM 10,294 ·
EU 10,000 · **US 9,994** · EMEA 5,029 · Africa 4,587 · Canada 384. Global
span 2011-01-01 → 2014-12-31; global sales 12,642,501.91. US segment:
5,009 orders, 793 customers, 1,862 Product IDs, dates 2011-01-04 →
2014-12-31, `Order Priority` = Medium 5,710 / High 3,069 / Critical 783 /
Low 432.

## 3. Dataset 2 overview

`Dataset 2 Rohitgrewal.zip` → `Global Superstore Data.xlsx` (extracted to
temp, not the project). Sheets: **Orders** (51,290 × 24 — same row count as
Dataset 1, same global sales 12,642,501.91 to the cent, dates 2014-01-01 →
2017-12-31, but transformed keys: short Product IDs e.g. `FUR-BO-4861`,
customer-coded Order IDs e.g. `IN-2017-CA120551-42816`, 25,728 order IDs vs
Dataset 1's 25,035); **Returns** (2,033 × 3: `Returned`, `Order ID`,
`Region`); **People** (24 × 2, irrelevant). Returns: all 2,033 rows
`Returned = Yes`, 0 nulls, **1,970 unique Order IDs**, 61 duplicated IDs
(124 rows, byte-identical duplicates — §9). Regions span 23 values incl.
Western/Eastern/Central/Southern US (405 rows, 174 unique US- IDs).

## 4. Dataset 1 ↔ Phase 1 compatibility results

| # | Check | Dataset 1 US | Frozen Phase 1 | Result |
|---|---|---|---|---|
| 1 | Structure | 24 cols (21 + Market/ShipCost/Priority) | 21 source cols | Superset ✅ |
| 2 | Rows | 9,994 | 9,994 | ✅ |
| 3 | Columns/dtypes | Same names/types (dates DD-MM-YYYY strings) | Same (M/D/YYYY) | ✅, parse with `dayfirst` |
| 4 | Order ID format | `CA-2012-124891` (years 2011–14) | `CA-2016-152156` (years 2014–17) | Recoded (§6) |
| 5 | Unique Order IDs | 5,009 | 5,009 | ✅ count |
| 6 | Order dates | 2011-01-04 → 2014-12-31 | 2014-01-03 → 2017-12-30 | +3y−1d shift (§6) |
| 7 | Ship dates | 2011-01-08 → 2015-01-06 | 2014-01-07 → 2018-01-05 | Same shift ✅ |
| 8 | Sales total | 2,297,200.8603 | 2,297,200.8603 | ✅ exact |
| 9 | Quantity total | 37,873 | 37,873 | ✅ exact |
| 10 | Discounts | All 12 values, identical counts (0.0×4,798 … 0.45×11) | Identical | ✅ exact |
| 11 | Customers | 793 IDs = same set; names = same set | 793 | ✅ |
| 12 | Product IDs | 1,862 = same set | 1,862 | ✅ |
| 13 | Product Names | 1,841 (coarser on 197 rows, §12) | 1,850 | ⚠️ documented |
| 14 | Category / Sub-Cat | Same sets; agree on all matched pairs | Same | ✅ |
| 15 | Ship Mode | Identical counts (5,968/1,945/1,538/543) | Identical | ✅ |
| 16 | Region | Identical counts (3,203/2,848/2,323/1,620) | Identical | ✅ |
| 17 | City / State | Identical sets; agree on all matched pairs | Same | ✅ |

Composite-signature match (`Customer ID, Product ID, Sales, Quantity,
Discount, Ship Mode, City, State`, no dates/IDs/names): outer merge
**9,996 pairs / 0 left-only / 0 right-only** — i.e. 100% of rows both sides
(the 9,996 = 9,994 + 2 from one benign 2×2 key, §12). Matched-set sales,
quantity, and discount distribution reconcile exactly.

## 5. Dataset 2 Returns ↔ Dataset 1 compatibility results

| Test | Result |
|---|---|
| Returns IDs in Dataset 1 (direct, 1,970 IDs) | **0** |
| 20 representative Dataset 1 Order IDs in Returns | **0** |
| US-specific (174 US- Returns IDs ∩ 5,009 D1-US IDs) | **0** |
| After stripping Returns trailing serial | **0** (structures still differ) |
| Returns IDs in Dataset 2 Orders (own universe) | **2,033/2,033 = 100%** |
| Unmatched Returns IDs (vs D1) | 1,970 unique (all) |

## 6. Order ID format comparison

| Universe | Format | Example | Years |
|---|---|---|---|
| Phase 1 | `XX-YYYY-NNNNNN` | `CA-2016-152156` | 2014–17 |
| Dataset 1 | `XX-YYYY-NNNNNN` | `CA-2012-124891` | 2011–14 |
| Dataset 2 Orders/Returns | `XX-YYYY-CUSTCODE-SERIAL` | `US-2017-FH1427528-43096` | 2014–17 |

Phase 1 ↔ Dataset 1: same shape, different code values (0% direct
intersection), but **5,002/5,009 numeric suffixes shared with an exact +3-year
mapping**; the 7 exceptions match the 7 year-boundary spill rows from the
+3y−1d date shift (year-count deltas 2,580→2,587 / 3,319→3,312). Different
formats do NOT mean different transactions here — the composite evidence (§4)
proves identity. Dataset 2's scheme is structurally incompatible with both:
no suffix correspondence exists, and Dataset 2 counts **25,728** order IDs
against Dataset 1's **25,035** for the same 51,290 rows — the order universes
are partitioned differently, so even a D1↔D2 order join is unsafe without
further study (out of scope; D2 adoption is not proposed).

## 7. Match rates

- Phase 1 Order IDs found in Dataset 1-US: **0% direct** (recoded), **100%
  via composite signature** (9,994/9,994 rows; 1 benign ambiguous key).
- Dataset 1-US Order IDs found in Phase 1: symmetric to above.
- Returns Order IDs found in Dataset 1: **0%** (0/1,970 unique).
- US-specific Returns ∩ D1-US: **0%** (0/174).
- Returns Order IDs found in Dataset 2 Orders: **100%** (2,033/2,033 rows).

## 8. Sample match evidence

- Identical double-line order both sides: D1 `US-2011-150119` rows 34702/34703
  ≡ Phase 1 `US-2014-150119` rows 3406/3407 (`LB-16795`, `FUR-CH-10002965`,
  281.372 × 2 @ 0.3, Standard, Columbus OH, 2011-04-23 ≡ 2014-04-23) —
  including the duplicated-line structure, confirming the same source events.
- 20-ID sample (seed 7) from Dataset 1 checked against Returns: 0 hits
  (list retained in probe logs; IDs span CA/US prefixes across all years).
- Name-collapse example: Phase 1 `OFF-EN-10001028 … 'Staple envelope'` ≡
  Dataset 1 same PID named `'Staples'` (48 rows) — IDs and money identical,
  label coarser.

## 9. Duplicate Return Order ID investigation

61 Order IDs appear twice (124 rows). Every duplicate pair is **byte-identical**
(`Returned`, `Order ID`, `Region` all equal; 61 distinct patterns for 124
rows) — pure file-level duplication contributing zero additional information,
not multiple return events (no event count, date, or line detail exists to
distinguish a "second return"). Per instructions duplicates were NOT dropped;
any future use must dedupe explicitly with owner approval and record the rule.
Returned-order line counts in Dataset 2 Orders range 1–13 (US: 50×1-line …
1×11-line), confirming Returns is **order-level**: one row per order at most,
with no line, quantity, or value detail.

## 10. Shipping Cost grain investigation

Field `Shipping Cost` (float64, 0 nulls, 0 zeros, 0 negatives; range
0.01–933.57; mean 23.83, median 5.10; 3,804 distinct values). Decisive test:
**all 2,471 multi-line orders show varying Shipping Cost across their lines**
(e.g. one order: 32.08 vs 12.97 on lines of 502.49×3 and 196.70×6) — it is
**genuinely line-level**, not an order charge repeated per line. Line-level
summation therefore does not double-count an order total; naive US line sum =
**238,173.79** vs order-dedup sum 194,551.57 (the latter is meaningless under
line grain — reported only to quantify the double-count fallacy if grain were
misread). No approval for use is granted here (architecture update deferred);
grain safety is established for a future loader.

## 11. Data-quality findings

- D1: no nulls in functional fields; US `Postal Code` complete (global
  nulls are non-US structural); dates need `dayfirst` parsing; `.xlsx` twin
  unexamined (CSV sufficed).
- D2 Returns: 124/2,033 rows are exact duplicates (§9); `Returned` is a
  constant `Yes` (no `No` rows — absence proves nothing, §2 of brief).
- D2 Orders: same global totals as D1 but different order partitioning
  (25,728 vs 25,035 IDs) — a second, subtler incompatibility.
- Cross-version name drift (D1 `Staples` collapse; encoding variants behind
  136 D1↔D2 signature mismatches) means **Product Name must never be a join
  key** across file versions; Product ID + money + parties is the reliable
  key.

## 12. Risks / ambiguities

1. **One ambiguous composite key with material consequence.** Key
   (`LB-16795`, `FUR-CH-10002965`, 281.372 × 2 @ 0.3, Standard, Columbus OH)
   matches 2 rows each side (D1 rows 34702/34703 ≡ Phase 1 rows 3406/3407,
   order `US-2011-150119` ≡ `US-2014-150119`). The D1 candidates differ on
   Shipping Cost (**21.59 vs 3.46**), so row-level pairing is genuinely
   ambiguous — either assignment attaches a different freight value to a
   Phase 1 row. Aggregates (order/customer/product) are unaffected either
   way (order total 25.05 is invariant). A future loader must handle this
   pair explicitly (e.g. order-level assignment with a documented split, or
   an ambiguity flag) — never silently pick a pairing.
2. **197 name-coarsened rows**: shipping-cost join unaffected (key excludes
   names), but any future product-label display from D1 would degrade 46
   products — frozen Phase 1 names must remain canonical.
3. **7 suffix-mismatched orders**: join must use the composite key, never
   Order ID suffix mapping.
4. **Returns absence ≠ non-return**: Returns lists only returned orders from
   an incompatible universe — no flag may be manufactured for Phase 1 orders.
5. **Shipping Cost provenance unknown**: values are observed in-file but
   their original computation (carrier bill vs internal formula) is
   undocumented — future architecture must tier it accordingly (observed
   field, unverified methodology).

## 13. Recommended path forward

1. **Approve Dataset 1-US as the Phase 2 freight enrichment source** keyed
   on the §4 composite signature (frozen Phase 1 names/IDs stay canonical;
   document the +3y−1d / recode / name caveats in the architecture update).
2. **Keep Returns unavailable** for authoritative analysis; revisit only with
   a validated crosswalk (none exists) or a native return feed.
3. When architecture is updated: treat Shipping Cost as **line-level
   observed-but-unverified** input feeding the F-S/F-H evaluation; run the
   order-dedup fallacy check as a loader assertion; dedupe Returns only by
   approved rule if its universe is ever adopted.
4. Do not adopt Dataset 2 Orders (order-partition mismatch) without its own
   compatibility study.

## 14. Authoritative-data statement

Authoritative today: all frozen Phase 1 outputs (unchanged). Conditionally
joinable (pending architecture approval, not yet usable): Dataset 1 US
Shipping Cost at line grain via the composite key. **Not authoritative and
not joinable**: Dataset 2 Returns for the Phase 1 universe (wrong key
universe; order-level `Yes`-only flags with no quantity, refund, date,
reason, or line detail — §2 of brief: no refund inferred, no cost computed,
no flag manufactured). No other new data was validated.
