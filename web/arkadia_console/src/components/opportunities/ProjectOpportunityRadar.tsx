import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "../../lib/apiClient";
import { Panel } from "../ui";

interface OpportunityEntry {
  id: string;
  prospect: string;
  location?: string;
  commodity?: string;
  buyer_type?: string;
  contact_route?: string;
  status: string;
  evidence_status?: string;
  why_this_prospect?: string;
  notes?: string;
}

interface OpportunityBoardResponse {
  project_id: string;
  entries: OpportunityEntry[];
  statuses: string[];
  authority?: {
    reconnaissance_only?: boolean;
    execution_authority?: string;
    budget_authority?: string;
  };
}

type ReadState =
  | { kind: "loading" }
  | { kind: "ready"; board: OpportunityBoardResponse }
  | { kind: "auth"; message: string }
  | { kind: "unavailable"; message: string }
  | { kind: "error"; message: string };

/**
 * Project-scoped Opportunity Radar read surface.
 *
 * The parent supplies the canonical, project-scoped API path from the shared
 * endpoint integration. This component never invents a host or owns routing.
 * It is reconnaissance only: it deliberately exposes no execute/spend action.
 */
export function ProjectOpportunityRadar({ readPath }: { readPath: string }) {
  const [state, setState] = useState<ReadState>({ kind: "loading" });
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: "loading" });
    apiRequest<OpportunityBoardResponse>(readPath)
      .then((board) => {
        if (!cancelled) setState({ kind: "ready", board });
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        const error = caught instanceof ApiError ? caught : null;
        const message = error?.message ?? (caught instanceof Error ? caught.message : "Request failed.");
        if (error?.kind === "AUTH_REQUIRED" || error?.kind === "FORBIDDEN") {
          setState({ kind: "auth", message: "Sign in with access to this project to read its opportunity board." });
        } else if (error?.kind === "NETWORK_ERROR" || error?.kind === "SERVER_ERROR") {
          setState({ kind: "unavailable", message: "The board could not be read. This is not an empty board." });
        } else {
          setState({ kind: "error", message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [readPath, refreshKey]);

  return (
    <Panel>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Project field · Opportunity Radar</p>
          <p className="mt-1 text-sm text-white/65">Demand and supplier reconnaissance, kept separate from transaction authority.</p>
        </div>
        <button
          type="button"
          onClick={() => setRefreshKey((key) => key + 1)}
          disabled={state.kind === "loading"}
          className="rounded border border-line px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-white/65 disabled:opacity-40"
        >
          Refresh
        </button>
      </div>

      {state.kind === "loading" && (
        <p role="status" className="animate-pulse text-sm text-white/45">Reading the project board…</p>
      )}
      {state.kind === "auth" && (
        <p role="alert" className="text-sm text-gold">{state.message}</p>
      )}
      {state.kind === "unavailable" && (
        <p role="alert" className="text-sm text-gold">{state.message}</p>
      )}
      {state.kind === "error" && (
        <p role="alert" className="text-sm text-rose-300">Board read failed: {state.message}</p>
      )}
      {state.kind === "ready" && (
        <>
          {state.board.authority?.reconnaissance_only && (
            <p className="mb-3 rounded border border-line px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-white/45">
              Reconnaissance only · execution: {state.board.authority.execution_authority ?? "unreported"} · budget: {state.board.authority.budget_authority ?? "unreported"}
            </p>
          )}
          {state.board.entries.length === 0 ? (
            <p className="text-sm text-white/50">No prospects recorded for this project yet.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {state.board.entries.map((entry) => (
                <li key={entry.id} className="rounded-lg border border-line bg-ink/40 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="text-sm text-white/90">{entry.prospect}</p>
                    <span className="rounded border border-line px-2 py-1 font-mono text-[10px] text-white/55">{entry.status}</span>
                  </div>
                  <p className="mt-1 text-xs text-white/45">
                    {[entry.location, entry.commodity, entry.buyer_type].filter(Boolean).join(" · ") || "Location, commodity and buyer type not yet recorded"}
                  </p>
                  <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-white/35">
                    Evidence: {entry.evidence_status ?? "not reported"}
                  </p>
                  {entry.why_this_prospect && <p className="mt-2 text-xs text-white/60">{entry.why_this_prospect}</p>}
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-[11px] text-white/35">{state.board.entries.length} recorded prospect(s). No spending or execution is authorized by this view.</p>
        </>
      )}
    </Panel>
  );
}
