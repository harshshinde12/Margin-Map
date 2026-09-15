# Phase 7A — Power BI Data Connection and Report Foundation

```text
FOUNDATION ONLY — NO VISUALS, NO CALCULATIONS, NO FORECASTING
```

## 1. Status and Purpose

This document prepares the Power BI report foundation only. It records the verified SQLite source, the six approved read-only views, and the intended import procedure for future visuals. It creates no dashboard visuals, no DAX/Power Query calculations, no new metrics, no forecast, no optimization, no segmentation, no recommendation, and no causal analysis.

All future visuals remain bound by the approved Phase 5 display scope (`docs/PHASE_5_DISPLAY_SCOPE_AND_CONVENTIONS.md`), the frozen Phase 6 SQL data layer (`docs/PHASE_6_SQL_DATA_LAYER_FREEZE.md`), and the binding Gate 10 display rules (§11 below). Frozen AO-01–AO-06 artifacts are read-only and untouched.

Verification date (UTC): 2026-09-15. Validator result at foundation time: 13/13 PASS (`python sql/validate_sql_outputs.py`).

## 2. Database Source Path

* Local SQLite database file:

```text
data/processed/marginmap.db
```

* Verified present at foundation time: exists, size ~17,211,392 bytes.
* Technology: SQLite via Python standard-library `sqlite3` (engine 3.50.4 at Phase 6 build); no server, no credentials, no third-party database dependency.
* Tracked or ignored: **not committed**. Ignored by `.gitignore` line 16 (`*.db`, verified via `git check-ignore -v data/processed/marginmap.db`). It is a locally rebuildable artifact, not a frozen source.
* Rebuild authority (sole writer):

```text
python sql/load_data.py
```

* Re-validate after any rebuild:

```text
python sql/validate_sql_outputs.py
```

* Expected rebuild output: `OK: loaded 61016 rows into data/processed/marginmap.db` followed by 13 PASS lines and `OK: all Phase 6 SQL validation checks passed`.
* The database was **not modified manually** in this task. All verification queries opened it read-only (`mode=ro` URI). The loader was not re-executed in this task because the existing file already validated 13/13 PASS; rebuild only if missing or validation fails.

## 3. View-Name Note (Task Text vs Frozen Layer)

The Phase 7A task text lists the six views with a `vw_` prefix (`vw_baseline_total`, `vw_contribution_by_band`, `vw_scenario_comparison_total`, `vw_variance_by_band`, `vw_order_reading`, `vw_quality_summary`).

The frozen Phase 6 layer (`sql/views.sql`, `docs/PHASE_6_SQL_DATA_LAYER_FREEZE.md` §6) defines the six views **without** that prefix. The exact frozen names below are authoritative for Power BI. Mapping for traceability:

| Task-text name | Frozen actual view name (use this) |
| -------------- | ---------------------------------- |
| `vw_baseline_total` | `baseline_total` |
| `vw_contribution_by_band` | `contribution_by_band` |
| `vw_scenario_comparison_total` | `scenario_comparison_total` |
| `vw_variance_by_band` | `variance_by_band` |
| `vw_order_reading` | `order_reading` |
| `vw_quality_summary` | `quality_summary` |

No `vw_*` objects exist in the database. Power BI queries must use the frozen names.

## 4. Six Approved Views (Verified)

Verified 2026-09-15 by read-only inspection: 6/6 tables present, 6/6 views present, each view with full base-table row coverage. No view performs filtering, aggregation, recalculation, or grain merging — each is `SELECT * ... ORDER BY rowid` over its base table, preserving frozen file order.

| # | Display group | Frozen view (query this) | Base table | Rows (view = table = CSV) | Columns |
| - | ------------- | ------------------------ | ---------- | ------------------------- | ------- |
| AO-01 | Baseline TOTAL summary | `baseline_total` | `ao01_baseline_total` | 20 | `output_name, scenario_status, grain, source_artifact, metric_name, metric_value, unit, definition_ref, limitation` |
| AO-02 | Contribution by discount band | `contribution_by_band` | `ao02_band_contribution` | 238 | `output_name, scenario_status, grain, basis, band, source_artifact, metric_name, metric_value, unit, definition_ref, limitation` |
| AO-03 | TOTAL scenario comparison | `scenario_comparison_total` | `ao03_scenario_comparison` | 105 | `output_name, scenario_status, grain, scenario_id, block, source_artifact, metric_name, metric_value, unit, definition_ref, limitation` |
| AO-04 | Variance by baseline discount band | `variance_by_band` | `ao04_band_variance` | 420 | `output_name, scenario_status, grain, scenario_id, band, block, source_artifact, metric_name, metric_value, unit, definition_ref, limitation` |
| AO-05 | Observed order-level context | `order_reading` | `ao05_order_reading` | 60,108 | `output_name, scenario_status, grain, order_id, discount_band, return_status, neg_flag, ambiguity_note, source_artifact, metric_name, metric_value, unit, definition_ref, limitation` |
| AO-06 | Data-quality and eligibility summary | `quality_summary` | `ao06_quality_summary` | 125 | `output_name, scenario_status, grain, artifact, check_id, metric_name, metric_value, unit, status, expected, actual, source_artifact, definition_ref, limitation` |

