interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.trim().toUpperCase();
  const tone =
    normalized === 'PASS'
      ? 'badge-pass'
      : normalized === 'WARNING' || normalized === 'WARN'
        ? 'badge-warn'
        : normalized === 'N/A' || normalized === ''
          ? 'badge-warn'
          : 'badge-neutral';
  return <span className={`badge ${tone}`}>{status === '' ? 'N/A' : status}</span>;
}
