import { describe, it, expect } from "vitest";
import {
  isValidPhoneNo,
  sanitizePhoneNo,
  validatePhoneField,
} from "@/lib/utils";

describe("Phone validation utils", () => {
  it("should validate valid +91 Indian phone numbers", () => {
    expect(isValidPhoneNo("+919876543210")).toBe(true);
    expect(isValidPhoneNo("+918123456789")).toBe(true);
    expect(isValidPhoneNo("+917000000000")).toBe(true);
  });

  it("should reject invalid phone numbers", () => {
    expect(isValidPhoneNo("9876543210")).toBe(false); // missing +91
    expect(isValidPhoneNo("+91987654321")).toBe(false); // 9 digits
    expect(isValidPhoneNo("+9198765432100")).toBe(false); // 11 digits
    expect(isValidPhoneNo("+19876543210")).toBe(false); // not +91
    expect(isValidPhoneNo("+91abcdefghij")).toBe(false);
  });

  it("should sanitize phone inputs properly", () => {
    expect(sanitizePhoneNo("9876543210")).toBe("+919876543210");
    expect(sanitizePhoneNo("+91 9876543210")).toBe("+919876543210");
    expect(sanitizePhoneNo("+91-9876-543210")).toBe("+919876543210");
    expect(sanitizePhoneNo("+91987654321012345")).toBe("+919876543210"); // caps to 10 digits
  });

  it("validatePhoneField should give clear error messages", () => {
    expect(validatePhoneField("", true)).toBe("Phone number is required");
    expect(validatePhoneField("12345", true)).toContain("must start with +91");
    expect(validatePhoneField("+919876543210", true)).toBeUndefined();
  });
});
