/**
 * Project runtime-context canvas — the "cognitive canvas" the Solariun project
 * lens had only announced as not-yet-wired.
 *
 * One read of the bounded projection `GET /solspire/projects/{id}/runtime-context`
 * (handler `solspire/console_router.py::project_runtime_context`). It is a
 * projection, not a second memory/task/event system: project-owned records come
 * from project_store, and Daily Pulse / Workload / WorkEvents are reported from
 * their existing spines with their **actual binding state**. A missing binding
 * renders UNKNOWN — the endpoint states its own epistemic boundary and this
 * surface repeats it rather than inferring anything.
 *
 * Truthful states: loading; ready; auth-required; backend unavailable; read
 * failed; and the deliberate ambiguity of a 404 — `require_project_owner`
 * answers identically for a missing project and for one the caller does not
 * own, so this surface says exactly that and never guesses which occurred.
 *
 * Read-only: no control here mutates project, pulse, workload, or weaver state.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest, ApiError } from "../../lib/apiClient";
import { solspireProjectRuntime } from "../../lib/endpoints";

/** The response shape actually returned by the handler (fields typed narrowly). */
export interface ProjectRuntimeContext {
  project: {
    id: string;
    name: string;
    status?: string;
    runtime_contract?: unknown;
  };
  project_store: {
    tasks: unknown[];
    files: unknown[];
    memory: unknown[];
    events: unknown[];
    repositories: unknown[];
  };
  knowledge_graph: { state?: string; detail?: string };
  control_plane: {
    workspace: unknown | null;
    daily_pulse: unknown | null;
    workload: unknown | null;
    work_events: unknown[];
  };
  binding_state: Record<string, string>;
  epistemic_boundary?: string;
  retrieved_at?: string;
}

const BINDING_LABELS: Record<string, string> = {
  daily_pulse: "daily pulse",
  workload: "workload",
  workevents: "work events",
  knowledge_os: "knowledge OS",
  knowledge_graph: "knowledge graph",
  weaver: "weaver",
  arkana: "arkana",
  living_larder: "living larder",
};

function storeCount(value: unknown[] | undefined): string {
  // The handler bounds every list ([:20]); the count is what is shown, never
  // the records themselves.
  return Array.isArray(value) ? String(value.length) : "—";
}

export function ProjectRuntimeCanvas({ projectId }: { projectId: string }) {
  const view = useHydration<ProjectRuntimeContext>(
    solspireProjectRuntime(projectId),
    (path) => apiRequest<ProjectRuntimeContext>(path),
  );

  if (view.state === "error" && view.error instanceof ApiError && view.error.kind === "NOT_FOUND") {
    return (
      <div data-testid="canvas-not-found">
        <Panel className="border-dashed border-line">
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Project not visible</p>
          <p className="mt-2 text-sm text-white/60">
            The runtime context could not be read: this contract answers 404 identically for a project
            that does not exist and for one this identity does not own — existence is never leaked, so
            this surface does not claim which occurred.
          </p>
        </Panel>
      </div>
    );
  }

  if (view.state !== "ready" || !view.data) {
    return <ContractState state={view.state} error={view.error?.message} onRetry={view.reload} />;
  }

  const ctx = view.data;
  const bindings = Object.entries(ctx.binding_state ?? {});
  const contract = ctx.project.runtime_contract;

  return (
    <div data-testid="project-runtime-canvas" className="flex flex-col gap-3">
      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Runtime context</p>
        <Facts
          rows={[
            { label: "project", value: ctx.project.name },
            { label: "status", value: ctx.project.status ?? "—" },
            {
              label: "runtime contract",
              value:
                contract === null || contract === undefined
                  ? "absent"
                  : typeof contract === "string"
                    ? contract
                    : JSON.stringify(contract),
            },
            { label: "store · tasks", value: storeCount(ctx.project_store?.tasks) },
            { label: "store · files", value: storeCount(ctx.project_store?.files) },
            { label: "store · memory", value: storeCount(ctx.project_store?.memory) },
            { label: "store · events", value: storeCount(ctx.project_store?.events) },
            { label: "store · repos", value: storeCount(ctx.project_store?.repositories) },
            {
              label: "knowledge graph",
              value:
                ctx.knowledge_graph?.state === "UNAVAILABLE"
                  ? `UNAVAILABLE${ctx.knowledge_graph.detail ? ` (${ctx.knowledge_graph.detail})` : ""}`
                  : (ctx.knowledge_graph?.state ?? "UNKNOWN"),
            },
            { label: "workspace", value: ctx.control_plane?.workspace ? "bound" : "UNKNOWN" },
            { label: "work events", value: storeCount(ctx.control_plane?.work_events) },
            { label: "retrieved", value: <span className="font-mono text-xs">{ctx.retrieved_at ?? "—"}</span> },
          ]}
        />
      </Panel>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Binding state · actual, not inferred
        </p>
        <ul className="flex flex-wrap gap-2">
          {bindings.map(([key, value]) => (
            <li
              key={key}
              className={`rounded px-2 py-1 font-mono text-[10px] uppercase tracking-widest ${
                value === "UNKNOWN"
                  ? "border border-dashed border-white/20 text-white/40"
                  : "border border-emerald/30 text-emerald/80"
              }`}
              data-testid={`binding-${key}`}
            >
              {BINDING_LABELS[key] ?? key} · {value}
            </li>
          ))}
        </ul>
        {ctx.epistemic_boundary && (
          <p className="mt-3 text-xs text-white/40">{ctx.epistemic_boundary}</p>
        )}
      </Panel>
    </div>
  );
}
