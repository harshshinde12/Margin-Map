/**
 * Display-only formatting helpers.
 *
 * These convert the API's verbatim string values into readable text.
 * They never create new metrics: parsing a single stored value for
 * presentation is not analysis.
 */

const usd0 = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

const usd2 = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const int = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });

function toNumber(raw: string): number | null {
  if (raw === '' || raw === null || raw === undefined) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/** Compact currency for KPI cards, e.g. $2.30M. Raw value preserved in title. */
export function formatCompactCurrency(raw: string): string {
  const n = toNumber(raw);
  if (n === null) return 'N/A';
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return usd0.format(n);
}

/** Full currency for tables and tooltips. */
export function formatCurrency(raw: string): string {
  const n = toNumber(raw);
  if (n === null) return 'N/A';
  return usd2.format(n);
}

/** Signed currency for variance values, e.g. +$45,401.37. */
export function formatSignedCurrency(raw: string): string {
  const n = toNumber(raw);
  if (n === null) return 'N/A';
  const sign = n > 0 ? '+' : n < 0 ? '−' : '';
  return `${sign}${usd2.format(Math.abs(n))}`;
}

/** Percent values are stored as rates (e.g. 24.6 means 24.6%). */
export function formatPercent(raw: string, digits = 1): string {
  const n = toNumber(raw);
  if (n === null) return 'N/A';
  return `${n.toFixed(digits)}%`;
}

/** Percentage-point deltas (PP unit). */
export function formatPercentagePoints(raw: string, digits = 1): string {
  const n = toNumber(raw);
  if (n === null) return 'N/A';
  const sign = n > 0 ? '+' : n < 0 ? '−' : '';
  return `${sign}${Math.abs(n).toFixed(digits)} pp`;
}

/** Counts: stored as numeric strings. */
export function formatCount(raw: string): string {
  const n = toNumber(raw);
  if (n === null) return 'N/A';
  return int.format(n);
}

/** Decimal ratios shown with fixed precision (DEC spec: 4dp, e.g. WAD 0.1979). */
export function formatDecimal(raw: string, digits = 4): string {
  const n = toNumber(raw);
  if (n === null) return 'N/A';
  return n.toFixed(digits);
}

/**
 * Unit-aware formatter used by tables and tooltips.
 * Empty-string values (the frozen N/A convention) render as "N/A".
 */
export function formatByUnit(raw: string, unit: string): string {
  if (raw === '') return 'N/A';
  switch (unit) {
    case 'CUR':
      return formatCurrency(raw);
    case 'PCT':
      return formatPercent(raw);
    case 'PP':
      return formatPercentagePoints(raw);
    case 'CT':
      return formatCount(raw);
    case 'DEC':
      return formatDecimal(raw);
    default:
      return raw;
  }
}

/** Human-readable label for a snake_case metric name. */
const METRIC_LABEL_OVERRIDES: Record<string, string> = {
  wad: 'WAD',
};

export function metricLabel(metricName: string): string {
  const override = METRIC_LABEL_OVERRIDES[metricName.toLowerCase()];
  if (override) return override;
  return metricName
    .split('_')
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(' ');
}

/** Parse helper exposed for chart mapping (single stored values only). */
export function parseValue(raw: string): number | null {
  return toNumber(raw);
}
