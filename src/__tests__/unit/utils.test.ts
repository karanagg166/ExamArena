import { describe, it, expect } from 'vitest';
import {
  isValidEmail,
  isValidPhoneNo,
  isValidPincode,
  sanitizePincode,
  sanitizePhoneNo,
  sanitizeAlpha,
  sanitizeNumber,
  validateEmailField,
  validatePhoneField,
  validatePincodeField,
  validateNameField,
  cn,
} from '@/lib/utils';

describe('Unit: Utilities & Validation (FU1-FU17)', () => {
  describe('Email validation', () => {
    it('FU1: validates standard email format', () => {
      expect(isValidEmail('user@example.com')).toBe(true);
      expect(isValidEmail('john.doe+test@domain.co.in')).toBe(true);
    });

    it('FU2: rejects email without @ symbol', () => {
      expect(isValidEmail('testexample.com')).toBe(false);
    });

    it('FU3: rejects email without domain', () => {
      expect(isValidEmail('test@')).toBe(false);
      expect(isValidEmail('@example.com')).toBe(false);
    });

    it('FU4: allows empty string for optional email fields', () => {
      expect(isValidEmail('')).toBe(true);
      expect(isValidEmail('   ')).toBe(true);
    });

    it('validateEmailField requires email when required=true', () => {
      expect(validateEmailField('', true)).toBe('Email is required');
      expect(validateEmailField('invalid-email', false)).toContain('Please enter a valid email');
      expect(validateEmailField('valid@example.com', true)).toBeUndefined();
    });
  });

  describe('Phone validation and sanitization', () => {
    it('FU5: validates +91 10-digit Indian phone numbers', () => {
      expect(isValidPhoneNo('+919876543210')).toBe(true);
    });

    it('FU6: rejects short phone numbers', () => {
      expect(isValidPhoneNo('+9198765432')).toBe(false);
    });

    it('FU7: rejects phone numbers missing +91', () => {
      expect(isValidPhoneNo('9876543210')).toBe(false);
    });

    it('FU12: sanitizePhoneNo prepends +91 to 10-digit numbers', () => {
      expect(sanitizePhoneNo('9876543210')).toBe('+919876543210');
    });

    it('FU13: sanitizePhoneNo preserves and normalizes +91', () => {
      expect(sanitizePhoneNo('+91 9876543210')).toBe('+919876543210');
      expect(sanitizePhoneNo('+919876543210')).toBe('+919876543210');
    });

    it('validatePhoneField gives clear feedback for required and format', () => {
      expect(validatePhoneField('', true)).toBe('Phone number is required');
      expect(validatePhoneField('1234', false)).toContain('must start with +91');
      expect(validatePhoneField('+919876543210', true)).toBeUndefined();
    });
  });

  describe('Pincode validation and sanitization', () => {
    it('FU8: validates 6-digit pincode', () => {
      expect(isValidPincode('110001')).toBe(true);
      expect(isValidPincode('560001')).toBe(true);
    });

    it('FU9: rejects 5-digit pincode', () => {
      expect(isValidPincode('11000')).toBe(false);
    });

    it('FU10: rejects alphanumeric pincode', () => {
      expect(isValidPincode('11000A')).toBe(false);
    });

    it('FU11: sanitizePincode strips non-digits and truncates to 6 digits', () => {
      expect(sanitizePincode('110-001-abc')).toBe('110001');
      expect(sanitizePincode('11000199999')).toBe('110001');
    });

    it('validatePincodeField returns clear messages', () => {
      expect(validatePincodeField('', true)).toBe('Pincode is required');
      expect(validatePincodeField('1234', false)).toBe('Pincode must be exactly 6 digits');
      expect(validatePincodeField('110001', true)).toBeUndefined();
    });
  });

  describe('Name & Alpha validation', () => {
    it('FU14: sanitizeAlpha strips numbers and special symbols', () => {
      expect(sanitizeAlpha('John Doe 123!')).toBe('John Doe ');
    });

    it('sanitizeNumber strips non-digit characters', () => {
      expect(sanitizeNumber('abc 123 xyz 456')).toBe('123456');
    });

    it('FU15: validateNameField rejects short names', () => {
      expect(validateNameField('', 'First Name', true)).toBe('First Name is required');
      expect(validateNameField('A', 'Name', false)).toBe('Name must be at least 2 characters');
    });

    it('FU16: validateNameField accepts valid names', () => {
      expect(validateNameField('Principal Sharma', 'Name', true)).toBeUndefined();
    });
  });

  describe('Classnames utility (cn)', () => {
    it('FU17: merges class names properly with tailwind-merge', () => {
      const result = cn('p-4 text-red-500', 'p-6 text-blue-500');
      expect(result).toBe('p-6 text-blue-500');
    });
  });
});
