/**
 * Utility functions for Indian Standard Time (IST, UTC+5:30) formatting and parsing.
 */

export const IST_TIMEZONE = "Asia/Kolkata";
export const IST_LOCALE = "en-IN";

const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/**
 * Helper to get date parts in IST
 */
function getISTDateParts(date: Date) {
  // Convert UTC timestamp to IST timestamp (+05:30)
  const istOffsetMinutes = 330;
  const istTime = new Date(date.getTime() + istOffsetMinutes * 60 * 1000);

  const year = istTime.getUTCFullYear();
  const monthIdx = istTime.getUTCMonth();
  const day = istTime.getUTCDate();
  const rawHours = istTime.getUTCHours();
  const minutes = istTime.getUTCMinutes();
  const seconds = istTime.getUTCSeconds();

  const isPM = rawHours >= 12;
  const hours12 = rawHours % 12 === 0 ? 12 : rawHours % 12;
  const ampm = isPM ? "PM" : "AM";
  const minutesPadded = String(minutes).padStart(2, "0");
  const secondsPadded = String(seconds).padStart(2, "0");

  return {
    year,
    monthIdx,
    monthShort: MONTHS_SHORT[monthIdx],
    day,
    hours12,
    minutesPadded,
    secondsPadded,
    ampm,
    rawHours,
  };
}

/**
 * Formats an ISO date/timestamp into a readable IST string.
 * Example output: "15 Sep 2026, 3:30 PM IST" or "15 Sep 2026"
 */
export function formatDateTimeIST(
  dateInput: string | number | Date | null | undefined,
  options?: {
    includeTime?: boolean;
    includeSeconds?: boolean;
    includeTimezoneSuffix?: boolean;
  }
): string {
  if (!dateInput) return "—";
  const date = typeof dateInput === "object" ? dateInput : new Date(dateInput);
  if (isNaN(date.getTime())) return "—";

  const includeTime = options?.includeTime ?? true;
  const includeTimezoneSuffix = options?.includeTimezoneSuffix ?? true;
  const includeSeconds = options?.includeSeconds ?? false;

  const { day, monthShort, year, hours12, minutesPadded, secondsPadded, ampm } = getISTDateParts(date);

  if (!includeTime) {
    return `${day} ${monthShort} ${year}`;
  }

  const timeStr = includeSeconds
    ? `${hours12}:${minutesPadded}:${secondsPadded} ${ampm}`
    : `${hours12}:${minutesPadded} ${ampm}`;

  return includeTimezoneSuffix
    ? `${day} ${monthShort} ${year}, ${timeStr} IST`
    : `${day} ${monthShort} ${year}, ${timeStr}`;
}

/**
 * Formats a date only in IST (e.g., "15 Sep 2026").
 */
export function formatDateIST(dateInput: string | number | Date | null | undefined): string {
  return formatDateTimeIST(dateInput, { includeTime: false, includeTimezoneSuffix: false });
}

/**
 * Formats a time only in IST (e.g., "3:30 PM IST").
 */
export function formatTimeIST(dateInput: string | number | Date | null | undefined): string {
  if (!dateInput) return "—";
  const date = typeof dateInput === "object" ? dateInput : new Date(dateInput);
  if (isNaN(date.getTime())) return "—";

  const { hours12, minutesPadded, ampm } = getISTDateParts(date);
  return `${hours12}:${minutesPadded} ${ampm} IST`;
}

/**
 * Converts an ISO string or Date to `YYYY-MM-DDTHH:mm` representing IST for `<input type="datetime-local">`.
 */
export function toISTInputString(dateInput: string | number | Date | null | undefined): string {
  if (!dateInput) return "";
  const date = typeof dateInput === "object" ? dateInput : new Date(dateInput);
  if (isNaN(date.getTime())) return "";

  // Convert to IST offset (+05:30)
  const istOffsetMinutes = 330;
  const istTime = new Date(date.getTime() + istOffsetMinutes * 60 * 1000);

  const year = istTime.getUTCFullYear();
  const month = String(istTime.getUTCMonth() + 1).padStart(2, "0");
  const day = String(istTime.getUTCDate()).padStart(2, "0");
  const hours = String(istTime.getUTCHours()).padStart(2, "0");
  const minutes = String(istTime.getUTCMinutes()).padStart(2, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Converts a `YYYY-MM-DDTHH:mm` string from datetime-local input (assumed to be in IST) to an ISO UTC string.
 */
export function fromISTInputStringToISO(inputVal: string): string {
  if (!inputVal) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(inputVal);
  if (!match) {
    const d = new Date(inputVal);
    return isNaN(d.getTime()) ? "" : d.toISOString();
  }
  // Construct ISO string with +05:30 offset
  const isoWithTz = `${inputVal}:00+05:30`;
  const d = new Date(isoWithTz);
  return isNaN(d.getTime()) ? "" : d.toISOString();
}
