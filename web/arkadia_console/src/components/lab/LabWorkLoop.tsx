/**
 * Engineering Lab — canonical work-loop read model (Workstream 4, feature-local).
 *
 * Recovers the canonical DB->PLAN->EXECUTE work-loop projection onto the Weaver
 * surface. The loop is the *runtime definition* the Lab's own overview returns
 * (`GET /api/lab/engineering/overview` -> `loop`); it is not a live run-status
 * indicator and it grants no authority. Listing a stage does not mean that stage
 * has been entered, let alone completed.
 *
 * Read-only by construction: this module issues a single GET and reaches no
 * mutating Lab endpoint. Its whole reason to exist is the governance distinction
 * that Weaver holds — a stage in a loop is a description of the pipeline, not an
 * approval, an execution, or acceptance.
 *
 * This is a feature-local read model, not a new endpoint registration
 * (SHARED-CONTRACTS.md §3.1): it consumes the existing `labEngineeringOverview`
 * registry member and adds nothing to `lib/endpoints.ts`.
 */
import { Panel, ContractState } from "../ui";
import { ExecutionLoop } from "./ExecutionLoop";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";

/** The overview shape this read model depends on — only the `loop` field. */
interface LabOverviewLoop {
  loop?: unknown;
}

/** Keep only the stages the backend actually returned as strings. */
function loopStages(loop: unknown): string[] {
  if (!Array.isArray(loop)) return [];
  return loop.filter((stage): stage is string => typeof stage === "string");
}

export function LabWorkLoop() {
  // Anchor on the declared registry member so the path is not a page-local
  // literal (the endpoint-registry guard requires the `endpoints.` reference).
  const overview = useHydration<LabOverviewLoop>(endpoints.labEngineeringOverview, (p) =>
    apiRequest<LabOverviewLoop>(p),
  );

  return (
    <div className="mb-4" data-testid="lab-work-loop">
      {overview.state === "ready" && overview.data ? (
        <ExecutionLoop stages={loopStages(overview.data.loop)} />
      ) : (
        <Panel>
          <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Canonical work loop</p>
          <ContractState
            state={overview.state}
            error={overview.error?.message}
            onRetry={overview.reload}
          />
        </Panel>
      )}
    </div>
  );
}
