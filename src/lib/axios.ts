import axios from "axios";

// Helper to generate UUID v4 compatible request ID
function generateRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "req-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 9);
}

// Base URL should NOT include /api — backend routes are /api/v1/...
// NEXT_PUBLIC_API_URL should be set to http://localhost:8000 (or production URL)
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "content-type": "application/json",
  },
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  if (!config.headers["X-Request-ID"] && !config.headers["x-request-id"]) {
    config.headers["X-Request-ID"] = generateRequestId();
  }
  return config;
});

