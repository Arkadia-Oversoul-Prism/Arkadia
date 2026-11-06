/**
 * The contextual inspector — region (C) of the workspace.
 *
 * It shows *live state*, and it is careful about what a state indicator is
 * allowed to imply. The lifecycle strip renders the seven stages
 * (Understand → Propose → Authorize → Execute → Verify → Accept → Release) and
 * each stage carries its own evidence state, so a green dot never stands in for
 * a claim the evidence does not support:
 *
 *   proposed ≠ authorized · running ≠ completed · completed ≠ verified ·
 *   verified ≠ accepted · accepted ≠ released
 *
 * The strip is driven by the canonical governed chain
 * (`GET /solspire/voice/events/{id}/chain`, see `lib/missionLifecycle.ts`).
 * A stage with no recorded evidence renders `unknown`; a stage the backend
 * cannot represent at all renders `unavailable` with a plain reason. Neither
 * ever reads as complete.
 *
 * The permissions block reads the *real* authorization contract. When no grant
 * is linked it says so plainly rather than showing an empty "allowed" list,
 * because an absent grant must never read as unrestricted access.
 */
import { type ReactNode } from "react";
import { Panel, Facts, StatusPill } from "../ui";

export type LifecycleStage =
  | "understand"
  | "propose"
  | "authorize"
  | "execute"
  | "verify"
  | "accept"
  | "release";

export type StageState = "done" | "active" | "pending" | "refused" | "unavailable" | "unknown";

export interface Lifecycle {
  stage: LifecycleStage;
  state: StageState;
  /** The evidence that justifies this state, or why there is none. */
  evidence?: string;
}

const STAGE_LABEL: Record<LifecycleStage, string> = {
  understand: "Understand",
  propose: "Propose",
  authorize: "Authorize",
  execute: "Execute",
  verify: "Verify",
  accept: "Accept",
  release: "Release",
};

const STATE_TONE: Record<StageState, string> = {
  done: "text-emerald",
  active: "text-gold",
  pending: "text-white/35",
  refused: "text-red-300",
  unavailable: "text-white/25",
  // `unknown` is deliberately the dimmest tone: no evidence exists, so the
  // stage must not read as progress. It is distinct from `pending` (the chain
  // is in progress but this stage is not reached) and from `unavailable`
  // (the contract could not be read at all).
  unknown: "text-white/20",
};

export interface InspectorContext {
  projectName?: string;
  projectId?: string;
  branch?: string;
  revision?: string;
  taskLabel?: string;
  taskState?: string;
  sources?: Array<{ label: string; detail?: string }>;
  /** The linked authorization, if any. Absent means no grant is linked. */
  authorization?: {
    ref: string;
    operations: string[];
    usable: boolean;
    reason?: string;
  } | null;
  approvals?: Array<{ id: string; label: string; state: string }>;
  evidence?: Array<{ label: string; detail?: string }>;
  lifecycle?: Lifecycle[];
  /**
   * Where the lifecycle state came from, in plain terms.
   *
   * The strip is driven by the canonical governed chain
   * (`GET /solspire/voice/events/{id}/chain`). When that read is refused or
   * unreachable the note says so, so a viewer never reads an all-pending strip
   * as "nothing has happened" when the truth is "we could not look".
   */
  lifecycleNote?: string;
  /**
   * The canonical project thread this conversation is recorded against.
   *
   * Absent means no project is active, so there is no thread to report. When
   * present, `state` is the truth: `attached` means the turn-append route is
   * reachable, `unavailable` means it is not and the conversation is not being
   * persisted. The inspector must never imply persistence it does not have.
   */
  thread?: {
    state: "idle" | "attaching" | "attached" | "unavailable";
    conversationId?: string;
    note?: string | null;
  };
  /**
   * Additional live panels contributed by the active surface.
   *
   * The inspector is the one place that shows "what is true right now" for the
   * workspace, so a capability that has real live state (the Engineering Lab's
   * repository context, the Weaver approval ledger) renders *here* rather than
   * on a separate page the user has to leave the conversation to reach. The
   * slot is a `ReactNode`, not a data contract: the contributing surface owns
   * its own reads and its own honest empty/unavailable states, and the
   * inspector only decides where they sit.
   */
  panels?: ReactNode;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="cg-inspector-section">
      <p className="cg-inspector-title">{title}</p>
      {children}
    </section>
  );
}

