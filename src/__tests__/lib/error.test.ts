import { describe, it, expect } from 'vitest';
import { getErrorMessage } from '@/lib/error';

describe('getErrorMessage', () => {
  it('returns plain string error as-is', () => {
    expect(getErrorMessage('Simple error string')).toBe('Simple error string');
  });

  it('handles Axios error with detail string', () => {
    const error = {
      isAxiosError: true,
      response: {
        data: {
          detail: 'Unauthorized access',
        },
      },
    };
    expect(getErrorMessage(error)).toBe('Unauthorized access');
  });

  it('handles Axios error with Pydantic validation array detail', () => {
    const error = {
      isAxiosError: true,
      response: {
        data: {
          detail: [
            { loc: ['body', 'email'], msg: 'field required' },
            { loc: ['body', 'password'], msg: 'string too short' },
          ],
        },
      },
    };
    expect(getErrorMessage(error)).toBe('body -> email: field required | body -> password: string too short');
  });

  it('handles Axios error with detail object containing msg', () => {
    const error = {
      isAxiosError: true,
      response: {
        data: {
          detail: { msg: 'Token expired' },
        },
      },
    };
    expect(getErrorMessage(error)).toBe('Token expired');
  });

  it('handles Axios error with message field', () => {
    const error = {
      isAxiosError: true,
      response: {
        data: {
          message: 'Server error occurred',
        },
      },
    };
    expect(getErrorMessage(error)).toBe('Server error occurred');
  });

  it('handles standard JS Error object', () => {
    const err = new Error('Database connection failed');
    expect(getErrorMessage(err)).toBe('Database connection failed');
  });

  it('returns fallback string for unknown error', () => {
    expect(getErrorMessage(null)).toBe('An unexpected error occurred.');
    expect(getErrorMessage(12345)).toBe('An unexpected error occurred.');
  });
});
