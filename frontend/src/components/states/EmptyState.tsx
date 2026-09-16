interface EmptyStateProps {
  message?: string;
  onClear?: () => void;
}

export function EmptyState({ message, onClear }: EmptyStateProps) {
  return (
    <div className="state-card">
      <h4>No records found.</h4>
      <p>{message ?? 'No records match the selected filters.'}</p>
      {onClear ? (
        <button type="button" className="btn" onClick={onClear}>
          Clear Filters
        </button>
      ) : null}
    </div>
  );
}
