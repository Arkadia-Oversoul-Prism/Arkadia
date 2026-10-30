/**
 * Bounded test operation on the mission workspace.
 *
 * Posts one `test` operation to the existing execute route. The server pins
 * the command; this panel sends a selector only. Whatever comes back is
 * labeled as the substrate's report — never as independent verification,
 * acceptance, or a live worker.
 *
 * The panel keeps its own in-flight flag. It does not take the workspace
 * busy lock, so inspection of the mission stays available while a request
 * is outstanding.
 */
import { useState } from "react";
import { ApiError } from "../../lib/apiClient";
import { Panel } from "../ui";
import {
  executeBoundedTest,
  localTestSelectorRefusal,
  type LabObservation,
  type LabRunResult,
} from "./missionContract";

interface LabBoundedTestProps {
  sessionId: string;
  sessionState: string;
  /** Operations named by an authorization recorded in this view.
   *  `null` means the terms were not re-read (resume). The server still decides. */
  namedOperations: string[] | null;
  objective: string;
  onSettled?: () => Promise<void> | void;
}

type PanelStatus = "IDLE" | "RUNNING" | "REPORTED" | "UNAVAILABLE" | "REFUSED" | "FAILED" | "NOT_SENT";

interface TestObservation extends LabObservation {
  returncode?: number | null;
  stdout?: string;
  stderr?: string;
  argv?: string[];
  truncated?: boolean;
  boundary?: string;
}

function describeError(error: unknown): string {
  if (error instanceof ApiError) return `${error.status ?? "—"} ${error.kind}: ${error.message}`;
  if (error && typeof error === "object" && "message" in error) {
    return String((error as { message: unknown }).message);
  }
  return String(error);
}

/** Classify a transport failure. A missing boundary is not a suite result. */
export function classifyTestTransport(message: string): "UNAVAILABLE" | "REFUSED" | "FAILED" {
  const text = message.toLowerCase();
  if (
    text.includes("unknown operation kind") ||
    text.includes("read/list only") ||
    text.includes("container") ||
    text.includes("digest") ||
    text.includes("sandbox unavailable") ||
    (text.includes("image") && text.includes("pinned"))
  ) {
    return "UNAVAILABLE";
  }
  if (
    text.includes("does not permit") ||
    text.includes("session must be authorized") ||
    text.includes("session != authorization") ||
    text.includes("conflict") ||
    text.includes(" 409 ")
  ) {
    return "REFUSED";
  }
  return "FAILED";
}

function clip(value: string, limit = 4000): string {
  if (value.length <= limit) return value;
  return `${value.slice(0, limit)}\n… truncated in this view; the server record is authoritative`;
}

