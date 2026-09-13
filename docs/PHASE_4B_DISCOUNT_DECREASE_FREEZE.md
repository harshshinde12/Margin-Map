# Phase 4B Discount Decrease Freeze

## 1. Freeze status

`FROZEN — APPROVED`

## 2. Scope frozen

- Uniform discount decrease scenario applied to all valid lines (9,994 lines; 5,009 orders).
- Decimal-scale percentage-point input (`--decrease-pp`; `0.05` means a decrease of 5 percentage points; display-scale values such as `5` are rejected).
- Line-level hypothetical calculations with `hypothetical_discount = round6(round6(observed_discount) - decrease)`, bounds `[0.00, 0.80]`, fail-loud whole-run rejection, no clipping, no silent exclusion.
- Bottom-up order aggregation using authoritative order freight only.
- Baseline Order × Discount Band reporting on the ORDER basis (B0–B5 plus TOTAL; baseline bands only, never re-banded).
- Constant observed quantity (total 37,873).
- Frozen revenue-based modeled-COGS percentage (baseline identity asserted; hypothetical COGS from hypothetical net revenue).
- Observed freight pass-through with ambiguous-pair NULL/flag preservation (2 lines, `US-2014-150119`; 25.05 pair total via order aggregation only).
- Return/support OFF.
- Hypothetical arithmetic sensitivity only: not a forecast, not a demand statement, not evidence about what would have sold, not a causal estimate, not a pricing recommendation.

## 3. Implementation

- Implementation path: `src/data/build_phase4b_decrease_scenarios.py` (standalone; 636 lines).
- Design document: `docs/PHASE_4B_DESIGN_DISCOUNT_DECREASE.md` (§§1–25).
- Contract documents: `docs/PHASE_4B_IMPLEMENTATION_CONTRACT.md` (§§1–10), `docs/PHASE_4B_DECISION_LOG.md` (Gates 1–10), frozen Phase 4A architecture.
- Relevant source scripts: `src/data/build_phase4b_scenarios.py` (frozen uniform replacement), `src/data/build_phase4b_increase_scenarios.py` (frozen discount increase) — both inspected for pattern comparison only.
- Confirmation that the implementation is standalone: the decrease script imports nothing from the uniform-replacement or increase scripts, executes neither, and reuses frozen idioms (gross reconstruction, WAD dual-form check, `assign_band` boundaries, `fail()` + `sha256()` + quality-JSON pattern, authoritative order join) by copy only.
- Confirmation that existing generators were not modified: uniform script hash `295e17776fb034cc6c69c5de79923c725714e8afda917ac151b7ecf8e7b3de50` matches `docs/PHASE_4B_FREEZE.md`; increase script hash `20b71d70e2e6ea0fcfe156eee065cb9099858c2e8010d4a09c53586038f9b0bc` unchanged with a clean working tree; `git status --short` showed no modifications to either file.

## 4. Validation evidence

