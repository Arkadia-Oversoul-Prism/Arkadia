/**
 * SolSpire proposals — the read-only proposal ledger.
 *
 * The contract is `GET /solspire/proposals` (`solspire/proposal_router.py`):
 * authenticated, owner-scoped through the subject's canonical workspace, and it
 * answers `{proposals: [...], count: n}`. `409` means no canonical workspace is
 * bound yet — a workspace prerequisite, not a broken read — so it is rendered as
 * a narrow expected refusal rather than a failure.
 *
 * The ledger is deliberately read-only. A proposal's decision
 * (`POST /solspire/proposals/{id}/decision`) and an authorization
 * (`POST /solspire/authority/proposals/{id}/authorize`) are human acts on the
 * authority chain, so this surface offers no control that could imply either.
 * It renders the recorded status only: a proposal being present, or carrying an
 * advanced status, is not an approval, an execution, or an acceptance.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import { isRecord } from "../../lib/records";

const read = <T,>(path: string): Promise<T> => apiRequest<T>(path);

/** The fields the served handler publishes, in the order an operator reads them. */
const LEDGER_FIELDS = [
  "proposal_id",
  "proposal_status",
  "objective",
  "scope",
  "requested_decision",
  "proposal_version",
  "updated_at",
] as const;

/** Epoch seconds (the handler's `time.time()` clock) as an ISO-8601 instant. */
function recordedInstant(value: unknown): string {
  const seconds = typeof value === "number" ? value : Number.NaN;
  if (!Number.isFinite(seconds)) return "UNKNOWN";
  return new Date(seconds * 1000).toISOString().replace(".000Z", "Z");
}

function fieldValue(name: (typeof LEDGER_FIELDS)[number], record: Record<string, unknown>): string {
  const value = record[name];
  if (name === "updated_at") return recordedInstant(value);
  if (value === null || value === undefined || value === "") return "UNKNOWN";
  if (typeof value === "object") return "UNKNOWN";
  return String(value);
}

/** The proposal list a payload carries, or null when it carries none. */
function proposalsFrom(payload: unknown): Record<string, unknown>[] | null {
  if (!isRecord(payload) || !Array.isArray(payload.proposals)) return null;
  return payload.proposals.filter(isRecord);
}

export function ProposalLedger() {
  const ledger = useHydration<unknown>(endpoints.solspireProposals, read<unknown>);
  const proposals = ledger.state === "ready" ? proposalsFrom(ledger.data) : null;
  const workspaceUnbound = ledger.error?.kind === "CONFLICT";

  if (workspaceUnbound) {
    return (
      <Panel className="border-dashed border-line">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Proposal ledger
        </p>
        <p className="text-sm text-white/70">
          No canonical workspace is bound to this identity yet, so there are no proposals to read.
          This is a workspace prerequisite, not an empty ledger and not a failure.
        </p>
        {ledger.error && <p className="mt-1 font-mono text-xs text-white/40">{ledger.error.message}</p>}
        <button
          type="button"
          onClick={ledger.reload}
          className="mt-4 rounded border border-emerald/40 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-emerald"
        >
          Retry
        </button>
      </Panel>
    );
  }

  return (
    <Panel>
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Proposal ledger</p>
      {ledger.state === "ready" ? (
        proposals === null ? (
          <p className="text-sm text-white/70">
            The proposals contract answered with a shape this surface cannot list. No fabricated
            proposal is shown in its place.
          </p>
        ) : proposals.length === 0 ? (
          <p className="text-sm text-white/50">
            No proposals are recorded for this workspace. An empty ledger is not an approval.
          </p>
        ) : (
          <>
            <p className="mb-3 text-sm text-white/60">
              {proposals.length} proposal{proposals.length === 1 ? "" : "s"} recorded. Status is the
              recorded value; deciding or authorizing one is a human act this surface does not offer.
            </p>
            <ul className="flex flex-col gap-2" data-testid="proposal-ledger-list">
              {proposals.map((proposal, index) => (
                <li key={String(proposal.proposal_id ?? index)} className="rounded border border-line bg-ink/40 p-3">
                  <Facts
                    rows={LEDGER_FIELDS.map((name) => ({ label: name, value: fieldValue(name, proposal) }))}
                  />
                </li>
              ))}
            </ul>
          </>
        )
      ) : (
        <ContractState state={ledger.state} error={ledger.error?.message} onRetry={ledger.reload} />
      )}
    </Panel>
  );
}
