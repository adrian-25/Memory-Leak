/**
 * HealthStatus — Server Component
 *
 * Fetches the backend /health endpoint at render time (server-side).
 * Displays live connectivity status for PostgreSQL, pgvector, and Neo4j.
 *
 * This component proves Frontend → Backend → Database connectivity.
 *
 * Phase 1 only. Will be absorbed into the monitoring dashboard in Phase 11.
 */

import type { HealthResponse, ServiceHealthStatus } from "@/types/api";

const LOCAL_BACKEND_URL = "http://localhost:8000";
const RENDER_API_URL = "https://memory-leak-api.onrender.com";

// Prefer an explicit URL over the legacy host/port setting. Render can retain
// removed Blueprint variables, and the old private value otherwise overrides
// the working HTTPS address at runtime.
const BACKEND_URL =
  process.env.NEXT_INTERNAL_API_URL?.replace("/api/v1", "") ||
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace("/api/v1", "") ||
  (process.env.NODE_ENV === "production" ? RENDER_API_URL : undefined) ||
  (process.env.NEXT_INTERNAL_API_HOSTPORT
    ? `http://${process.env.NEXT_INTERNAL_API_HOSTPORT}`
    : LOCAL_BACKEND_URL);

async function getHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/health`, {
      next: { revalidate: 10 }, // re-fetch every 10 seconds
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

function StatusBadge({ status }: { status: string }) {
  const colours: Record<string, string> = {
    ok: "bg-emerald-100 text-emerald-700",
    healthy: "bg-emerald-100 text-emerald-700",
    degraded: "bg-amber-100 text-amber-700",
    error: "bg-red-100 text-red-700",
    not_initialised: "bg-slate-100 text-slate-500",
    not_configured: "bg-slate-100 text-slate-500",
    extension_not_installed: "bg-red-100 text-red-700",
    unhealthy: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
        colours[status] ?? "bg-slate-100 text-slate-500"
      }`}
    >
      {status}
    </span>
  );
}

export default async function HealthStatus() {
  const health = await getHealth();

  if (!health) {
    return (
      <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
        ⚠️ Could not reach the API. Please try again in a moment.
      </div>
    );
  }

  const serviceRows: { label: string; key: keyof typeof health.services }[] = [
    { label: "PostgreSQL", key: "postgres" },
    { label: "pgvector", key: "pgvector" },
    { label: "Neo4j", key: "neo4j" },
  ];

  return (
    <div className="space-y-3">
      {/* Overall status */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <p className="font-semibold text-slate-700">
            {health.service}{" "}
            <span className="text-slate-400 font-normal text-xs">
              v{health.version}
            </span>
          </p>
          <p className="text-xs text-slate-400">{health.environment}</p>
        </div>
        <StatusBadge status={health.status} />
      </div>

      {/* Per-service status */}
      {serviceRows.map(({ label, key }) => {
        const svc = health.services[key] as ServiceHealthStatus;
        return (
          <div key={key} className="flex items-center justify-between text-sm">
            <span className="text-slate-600">{label}</span>
            <div className="flex items-center gap-2">
              {svc.detail && (
                <span className="text-xs text-slate-400 max-w-xs truncate">
                  {svc.detail}
                </span>
              )}
              <StatusBadge status={svc.status} />
            </div>
          </div>
        );
      })}

      <p className="text-right text-xs text-slate-400">
        checked {new Date(health.timestamp).toLocaleTimeString()}
      </p>
    </div>
  );
}
