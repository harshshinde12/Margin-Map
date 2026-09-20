import { useMemo, useState } from 'react';
import { api } from '../api/client';
import type { QualityCheck } from '../api/types';
import { SelectField } from '../components/filters/FilterBar';
import { KpiCard } from '../components/kpi/KpiCard';
import { PageHeader } from '../components/layout/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/states/EmptyState';
import { ErrorState } from '../components/states/ErrorState';
import { KpiSkeleton, TableSkeleton } from '../components/states/LoadingSkeleton';
import { DataTable } from '../components/tables/DataTable';
import type { Column } from '../components/tables/DataTable';
import { Pagination } from '../components/tables/Pagination';
import { useApi } from '../hooks/useApi';
import { formatByUnit, metricLabel } from '../utils/format';

const PAGE_SIZE = 25;

export function Quality() {
  const [artifact, setArtifact] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(0);

  const { data, loading, error, reload } = useApi(
    () =>
      api.quality({
        artifact: artifact || undefined,
        status: status || undefined,
      }),
    [artifact, status],
  );

  // Artifact options come from an unfiltered fetch so choosing one never
  // collapses the dropdown to itself.
  const { data: allQuality } = useApi(() => api.quality(), []);

  const artifacts = useMemo(
    () => Array.from(new Set((allQuality?.data ?? []).map((r) => r.artifact))).sort(),
    [allQuality],
  );

  const verdicts = useMemo(() => {
    const rows = (data?.data ?? []).filter((r) => r.artifact === 'ALL_ARTIFACTS');
    const get = (metric: string) => rows.find((r) => r.metric_name === metric)?.metric_value;
    return {
      artifacts: get('artifacts_verified'),
      checks: get('checks_attested'),
      eligibility: get('overall_eligibility'),
    };
  }, [data]);

  const showVerdicts = artifact === '' || artifact === 'ALL_ARTIFACTS';

  const rows = useMemo(() => data?.data ?? [], [data]);
  const pageRows = useMemo(
    () => rows.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE),
    [rows, page],
  );
  const hasNext = (page + 1) * PAGE_SIZE < rows.length;

  const reset = () => {
    setArtifact('');
    setStatus('');
    setPage(0);
  };

  const columns: Column<QualityCheck>[] = useMemo(
    () => [
      { key: 'artifact', header: 'Artifact', render: (r) => r.artifact },
      { key: 'check', header: 'Check', render: (r) => r.check_id },
      { key: 'metric', header: 'Metric', render: (r) => metricLabel(r.metric_name) },
      {
        key: 'value',
        header: 'Value',
        render: (r) =>
          r.metric_value === ''
            ? 'N/A'
            : ['CUR', 'PCT', 'PP', 'CT', 'DEC'].includes(r.unit)
              ? formatByUnit(r.metric_value, r.unit)
              : r.metric_value,
      },
      {
        key: 'status',
        header: 'Status',
        render: (r) => <StatusBadge status={r.status} />,
      },
      {
        key: 'expected',
        header: 'Expected',
        render: (r) => (
          <span className="truncate" style={{ display: 'inline-block' }} title={r.expected}>
            {r.expected}
          </span>
        ),
      },
      {
        key: 'actual',
        header: 'Actual',
        render: (r) => (
          <span className="truncate" style={{ display: 'inline-block' }} title={r.actual}>
            {r.actual}
          </span>
        ),
      },
    ],
    [],
  );

  const allPass = rows.length > 0 && rows.every((r) => r.status === 'PASS');

  return (
    <div className="page">
      <PageHeader
        title="Data Quality & Analytical Reliability"
        lede="Eligibility gate: which artifacts may source interpretation. Arithmetic and lineage fitness only."
        meta={
          <>
            <span className="badge badge-info">AO-06 · Artifact grain</span>
            {allPass ? (
              <span className="badge badge-pass">All checks PASS</span>
            ) : (
              <span className="badge badge-warn">Checks need review</span>
            )}
          </>
        }
      />

      <div className="filter-bar" role="group" aria-label="Quality filters">
        <SelectField
          id="q-artifact"
          label="Artifact"
          value={artifact}
          onChange={(v) => {
            setArtifact(v);
            setPage(0);
          }}
          options={artifacts.map((a) => ({ value: a, label: a }))}
        />
        <SelectField
          id="q-status"
          label="Status"
          value={status}
          onChange={(v) => {
            setStatus(v);
            setPage(0);
          }}
          options={[{ value: 'PASS', label: 'PASS' }]}
        />
        <button type="button" className="btn" onClick={reset}>
          Reset Filters
        </button>
      </div>

      {loading ? (
        <>
          <div className="section">
            <KpiSkeleton />
          </div>
          <TableSkeleton />
        </>
      ) : error || !data ? (
        <ErrorState message={error ?? undefined} onRetry={reload} />
      ) : rows.length === 0 ? (
        <EmptyState message="No quality checks match the selected filters." onClear={reset} />
      ) : (
        <>
          {showVerdicts ? (
            <div className="section">
              <div className="kpi-grid cols-3">
                <KpiCard label="Artifacts Verified" value={verdicts.artifacts || 'N/A'} sub="Source artifacts" />
                <KpiCard label="Checks Attested" value={verdicts.checks || 'N/A'} sub="Upstream PASS checks" />
                <KpiCard
                  label="Overall Eligibility"
                  value={verdicts.eligibility || 'N/A'}
                  sub="Gate verdict"
                />
              </div>
            </div>
          ) : null}

          <div className="section">
            <div className="section-head">
              <div>
                <h3>Quality checks</h3>
                <p>{rows.length} stored checks · mirrored verbatim · no scores computed</p>
              </div>
            </div>
            <DataTable
              ariaLabel="Quality checks"
              columns={columns}
              rows={pageRows}
              rowKey={(r, i) => `${r.artifact}-${r.check_id}-${r.metric_name}-${i}`}
            />
            {rows.length > PAGE_SIZE ? (
              <Pagination
                offset={page * PAGE_SIZE}
                limit={PAGE_SIZE}
                pageCount={pageRows.length}
                hasNext={hasNext}
                onPrev={() => setPage((p) => Math.max(0, p - 1))}
                onNext={() => setPage((p) => p + 1)}
                rangeLabel={`Rows ${page * PAGE_SIZE + 1}–${page * PAGE_SIZE + pageRows.length} of ${rows.length}`}
              />
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
