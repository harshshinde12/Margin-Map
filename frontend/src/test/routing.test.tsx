import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../App';

const BASELINE = {
  data: [
    {
      output_name: 'Baseline performance summary (TOTAL)',
      scenario_status: 'OBSERVED BASELINE',
      grain: 'TOTAL',
      source_artifact: 'order_margin_map_phase2.csv',
      metric_name: 'net_revenue',
      metric_value: '2297200.8603000003',
      unit: 'CUR',
      definition_ref: 'Net revenue',
      limitation: 'Authoritative',
    },
    {
      output_name: 'Baseline performance summary (TOTAL)',
      scenario_status: 'OBSERVED BASELINE',
      grain: 'TOTAL',
      source_artifact: 'x',
      metric_name: 'contribution_profit',
      metric_value: '565116.9418299999',
      unit: 'CUR',
      definition_ref: 'Contribution profit',
      limitation: 'Authoritative',
    },
  ],
  count: 2,
};

function mockApi() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (rawUrl: string) => {
      const url = String(rawUrl);
      if (url.includes('/api/health'))
        return new Response(JSON.stringify({ status: 'ok', database: 'connected', read_only: true }), {
          status: 200,
        });
      if (url.includes('/api/baseline'))
        return new Response(JSON.stringify(BASELINE), { status: 200 });
      return new Response(JSON.stringify({ data: [], count: 0 }), { status: 200 });
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe('routing and API response rendering', () => {
  it('redirects / to /executive and renders backend values', async () => {
    mockApi();
    renderAt('/');
    await waitFor(() => expect(screen.getByText('Executive Profitability Overview')).toBeInTheDocument());
    // Verbatim backend value rendered through the KPI card.
    await waitFor(() => expect(screen.getByText('$2.30M')).toBeInTheDocument());
  });

  it('shows a professional 404 for unknown routes', async () => {
    mockApi();
    renderAt('/does-not-exist');
    await waitFor(() => expect(screen.getByText('Page not found.')).toBeInTheDocument());
  });

  it('renders all six navigation entries', async () => {
    mockApi();
    renderAt('/executive');
    for (const label of ['Executive', 'Discount Bands', 'Scenarios', 'Variance', 'Orders', 'Data Quality']) {
      expect(await screen.findByText(label)).toBeInTheDocument();
    }
  });
});
