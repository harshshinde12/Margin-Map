import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api/client';
import type { BaselineMetric } from '../api/types';
import { ChartCard } from '../components/charts/ChartCard';
import { CHART } from '../components/charts/theme';
import { KpiCard } from '../components/kpi/KpiCard';
import { PageHeader } from '../components/layout/PageHeader';
import { ErrorState } from '../components/states/ErrorState';
import { EmptyState } from '../components/states/EmptyState';
import { ChartSkeleton, KpiSkeleton, TableSkeleton } from '../components/states/LoadingSkeleton';
import { DataTable } from '../components/tables/DataTable';
import type { Column } from '../components/tables/DataTable';
import { useApi } from '../hooks/useApi';
import {
  formatByUnit,
  formatCompactCurrency,
  formatCount,
  formatCurrency,
  formatDecimal,
  formatPercent,
  metricLabel,
} from '../utils/format';

/** KPI slots rendered only when the metric is present in the API response. */
const PRIMARY_KPIS = [
  { metric: 'net_revenue', label: 'Net Revenue' },
  { metric: 'modeled_gross_profit', label: 'Modeled Gross Profit' },
  { metric: 'contribution_profit', label: 'Contribution Profit' },
  { metric: 'contribution_margin_pct', label: 'Contribution Margin' },
  { metric: 'cost_to_serve', label: 'Cost to Serve' },
] as const;

/** Currency metrics shown side-by-side as stored (no derivation). */
const CHART_METRICS = [
  'net_revenue',
  'discount_amount',
  'modeled_cogs',
  'modeled_gross_profit',
  'cost_to_serve',
  'contribution_profit',
] as const;

export function Executive() {
  const { data, loading, error, reload } = useApi(() => api.baseline(), []);

  const byMetric = useMemo(() => {
    const map = new Map<string, BaselineMetric>();
    for (const row of data?.data ?? []) map.set(row.metric_name, row);
    return map;
  }, [data]);

  const chartData = useMemo(
    () =>
      CHART_METRICS.map((m) => byMetric.get(m))
        .filter((r): r is BaselineMetric => !!r && r.unit === 'CUR')
        .map((r) => ({
          name: metricLabel(r.metric_name),
          value: Number(r.metric_value),
          raw: r.metric_value,
        }))
        .filter((d) => Number.isFinite(d.value)),
    [byMetric],
  );

  const columns: Column<BaselineMetric>[] = useMemo(
    () => [
      { key: 'metric', header: 'Metric', render: (r) => metricLabel(r.metric_name) },
      {
        key: 'value',
        header: 'Value',
        numeric: true,
        render: (r) => formatByUnit(r.metric_value, r.unit),
      },
      { key: 'unit', header: 'Unit', render: (r) => r.unit },
      {
        key: 'definition',
        header: 'Definition',
        render: (r) => <span className="truncate" style={{ display: 'inline-block' }}>{r.definition_ref}</span>,
        title: (r) => r.definition_ref,
      },
      {
        key: 'limitation',
        header: 'Limitation',
        render: (r) => <span className="truncate" style={{ display: 'inline-block' }}>{r.limitation}</span>,
        title: (r) => r.limitation,
      },
    ],
    [],
  );

  return (
    <div className="page">
      <PageHeader
        title="Executive Profitability Overview"
        lede="Baseline profitability and contribution performance — observed baseline at TOTAL grain."
        meta={
          <>
            <span className="badge badge-info">AO-01 · Baseline TOTAL</span>
            <span className="badge badge-neutral">Observed baseline</span>
          </>
        }
      />

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
      ) : data.data.length === 0 ? (
        <EmptyState message="The baseline endpoint returned no rows." />
      ) : (
        <>
          <div className="section">
            <div className="kpi-grid">
              {PRIMARY_KPIS.map((kpi) => {
                const record = byMetric.get(kpi.metric);
                if (!record) return null;
                const value =
                  record.unit === 'PCT'
                    ? formatPercent(record.metric_value)
                    : formatCompactCurrency(record.metric_value);
                return (
                  <KpiCard
                    key={kpi.metric}
                    label={kpi.label}
                    value={value}
                    sub="Baseline · TOTAL"
                    title={`${metricLabel(record.metric_name)}: ${formatByUnit(record.metric_value, record.unit)}`}
                  />
                );
              })}
            </div>
          </div>

          <div className="section">
            <div className="kpi-grid cols-4">
              {(
                [
                  { metric: 'order_count', format: formatCount, label: 'Orders' },
                  { metric: 'line_count', format: formatCount, label: 'Order Lines' },
                  { metric: 'revenue_realization_rate', format: (v: string) => formatPercent(v), label: 'Revenue Realization' },
                  { metric: 'wad', format: (v: string) => formatDecimal(v), label: 'WAD · Wtd. Avg. Discount' },
                ] as const
              ).map((item) => {
                const record = byMetric.get(item.metric);
                if (!record) return null;
                return (
                  <KpiCard
                    key={item.metric}
                    label={item.label}
                    value={item.format(record.metric_value)}
                    sub={`Baseline · TOTAL · ${record.unit}`}
                    title={`${metricLabel(record.metric_name)}: ${formatByUnit(record.metric_value, record.unit)} (${record.unit})`}
                  />
                );
              })}
            </div>
          </div>

          <div className="section">
            <div className="section-head">
              <div>
                <h3>Baseline economics</h3>
                <p>Stored currency metrics shown side-by-side — values as reported, no decomposition implied.</p>
              </div>
            </div>
            <ChartCard
              title="Baseline Value by Metric"
              note="USD · observed baseline TOTAL · hover for exact values"
              height={300}
            >
              <ResponsiveContainer>
                <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} horizontal={false} />
                  <XAxis
                    type="number"
                    tick={{ fill: CHART.tick, fontSize: 12 }}
                    tickFormatter={(v: number) => `$${(v / 1_000_000).toFixed(1)}M`}
                  />
                  <YAxis type="category" dataKey="name" width={150} tick={{ fill: CHART.tick, fontSize: 12 }} />
                  <Tooltip
                    formatter={(_value, _name, props) => [formatCurrency(String(props?.payload?.raw ?? '')), 'Value']}
                    labelStyle={{ fontWeight: 600 }}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {chartData.map((d) => (
                      <Cell
                        key={d.name}
                        fill={d.name === 'Contribution Profit' ? CHART.teal : CHART.blue}
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
                <h3>Baseline details</h3>
                <p>All {data.count} approved AO-01 metrics with definitions and limitations.</p>
              </div>
            </div>
            <DataTable
              ariaLabel="Baseline metrics"
              columns={columns}
              rows={data.data}
              rowKey={(r) => r.metric_name}
            />
          </div>
        </>
      )}
    </div>
  );
}
