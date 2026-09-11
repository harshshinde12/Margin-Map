# MarginMap — DATA AUDIT (Phase 0)

> Rule: no calculations, no synthetic data, no modeling in this phase.
> Everything below was observed directly from the source file.
> Audit date: 2026-09-11. Auditor: reproducible Pandas script over the ZIP.

## 1. Source inspected

- Folder: `Margin Map/` contained exactly **1 file**: `archive.zip` (562,846 bytes).
- ZIP contents: exactly **1 file**: `Sample - Superstore.csv` (2,287,806 bytes uncompressed).
- File type: CSV, header row present, comma-delimited, quoted text fields.
- **Encoding: `latin1`, NOT UTF-8.** UTF-8 read fails
  (`UnicodeDecodeError ... byte 0xa0`). All future Python reads must use
  `encoding="latin1"` (or `cp1252`).
- No other files, no data dictionary, no returns table, no cost table.

## 2. Shape & grain

- Rows: **9,994**. Columns: **21**. Missing values: **0 in every column**.
- Duplicate full rows: **0**.
- `Order ID`: **5,009 unique** over 9,994 rows → avg **~2.0 lines per order**.
  Duplicate `Order ID` values are EXPECTED (line-item grain), not a quality issue.
- Grain: **one row = one product line within an order**.
  `Row ID` is unique (9,994 unique, 1–9994) and is a line surrogate key, not an order key.

## 3. Exact columns (21, case/spacing sensitive)

```text
Row ID, Order ID, Order Date, Ship Date, Ship Mode, Customer ID, Customer Name,
Segment, Country, City, State, Postal Code, Region, Product ID, Category,
Sub-Category, Product Name, Sales, Quantity, Discount, Profit
```

Pandas dtypes as read: `Row ID int64, Quantity int64, Postal Code int64,
Sales/Quantity/Discount/Profit numeric, all others object (string)`.
Dates arrive as **strings** (`M/D/YYYY`, e.g. `11/8/2016`) and must be parsed.

## 4. Checklist answers (1–25)

| # | Item | Finding |
|---|------|---------|
| 1 | ZIP contents | `archive.zip` → `Sample - Superstore.csv` only |
| 2 | File types | CSV only. No Excel, no returns/cost sidecars |
| 3 | Row count | 9,994 |
| 4 | Column names | 21 listed above |
| 5 | Data types | 4 numeric + IDs/dates as strings; `Postal Code` read as int64 (see §7) |
| 6 | Missing values | 0 missing in all 21 columns |
| 7 | Duplicate rows | 0 fully-duplicate rows |
| 8 | Duplicate Order IDs | 4,985 extra lines beyond 5,009 unique IDs — expected line-item grain |
| 9 | Date range | Order Date **2014-01-03 → 2017-12-30**; Ship Date 2014-01-07 → 2018-01-05. 48 months, continuous (no empty months; Nov/Dec peaks each year) |
| 10 | Unique customers | **793** (`Customer ID` ⟷ `Customer Name` is 1:1, verified) |
| 11 | Unique products | **1,862 `Product ID`s / 1,850 `Product Name`s** (names not unique — see §7) |
| 12 | Unique regions | 4: West 3,203 · East 2,848 · Central 2,323 · South 1,620 rows |
| 13 | Unique categories | 3: Office Supplies 6,026 · Furniture 2,121 · Technology 1,847 |
| 14 | Unique segments | 3: Consumer 5,191 · Corporate 3,020 · Home Office 1,783 |
| 15 | Revenue fields | `Sales` only. **Proven to be NET of discount** (see §5) |
| 16 | Cost fields | **NONE.** No COGS, no unit cost, no freight column |
| 17 | Profit fields | `Profit` only. **Formula unknown — DO NOT USE BLINDLY** (see §6) |
| 18 | Discount fields | `Discount` only. Fraction 0–0.8, 12 distinct values. 48.0% of rows have 0 discount |
| 19 | Shipping/freight fields | **NONE.** Only `Ship Mode` (4 values) + `Ship Date`. No dollar freight column |
| 20 | Returns info | **NONE** (no flag, no table) |
| 21 | Support-cost info | **NONE** |
| 22 | COGS explicit? | **NO** |
| 23 | Channel explicit? | **NO.** Only possible proxy is `Ship Mode` (fulfilment method, NOT a sales channel) |
| 24 | Product weight? | **NO** |
| 25 | Already-calculated fields? | **YES — `Sales` and `Profit` are derived, not raw** (see §5–6). `Discount` is a rate. No list-price / unit-cost columns to reproduce them |

