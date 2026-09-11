# MarginMap — Decision Log (Phase 1A)

> Append-only. New decisions get the next number. Never silently change a
> decision — supersede with a new dated entry referencing the old one.

## D01 — Sales = Net Revenue

- **Decision:** `Net Revenue = Sales` (source field, line grain).
- **Reason:** Phase 0 proved `Sales = UnitPrice × Qty × (1 − Discount)` via
  constant implied unit price per Product ID across discounts.
- **Impact:** `Sales` is the single revenue denominator for all margins and
  variances. Subtracting discount from `Sales` again is a double-count error.

## D02 — Source Profit remains quarantined

- **Decision:** existing `Profit` column is diagnostic/reference only; never the
  official profitability calculation; never compute `COGS = Sales − Profit`.
- **Reason:** original `Profit` formula is unknown (which costs it nets is
  unproven); building on it risks double-counting/leakage.
- **Impact:** official profit metrics (`Gross Profit`, `Contribution Profit`)
  require an explicit COGS input built later; `Profit` may be compared
  diagnostically only after investigation.

## D03 — Ship Mode ≠ Channel

- **Decision:** do not rename or report `Ship Mode` as sales channel.
- **Reason:** `Ship Mode` (Standard/Second/First/Same Day) is a fulfilment
  method, not where/how the sale was made.
- **Impact:** no channel analysis on `Ship Mode`; channel stays a limitation.

## D04 — Segment ≠ Channel

- **Decision:** do not rename or report `Segment` (Consumer/Corporate/Home
  Office) as sales channel.
- **Reason:** segment is customer type, not sales channel.
- **Impact:** channel requires a separate future solution; segment used only
  as customer-type dimension.

## D05 — Product ID is the product key

- **Decision:** `Product ID` is the key; `Product Name` is a descriptive
  attribute only.
- **Reason:** audit found 1,862 IDs vs 1,850 names (one name → up to 10 IDs;
  one ID → 2 names; `FUR-BO-10002213` dual-price flag).
- **Impact:** all product joins/aggregations keyed by `Product ID`; name never
  used as a key in code, SQL, or Power BI.

## D06 — COGS will be modeled separately (no values in Phase 1A)

- **Decision:** `COGS = Quantity × COGS per Unit` with a future modeled
  per-unit input; no rates or tables created in Phase 1A.
- **Reason:** source has no COGS/unit-cost; inventing values now would corrupt
  the waterfall and interview traceability.
- **Impact:** `Gross Profit`/`Gross Margin %` formulas are approved but not
  computable until the COGS input (methodology + assumption + validation) exists.

## D07 — Freight will be modeled separately (no rates in Phase 1A)

- **Decision:** freight is a future modeled cost-to-serve input; no rates,
  keys, or allocations selected in Phase 1A.
- **Reason:** no dollar freight in source (only `Ship Mode`); no weight for
  weight-based keys.
- **Impact:** `Total Cost-to-Serve` and `Contribution` formulas approved but
  freight component pending Phase 1B/2 design.

## D08 — Returns are absent from source data

- **Decision:** no return flag/table exists; return cost is a future modeled or
  explicitly labelled scenario layer; nothing invented in Phase 1A.
- **Reason:** field search (Return/Returns) returned no columns.
- **Impact:** Phase 1 scope excludes returns; later work must separate refunded
  revenue from handling cost to avoid double-subtraction.

## D09 — Support costs are absent from source data

- **Decision:** no support/service data exists; support cost is a future modeled
  or explicitly labelled scenario layer; nothing invented in Phase 1A.
- **Reason:** field search (Support/Service) returned no columns.
- **Impact:** contribution model carries the line item with pending methodology.

## D10 — No invented rates or costs in Phase 1A

- **Decision:** Phase 1A produces definitions, formulas, lineage, and controls
  only — no fact/dimension tables, scripts, COGS/freight/return/support values,
  synthetic data, simulators, or dashboards.
- **Reason:** accuracy and traceability outrank speed; internship evaluation
  requires every number to be explainable.
- **Impact:** implementation phases are blocked on these definitions; any
  deviation must be logged as a new decision, not a silent edit.
