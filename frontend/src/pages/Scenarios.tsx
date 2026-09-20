import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api/client';
import type { ScenarioRecord } from '../api/types';
import { ChartCard } from '../components/charts/ChartCard';
import { CHART } from '../components/charts/theme';
import { SelectField } from '../components/filters/FilterBar';
import { KpiCard } from '../components/kpi/KpiCard';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/states/EmptyState';
import { ErrorState } from '../components/states/ErrorState';
import { ChartSkeleton, KpiSkeleton, TableSkeleton } from '../components/states/LoadingSkeleton';
import { DataTable } from '../components/tables/DataTable';
import type { Column } from '../components/tables/DataTable';
import { useApi } from '../hooks/useApi';
import { formatByUnit, formatSignedCurrency, metricLabel, parseValue } from '../utils/format';

const SCENARIO_LABELS: Record<string, string> = {
  uniform_replace_0_10: 'Uniform 10% replacement',
  uniform_replace_0_20: 'Uniform 20% replacement (median observed discount)',
  discount_increase_pp_0_00: 'Discount increase 0.00 pp (identity control)',
  discount_decrease_pp_0_00: 'Discount decrease 0.00 pp (identity control)',
};

function scenarioLabel(id: string): string {
  return SCENARIO_LABELS[id.replace(/\./g, '_')] ?? id;
}

/** Preferred chart metrics, intersected with what both blocks actually store. */
const PREFERRED_METRICS = [
  'contribution_profit',
  'net_revenue',
  'gross_profit',
  'modeled_cogs',
  'discount_amount',
  'cost_to_serve',
] as const;

export function Scenarios() {
  const [scenarioId, setScenarioId] = useState('uniform_replace_0.10');

  const { data, loading, error, reload } = useApi(
    () => api.scenarios({ scenario_id: scenarioId }),
    [scenarioId],
  );

  const scenarioIds = ['uniform_replace_0.10', 'uniform_replace_0.20', 'discount_increase_pp_0.00', 'discount_decrease_pp_0.00'];

  const byBlockMetric = useMemo(() => {
    const map = new Map<string, ScenarioRecord>();
    for (const r of data?.data ?? []) map.set(`${r.block}|${r.metric_name}`, r);
    return map;
  }, [data]);

  const chartMetrics = useMemo(
    () =>
      PREFERRED_METRICS.filter(
        (m) =>
          byBlockMetric.get(`baseline|${m}`)?.unit === 'CUR' &&
          byBlockMetric.get(`hypothetical|${m}`)?.unit === 'CUR' &&
          parseValue(byBlockMetric.get(`baseline|${m}`)!.metric_value) !== null,
      ),
    [byBlockMetric],
  );

  const chartData = useMemo(
    () =>
      chartMetrics.map((m) => ({
        name: metricLabel(m),
        Baseline: parseValue(byBlockMetric.get(`baseline|${m}`)!.metric_value) ?? 0,
        Hypothetical: parseValue(byBlockMetric.get(`hypothetical|${m}`)!.metric_value) ?? 0,
      })),
    [chartMetrics, byBlockMetric],
  );

  const varianceRows = useMemo(
    () => (data?.data ?? []).filter((r) => r.block === 'variance'),
    [data],
  );

  const headline = byBlockMetric.get('variance|variance_contribution_profit');

  const columns: Column<ScenarioRecord>[] = useMemo(
    () => [
      { key: 'metric', header: 'Variance metric', render: (r) => metricLabel(r.metric_name) },
      {
        key: 'value',
        header: 'Value',
        numeric: true,
        render: (r) => {
          const v = parseValue(r.metric_value);
          const formatted = formatByUnit(r.metric_value, r.unit);
          if (v === null || v === 0 || r.unit === 'Label' || r.unit === 'Flag' || r.metric_value === '') {
            return <span className={r.metric_value === '' ? 'cell-muted' : ''}>{formatted}</span>;
          }
          return <span className={v > 0 ? 'cell-positive' : 'cell-negative'}>{formatted}</span>;
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

  return (
    <div className="page">
      <PageHeader
        title="Scenario Sensitivity"
        lede="Validated TOTAL sensitivity: stored baseline beside its identical-scope hypothetical. Arithmetic sensitivity — not a forecast."
        meta={
          <>
            <span className="badge badge-info">AO-03 · Overall TOTAL</span>
            <span className="badge badge-warn">Sensitivity · not a forecast</span>
          </>
        }
      />

      <div className="caveat" role="note">
        Illustrative arithmetic sensitivity under stated assumptions — not a forecast,
        causal estimate, demand prediction, or pricing recommendation.
      </div>

      <div className="filter-bar" role="group" aria-label="Scenario filters">
        <SelectField
          id="scenario"
          label="Scenario instance"
          value={scenarioId}
          onChange={setScenarioId}
          options={scenarioIds.map((id) => ({ value: id, label: scenarioLabel(id) }))}
        />
      </div>

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
        <EmptyState
          message="No scenario rows match the selected instance."
          onClear={() => setScenarioId('uniform_replace_0.10')}
        />
      ) : (
        <>
          <div className="section">
            <div className="kpi-grid cols-3">
              <KpiCard
                label="Scenario instance"
                value={scenarioLabel(scenarioId)}
                sub={`${data.count} stored rows · 3 blocks`}
              />
              <KpiCard
                label="Variance · Contribution profit"
                value={headline ? formatSignedCurrency(headline.metric_value) : 'N/A'}
                sub="Stored variance block value"
                tone={
                  headline && (parseValue(headline.metric_value) ?? 0) < 0
                    ? 'negative'
                    : 'positive'
                }
              />
              <KpiCard
                label="Standing"
                value="Hypothetical"
                sub="Arithmetic sensitivity output"
              />
            </div>
          </div>

          <div className="section">
            <div className="section-head">
              <div>
                <h3>Baseline vs hypothetical</h3>
                <p>Stored currency metrics · grouped for direct comparison · no differences computed here</p>
              </div>
            </div>
            <ChartCard title={`${scenarioLabel(scenarioId)} — baseline vs hypothetical`} height={320}>
              <ResponsiveContainer>
                <BarChart data={chartData} margin={{ left: 8, right: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: CHART.tick, fontSize: 11 }} interval={0} angle={-12} dy={10} height={56} />
                  <YAxis
                    tick={{ fill: CHART.tick, fontSize: 12 }}
                    tickFormatter={(v: number) => `$${(v / 1_000_000).toFixed(1)}M`}
                  />
                  <Tooltip
                    formatter={(value) => [
                      formatByUnit(String(value ?? ''), 'CUR'),
                      undefined,
                    ]}
                  />
                  <Legend />
                  <Bar dataKey="Baseline" fill={CHART.navy} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Hypothetical" fill={CHART.teal} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="section">
            <div className="section-head">
              <div>
                <h3>Stored variance block</h3>
                <p>{varianceRows.length} variance rows exactly as stored — the change is reported, never recomputed</p>
              </div>
            </div>
            <DataTable
              ariaLabel="Scenario variance"
              columns={columns}
              rows={varianceRows}
              rowKey={(r) => `${r.scenario_id}-${r.block}-${r.metric_name}`}
            />
          </div>
        </>
      )}
    </div>
  );
}
