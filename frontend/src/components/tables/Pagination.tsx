interface PaginationProps {
  offset: number;
  limit: number;
  pageCount: number;
  hasNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  limitOptions?: number[];
  onLimitChange?: (limit: number) => void;
  rangeLabel: string;
}

export function Pagination({
  offset,
  limit,
  pageCount,
  hasNext,
  onPrev,
  onNext,
  limitOptions,
  onLimitChange,
  rangeLabel,
}: PaginationProps) {
  const page = Math.floor(offset / limit) + 1;
  return (
    <div className="pagination">
      <span>{rangeLabel}</span>
      <div className="pager-controls">
        {limitOptions && onLimitChange ? (
          <label>
            Rows{' '}
            <select
              aria-label="Rows per page"
              value={limit}
              onChange={(e) => onLimitChange(Number(e.target.value))}
              style={{ font: 'inherit', padding: '4px 6px', borderRadius: 6 }}
            >
              {limitOptions.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <button type="button" className="btn" onClick={onPrev} disabled={offset === 0}>
          Previous
        </button>
        <span aria-live="polite">
          Page {page}
          {pageCount > 0 ? ` · ${pageCount} rows` : ''}
        </span>
        <button type="button" className="btn" onClick={onNext} disabled={!hasNext}>
          Next
        </button>
      </div>
    </div>
  );
}
