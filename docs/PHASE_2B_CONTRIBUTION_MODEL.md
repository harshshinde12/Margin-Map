# Phase 2B Contribution Model — Order-Level Authority (2B.1 correction)

> Built by `src/data/build_phase2_order_fact.py` (reads the line fact
> read-only) → `data/processed/order_margin_map_phase2.csv` (5,009 rows, one
> per order). All 16 fail-loud checks pass; deterministic across runs. The
> line fact is byte-identical before/after; Phase 1 untouched.

## 1. Why order grain is authoritative for contribution

The line fact correctly leaves rows 3406/3407 freight-NULL (21.59 vs 3.46
individually unknowable), so line-level SUM understates project contribution
by 200.0476 — correct NULL propagation, but wrong project total, because
order-level freight IS fully known. Contribution therefore aggregates
authoritatively at order grain and above; the line fact remains the detailed
source, never overwritten, never back-filled.

## 2. Construction (no line assignment invented)

Per order: revenue/COGS summed from lines; freight = summed uniquely-assigned
line freight **plus the 25.05 ambiguous-pair total on its order only**
(order `US-2014-150119` totals 26.55 including 1.50 of unique lines —
independently cross-checked against the line fact's own order totals, gap
< 1e-6). Return status rolls up unmixed (YES > UNKNOWN > NOT_RETURNED; mixed
orders would abort). Scenarios OFF (0), enforced on input and output.

```text
order_cost_to_serve = order_freight + 0 + 0
order_contribution_profit = order_revenue − order_cogs − order_cost_to_serve
order_contribution_margin_pct = profit / revenue × 100 (NULL if revenue 0)
```

## 3. Reconciliation (exact)

Revenue 2,297,200.8603 · COGS 1,493,910.1285 · Freight 238,173.79 ·
Contribution profit **565,116.9418** · Overall margin **24.60%** (SUM/SUM).
Ambiguous order freight = 26.55. Return YES = 296 orders; UNKNOWN = 1
(`CA-2015-102015`); scenarios OFF; Profit quarantined untouched;
COGS/CTS separate.

## 4. Grain authority rules

- **Overall / order / customer-level contribution:** authoritative from the
  order fact (or equivalently line sums plus the documented 25.05 pair
  adjustment — same number both ways).
- **Transaction lines 3406/3407:** remain NULL-freight, flagged, unassigned —
  no analysis may impute 21.59/3.46 to either row.
- **Product-level contribution:** NOT derivable from this correction. The
  25.05 pair belongs to one order, not to either line's product view without
  an attribution rule — any product split requires a separate documented
  attribution decision (D2A-series) and must never be inferred from the
  order-level treatment. Until then, product contribution stays out of scope.
