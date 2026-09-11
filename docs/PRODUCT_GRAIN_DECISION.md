# Product Grain Decision (Phase 1C-1)

> Investigation only. No COGS, rates, allocations, or profit calculations were
> created. Source data and `data/processed/fact_sales.csv` were not modified
> (read-only input). Method: `src/data/analyze_product_grain.py`;
> evidence: `data/processed/product_grain_diagnostics.csv` (64 rows, one per
> conflicting product_id + product_name) +
> `data/processed/product_grain_diagnostics.json`.
> Price tolerance: **0.01 (1 cent), comparisons on UNROUNDED values**.

## 1. Purpose

A future COGS model needs one cost per unit of "product." Phase 1B showed
`product_id` cannot be assumed to be a clean 1:1 product key (32 IDs map to 2
names each, 337 rows). Assigning one COGS per `product_id` before resolving
this would attach a single unit cost to what may be two different products and
corrupt every downstream margin. This document establishes the correct
analytical grain on evidence, before any COGS work (Phase 1C-2).

## 2. Dataset Evidence

- Distinct Product IDs: **1,862**. Distinct Product Names: **1,850**.
- IDs with exactly one name: **1,830**. IDs with two names: **32 (1.719%)**.
  No ID has more than two names. Affected rows: **337 (3.372%)**.
- Affected sales: **$97,465.67 (4.243%)**; affected quantity **1,273 (3.361%)**.
  Material — cannot be ignored or averaged away.
- Unique `product_id + product_name` combinations: **1,894** (= 1,862 + 32,
  exactly one extra combo per conflicting ID).
- Within-combo price behavior: every conflicting combo has **exactly 1 distinct
  implied unit price (range 0.00)**; sibling names under the same ID
  **always differ materially** (all 32 pairs, tolerance 0.01).
- Reverse phenomenon: **16 Product Names span multiple Product IDs**
  (314 rows, 3.14%), dominated by generic consumables
  (`Staples` → 10 IDs, `Staple envelope` → 9, `Easy-staple paper` → 8).
- Category/Sub-Category: **fully consistent** — 0 PIDs span categories, 0 span
  sub-categories, 0 (PID, name) combos span either. Safe as attributes.

## 3. Product ID Conflict Findings

All 32 collisions have the same shape: one ID, two names, each name with its
own constant implied unit price. Representative examples (full table in the
diagnostics CSV, sorted by rows desc):

| product_id | names (rows / sales) | implied units |
|---|---|---|
| OFF-PA-10001970 (19 rows) | `Xerox 1881` vs `Xerox 1908` | two distinct prices |
| TEC-AC-10003832 (18 rows, $11,203.76) | Imation 16GB flash drive vs Logitech P710e speakerphone | two distinct prices |
| FUR-FU-10004270 (16 rows) | two furnishings names | two distinct prices |
| TEC-AC-10002049 (15 rows, **$13,756.54**, largest conflict) | two accessories names | two distinct prices |
| **FUR-BO-10002213** (10 rows, $12,921.64) | `DMI Eclipse Executive Suite Bookcases` (6 rows, $11,046.61, unit **500.98**) vs `Sauder Forest Hills Library, Woodland Oak Finish` (4 rows, $1,875.03, unit **140.98**) | 500.98 vs 140.98 |

FUR-BO-10002213 is therefore typical, not exceptional: both names share
Category `Furniture` / Sub-Category `Bookcases`, yet are different-priced
items under one ID. Because name AND price both differ, these read as ID
collisions (not price drift), though the dataset alone cannot prove physical
SKU identity (§11). All records preserved; nothing merged, averaged, or deleted.

## 4. Product ID + Product Name Findings

The combination **is a stable analytical grain** on all tested dimensions:

- Uniqueness: 1,894 combos; each conflicting ID resolves into exactly 2
  price-constant combos (within-combo price range 0.00 everywhere).
- Attribute stability: 0 combos span categories; 0 span sub-categories.
- Discrimination: sibling names under one ID always differ in price, so the
  composite never lumps distinct-priced items.
- Caveat (not a failure): it does not collapse the reverse phenomenon (§5) —
  nor should it: distinct IDs must stay distinct.

## 5. Reverse Product Name Analysis