export function Inspector({ context }: { context: InspectorContext }) {
  const auth = context.authorization;
  return (
    <div className="cg-inspector-body" data-testid="workspace-inspector">
      <Section title="Context">
        {context.projectName ? (
          <Facts
            rows={[
              { label: "Project", value: context.projectName },
              ...(context.projectId ? [{ label: "Project id", value: context.projectId }] : []),
              ...(context.branch ? [{ label: "Branch", value: context.branch }] : []),
              ...(context.revision ? [{ label: "Revision", value: context.revision }] : []),
            ]}
          />
        ) : (
          <p className="cg-inspector-empty">
            No project selected. Choose one in the rail to attach this conversation to its work.
          </p>
        )}
      </Section>

      <Section title="Active task">
        {context.taskLabel ? (
          <div className="flex items-center justify-between gap-2">
            <span className="min-w-0 break-words text-xs text-white/75">{context.taskLabel}</span>
            <StatusPill state={context.taskState === "running" ? "live" : "off"} label={context.taskState ?? "unknown"} />
          </div>
        ) : (
          <p className="cg-inspector-empty">No task is active in this conversation.</p>
        )}
      </Section>

      <Section title="Lifecycle">
        <ol className="cg-lifecycle" data-testid="workspace-lifecycle">
          {(context.lifecycle ?? []).map((entry) => (
            <li key={entry.stage} className="cg-lifecycle-step">
              <span className={`cg-lifecycle-dot ${STATE_TONE[entry.state]}`} aria-hidden />
              <div className="min-w-0">
                <p className="text-[11px] text-white/75">
                  {STAGE_LABEL[entry.stage]}
                  <span className="ml-2 font-mono text-[9px] uppercase tracking-widest text-white/35">
                    {entry.state}
                  </span>
                </p>
                {entry.evidence ? (
                  <p className="mt-0.5 break-words text-[10px] text-white/40">{entry.evidence}</p>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
        <p className="cg-inspector-note">
          Each stage is a separate recorded act. A stage marked done is not a claim that the next one
          happened.
        </p>
        {context.lifecycleNote ? (
          <p className="cg-inspector-note" data-testid="workspace-lifecycle-source">
            {context.lifecycleNote}
          </p>
        ) : null}
      </Section>

      <Section title="Permissions">
        {auth ? (
          <div data-testid="workspace-authorization">
            <Facts
              rows={[
                { label: "Grant", value: auth.ref },
                { label: "Usable", value: auth.usable ? "yes" : "no" },
                { label: "Operations", value: auth.operations.length ? auth.operations.join(", ") : "none named" },
                ...(auth.reason ? [{ label: "Reason", value: auth.reason }] : []),
              ]}
            />
          </div>
        ) : (
          <p className="cg-inspector-empty" data-testid="workspace-no-authorization">
            No authorization is linked to this session. Consequential operations are refused — an
            absent grant is the empty set, never unrestricted access.
          </p>
        )}
      </Section>

      <Section title="Pending approvals">
        {context.approvals?.length ? (
          <ul className="cg-inspector-list">
            {context.approvals.map((approval) => (
              <li key={approval.id} className="cg-inspector-item">
                <span className="min-w-0 break-words text-xs text-white/75">{approval.label}</span>
                <StatusPill state={approval.state === "pending" ? "warn" : "off"} label={approval.state} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="cg-inspector-empty">Nothing is waiting on a human decision.</p>
        )}
      </Section>

      <Section title="Project thread">
        {context.thread ? (
          <div data-testid="workspace-thread">
            <Facts
              rows={[
                { label: "State", value: context.thread.state },
                ...(context.thread.conversationId
                  ? [{ label: "Conversation", value: context.thread.conversationId }]
                  : []),
              ]}
            />
            {context.thread.note ? (
              <p className="cg-inspector-note" data-testid="workspace-thread-note">
                {context.thread.note}
              </p>
            ) : null}
            <p className="cg-inspector-note">
              Turns are recorded through the canonical project-conversation service, which composes
              the project record, the Knowledge OS note and the project activity event. This surface
              keeps no second store.
            </p>
          </div>
        ) : (
          <p className="cg-inspector-empty">
            No project is active, so this conversation is not being recorded against one.
          </p>
        )}
      </Section>

      <Section title="Sources">
        {context.sources?.length ? (
          <ul className="cg-inspector-list">
            {context.sources.map((source, i) => (
              <li key={i} className="cg-inspector-item">
                <span className="min-w-0 break-words text-xs text-white/75">{source.label}</span>
                {source.detail ? (
                  <span className="font-mono text-[10px] text-white/35">{source.detail}</span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="cg-inspector-empty">No sources are attached to this turn.</p>
        )}
      </Section>

      <Section title="Evidence">
        {context.evidence?.length ? (
          <ul className="cg-inspector-list">
            {context.evidence.map((item, i) => (
              <li key={i} className="cg-inspector-item">
                <span className="min-w-0 break-words text-xs text-white/75">{item.label}</span>
                {item.detail ? (
                  <span className="font-mono text-[10px] text-white/35">{item.detail}</span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="cg-inspector-empty">No evidence has been recorded for this conversation yet.</p>
        )}
      </Section>

      {context.panels}

      <Panel className="cg-inspector-boundary">
        <p className="font-mono text-[10px] uppercase tracking-widest text-gold/70">Boundary</p>
        <p className="mt-1 text-[11px] leading-relaxed text-white/50">
          SolSpire coordinates capabilities; it does not grant them authority. Conversational intent
          never substitutes for a required authorization.
        </p>
      </Panel>
    </div>
  );
}
