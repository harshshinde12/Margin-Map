# Scenario Model Remediation

## 1. Existing Problem

Universal pp-shift scenarios (increase/decrease) could only ever ship as
±0.00 identity controls: any nonzero Δ breaches the fail-loud per-line
bounds on the observed masses at 0.00 (4,798 lines) and 0.80 (300 lines).
The system therefore offered 1 genuine scenario + 2 integrity checks while
appearing to cover the shift space (ISS-02/L-02).

## 2. Current Mathematical Behavior

- Replacement: `d' = stated rate`; `hypo_net = gross × (1−d')`,
  `gross = sales/(1−d)`; `hypo_cogs = hypo_net × frozen pct`;
  `hypo_cts` = authoritative order freight passthrough; returns/support OFF;
  `variance = hypo − base`; bands = BASELINE order-WAD bands (never re-banded).
- Increase/decrease: `d' = round6(d) ± Δ`, bounds [0.00, 0.80] fail-loud per
  line (no clipping/drops/partial runs).

## 3. Discount Distribution

12 unique values; 0.00: 4,798; 0.20: 3,657; 0.10: 94; 0.15: 52; 0.30: 227;
0.32: 27; 0.40: 206; 0.45: 11; 0.50: 66; 0.60: 138; 0.70: 418; 0.80: 300.
Min 0.0, max 0.8, mean 0.1562, median 0.20.

## 4. Why ±0.00 Occurs

Answer C+D (mathematical consequence + definition problem), NOT a UI bug:
any Δ>0 breaches bounds (up: 300 lines; down: 4,798 lines) and the whole run
fails by design. Only Δ=0.00 passes both slices. Independently reproduced
(§9 table below).

## 5. Candidate Scenario Designs

| Design | Affected | Clipped/breached | Verdict |
|---|---|---|---|
| A. Universal pp shift | 9,994 | 300 up / 4,798 down → unshippable | REJECTED as genuine content (kept as identity controls) |
| B. Relative change | 5,196 (+10%) | 300 breach; 0-mass unchanged | REJECTED (breach + weak interpretability) |
| C. Band migration | unknown | behavioral model needed | REJECTED (fabrication risk) |
| D. Cap/floor-aware pp | all | 300/4,798 silently redefined; floor ≈ identity | REJECTED (violates no-clipping contract) |
| E. Band-specific change | unknown | same as C + complexity | REJECTED |
| F. Replacement | 9,900 (0.10) / 6,337 (0.20) | 0 | SELECTED |

## 6. Selected Design

Add second replacement scenario `uniform_replace_0.20` (median observed
discount, most common nonzero mass). The shipped pair is a lower-rate (0.10,
below-mean) + median (0.20) replacement pair bracketing the mean observed
discount (0.1562) — it is NOT two-sided around the median (both rates are at
or below it). No symmetric 0.30 scenario is added: 0.30 has no independent
anchor (not mean/median/mode) and symmetry alone is not a justification.
Identity controls retained as integrity checks with honest labels.

## 7. Scenario Contract

| Field | uniform_replace_0.20 |
|---|---|
| scenario_id | uniform_replace_0.20 |
| scenario_name | Uniform 20% replacement (median observed discount) |
| scenario_type | uniform_replacement |
| assumption | every line discounted at 20% |
| assumption_unit | rate (decimal fraction) |
| baseline_definition | observed TOTAL at actual discounts |
| hypothetical_definition | identical scope at d'=0.20, qty constant, frozen COGS pct, freight passthrough, returns/support OFF |
| bounds | d' ∈ [0.00, 0.80]; per-line fail-loud |
| affected_population | 6,337/9,994 lines change (3,657 already at 0.20); 0 clipped |
| interpretation | ILLUSTRATIVE sensitivity, not forecast/pricing guidance |
| caveat | constant-quantity, no demand response; COGS rate frozen |

## 8. Assumptions

Constant observed quantity; frozen modeled-COGS pct applied to hypo revenue;
observed freight passthrough (NULL preserved on 2 ambiguous lines);
returns/support OFF; baseline bands retained.

## 9. Mathematical Formulas

Per §2. Independently recomputed: hypo 560,667.96392, variance
−4,448.97791, bands sum to TOTAL (gap 0.0), baselines identical across all 4
instances, freight variance exactly 0.

## 10. Baseline Preservation

Verified: baseline blocks byte-identical across all 4 scenario instances;
frozen totals (rev/cogs/freight/contrib) match.

## 11. Band Interaction

BASELINE bands by explicit design (B0 cohort stays identifiable); documented
in contract and AO limitation fields. No silent re-banding.

## 12. COGS Interaction

COGS scales with hypo revenue at the frozen rate (methodology-supported);
assumptions unchanged; no COGS re-estimation from discounts.

## 13. Return Interaction

Unchanged: flag-only semantics preserved; no refund model introduced.

## 14. AO-03 Impact

105 → 140 rows (+35 uniform020 block rows); N/A 6 → 8 (+2 unlicensed views).

## 15. AO-04 Impact

420 → 560 rows (+140 band rows); N/A 42 → 56; band economics sensible
(B0/B1/B2 negative, B3+ positive — raising discounts to 20% hurts
low-discount bands, helps high-discount bands).

## 16. SQLite Impact

Rebuilt: 61,211 rows; counts 20/238/140/560/60108/145; validation 13/13 PASS.

## 17. API Impact

Contract unchanged (generic scenario_id filter already supported); 2 new
regression tests (uniform020 values, baseline identity).

## 18. React Impact

Scenario lists extended in Scenarios/Variance with data-anchored label;
single-value select discipline retained; no hard-coded values beyond the
source-driven option lists.

## 19. Power BI Impact

No PBIP edits (53 churn files untouched). Existing uniform_0.10 measure
unaffected; new scenario appears in data-driven slicers automatically;
dedicated 0.20 card left for a future Desktop pass (documented).

## 20. Validation

Pipeline fail-loud gates PASS (15/15 new instance); variance/margin
reconciliation ±1e-9; band-TOTAL reconciliation gap 0.0; backend 49/49;
frontend 23/23; lint/build clean; SQL 13/13.

## 21. Limitations

Replacement scenarios assume constant quantity (no elasticity); identity
controls remain non-economic by design; nonzero pp-shifts still unshippable
under the no-clipping contract (documented, not patched); Power BI has no
dedicated 0.20 card yet.

## 22. Reproducibility

`build_phase4b_scenarios.py --rate {0.10,0.20}` (per-rate quality JSONs) →
`build_phase4c_{scenario_comparison,band_variance,quality_summary}.py` →
`load_data.py` → `validate_sql_outputs.py`. Deterministic, no manual edits.
