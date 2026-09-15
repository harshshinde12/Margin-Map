# Phase 6 SQL Data Layer Freeze — Read-Only SQLite Access to Frozen Phase 4C Outputs

`FROZEN — APPROVED`

## 1. Freeze Status

* Phase: Phase 6 SQL data layer (first working SQL access to frozen Phase 4C outputs).
* Status: `FROZEN — APPROVED`
* Formal audit completed with result PASS and no blocking issues.
* This document records the approved reference state and introduces no new analytical logic, calculation, scenario, forecast, or recommendation.

## 2. Objective

Provide a local, file-based, read-only SQL data layer over the six frozen Phase 4C analytical outputs (AO-01–AO-06) for the approved display phase, preserving every frozen value, grain, authority marker, standing label, N/A marker, and limitation exactly as stored. The layer performs no analysis of its own.

## 3. Approved Scope

* Six frozen AO CSVs loaded read-only into SQLite (20 + 238 + 105 + 420 + 60,108 + 125 = 61,016 rows).
* One table per output plus one thin ordered view per approved display use case.
* Chain-of-custody hash verification before loading; fail-loud validation with no partial writes.
* Explicitly not included: new metrics, recalculations, grain merging, filters beyond the approved scope, scenarios, forecasting, optimization, causal analysis, recommendations, dashboards, visuals, or any Power BI/backend/frontend work (none created: `powerbi/` holds only its placeholder).

## 4. Source Artifacts

| Artifact | Role | Integrity evidence |
| -------- | ---- | ------------------ |
| `phase4c_baseline_total.csv` (20 rows) | AO-01 source | bytes equal SHA-256 in `phase4c_baseline_total_quality.json` (18/18 PASS) |
| `phase4c_band_contribution.csv` (238 rows) | AO-02 source | bytes equal SHA-256 in `phase4c_band_contribution_quality.json` (17/17 PASS) |
| `phase4c_scenario_comparison_total.csv` (105 rows) | AO-03 source | bytes equal SHA-256 in `phase4c_scenario_comparison_total_quality.json` (19/19 PASS) |
| `phase4c_contribution_variance_by_band.csv` (420 rows) | AO-04 source | bytes equal SHA-256 in `phase4c_contribution_variance_by_band_quality.json` (21/21 PASS) |
| `phase4c_order_reading.csv` (60,108 rows) | AO-05 source | bytes equal SHA-256 in `phase4c_order_reading_quality.json` (17/17 PASS) |
| `phase4c_quality_summary.csv` (125 rows) | AO-06 source | bytes equal SHA-256 in `phase4c_quality_summary_quality.json` (9/9 PASS) |

All six source CSVs verified byte-identical to their quality-record hashes during audit (independently recomputed, all OK).

## 5. SQLite Architecture

* Technology: SQLite via Python's standard library (`sqlite3`; engine 3.50.4 at build); no server, credentials, or third-party database dependency.
* Location: `data/processed/marginmap.db`, alongside the frozen artifacts it mirrors.
* All columns TEXT: frozen strings (including empty N/A markers and flag text) preserved exactly with no type coercion.
* UNIQUE record identity per table, except `ao06_quality_summary`, which carries no UNIQUE constraint by design because its mirror rows inherit the frozen Phase 3B record's one reused check ID (`frozen` twice); fidelity there is enforced by exact multiset match instead of rewording frozen evidence.
* Database opened read-only (`mode=ro`) by the validator; the loader is the sole writer and only ever writes the new database file.

## 6. Tables and Views

* `ao01_baseline_total` — 20 rows; UNIQUE(metric_name).
* `ao02_band_contribution` — 238 rows; UNIQUE(basis, band, metric_name).
* `ao03_scenario_comparison` — 105 rows; UNIQUE(scenario_id, block, metric_name).
* `ao04_band_variance` — 420 rows; UNIQUE(scenario_id, band, block, metric_name).
* `ao05_order_reading` — 60,108 rows; UNIQUE(order_id, metric_name).
* `ao06_quality_summary` — 125 rows; no UNIQUE (documented above).
* Views (thin `SELECT * ... ORDER BY rowid` over each table, frozen file order preserved): `baseline_total`, `contribution_by_band`, `scenario_comparison_total`, `variance_by_band`, `order_reading`, `quality_summary` — each verified to return full base-table row coverage.

## 7. Loading Rules

`python sql/load_data.py [--processed-dir DIR] [--db PATH]`: asserts all six CSVs and quality JSONs exist; asserts every CSV's bytes equal its recorded hash and every recorded check PASS before loading; rejects ragged rows; asserts table columns equal CSV headers; rebuilds the database file fresh (prior file removed, never patched); inserts rows in frozen file order; creates views last; commits once. Any breach aborts before any database write.

## 8. Validation Evidence

