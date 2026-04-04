import type { AxiosError } from "axios";

/**
 * Parses an error object (likely from Axios/FastAPI) and returns a human-readable string.
 * Handles:
 * 1. Simple strings
 * 2. FastAPI validation error lists (Pydantic)
 * 3. Generic Error objects
 * 4. Fallback messages
 */
export function getErrorMessage(error: unknown): string {
  if (typeof error === "string") return error;

  // Handle Axios Error
  const axiosError = error as AxiosError<any>;
  if (axiosError?.response?.data) {
    const data = axiosError.response.data;

    // Handle "detail" field (common in FastAPI)
    if (data.detail) {
      if (typeof data.detail === "string") return data.detail;
      
      // If detail is an array (Pydantic validation errors)
      if (Array.isArray(data.detail)) {
        return data.detail
          .map((err: any) => {
            const loc = err.loc ? `${err.loc.join(" -> ")}: ` : "";
            return `${loc}${err.msg}`;
          })
          .join(" | ");
      }

      // If detail is an object with a message
      if (typeof data.detail === "object" && data.detail.msg) {
        return data.detail.msg;
      }
      
      // Just stringify if it's an object we don't recognize
      return JSON.stringify(data.detail);
    }

    // Handle other common error fields
    if (data.message) return data.message;
    if (data.error) return typeof data.error === "string" ? data.error : JSON.stringify(data.error);
  }

  // Handle standard Error object
  if (error instanceof Error) return error.message;

  return "An unexpected error occurred.";
}
