/**
 * Engineering Lab — run → work-event → evidence trace (Workstream 4, feature-local).
 *
 * Renders the linkage ledger produced by `labRunTrace.ts` over the session view
 * the surface already holds. It issues no request of its own: it is a pure
 * projection of `GET /api/lab/engineering/sessions/{id}`, so the read-only
 * ceiling is structural rather than a promise.
 *
 * The ledger's job is to keep five things visibly distinct:
 *
 *   execution (a run) != evidence (a record) != verification (a recorded state)
 *   != review (a boundary) != acceptance (a human act)
 *
 * A reference that does not resolve is shown as unresolved. Nothing is inferred
 * from a record's mere presence, and acceptance is reported only from the human
 * terminal state the substrate records.
 */
import { Panel } from "../ui";
import {
  buildRunTrace,
  type LabTraceSource,
  type RunTrace,
} from "./labRunTrace";

function RunRow({ trace }: { trace: RunTrace }) {
  return (
    <li
      className="rounded border border-line bg-ink/40 p-3"
      data-testid={`lab-trace-run-${trace.run_id}`}
    >
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 font-mono text-[11px]">
        <span className="text-azure/85">{trace.run_id}</span>
        <span className="text-white/70">{trace.state}</span>
        {trace.result_state && <span className="text-white/45">result: {trace.result_state}</span>}
        <span className="text-white/45">
          {trace.events.length} event{trace.events.length === 1 ? "" : "s"} ·{" "}
          {trace.evidence.length} evidence
        </span>
      </div>
      {trace.objective && <p className="mt-1 text-xs text-white/55">{trace.objective}</p>}

      <p className="mt-2 text-xs text-white/55" data-testid={`lab-trace-verification-${trace.run_id}`}>
        verification stage: {trace.verification.stage_entered ? "entered" : "not entered"} ·{" "}
        verification asserted: {trace.verification.asserted ? "yes" : "no"} · {trace.verification.note}
      </p>
      {trace.verification.entered_basis.length > 0 && (
        <p className="mt-1 font-mono text-[10px] text-white/35">
          entered basis: {trace.verification.entered_basis.join(" · ")}
        </p>
      )}
      {trace.verification.asserted_basis.length > 0 && (
        <p className="mt-1 font-mono text-[10px] text-white/35">
          asserted basis: {trace.verification.asserted_basis.join(" · ")}
        </p>
      )}

      <p className="mt-1 text-xs text-white/55">
        review: {trace.review.at_boundary ? "at the human review boundary" : "not at the boundary"} ·
        human decision required: {trace.review.human_decision_required ? "yes" : "no"} ·{" "}
        {trace.review.note}
      </p>

      {trace.events.length > 0 && (
        <ul className="mt-2 flex flex-col gap-0.5" data-testid={`lab-trace-events-${trace.run_id}`}>
          {trace.events.map((event) => (
            <li key={event.event_id} className="font-mono text-[10px] text-white/50">
              <span className="text-azure/70">{event.event_type ?? "event"}</span>
              {typeof event.sequence === "number" ? ` · #${event.sequence}` : ""}
              {event.timestamp_utc ? ` · ${event.timestamp_utc}` : ""}
            </li>
          ))}
        </ul>
      )}

      {trace.evidence.length > 0 && (
        <ul className="mt-2 flex flex-col gap-0.5" data-testid={`lab-trace-evidence-${trace.run_id}`}>
          {trace.evidence.map((record) => (
            <li key={record.evidence_id} className="font-mono text-[10px] text-white/50">
              {record.evidence_id} · {record.state ?? "recorded"} · recorded, not a verdict
            </li>
          ))}
        </ul>
      )}

      {(trace.dangling_evidence_refs.length > 0 || trace.unreferenced_evidence_ids.length > 0) && (
        <p className="mt-2 text-[11px] text-gold/80" data-testid={`lab-trace-partial-${trace.run_id}`}>
          {trace.dangling_evidence_refs.length > 0 &&
            `declared evidence reference(s) that do not resolve: ${trace.dangling_evidence_refs.join(", ")}. `}
          {trace.unreferenced_evidence_ids.length > 0 &&
            `evidence linked by run_ref but absent from the run's own evidence_refs: ${trace.unreferenced_evidence_ids.join(", ")}.`}
        </p>
      )}
    </li>
  );
}

export function LabRunTrace({ view }: { view: LabTraceSource }) {
  const ledger = buildRunTrace(view);
  const accepted = ledger.acceptance.state === "HUMAN_ACCEPTED";

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Run → work event → evidence trace
      </p>
      <p className="mb-4 text-xs text-white/40">
        Read-only. Each run is joined to its work events and evidence records on the references the
        substrate recorded. A reference that does not resolve is reported as unresolved, never
        guessed. An execution is not evidence, evidence is not verification, verification is not
        review, and review is not acceptance.
      </p>

      {ledger.runs.length === 0 ? (
        <p className="text-sm text-white/50" data-testid="lab-trace-empty">
          No runs recorded for this session, so there is nothing to trace. An authorized session is
          not an executed run.
        </p>
      ) : (
        <ul className="flex flex-col gap-2" data-testid="lab-trace-runs">
          {ledger.runs.map((trace) => (
            <RunRow key={trace.run_id} trace={trace} />
          ))}
        </ul>
      )}

      {ledger.session_events.length > 0 && (
        <p className="mt-3 text-xs text-white/45" data-testid="lab-trace-session-events">
          {ledger.session_events.length} session-level work event
          {ledger.session_events.length === 1 ? "" : "s"} carry no run reference (for example the
          session's own creation). Recorded work, not a run&apos;s work.
        </p>
      )}

      {ledger.evidence_without_verification.length > 0 && (
        <p className="mt-3 text-xs text-gold/80" data-testid="lab-trace-evidence-without-verification">
          {ledger.evidence_without_verification.length} run
          {ledger.evidence_without_verification.length === 1 ? "" : "s"} produced evidence that no
          recorded value verifies. Evidence is a record, not a verdict.
        </p>
      )}

      <p
        className={`mt-3 text-xs ${accepted ? "text-emerald/80" : "text-white/45"}`}
        data-testid="lab-trace-acceptance"
      >
        acceptance: {accepted ? "recorded by a human" : "not recorded"} · {ledger.acceptance.note}
      </p>

      <p className="mt-2 text-xs text-white/45" data-testid="lab-trace-unresolved">
        {ledger.unresolved.length > 0
          ? ledger.unresolved.join(" ")
          : "No references were recorded in this view, so none are unresolved."}
      </p>
    </Panel>
  );
}
