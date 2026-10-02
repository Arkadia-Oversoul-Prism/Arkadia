import { useParams, Link } from "react-router-dom";
import { APPROVAL_NOT_EXECUTION } from "../data/approvalNotExecution";
import { EXECUTION_NOT_WORK_EVENT } from "../data/executionNotWorkEvent";
import { WORK_EVENT_NOT_EVIDENCE } from "../data/workeventNotEvidence";
import { EVIDENCE_NOT_VERIFICATION } from "../data/evidenceNotVerification";
import { stageById, STAGES, type StageId } from "../lib/grammar";
import { deploymentLadder, postureTone } from "../lib/posture";
import { authorityState } from "../lib/authority";
import { VERB_MEANING, type Verb, type BoundaryInstance } from "../lib/boundary";
import { Card, Chip, Pill, PostureChip } from "../components/ui";

/** The worked boundary instances the console can render end-to-end. */
const WORKED: BoundaryInstance[] = [APPROVAL_NOT_EXECUTION, EXECUTION_NOT_WORK_EVENT, WORK_EVENT_NOT_EVIDENCE, EVIDENCE_NOT_VERIFICATION];

/**
 * The boundary instance view — the primary unit of the console (architecture §9 Q5).
 *
 * Resolves a worked boundary instance or a generic stage. A worked boundary is
 * rendered end-to-end: authority, posture, evidence, consequences, and available
 * operator verbs.
 */
export function BoundaryView() {
  const { id } = useParams<{ id: string }>();

  const worked = WORKED.find((b) => b.id === id);
  if (worked) {
    return <WorkedBoundary b={worked} />;
  }

  const stageId = (id ?? "").toUpperCase() as StageId;
  if (STAGES.some((s) => s.id === stageId)) {
    return <StageDetail id={stageId} />;
  }

  return (
    <Card title="Unknown boundary">
      <p className="small dim" style={{ marginTop: 0 }}>
        No boundary named <span className="mono">{id}</span>.{" "}
        <Link to="/inspector">Open the Boundary Inspector</Link>.
      </p>
    </Card>
  );
}

function StageDetail({ id }: { id: StageId }) {
  const s = stageById(id);
  return (
    <div className="grid" style={{ gap: 16 }}>
      <Card
        title={s.label}
        actions={<Link to="/inspector" className="btn ghost sm">← inspector</Link>}
      >
        <p className="small dim" style={{ marginTop: 0 }}>{s.question}</p>
        <div className="grid cols-2" style={{ gap: 16 }}>
          <div>
            <div className="subhead">Surface</div>
            <div className="mono tiny">{s.surface}</div>
            <div className="subhead mt">Enforcement</div>
            <div className="mono tiny">{s.enforcement}</div>
          </div>
          <div>
            <div className="subhead">Evidence</div>
            <ul className="evidence-list">
              {s.evidence.map((e) => (
                <li key={e} className="mono tiny">{e}</li>
              ))}
            </ul>
            <div className="subhead mt">Posture</div>
            <PostureChip posture={s.posture} />
          </div>
        </div>
        {s.posture.note && <p className="tiny faint mt">{s.posture.note}</p>}
      </Card>
    </div>
  );
}

function VerbRow({ verb, blocked }: { verb: Verb; blocked?: boolean }) {
  return (
    <div className={`verb ${blocked ? "verb-blocked" : "verb-available"}`}>
      <span className="verb-name mono">{verb}</span>
      <span className="verb-why tiny">{VERB_MEANING[verb]}</span>
      <span className="verb-state tiny">
        {blocked ? "unavailable — Govern authority not held" : "available"}
      </span>
    </div>
  );
}

