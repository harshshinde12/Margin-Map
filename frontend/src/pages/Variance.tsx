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
import type { VarianceRecord } from '../api/types';
import { ChartCard } from '../components/charts/ChartCard';
import { CHART } from '../components/charts/theme';
import { SelectField } from '../components/filters/FilterBar';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/states/EmptyState';
import { ErrorState } from '../components/states/ErrorState';
import { ChartSkeleton, TableSkeleton } from '../components/states/LoadingSkeleton';
import { DataTable } from '../components/tables/DataTable';
import type { Column } from '../components/tables/DataTable';
import { useApi } from '../hooks/useApi';
import { formatByUnit, formatSignedCurrency, metricLabel, parseValue } from '../utils/format';

const SCENARIOS = [
  { value: 'uniform_replace_0.10', label: 'Uniform 10% replacement' },
  { value: 'uniform_replace_0.20', label: 'Uniform 20% replacement (median observed discount)' },
  { value: 'discount_increase_pp_0.00', label: 'Discount increase 0.00 pp (identity control)' },
  { value: 'discount_decrease_pp_0.00', label: 'Discount decrease 0.00 pp (identity control)' },
];

const VARIANCE_METRICS = [
  { value: 'variance_contribution', label: 'Variance · Contribution' },
  { value: 'variance_net_revenue', label: 'Variance · Net Revenue' },
  { value: 'variance_discount_amount', label: 'Variance · Discount Amount' },
  { value: 'variance_cogs', label: 'Variance · COGS' },
  { value: 'variance_cost_to_serve', label: 'Variance · Cost to Serve' },
  { value: 'variance_freight', label: 'Variance · Freight' },
  { value: 'margin_change_pp', label: 'Margin Change (pp)' },
  { value: 'relative_contribution_variance', label: 'Relative Contribution Variance' },
];

const BANDS = ['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'TOTAL'] as const;

export function Variance() {
  const [scenarioId, setScenarioId] = useState('uniform_replace_0.10');
  const [metric, setMetric] = useState('variance_contribution');

  const { data, loading, error, reload } = useApi(
    () => api.variance({ scenario_id: scenarioId, block: 'variance', metric_name: metric }),
    [scenarioId, metric],
  );

  const chartData = useMemo(() => {
    const byBand = new Map((data?.data ?? []).map((r) => [r.band, r]));
    return BANDS.map((b) => byBand.get(b))
      .filter((r): r is VarianceRecord => !!r && parseValue(r.metric_value) !== null)
      .map((r) => ({
        band: r.band,
        value: parseValue(r.metric_value) ?? 0,
        raw: r.metric_value,
        unit: r.unit,
        isTotal: r.band === 'TOTAL',
      }));
  }, [data]);

  const chartUnit = chartData[0]?.unit ?? 'CUR';

  const reset = () => {
    setScenarioId('uniform_replace_0.10');
    setMetric('variance_contribution');
  };

  const columns: Column<VarianceRecord>[] = useMemo(
    () => [
      { key: 'band', header: 'Band', render: (r) => r.band },
      {
        key: 'value',
        header: 'Variance',
        numeric: true,
        render: (r) => {
          const v = parseValue(r.metric_value);
          if (v === null || v === 0) return formatByUnit(r.metric_value, r.unit);
          return (
            <span className={v > 0 ? 'cell-positive' : 'cell-negative'}>
              {r.unit === 'CUR'
                ? formatSignedCurrency(r.metric_value)
                : formatByUnit(r.metric_value, r.unit)}
            </span>
          );
        },
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

  const metricLabelText =
    VARIANCE_METRICS.find((m) => m.value === metric)?.label ?? metricLabel(metric);

  return (
    <div className="page">
      <PageHeader
        title="Contribution Variance by Discount Band"
        lede="How headline sensitivity distributes across baseline discount configurations — stored variance block, baseline bands only."
        meta={
          <>
            <span className="badge badge-info">AO-04 · Overall × band</span>
            <span className="badge badge-neutral">Variance block</span>
          </>
        }
      />

      <div className="filter-bar" role="group" aria-label="Variance filters">
        <SelectField
          id="v-scenario"
          label="Scenario instance"
          value={scenarioId}
          onChange={setScenarioId}
          options={SCENARIOS}
        />
        <SelectField
          id="v-metric"
          label="Variance metric"
          value={metric}
          onChange={setMetric}
          options={VARIANCE_METRICS}
        />
        <button type="button" className="btn" onClick={reset}>
          Reset Filters
        </button>
      </div>

      {loading ? (
        <>
          <div className="section">
            <ChartSkeleton />
          </div>
          <TableSkeleton />
        </>
      ) : error || !data ? (
        <ErrorState message={error ?? undefined} onRetry={reload} />
      ) : chartData.length === 0 ? (
        <EmptyState message="No variance rows match the selected filters." onClear={reset} />
      ) : (
        <>
          <div className="section">
            <div className="section-head">
              <div>
                <h3>
                  {metricLabelText} — {SCENARIOS.find((s) => s.value === scenarioId)?.label}
                </h3>
                <p>Positive movement in green · negative in red · zero neutral · TOTAL in gray</p>
              </div>
            </div>
            <ChartCard title={`${metricLabelText} by band`} height={300}>
              <ResponsiveContainer>
                <BarChart data={chartData} margin={{ left: 8, right: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                  <XAxis dataKey="band" tick={{ fill: CHART.tick, fontSize: 12 }} />
                  <YAxis
                    tick={{ fill: CHART.tick, fontSize: 12 }}
                    tickFormatter={(v: number) =>
                      chartUnit === 'CUR'
                        ? `$${(v / 1000).toFixed(0)}K`
                        : chartUnit === 'PP'
                          ? `${v.toFixed(1)} pp`
                          : chartUnit === 'PCT'
                            ? `${v.toFixed(1)}%`
                            : v.toLocaleString('en-US')
                    }
                  />
                  <Tooltip
                    formatter={(_value, _name, props) => [
                      formatByUnit(
                        String(props?.payload?.raw ?? ''),
                        String(props?.payload?.unit ?? ''),
                      ),
                      metricLabelText,
                    ]}
                    labelFormatter={(label) => `Band ${label}`}
                  />
                  <ReferenceLine y={0} stroke={CHART.slate} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {chartData.map((d) => (
                      <Cell
                        key={d.band}
                        fill={d.isTotal ? '#94a3b8' : d.value > 0 ? CHART.green : d.value < 0 ? CHART.trueRed : CHART.slate}
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
                <h3>Variance detail</h3>
                <p>{chartData.length} stored band rows · no thresholds · no classifications</p>
              </div>
            </div>
            <DataTable
              ariaLabel="Variance by band"
              columns={columns}
              rows={chartData
                .map((d) => (data?.data ?? []).find((r) => r.band === d.band))
                .filter((r): r is VarianceRecord => !!r)}
              rowKey={(r) => `${r.scenario_id}-${r.band}-${r.metric_name}`}
            />
          </div>
        </>
      )}
    </div>
  );
}
