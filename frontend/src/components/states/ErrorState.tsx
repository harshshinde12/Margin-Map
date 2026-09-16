interface ErrorStateProps {
  message?: string;
  onRetry: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="state-card" role="alert">
      <h4>Unable to load analytical data.</h4>
      <p>{message ?? 'The backend did not respond. Check that the API is running and retry.'}</p>
      <button type="button" className="btn btn-primary" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}
