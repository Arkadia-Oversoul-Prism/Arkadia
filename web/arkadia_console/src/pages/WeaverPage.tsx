import { Page, Panel, ContractState, NotYetWired } from "../components/ui";
import { LabSessionList } from "../components/lab/LabSessionList";
import { useAuth } from "../contexts/AuthContext";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";

interface ApprovalRecord {
  id?: string;
  status?: string;
  [key: string]: unknown;
}

export function WeaverPage() {
  const { isAuthenticated } = useAuth();
  const approvals = useHydration<ApprovalRecord[] | { approvals?: ApprovalRecord[] }>(
    endpoints.approvals,
    (p) => apiRequest<ApprovalRecord[] | { approvals?: ApprovalRecord[] }>(p),
    [isAuthenticated],
  );

  const records = Array.isArray(approvals.data)
    ? approvals.data
    : (approvals.data as { approvals?: ApprovalRecord[] } | null)?.approvals ?? [];

  return (
    <Page
      title="Weaver"
      subtitle="Governed execution and orchestration. Proposal, approval, execution, and verification remain distinct stages."
    >
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Approvals</p>
        <p className="mb-4 text-xs text-white/40">
          Approval is not execution. An execution record is not verification.
        </p>
        {approvals.state === "ready" ? (
          records.length === 0 ? (
            <p className="text-sm text-white/50">No pending approvals.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {records.map((r, i) => (
                <li key={r.id ?? i} className="rounded border border-line bg-ink/40 p-3 font-mono text-xs text-white/70">
                  {r.id ?? "approval"} · {r.status ?? "pending"}
                </li>
              ))}
            </ul>
          )
        ) : (
          <ContractState state={approvals.state} error={approvals.error?.message} onRetry={approvals.reload} />
        )}
      </Panel>

      <LabSessionList />

      <NotYetWired
        contract="/api/lab/engineering/sessions/{id}/execute"
        note="Authorize, execute, transition, and run-agent are mutating Lab-state acts on the session view above. They require a human decision and are not wired to this read-only surface — an approval is not an execution, and a run at the review boundary is not acceptance."
      />
    </Page>
  );
}
