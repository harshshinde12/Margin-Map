interface KpiCardProps {
  label: string;
  value: string;
  sub?: string;
  tone?: 'default' | 'positive' | 'negative';
  title?: string;
}

export function KpiCard({ label, value, sub, tone = 'default', title }: KpiCardProps) {
  return (
    <div className="kpi-card" title={title}>
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value${tone !== 'default' ? ` ${tone}` : ''}`}>{value}</div>
      {sub ? <div className="kpi-sub">{sub}</div> : null}
    </div>
  );
}
