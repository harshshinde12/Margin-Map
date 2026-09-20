import { describe, expect, it } from 'vitest';
import {
  formatByUnit,
  formatCompactCurrency,
  formatCount,
  formatCurrency,
  formatDecimal,
  formatPercent,
  formatPercentagePoints,
  metricLabel,
  parseValue,
} from './format';

describe('display formatting (presentation only, no new metrics)', () => {
  it('formats compact currency for KPI cards', () => {
    expect(formatCompactCurrency('2297200.8603000003')).toBe('$2.30M');
    expect(formatCompactCurrency('565116.9418299999')).toBe('$565.1K');
    expect(formatCompactCurrency('')).toBe('N/A');
  });

  it('formats full currency for tables', () => {
    expect(formatCurrency('565116.9418299999')).toBe('$565,116.94');
    expect(formatCurrency('')).toBe('N/A');
  });

  it('formats percents and percentage points', () => {
    expect(formatPercent('24.600240736293262')).toBe('24.6%');
    expect(formatPercentagePoints('7.18798060226743')).toBe('+7.2 pp');
    expect(formatPercentagePoints('-1.5')).toBe('−1.5 pp');
  });

  it('formats counts without decimals', () => {
    expect(formatCount('5009')).toBe('5,009');
  });

  it('renders the frozen empty-string N/A convention as N/A', () => {
    expect(formatByUnit('', 'CUR')).toBe('N/A');
    expect(formatByUnit('', 'Label')).toBe('N/A');
  });

  it('dispatches formatting by unit', () => {
    expect(formatByUnit('565116.9418299999', 'CUR')).toBe('$565,116.94');
    expect(formatByUnit('24.6', 'PCT')).toBe('24.6%');
    expect(formatByUnit('5009', 'CT')).toBe('5,009');
    expect(formatByUnit('PASS', 'Label')).toBe('PASS');
  });

  it('humanizes metric names without changing values', () => {
    expect(metricLabel('contribution_profit')).toBe('Contribution Profit');
    expect(metricLabel('variance_contribution_profit')).toBe('Variance Contribution Profit');
    expect(metricLabel('wad')).toBe('WAD');
  });

  it('formats decimal ratios at 4dp per display spec (WAD)', () => {
    expect(formatDecimal('0.19788653436077944')).toBe('0.1979');
    expect(formatByUnit('0.19788653436077944', 'DEC')).toBe('0.1979');
  });

  it('parses single stored values, rejecting non-numeric labels', () => {
    expect(parseValue('565116.94')).toBeCloseTo(565116.94);
    expect(parseValue('')).toBeNull();
    expect(parseValue('ALL_SOURCES_ELIGIBLE')).toBeNull();
  });
});
