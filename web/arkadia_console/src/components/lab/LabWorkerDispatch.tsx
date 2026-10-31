/**
 * P0.5 — dispatch a model-backed worker from the mission workspace.
 *
 * The missing link between "the Lab can inspect and test code" and "the Lab
 * can employ an engineering worker": this panel reads the gateway's own
 * availability, posts `run-agent` for an already-authorized session, and
 * renders the loop's real terminal state, reason, granted tool envelope and
 * turns.
 *
 * Three rules it refuses to blur:
 *
 *  1. **Connected is not working.** `status` (configured/reachable) and
 *     `dispatchable` (an adapter can actually be called) are shown as separate
 *     facts. No dispatchable provider is an honest `UNAVAILABLE`, not a
 *     silent disable and never a simulated worker.
 *  2. **The dispatch outcome is read, not narrated.** `loop_state`,
 *     `loop_reason`, `effective_tools` and each turn come back from the
 *     substrate; nothing here invents progress or claims success.
 *  3. **The run is a proposal.** When the loop stops at the human review
 *     boundary this panel says so — it cannot merge, deploy, or self-authorize,
 *     and no dispatch implies acceptance.
 */
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../../lib/apiClient";
import { Panel } from "../ui";
import {
  dispatchWorker,
  getGatewayView,
  type LabDispatchResult,
  type LabGatewayView,
} from "./missionContract";

interface LabWorkerDispatchProps {
  sessionId: string;
  /** The session must be AUTHORIZED (or QUEUED) before the loop will run. */
  authorized: boolean;
  objective: string;
  /** Re-read the canonical session view after dispatch settles. */
  onSettled: () => Promise<void>;
}

function describeError(error: unknown): string {
  if (error && typeof error === "object" && "message" in error) {
    return String((error as { message: unknown }).message);
  }
  return String(error);
}

type GatewayPanelState = "LOADING" | "LIVE" | "EMPTY" | "UNAVAILABLE" | "FAILED";

function classifyGatewayFailure(error: unknown): "UNAVAILABLE" | "FAILED" {
  if (
    error instanceof ApiError &&
    (error.kind === "NETWORK_ERROR" || [401, 403, 404, 503].includes(error.status ?? 0))
  ) {
    return "UNAVAILABLE";
  }
  return "FAILED";
}

