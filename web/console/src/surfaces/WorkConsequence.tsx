import { useState } from "react";
import { Link } from "react-router-dom";
import * as ep from "../api/endpoints";
import { ApiError } from "../api/client";
import type { Approval, Job } from "../api/types";
import { useAsync } from "../lib/hooks";
import { executionFor, approvalsForJob, jobRecordedKey, LINK_WINDOW_SECONDS } from "../lib/lineage";
import { Card, Pill, Chip } from "../components/ui";

/**
 * 03 · Work / Consequence — the operational view (read-only).
 *
 * Reads the live substrate and renders what actually exists. Truthful emptiness
 * is preserved: an empty list is shown as empty, never filled with invented
 * records. There are no mutation controls on this surface — inspection only.
 */

type Connection = "connecting" | "connected" | "auth" | "unreachable";

function connectionOf(errors: (Error | null)[], loading: boolean): Connection {
  const err = errors.find(Boolean) as Error | undefined;
  if (err) {
    if (err instanceof ApiError && (err.isAuth || err.isForbidden)) return "auth";
    return "unreachable";
  }
  if (loading) return "connecting";
  return "connected";
}

function ConnectionBanner({ state }: { state: Connection }) {
  const map: Record<Connection, { tone: string; text: string }> = {
    connecting: { tone: "muted", text: "CONNECTING — reading the substrate" },
    connected: { tone: "enforced", text: "CONNECTED — reading live substrate (read-only)" },
    auth: {
      tone: "unverified",
      text: "AUTH REQUIRED (401/403) — the substrate rejected the session. Live data is unavailable.",
    },
    unreachable: {
      tone: "unprovisioned",
      text: "UNREACHABLE — the substrate did not answer. Live data is unavailable.",
    },
  };
  const m = map[state];
  return (
    <div className={`conn conn-${state}`}>
      <Pill tone={m.tone}>{m.text}</Pill>
    </div>
  );
}

function Empty({ what }: { what: string }) {
  return (
    <div className="empty">
      <div className="empty-mark">◌</div>
      <div>No {what}.</div>
      <div className="tiny faint mt">Truthful emptiness — nothing is fabricated to fill this view.</div>
    </div>
  );
}

function fmtTime(t: number | string | null | undefined): string {
  if (t === null || t === undefined) return "—";
  const ms = typeof t === "number" ? t * 1000 : Date.parse(t);
  if (Number.isNaN(ms)) return String(t);
  return new Date(ms).toISOString().replace("T", " ").slice(0, 19);
}

