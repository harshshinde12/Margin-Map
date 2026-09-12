# Phase 2B Data Model (implementation — scenarios OFF)

> Built by `src/data/build_phase2_fact.py` → `data/processed/
> fact_margin_map_phase2.csv` (9,994 rows × 49 cols, line grain) +
> `data/processed/phase2_quality_report.json`. All 14 fail-loud checks (A–M)
> pass; determinism verified by repeated execution. Phase 1 frozen inputs
> byte-identical before/after. No dashboard, no recommendations, no rates.

## 1. What this dataset is

The first Phase 2 analytical fact: frozen Phase 1 financials (Net Revenue,
modeled COGS, Gross Profit/Margin) plus **observed freight** and **observed
order-level return status**, with return-processing and support held as
OFF/default-zero scenarios. Contribution here is therefore the
freight-loaded baseline — the MarginMap modeled/observed measure under
current scenario settings, explicitly not actual profit.

## 2. Observed inputs

### Modeled COGS (frozen Phase 1, reused bit-identical)

`modeled_cogs` = Net Revenue × modeled COGS % (benchmark-derived, frozen).
Totals: revenue 2,297,200.86 · COGS 1,493,910.13. Carried through untouched;
re-asserted equal post-build.

### Observed Freight (Dataset 1-US join)

`freight_cost_observed` = line Shipping Cost from `Dataset 1 Apoorva.zip` →
`Global_Superstore2.csv`, US segment, joined by composite signature
(Customer ID, Product ID, Sales, Quantity, Discount, Ship Mode, City, State):
9,994/9,994 lines matched, 0 unmatched (fail-loud). Line-grained (varies
across all multi-line orders); US total 238,173.79.

**Source note (documented correction):** the task brief named
`sample_-_superstore.xls` as the freight source, but its Orders sheet
contains no Shipping Cost column (fail-loud KeyError on first run). The
validated source per the compatibility investigation is Dataset 1-US, whose
join-audit total matches the expected 238,173.79 exactly. Returns still come
from the workbook per the validated crosswalk. Nothing about the methodology
changed — only the file pointer, on evidence.

**Ambiguity handling.** Key (`LB-16795`, `FUR-CH-10002965`, 281.372 × 2 @
0.3, Standard, Columbus OH) matches two candidate rows (21.59 / 3.46) for
Phase 1 rows 3406/3407: both lines carry `freight_cost_observed = NULL`,
`freight_ambiguity_flag = TRUE`, `freight_join_status = MATCHED_AMBIGUOUS`
(9,992 lines are `MATCHED_UNIQUE`). The invariant pair total (25.05) is
preserved at order level via `freight_order_total` (informational per line —
**do not sum**; the ambiguous order's full total is 26.55 including two
uniquely-matched lines at 1.50). Consequence, stated openly: the 2 lines
carry NULL `cost_to_serve`/`contribution_*`, so summed contribution excludes
their 225.10 gross profit; order-level contribution for that order is
computable as order revenue − order COGS − 26.55.

### Observed Return Status (order-level, crosswalked)

`return_status` ∈ `YES` (800 lines / 296 orders) · `NOT_RETURNED` (9,188
lines) · `UNKNOWN` (6 lines / order `CA-2015-102015`, suffix absent from the
candidate universe — never defaulted). Mapping: candidate Return ID → exact
candidate order → numeric suffix → unique MarginMap order, with +9 year
assertion and line-set verification per return (295 exact + 1 one-cent
tolerance, fail-loud otherwise). `NOT_RETURNED` rests on the documented
candidate-Returns completeness assumption. The flag repeats per line **for
filtering only** — it does not establish which product lines were returned.

## 3. Scenario inputs (OFF)

`return_processing_cost_scenario = 0` with `return_processing_scenario_
enabled = FALSE`; `support_cost_scenario = 0` with `support_scenario_enabled
= FALSE`. Zero means *scenario excluded from contribution*, never actual
business cost. No return/support rates exist anywhere in this phase.

## 4. Derived measures (scenarios OFF)

```text
cost_to_serve       = freight_cost_observed + 0 + 0   (NULL if freight NULL)
contribution_profit = net_revenue − modeled_cogs − cost_to_serve
contribution_margin_pct = profit / net_revenue × 100  (NULL if net = 0; none)
```

Totals: cost-to-serve 238,148.74 (line sum; +25.05 held at order level =
238,173.79) · contribution profit 564,916.89 · overall margin 24.59%
(SUM/SUM). `source_profit_quarantined` is carried through and referenced in
zero calculations (structural — the script never reads it except passthrough).

## 5. Grain and label discipline

One row = one MarginMap product-line transaction (`row_id` unique, order
preserved). All 35 Phase 1 columns retained in order; 14 Phase 2 columns
appended. Order-level attributes (`freight_order_total`, `return_status`)
repeat per line only as labeled: the first is do-not-sum informational, the
second a filter flag. Every modeled/scenario field keeps its Phase 1/2A
prefix; `freight_cost_observed` is unprefixed-by-design (observed signal).
BI consumers must re-assert dtypes on read (booleans serialize True/False).

## 6. Limitations carried into review

- Contribution is freight-only: return/support layers OFF by design.
- 2 lines NULL-contribution (ambiguity control, §2).
- Return YES is order-level; 1 order UNKNOWN; NOT_RETURNED is
  assumption-conditional.
- Shipping Cost methodology unverified (observed field, not audited bills).
- No customer/product analysis, recommendations, or dashboard in this phase.
