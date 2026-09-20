# P2 Remediation Report — Float-Join Hardening + Forensic P2 Audit

## 1. Executive summary

Float join HARDENED (no stable replacement key exists — proven). Of P2-01…P2-11:
2 REAL bugs fixed (sparsity theater, obscure fillna), 4 defensive hardenings
(normalized join, rate-precision guards ×3, sensitivity no-clip assertion,
min_count already applied in CTS pass), 1 documentation typo fixed (AO-04
B1/B2), 5 documented-no-change (separator, NULL guards, crosswalk, freeze,
ties, exact-float). No analytical value changed except AO-06 mirror text
(descriptions). NO COMMIT, NO PUSH, Power BI untouched.

## 2. Float-join finding

Freight join (`build_phase2_fact.py`) merged on raw-float composite signature
(Customer/Product/Sales/Quantity/Discount/ShipMode/City/State): 9,994/9,994
exact matches, dual-form reconciliation, fail-loud gates. Correct outputs,
brittle mechanism (binary float representation).

## 3. Stable-key investigation

- D1-US Row ID: unique but unshared numbering vs fact row_id — unusable.
- Order+Product: 8 collisions on BOTH sides — many-to-many, unsafe alone.
- Order years shifted (+3 D1→fact; +9 xls→fact); suffix sets unequal.
- The exact ambiguous pair (rows 3406/3407) is indistinguishable on ALL shared
  attributes — no key, float or stable, can separate it. Floats (Sales,
  Discount, Quantity) are NECESSARY disambiguators for 7 split pairs.
- Conclusion: NO stable key improves on the signature. Documented, not invented.

## 4. Float-join remediation

`_norm_sig()`: Sales→cents (round 2), Discount→6dp, Quantity→int64, strings
stripped, NaN-after-normalization fails loudly. Same production key,
normalized; all cardinality/total gates retained. Output byte-identical
(`4038684d…` before/after).

## 5. Separator collision audit

ISSUE: `analytical_product_key` uses ` || `. STATUS: DOCUMENTED — prior-pass
fail-loud guard + zero `||` (and zero `|`) in all 9,994 ids/names. EVIDENCE:
audit script counts 0/0. No change.

## 6. Sensitivity clipping audit

ISSUE: `.clip(0,100)` could silently redefine scenarios. STATUS: FIXED —
explicit no-op assertion added (benchmarks 20–45, never clips; future edge
benchmark fails loudly instead of clipping). VALIDATION: pipeline PASS.

## 7. NULL guard audit

ISSUE: guards that cannot trigger. STATUS: DOCUMENTED — `np.where(x==0,nan)`
+ fail-on-NaN correctly fail-loud on future bad input (no silent pass of bad
data; just ungraceful). No change: altering abort semantics risks masking.

## 8. Crosswalk audit

ISSUE: set logic direction/duplicates/UNKNOWN. STATUS: PASS — candidate
Returns ⊆ candidate Orders verified; IDs unique; per-row +9yr + line-set;
UNKNOWN (`CA-2015-102015`) verified absent from YES set (not absorbed).
EVIDENCE: `p2_unk.py` output. No change.

## 9. Filename audit

ISSUE: `f"{rate:.2f}"` truncation collisions (0.105→0.10). STATUS: FIXED —
precision guards in all three 4B scripts (non-2dp-exact rates fail loudly).
VALIDATION: `--rate 0.105` fails `[rate-precision]`; shipped 0.10/0.20/0.00 pass.

## 10. Float validation audit

ISSUE: exact `==`/`!=` on floats. STATUS: DOCUMENTED — currency uses TOL/
VAR_TOL; identity zeros are deterministic same-path computations (exact
appropriate); int/string equality untouched. No change.

## 11. Freeze audit

ISSUE: brittle fingerprinting. STATUS: DOCUMENTED — content SHA-256 (meaningful),
fixed shapes intentional, per-rate quality JSONs (new) preserve custody.
No weakening. No change.

## 12. Sparsity audit

ISSUE: both-branch-PASS gate (theater). STATUS: FIXED — replaced with boolean/
non-null validity gate (capable of failing) + informational fraction record.
EVIDENCE: code diff; pipeline PASS.

## 13. fillna/default audit

ISSUE: `fillna(1)` obscure. STATUS: FIXED — explicit `(s.notna() & (s < 0))`;
proven equivalent (synthetic test 1 == 1); NULLs correctly excluded from
negative counts.

## 14. Region tie-break audit

ISSUE: `idxmax` first-max on ties. STATUS: DOCUMENTED — zero tied customers
in data (0 ties / 766 multi-region); groupby-sorted deterministic. No change.

## 15. AO-04 documentation audit

ISSUE: "B1 24 largest share" vs stored B1 3 / B2 24. STATUS: FIXED — doc
corrected with correction note; implementation untouched (was already correct).

## 16. Issues classified by severity

- REAL bugs (fixed): sparsity theater (P3), AO-04 typo (P4 doc). fillna(1)
  reclassified hardening (equivalent, clearer).
- Material methodology: NONE.
- Defensive hardening: float normalization, 3× precision guards, sensitivity
  assertion, min_count (CTS pass).
- Documentation-only: separator, NULL guards, crosswalk, freeze, ties,
  exact-float policy.

## 17. Fixes performed

1. `build_phase2_fact.py`: `_norm_sig()` normalization.
2. `build_phase3b_discount_analysis.py`: sparsity gate + fillna explicit.
3. `build_phase4b_{scenarios,increase,decrease}_scenarios.py`: precision guards.
4. `apply_modeled_cogs.py`: sensitivity no-clip assertion.
5. `PHASE_4C_AO-04_FREEZE.md`: B1/B2 correction note.
6. `backend/tests/test_variance.py`: uniform020 band-sum test.

## 18. Before/after metrics

- fact_margin_map hash identical (`4038684d…`); order fact identical;
  AO-01/02/03/05 values identical; AO-06 shifts only in mirrored phase3b
  record text (sparsity-gate descriptions); DB now `0aa7114c…`
  (17,293,312 bytes; 61,211 rows; counts 20/238/140/560/60108/145).
  Row-count growth vs the original 61,016-row baseline comes from the prior
  Scenario pass (+35/+140/+20 rows), not this pass — this pass changes only
  mirrored description text.
- Discount neg-line counts identical (equivalence proven).

## 19. Regression tests

Backend 56/56 (55 + 1 band-sum test); frontend 23/23; lint clean; build
clean; SQL 13/13; browser 7 routes + 0.20 check zero pageerrors.

## 20. Remaining limitations

Float signature remains (normalized, documented); exact-identity zeros rely
on deterministic paths; freeze shapes intentionally rigid; ties untested in
production data; carrier methodology unverified (prior).

## 21. Files changed

Upstream: `build_phase2_fact.py`, `build_phase3b_discount_analysis.py`,
`build_phase4b_{scenarios,increase,decrease}_scenarios.py`,
`apply_modeled_cogs.py`; docs: `PHASE_4C_AO-04_FREEZE.md`,
`docs/P2_REMEDIATION_REPORT.md` (new); tests: `test_variance.py`.
Power BI: untouched (53 churn preserved).

## 22. Reproducibility instructions

Rerun chain from `build_phase2_fact.py` through Phase 4C → `load_data.py` →
`validate_sql_outputs.py` → `pytest` → `check_cogs_independence.py`.
Negative controls: `--rate 0.105` must fail `[rate-precision]`.
