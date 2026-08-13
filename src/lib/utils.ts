import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import React from "react";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Checks if key pressed is a navigation/control key (Backspace, Tab, Delete, Arrows, Cmd/Ctrl combos)
 */
export function isControlKey(e: React.KeyboardEvent): boolean {
  if (
    e.key === "Backspace" ||
    e.key === "Tab" ||
    e.key === "Enter" ||
    e.key === "Delete" ||
    e.key === "Escape" ||
    e.key.startsWith("Arrow") ||
    e.key === "Home" ||
    e.key === "End"
  ) {
    return true;
  }
  if (e.metaKey || e.ctrlKey) {
    return true;
  }
  return false;
}

/**
 * Keystroke handler for Pincodes and Digits-only fields.
 * Blocks any key that isn't a digit (0-9).
 */
export function blockNonDigits(e: React.KeyboardEvent) {
  if (isControlKey(e)) return;
  if (!/^\d$/.test(e.key)) {
    e.preventDefault();
  }
}

/**
 * Keystroke handler for Phone numbers.
 * Allows digits, '+', '-', '(', ')', and spaces. Blocks all alphabets and special chars.
 */
export function blockNonPhone(e: React.KeyboardEvent) {
  if (isControlKey(e)) return;
  if (!/^[\d\s()+-]$/.test(e.key)) {
    e.preventDefault();
  }
}

/**
 * Keystroke handler for Names / Alphabetic text.
 * Allows letters (a-z, A-Z), spaces, hyphens, and apostrophes. Blocks digits.
 */
export function blockNonAlpha(e: React.KeyboardEvent) {
  if (isControlKey(e)) return;
  if (!/^[a-zA-Z\s.'-]$/.test(e.key)) {
    e.preventDefault();
  }
}

/**
 * Sanitizers for onChange paste/input fallback
 */
export function sanitizePincode(value: string): string {
  return value.replace(/\D/g, "").slice(0, 6);
}

export function sanitizePhoneNo(value: string): string {
  const hasPlus = value.startsWith("+");
  const cleaned = value.replace(/[^\d\s()-]/g, "");
  return hasPlus ? `+${cleaned.replace(/^\+/, "")}` : cleaned;
}

export function sanitizeAlpha(value: string): string {
  return value.replace(/[^a-zA-Z\s.'-]/g, "");
}

export function sanitizeNumber(value: string): string {
  return value.replace(/\D/g, "");
}

/**
 * Validation Helpers
 */
export function isValidEmail(email: string): boolean {
  if (!email || !email.trim()) return true;
  return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email.trim());
}

export function isValidPhoneNo(phone: string): boolean {
  if (!phone || !phone.trim()) return true;
  const digitsOnly = phone.replace(/\D/g, "");
  return digitsOnly.length >= 10 && digitsOnly.length <= 15;
}

export function isValidPincode(pincode: string): boolean {
  if (!pincode || !pincode.trim()) return true;
  return /^\d{6}$/.test(pincode.trim());
}

export function validateEmailField(email: string, required = false): string | undefined {
  if (required && !email.trim()) {
    return "Email is required";
  }
  if (email.trim() && !isValidEmail(email)) {
    return "Please enter a valid email address (e.g. user@example.com)";
  }
  return undefined;
}

export function validatePhoneField(phone: string, required = false): string | undefined {
  if (required && !phone.trim()) {
    return "Phone number is required";
  }
  if (phone.trim() && !isValidPhoneNo(phone)) {
    return "Phone number must contain between 10 and 15 digits";
  }
  return undefined;
}

export function validatePincodeField(pincode: string, required = false): string | undefined {
  if (required && !pincode.trim()) {
    return "Pincode is required";
  }
  if (pincode.trim() && !isValidPincode(pincode)) {
    return "Pincode must be exactly 6 digits";
  }
  return undefined;
}

export function validateNameField(name: string, label = "Name", required = false): string | undefined {
  if (required && !name.trim()) {
    return `${label} is required`;
  }
  if (name.trim() && name.trim().length < 2) {
    return `${label} must be at least 2 characters`;
  }
  return undefined;
}

