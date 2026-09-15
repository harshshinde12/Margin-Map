-- Margin Map Phase 6 SQL data layer — table definitions.
-- One table per frozen Phase 4C analytical output (AO-01..AO-06).
-- Every column is TEXT so frozen values (including empty N/A markers
-- and flag strings) are preserved byte-for-byte; no type coercion,
-- no recalculation, no grain merging. UNIQUE constraints enforce the
-- frozen record identity of each output. Read-only layer: nothing here
-- writes back to the frozen CSVs.

CREATE TABLE IF NOT EXISTS ao01_baseline_total (
    output_name      TEXT NOT NULL,
    scenario_status  TEXT NOT NULL,
    grain            TEXT NOT NULL,
    source_artifact  TEXT NOT NULL,
    metric_name      TEXT NOT NULL,
    metric_value     TEXT NOT NULL,
    unit             TEXT NOT NULL,
    definition_ref   TEXT NOT NULL,
    limitation       TEXT NOT NULL,
    UNIQUE (metric_name)
);

CREATE TABLE IF NOT EXISTS ao02_band_contribution (
    output_name      TEXT NOT NULL,
    scenario_status  TEXT NOT NULL,
    grain            TEXT NOT NULL,
    basis            TEXT NOT NULL,
    band             TEXT NOT NULL,
    source_artifact  TEXT NOT NULL,
    metric_name      TEXT NOT NULL,
    metric_value     TEXT NOT NULL,
    unit             TEXT NOT NULL,
    definition_ref   TEXT NOT NULL,
    limitation       TEXT NOT NULL,
    UNIQUE (basis, band, metric_name)
);

CREATE TABLE IF NOT EXISTS ao03_scenario_comparison (
    output_name      TEXT NOT NULL,
    scenario_status  TEXT NOT NULL,
    grain            TEXT NOT NULL,
    scenario_id      TEXT NOT NULL,
    block            TEXT NOT NULL,
    source_artifact  TEXT NOT NULL,
    metric_name      TEXT NOT NULL,
    metric_value     TEXT NOT NULL,
    unit             TEXT NOT NULL,
    definition_ref   TEXT NOT NULL,
    limitation       TEXT NOT NULL,
    UNIQUE (scenario_id, block, metric_name)
);

CREATE TABLE IF NOT EXISTS ao04_band_variance (
    output_name      TEXT NOT NULL,
    scenario_status  TEXT NOT NULL,
    grain            TEXT NOT NULL,
    scenario_id      TEXT NOT NULL,
    band             TEXT NOT NULL,
    block            TEXT NOT NULL,
    source_artifact  TEXT NOT NULL,
    metric_name      TEXT NOT NULL,
    metric_value     TEXT NOT NULL,
    unit             TEXT NOT NULL,
    definition_ref   TEXT NOT NULL,
    limitation       TEXT NOT NULL,
    UNIQUE (scenario_id, band, block, metric_name)
);

CREATE TABLE IF NOT EXISTS ao05_order_reading (
    output_name      TEXT NOT NULL,
    scenario_status  TEXT NOT NULL,
    grain            TEXT NOT NULL,
    order_id         TEXT NOT NULL,
    discount_band    TEXT NOT NULL,
    return_status    TEXT NOT NULL,
    neg_flag         TEXT NOT NULL,
    ambiguity_note   TEXT NOT NULL,
    source_artifact  TEXT NOT NULL,
    metric_name      TEXT NOT NULL,
    metric_value     TEXT NOT NULL,
    unit             TEXT NOT NULL,
    definition_ref   TEXT NOT NULL,
    limitation       TEXT NOT NULL,
    UNIQUE (order_id, metric_name)
);

-- NOTE: ao06 has no UNIQUE constraint by design. Its upstream-check
-- mirror rows inherit the frozen Phase 3B record's one reused check ID
-- ('frozen' appears twice there); forcing uniqueness would require
-- rewording frozen evidence, which is forbidden. Fidelity is enforced
-- instead by the mirror-fidelity validation (exact multiset match).
CREATE TABLE IF NOT EXISTS ao06_quality_summary (
    output_name      TEXT NOT NULL,
    scenario_status  TEXT NOT NULL,
    grain            TEXT NOT NULL,
    artifact         TEXT NOT NULL,
    check_id         TEXT NOT NULL,
    metric_name      TEXT NOT NULL,
    metric_value     TEXT NOT NULL,
    unit             TEXT NOT NULL,
    status           TEXT NOT NULL,
    expected         TEXT NOT NULL,
    actual           TEXT NOT NULL,
    source_artifact  TEXT NOT NULL,
    definition_ref   TEXT NOT NULL,
    limitation       TEXT NOT NULL
);