- Total checks: 22.
- Passed checks: 22.
- Failed checks: 0.
- All check identifiers: `decrease-exists`, `decrease-sign`, `decrease-bounds`, `quarantine`, `inputs`, `scenarios-off`, `discount-range`, `ambiguity`, `discount-bounds-per-line`, `no-silent-exclusion`, `hypo-revenue-dual-subtractive`, `hypo-lines`, `freight-passthrough`, `order-bands`, `quantity-constant`, `cogs-reconcile`, `frozen`, `variances`, `totals`, `metadata`, `metadata-decrease`, `frozen-inputs`. Identifiers are unique with zero duplicates; every record carries `id`, `description`, `expected`, `actual`, and `status` (`PASS`).
- Identity-case totals (`--decrease-pp 0.00`; `discount_decrease_pp_0.00`): baseline net revenue 2297200.8603 = hypothetical net revenue (variance 0.0); baseline contribution 565116.9418 = hypothetical contribution (variance 0.0); baseline COGS 1493910.1285 = hypothetical COGS; freight 238173.79 both sides with freight variance exactly 0; margin change 0.0pp.
- Quantity and row counts: 9,994 lines, 5,009 unique orders, quantity 37,873 at line, order, and TOTAL levels.
- Order counts: 5,009 orders joined one-to-one with the authoritative order fact.
- Band counts: `B0=2055 | B1=415 | B2=1634 | B3=278 | B4=274 | B5=353`, plus TOTAL; 6 band rows + TOTAL = 7 rows × 52 columns.
- Freight and null-freight evidence: `freight-passthrough` PASS (values bit-identical to load-time snapshot, flags unchanged, exactly 2 NULLs preserved); `ambiguity` PASS (2 lines NULL freight in `US-2014-150119`).
- COGS and contribution reconciliation: baseline COGS-percentage identity gap 4.55e-13; order COGS rollup gap 1.82e-12; gross dual gap 1.82e-12; baseline reconciled to Phase 2 facts within 0.05; variances reconciled both ways with freight variance 0.
- Decrease-specific validation evidence: `decrease-exists` / `decrease-sign` / `decrease-bounds` PASS for `0.0`; `discount-bounds-per-line` PASS with `min d'=0.000000`; `no-silent-exclusion` PASS with full scope; `hypo-revenue-dual-subtractive` PASS with gap 9.09e-13; `metadata-decrease` PASS with `discount_decrease` / `decrease_pp` / `discount_decrease_pp_0.00` / `stated_decrease_pp 0.0` on every row and consistent with the filename. Unsupported metrics explicitly `N/A` (`COMPARATOR_NOT_IN_INITIAL_BUILD`, `RESPONSE_NOT_ESTIMATED`).

## 5. Edge-case evidence

- `--decrease-pp 0.00`: success (identity scenario, 22/22 PASS, variances zero) per the committed quality JSON and CSV.
- `--decrease-pp 0.05`: intentional fail-loud behavior. Code path `discount-bounds-per-line` fails the whole run before any output is written, reporting violating counts, minimum `d'`, and sample `row_id`s. The implementation report records 4,798 violating lines with minimum `d'=-0.050000` from observed zero-discount mass. No `phase4b_scenario_decrease_0.05` CSV or quality JSON exists on disk.
- Negative input: fails via `decrease-sign` as the wrong slice type (a negative decrement is the frozen increase type).
- Display-scale input `5`: fails via `decrease-bounds` with a decimal-scale hint (`use decimal, e.g. 0.05`).
- Non-numeric input: fails at argument parsing before any file I/O.
- Excessive input (e.g. `0.95`): fails via `decrease-bounds`.
- Missing input: fails at argument parsing (required argument) before any file I/O.
- Invalid-source-value behavior: inherited fail-loud gates (`discount-range`, input shapes, quarantine, reconciliation) abort before any output is treated as valid; frozen inputs contain no such values.
- Null-freight preservation: 2 NULLs preserved and validated; no imputation path exists in the code.
- Positive decreases may fail when observed zero-discount lines would violate the lower bound, and this is intentional fail-loud behavior, not an implementation defect. Failed runs leave no valid scenario outputs behind: only `phase4b_scenario_decrease_0.00` artifacts exist.

## 6. Determinism evidence

- Repeated-run result: the implementation report records two consecutive `--decrease-pp 0.00` runs producing byte-identical artifacts. This audit did not re-execute the implementation (audit boundary); it verified the committed artifacts instead.
- CSV hash: `data/processed/phase4b_scenario_decrease_0.00.csv` = `8089d3b22c4e82cd2c31ba59b2fb1ababd91ccf5816dda419e4f4ea3c359636d`, matching the `sha256` recorded in the quality JSON `outputs` block.
- Quality JSON hash: `data/processed/phase4b_scenario_decrease_0.00_quality.json` = `bbde89e48a1360e5e0f11c81ac05344fb4d1739993e8564f5886da18b31e107c`.
- Confirmation of no timestamps, randomness, or unstable ordering: the script contains no timestamp, random, datetime, UUID, or environment-specific logic; band keys are sorted deterministically (B0–B5, TOTAL); the quality JSON records input hashes and the output hash.

