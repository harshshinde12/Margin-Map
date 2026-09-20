# MarginMap — Financial Model (Phase 1A)

> Status: **Phase 1A — definitions only.** No values, rates, tables, code,
> or allocations are created in this document. All formulas below are the
> approved standard for later implementation. Source: `Sample - Superstore.csv`
> inside `archive.zip` (9,994 rows, line grain). See `DATA_AUDIT.md` for audit
> evidence and `KPI_DICTIONARY.md` for the KPI table. Decisions logged in
> `DECISION_LOG.md`.

## 1. Purpose

Establish the single, auditable financial logic for MarginMap before any
implementation, so that every later calculation (Python, SQL, Power BI) follows
the same definitions, lineage, denominators, and double-counting controls.

## 2. Business objective

Revenue growth can hide margin erosion when logistics, discounting, returns,
and support costs are not allocated correctly. MarginMap reveals true
profitability across Product, Customer, Region, Segment (and Channel only if
reliable channel data can be established later), supporting profitability
analysis, cost-to-serve analysis, pricing/discount decisions, scenario
analysis, margin-risk identification, monthly variance explanation, and
executive decision-making.

## 3. Financial waterfall (authoritative)

```text
Gross Revenue
      ↓ (− Discount Amount)
Net Revenue (= Sales)
      ↓ (− COGS)
Gross Profit
      ↓ (− Freight / Logistics Cost)
      ↓ (− Return-related Cost)
      ↓ (− Support / Service Cost)
Contribution Profit
Contribution Margin % = Contribution Profit / Net Revenue × 100
```

COGS is a product cost. Freight + Return + Support = Total Cost-to-Serve
(operational/service cost). The two layers must never be merged.

## 4. Revenue definitions

### 4.1 Net Revenue (authoritative revenue measure)

- **Formula:** `Net Revenue = Sales`
- **Reason:** verified source `Sales` already reflects the recorded discount
  (Phase 0 implied-unit-price test). Subtracting discount again double-counts.
- **Source:** source field `Sales`. **Type:** source-derived. **Grain:** transaction line.

### 4.2 Gross Revenue (derived reference only)

- **Formula:** `Gross Revenue = Sales / (1 − Discount)`, Discount as decimal.
- **Example:** Sales = 800, Discount = 0.20 → Gross = 800 / 0.80 = 1,000.
- **Status:** reconstructed reference metric. NOT an independently sourced
  list-price field. Must be labelled as derived wherever shown.
- **Edge case:** if `Discount = 1`, return NULL/blank (division by zero).
  If `Discount` is NULL/missing: **REQUIRES VALIDATION** — do not default to 0
  without a documented rule (Phase 1B decision).

### 4.3 Discount Amount

- **Primary formula:** `Discount Amount = Gross Revenue − Net Revenue`
  (i.e. `Gross Revenue − Sales`).
- **Equivalent:** `Discount Amount = Gross Revenue × Discount`.
- Use the first form as primary because it reconciles Gross to Net.

### 4.4 Discount %

- Source field `Discount`, stored as decimal (0.20 = 20%).
- Do not multiply the stored field by 100 inside calculations; multiply by 100
  only for display formatting.

## 5. Discount definitions (analytics framing)

- **Discount Leakage = Gross Revenue − Net Revenue.** This is a revenue
  reduction associated with the recorded discount. Do NOT call it profit loss
  automatically — profitability impact depends on cost structure.
- **Discount impact on contribution (conceptual, Phase 3 to model):**
  higher discount → lower Net Revenue → potentially lower Contribution Profit
  and Contribution Margin %, unless volume response offsets it. No model built
  in Phase 1A.

## 6. COGS definitions (future modeled input — no values in Phase 1A)

### 6.1 COGS per Unit

- Conceptual definition: modeled product-level unit cost.
- No value created in Phase 1A. Methodology, source/assumption, and validation
  approach to be designed later. Every modeled field must carry those three
  attributes before use.

### 6.2 Total COGS (future formula)

- **Formula:** `COGS = Quantity × COGS per Unit`.

### 6.3 Gross Profit

- **Formula:** `Gross Profit = Net Revenue − COGS`.

### 6.4 Gross Margin %

- **Formula:** `Gross Margin % = Gross Profit / Net Revenue × 100`.
- If `Net Revenue = 0`, return NULL/blank. Never divide by zero.
- Denominator is always Net Revenue, never Gross Revenue.

## 7. Cost-to-serve definitions (future modeled inputs — no rates in Phase 1A)

> Superseded in part by Phase 2: OBSERVED `Shipping Cost` is joined line-grain
> (9,994/9,994 matched; see `docs/COST_TO_SERVE_MODEL.md` §2). The Phase 1A
> statements below remain the Phase 1A record; for freight methodology,
> ambiguity handling (`ORDER_LEVEL_AMBIGUOUS`), and OFF-scenario semantics,
> `docs/COST_TO_SERVE_MODEL.md` governs.

Cost-to-serve is conceptually separate from COGS: product cost vs.
operational/service cost of selling and servicing the customer/order.
Scope: Freight/Logistics, Return-related, Support/Service costs.

### 7.1 Freight Cost

- NOT available in source (only `Ship Mode` + dates, no dollar cost).
- Future modeled input. No rate created in Phase 1A.

