/**
 * TypeScript types that mirror the backend Pydantic schemas.
 * These are maintained manually and must stay in sync with docs/api-specification.md.
 *
 * Phase 1: Health check types only.
 * Additional types added in later phases as endpoints are implemented.
 */

// ─── Health ───────────────────────────────────────────────────────────────────

export type ServiceStatus =
  | "ok"
  | "error"
  | "not_initialised"
  | "extension_not_installed";

export type OverallStatus = "healthy" | "degraded" | "unhealthy";

export interface ServiceHealthStatus {
  status: ServiceStatus;
  detail?: string | null;
}

export interface HealthResponse {
  status: OverallStatus;
  version: string;
  service: string;
  environment: string;
  timestamp: string; // ISO 8601
  services: {
    postgres: ServiceHealthStatus;
    pgvector: ServiceHealthStatus;
    neo4j: ServiceHealthStatus;
  };
}

// ─── Error ───────────────────────────────────────────────────────────────────

export interface ApiErrorDetail {
  field?: string;
  message: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: ApiErrorDetail[];
  };
}
