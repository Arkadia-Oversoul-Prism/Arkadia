/**
 * SolSpire control-plane readings — the bounded daily/weekly spine.
 *
 * Four owner-scoped reads over the canonical `/solspire` router, each through
 * the shared endpoint registry:
 *   GET /solspire/workspace    -> the canonical workspace bound to the subject
 *   GET /solspire/workloads    -> the single canonical workload
 *   GET /solspire/pulses       -> bounded daily pulses (list)
 *   GET /solspire/syntheses    -> bounded weekly syntheses (list)
 *
 * Two of these have a *narrower* contract than the others and the surface must
 * say so rather than let a `404`/`409` read as a failure:
 *
 *   - `GET /solspire/workloads` answers `404` until a canonical workload exists
 *     and `409` when no canonical workspace is bound yet. A `404` is the honest
 *     "no workload yet" state, not a broken read.
 *   - `GET /solspire/pulses` and `/solspire/syntheses` answer `409` for the same
 *     missing-workspace reason.
 *
 * The distinction is drawn from the response *status*, never guessed from an
 * empty body. This surface only reads: it offers no create, decide, or execute
 * control, so an empty reading is never presented as a state the UI produced.
 */
import type { ReactNode } from "react";
import { Panel, Facts, ContractState } from "../../components/ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest, ApiError } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import type {
  SolspirePulseList,
  SolspireSynthesisList,
  SolspireWorkloadRead,
  SolspireWorkspaceRead,
} from "../../lib/types";

const read = <T,>(path: string): Promise<T> => apiRequest<T>(path);

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">{title}</p>
      {children}
    </div>
  );
}

/** A narrow, expected refusal — distinct from a transport or server failure. */
function NarrowState({ error, onRetry, label }: { error: ApiError | null; onRetry: () => void; label: string }) {
  return (
    <Panel className="border-dashed border-line">
      <p className="text-sm text-white/70">{label}</p>
      {error && <p className="mt-1 font-mono text-xs text-white/40">{error.message}</p>}
      <button
        onClick={onRetry}
        className="mt-4 rounded border border-emerald/40 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-emerald"
      >
        Retry
      </button>
    </Panel>
  );
}

export function SolSpireControlPlane() {
  const workspace = useHydration<SolspireWorkspaceRead>(endpoints.solspireWorkspace, read<SolspireWorkspaceRead>);
  const workload = useHydration<SolspireWorkloadRead>(endpoints.solspireWorkloads, read<SolspireWorkloadRead>);
  const pulses = useHydration<SolspirePulseList>(endpoints.solspirePulses, read<SolspirePulseList>);
  const syntheses = useHydration<SolspireSynthesisList>(endpoints.solspireSyntheses, read<SolspireSynthesisList>);

  // `409` on the workload read means the canonical workspace is not bound yet —
  // a workspace-level prerequisite, not a broken workload.
  const workloadUnbound = workload.error?.kind === "CONFLICT";
  const workloadAbsent = workload.error?.kind === "NOT_FOUND";
  const pulsesUnbound = pulses.error?.kind === "CONFLICT";
  const synthesesUnbound = syntheses.error?.kind === "CONFLICT";

  return (
    <div className="flex flex-col gap-4">
      <Section title="Canonical workspace">
        {workspace.state === "ready" && workspace.data ? (
          <Panel>
            <Facts
              rows={[
                { label: "name", value: workspace.data.workspace.display_name },
                { label: "lifecycle", value: workspace.data.workspace.lifecycle },
                { label: "type", value: workspace.data.workspace.workspace_type },
                { label: "binding", value: workspace.data.subject_binding },
              ]}
            />
          </Panel>
        ) : (
          <ContractState state={workspace.state} error={workspace.error?.message} onRetry={workspace.reload} />
        )}
      </Section>

      <Section title="Canonical workload">
        {workload.state === "ready" && workload.data ? (
          <Panel>
            <Facts
              rows={[
                { label: "title", value: workload.data.workload.title },
                { label: "phase", value: workload.data.workload.phase },
                { label: "status", value: workload.data.workload.status },
                { label: "objective", value: workload.data.workload.objective },
              ]}
            />
          </Panel>
        ) : workloadAbsent ? (
          <NarrowState
            error={workload.error}
            onRetry={workload.reload}
            label="No canonical workload exists for this subject yet. A 404 here is the honest empty state, not a failed read."
          />
        ) : workloadUnbound ? (
          <NarrowState
            error={workload.error}
            onRetry={workload.reload}
            label="The canonical workspace is not bound yet, so no workload can be read."
          />
        ) : (
          <ContractState state={workload.state} error={workload.error?.message} onRetry={workload.reload} />
        )}
      </Section>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title={`Daily pulses${pulses.data ? ` · ${pulses.data.count}` : ""}`}>
          {pulses.state === "ready" && pulses.data ? (
            <Panel>
              {pulses.data.pulses.length === 0 ? (
                <p className="text-sm text-white/50">No daily pulses recorded yet.</p>
              ) : (
                <ul className="flex flex-col gap-2" data-testid="solspire-pulses">
                  {pulses.data.pulses.map((p) => (
                    <li key={p.pulse_id} className="rounded border border-line bg-ink/40 p-3">
                      <div className="flex items-baseline justify-between gap-3">
                        <p className="text-sm text-white/85">{p.date}</p>
                        <p className="font-mono text-[10px] text-white/35">
                          {p.period} · v{p.version}
                        </p>
                      </div>
                      {p.state_summary && <p className="mt-1 text-xs text-white/55">{p.state_summary}</p>}
                      <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-white/35">{p.status}</p>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          ) : pulsesUnbound ? (
            <NarrowState
              error={pulses.error}
              onRetry={pulses.reload}
              label="The canonical workspace is not bound yet, so no pulses can be read."
            />
          ) : (
            <ContractState state={pulses.state} error={pulses.error?.message} onRetry={pulses.reload} />
          )}
        </Section>

        <Section title={`Weekly syntheses${syntheses.data ? ` · ${syntheses.data.count}` : ""}`}>
          {syntheses.state === "ready" && syntheses.data ? (
            <Panel>
              {syntheses.data.syntheses.length === 0 ? (
                <p className="text-sm text-white/50">No weekly syntheses recorded yet.</p>
              ) : (
                <ul className="flex flex-col gap-2" data-testid="solspire-syntheses">
                  {syntheses.data.syntheses.map((s) => (
                    <li key={s.synthesis_id} className="rounded border border-line bg-ink/40 p-3">
                      <div className="flex items-baseline justify-between gap-3">
                        <p className="text-sm text-white/85">
                          {s.period_start} → {s.period_end}
                        </p>
                        <p className="font-mono text-[10px] text-white/35">v{s.version}</p>
                      </div>
                      {s.summary && <p className="mt-1 text-xs text-white/55">{s.summary}</p>}
                      <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-white/35">{s.status}</p>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          ) : synthesesUnbound ? (
            <NarrowState
              error={syntheses.error}
              onRetry={syntheses.reload}
              label="The canonical workspace is not bound yet, so no syntheses can be read."
            />
          ) : (
            <ContractState state={syntheses.state} error={syntheses.error?.message} onRetry={syntheses.reload} />
          )}
        </Section>
      </div>
    </div>
  );
}