### 7.2 Return Cost

- Return information NOT available in source. Future modeled input or
  explicitly documented scenario layer. No values in Phase 1A.

### 7.3 Support Cost

- Support/service information NOT available in source. Future modeled input or
  explicitly documented scenario layer. No values in Phase 1A.

### 7.4 Total Cost-to-Serve

- **Formula:** `Total Cost-to-Serve = Freight Cost + Return Cost + Support Cost`.
- Do NOT include COGS inside Cost-to-Serve.

## 8. Contribution profitability

- **Formula:** `Contribution Profit = Net Revenue − COGS − Freight Cost − Return Cost − Support Cost`.
- **Equivalent:** `Contribution Profit = Gross Profit − Total Cost-to-Serve`,
  provided both components are calculated consistently.
- **Formula:** `Contribution Margin % = Contribution Profit / Net Revenue × 100`.
- If `Net Revenue = 0`, return NULL/blank. Denominator is Net Revenue.

## 9. Variance definitions (future reporting)

- **Absolute variance:** `Variance = Actual − Comparison`.
  Example: `Revenue Variance = Current Month Revenue − Previous Month Revenue`.
- **Variance %:** `Variance % = (Actual − Comparison) / Comparison × 100`.
  If `Comparison = 0`, return NULL/blank.
- **Margin change:** report in **percentage points**, not percent.
  Example: 18% → 15% = **−3 percentage points** (not "−3%").
- Future metrics: Revenue Variance, Gross Profit Variance, Gross Margin Change,
  Contribution Profit Variance, Contribution Margin Change, Cost-to-Serve Variance.

## 10. Source vs modeled data

- **Source-derived:** `Sales`, `Quantity`, `Discount`, `Profit` (quarantined
  reference only), order/customer/product/region/segment/ship-mode attributes,
  dates. Lineage: direct from CSV.
- **Modeled (future):** COGS per unit, COGS, Freight, Return, Support,
  allocation outputs, scenario outputs. Each requires methodology +
  source/assumption + calculation logic + validation approach before use.
- Never mix source and modeled values without labelling. Never present a
  modeled cost as observed.

## 11. DO NOT DOUBLE COUNT — CRITICAL CONTROL

1. `Sales` is already Net Revenue. Do NOT subtract `Discount` from `Sales` again.
2. Reconstructed `Gross Revenue` is derived via `Sales / (1 − Discount)`;
   `Discount Amount = Gross − Net`. Do not add a second discount deduction.
3. Source `Profit` is QUARANTINED. Do NOT compute `COGS = Sales − Profit` and
   do NOT treat `Sales − Profit` as official COGS.
4. COGS stays separate from Cost-to-Serve. `Total Cost-to-Serve = Freight +
   Return + Support` only — never add COGS inside it; never subtract COGS twice
   via both `Gross Profit` and `Cost-to-Serve`.
5. `Ship Mode` is a shipping/logistics dimension, NOT sales channel.
   `Segment` is NOT sales channel either. Channel absence is a documented limitation.
6. When return data is introduced later, establish whether refunded revenue is
   already removed from `Sales`; if so, do NOT subtract returns revenue a
   second time. Return *cost* (handling, reverse logistics) is separate from
   refunded *revenue* — define each before implementing.
7. Freight must appear exactly once per line: either as a direct cost or as an
   allocated cost, never both. Allocation outputs must reconcile to the
   allocation-period control total.
8. Any future implementation violating these rules must be flagged and blocked
   before merge/dashboard release.

## 12. Edge cases

| Case | Rule |
|---|---|
| `Discount = 1` | `Gross Revenue` = NULL/blank (division by zero) |
| `Discount` NULL / outside [0, 1) | **REQUIRES VALIDATION** — no silent default; Phase 1B must set a rule |
| `Net Revenue = 0` | All margin % and any /Net-Revenue metric = NULL/blank |
| Variance `Comparison = 0` | `Variance %` = NULL/blank (absolute variance still reported) |
| Margin change | Percentage points, never "%" shorthand |
| `Quantity ≤ 0`, negative `Sales` | **REQUIRES VALIDATION** — none observed in audit (Quantity 1–14), but implementation must guard |
| `FUR-BO-10002213` dual implied unit price | **REQUIRES VALIDATION** — investigate before unit-price reconstruction is used |
| Source `Profit` formula | Unknown — quarantined; diagnostic use only after investigation |

## 13. Current data limitations

No explicit COGS, unit cost, freight dollars, returns, support costs, sales
channel, or product weight in source. `Country` is constant (US only).
`Product Name` is not a key. `Ship Mode`/`Segment` are not channels.
Reconstructed `Gross Revenue`/`Discount Amount` are derived references, not
observed list prices. See `DATA_AUDIT.md` §§7–10.

## 14. Decisions reserved for later phases

- COGS per-unit methodology, source, and validation (Phase 1B+).
- Freight/return/support allocation drivers, keys, grains, periods (Phase 1B/2).
- Whether returns/support are excluded scope or labelled scenarios.
- Channel solution, if any (documented limitation until then).
- Discount elasticity-lite and policy simulation design (Phase 3).
- Dashboard/decimal/NULL display conventions and variance comparison choices
  (Phase 4). None of these are decided in Phase 1A.
