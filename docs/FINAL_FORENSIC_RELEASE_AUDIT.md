# Final Forensic Release Audit — Margin Map

## 1. Executive conclusion

All six frozen remediations verified intact; full sweep finds ZERO P0/P1 and
ZERO open P2 — every prior P2 is closed (fixed, hardened, or documented with
proof). Methodology is defensible end-to-end with explicitly documented
limits. Recommendation: READY_WITH_DOCUMENTED_LIMITATIONS. NO COMMIT, NO PUSH.

## 2. Full remediation history

1. Postal hardening + display honesty (WAD/labels/filters/N/A/Quality) + docs.
2. P0 COGS: independence proof + assumption schema + guards (values unchanged).
3. P1 Returns: OUTCOME C flag-only + caveat + tests (values unchanged).
4. P1 Scenarios: uniform_0.20 added (AO-03 140, AO-04 560, AO-06 145).
5. P1 CTS/Freight: reconciliation exact; min_count hardening (byte-identical).
6. Float-join hardened (normalized signature, byte-identical) + P2 audit
   (sparsity gate, fillna explicit, precision guards, sensitivity assertion,
   AO-04 typo fix).

## 3. Remaining limitations

Modeled-COGS assumption-restatement; fallback granularity; ±5pp narrowness;
returns flag-only; constant-quantity scenarios; pp-shifts unshippable;
float-signature (normalized) brittleness; carrier methodology unverified;
touch/SR/multi-browser gaps; ~672KB bundle. All disclosed in report docs.

## 4. Data lineage

archive.zip (9,994-line US Superstore slice, latin1) → fact_sales (postal
fix) → dim_product (1,894) + benchmarks (17 external) → fact_sales_cogs →
phase2 line/order (+D1-US freight 238,173.79, Returns flag 296+1) → 2C/3B →
4B (0.10/0.20/±0.00) → 4C AOs (20/238/140/560/60108/145) → SQLite → API →
React → Power BI (CSV-partitioned, absolute paths).

## 5. Analytical methodology

SUM/SUM margins (never averaged); WAD gross-weighted; bands B0–B5+TOTAL
inclusive-upper; baseline bands frozen in scenarios; NULL-propagating CTS;
fail-loud gates at every layer; no manual output patching.

## 6. COGS methodology

External gross-margin benchmarks (Damodaran/MillerKnoll/HNI/Logitech/Xerox/
Best Buy/CSIMarket, 2026-09-11); `modeled_cogs = net × (100−benchmark)/100`;
∂COGS/∂Profit = 0 (checker PASS); schema carries rate/method/year/status;
assumption-restatement disclosed.

## 7. Returns methodology

Order-level flag only (296 YES / 4,712 NOT_RETURNED / 1 UNKNOWN); values
retained; no refund leg (no data); freight retained as observed; handling OFF.

## 8. Scenario methodology

Replacement only as genuine content (0.10 below-mean + 0.20 median pair
bracketing mean 0.1562); ±0.00 identity controls as integrity checks;
constant qty, frozen COGS pct, freight passthrough, baseline immutable +
identical, variance = hypo − base.

## 9. CTS/freight methodology

OBSERVED line-grain Shipping Cost (D1-US), normalized-signature join
(9,994/9,994), ambiguous pair held at order, `freight_order_total`
informational (never summed; only deduped consumer), CTS = freight + OFF/0.

## 10. API architecture

Read-only GET (`mode=ro` + `query_only`), allowlisted columns/filters,
string passthrough (verbatim precision), page-scoped orders envelope
(documented), CORS allowlist. No analytical logic in transport.

## 11. Frontend architecture

6 pages + 404; unit-aware formatting (DEC 4dp, WAD labeled); N/A preserved
in tables, excluded from charts; fixed ORDER/LINE basis; single-value
scenario selects; derived Quality badge; Escape drawer; skeletons/alerts/
empty states; aria-live filters/pager.

## 12. Power BI architecture (static audit, untouched)

