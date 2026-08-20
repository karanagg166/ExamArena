import { describe, it, expect } from 'vitest';
import {
  formatDateTimeIST,
  formatDateIST,
  formatTimeIST,
  toISTInputString,
  fromISTInputStringToISO,
} from '@/lib/date';

describe('IST Date Utilities (src/lib/date.ts)', () => {
  it('formats UTC ISO timestamp to IST datetime string', () => {
    // 2026-09-15T10:00:00Z -> 10:00 UTC = 15:30 IST
    const iso = '2026-09-15T10:00:00Z';
    const result = formatDateTimeIST(iso, { includeTimezoneSuffix: true });
    expect(result).toContain('15 Sep 2026');
    expect(result).toMatch(/3:30\s*(pm|PM)/i);
    expect(result).toContain('IST');
  });

  it('formats date only in IST', () => {
    const iso = '2026-09-15T20:00:00Z'; // 20:00 UTC = 01:30 Next Day (16 Sep) in IST
    const result = formatDateIST(iso);
    expect(result).toBe('16 Sep 2026');
  });

  it('formats time only in IST', () => {
    const iso = '2026-09-15T10:00:00Z'; // 10:00 UTC = 3:30 PM IST
    const result = formatTimeIST(iso);
    expect(result).toMatch(/3:30\s*(pm|PM)\s*IST/i);
  });

  it('handles null, undefined, or invalid date inputs gracefully', () => {
    expect(formatDateTimeIST(null)).toBe('—');
    expect(formatDateTimeIST(undefined)).toBe('—');
    expect(formatDateTimeIST('invalid-date')).toBe('—');
    expect(toISTInputString(null)).toBe('');
    expect(fromISTInputStringToISO('')).toBe('');
  });

  it('converts UTC ISO to datetime-local IST input string', () => {
    const iso = '2026-08-20T04:30:00.000Z'; // 04:30 UTC = 10:00 IST
    const inputStr = toISTInputString(iso);
    expect(inputStr).toBe('2026-08-20T10:00');
  });

  it('converts datetime-local IST input string to UTC ISO', () => {
    const inputVal = '2026-08-20T10:00'; // 10:00 IST = 04:30 UTC
    const isoStr = fromISTInputStringToISO(inputVal);
    expect(isoStr).toBe('2026-08-20T04:30:00.000Z');
  });
});
