import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api/client';
import type { ContributionRecord } from '../api/types';
import { ChartCard } from '../components/charts/ChartCard';
import { BAND_ORDER, CHART } from '../components/charts/theme';
import { SelectField } from '../components/filters/FilterBar';
import { KpiCard } from '../components/kpi/KpiCard';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/states/EmptyState';
import { ErrorState } from '../components/states/ErrorState';
import { ChartSkeleton, KpiSkeleton, TableSkeleton } from '../components/states/LoadingSkeleton';
import { DataTable } from '../components/tables/DataTable';
import type { Column } from '../components/tables/DataTable';
import { useApi } from '../hooks/useApi';
import {
  formatByUnit,
  formatCompactCurrency,
  metricLabel,
  parseValue,
} from '../utils/format';

const BANDS = ['B0', 'B1', 'B2', 'B3', 'B4', 'B5'] as const;

export function DiscountBands() {
  const [basis, setBasis] = useState('ORDER');
  const [band, setBand] = useState('');
  const [metric, setMetric] = useState('contribution_profit');

  const { data, loading, error, reload } = useApi(
    () => api.contribution({ basis }),
    [basis],
  );

  const metrics = useMemo(
    () => Array.from(new Set((data?.data ?? []).map((r) => r.metric_name))).sort(),
    [data],
  );

  const activeMetric = metrics.includes(metric) ? metric : (metrics[0] ?? 'contribution_profit');

  const chartRows = useMemo(() => {
    const rows = (data?.data ?? []).filter(
      (r) => r.metric_name === activeMetric && parseValue(r.metric_value) !== null,
    );
    const byBand = new Map(rows.map((r) => [r.band, r]));
    return BAND_ORDER.map((b) => byBand.get(b)).filter(
      (r): r is ContributionRecord => !!r,
    );
  }, [data, activeMetric]);

  const chartData = useMemo(
    () =>
      chartRows.map((r) => ({
        band: r.band,
        value: parseValue(r.metric_value) ?? 0,
        raw: r.metric_value,
        unit: r.unit,
        isTotal: r.band === 'TOTAL',
      })),
    [chartRows],
  );

  const chartUnit = chartRows[0]?.unit ?? 'CUR';

  const tableRows = useMemo(
    () => (data?.data ?? []).filter((r) => (band ? r.band === band : true) && r.metric_name === activeMetric),
    [data, band, activeMetric],
  );

  const totalRow = useMemo(
    () => tableRows.find((r) => r.band === 'TOTAL') ?? null,
    [tableRows],
  );

  const bodyRows = useMemo(() => tableRows.filter((r) => r.band !== 'TOTAL'), [tableRows]);

  const reset = () => {
    setBand('');
    setMetric('contribution_profit');
    setBasis('ORDER');
  };
  const hasActive = band !== '' || metric !== 'contribution_profit' || basis !== 'ORDER';

  const columns: Column<ContributionRecord>[] = useMemo(
    () => [
      { key: 'band', header: 'Band', render: (r) => r.band },
      { key: 'basis', header: 'Basis', render: (r) => r.basis },
      { key: 'metric', header: 'Metric', render: (r) => metricLabel(r.metric_name) },
      {
        key: 'value',
        header: 'Value',
        numeric: true,
        render: (r) => formatByUnit(r.metric_value, r.unit),
      },
      { key: 'unit', header: 'Unit', render: (r) => r.unit },
      {
        key: 'limitation',
        header: 'Limitation',
        render: (r) => (
          <span className="truncate" style={{ display: 'inline-block' }}>
            {r.limitation}
          </span>
        ),
        title: (r) => r.limitation,
      },
    ],
    [],
  );

  return (
    <div className="page">
      <PageHeader
        title="Discount Band Contribution"
        lede="Where baseline revenue, freight, and contribution sit across observed discount configurations."
        meta={
          <>
            <span className="badge badge-info">AO-02 · Overall × band</span>
            <span className="badge badge-neutral">ORDER basis authoritative</span>
          </>
        }
      />

      <div className="filter-bar" role="group" aria-label="Contribution filters">
          <SelectField
            id="basis"
            label="Basis"
            value={basis}
            onChange={setBasis}
            allowAll={false}
            options={[
              { value: 'ORDER', label: 'ORDER — authoritative' },
              { value: 'LINE', label: 'LINE — partial companion' },
            ]}
          />
        <SelectField
          id="band"
          label="Discount band"
          value={band}
          onChange={setBand}
          options={BANDS.map((b) => ({ value: b, label: b }))}
        />
        <SelectField
          id="metric"
          label="Metric"
          value={activeMetric}
          onChange={setMetric}
          allLabel="Select metric"
          options={metrics.map((m) => ({ value: m, label: metricLabel(m) }))}
        />
        <button type="button" className="btn" onClick={reset} disabled={!hasActive}>
          Reset Filters
        </button>
      </div>

      {hasActive ? (
        <div className="active-filters" aria-live="polite">
          Active filters:
          {basis ? <span className="chip">Basis: {basis}</span> : null}
          {band ? <span className="chip">Band: {band}</span> : null}
          <span className="chip">Metric: {metricLabel(activeMetric)}</span>
        </div>
      ) : null}

      {loading ? (
        <>
          <div className="section">
            <KpiSkeleton />
          </div>
          <div className="section">
            <ChartSkeleton />
          </div>
          <TableSkeleton />
        </>
      ) : error || !data ? (
        <ErrorState message={error ?? undefined} onRetry={reload} />
      ) : tableRows.length === 0 ? (
        <EmptyState message="No contribution rows match the selected filters." onClear={reset} />
      ) : (
        <>
          <div className="section">
            <div className="kpi-grid cols-3">
              {bodyRows.slice(0, 3).map((r) => (
                <KpiCard
                  key={r.band}
                  label={`${r.band} · ${metricLabel(r.metric_name)}`}
                  value={
                    r.unit === 'CUR'
                      ? formatCompactCurrency(r.metric_value)
                      : formatByUnit(r.metric_value, r.unit)
                  }
                  sub={`${r.basis} basis · ${r.unit}`}
                  title={formatByUnit(r.metric_value, r.unit)}
                />
              ))}
            </div>
          </div>

          <div className="section">
            <div className="section-head">
              <div>
                <h3>
                  {metricLabel(activeMetric)} by discount band
                </h3>
                <p>
                  {basis} basis · TOTAL shown as a gray reference bar · hover for exact values
                </p>
              </div>
            </div>
            <ChartCard
              title={`${metricLabel(activeMetric)} — B0 to B5 with TOTAL reference`}
              height={300}
            >
              <ResponsiveContainer>
                <BarChart data={chartData} margin={{ left: 8, right: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                  <XAxis dataKey="band" tick={{ fill: CHART.tick, fontSize: 12 }} />
                  <YAxis
                    tick={{ fill: CHART.tick, fontSize: 12 }}
                    tickFormatter={(v: number) =>
                      chartUnit === 'CUR'
                        ? `$${(v / 1000).toFixed(0)}K`
                        : chartUnit === 'PCT' || chartUnit === 'PP'
                          ? `${v.toFixed(1)}${chartUnit === 'PCT' ? '%' : ' pp'}`
                          : v.toLocaleString('en-US')
                    }
                  />
                  <Tooltip
                    formatter={(_value, _name, props) => [
                      formatByUnit(
                        String(props?.payload?.raw ?? ''),
                        String(props?.payload?.unit ?? ''),
                      ),
                      metricLabel(activeMetric),
                    ]}
                    labelFormatter={(label) => `Band ${label}`}
                  />
                  <ReferenceLine y={0} stroke={CHART.slate} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {chartData.map((d) => (
                      <Cell
                        key={d.band}
                        fill={d.isTotal ? '#94a3b8' : d.value < 0 ? CHART.trueRed : CHART.blue}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="section">
            <div className="section-head">
              <div>
                <h3>Contribution detail</h3>
                <p>
                  {tableRows.length} stored rows · values formatted by unit · TOTAL pinned below
                </p>
              </div>
            </div>
            <DataTable
              ariaLabel="Contribution by band"
              columns={columns}
              rows={bodyRows}
              rowKey={(r) => `${r.basis}-${r.band}-${r.metric_name}`}
              totalRow={totalRow}
            />
          </div>
        </>
      )}
    </div>
  );
}