`python sql/validate_sql_outputs.py` reports exactly 13/13 PASS: `db-exists`, `tables-exist` (6/6), `views-exist` (6/6 with full row coverage), `columns-match` (6/6 headers), `row-counts` (20/238/105/420/60108/125 in database and CSVs), `content-equal` (all 61,016 rows identical to frozen CSVs), `spot-values` (AO-01 contribution `565116.9418299999`; AO-03 uniform variance `95406.2413300001`; AO-04 B5 variance `45401.369600000005`; AO-06 verdict `ALL_SOURCES_ELIGIBLE`), `na-preserved` (14/6/42 empty N/A rows), `status-labels` (`OBSERVED BASELINE` / `HYPOTHETICAL_ARITHMETIC_SENSITIVITY` separation), `mirror-fidelity` (75 upstream checks mirrored verbatim in order), `order-coverage` (5,009 distinct orders), `band-coverage` (B0–B5 + TOTAL), `frozen-unchanged` (6/6 AO CSVs byte-identical to quality records). One documentation nit found in audit: the validator docstring lists 12 of the 13 check names (omits `mirror-fidelity`, which is implemented and passing) — recorded here as a non-blocking note, not repaired, to keep the frozen implementation byte-identical.

## 9. Reconciliation and Source Fidelity

* Row counts per table equal the frozen CSV data-row counts exactly (20/238/105/420/60108/125).
* Full content equality verified cell-for-cell (`ORDER BY rowid` vs CSV rows): all 61,016 rows identical.
* Spot values verified against frozen figures; N/A empty-string counts verified (14/6/42); order/band coverage and status separation verified; all six AO CSVs re-hashed identical to their quality records during audit.

## 10. N/A and Grain Handling

* Empty-string N/A markers preserved exactly (never NULL-filled, never zero-filled) with their reason columns intact: 14 rows (AO-02), 6 rows (AO-03), 42 rows (AO-04).
* Grain and authority preserved per row: TOTAL, Overall × band with ORDER/LINE basis markers, per-instance blocks, order grain, and artifact gate — separate rows/blocks exactly as frozen, with authority and limitation text intact. No grain merging occurs anywhere in schema, loader, views, or validator.

## 11. Determinism and Failure Behavior

* Determinism (implementation-reported and code-supported): fixed file/table/row ordering, `repr()`-stable loader formatting, no timestamps, no randomness, no environment-dependent values; consecutive rebuilds byte-identical (verified during implementation: `b75c75f3…` twice). The audit did not re-execute the loader (read-only boundary); determinism is recorded as implementation-reported evidence supported by code inspection.
* Failure behavior (implementation-reported and code-supported): missing input fails `[inputs-exist]` with nothing written; tampered content fails `[quality-chain]` with nothing written; schema mismatch fails `[schema-match]`; any validation failure exits non-zero before writes. The audit verified these gates by code inspection, not by rerun.

## 12. Artifact Protection

* All six AO CSVs and six quality JSONs verified byte-identical to their records during audit; no frozen AO source file modified (read-only opens throughout; the sole writer targets only the new database file).
* No AO implementation script, freeze document, design document, upstream artifact, or Git configuration modified, except the single `.gitignore` rule below.
* `.gitignore` correction applied in this freeze task: added exactly `*.db` (line 16, data-artifact group); no other ignore rule touched. `data/processed/marginmap.db` is now ignored (verified via `git check-ignore`).
* No Power BI files, dashboards, visuals, or frontend/backend files created (`powerbi/` holds only its placeholder); no analytical calculations added.

## 13. Limitations and Deferred Work

* The layer mirrors frozen values; it performs no analysis and licenses no behavioral, predictive, or causal reading.
* Numerics are stored as exact frozen text; downstream queries must cast explicitly for arithmetic.
* AO-06 upstream checks are mirrored, not re-executed, per the frozen evidence design.
* Same-machine consecutive rebuilds are byte-identical; cross-machine/version byte-identity is not asserted.
* Deferred: all Power BI display implementation under the approved Phase 5 scope (authorized separately; not started).

## 14. Change Boundary

This freeze does not include: new metrics or recalculations; grain merging or re-banding; new scenarios, dimensions, or scenario detail; dashboards, visuals, or Power BI work; recommendations, optimization, forecasting, or causal claims; changes to any AO implementation, output, quality JSON, or freeze record; changes to upstream artifacts; or any modification beyond `sql/schema.sql`, `sql/views.sql`, `sql/load_data.py`, `sql/validate_sql_outputs.py`, `docs/PHASE_6_SQL_DATA_LAYER.md`, the `.gitignore` `*.db` rule, and this document.

## 15. Freeze Decision

* Phase 6 SQL data layer is approved for freeze: implementation, validation (13/13), and formal audit (PASS, no blocking issues) all hold.
* The approved reference state is the five layer files plus this record; the database remains an ignored, locally rebuildable artifact.
* Any future change must be separately scoped, validated, and documented.
