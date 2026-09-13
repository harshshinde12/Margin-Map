# Phase 4B Implementation — First Slice (Uniform Discount Replacement)

> Status: **IMPLEMENTED AND VERIFIED — first slice only.**
> Built by `src/data/build_phase4b_scenarios.py` → one uniform-replacement
> scenario at stated rate 0.10 plus `phase4b_scenario_quality.json`
> (15/15 fail-loud checks pass; byte-identical across consecutive runs;
> frozen inputs byte-identical before and after). Design authority: the
> frozen Phase 4A architecture, the approved Phase 4B gate decisions
> (`docs/PHASE_4B_DECISION_LOG.md`), and `docs/PHASE_4B_IMPLEMENTATION_
> CONTRACT.md` §§1–10.
>
> **Reading guide — what this slice is and is not.** Every figure below is
> hypothetical arithmetic sensitivity under stated assumptions (constant
> observed quantity, frozen modeled-COGS percentage, observed freight
> passthrough, return/support OFF). Nothing here is a forecast, a demand
> statement, evidence about what would have sold, a causal estimate, or a
> pricing recommendation.

## 1. Purpose and scope

Implement the smallest contract-compliant vertical slice of the Phase 4B
scenario module: prove the full path — stated rate in, validated Order ×
Discount Band scenario out — with every Gate 9 check enforced, before any
broader scope (further scenario types, segment reporting, displays) is
considered. Out of scope by mandate: everything listed in §10.

## 2. Implemented scenario behavior

- **Scenario type:** uniform discount replacement (`uniform_replacement`,
  `replacement_rate` input form); **stated rate 0.10** (required CLI
  argument `--rate`, validated against [0.00, 0.80], recorded in metadata,
  output filename, and quality JSON — never hidden in code).
- **Scope:** all valid transaction lines (9,994; observed discounts
  verified within [0, 1), zero NULLs); out-of-scope passthrough not
  applicable in this slice since scope is universal.
- **Line level:** each line receives `hypothetical_discount = 0.10`;
  hypothetical net revenue, discount amount, and COGS computed per §4;
  quantity reused bit-identical; freight carried unchanged with NULLs
  preserved.
- **Order level:** bottom-up aggregation (sums of line hypotheticals);
  hypothetical cost-to-serve equals authoritative `order_freight` (which
  already holds the 25.05 ambiguous-pair total) plus 0 + 0; hypothetical
  contribution = hypo net − hypo COGS − order freight.
- **Reporting:** Order × Discount Band on the ORDER basis, grouped by
  **baseline** observed order-WAD bands (D3B-03 rule), so the B0 reference
  cohort stays identifiable: 6 band rows + TOTAL = 7 rows. Baseline
  (authoritative), hypothetical, and variance blocks side by side.

## 3. Input and output lineage

| Layer | Source | Standing |
|---|---|---|
| Observed baseline | `fact_margin_map_phase2.csv` (49 cols, 9,994 lines), `order_margin_map_phase2.csv` (10 cols, 5,009 orders) — read-only, hashed before/after | Observed historical fact |
| Derived reference | Gross revenue recomputed per frozen formula; order WAD; bands | Derived, never observed list prices |
| Modeled | `modeled_cogs_pct` per line from the line fact (never from order currency) | Analytical estimate, conditional |
| Authoritative join | `order_freight`, `order_cost_to_serve`, `order_contribution_*` from the order fact — joined, never recomputed | Phase 2 authority |
| Hypothetical | `hypothetical_*` columns computed under the stated rate | Scenario-only values |
| Unsupported | `fixed_unit_cost_view`, `demand_response_view` = `N/A` with explicit reasons | Marked unavailable, never estimated |

`source_profit_quarantined` is excluded from working frames (established
`usecols` pattern, load-time assertion). Outputs
(`phase4b_scenario_uniform_0.10.csv`, 7 rows × 52 cols;
`phase4b_scenario_quality.json`) are new ignored artifacts; frozen files
are never written.

## 4. Formula definitions

All formulas restate frozen Phase 1A definitions — nothing redefined;
quantity q held constant throughout:

```text
gross(line)        = sales / (1 - d)              [d = observed discount]
hypo_net(line)     = gross * (1 - 0.10)
                     = sales * 0.90 / (1 - d)      (dual form, reconciled)
hypo_disc_amt      = gross - hypo_net
hypo_cogs(line)    = hypo_net * modeled_cogs_pct / 100
hypo_cts(order)    = order_freight + 0 + 0        (return/support OFF)
hypo_contrib(order)= SUM(hypo_net) - SUM(hypo_cogs) - order_freight
band(order)        = baseline observed order-WAD band
variance           = hypothetical - baseline       (reconciled both ways)
margin change      = hypo_margin_pp - base_margin_pp   (SUM/SUM; pp units)
```

