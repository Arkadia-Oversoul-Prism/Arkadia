import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "../../lib/apiClient";
import { Panel } from "../ui";
import { ProspectEntryForm } from "./ProspectEntryForm";
import {
  UNVERIFIED,
  fact,
  statusColumns,
  summarize,
  upsertEntry,
  type OpportunityEntry,
} from "./opportunityRadarContract";

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
 * Project-scoped Opportunity Radar read surface, with create/edit entry controls.
 *
 * The parent supplies the canonical, project-scoped board path from the shared
 * endpoint integration. This component never invents a host or owns routing, and
 * it derives its write targets from that same board path so the POST/PATCH
 * destination cannot drift from the GET.
 *
 * Writes go only to the two verified handlers on `solspire/buyer_recon_router.py`
 * (create and edit). Nothing is shown as recorded until the server confirms it:
 * the saved entry is the one the response carried. It is reconnaissance only —
 * there is no delete, bulk, spend, approve, or execute control, and an unverified
 * commercial fact renders as the backend's own `UNKNOWN` sentinel.
 */
export function ProjectOpportunityRadar({ readPath }: { readPath: string }) {
  const [state, setState] = useState<ReadState>({ kind: "loading" });
  const [refreshKey, setRefreshKey] = useState(0);
  const [entries, setEntries] = useState<OpportunityEntry[]>([]);
  const [form, setForm] = useState<{ mode: "create" } | { mode: "edit"; entry: OpportunityEntry } | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState({ kind: "loading" });
    apiRequest<OpportunityBoardResponse>(readPath)
      .then((board) => {
        if (cancelled) return;
        setState({ kind: "ready", board });
        setEntries(board.entries);
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

  // A board switch must not carry a form — or a locally held entry — across
  // projects. The read resets both, so an edit control can never address an
  // entry id that belongs to another project's board.
  useEffect(() => {
    setForm(null);
    setEntries([]);
  }, [readPath]);

  const summary = summarize(entries);

  return (
    <div className="flex flex-col gap-3">
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
            {/* Pipeline strip — a real count per declared status, over the same
                entries the list below shows. A status the backend stored but does
                not declare has no column here, so it is counted separately rather
                than dropped (see the off-vocabulary note under the list). */}
            <ul
              className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4"
              data-testid="opportunity-pipeline"
            >
              {statusColumns().map((column) => (
                <li key={column.status} className="rounded border border-line bg-ink/40 px-2 py-1">
                  <p className="font-mono text-[9px] uppercase tracking-widest text-white/40">{column.label}</p>
                  <p
                    className={`text-sm ${column.status === "READY_TO_EXECUTE" ? "text-gold" : "text-emerald"}`}
                    data-testid={`opportunity-pipeline-${column.status}`}
                  >
                    {summary.byStatus[column.status] ?? 0}
                  </p>
                </li>
              ))}
            </ul>
            {entries.length === 0 ? (
              <p className="text-sm text-white/50">No prospects recorded for this project yet.</p>
            ) : (
              <ul className="flex flex-col gap-2" data-testid="opportunity-entry-list">
                {entries.map((entry) => (
                  <li key={entry.id} className="rounded-lg border border-line bg-ink/40 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="text-sm text-white/90">{entry.prospect}</p>
                      <span className="rounded border border-line px-2 py-1 font-mono text-[10px] text-white/55">{entry.status}</span>
                    </div>
                    <p className="mt-1 text-xs text-white/45">
                      {[fact(entry.location), fact(entry.commodity), fact(entry.buyer_type)]
                        .filter((value) => value !== UNVERIFIED)
                        .join(" · ") || "Location, commodity and buyer type not yet recorded"}
                    </p>
                    <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-white/35">
                      Evidence: {entry.evidence_status ?? "not reported"}
                    </p>
                    <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-white/50 sm:grid-cols-3">
                      <div>
                        <dt className="font-mono text-[9px] uppercase tracking-widest text-white/30">Buyer price</dt>
                        <dd>{fact(entry.buyer_price)}</dd>
                      </div>
                      <div>
                        <dt className="font-mono text-[9px] uppercase tracking-widest text-white/30">Landed cost</dt>
                        <dd>{fact(entry.landed_cost)}</dd>
                      </div>
                      <div>
                        <dt className="font-mono text-[9px] uppercase tracking-widest text-white/30">Margin</dt>
                        <dd>{fact(entry.expected_gross_margin)}</dd>
                      </div>
                    </dl>
                    {entry.why_this_prospect && <p className="mt-2 text-xs text-white/60">{entry.why_this_prospect}</p>}
                    <div className="mt-3">
                      <button
                        type="button"
                        data-testid={`opportunity-entry-edit-${entry.id}`}
                        onClick={() => setForm({ mode: "edit", entry })}
                        className="rounded border border-line px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-white/65"
                      >
                        Edit
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-3 text-[11px] text-white/35">
              {summary.total} recorded prospect(s), {summary.actionable} at a decision stage. No spending or execution is authorized by this view.
            </p>
            {summary.offVocabulary > 0 && (
              <p className="mt-1 text-[11px] text-gold" data-testid="opportunity-off-vocabulary">
                {summary.offVocabulary} recorded prospect(s) carry a status outside the declared pipeline
                and are not counted in the columns above.
              </p>
            )}
          </>
        )}
      </Panel>

      {state.kind === "ready" && !form && (
        <button
          type="button"
          data-testid="opportunity-entry-create"
          onClick={() => setForm({ mode: "create" })}
          className="self-start rounded border border-emerald/40 px-4 py-1.5 font-mono text-[11px] uppercase tracking-widest text-emerald"
        >
          Record prospect
        </button>
      )}

      {state.kind === "ready" && form?.mode === "create" && (
        <ProspectEntryForm
          boardPath={readPath}
          mode="create"
          onSaved={(entry) => {
            setEntries((current) => upsertEntry(current, entry));
            setForm(null);
          }}
          onCancel={() => setForm(null)}
        />
      )}

      {state.kind === "ready" && form?.mode === "edit" && (
        <ProspectEntryForm
          boardPath={readPath}
          mode="edit"
          entry={form.entry}
          onSaved={(entry) => {
            setEntries((current) => upsertEntry(current, entry));
            setForm(null);
          }}
          onCancel={() => setForm(null)}
        />
      )}
    </div>
  );
}
