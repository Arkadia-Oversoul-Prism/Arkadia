/**
 * Engineering Lab — run → work-event → evidence → artifact trace (Workstream 4, feature-local).
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
 * An artifact is a *captured proposal*: it is shown joined to the run that
 * captured it and is never presented as an applied change, an evidence record,
 * or a verdict.
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
          {trace.evidence.length} evidence · {trace.artifacts.length} artifact
          {trace.artifacts.length === 1 ? "" : "s"}
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

      {trace.artifacts.length > 0 && (
        <ul className="mt-2 flex flex-col gap-0.5" data-testid={`lab-trace-artifacts-${trace.run_id}`}>
          {trace.artifacts.map((artifact) => (
            <li key={artifact.artifact_id} className="font-mono text-[10px] text-white/50">
              {artifact.artifact_id} · {artifact.kind ?? "artifact"}
              {artifact.title ? ` · ${artifact.title}` : ""} · captured, not applied
            </li>
          ))}
        </ul>
      )}

      {(trace.dangling_evidence_refs.length > 0 ||
        trace.unreferenced_evidence_ids.length > 0 ||
        trace.dangling_artifact_refs.length > 0 ||
        trace.unreferenced_artifact_ids.length > 0) && (
        <p className="mt-2 text-[11px] text-gold/80" data-testid={`lab-trace-partial-${trace.run_id}`}>
          {trace.dangling_evidence_refs.length > 0 &&
            `declared evidence reference(s) that do not resolve: ${trace.dangling_evidence_refs.join(", ")}. `}
          {trace.unreferenced_evidence_ids.length > 0 &&
            `evidence linked by run_ref but absent from the run's own evidence_refs: ${trace.unreferenced_evidence_ids.join(", ")}. `}
          {trace.dangling_artifact_refs.length > 0 &&
            `declared artifact reference(s) that do not resolve: ${trace.dangling_artifact_refs.join(", ")}. `}
          {trace.unreferenced_artifact_ids.length > 0 &&
            `artifacts linked by run_id but absent from the run's own artifact_refs: ${trace.unreferenced_artifact_ids.join(", ")}.`}
        </p>
      )}
    </li>
  );
}

/**
 * One session-level linkage classification, rendered by *identity*.
 *
 * The ledger reports these as a total inside `ledger.unresolved`, which tells a
 * reader that a reference failed to resolve but never which one. A duplicate id
 * is dropped from the traced set rather than merged, so the identity is the only
 * way to find the record the surface left out.
 */
function LinkageGroup({
  kind,
  label,
  ids,
  note,
}: {
  kind: string;
  label: string;
  ids: string[];
  note: string;
}) {
  if (ids.length === 0) return null;
  return (
    <li className="text-xs text-gold/80" data-testid={`lab-trace-linkage-${kind}`}>
      {ids.length} {label}: <span className="font-mono text-[10px] text-white/55">{ids.join(", ")}</span>{" "}
      {note}
    </li>
  );
}

export function LabRunTrace({ view }: { view: LabTraceSource }) {
  const ledger = buildRunTrace(view);
  const accepted = ledger.acceptance.state === "HUMAN_ACCEPTED";

  const linkage = [
    {
      kind: "unlinked-events",
      label: "work event(s) name a run that is not in this view",
      ids: ledger.unlinked_events.map((event) => event.event_id),
      note: "Recorded work whose run is absent.",
    },
    {
      kind: "unlinked-evidence",
      label: "evidence record(s) name a run not in this view",
      ids: ledger.unlinked_evidence.map((record) => record.evidence_id),
      note: "Not attributed to any run here.",
    },
    {
      kind: "unattributed-evidence",
      label: "evidence record(s) carry no run reference",
      ids: ledger.unattributed_evidence.map((record) => record.evidence_id),
      note: "A record with no link, not a link that failed.",
    },
    {
      kind: "unlinked-artifacts",
      label: "artifact(s) name a run not in this view",
      ids: ledger.unlinked_artifacts.map((artifact) => artifact.artifact_id),
      note: "A captured proposal whose run is absent.",
    },
    {
      kind: "unattributed-artifacts",
      label: "artifact(s) carry no run reference",
      ids: ledger.unattributed_artifacts.map((artifact) => artifact.artifact_id),
      note: "Captured with no link, not a link that failed.",
    },
    {
      kind: "duplicate-evidence",
      label: "duplicate evidence id(s) in the view",
      ids: ledger.duplicate_evidence_ids,
      note: "Only the first record per id is traced.",
    },
    {
      kind: "duplicate-artifacts",
      label: "duplicate artifact id(s) in the view",
      ids: ledger.duplicate_artifact_ids,
      note: "Only the first record per id is traced.",
    },
  ].filter((group) => group.ids.length > 0);

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Run → work event → evidence → artifact trace
      </p>
      <p className="mb-4 text-xs text-white/40">
        Read-only. Each run is joined to its work events, evidence records, and captured artifacts
        on the references the substrate recorded. A reference that does not resolve is reported as
        unresolved, never guessed. An execution is not evidence, evidence is not verification,
        verification is not review, review is not acceptance, and an artifact is a captured
        proposal, not an applied change.
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

      {linkage.length > 0 && (
        <ul
          className="mt-3 flex flex-col gap-1 border-t border-line/60 pt-3"
          data-testid="lab-trace-linkage"
        >
          {linkage.map((group) => (
            <LinkageGroup
              key={group.kind}
              kind={group.kind}
              label={group.label}
              ids={group.ids}
              note={group.note}
            />
          ))}
        </ul>
      )}

      <p className="mt-2 text-xs text-white/45" data-testid="lab-trace-unresolved">
        {ledger.unresolved.length > 0
          ? ledger.unresolved.join(" ")
          : "No references were recorded in this view, so none are unresolved."}
      </p>
    </Panel>
  );
}
