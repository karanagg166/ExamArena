import axios from "axios";

// Base URL should NOT include /api — backend routes are /api/v1/...
// NEXT_PUBLIC_API_URL should be set to http://localhost:8000 (or production URL)
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "content-type": "application/json",
  },
  withCredentials: true,
});
