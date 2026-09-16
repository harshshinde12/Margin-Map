import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, api } from './client';

function mockFetch(handler: (url: string) => Response) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => handler(url)),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('centralized API client', () => {
  it('calls the baseline endpoint and returns parsed JSON', async () => {
    mockFetch(
      () =>
        new Response(JSON.stringify({ data: [{ metric_name: 'net_revenue' }], count: 1 }), {
          status: 200,
        }),
    );
    const body = await api.baseline();
    expect(body.count).toBe(1);
    expect(vi.mocked(fetch).mock.calls[0][0] as string).toContain('/api/baseline');
  });

  it('serializes supported filters as query parameters', async () => {
    mockFetch(() => new Response(JSON.stringify({ data: [], count: 0 }), { status: 200 }));
    await api.contribution({ band: 'B2', metric_name: 'contribution_profit' });
    const url = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(url).toContain('band=B2');
    expect(url).toContain('metric_name=contribution_profit');
  });

  it('maps network failures to a friendly ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('failed');
      }),
    );
    await expect(api.health()).rejects.toMatchObject({ status: 0 });
    await expect(api.health()).rejects.toBeInstanceOf(ApiError);
  });

  it('maps HTTP 400 and 404 to typed errors without raw internals', async () => {
    mockFetch(() => new Response('{}', { status: 400 }));
    await expect(api.orders({ limit: 501 })).rejects.toMatchObject({ status: 400 });
    mockFetch(() => new Response('{}', { status: 404 }));
    await expect(api.baseline()).rejects.toMatchObject({ status: 404 });
  });

  it('maps invalid JSON to a generic load error', async () => {
    mockFetch(() => new Response('not-json{', { status: 200 }));
    await expect(api.quality()).rejects.toBeInstanceOf(ApiError);
  });
});
