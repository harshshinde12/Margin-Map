/**
 * Centralized API client for the Margin Map read-only backend (Phase 8).
 *
 * All data access flows through this module. The base URL comes from
 * VITE_API_BASE_URL so it is never hard-coded in components.
 * An empty/unset VITE_API_BASE_URL means same-origin (production:
 * FastAPI serves the React build and /api from one origin).
 * Local development sets VITE_API_BASE_URL=http://127.0.0.1:8000.
 * The client performs no analytical computation of any kind.
 */

import type {
  BaselineMetric,
  ContributionRecord,
  HealthResponse,
  ListResponse,
  OrderReading,
  OrdersPage,
  QualityCheck,
  ScenarioRecord,
  VarianceRecord,
} from './types';

const _rawBase = (
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
).trim().replace(/\/$/, '');
/** Empty string = same-origin relative URLs (production). Set
 * VITE_API_BASE_URL=http://127.0.0.1:8000 for local two-origin dev. */
export const API_BASE_URL: string = _rawBase;

export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const query = Object.entries(params ?? {})
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
  return `${API_BASE_URL}${path}${query ? `?${query}` : ''}`;
}

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path, params));
  } catch {
    throw new ApiError(0, 'Unable to reach the Margin Map API. Start the backend and retry.');
  }
  if (!response.ok) {
    if (response.status === 400) throw new ApiError(400, 'Invalid query parameter.');
    if (response.status === 404) throw new ApiError(404, 'Requested resource does not exist.');
    throw new ApiError(response.status, 'Unable to load analytical data.');
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(response.status, 'Unable to load analytical data.');
  }
}

export type ContributionFilters = {
  band?: string;
  metric_name?: string;
  scenario_status?: string;
  basis?: string;
};

export type ScenarioFilters = {
  scenario_status?: string;
  metric_name?: string;
  scenario_id?: string;
  block?: string;
};

export type VarianceFilters = {
  band?: string;
  scenario_status?: string;
  metric_name?: string;
  scenario_id?: string;
  block?: string;
};

export type OrderFilters = {
  order_id?: string;
  discount_band?: string;
  return_status?: string;
  neg_flag?: string;
  metric_name?: string;
  limit?: number;
  offset?: number;
};

export type QualityFilters = {
  artifact?: string;
  status?: string;
  check_id?: string;
};

export const api = {
  health: () => get<HealthResponse>('/api/health'),
  baseline: (params?: { metric_name?: string }) =>
    get<ListResponse<BaselineMetric>>('/api/baseline', params),
  contribution: (params?: ContributionFilters) =>
    get<ListResponse<ContributionRecord>>('/api/contribution', params),
  scenarios: (params?: ScenarioFilters) =>
    get<ListResponse<ScenarioRecord>>('/api/scenarios', params),
  variance: (params?: VarianceFilters) =>
    get<ListResponse<VarianceRecord>>('/api/variance', params),
  orders: (params?: OrderFilters) => get<OrdersPage>('/api/orders', params),
  quality: (params?: QualityFilters) =>
    get<ListResponse<QualityCheck>>('/api/quality', params),
};

export type { OrderReading };