export function LabWorkerDispatch({ sessionId, authorized, objective, onSettled }: LabWorkerDispatchProps) {
  const [gateway, setGateway] = useState<LabGatewayView | null>(null);
  const [gatewayState, setGatewayState] = useState<GatewayPanelState>("LOADING");
  const [gatewayError, setGatewayError] = useState<string | null>(null);
  const [dispatching, setDispatching] = useState(false);
  const [result, setResult] = useState<LabDispatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadGateway = useCallback(async () => {
    setGatewayState("LOADING");
    setGatewayError(null);
    try {
      const view = await getGatewayView();
      setGateway(view);
      const providers = Array.isArray(view.catalog) ? view.catalog : null;
      if (providers === null) {
        setGatewayState("UNAVAILABLE");
        setGatewayError("The gateway response did not include a provider catalog.");
        return;
      }
      setGatewayState(providers.length > 0 ? "LIVE" : "EMPTY");
    } catch (err) {
      // A failed availability read is reported, not treated as "available".
      setGateway(null);
      setGatewayError(describeError(err));
      setGatewayState(classifyGatewayFailure(err));
    }
  }, []);

  useEffect(() => {
    void loadGateway();
  }, [loadGateway]);

  const catalog = gateway?.catalog ?? [];
  const dispatchable = catalog.filter((p) => p.dispatchable);
  const canDispatch = authorized && !dispatching;

  async function handleDispatch(): Promise<void> {
    setDispatching(true);
    setError(null);
    try {
      // Provider is chosen server-side by the gateway's honest selection; the
      // console names the family it is asking for and the backend decides.
      const preferred = dispatchable[0]?.provider ?? catalog[0]?.provider ?? "ollama";
      setResult(
        await dispatchWorker(sessionId, objective.trim() || "Read-only investigation", preferred, 6),
      );
    } catch (err) {
      setError(describeError(err));
      setResult(null);
    } finally {
      void loadGateway();
      try {
        await onSettled();
      } catch {
        // The parent records canonical-refresh failures in its evidence state.
      } finally {
        setDispatching(false);
      }
    }
  }

  return (
    <Panel>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">
            Worker dispatch — model-backed agent loop
          </p>
          <p className="mt-1 text-xs text-white/35">
            Runs <span className="font-mono">run-agent</span> against this authorized session. The loop's tool
            envelope is read-only and is reported below as the server granted it.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void handleDispatch()}
          disabled={!canDispatch}
          className="rounded border border-azure/50 bg-azure/10 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-azure enabled:hover:bg-azure/20 disabled:cursor-not-allowed disabled:opacity-40"
          data-testid="mission-dispatch-button"
        >
          {dispatching ? "Dispatching…" : "Dispatch worker"}
        </button>
      </div>

      {!authorized ? (
        <p className="mb-3 rounded border border-gold/30 bg-gold/5 px-3 py-2 text-xs text-gold/90">
          The session is not authorized. Dispatch is refused by the substrate until a human authorization is
          attached — SESSION is not AUTHORIZATION.
        </p>
      ) : null}

      <div data-testid="mission-provider-availability">
        <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/35">
          Inference availability — reported by the gateway
        </p>
        {gatewayState === "LOADING" ? (
          <p className="text-xs text-white/35" data-testid="mission-provider-state" data-state="LOADING">
            Reading provider status…
          </p>
        ) : gatewayState === "EMPTY" ? (
          <p className="text-xs text-white/45" data-testid="mission-provider-state" data-state="EMPTY">
            The gateway returned an empty provider catalog. No provider availability was reported.
          </p>
        ) : gatewayState === "UNAVAILABLE" ? (
          <p className="text-xs text-amber-200" data-testid="mission-provider-state" data-state="UNAVAILABLE">
            Provider availability is unavailable: {gatewayError ?? "The gateway did not return a provider catalog."}. No provider state is assumed.
          </p>
        ) : gatewayState === "FAILED" ? (
          <p className="text-xs text-red-300" data-testid="mission-provider-state" data-state="FAILED">
            Provider availability read failed: {gatewayError ?? "The gateway response could not be read."}.
          </p>
        ) : (
          <ul className="space-y-1.5" data-testid="mission-provider-state" data-state="LIVE">
            {catalog.map((p) => (
              <li
                key={p.provider}
                className="flex flex-wrap items-center gap-2 rounded border border-line bg-ink/60 px-2 py-1.5 text-xs"
              >
                <span className="font-mono text-white/80">{p.provider}</span>
                <span className="font-mono text-[10px] uppercase tracking-widest text-white/40">
                  {p.config_class}
                </span>
                <span
                  className={`font-mono text-[10px] uppercase tracking-widest ${
                    p.status === "AVAILABLE" ? "text-emerald" : "text-white/45"
                  }`}
                >
                  {p.status}
                </span>
                <span
                  className={`font-mono text-[10px] uppercase tracking-widest ${
                    p.dispatchable ? "text-emerald" : "text-amber-300"
                  }`}
                >
                  {p.dispatchable ? "dispatchable" : "not dispatchable"}
                </span>
                {p.detail ? <span className="min-w-0 break-words text-white/40">{p.detail}</span> : null}
              </li>
            ))}
          </ul>
        )}
        {gatewayState === "LIVE" && catalog.length > 0 && dispatchable.length === 0 ? (
          <p className="mt-2 rounded border border-amber-300/30 bg-amber-300/5 px-3 py-2 text-xs text-amber-200/90">
            No dispatchable inference provider is configured. A dispatch will stop{" "}
            <span className="font-mono">BLOCKED</span> with the gateway's own reason — this surface reports that
            outcome rather than simulating a worker.
          </p>
        ) : null}
      </div>

      {error ? (
        <p className="mt-3 rounded border border-red-400/30 bg-red-500/5 px-3 py-2 text-xs text-red-300">
          Dispatch failed: {error}
        </p>
      ) : null}

      {result ? (
        <div className="mt-4 space-y-3" data-testid="mission-dispatch-result">
          <dl className="grid gap-2 text-xs sm:grid-cols-4">
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">loop state</dt>
              <dd className="mt-0.5 font-mono text-white/85" data-testid="mission-dispatch-state">
                {result.loop_state ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">run state</dt>
              <dd className="mt-0.5 font-mono text-white/85">{result.state}</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">provider</dt>
              <dd className="mt-0.5 font-mono text-white/85">
                {result.provider ?? "—"} · {result.model ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">run</dt>
              <dd className="mt-0.5 font-mono text-white/85">{result.run_id}</dd>
            </div>
          </dl>

          {result.loop_reason ? (
            <p className="rounded border border-line bg-ink/60 px-3 py-2 font-mono text-[11px] text-white/70">
              reason: {result.loop_reason}
            </p>
          ) : null}

          <div>
            <p className="mb-1 font-mono text-[10px] uppercase tracking-widest text-white/35">
              Granted tool envelope (server-reported)
            </p>
            {(result.effective_tools ?? []).length === 0 ? (
              <p className="text-xs text-white/40">No tools were granted to this run.</p>
            ) : (
              <ul className="flex flex-wrap gap-1.5">
                {(result.effective_tools ?? []).map((tool) => (
                  <li
                    key={tool}
                    className="rounded border border-line bg-ink/60 px-2 py-0.5 font-mono text-[11px] text-white/70"
                  >
                    {tool}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {(result.turns ?? []).length === 0 ? (
            <p className="text-xs text-white/40">
              The loop recorded no model turns. A reason above, not an invented transcript, is the evidence.
            </p>
          ) : (
            <ol className="space-y-2">
              {(result.turns ?? []).map((turn) => (
                <li key={turn.turn_index} className="rounded border border-line bg-ink/60 p-2">
                  <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
                    turn {turn.turn_index} · {turn.decision ?? "—"}
                    {turn.tool_name ? ` · ${turn.tool_name}` : ""}
                  </p>
                  <p className="mt-1 whitespace-pre-wrap break-words text-xs text-white/70">
                    {(turn.text ?? "").slice(0, 2000) || "—"}
                  </p>
                </li>
              ))}
            </ol>
          )}

          <p className="rounded border border-gold/30 bg-gold/5 px-3 py-2 text-xs text-gold/90">
            Dispatch state <span className="font-mono">{result.state}</span> is a proposal awaiting human review.
            It is not an acceptance, and this surface cannot merge, deploy, or self-authorize.
          </p>
        </div>
      ) : null}
    </Panel>
  );
}