Total: 20 + 238 + 105 + 420 + 60,108 + 125 = **61,016 rows**.

Row-count expectations for Power BI import (fail-loud if different): 20 / 238 / 105 / 420 / 60108 / 125 respectively. Any other count means a stale or corrupt local `.db` — rebuild via §2 and re-validate before proceeding.

## 5. Expected View Grain (Per View)

| View | `grain` value(s) in data | Grain meaning | Authority / limitation carried in-row |
| ---- | ------------------------ | ------------- | ------------------------------------- |
| `baseline_total` | `TOTAL` | Overall TOTAL, order economics rolled up. Single authoritative baseline reference. | `scenario_status = OBSERVED BASELINE`. Conditional on modeled COGS benchmarks; return/support OFF (excluded, not actual); freight methodology caveat in `limitation`. |
| `contribution_by_band` | `Overall x discount band` with `basis` = `ORDER` (authoritative) and `LINE` (partial companion) | Where baseline revenue, freight, and contribution sit across observed discount configurations. | ORDER rows authoritative for headlines; LINE rows partial (gap 200.0476 to authoritative total) — display in separately labeled companion block only, never averaged with ORDER rows. `N/A`: 14 empty-`metric_value` rows with reason columns intact. |
| `scenario_comparison_total` | `Overall TOTAL` per (`scenario_id`, `block`) | Headline arithmetic sensitivity per frozen instance beside its identical-scope baseline. | `scenario_id` ∈ `uniform_replace_0.10`, `discount_increase_pp_0.00`, `discount_decrease_pp_0.00`; `block` ∈ `baseline`, `hypothetical`, `variance`; `scenario_status` ∈ `OBSERVED BASELINE`, `HYPOTHETICAL_ARITHMETIC_SENSITIVITY` (separated, never merged). Identity slices zero by construction; nonzero universal shifts have no valid output; LINE detail not licensed. `N/A`: 6 empty rows with reasons. |
| `variance_by_band` | `Overall x discount band` per (`scenario_id`, `band`, `block`) | How headline sensitivity distributes across baseline discount configurations. | `band` ∈ B0–B5 + TOTAL (no other bands); baseline bands only, never re-banded; same `scenario_id`/`block`/`scenario_status` separation as AO-03. `N/A`: 42 empty rows with reasons. |
| `order_reading` | `Order` (`order_id`), 5,009 distinct orders | Distributional context (WAD spread, negative orders, ambiguity case, volume) supporting — never replacing — band readings. | Observed values only (`OBSERVED BASELINE`). Single observations; no hypothetical order-level detail exists or may be fabricated. `discount_band`, `return_status`, `neg_flag`, `ambiguity_note` must travel with any displayed order value. |
| `quality_summary` | `Artifact` then `TOTAL` verdict | Eligibility gate: which artifacts may source interpretation. | `scenario_status = QUALITY_GATE`. 75 upstream checks mirrored verbatim in frozen order (16 + 15 + 22 + 22); TOTAL verdict `overall_eligibility = ALL_SOURCES_ELIGIBLE`. Arithmetic/lineage fitness only; no behavioral reading licensed. `ao06` has no UNIQUE constraint by design (frozen Phase 3B reused check ID `frozen` twice); fidelity enforced by exact multiset match. |

Source authority per view (distinct `output_name` / `source_artifact` values verified in data):