## 5. Validation coverage

15 unique recorded checks, 15/15 PASS: quarantine exclusion; input shapes;
scenarios OFF; observed discount range; ambiguity preservation (2 lines,
`US-2014-150119`); line dual-forms (gross/hypo/COGS-pct gaps ≤ 1e-6);
genuine snapshot freight passthrough (values identical, 2 NULLs, flags
unchanged); order-band coverage (B0 2,055 / B1 415 / B2 1,634 / B3 278 /
B4 274 / B5 353); **quantity-constant** (line + order totals 37,873);
**COGS rollup reconciliation** to the authoritative order fact (gap
1.82e-12) plus frozen COGS total; baseline reconciliation (contrib
565,116.9418 / freight 238,173.79); variance reconciliation with freight
variance exactly 0; TOTAL reconciliation; metadata/N-A completeness;
frozen-input hash integrity. Fail-loud abort gates (unrecorded by design)
cover out-of-range rates, missing inputs, shape mismatches, and any
reconciliation breach. Verified result at rate 0.10: baseline contribution
565,116.94 → hypothetical 660,523.18 (variance +95,406.24, +1.03pp) —
arithmetic consequences of the stated rate, nothing more.

## 6. Invalid-input behavior

`--rate 0.95` fails loudly (`VALIDATION FAILED [rate-bounds]`) in argument
parsing, before any file I/O: no CSV created, no partial-subset output, no
clipping, extrapolation, correction, or silent exclusion — the invalid
scenario is rejected as a whole, with offending values reported in the
failure diagnostic. Verified by probe.

## 7. Determinism evidence

Consecutive `--rate 0.10` runs produce byte-identical artifacts
(SHA-256-compared): CSV
`6771a5f2ec4eb1584a7965768766e329c4e80f1b3ae805992c9ff65a7b9da2d1`;
quality JSON
`4e3c4d8a9e3a8b127ee1f4522f505cc9bafaa2682173712d68fc84915855047b`.
No timestamps, no randomness; sorted band keys; versioned constants.

## 8. Frozen-file integrity evidence

SHA-256 recomputed and identical to freeze records; script asserts
byte-identical inputs before/after every run:

- `data/processed/fact_sales_cogs.csv`
  `4d8de717486b323ffb656d13c94fd6bd94f8e61d1a93ea339a602ab5303b9988`
- `data/processed/fact_margin_map_phase2.csv`
  `4c471feeda642e5ecbd2263782b4fc0f1655962f6c6488bdfe47886df2f01cb1`
- `data/processed/order_margin_map_phase2.csv`
  `ae6c349c9995747f2fef91cf1db6b940a73d99d6b2fede5ff3dff918f429d267`

Implementation script hash (corrected C1–C4 version):
`295e17776fb034cc6c69c5de79923c725714e8afda917ac151b7ecf8e7b3de50`.

## 9. Known limitations

Hypothetical gross margins are constant by COGS construction (disclosed
on-output via `cogs_method`); single rate (0.10) and universal scope only;
`low_sample_flag` thresholds carried provisionally from Phase 3B;
`demand_response_view` and `fixed_unit_cost_view` unavailable by design;
freight methodology caveat carried from Phase 2; outputs are ignored
reproducible artifacts, not committed tables.

## 10. Explicitly deferred scope

Discount increase/decrease scenarios; relative discount changes; Segment ×
Discount Band reporting; customer reporting; category- and
product-specific scenarios; demand response and elasticity; forecasting;
optimization; causal analysis; dashboards and Power BI; return-processing
costs; support costs; fixed-unit-cost comparator. Deferred items are not
implemented, partially supported, or represented as available.

## 11. Reproducibility command

From the project root, on frozen inputs:

```text
python src/data/build_phase4b_scenarios.py --rate 0.10
```

Expected: 7 band rows → `data/processed/phase4b_scenario_uniform_0.10.csv`
plus `data/processed/phase4b_scenario_quality.json`, 15/15 checks PASS,
byte-identical reruns. Any other rate within [0.00, 0.80] runs the same
code path with its own recorded metadata; any rate outside fails loudly
with no output.

## 12. Freeze status

**First slice COMPLETE AND VERIFIED — ready to freeze** (see
`docs/PHASE_4B_FREEZE.md`). No further slice begins under this record.