16 generic names appear under 2–10 IDs each (314 rows). Top cases: `Staples`
(10 IDs, 46 rows, $755.47), `Staple envelope` (9 IDs, 48 rows, $1,686.81),
`Easy-staple paper` (8 IDs, 46 rows, $2,504.19), `KI Adjustable-Height Table`
(2 IDs, 18 rows, $4,552.64). Classification (separate SKUs vs duplicate IDs vs
labeling inconsistency) is **unresolved ambiguity**: the dataset has no SKU,
UPC, or spec attributes to decide. Conservative treatment: keep every
(PID, name) distinct — never merge distinct IDs because names match. Name alone
must never be used as a key.

## 6. Category/Sub-Category Consistency

Per-PID: 0 multi-category, 0 multi-sub-category across all 1,862 IDs. Per
(PID, name): likewise 0/0. Category and Sub-Category are therefore safe
supporting attributes of the analytical grain (descriptive rollups, portfolio
cuts), with no evidence of hierarchy drift.

## 7. Candidate Analytical Keys

- **A. Product ID alone.** Rejected. Fails on 32 IDs / 337 rows / 4.24% of
  sales: one COGS per ID would force a single unit cost onto two
  different-priced items (e.g. 500.98 vs 140.98), mis-stating both margins.
  Simple and traceable, but factually wrong where it matters most
  (conflicts concentrate in high-value Technology/Furniture rows).
- **B. Product ID + Product Name.** Recommended. Resolves 100% of collisions
  into price-constant, attribute-stable groups; natural (human-readable,
  explainable in interview); fully reproducible (`product_id || product_name`);
  zero invented identifiers; original fields untouched. Cost: slightly wider
  grain (1,894 vs 1,862); does not resolve the 16 generic-name reverses —
  correctly, since those must stay split.
- **C. Surrogate/variant key.** Not warranted now. Adds an opaque ID layer,
  mapping maintenance, and join complexity with no demonstrated benefit over B:
  B already yields unique, stable, price-constant groups. Revisit only if a
  future source introduces same-ID/same-name variants (no such case observed).
- **D. PID + name + unit price.** Considered and rejected as redundant: name
  split already produces single-price groups (range 0.00 in all 64 combos), so
  price adds no discrimination and would bake a derived diagnostic into the key.

## 8. Recommended Analytical Grain

**ONE clear recommendation: `product_id + product_name` (Option B).**

- Physical form (Phase 1C-2, not now): `analytical_product_key =
  product_id || product_name`, coexisting with untouched
  `product_id` / `product_name` source columns.
- Why: it is the finest grain provably consistent with prices and attributes,
  it fixes every observed collision with no invention, and it degrades safely
  (unknowns stay split rather than merged).
- Effect on the 1,830 clean IDs: none — one combo each, identical rollups to
  PID-level analysis.

## 9. COGS Modeling Implication

When COGS is introduced (Phase 1C-2): assign **one COGS per unit per
`analytical_product_key`** (i.e. Option 2: PID + name → COGS per Unit), joined
on the composite key, with `product_id` retained for traceability. Consequences:
conflicting IDs get two independent unit costs (correct); clean IDs behave as
today; the 16 generic-name reverses keep per-ID costs (conservative; merging
them would require external SKU proof). No COGS values, rates, or assignments
are created in this phase.

## 10. Source Preservation Rule

Source `product_id` and `product_name` values remain **byte-identical and
unchangeable** in `fact_sales.csv` and all diagnostics. The analytical key is
additive (a new derived column in a later phase), never a replacement. No IDs
renamed, no names edited, no rows deleted, no prices averaged, no products
merged on visual similarity.

## 11. Known Limitations

- The dataset alone **cannot prove whether two names under one ID are distinct
  physical SKUs** (probable, given divergent prices) or a labeling defect; the
  recommendation is robust to either interpretation.
- The 16 reverse cases (one name, many IDs) cannot be classified without
  external SKU/spec data.
- Implied unit price assumes the Phase 1A identity (Sales net of discount);
  it is a diagnostic, not a validated list price.
- Findings are sample-bound (US Superstore 2014–2017); grain logic transfers,
  specific collisions do not.

## 12. Decision Status

**PHASE 1C-1 COMPLETE — PENDING REVIEW.** Not frozen until the project owner
approves the Option B recommendation. No Phase 1C-2 work (COGS, keys
materialization, profit math) begins before approval.