* `baseline_total`: `output_name = Baseline performance summary (TOTAL)`; `source_artifact` spans `order_margin_map_phase2.csv` and `fact_margin_map_phase2.csv` (incl. cross-check and NULL-preservation notes) — see `source_artifact` column per metric row.
* `contribution_by_band`: `Contribution by discount band (observed, ORDER basis)`; `source_artifact = discount_band_summary.csv`.
* `scenario_comparison_total`: `Scenario comparison at TOTAL`; `source_artifact` ∈ `phase4b_scenario_uniform_0.10.csv`, `phase4b_scenario_increase_0.00.csv`, `phase4b_scenario_decrease_0.00.csv`.
* `variance_by_band`: `Contribution variance by discount band`; same three Phase 4B scenario CSVs as AO-03.
* `order_reading`: `Order-level baseline reading`; `source_artifact = discount_order_summary.csv`.
* `quality_summary`: `Data-quality summary`; `source_artifact` ∈ `phase3b_quality_report.json`, `phase4b_scenario_quality.json`, `phase4b_scenario_increase_0.00_quality.json`, `phase4b_scenario_decrease_0.00_quality.json` (mirrored checks) plus `Section 10 records` / `this gate` rows for the TOTAL verdict.

All columns are TEXT. Frozen strings — including empty N/A markers and flag text — are preserved exactly with no type coercion. Downstream queries must cast explicitly for any arithmetic (and no new arithmetic is authorized in the display phase).

## 6. Intended Power BI Query / Import Method

Power BI Desktop has **no native SQLite connector**. The approved method is **Import mode via the SQLite ODBC driver**. No `.pbix` is created in this foundation task.

1. Install the SQLite ODBC driver matching the Power BI Desktop bitness on the report machine (64-bit in the normal case; e.g. `SQLite3 ODBC Driver` from the widely used ch-werner build). No database server or credential is required.
2. In Power BI Desktop: **Get Data → ODBC** (or **Get Data → More → Other → ODBC**).
3. Use a connection string with the absolute local path (DSN-less form):

```text
Driver=SQLite3 ODBC Driver;Database=C:\full\path\to\data\processed\marginmap.db;
```

   Substitute the actual checkout path for `C:\full\path\to`. A file/User DSN pointing at the same file is an acceptable equivalent; record whichever is used.
4. Create **one Power Query query per approved view**, each a plain pass-through with no transformation beyond selecting the view:

```sql
SELECT * FROM baseline_total;
SELECT * FROM contribution_by_band;
SELECT * FROM scenario_comparison_total;
SELECT * FROM variance_by_band;
SELECT * FROM order_reading;
SELECT * FROM quality_summary;
```

5. Load with **Import** (not DirectQuery). Rationale: the source is a static frozen file snapshot; Import gives a stable, refresh-controlled copy, avoids per-interaction ODBC round-trips (especially for the 60,108-row `order_reading`), and matches the read-only mirror design. DirectQuery against a local file is not required and not recommended here.
6. In Power Query, keep all columns as **Text** on import to preserve frozen fidelity (empty-string N/A markers, flag text, exact numeric strings). Do not change types as a "fix" — any display-time formatting must leave the stored value untouched and must render empty `metric_value` as `N/A` with its reason, never as zero or blank without explanation.
7. Apply **no merges, appends, joins, grouping, or calculated columns** across queries (see §8 for why). Each future visual reads from exactly one query/view.
8. Validate the import before any visual work: row counts per query must equal §4 expectations (20 / 238 / 105 / 420 / 60108 / 125); spot-check AO-01 `contribution_profit = 565116.9418299999`, AO-03 uniform variance `variance_contribution_profit = 95406.2413300001`, AO-04 B5 uniform variance `variance_contribution = 45401.369600000005`, AO-06 `overall_eligibility = ALL_SOURCES_ELIGIBLE`; confirm N/A empties 14 / 6 / 42 in AO-02 / AO-03 / AO-04.

## 7. Refresh / Rebuild Instructions

The `.pbix` (when later created) never edits the database. Refresh is a two-step, file-first procedure:

```text
python sql/load_data.py
python sql/validate_sql_outputs.py
```

then, in Power BI Desktop, **Refresh** the six ODBC queries.

Rules:

* If the `.db` is missing, stale, moved, or any validation check fails, rebuild with the loader (it verifies chain-of-custody hashes and recorded PASS standing **before** writing anything, rebuilds the file fresh, and aborts fail-loud with nothing written on any breach). Never hand-edit the `.db` (no manual INSERT/UPDATE/DELETE, no GUI SQLite edits).
* After rebuild, re-run the validator and re-confirm the §4 row counts and §6 spot values before refreshing Power BI.
* If the repository checkout path changes, update the ODBC connection string / DSN to the new absolute path of `data/processed/marginmap.db`; the relative path from the repo root is unchanged.
* Scheduled / gateway refresh is out of scope for this local file-based workflow: refresh requires the machine running Power BI to have file access to the rebuilt `.db` and the matching ODBC driver.

## 8. Relationship Requirements — None Created

**Required relationships: none.** Load the six queries as six disconnected tables with **no model relationships** between them.