function WorkedBoundary({ b }: { b: BoundaryInstance }) {
  const auth = authorityState();
  const rungs = deploymentLadder(b.posture.deployment);
  const tone = postureTone(b.posture);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <Card
        title={
          <span className="row" style={{ gap: 12 }}>
            {b.title}
            <Pill tone="muted">{b.from} → {b.to}</Pill>
          </span>
        }
        actions={<Link to="/inspector" className="btn ghost sm">← inspector</Link>}
      >
        <p className="small" style={{ marginTop: 0 }}>{b.means}</p>
        <div className="prior-collapse">
          <span className="tiny faint">PRIOR COLLAPSE</span>
          <span className="small">{b.priorCollapse}</span>
        </div>
      </Card>

      {/* Decision and act: two linked objects, never one control. */}
      {b.id === "approval-not-execution" && (
        <Card title="Decision and act are two events">
          <div className="two-events">
            <div className="event event-decision">
              <div className="event-tag mono">APPROVAL</div>
              <div className="event-title">Record a decision</div>
              <div className="event-body tiny faint">
                POST /api/approvals/&#123;id&#125;/approve records status=approved, decided_by, decided_at.
                It does not run the tool.
              </div>
            </div>
            <div className="event-link" aria-hidden>
              <span className="event-link-mark">≠</span>
              <span className="tiny faint">the request carries approval_id; the record does not</span>
            </div>
            <div className="event event-execution">
              <div className="event-tag mono">EXECUTION</div>
              <div className="event-title">Perform the act</div>
              <div className="event-body tiny faint">
                POST /api/tools/&#123;tool&#125;/run requires the approval_id, checks it is unconsumed and
                same-subject, then consumes it.
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Execution and the Work Event spine: separate records, not joined. */}
      {b.id === "execution-not-workevent" && (
        <Card title="Two records, not joined">
          <div className="two-events">
            <div className="event event-decision">
              <div className="event-tag mono">EXECUTION</div>
              <div className="event-title">Perform the act</div>
              <div className="event-body tiny faint">
                A tool run returns a synchronous envelope and consumes its approval
                (consumed_at / consumed_by). A kernel job records its own
                lease.acquired and execution.started/completed events.
              </div>
            </div>
            <div className="event-link" aria-hidden>
              <span className="event-link-mark">≠</span>
              <span className="tiny faint">no identifier connects them</span>
            </div>
            <div className="event event-execution">
              <div className="event-tag mono">WORK EVENT</div>
              <div className="event-title">Record continuity</div>
              <div className="event-body tiny faint">
                A SolSpire WorkEvent is persisted in its own table, created only by
                POST /solspire/workevents. No execution or job path constructs one.
              </div>
            </div>
          </div>
        </Card>
      )}

      <div className="grid cols-2" style={{ gap: 16 }}>
        <Card title="Posture">
          <PostureChip posture={b.posture} />
          <ul className="ladder mt">
            {rungs.map((r) => (
              <li key={r.key} className={r.reached ? "reached" : "unreached"}>
                <span className="rung-lamp" />
                <span className="mono tiny">{r.label}</span>
              </li>
            ))}
          </ul>
          <div className={`posture-verdict tone-${tone}`}>
            {tone === "enforced"
              ? "Fully proven."
              : tone === "declared"
                ? "Declared, not machine-checked."
                : "Enforced, but NOT production-verified."}
          </div>
          {b.posture.note && <p className="tiny faint mt">{b.posture.note}</p>}
        </Card>

        <Card title="Operator verbs">
          {b.verbs.map((v) => (
            <VerbRow key={v} verb={v} />
          ))}
          {b.verbsBlockedByProvisioning.map((v) => (
            <VerbRow key={v} verb={v} blocked />
          ))}
          {b.verbsBlockedByProvisioning.length > 0 && (
            <p className="tiny faint mt">
              AUTHORIZE is shown, but not offered to an ordinary principal. {auth.statement}{" "}
              {auth.constraint}
            </p>
          )}
        </Card>
      </div>

      <Card title="Non-collapses established here">
        <div className="grid" style={{ gap: 10 }}>
          {b.nonCollapses.map((nc) => (
            <div key={`${nc.left}-${nc.right}`} className="noncollapse">
              <div className="row" style={{ gap: 10, alignItems: "center" }}>
                <span className="chain-node">{nc.left}</span>
                <span className="neq">≠</span>
                <span className="chain-node">{nc.right}</span>
                <Pill tone={nc.enforced ? "enforced" : "declared"}>
                  {nc.enforced ? "ENFORCED" : "DECLARED"}
                </Pill>
              </div>
              <ul className="evidence-list">
                {nc.evidence.map((e) => (
                  <li key={e} className="mono tiny">{e}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Card>

      {b.id === "approval-not-execution" && (
        <Card title="Evidence chain">
          <p className="tiny faint" style={{ marginTop: 0 }}>
            The path a reviewer traverses to prove the decision and the act are distinct.
          </p>
          <div className="evidence-chain">
            {[
              ["approval_id", "the request carries this key; the job record does not persist it"],
              ["subject_ref", "who proposed — must equal the executing subject"],
              ["decided_by", "the distinct authority that recorded the decision"],
              ["consumed_at / consumed_by", "the act consumed the approval, once"],
              ["tool envelope", "the synchronous result: {success, results, tool_used, summary}"],
              ["job / trace", "a kernel-loop record, IF one was enqueued — not a persisted join"],
            ].map(([k, why], i, arr) => (
              <div key={k} className="chain-link">
                <div className="chain-step">
                  <span className="mono tiny">{k}</span>
                  <span className="tiny faint">{why}</span>
                </div>
                {i < arr.length - 1 && <span className="chain-arrow" aria-hidden>↓</span>}
              </div>
            ))}
          </div>
        </Card>
      )}

      {b.id === "execution-not-workevent" && (
        <Card title="Evidence chain">
          <p className="tiny faint" style={{ marginTop: 0 }}>
            What execution records — and where the chain stops, because no WorkEvent is created.
          </p>
          <div className="evidence-chain">
            {[
              ["tool envelope", "the synchronous result: {success, results, tool_used, summary}"],
              ["approval consumed_at / consumed_by", "the act is recorded on the approval"],
              ["job execution.events", "lease.acquired, execution.started/completed — kernel-internal"],
              ["job / trace", "the kernel-loop record of what ran (if a job was enqueued)"],
              ["work_event_id", "ABSENT — no execution → WorkEvent identifier exists"],
            ].map(([k, why], i, arr) => (
              <div key={k} className="chain-link">
                <div className="chain-step">
                  <span className="mono tiny">{k}</span>
                  <span className="tiny faint">{why}</span>
                </div>
                {i < arr.length - 1 && <span className="chain-arrow" aria-hidden>↓</span>}
              </div>
            ))}
          </div>
        </Card>
      )}

      {b.id === "workevent-not-evidence" && (
        <Card title="Evidence chain">
          <p className="tiny faint" style={{ marginTop: 0 }}>
            What a WorkEvent records — and where the chain stops, because no evidence is produced.
          </p>
          <div className="evidence-chain">
            {[
              ["work_event_id", "the continuity record, created by POST /solspire/workevents"],
              ["artifact_refs / decision_ref / witness_ref", "opaque references — no code resolves them to a record"],
              ["evidence from the WorkEvent", "ABSENT — creating a WorkEvent produces no evidence"],
              ["ew_evidence.execution_attempt_id", "the runtime evidence chain binds to an execution attempt — a different spine"],
              ["ew_verifications.evidence_refs", "a list of evidence ids, never a work_event_id"],
              ["work_event → evidence identifier", "ABSENT — no table or field joins the two"],
            ].map(([k, why], i, arr) => (
              <div key={k} className="chain-link">
                <div className="chain-step">
                  <span className="mono tiny">{k}</span>
                  <span className="tiny faint">{why}</span>
                </div>
                {i < arr.length - 1 && <span className="chain-arrow" aria-hidden>↓</span>}
              </div>
            ))}
          </div>
        </Card>
      )}

      {b.id === "evidence-not-verification" && (
        <Card title="Evidence chain">
          <p className="tiny faint" style={{ marginTop: 0 }}>
            How evidence becomes a verification — and why the link is a correlation, not a join.
          </p>
          <div className="evidence-chain">
            {[
              ["ew_evidence.id (ev-…)", "the durable evidence record — created alone, unverified"],
              ["ew_evidence.source_ref / execution_attempt_id", "what the evidence is bound to (a foreign key on the attempt)"],
              ["ew_verifications.evidence_refs", "a JSON text list citing evidence ids — NOT a foreign key"],
              ["projection join", "instr(v.evidence_refs, e.id) — substring match, correlation not constraint"],
              ["ew_verifications.id (vr-…)", "a separate durable record with its own verdict and verifier"],
              ["evidence → verification pointer", "ABSENT — evidence carries no reverse column; the link lives only on the verification"],
            ].map(([k, why], i, arr) => (
              <div key={k} className="chain-link">
                <div className="chain-step">
                  <span className="mono tiny">{k}</span>
                  <span className="tiny faint">{why}</span>
                </div>
                {i < arr.length - 1 && <span className="chain-arrow" aria-hidden>↓</span>}
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card title="Surfaces touched">
        <div className="chips">
          {b.surfaces.map((s) => (
            <Chip key={s}>{s}</Chip>
          ))}
        </div>
      </Card>

      <Card title="Unresolved">
        <ul className="unresolved-list">
          {b.unresolved.map((u) => (
            <li key={u}>{u}</li>
          ))}
        </ul>
        <p className="tiny faint mt">
          These are persistent posture, not warnings that disappear.
        </p>
      </Card>
    </div>
  );
}
