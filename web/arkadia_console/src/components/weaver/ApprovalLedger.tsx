/**
 * Weaver — approval ledger surface (Workstream 4, feature-local).
 *
 * Renders `endpoints.approvals` (`GET /api/approvals`, authenticated and
 * owner/govern-scoped) through the pure projection in `approvalLedger.ts`.
 *
 * Read-only by construction: GET only. Requesting, approving, and rejecting are
 * mutating governance acts (`POST /api/approvals/...`) and stay unwired — deciding
 * an approval is a `Govern`-authority act, and executing the permitted tool is a
 * further separate act at the tool-run boundary. The surface shows where an
 * approval sits; it never advances it.
 *
 * The ledger distinguishes a recorded decision from an execution: a `DECIDED`
 * record is an authorization, and the execution boundary is only reached when a
 * real consumption is recorded. It reports a self-decision as a boundary
 * violation (the backend refuses self-approval) rather than showing a decision
 * the backend would not have produced.
 */
import { Panel, ContractState } from "../ui";
import { useAuth } from "../../contexts/AuthContext";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import {
  buildApprovalLedger,
  type ApprovalPayload,
  type ApprovalReading,
} from "./approvalLedger";

const PHASE_TONE: Record<string, string> = {
  REQUESTED: "text-azure",
  DECIDED: "text-gold",
  CONSUMED: "text-emerald",
  UNKNOWN: "text-white/45",
};

function ReadingRow({ reading }: { reading: ApprovalReading }) {
  return (
    <li
      className="rounded border border-line bg-ink/40 p-3"
      data-testid={`weaver-approval-${reading.id}`}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-mono text-xs text-white/80">{reading.tool_name}</span>
        <span
          className={`font-mono text-[11px] uppercase tracking-wider ${PHASE_TONE[reading.phase]}`}
          data-testid={`weaver-approval-phase-${reading.id}`}
          data-phase={reading.phase}
        >
          {reading.phase}
        </span>
      </div>
      {reading.description && (
        <p className="mt-1 text-xs text-white/55">{reading.description}</p>
      )}
      <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
        <span>status {reading.status_known ? reading.status : `${reading.status} (unknown)`}</span>
        {reading.subject_ref && <span>subject {reading.subject_ref}</span>}
        {reading.decided_by && <span>decided by {reading.decided_by}</span>}
        {reading.consumed_at && <span>consumed {reading.consumed_at}</span>}
        {reading.self_rejected && <span data-testid={`weaver-approval-withdrawn-${reading.id}`}>withdrawn</span>}
      </dl>
      <p
        className={`mt-2 text-xs ${reading.boundary_violation ? "text-red-300" : "text-white/50"}`}
        data-testid={`weaver-approval-note-${reading.id}`}
      >
        {reading.note}
      </p>
    </li>
  );
}

export function ApprovalLedger() {
  const { isAuthenticated } = useAuth();
  const approvals = useHydration<ApprovalPayload>(endpoints.approvals, (p) =>
    apiRequest<ApprovalPayload>(p),
    [isAuthenticated],
  );

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">Approvals</p>
      <p className="mb-4 text-xs text-white/40">
        An approval is an authorization, not the execution it authorizes. A decision records a
        human gate; the permitted action is taken later, at the tool boundary.
      </p>

      {approvals.state === "ready" ? (
        <LedgerBody payload={approvals.data} />
      ) : (
        <ContractState
          state={approvals.state}
          error={approvals.error?.message}
          onRetry={approvals.reload}
        />
      )}
    </Panel>
  );
}

function LedgerBody({ payload }: { payload: ApprovalPayload | null }) {
  const { readings, counts, violations } = buildApprovalLedger(payload);

  if (readings.length === 0) {
    return <p className="text-sm text-white/50">No approvals recorded for this identity.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="font-mono text-[10px] uppercase tracking-wider text-white/40" data-testid="weaver-approval-counts">
        {counts.total} total · {counts.pending} requested · {counts.decided} decided ·{" "}
        {counts.consumed} consumed
        {counts.unknown > 0 ? ` · ${counts.unknown} unknown` : ""}
      </p>

      {violations.length > 0 && (
        <p
          className="rounded border border-red-400/40 bg-red-400/5 p-2 text-xs text-red-300"
          data-testid="weaver-approval-violations"
        >
          {violations.length} record(s) carry a state the backend would not have produced.
          A decision must come from a different authority than the requester.
        </p>
      )}

      <ul className="flex flex-col gap-2" data-testid="weaver-approvals">
        {readings.map((reading) => (
          <ReadingRow key={reading.id} reading={reading} />
        ))}
      </ul>
    </div>
  );
}
