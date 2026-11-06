import { Page, NotYetWired } from "../components/ui";
import { WeaverOrchestration } from "../components/weaver/WeaverOrchestration";

/**
 * Weaver — governed execution and orchestration.
 *
 * The surface composes the real read models (approval ledger, canonical work
 * loop, session ladder with runs/events/evidence/artifacts, deployed agents) and
 * declares the orchestration dimensions the contracts do not publish. It does
 * not invent workers, progress or telemetry, and it wires no mutating act:
 * authorizing, executing and transitioning are human decisions taken on the
 * Engineering Lab's mission workspace, not here.
 */
export function WeaverPage() {
  return (
    <Page
      title="Weaver"
      subtitle="Governed execution and orchestration. Proposal, approval, execution, and verification remain distinct stages."
    >
      <WeaverOrchestration />

      <NotYetWired
        contract="/api/lab/engineering/sessions/{id}/execute"
        note="Authorize, execute, transition, and run-agent are mutating Lab-state acts on the session view above. They require a human decision and are not wired to this read-only surface — an approval is not an execution, and a run at the review boundary is not acceptance."
      />
    </Page>
  );
}
