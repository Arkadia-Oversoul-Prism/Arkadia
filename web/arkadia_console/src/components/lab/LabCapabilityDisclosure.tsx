import { NotYetWired } from "../ui";

/**
 * Keep the remaining-surface notice aligned with the controls actually mounted
 * in MissionWorkspace. This describes integration boundaries; it does not
 * claim provider or container availability.
 */
export function LabCapabilityDisclosure() {
  return (
    <NotYetWired
      contract="/api/lab/engineering/sessions/{session_id}/transition"
      note="Already wired in Mission Control: session creation, a separate human authorization step, a bounded read-only investigation, selector-only bounded test requests through the existing execute route, and run-agent dispatch for an already-authorized session. Bounded tests still require the existing authorization and digest-pinned container boundary; model-backed dispatch still depends on a dispatchable provider. Not wired here: session transition, repository mutation, merge, and production deployment. Approval is not execution; a returned report is not independent verification or acceptance."
    />
  );
}
