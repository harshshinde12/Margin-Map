import { useMemo, useState } from 'react';
import { api } from '../api/client';
import type { OrderReading } from '../api/types';
import { SelectField, TextField } from '../components/filters/FilterBar';
import { PageHeader } from '../components/layout/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/states/EmptyState';
import { ErrorState } from '../components/states/ErrorState';
import { TableSkeleton } from '../components/states/LoadingSkeleton';
import { DataTable } from '../components/tables/DataTable';
import type { Column } from '../components/tables/DataTable';
import { Pagination } from '../components/tables/Pagination';
import { useApi } from '../hooks/useApi';
import { formatByUnit, metricLabel } from '../utils/format';

const BANDS = ['B0', 'B1', 'B2', 'B3', 'B4', 'B5'];
const RETURN_STATES = ['NOT_RETURNED', 'YES', 'UNKNOWN'];
const NEG_FLAGS = ['True', 'False'];
const METRICS = [
  'contribution_profit',
  'contribution_margin',
  'net_revenue',
  'gross_revenue',
  'modeled_gross_profit',
  'modeled_gross_margin',
  'cost_to_serve',
  'freight_cost',
  'quantity',
  'line_count',
  'wad',
  'revenue_realization_rate',
];
const LIMITS = [50, 100, 250, 500];

export function Orders() {
  const [orderId, setOrderId] = useState('');
  const [band, setBand] = useState('');
  const [returnStatus, setReturnStatus] = useState('');
  const [negFlag, setNegFlag] = useState('');
  const [metric, setMetric] = useState('');
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [applied, setApplied] = useState({
    order_id: '',
    band: '',
    returnStatus: '',
    negFlag: '',
    metric: '',
  });

  const { data, loading, error, reload } = useApi(
    () =>
      api.orders({
        order_id: applied.order_id || undefined,
        discount_band: applied.band || undefined,
        return_status: applied.returnStatus || undefined,
        neg_flag: applied.negFlag || undefined,
        metric_name: applied.metric || undefined,
        limit,
        offset,
      }),
    [applied, limit, offset],
  );

  const apply = () => {
    setOffset(0);
    setApplied({ order_id: orderId.trim(), band, returnStatus, negFlag, metric });
  };

  const reset = () => {
    setOrderId('');
    setBand('');
    setReturnStatus('');
    setNegFlag('');
    setMetric('');
    setLimit(50);
    setOffset(0);
    setApplied({ order_id: '', band: '', returnStatus: '', negFlag: '', metric: '' });
  };

  const hasActive =
    applied.order_id !== '' ||
    applied.band !== '' ||
    applied.returnStatus !== '' ||
    applied.negFlag !== '' ||
    applied.metric !== '';

  const rows = useMemo(() => data?.data ?? [], [data]);
  const hasNext = (data?.count ?? 0) === limit;

  const columns: Column<OrderReading>[] = useMemo(
    () => [
      { key: 'order', header: 'Order', render: (r) => r.order_id },
      { key: 'band', header: 'Band', render: (r) => r.discount_band },
      { key: 'metric', header: 'Metric', render: (r) => metricLabel(r.metric_name) },
      {
        key: 'value',
        header: 'Value',
        numeric: true,
        render: (r) => formatByUnit(r.metric_value, r.unit),
      },
      { key: 'unit', header: 'Unit', render: (r) => r.unit },
      { key: 'return', header: 'Return', render: (r) => r.return_status },
      {
        key: 'neg',
        header: 'Neg.',
        render: (r) =>
          r.neg_flag === 'True' ? (
            <span className="badge badge-warn">True</span>
          ) : (
            <span className="cell-muted">False</span>
          ),
      },
      {
        key: 'ambiguity',
        header: 'Ambiguity',
        render: (r) =>
          r.ambiguity_note ? (
            <span className="truncate" style={{ display: 'inline-block' }} title={r.ambiguity_note}>
              {r.ambiguity_note}
            </span>
          ) : (
            <span className="cell-muted">—</span>
          ),
      },
    ],
    [],
  );

  return (
    <div className="page">
      <PageHeader
        title="Order-Level Readings"
        lede="Observed order-grain context supporting — never replacing — band readings. Single observations; no hypothetical detail."
        meta={
          <>
            <span className="badge badge-info">AO-05 · Order grain</span>
            <span className="badge badge-neutral">5,009 orders · observed only</span>
          </>
        }
      />

      <div className="filter-bar" role="group" aria-label="Order filters">
        <TextField id="o-id" label="Order ID" value={orderId} placeholder="e.g. CA-2014-100006" onChange={setOrderId} />
        <SelectField
          id="o-band"
          label="Discount band"
          value={band}
          onChange={setBand}
          options={BANDS.map((b) => ({ value: b, label: b }))}
        />
        <SelectField
          id="o-return"
          label="Return status"
          value={returnStatus}
          onChange={setReturnStatus}
          options={RETURN_STATES.map((s) => ({ value: s, label: s }))}
        />
        <SelectField
          id="o-neg"
          label="Negative flag"
          value={negFlag}
          onChange={setNegFlag}
          options={NEG_FLAGS.map((f) => ({ value: f, label: f }))}
        />
        <SelectField
          id="o-metric"
          label="Metric"
          value={metric}
          onChange={setMetric}
          options={METRICS.map((m) => ({ value: m, label: metricLabel(m) }))}
        />
        <button type="button" className="btn btn-primary" onClick={apply}>
          Apply
        </button>
        <button type="button" className="btn" onClick={reset}>
          Reset
        </button>
      </div>

      {hasActive ? (
        <div className="active-filters" aria-live="polite">
          Active filters:
          {applied.order_id ? <span className="chip">Order: {applied.order_id}</span> : null}
          {applied.band ? <span className="chip">Band: {applied.band}</span> : null}
          {applied.returnStatus ? <span className="chip">Return: {applied.returnStatus}</span> : null}
          {applied.negFlag ? <span className="chip">Neg: {applied.negFlag}</span> : null}
          {applied.metric ? <span className="chip">Metric: {metricLabel(applied.metric)}</span> : null}
        </div>
      ) : null}

      <div className="section">
        <div className="section-head">
          <div>
            <h3>Order readings</h3>
            <p>One row per (order, metric) · values formatted by unit · never aggregated</p>
          </div>
          <StatusBadge status={loading ? 'Loading' : `${rows.length} rows`} />
        </div>
        {loading ? (
          <TableSkeleton rows={10} />
        ) : error || !data ? (
          <ErrorState message={error ?? undefined} onRetry={reload} />
        ) : rows.length === 0 ? (
          <EmptyState message="No order readings match the selected filters." onClear={reset} />
        ) : (
          <>
            <DataTable
              ariaLabel="Order readings"
              columns={columns}
              rows={rows}
              rowKey={(r, i) => `${r.order_id}-${r.metric_name}-${i}`}
            />
            <Pagination
              offset={offset}
              limit={limit}
              pageCount={rows.length}
              hasNext={hasNext}
              onPrev={() => setOffset((o) => Math.max(0, o - limit))}
              onNext={() => setOffset((o) => o + limit)}
              limitOptions={LIMITS}
              onLimitChange={(n) => {
                setLimit(n);
                setOffset(0);
              }}
              rangeLabel={`Rows ${offset + 1}–${offset + rows.length} · page size ${limit} (max 500)`}
            />
          </>
        )}
      </div>
    </div>
  );
}
