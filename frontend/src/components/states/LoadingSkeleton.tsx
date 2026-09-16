export function KpiSkeleton() {
  return (
    <div className="kpi-grid" aria-label="Loading indicators" aria-busy="true">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skeleton skeleton-kpi" />
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return <div className="skeleton skeleton-chart" aria-label="Loading chart" aria-busy="true" />;
}

export function TableSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div aria-label="Loading table" aria-busy="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton skeleton-table-row" />
      ))}
    </div>
  );
}
