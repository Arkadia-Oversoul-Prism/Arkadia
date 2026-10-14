/**
 * Engineering Lab — operational authority readings (Workstream 4, feature-local).
 *
 * Renders the `authority`/`counts` reading produced by `labGovernance.ts` over
 * the Lab overview the surface already holds. It issues no request of its own: a
 * pure projection of `GET /api/lab/engineering/overview`, so the read-only
 * ceiling is structural rather than a promise.
 *
 * The Lab states the ceiling it holds and the mutations it forbids. This surface
 * shows those declarations as declarations — a ceiling is not a granted
 * authority, and a declared human gate is not consent. A run counted at the
 * review boundary is awaiting a human decision; it is not an accepted result.
 */
import { Panel } from "../ui";
import { readLabGovernance, type LabGovernanceSource } from "./labGovernance";

function reading(value: number | null, suffix = ""): string {
  return value === null ? "unknown" : `${value}${suffix}`;
}

// Only `null` is unknown. A reported `false` is a reported state, so it must read
// as its own word — collapsing it into "not declared" would turn a declared-open
// gate into an absent one, the exact collapse this surface exists to prevent.
function declared(value: boolean | null, whenTrue: string, whenFalse: string): string {
  if (value === null) return "unknown";
  return value ? whenTrue : whenFalse;
}

export function LabAuthorityReadings({ source }: { source?: LabGovernanceSource | null }) {
  const readingData = readLabGovernance(source);

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Lab authority
      </p>
      <p className="mb-4 text-xs text-white/40">
        What the Lab declares about its own ceiling. A ceiling is the maximum it may hold, not a
        granted authority, and not an execution.
      </p>

      <dl
        className="grid grid-cols-2 gap-x-6 gap-y-1 font-mono text-[11px] text-white/60 sm:grid-cols-3"
        data-testid="lab-authority-readings"
      >
        <div>
          <dt className="text-white/35">ceiling</dt>
          <dd data-testid="lab-authority-ceiling">{reading(readingData.ceiling)}</dd>
        </div>
        <div>
          <dt className="text-white/35">autonomous merge</dt>
          <dd data-testid="lab-authority-merge">
            {declared(readingData.autonomous_merge, "closed", "permitted")}
          </dd>
        </div>
        <div>
          <dt className="text-white/35">autonomous deploy</dt>
          <dd data-testid="lab-authority-deploy">
            {declared(readingData.autonomous_deploy, "closed", "permitted")}
          </dd>
        </div>
        <div>
          <dt className="text-white/35">human gate</dt>
          <dd data-testid="lab-authority-human-gate">
            {declared(readingData.human_authorization_required, "required", "not required")}
          </dd>
        </div>
        <div>
          <dt className="text-white/35">sessions</dt>
          <dd data-testid="lab-authority-sessions">{reading(readingData.sessions)}</dd>
        </div>
        <div>
          <dt className="text-white/35">active</dt>
          <dd data-testid="lab-authority-active">{reading(readingData.active)}</dd>
        </div>
        <div>
          <dt className="text-white/35">awaiting human</dt>
          <dd data-testid="lab-authority-awaiting-human">{reading(readingData.awaiting_human)}</dd>
        </div>
      </dl>

      <p
        className={`mt-3 text-xs ${readingData.mutation_closed && readingData.human_gate_declared ? "text-white/50" : "text-gold/80"}`}
        data-testid="lab-authority-note"
      >
        {readingData.note}
      </p>
    </Panel>
  );
}
