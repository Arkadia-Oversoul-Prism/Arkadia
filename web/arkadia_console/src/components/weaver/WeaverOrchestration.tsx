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
 * AO-006 closed three of those four gaps at the contract level: the run record
 * now publishes `depends_on`, `subtasks`, `attempt` and `retryable`, and the
 * unified canvas (`/api/canvas`) projects them together with an explicit
 * `updated_at`-based poll contract. Those three dimensions are therefore no
 * longer declared unavailable here — they are read from the canvas. The one
 * remaining declaration is live worker telemetry, which is still a real gap:
 * no SSE/WebSocket orchestration transport is served, so the surface labels the
 * read as polled rather than live.
 *
 * The frontend wiring of the canvas sections into this component is declared
 * deferred in the AO-006 PR body: the backend contract and its guard land here,
 * and the surface consumes them in the follow-up. Until then this component
 * keeps its existing real read models and declares only the telemetry gap.
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
