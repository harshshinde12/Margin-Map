import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { StatusBadge } from './StatusBadge';
import { KpiCard } from '../kpi/KpiCard';
import { EmptyState } from '../states/EmptyState';
import { ErrorState } from '../states/ErrorState';
import { Pagination } from '../tables/Pagination';

describe('core components', () => {
  it('renders KPI label and value', () => {
    render(<KpiCard label="Net Revenue" value="$2.30M" sub="Baseline · TOTAL" />);
    expect(screen.getByText('Net Revenue')).toBeInTheDocument();
    expect(screen.getByText('$2.30M')).toBeInTheDocument();
  });

  it('renders error state with retry', () => {
    const onRetry = vi.fn();
    render(<ErrorState message="boom" onRetry={onRetry} />);
    expect(screen.getByText('Unable to load analytical data.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders empty state distinctly from errors, with clear action', () => {
    const onClear = vi.fn();
    render(<EmptyState message="No records match." onClear={onClear} />);
    expect(screen.getByText('No records match.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Clear Filters' }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it('maps PASS status to the pass badge tone', () => {
    render(<StatusBadge status="PASS" />);
    expect(screen.getByText('PASS').className).toContain('badge-pass');
  });

  it('disables previous on the first page and next at the end', () => {
    const noop = () => undefined;
    const { rerender } = render(
      <Pagination
        offset={0}
        limit={50}
        pageCount={50}
        hasNext
        onPrev={noop}
        onNext={noop}
        rangeLabel="Rows 1–50"
      />,
    );
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Next' })).not.toBeDisabled();

    rerender(
      <Pagination
        offset={100}
        limit={50}
        pageCount={10}
        hasNext={false}
        onPrev={noop}
        onNext={noop}
        rangeLabel="Rows 101–110"
      />,
    );
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
  });
});
