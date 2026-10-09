/**
 * MemoryLeak — Home page (Phase 1 shell)
 *
 * Displays a system status card by calling the backend /health endpoint.
 * This proves Frontend → Backend connectivity works.
 *
 * NOTE: This is the Phase 1 infrastructure shell.
 * The full dashboard (Phase 11) will replace this page.
 */

import { Suspense } from "react";
import HealthStatus from "@/components/HealthStatus";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
            MemoryLeak
          </h1>
          <p className="text-lg text-slate-500">
            Organizational Knowledge Risk &amp; Dependency Intelligence
          </p>
          <span className="inline-block rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
            Phase 1 — Infrastructure
          </span>
        </div>

        {/* Infrastructure Status */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
            Infrastructure Status
          </h2>
          <Suspense fallback={<StatusSkeleton />}>
            <HealthStatus />
          </Suspense>
        </div>

        {/* Phase roadmap */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
            Development Status
          </h2>
          <div className="space-y-2 text-sm">
            {[
              { phase: "Phase 0", label: "Planning", done: true },
              { phase: "Phase 1", label: "Infrastructure", active: true },
              { phase: "Phase 2", label: "Synthetic Data Engine", done: false },
              { phase: "Phase 3", label: "Ingestion Pipeline", done: false },
              { phase: "Phase 4", label: "NLP + Embeddings", done: false },
              { phase: "Phase 5", label: "Knowledge Graph", done: false },
              { phase: "Phase 6", label: "Intelligence Engine", done: false },
            ].map(({ phase, label, done, active }) => (
              <div
                key={phase}
                className={`flex items-center justify-between rounded-lg px-3 py-2 ${
                  active
                    ? "bg-indigo-50 text-indigo-700"
                    : done
                    ? "text-slate-400"
                    : "text-slate-500"
                }`}
              >
                <span className="font-medium">{phase}</span>
                <span>{label}</span>
                <span className="text-xs">
                  {active ? "▶ In progress" : done ? "✓ Complete" : "Pending"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

function StatusSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center justify-between">
          <div className="h-4 w-24 rounded bg-slate-200" />
          <div className="h-4 w-16 rounded bg-slate-200" />
        </div>
      ))}
    </div>
  );
}
