/**
 * Weaver — orchestration and execution inspection, composed from real contracts.
 *
 * The mission asks that Weaver's orchestration views expose real states and
 * outputs: active workers, tasks and subtasks, dependencies, execution states,
 * outputs, errors, logs, retry conditions and human-intervention requirements —
 * with no invented workers, telemetry or execution results.
 *
 * This component therefore does two things, and refuses a third:
 *
 *   1. It **composes** the existing read models that do publish real state —
 *      the approval ledger (`/api/approvals`), the canonical work loop
 *      (`/api/lab/engineering/overview`), the session ladder with its runs,
 *      work events, evidence and artifacts (`/api/lab/engineering/sessions`),
 *      and the deployed-agent registry (`/api/lab/engineering/agents`).
 *   2. It **declares** the dimensions the contracts do not publish, as
 *      `unavailable` with the reason — never as an empty list that reads like
 *      "there are none", and never as a fabricated value.
 *   3. It **refuses** to invent workers, progress percentages, retry counters or
 *      live telemetry. There is no SSE/WebSocket transport for orchestration in
 *      this console, so nothing here claims to be live.
 *
 * The unavailable dimensions are not a UI gap to be papered over: they are a
 * contract gap. `api/lab_routes.py` and `lab/engineering_lab/runtime.py` publish
 * no dependency graph, no subtask decomposition and no retry-condition field, so
 * the smallest honest thing the console can do is say so and name the contract
 * change that would close it.
 */
import { Panel } from "../ui";
import { ApprovalLedger } from "./ApprovalLedger";
import { LabWorkLoop } from "../lab/LabWorkLoop";
import { LabSessionList } from "../lab/LabSessionList";
import { LabAgentRegistry } from "../lab/LabAgentRegistry";

/**
 * Dimensions the orchestration contracts do not publish.
 *
 * Each entry names the dimension, the reason it is unavailable, and the smallest
 * contract-level change that would make it real. This is a declaration, not a
 * placeholder: the surface renders it as `unavailable`, which is a distinct
 * state from "empty" and from "unknown".
 */
const UNAVAILABLE_DIMENSIONS: Array<{ dimension: string; reason: string; contractChange: string }> = [
  {
    dimension: "Task dependencies",
    reason:
      "No Lab or Weaver contract publishes a dependency edge between tasks or runs. A session view returns runs, events, evidence and artifacts — not a graph.",
    contractChange:
      "A `depends_on: string[]` field on the run record in the session view, or a dedicated `/engineering/sessions/{id}/dependencies` read.",
  },
  {
    dimension: "Subtask decomposition",
    reason:
      "A run is the smallest unit the substrate records. There is no subtask record, so a per-subtask progress view would be invented.",
    contractChange:
      "A `subtasks: [{id, state, objective}]` array on the run record, written by the runtime as it decomposes work.",
  },
  {
    dimension: "Retry conditions",
    reason:
      "The runtime records a run's terminal `state` and `result_state`, but not a retry counter or the condition that would permit a retry.",
    contractChange:
      "`attempt: number` and `retryable: boolean` on the run record, plus the policy reference that decided it.",
  },
  {
    dimension: "Live worker telemetry",
    reason:
      "There is no SSE or WebSocket transport for orchestration state in this console. Polling the session view is the only real read, so no live indicator is shown.",
    contractChange:
      "An orchestration event stream, or an explicit `updated_at`-based poll contract the surface can honestly label as polled.",
  },
];

export function WeaverOrchestration() {
  return (
    <div data-testid="weaver-orchestration">
      <ApprovalLedger />

      <LabWorkLoop />

      <LabSessionList />

      <LabAgentRegistry />

      <Panel className="mb-4" data-testid="weaver-unavailable-dimensions">
        <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Not published by the contracts
        </p>
        <p className="mb-4 text-xs text-white/40">
          These orchestration dimensions have no contract behind them. They are shown as
          unavailable rather than as an empty list, because "the substrate does not record this" and
          "there are none" are different facts.
        </p>
        <ul className="flex flex-col gap-3">
          {UNAVAILABLE_DIMENSIONS.map((item) => (
            <li
              key={item.dimension}
              className="rounded border border-line bg-ink/40 p-3"
              data-testid={`weaver-unavailable-${item.dimension.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="text-sm text-white/80">{item.dimension}</span>
                <span className="font-mono text-[10px] uppercase tracking-wider text-white/30">
                  unavailable
                </span>
              </div>
              <p className="mt-1 text-xs leading-relaxed text-white/50">{item.reason}</p>
              <p className="mt-2 font-mono text-[10px] leading-relaxed text-teal/60">
                smallest contract change: {item.contractChange}
              </p>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
