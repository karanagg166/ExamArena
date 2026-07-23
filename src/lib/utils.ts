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