## 7. Frozen-artifact protection

- Frozen input hashes (verified, matching all prior freeze records): `fact_margin_map_phase2.csv` = `4c471feeda642e5ecbd2263782b4fc0f1655962f6c6488bdfe47886df2f01cb1`; `order_margin_map_phase2.csv` = `ae6c349c9995747f2fef91cf1db6b940a73d99d6b2fede5ff3dff918f429d267`; `fact_sales_cogs.csv` = `4d8de717486b323ffb656d13c94fd6bd94f8e61d1a93ea339a602ab5303b9988`.
- Frozen scenario hashes (verified unchanged): `phase4b_scenario_uniform_0.10.csv` = `6771a5f2ec4eb1584a7965768766e329c4e80f1b3ae805992c9ff65a7b9da2d1`; `phase4b_scenario_quality.json` = `4e3c4d8a9e3a8b127ee1f4522f505cc9baabc84915855047b` (shown here in lowercase as computed; matches the recorded value); `phase4b_scenario_increase_0.00.csv` = `10fb41f207c7cc011d3fbfe5bdbaec0bbfdc0be4e53cf39f3a0bf7ce087c9560`; `phase4b_scenario_increase_0.00_quality.json` = `52c9938394667dad4b8c29baefc282d84bb5f53450b1a9bb608dc559e4dcf7bf`.
- Existing script hashes: uniform generator `295e17776fb034cc6c69c5de79923c725714e8afda917ac151b7ecf8e7b3de50` (matches freeze record); increase generator `20b71d70e2e6ea0fcfe156eee065cb9099858c2e8010d4a09c53586038f9b0bc`; decrease generator `e6e841ee8926979a3f596fb4ddD7ed0a2c27e0d38c10b37aadd9e4fee3f47b7c` (new slice, independently hashed; shown here in the computed case).
- Confirmation that no frozen artifact changed: `git status --short` is clean (no modifications); quality JSON input hashes match the frozen files; the decrease run asserts byte-identical frozen inputs before and after.

## 8. Git and artifact policy

- Decrease CSV path: `data/processed/phase4b_scenario_decrease_0.00.csv`.
- Decrease quality JSON path: `data/processed/phase4b_scenario_decrease_0.00_quality.json`.
- CSV ignored status: ignored under `.gitignore:14` (`*.csv`); confirmed via `git check-ignore -v`.
- Quality JSON committable status: not ignored and tracked (present in `git ls-files`); it is the committable validation evidence.
- Confirmation that no frozen quality JSON was overwritten: `phase4b_scenario_quality.json` and `phase4b_scenario_increase_0.00_quality.json` hashes are unchanged; the suffixed decrease filename keeps namespaces separate.
- Confirmation that the decrease namespace is separate: `phase4b_scenario_decrease_*` collides with neither `phase4b_scenario_uniform_*` nor `phase4b_scenario_increase_*`; scenario identifiers `discount_decrease_pp_*` are distinct from `uniform_replacement` and `discount_increase`.
- Implementation and quality JSON are committed (`git ls-files` lists both); the CSV remains ignored; no freeze document existed before this task.

## 9. Scope exclusions

The slice does not include forecasting, optimization, recommendations, predictive modeling, operational decisioning, customer targeting, external data, dashboards, return/support adjustments, or schema changes. The implementation and output metadata were scanned: the only matches for forecast, optimization, recommendation, prediction, targeting, deployment, dashboard, or external-data terms are exclusionary statements (e.g. hypothetical sensitivity, not a forecast). No return/support rate layer, no fixed-unit-cost comparator, and no quarantined-Profit usage exist.

## 10. Final freeze decision

`The Discount Decrease scenario slice is frozen and approved for the defined Phase 4B analytical sensitivity scope. This freeze does not authorize forecasting, optimization, operational decisioning, or production deployment.`