Tracked PBIP: auto metric_name relationship (cross-grain filter RISK —
report uses visual-level filters; no mis-filtering observed in QA);
card `Sum(metric_value)` gated by single-metric filters (valid as built;
new metrics/scenarios would need visual-filter review); AO05 stored as
string/none (safe); measures scope to uniform_0.10 headline (new 0.20 flows
via slicers; dedicated card deferred); absolute `File.Contents` CSV paths
(repro limitation — fresh clones must rerun `pageN_build.py`); N/A relies on
text-typed CSVs (valid today). Verdict: REVIEW_REQUIRED only for future
edits; NO current defect breaks the shipped report; 53 churn files preserved.

## 13. QA results

Backend 56/56 (41 baseline + 3 COGS + 3 returns + 6 CTS + 2 scenario + 1
variance-band). Frontend 23/23. Lint clean. Build clean. SQL 13/13
(20/238/140/560/60108/145; mirror 90; N/A 14/8/56). Independence checker
PASS. Negative controls proven (`--rate 0.105` fails; fillna equivalence).

## 14. Browser results

Real Chrome/Blink: 5 viewports × 8 routes, zero pageerrors, zero overflow;
scenario 0.20 selectable; WAD 0.1979; identity labels; Escape drawer;
filters/pagination/states verified.

## 15. Security results

Read-only DB (mode=ro); allowlisted SQL columns/filters; no POST/PUT/DELETE;
CORS origin allowlist; no secrets tracked (only `.env.example` local URL);
no new endpoints added in any remediation. Carried-forward PASS.

## 16. Reconciliation results

Revenue 2,297,200.86; COGS 1,493,910.13; profit 803,290.73; margin 34.97%;
contribution 565,116.94; freight 238,173.79 (7-layer Δ=0.00); uniform_0.20
hypo 560,667.96 / variance −4,448.98; AO-04 bands sum gap 0.0; DB
`0aa7114c…` 17,293,312 bytes. All independently recomputed, none hard-coded
into calculations.

## 17. Reproducibility

backend/README + frontend/README give relative-path startup (uvicorn from
`backend/`, `npm install/dev/test/build`); pipeline reruns via documented
`src/data/*.py` order; `load_data.py` + validator rebuild DB; PBIP needs
Desktop + `pageN_build.py` rerun on fresh clones (absolute paths). No AI
references in user docs. Root README lacks a quickstart block (P4 note).

## 18. Git scope

96 changed + untracked reports: (A) this-pass: AO-04 typo doc line (current
audit changed nothing else — all items already fixed); (B) prior
remediations: pipeline scripts, frontend, tests, validators, 5 remediation
reports; (C) 53 pre-existing PBI churn, untouched; (D) ignored CSVs/DB/dist/
caches + tracked quality-JSON hash records (legitimate rebuild artifacts).
No unexplained source changes. Raw `archive.zip` untouched.

## 19. Known limitations

See §3 + per-report §18/§20/§25 sections. Nothing hidden; uncertainty
explicit (bands next to headlines, OFF≠zero, flag-only, hypothetical≠forecast).

## 20. Release recommendation

READY_WITH_DOCUMENTED_LIMITATIONS. Ship the code + docs boundary; Power BI
needs no change for this release; revisit only if AO grains change.

## Triage appendix

| ID | Finding | Severity | Evidence | Action | Status |
|---|---|---|---|---|---|
| F-01..R-08, D-01 (prior) | postal/validation/display/docs | P2–P3 | prior reports | fixed | CLOSED |
| L-01..L-05 | COGS/returns/scenario/CTS structure | P0–P2 limits | proofs | documented + guarded | CLOSED AS LIMIT |
| P2-01/03/04/06/07/10 | separator/NULL/crosswalk/freeze/ties/floats | P3 | zero-occurrence proofs | documented | CLOSED |
| P2-02/05/09 | clip/filename/fillna | P3 | code | hardened | CLOSED |
| P2-08/P2-11 | sparsity theater/AO-04 typo | P3/P4 | code/docs | fixed | CLOSED |
| PBI relationship/paths | cross-grain/auto-paths | P3 | static TMDL/M | review-only, untouched | DOCUMENTED |
| Root README quickstart | missing block | P4 | README grep | none (note) | OPEN P4 |

P0/P1 open: 0. P2 open: 0. P3/P4 open: documented limits + 1 P4 note.