Additional dims observed: `Country` = United States only (1 value);
49 states, 531 cities; `Ship Mode` = Standard 5,968 · Second 1,945 ·
First 1,538 · Same Day 543. `Quantity` range 1–14 (mean 3.79).
`Sub-Category`: 17 values (Binders 1,523 … Labels 364 … full table in §8).

## 5. `Sales` is NET of discount (proven, not assumed)

For each row we computed `implied_unit = Sales / (Quantity × (1 − Discount))`.
For the same `Product ID` across different discounts the implied unit price is
**constant** (e.g. `FUR-BO-10000362` → 170.98 at discounts 0 / 0.15 / 0.2 / 0.3;
`OFF-PA-10001970` → 12.28 and 55.98 variants — see below). Therefore:

- `Sales = UnitPrice × Quantity × (1 − Discount)` (net revenue at line level).
- There is **no separate gross-revenue or discount-amount column**; discount
  dollars must be derived as `UnitPrice × Qty × Discount` once unit price is
  reconstructed — but that reconstruction is a Phase 1 decision, not audit.
- Do NOT treat `Sales` as gross revenue. Any formula using
  `gross − discount = net` must define gross from the implied unit price.

## 6. `Profit` field — DO NOT USE BLINDLY (critical warning)

- Totals: `SUM(Sales) = 2,297,200.86`, `SUM(Profit) = 286,397.02`,
  overall implied margin **12.47%**.
- Distribution: 8,058 positive rows, **1,871 negative (18.7%)**, 65 zero.
- Implied line margin (`Profit/Sales`): median 27%, mean 12.0%,
  min **−275%**, max **+50%**. 349 rows worse than −100%.
- Discount destroys margin in THIS field: 0 discount → +29.5% margin;
  (0–0.2] → +11.9%; (0.2–0.4] → −15.3%; (0.4–0.6] → −40.7%;
  (0.6–0.8] → **−122.6%**.
- Category margins inside this field: Furniture **+2.49%**,
  Office Supplies +17.04%, Technology +17.40%.
  Sub-categories **Tables −8.56%, Bookcases −3.02%, Supplies −2.55%** are
  lifetime-negative; Machines only +1.79%.
- What is unknown: whether `Profit` = `Sales − COGS` only, or already nets
  freight/allocations; what COGS basis (unit cost × qty?) was used; whether
  discount accounting is consistent (yes for Sales, unknown for Profit).
- **Risk of double-counting/leakage:** if we build
  `NetRevenue − COGS − freight − …` on top of a `Profit` that already
  subtracts something, we double-count. **Phase 1 must reverse-engineer or
  quarantine `Profit` (keep as reference column, never as model foundation)
  until its formula is validated.**

## 7. Data-quality issues (real, not blocking)

1. **Encoding is latin1**, not UTF-8 (§1). Reproducibility risk if ignored.
2. **Dates are strings** (`M/D/YYYY`, no time). Must parse explicitly;
   `Ship Date` max (2018-01-05) exceeds `Order Date` max — normal fulfilment lag.
3. **`Postal Code` as int64** loses leading zeros and forbids joins to geo tables.
   Store as zero-padded string in Phase 1.
4. **`Product Name` is not a key**: 1,862 IDs vs 1,850 names; one name maps to up
   to 10 IDs (e.g. generic `Staples`), and at least one ID maps to 2 names.
   **Always key products by `Product ID`, never by name.**
5. **One flagged ID — `FUR-BO-10002213`** — shows TWO distinct implied unit
   prices (140.98 and 500.98). Possible variant/price-change sharing one ID or
   a data entry error. Must be dispositioned in Phase 1 (no silent averaging).
6. **No missing values at all** (0/9,994 in every column) — unusually clean for
   real data; treat as convenient, not as proof of correctness.
7. **US-only, 4-year window** — no FX, no multi-country logic needed, but also
   no external validity beyond this sample. Seasonal peaks every Nov/Dec.
8. `Country` is a constant — drop or ignore in modeling (zero information).

## 8. Reference distributions (from audit scripts)

Discount values: 0.0: 4,798 · 0.2: 3,657 · 0.7: 418 · 0.8: 300 · 0.3: 227 ·
0.4: 206 · 0.6: 138 · 0.1: 94 · 0.5: 66 · 0.15: 52 · 0.32: 27 · 0.45: 11.

Sub-category lifetime margins (sales-weighted, inside `Profit` field):
Tables −8.56% · Bookcases −3.02% · Supplies −2.55% · Machines +1.79% ·
Chairs +8.10% · Storage +9.51% · Phones +13.49% · Furnishings +14.24% ·
Binders +14.86% · Appliances +16.87% · Art +24.07% · Accessories +25.05% ·
Fasteners +31.40% · Copiers +37.20% · Envelopes +42.27% · Paper +43.39% ·
Labels +44.42%.

