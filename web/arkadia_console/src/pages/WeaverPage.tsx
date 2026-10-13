import { Page, NotYetWired } from "../components/ui";
import { LabSessionList } from "../components/lab/LabSessionList";
import { ApprovalLedger } from "../components/weaver/ApprovalLedger";

export function WeaverPage() {
  return (
    <Page
      title="Weaver"
      subtitle="Governed execution and orchestration. Proposal, approval, execution, and verification remain distinct stages."
    >
      <ApprovalLedger />

      <LabSessionList />

      <NotYetWired
        contract="/api/lab/engineering/sessions/{id}/execute"
        note="Authorize, execute, transition, and run-agent are mutating Lab-state acts on the session view above. They require a human decision and are not wired to this read-only surface — an approval is not an execution, and a run at the review boundary is not acceptance."
      />
    </Page>
  );
}
