-- Margin Map Phase 6 SQL data layer — read-only display views.
-- One view per approved display use case (Phase 5 inventory). Each view
-- is a thin, deterministically ordered select over its frozen-output
-- table: no new metrics, no recalculation, no grain merging, no filters
-- beyond the approved scope. ORDER BY rowid preserves the frozen,
-- validated file order of each source CSV.

CREATE VIEW IF NOT EXISTS baseline_total AS
SELECT * FROM ao01_baseline_total ORDER BY rowid;

CREATE VIEW IF NOT EXISTS contribution_by_band AS
SELECT * FROM ao02_band_contribution ORDER BY rowid;

CREATE VIEW IF NOT EXISTS scenario_comparison_total AS
SELECT * FROM ao03_scenario_comparison ORDER BY rowid;

CREATE VIEW IF NOT EXISTS variance_by_band AS
SELECT * FROM ao04_band_variance ORDER BY rowid;

CREATE VIEW IF NOT EXISTS order_reading AS
SELECT * FROM ao05_order_reading ORDER BY rowid;

CREATE VIEW IF NOT EXISTS quality_summary AS
SELECT * FROM ao06_quality_summary ORDER BY rowid;