Segment: Consumer 11.55% · Corporate 13.03% · Home Office 14.03%.
Region: Central 7.92% · South 11.93% · East 13.48% · West 14.94%.
Ship Mode: Standard 12.08% · Second 12.51% · Same Day 12.38% · First 13.93%
(near-flat — further evidence `Profit` likely EXCLUDES freight; otherwise
Same-Day/First-Class would trail — but this is a hypothesis to test, not a fact).

Loss-making cohorts (inside `Profit` field): 301/1,862 products and
155/793 customers lifetime-negative — Phase 2 must recompute these from the
transparent model, not copy them.

## 9. Gaps vs MarginMap requirements

| Requirement | Status | Recommended approach (decision needed, NOT implemented) |
|---|---|---|
| Sales + COGS integration | COGS MISSING | Option A: back-solve `COGS = Sales − Profit` as a diagnostic only (imports all `Profit` unknowns). Option B: build explicit unit-cost table per Product ID from external assumption + document as scenario. **Recommend A for diagnostics, B for the real model — confirm before Phase 1.** |
| Freight / logistics | MISSING (dollars) | Options: (1) Ship-Mode flat-rate allocation (transparent, arbitrary); (2) quantity- or sales-weighted allocation key; (3) external benchmark rates as scenario parameters. No weight → cannot do weight-based. **Recommend (1)+(2) as competing allocation keys with sensitivity test.** |
| Returns + return cost | MISSING | Options: (1) exclude returns scope explicitly and note as limitation; (2) scenario-rate (e.g. X% per sub-category) clearly labelled synthetic. **Recommend (1) for Phase 1, (2) only as labelled scenario in Phase 3+.** |
| Support / service cost | MISSING | Same as returns: exclude or scenario-rate per order/line. Needs your sign-off. |
| Allocation keys | NO INPUTS | Only viable keys from data: Quantity, Sales, line count, Ship Mode. Weight unavailable. **Recommend documenting all keys + running multi-key sensitivity.** |
| Discount analysis | POSSIBLE | `Discount` + net `Sales` + implied unit price support elasticity-lite and policy simulation. Cleanest Phase 3 input. |
| Channel | MISSING | `Ship Mode` is fulfilment, NOT sales channel. Options: (1) drop channel dimension; (2) treat Segment as pseudo-channel (document as proxy). **Recommend (1) + explicit limitation.** |
| Region / Segment / Product / Customer | PRESENT | Full drill-down possible. Customer = `Customer ID`, Product = `Product ID`. |
| Monthly variance | POSSIBLE | 48 continuous months; Order/Ship dates support monthly P&L once model exists. |
| Gross vs net margin formulas | BLOCKED on definitions | Cannot standardise until COGS/freight/returns treatment is agreed (see §10). |

**Fabrication rule:** nothing above was invented. Every missing field is marked
MISSING with options, not filled.

## 10. Open financial / business-model questions (must resolve before Phase 1)

1. **What is `Profit`?** Accept quarantine-and-reconstruct, or attempt full reverse-engineer first?
2. **Is `Sales` our Net Revenue?** Audit proves it is net of discount. Do we define `Gross = Sales/(1−Discount)` and `Discount$ = Gross − Sales`, or keep `Sales` as the top line? (Double-count risk if both are added.)
3. **COGS basis?** Back-solved vs assumed unit costs? Product-level or sub-category-level?
4. **Freight model?** Flat per Ship Mode? Per unit? Sensitivity range? Same-Day/First-Class premium?
5. **Returns & support?** Out-of-scope with limitation note, or labelled scenario rates?
6. **Channel definition?** Drop, or proxy? (Do NOT relabel Ship Mode as channel silently.)
7. **Contribution vs net margin?** Agree the layer cake:
   `Gross → Net (after discount) → Gross Profit (after COGS) → Contribution (after freight/allocations) → Net (after returns/support)` — confirm names before standardising.
8. **`FUR-BO-10002213` dual price?** Investigate, exclude, or average with note?
9. **Negative-margin rows (−275%)?** Keep (real discount economics) or cap for dashboard readability?
10. **Phase 1 grain?** Line-level fact table keyed by `Row ID` with `Order ID` as header — confirm.

## 11. Reproducibility

- Scripts used: ad-hoc Pandas reads of `archive.zip` / `Sample - Superstore.csv`
  with `encoding="latin1"`. No files were modified. No synthetic rows created.
- To reproduce: open the ZIP, read the CSV with `latin1`, expect 9,994 × 21,
  0 nulls, 5,009 orders, date range above, totals
  Sales 2,297,200.86 / Profit 286,397.02.
- Next phase needs: agreed formula sheet + allocation-key decision + confirmation
  to create `data/`, `notebooks/`, `src/`, `sql/`, `powerbi/` working files.