export function LabBoundedTest({
  sessionId,
  sessionState,
  namedOperations,
  objective,
  onSettled,
}: LabBoundedTestProps) {
  const [selector, setSelector] = useState("");
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<PanelStatus>("IDLE");
  const [notice, setNotice] = useState<string | null>(null);
  const [result, setResult] = useState<LabRunResult | null>(null);

  const executable = sessionState === "AUTHORIZED" || sessionState === "QUEUED";
  const grantKnown = namedOperations !== null;
  const testNamed = !grantKnown || namedOperations.includes("test");
  const selectorRefusal = localTestSelectorRefusal(selector);
  const canRun = executable && testNamed && !selectorRefusal && !running;

  async function handleRun(): Promise<void> {
    const refusal = localTestSelectorRefusal(selector);
    if (refusal) {
      setResult(null);
      setStatus("NOT_SENT");
      setNotice(`Not sent. Local preflight: ${refusal}. This is not a test result.`);
      return;
    }
    setRunning(true);
    setStatus("RUNNING");
    setNotice("Request in flight. This is not a live execution signal — only the response below is evidence.");
    setResult(null);
    try {
      const reported = await executeBoundedTest(
        sessionId,
        objective.trim() || "Run the bounded test operation",
        selector,
      );
      setResult(reported);
      setStatus("REPORTED");
      setNotice(
        "The fields below are what the execute route returned. They are the operation's own report, not an independent verification and not acceptance.",
      );
    } catch (error) {
      const message = describeError(error);
      const kind = classifyTestTransport(message);
      setResult(null);
      setStatus(kind);
      setNotice(
        kind === "UNAVAILABLE"
          ? `Unavailable. The runtime did not produce a test result. ${message}`
          : kind === "REFUSED"
            ? `Refused before a result. ${message}`
            : `The execute request failed. ${message}`,
      );
    } finally {
      setRunning(false);
      try {
        await onSettled?.();
      } catch {
        /* the test response above stays authoritative if the view refresh fails */
      }
    }
  }

  const observations = (result?.observations ?? []) as TestObservation[];

  return (
    <Panel>
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3" data-testid="mission-test-panel">
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">
            Bounded test — existing execute route
          </p>
          <p className="mt-1 text-xs text-white/35">
            Sends one <span className="font-mono">test</span> operation. This console does not send a command.
            The server pins the allowlist. A refusal stays a refusal — nothing here is labeled verified.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void handleRun()}
          disabled={!canRun}
          data-testid="mission-test-button"
          className="min-h-11 rounded border border-emerald/40 px-3 py-2 font-mono text-[11px] uppercase tracking-widest text-emerald enabled:hover:border-emerald/70 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {running ? "Request in flight…" : "Run bounded test"}
        </button>
      </div>

      <label className="block text-xs text-white/50" htmlFor="mission-test-selector">
        Optional selector
        <input
          id="mission-test-selector"
          data-testid="mission-test-selector"
          value={selector}
          onChange={(event) => setSelector(event.target.value)}
          placeholder="tests/test_example.py::test_name"
          spellCheck={false}
          autoCapitalize="off"
          className="mt-1 w-full rounded border border-line bg-ink px-2 py-2 font-mono text-xs text-white"
        />
      </label>
      <p className="mt-1 text-[11px] text-white/35">
        Empty runs the server-pinned suite. A selector names a test. It cannot pass options or a shell.
      </p>

      {!executable ? (
        <p className="mt-3 rounded border border-gold/30 bg-gold/5 px-3 py-2 text-xs text-gold/90">
          The session is {sessionState}. The substrate runs a test operation only from AUTHORIZED or QUEUED.
          SESSION is not AUTHORIZATION.
        </p>
      ) : null}

      {executable && grantKnown && !testNamed ? (
        <p className="mt-3 rounded border border-gold/30 bg-gold/5 px-3 py-2 text-xs text-gold/90">
          The authorization recorded in this view does not name test ({namedOperations.join(", ") || "none"}).
          This surface will not widen that grant.
        </p>
      ) : null}

      {executable && !grantKnown ? (
        <p className="mt-3 text-xs text-white/40">
          An authorization reference may be attached, but its operations were not re-read. The server decides
          whether test is permitted and this panel will show that decision.
        </p>
      ) : null}

      {selectorRefusal ? (
        <p className="mt-3 rounded border border-amber-300/30 bg-amber-300/5 px-3 py-2 text-xs text-amber-200/90">
          Not sent. Local preflight: {selectorRefusal}. This is not a test result.
        </p>
      ) : null}

      <p className="mt-3 font-mono text-[10px] uppercase tracking-widest text-white/40" data-testid="mission-test-status">
        Status {status}
        {running ? " — workspace stays usable" : ""}
      </p>
      {notice ? <p className="mt-2 text-xs text-white/70">{notice}</p> : null}

      {result ? (
        <div className="mt-4 space-y-3" data-testid="mission-test-result">
          <dl className="grid gap-2 text-xs sm:grid-cols-3">
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">result state</dt>
              <dd className="mt-0.5 font-mono text-white/85">{result.result_state}</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">run state</dt>
              <dd className="mt-0.5 font-mono text-white/85">{result.state}</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">run</dt>
              <dd className="mt-0.5 break-all font-mono text-white/85">{result.run_id}</dd>
            </div>
          </dl>
          <p className="text-xs text-white/45">
            Reported by the bounded execute operation for session {result.session_id}. No diff is invented when
            the operation does not return one. Evidence refs: {(result.evidence_refs ?? []).join(", ") || "none returned"}.
          </p>
          {observations.length === 0 ? (
            <p className="text-xs text-white/40">The response included no observations.</p>
          ) : (
            <ul className="space-y-3">
              {observations.map((observation, index) => (
                <li key={`${observation.kind}-${index}`} className="rounded border border-line bg-ink/60 px-3 py-2">
                  <p className="font-mono text-[10px] uppercase tracking-widest text-white/45">
                    {observation.kind} · ok {String(observation.ok ?? "unspecified")}
                    {observation.returncode !== undefined ? ` · exit ${String(observation.returncode)}` : ""}
                    {observation.boundary ? ` · ${observation.boundary}` : ""}
                    {observation.truncated ? " · output truncated by the boundary" : ""}
                  </p>
                  {observation.error ? (
                    <p className="mt-2 text-xs text-red-300">{observation.error}</p>
                  ) : null}
                  {observation.argv && observation.argv.length > 0 ? (
                    <p className="mt-2 break-all font-mono text-[11px] text-white/50">
                      argv reported by the boundary: {observation.argv.join(" ")}
                    </p>
                  ) : null}
                  {observation.stdout ? (
                    <pre
                      data-testid="mission-test-stdout"
                      className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] text-white/70"
                    >
                      {clip(observation.stdout)}
                    </pre>
                  ) : null}
                  {observation.stderr ? (
                    <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] text-amber-100/80">
                      {clip(observation.stderr)}
                    </pre>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </Panel>
  );
}