export function WorkConsequence() {
  const approvals = useAsync(() => ep.approvals(), []);
  const jobs = useAsync(() => ep.jobs(), []);
  const tools = useAsync(() => ep.tools(), []);

  const conn = connectionOf(
    [approvals.error, jobs.error, tools.error],
    approvals.loading && jobs.loading,
  );

  const approvalList: Approval[] = approvals.data?.approvals ?? [];
  const jobList: Job[] = jobs.data?.jobs ?? [];
  const requiresApproval: Record<string, boolean> = Object.fromEntries(
    (tools.data?.tools ?? []).map((t) => [t.name, t.requires_approval === true]),
  );

  const [selApproval, setSelApproval] = useState<string | null>(null);
  const [selJob, setSelJob] = useState<string | null>(null);

  const activeApproval = approvalList.find((a) => a.id === selApproval) ?? null;
  const activeJob = jobList.find((j) => j.job_id === selJob) ?? null;

  const lineage = activeApproval ? executionFor(activeApproval, jobList) : null;
  const reverse = activeJob ? approvalsForJob(activeJob, approvalList) : [];

  return (
    <div className="grid" style={{ gap: 16 }}>
      <Card title="Connection">
        <ConnectionBanner state={conn} />
        <p className="tiny faint" style={{ marginBottom: 0 }}>
          This surface reads approvals, jobs and the tool registry. It exposes no mutation control.
          Lineage between them is inferred where the substrate records enough, and labelled as inferred.
        </p>
      </Card>

      <Card
        title="Approvals"
        actions={approvals.data ? <Pill tone="muted">{approvalList.length}</Pill> : undefined}
      >
        {approvals.error ? (
          <Empty what="live approvals (substrate not reachable)" />
        ) : approvalList.length === 0 ? (
          <Empty what="approvals" />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Approval</th>
                  <th>Tool</th>
                  <th>Status</th>
                  <th>Subject</th>
                  <th>Decided by</th>
                  <th>Consumed</th>
                </tr>
              </thead>
              <tbody>
                {approvalList.map((a) => (
                  <tr
                    key={a.id}
                    className={`row-select ${selApproval === a.id ? "selected" : ""}`}
                    onClick={() => setSelApproval(a.id)}
                  >
                    <td className="mono tiny">{a.id}</td>
                    <td className="mono tiny">
                      {a.tool_name}
                      {requiresApproval[a.tool_name] && (
                        <span className="gate-dot" title="approval-gated">
                          {" "}
                          ●
                        </span>
                      )}
                    </td>
                    <td>
                      <Pill
                        tone={
                          a.status === "approved"
                            ? "enforced"
                            : a.status === "pending"
                              ? "unverified"
                              : "muted"
                        }
                      >
                        {a.status}
                      </Pill>
                    </td>
                    <td className="mono tiny">{a.subject_ref ?? "—"}</td>
                    <td className="mono tiny">{a.decided_by ?? "—"}</td>
                    <td className="tiny">{a.consumed_at ? fmtTime(a.consumed_at) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="tiny faint mt">Select an approval to follow its forward lineage.</p>
      </Card>

      {activeApproval && lineage && (
        <Card
          title={`Forward lineage · ${activeApproval.id}`}
          actions={
            <Pill tone={lineage.consumption.consumed ? "enforced" : "unverified"}>
              {lineage.consumption.consumed ? "consumed" : "not consumed"}
            </Pill>
          }
        >
          <div className="subhead">Recorded — exact</div>
          <div className="lin-meta tiny">
            <span>
              decision: <b>{activeApproval.status}</b>
            </span>
            <span>
              subject: <span className="mono">{activeApproval.subject_ref ?? "—"}</span>
            </span>
            <span>
              decided_by: <span className="mono">{activeApproval.decided_by ?? "—"}</span>
            </span>
            <span>
              consumed_at: <span className="mono">{activeApproval.consumed_at ? fmtTime(activeApproval.consumed_at) : "—"}</span>
            </span>
            <span>
              consumed_by: <span className="mono">{activeApproval.consumed_by ?? "—"}</span>
            </span>
          </div>
          <p className="tiny faint">{lineage.note}</p>

          <div className="subhead" style={{ marginTop: 12 }}>
            Inferred — attributable execution records
          </div>
          {lineage.executions.length > 0 ? (
            <div className="grid" style={{ gap: 8 }}>
              {lineage.executions.map((e) => (
                <div key={e.job.job_id} className="lin-card" onClick={() => setSelJob(e.job.job_id)}>
                  <div className="row between">
                    <span className="mono tiny">{e.job.job_id}</span>
                    <Pill tone="muted">{e.job.status}</Pill>
                  </div>
                  <div className="tiny faint">{e.basis}</div>
                  <div className="tiny faint">
                    source: {e.job.source ?? "—"} · created {fmtTime(e.job.created_at)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Empty what="attributable execution records" />
          )}
          <p className="tiny faint">
            The substrate does not persist an approval_id on the job, so this link is <b>inferred</b>{" "}
            (same tool + subject, within {LINK_WINDOW_SECONDS}s of consumption), never joined.
          </p>
        </Card>
      )}

      <Card
        title="Jobs (kernel work items)"
        actions={jobs.data ? <Pill tone="muted">{jobList.length}</Pill> : undefined}
      >
        {jobs.error ? (
          <Empty what="live jobs (substrate not reachable)" />
        ) : jobList.length === 0 ? (
          <Empty what="jobs" />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Job</th>
                  <th>Status</th>
                  <th>Intent</th>
                  <th>Source</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {jobList.map((j) => (
                  <tr
                    key={j.job_id}
                    className={`row-select ${selJob === j.job_id ? "selected" : ""}`}
                    onClick={() => setSelJob(j.job_id)}
                  >
                    <td className="mono tiny">{j.job_id}</td>
                    <td>
                      <Pill
                        tone={
                          j.status === "completed"
                            ? "enforced"
                            : j.status === "failed"
                              ? "unprovisioned"
                              : "unverified"
                        }
                      >
                        {j.status}
                      </Pill>
                    </td>
                    <td className="mono tiny">
                      {String((j.intent && (j.intent.tool_name ?? j.intent.type)) ?? "—")}
                    </td>
                    <td className="tiny">{j.source ?? "—"}</td>
                    <td className="tiny">{fmtTime(j.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {activeJob && (
        <Card
          title={`Reverse lineage · ${activeJob.job_id}`}
          actions={
            <Pill tone={reverse.length ? "enforced" : "muted"}>{reverse.length} attributable</Pill>
          }
        >
          <div className="subhead">Recorded — the job's own forward key</div>
          <div className="lin-meta tiny">
            <span>
              execution.task_id: <span className="mono">{jobRecordedKey(activeJob) ?? "—"}</span>
            </span>
            <span>
              intent.tool_name: <span className="mono">{String(activeJob.intent?.tool_name ?? "—")}</span>
            </span>
            <span>
              intent.subject_ref: <span className="mono">{String(activeJob.intent?.subject_ref ?? "—")}</span>
            </span>
          </div>
          <div className="subhead" style={{ marginTop: 12 }}>
            Inferred — attributable approvals
          </div>
          {reverse.length > 0 ? (
            <div className="chips">
              {reverse.map((a) => (
                <Chip key={a.id}>
                  {a.id} · {a.tool_name}
                </Chip>
              ))}
            </div>
          ) : (
            <Empty what="attributable approvals for this job" />
          )}
          <p className="tiny faint">
            Reverse lineage is inferred by the same tight rule. A job enqueued outside the tool-run
            path carries no subject, so no approval is attributable — absence is shown, not guessed.
          </p>
        </Card>
      )}

      <Card title="Why lineage is inferred, not joined">
        <p className="small" style={{ marginTop: 0 }}>
          The substrate records the two sides independently: an approval carries its subject and its
          consumption; a job carries its intent and source. Neither persists the other's id. Rather
          than fabricate a join the backend does not have, the console infers the link under a narrow
          rule and labels it. Where the substrate records nothing, the console shows nothing.
        </p>
        <p className="tiny faint">
          See the worked boundary for the decision/act separation this lineage evidences:{" "}
          <Link to="/boundary/approval-not-execution">APPROVAL ≠ EXECUTION</Link>.
        </p>
      </Card>

      <Card
        title="EXECUTION ≠ WORK EVENT"
        actions={<Pill tone="unverified">absent — no join</Pill>}
      >
        <p className="small" style={{ marginTop: 0 }}>
          Execution and the Work Event spine are <b>separate records</b> on this substrate, and they
          are <b>not joined</b>. A tool run returns synchronously and, if gated, consumes the
          approval — it creates no job and no WorkEvent. A kernel job records its own execution
          events (<span className="mono">lease.acquired</span>,{" "}
          <span className="mono">execution.started/completed</span>) but references no WorkEvent.
        </p>
        <div className="grid cols-2" style={{ gap: 16 }}>
          <div>
            <div className="subhead">Recorded</div>
            <ul className="evidence-list">
              <li className="tiny">execution evidence on the approval (consumed_at / consumed_by)</li>
              <li className="tiny">kernel job execution events (lease / checkpoints)</li>
              <li className="tiny">SolSpire WorkEvents, in their own spine</li>
            </ul>
          </div>
          <div>
            <div className="subhead">Absent</div>
            <ul className="evidence-list">
              <li className="tiny">a durable execution → WorkEvent identifier</li>
              <li className="tiny">a code path that creates a WorkEvent from an execution</li>
            </ul>
          </div>
        </div>
        <p className="tiny faint">
          The only creator of a WorkEvent is the WorkEvent router itself
          (<span className="mono">/solspire/workevents</span>). No execution or job module constructs
          one. Absence is the measurement, not a defect.
        </p>
        <p className="tiny faint">
          Partially exposed: <span className="mono">weaver/enterprise_orchestration.py</span> holds a
          richer proposal → authority → authorization → execution → evidence → verification graph.
          Its counters and verified evidence content are read over HTTP through the enterprise
          control-room projection; its{" "}
          <span className="mono">forward_walk</span> /{" "}
          <span className="mono">reverse_walk</span> traversal itself has no HTTP route.
        </p>
        <p className="tiny faint">
          See the worked boundary:{" "}
          <Link to="/boundary/execution-not-workevent">EXECUTION ≠ WORK EVENT</Link>.
        </p>
      </Card>

      <Card
        title="WORK EVENT ≠ EVIDENCE"
        actions={<Pill tone="unverified">absent — no join</Pill>}
      >
        <p className="small" style={{ marginTop: 0 }}>
          A WorkEvent is a <b>continuity record</b>, not an evidence record. Creating one through{" "}
          <span className="mono">POST /solspire/workevents</span> produces <b>no</b> evidence and{" "}
          <b>no</b> verification, and its reference fields are opaque strings that no code resolves.
          The runtime evidence chain that does exist binds evidence to an{" "}
          <span className="mono">execution_attempt</span> — a different spine.
        </p>
        <div className="grid cols-2" style={{ gap: 16 }}>
          <div>
            <div className="subhead">Recorded</div>
            <ul className="evidence-list">
              <li className="tiny">the WorkEvent and its opaque references (artifact_refs, decision_ref, witness_ref)</li>
              <li className="tiny">ew_evidence, bound to an execution attempt (enterprise spine)</li>
              <li className="tiny">ew_verifications, referencing evidence ids</li>
            </ul>
          </div>
          <div>
            <div className="subhead">Absent</div>
            <ul className="evidence-list">
              <li className="tiny">a durable WorkEvent → Evidence identifier</li>
              <li className="tiny">any code path that produces evidence from a WorkEvent</li>
              <li className="tiny">a dedicated route exposing evidence or verification as records</li>
            </ul>
          </div>
        </div>
        <p className="tiny faint">
          The WorkEvent manager has no evidence capability, and the enterprise evidence store has no
          WorkEvent capability — the two modules are disjoint. Absence is the measurement, not a defect.
        </p>
        <p className="tiny faint">
          Unexposed: the enterprise evidence → verification → proposal chain is readable over HTTP
          only as a control-room projection; its{" "}
          <span className="mono">forward_walk</span> /{" "}
          <span className="mono">reverse_walk</span> traversal has no HTTP route.
        </p>
        <p className="tiny faint">
          See the worked boundary:{" "}
          <Link to="/boundary/workevent-not-evidence">WORK EVENT ≠ EVIDENCE</Link>.
        </p>
      </Card>

      <Card
        title="EVIDENCE ≠ VERIFICATION"
        actions={<Pill tone="unverified">correlated — not joined</Pill>}
      >
        <p className="small" style={{ marginTop: 0 }}>
          Capturing evidence and verifying a claim are <b>separate records</b>. Evidence is created
          by <span className="mono">EnterpriseOrchestrationStore.evidence()</span> and carries a
          durable id (<span className="mono">ev-…</span>); creating it does <b>not</b> create a
          verification. A verification is a separate call whose{" "}
          <span className="mono">evidence_refs</span> is a JSON text list matched by substring —
          a correlation, not a foreign key.
        </p>
        <div className="grid cols-2" style={{ gap: 16 }}>
          <div>
            <div className="subhead">Recorded</div>
            <ul className="evidence-list">
              <li className="tiny">ew_evidence with a durable id and a real FK to the execution attempt</li>
              <li className="tiny">ew_verifications with its own id, verdict and verifier</li>
              <li className="tiny">the citation: ew_verifications.evidence_refs (JSON text)</li>
            </ul>
          </div>
          <div>
            <div className="subhead">Absent</div>
            <ul className="evidence-list">
              <li className="tiny">a foreign key between evidence and verification</li>
              <li className="tiny">a reverse pointer on ew_evidence to its verification</li>
              <li className="tiny">any route exposing either record as first-class</li>
            </ul>
          </div>
        </div>
        <p className="tiny faint">
          The relationship is asymmetric: a verification <b>requires</b> an existing evidence
          reference, but evidence can stand alone with no verification. Where the forward walk finds
          no verification, it shows none — absence is the measurement, not a defect.
        </p>
        <p className="tiny faint">
          Readable over HTTP only as the control-room projection (
          <span className="mono">GET /solspire/enterprise/workspaces/&#123;id&#125;/control-room</span>
          ); no route creates or lists evidence or verification.
        </p>
        <p className="tiny faint">
          See the worked boundary:{" "}
          <Link to="/boundary/evidence-not-verification">EVIDENCE ≠ VERIFICATION</Link>.
        </p>
      </Card>
    </div>
  );
}