Why no relationships (binding, not advisory):

* The six views sit at **incompatible grains by design**: overall TOTAL (AO-01) vs Overall × discount band with ORDER/LINE basis markers (AO-02) vs per-instance TOTAL blocks (AO-03) vs per-instance × baseline-band blocks (AO-04) vs Order grain with 5,009 distinct orders (AO-05) vs Artifact/TOTAL quality gate (AO-06). A relationship across any of these would let a filter or slicer propagate across grains that must never be combined (Phase 5 §6).
* Specific mixing hazards a relationship would enable: averaging ORDER-authoritative rows with LINE-partial rows; attributing TOTAL variance to order rows; cross-filtering `hypothetical`/`variance` blocks into `OBSERVED BASELINE` readings; re-banding AO-04 baseline bands via AO-02/AO-05 band fields; joining the 60,108 order rows to band/TOTAL aggregates; spreading AO-06 `QUALITY_GATE` rows across fact grains.
* Each future visual must therefore query **exactly one view** and carry that view's own grain, basis, block, scenario, and limitation labels in the visual itself. Any cross-view comparison is a side-by-side reading of separately labeled visuals, never a joined or blended number.
* No bridge, lookup, or date table is authorized. Any future request for a relationship requires a new separately documented approval — none is granted here.

## 9. Approved Report Pages / Display Groups (Defined, Not Built)

Six display groups only, per Phase 5 §4 inventory. Each maps 1:1 to one frozen view. No page/visual is built in this task.

1. Baseline profitability summary — from `baseline_total` (AO-01); one TOTAL view of revenue, COGS, gross/contribution profit and margins, WAD, volume, loss/cohort context, and NULL indicators.
2. Contribution by baseline discount band — from `contribution_by_band` (AO-02); ORDER-authoritative band view (B0–B5 + TOTAL) with LINE-partial companions kept in a separately labeled block.
3. TOTAL scenario comparison — from `scenario_comparison_total` (AO-03); per-instance baseline / hypothetical / variance blocks at TOTAL grain only.
4. Scenario variance allocation by baseline discount band — from `variance_by_band` (AO-04); per-band variance view on baseline bands with separated layers.
5. Observed order-level context — from `order_reading` (AO-05); distributional views (WAD spread, negative-order list, ambiguity case, volume) at order grain, observed values only.
6. Data-quality and eligibility summary — from `quality_summary` (AO-06); artifact eligibility table with check standing, plus the TOTAL verdict.

Explicitly deferred/prohibited (Phase 5 §7, binding): customer segmentation; product/category-specific scenario views; customer-level hypothetical detail (no such frozen artifact exists — fabrication forbidden); new scenario types; re-banding (hypothetical or otherwise); forecasting; causal claims; elasticity/demand analysis; optimization; pricing recommendations; any unsupported calculation; any modification of frozen artifacts.

## 10. Required Validation and Quality Indicators (Every Future Visual)

Per Phase 5 §§5–6 and Gate 10 (§11), every future visual must visibly carry, as applicable to its single source view:

* Observed-baseline vs hypothetical separation: `scenario_status` (`OBSERVED BASELINE` vs `HYPOTHETICAL_ARITHMETIC_SENSITIVITY` vs `QUALITY_GATE` for AO-06) and, for AO-03/AO-04, the `block` layer (`baseline` / `hypothetical` / `variance`) in distinct blocks or areas — never merged into unexplained numbers.
* Scenario identity: `scenario_id` (`uniform_replace_0.10` / `discount_increase_pp_0.00` / `discount_decrease_pp_0.00`) with discount input form (stated replacement rate vs pp change), per visual.
* Reporting grain and basis: `grain` (`TOTAL` / `Overall x discount band` / `Overall TOTAL` / `Order` / `Artifact`) plus `basis` (`ORDER` authoritative vs `LINE` partial) wherever AO-02 data appears; `band` (B0–B5 + TOTAL) for AO-02/AO-04; `order_id` context with `discount_band`, `return_status`, `neg_flag`, `ambiguity_note` for AO-05.
* Absolute vs margin-unit separation: absolute changes and margin changes in percentage points shown separately; margin-point changes never labeled `%`.
* Unsupported values: empty `metric_value` rendered as `N/A` with the row's reason/limitation text — never zero-filled, never silently omitted. Expected N/A volumes: 14 (AO-02), 6 (AO-03), 42 (AO-04).
* Profit-concept separation: gross profit, contribution profit, and discount-related revenue forgone kept distinct with `definition_ref` traceable.
* Methodology assumptions block (every visual where sensitivity appears): constant observed quantity; modeled COGS; freight passthrough; return-processing costs OFF; support costs OFF.
* Validation standing: AO-06 eligibility table with per-check `status`/`expected`/`actual` and the TOTAL verdict `ALL_SOURCES_ELIGIBLE`; upstream quality standings (AO-01 18/18, AO-02 17/17, AO-03 19/19, AO-04 21/21, AO-05 17/17, AO-06 9/9) cited where the corresponding view is displayed.
* Quality flags: `low_sample_flag`, ambiguity/negative markers, NULL indicators, and each row's `limitation` text where applicable.

