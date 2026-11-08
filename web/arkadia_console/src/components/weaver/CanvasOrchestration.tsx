/**
 * Weaver — one authenticated read across the canonical Lab, Arkana and Weaver
 * substrates. This is a projection, not a store and not an execution surface.
 *
 * The panel deliberately distinguishes:
 * - loading/authentication/authorization/transport failures (ContractState);
 * - a malformed or incomplete response (UNKNOWN);
 * - valid empty collections (real zero counts and explicit empty copy).
 *
 * It does not poll automatically or claim live telemetry. Refresh is an
 * explicit read of the same subject-scoped canvas contract.
 */
import { useAuth } from "../../contexts/AuthContext";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import { useHydration } from "../../lib/useHydration";
import { ContractState, Panel } from "../ui";

type JsonRecord = Record<string, unknown>;

interface CanvasDependency {
  from: string;
  to: string;
}

interface CanvasSubtask {
  run_id: string;
  id: string;
  kind: string;
  target: string;
  state: string;
  description?: string;
}

interface CanvasRetry {
  run_id: string;
  attempt: number;
  retryable: boolean;
  retry_policy: string;
}

interface CanvasProjection {
  lab: {
    contract: string;
    sessions: JsonRecord[];
  };
  arkana: {
    contract: string;
    threads: JsonRecord[];
    count: number;
  };
  weaver: {
    contract: string;
    sessions: JsonRecord[];
    runs: JsonRecord[];
    orchestration: {
      dependencies: CanvasDependency[];
      subtasks: CanvasSubtask[];
      retries: CanvasRetry[];
      poll: {
        mode: "poll";
        cursor_field: "updated_at";
        updated_at: string | null;
        note: string;
      };
    };
  };
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isRecordArray(value: unknown): value is JsonRecord[] {
  return Array.isArray(value) && value.every(isRecord);
}

function isDependency(value: JsonRecord): value is JsonRecord & CanvasDependency {
  return typeof value.from === "string" && typeof value.to === "string";
}

function isSubtask(value: JsonRecord): value is JsonRecord & CanvasSubtask {
  return (
    typeof value.run_id === "string" &&
    typeof value.id === "string" &&
    typeof value.kind === "string" &&
    typeof value.target === "string" &&
    typeof value.state === "string" &&
    (value.description === undefined || typeof value.description === "string")
  );
}

function isRetry(value: JsonRecord): value is JsonRecord & CanvasRetry {
  return (
    typeof value.run_id === "string" &&
    typeof value.attempt === "number" &&
    typeof value.retryable === "boolean" &&
    typeof value.retry_policy === "string"
  );
}

/** Return null for a malformed response; never turn a missing collection into zero. */
function parseCanvas(payload: unknown): CanvasProjection | null {
  if (!isRecord(payload) || payload.read_only !== true || !Array.isArray(payload.surfaces)) {
    return null;
  }
  const expectedSurfaces = ["engineering-lab", "arkana", "weaver"];
  if (
    payload.surfaces.length !== expectedSurfaces.length ||
    !expectedSurfaces.every((surface, index) => payload.surfaces[index] === surface) ||
    !isRecord(payload.sections)
  ) {
    return null;
  }

  const lab = payload.sections["engineering-lab"];
  const arkana = payload.sections.arkana;
  const weaver = payload.sections.weaver;
  if (!isRecord(lab) || !isRecord(arkana) || !isRecord(weaver)) return null;

  const labSessions = lab.sessions;
  const threads = arkana.threads;
  const threadCount = arkana.count;
  const weaverSessions = weaver.sessions;
  const runs = weaver.runs;
  const orchestration = weaver.orchestration;

  if (
    typeof lab.contract !== "string" ||
    !isRecordArray(labSessions) ||
    typeof arkana.contract !== "string" ||
    !isRecordArray(threads) ||
    typeof threadCount !== "number" ||
    threadCount !== threads.length ||
    typeof weaver.contract !== "string" ||
    !isRecordArray(weaverSessions) ||
    !isRecordArray(runs) ||
    !isRecord(orchestration)
  ) {
    return null;
  }

  const dependencyRows =
    isRecordArray(orchestration.dependencies) && orchestration.dependencies.every(isDependency)
      ? (orchestration.dependencies as CanvasDependency[])
      : null;
  const subtaskRows =
    isRecordArray(orchestration.subtasks) && orchestration.subtasks.every(isSubtask)
      ? (orchestration.subtasks as CanvasSubtask[])
      : null;
  const retryRows =
    isRecordArray(orchestration.retries) && orchestration.retries.every(isRetry)
      ? (orchestration.retries as CanvasRetry[])
      : null;
  const poll = orchestration.poll;
  if (
    dependencyRows === null ||
    subtaskRows === null ||
    retryRows === null ||
    !isRecord(poll) ||
    poll.mode !== "poll" ||
    poll.cursor_field !== "updated_at" ||
    !(poll.updated_at === null || typeof poll.updated_at === "string") ||
    typeof poll.note !== "string"
  ) {
    return null;
  }

  return {
    lab: { contract: lab.contract, sessions: labSessions },
    arkana: { contract: arkana.contract, threads, count: threadCount },
    weaver: {
      contract: weaver.contract,
      sessions: weaverSessions,
      runs,
      orchestration: {
        dependencies: dependencyRows,
        subtasks: subtaskRows,
        retries: retryRows,
        poll: {
          mode: "poll",
          cursor_field: "updated_at",
          updated_at: poll.updated_at,
          note: poll.note,
        },
      },
    },
  };
}

function SurfaceCount({
  id,
  label,
  value,
  unit,
  detail,
  contract,
}: {
  id: string;
  label: string;
  value: number;
  unit: string;
  detail?: string;
  contract: string;
}) {
  return (
    <section
      className="min-w-0 rounded border border-line bg-ink/40 p-3"
      data-testid={`weaver-canvas-surface-${id}`}
    >
      <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">{label}</p>
      <p className="mt-2 font-display text-2xl text-white/90">{value}</p>
      <p className="text-xs text-white/50">{unit}</p>
      {detail ? <p className="mt-1 text-xs text-white/45">{detail}</p> : null}
      <p className="mt-3 break-all font-mono text-[10px] text-azure/60">{contract}</p>
    </section>
  );
}

function CanvasReadout({ data }: { data: CanvasProjection }) {
  const { dependencies, subtasks, retries, poll } = data.weaver.orchestration;
  return (
    <div className="mt-4 min-w-0" data-testid="weaver-canvas-readout">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <SurfaceCount
          id="engineering-lab"
          label="Engineering Lab"
          value={data.lab.sessions.length}
          unit="recorded sessions"
          contract={data.lab.contract}
        />
        <SurfaceCount
          id="arkana"
          label="Arkana"
          value={data.arkana.count}
          unit="owned conversation threads"
          contract={data.arkana.contract}
        />
        <SurfaceCount
          id="weaver"
          label="Weaver"
          value={data.weaver.runs.length}
          unit="recorded runs"
          detail={`${data.weaver.sessions.length} recorded sessions`}
          contract={data.weaver.contract}
        />
      </div>

      <section className="mt-5 min-w-0" data-testid="weaver-canvas-orchestration">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/45">
          Recorded orchestration
        </p>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <div className="min-w-0 rounded border border-line/70 p-3" data-testid="weaver-canvas-dependencies">
            <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
              Dependencies · {dependencies.length}
            </p>
            {dependencies.length === 0 ? (
              <p className="mt-2 text-xs text-white/45">No dependency edges recorded.</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {dependencies.slice(0, 6).map((edge, index) => (
                  <li key={`${edge.from}-${edge.to}-${index}`} className="break-all font-mono text-[10px] text-white/65">
                    {edge.from} <span className="text-teal">→</span> {edge.to}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="min-w-0 rounded border border-line/70 p-3" data-testid="weaver-canvas-subtasks">
            <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
              Subtasks · {subtasks.length}
            </p>
            {subtasks.length === 0 ? (
              <p className="mt-2 text-xs text-white/45">No operation subtasks recorded.</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {subtasks.slice(0, 6).map((task) => (
                  <li key={`${task.run_id}-${task.id}`} className="min-w-0">
                    <p className="break-all font-mono text-[10px] text-white/70">
                      {task.kind} · {task.target}
                    </p>
                    <p className="mt-0.5 break-words text-[10px] text-white/40">
                      {task.run_id} · {task.state}
                      {task.description ? ` · ${task.description}` : ""}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="min-w-0 rounded border border-line/70 p-3" data-testid="weaver-canvas-retries">
            <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
              Retry decisions · {retries.length}
            </p>
            {retries.length === 0 ? (
              <p className="mt-2 text-xs text-white/45">No retry decisions recorded.</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {retries.slice(0, 6).map((retry) => (
                  <li key={retry.run_id} className="min-w-0">
                    <p className="break-all font-mono text-[10px] text-white/70">
                      {retry.run_id} · attempt {retry.attempt}
                    </p>
                    <p className="mt-0.5 text-[10px] text-white/55">
                      {retry.retryable ? "Retry permitted by policy" : "Not retryable"}
                    </p>
                    <p className="mt-0.5 break-all font-mono text-[10px] text-white/35">
                      {retry.retry_policy}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      <div className="mt-4 min-w-0 rounded border border-line/70 bg-ink/30 p-3" data-testid="weaver-canvas-poll-contract">
        <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
          Snapshot contract · {poll.mode} · cursor {poll.cursor_field}
        </p>
        <p className="mt-2 break-all font-mono text-[10px] text-white/60">
          Latest session/run update: {poll.updated_at ?? "No timestamp supplied"}
        </p>
        <p className="mt-2 text-xs leading-relaxed text-white/45">
          Snapshot only. This panel does not stream or refresh automatically; use Refresh snapshot
          to read the current server state.
        </p>
        <p className="mt-1 break-words text-[10px] leading-relaxed text-white/30">{poll.note}</p>
      </div>
    </div>
  );
}

export function CanvasOrchestration() {
  const { isAuthenticated } = useAuth();
  const snapshot = useHydration<unknown>(
    endpoints.canvas,
    (path) => apiRequest<unknown>(path),
    [isAuthenticated],
  );
  const data = snapshot.state === "ready" ? parseCanvas(snapshot.data) : null;

  return (
    <Panel className="mb-4" data-testid="weaver-canvas-snapshot">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/45">
            Unified substrate snapshot
          </p>
          <p className="max-w-2xl text-xs leading-relaxed text-white/45">
            One authenticated, read-only projection across Engineering Lab, Arkana and Weaver.
            Counts and records below come from the canonical server response.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded border border-teal/30 px-2 py-1 font-mono text-[9px] uppercase tracking-widest text-teal/80">
            read-only · snapshot
          </span>
          <button
            type="button"
            onClick={snapshot.reload}
            disabled={snapshot.state === "loading"}
            className="cg-btn"
            data-testid="weaver-canvas-refresh"
          >
            {snapshot.state === "loading" ? "Refreshing…" : "Refresh snapshot"}
          </button>
        </div>
      </div>

      {snapshot.state !== "ready" ? (
        <div className="mt-4">
          <ContractState
            state={snapshot.state}
            error={snapshot.error?.message}
            onRetry={snapshot.reload}
          />
        </div>
      ) : data ? (
        <CanvasReadout data={data} />
      ) : (
        <div
          className="mt-4 rounded border border-gold/30 bg-gold/5 p-3"
          data-testid="weaver-canvas-unknown"
        >
          <p className="font-mono text-[10px] uppercase tracking-widest text-gold">
            UNKNOWN · incomplete canvas response
          </p>
          <p className="mt-2 text-xs leading-relaxed text-white/55">
            The endpoint returned a payload, but one or more required surfaces, collections or
            provenance fields were absent or malformed. No zero counts have been inferred.
          </p>
        </div>
      )}
    </Panel>
  );
}
