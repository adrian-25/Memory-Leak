/**
 * MemoryLeak API client.
 *
 * Thin wrapper over fetch that:
 * - Reads the base URL from the environment variable NEXT_PUBLIC_API_BASE_URL
 * - Throws typed ApiError on non-2xx responses
 * - Provides typed methods for each endpoint group
 *
 * Phase 1: health() method only.
 * Additional methods are added as API endpoints are implemented.
 */

import type { ApiError, HealthResponse } from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // Health is at root, not /api/v1
  const url = path.startsWith("/health")
    ? (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(
        "/api/v1",
        ""
      ) + path
    : `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorBody: ApiError | null = null;
    try {
      errorBody = await response.json();
    } catch {
      // Response body is not JSON
    }
    throw new ApiClientError(
      response.status,
      errorBody?.error?.message ?? `HTTP ${response.status}`,
      errorBody
    );
  }

  return response.json() as Promise<T>;
}

// ─── Typed error class ────────────────────────────────────────────────────────

export class ApiClientError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body: ApiError | null = null
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

// ─── Health ───────────────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

// ─── Default export ───────────────────────────────────────────────────────────

const apiClient = {
  health: fetchHealth,
};

export default apiClient;
