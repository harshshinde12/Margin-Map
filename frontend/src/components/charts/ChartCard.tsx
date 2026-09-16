interface ChartCardProps {
  title: string;
  note?: string;
  height?: number;
  children: React.ReactNode;
}

export function ChartCard({ title, note, height = 300, children }: ChartCardProps) {
  return (
    <div className="card chart-card">
      <h4>{title}</h4>
      {note ? <p className="chart-note">{note}</p> : null}
      <div style={{ width: '100%', height }} role="img" aria-label={title}>
        {children}
      </div>
    </div>
  );
}
