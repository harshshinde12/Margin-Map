# Phase 6 SQL Data Layer — Read-Only Access to Frozen Phase 4C Outputs

## 1. SQL Technology Decision

* Database technology: **SQLite** (via Python's standard-library `sqlite3`; engine SQLite 3.50.4 in the build environment; no third-party database dependency).
* Database location: `data/processed/marginmap.db` (alongside the frozen processed artifacts it mirrors).
* Why it is appropriate: the display layer needs local, file-based, read-only access to six small frozen tables (61,016 rows total); SQLite requires no server, no credentials, and no new infrastructure, and Power BI connects to SQLite files directly. No repository architecture requires another database — `sql/` held only a placeholder before this phase.
* Tracked or ignored: the database file is **not committed**. It is a local rebuildable artifact (like the ignored generated CSVs): regenerate any time with `python sql/load_data.py`. Only the loader, schema, views, validator, and this document are intended for version control.
* Reproducible rebuild: `python sql/load_data.py` deletes any existing database file, verifies every source's bytes against its quality-record hash, then recreates schema, rows (in frozen file order), and views deterministically. Consecutive rebuilds are byte-identical (verified: `b75c75f3…` twice).

## 2. Source-Input Inventory

Only the six frozen Phase 4C output CSVs (read-only; each verified against the SHA-256 in its own quality JSON before loading):

| Input | Grain | Purpose | Quality JSON reference | Limitation |
| ----- | ----- | ------- | ---------------------- | ---------- |
| `phase4c_baseline_total.csv` (20 rows) | Overall TOTAL | Baseline TOTAL summary (AO-01) | `phase4c_baseline_total_quality.json` (18/18) | Conditional on benchmarks; OFF costs excluded |
| `phase4c_band_contribution.csv` (238 rows) | Overall × band, ORDER + LINE | Band contribution (AO-02) | `phase4c_band_contribution_quality.json` (17/17) | LINE rows partial (gap 200.0476) |
| `phase4c_scenario_comparison_total.csv` (105 rows) | Overall TOTAL per instance | Scenario comparison (AO-03) | `phase4c_scenario_comparison_total_quality.json` (19/19) | Identities zero by construction |
| `phase4c_contribution_variance_by_band.csv` (420 rows) | Overall × band per instance | Band variance (AO-04) | `phase4c_contribution_variance_by_band_quality.json` (21/21) | Baseline bands only, never re-banded |
| `phase4c_order_reading.csv` (60,108 rows) | Order | Order-level context (AO-05) | `phase4c_order_reading_quality.json` (17/17) | Single observations; no hypothetical detail |
| `phase4c_quality_summary.csv` (125 rows) | Artifact, then TOTAL | Eligibility gate (AO-06) | `phase4c_quality_summary_quality.json` (9/9) | Arithmetic/lineage fitness only |

Unavailable metrics stay `N/A` with documented reasons (empty value + reason columns); nothing is derived to fill them.

## 3. Table and View Inventory

Tables (one per frozen output; all columns TEXT to preserve exact frozen strings; UNIQUE record identity per output, except AO-06 whose mirrors inherit the frozen Phase 3B reused check ID by design):

* `ao01_baseline_total` — 20 rows; UNIQUE(metric_name).
* `ao02_band_contribution` — 238 rows; UNIQUE(basis, band, metric_name).
* `ao03_scenario_comparison` — 105 rows; UNIQUE(scenario_id, block, metric_name).
* `ao04_band_variance` — 420 rows; UNIQUE(scenario_id, band, block, metric_name).
* `ao05_order_reading` — 60,108 rows; UNIQUE(order_id, metric_name).
* `ao06_quality_summary` — 125 rows; mirror fidelity enforced by validation instead of UNIQUE.

Views (thin ordered selects, no new metrics or calculations):

* `baseline_total`, `contribution_by_band`, `scenario_comparison_total`, `variance_by_band`, `order_reading`, `quality_summary` — each `SELECT *` over its table `ORDER BY rowid` (frozen file order), with full row coverage asserted.

## 4. Grain and Authority Rules

Every table/view preserves source output name, reporting grain, scenario status, baseline/hypothetical/variance block, metric name/value, unit, definition reference, and limitation in dedicated columns. Incompatible grains are never combined: ORDER-authoritative, LINE-partial, gross-only, observed-baseline, and hypothetical-sensitivity values travel in separate rows/blocks exactly as frozen, with authority and limitation text intact.

## 5. Loading Process

`python sql/load_data.py [--processed-dir DIR] [--db PATH]`:
1. asserts all six CSVs and quality JSONs exist;
2. asserts each CSV's bytes equal the SHA-256 recorded in its quality JSON and that all recorded checks PASS;
3. asserts uniform CSV width per file;
4. removes any existing database file, executes `sql/schema.sql`, inserts rows in frozen file order (failing on any UNIQUE violation), executes `sql/views.sql`, and commits.

## 6. Validation Checks

`python sql/validate_sql_outputs.py` (13/13 PASS): `db-exists`, `tables-exist` (6/6), `views-exist` (6/6 with full row coverage), `columns-match` (6/6 headers), `row-counts` (20/238/105/420/60108/125 in db and CSVs), `content-equal` (all 61,016 rows identical to frozen CSVs), `spot-values` (AO-01 contribution, AO-03 uniform variance, AO-04 B5 variance, AO-06 verdict), `na-preserved` (14/6/42 empty N/A rows), `status-labels` (observed/hypothetical separation), `mirror-fidelity` (75 upstream checks mirrored verbatim in order), `order-coverage` (5,009 distinct orders), `band-coverage` (B0–B5 + TOTAL), `frozen-unchanged` (6/6 AO CSVs byte-identical to quality records). Failure behavior (directly tested): missing input fails `[inputs-exist]` with no database written; tampered content fails `[quality-chain]` with no database written; invalid content can never reach the tables.

## 7. Known Limitations

* The database mirrors frozen values; it performs no analysis and licenses no behavioral, predictive, or causal reading (same standing as its sources).
* Numeric values are stored as their exact frozen text; cast explicitly at query time if arithmetic is needed downstream.
* AO-06 upstream checks are mirrored, not re-executed, per the frozen evidence design.
* The `.db` file is environment-rebuildable but byte-identity across machines/versions is not guaranteed — only same-machine consecutive rebuilds are asserted byte-identical.

## 8. Rebuild Instructions

From the repository root, with frozen inputs in place:

```text
python sql/load_data.py
python sql/validate_sql_outputs.py
```

Expected: `OK: loaded 61016 rows into data/processed/marginmap.db` followed by 13 PASS lines and `OK: all Phase 6 SQL validation checks passed`.

## 9. Read-Only Statement

The SQL layer is read-only with respect to frozen Phase 4C outputs: it opens every source for reading only, verifies bytes before use, writes solely to the new database file, and modifies no frozen CSV, quality JSON, script, document, or upstream artifact.