## 11. Gate 10 Wording and Standing Caveat (Binding on Every Visual)

Gate 10 (`docs/PHASE_4B_DECISION_LOG.md`, approved by the project owner 2026-09-13) provides:

> Future displays must label results as hypothetical scenario analysis; show baseline, hypothetical, and variance values separately; show absolute changes and margin changes in percentage points; display scenario type, discount input, reporting grain, validation status, and quality flags; mark unsupported metrics as `N/A` with explanation; distinguish gross profit, contribution profit, and discount-related revenue forgone; display the key methodology assumptions (constant observed quantity; modeled COGS; freight passthrough; return-processing and support costs OFF); avoid implying forecasts, causal effects, demand predictions, or optimized pricing; keep deferred scenario views unavailable unless separately approved.

Standing caveat — must be visible on every visual where a predictive or causal misreading is possible (Phase 5 §5 wording, exact):

```text
Illustrative arithmetic sensitivity under stated assumptions; not a forecast, causal estimate, demand prediction, or optimized-pricing recommendation.
```

Permitted descriptive wording only: "illustrative constant-quantity scenario", "arithmetic change under the stated assumptions", "conditional illustration, not a forecast". Prohibited wording (forecast / prediction / causal / optimal / best-policy claims) must not appear except inside the prohibition itself. Gate 10 constrains every future visual but authorizes none; each display proceeds only under the Phase 5 §9 approval, strictly within the §9 inventory.

## 12. Limitations of the SQLite-to-Power BI Workflow

* No native connector: requires a separately installed SQLite ODBC driver whose bitness matches Power BI Desktop; a bitness mismatch is the most common connection failure.
* Absolute-path binding: the ODBC connection string/DSN points at one local checkout's `data/processed/marginmap.db`. Moving or re-cloning the repo breaks the connection until the path is updated. The `.db` is ignored by git, so a fresh clone has no `.db` until `python sql/load_data.py` is run.
* Manual-refresh model: there is no server-side scheduled refresh for this file source; refresh means rebuilding/validating the local `.db` first, then refreshing the Import tables in Power BI.
* TEXT-everything storage: numerics arrive as exact frozen text (fidelity feature, not a bug). Power BI must not coerce on import; any display formatting happens at visual level and must preserve the N/A-empty semantics (§10).
* Scale note: `order_reading` imports 60,108 rows — fine for Import mode, but it is context only. It must never be joined to aggregate views (§8) and no hypothetical order-level detail may be derived from it.
* AO-06 mirrors, not re-execution: `quality_summary` carries mirrored upstream check evidence, not live re-checks. Its standing is exactly as frozen.
* Determinism boundary: same-machine consecutive rebuilds are byte-identical (implementation-reported, code-supported); cross-machine/version byte-identity is not asserted.
* No new logic surface: the ODBC layer, Power Query, and the model must add no filters beyond the approved scope, no calculated columns/measures, no aggregations that cross grains, and no re-banding. Anything beyond pass-through `SELECT *` per §6 needs separate approval.

## 13. Change Boundary and Artifact Protection

* No AO-01–AO-06 script, CSV, quality JSON, or freeze document was modified in this task.
* The SQLite database was not modified manually; it was opened read-only for verification only.
* No dashboard visuals, no `.pbix`, no analytical calculations, and no forecasting/optimization/segmentation/recommendation/causal content were created.
* This document (`docs/PHASE_7_POWER_BI_FOUNDATION.md`) is the only file added in this task. No commit or push was performed.

## 14. Sources Consulted

`sql/schema.sql`, `sql/views.sql`, `sql/load_data.py`, `sql/validate_sql_outputs.py`, `docs/PHASE_5_DISPLAY_SCOPE_AND_CONVENTIONS.md`, `docs/PHASE_6_SQL_DATA_LAYER.md`, `docs/PHASE_6_SQL_DATA_LAYER_FREEZE.md`, `docs/PHASE_4B_DECISION_LOG.md` (Gate 10), plus read-only inspection of `data/processed/marginmap.db`.
