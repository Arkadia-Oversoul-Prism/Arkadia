/**
 * Repository context — the Lab's inspectable-engineering-output reading
 * (AEAS-01 P0.3).
 *
 * The mission workspace tells the operator what a run *reported*; this panel
 * shows what the tree *is*: branch, source revision, the real change inventory,
 * and the actual staged/unstaged diff — all observed by the backend through the
 * bounded read-only git boundary, never assembled on the client.
 *
 * Three honesty constraints it exists to keep:
 *
 *  1. **UNKNOWN never renders as a healthy default.** A status read that failed
 *     shows "not observed" with its reason, not "clean" and not "0 files".
 *  2. **An empty diff is distinct from an unread one.** "empty — the read
 *     succeeded and printed nothing" is a fact; an unavailable diff carries its
 *     reason instead of a blank block that reads as "no differences".
 *  3. **This surface cannot mutate.** There is no stage, checkout, or reset
 *     control here, because the contract it reads has no such operation.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import {
  buildRepositoryFacts,
  describeCoverage,
  describeDiff,
  type RepositoryContext,
} from "./labRepository";

/** Rows rendered before the list spills into its coverage note. */
const MAX_RENDERED_CHANGES = 100;

function ChangeRow({ entry }: { entry: RepositoryContext["changes"]["files"][number] }) {
  return (
    <li className="flex items-baseline gap-2 text-xs" data-testid="lab-repository-change">
      <span className="shrink-0 rounded border border-white/20 px-1.5 py-0.5 font-mono text-[10px] text-white/60">
        {entry.code}
      </span>
      <span className="shrink-0 font-mono text-[10px] uppercase tracking-widest text-azure">
        {entry.label}
      </span>
      <span className="min-w-0 break-all font-mono text-[11px] text-white/70">
        {entry.path}
        {entry.original_path ? (
          <span className="text-white/40"> (from {entry.original_path})</span>
        ) : null}
      </span>
      <span className="ml-auto shrink-0 font-mono text-[10px] text-white/35">
        {entry.staged ? "staged" : ""}
        {entry.staged && entry.unstaged ? " · " : ""}
        {entry.unstaged ? "worktree" : ""}
        {!entry.staged && !entry.unstaged ? "untracked/ignored" : ""}
      </span>
    </li>
  );
}

function DiffSide({
  title,
  side,
  testid,
}: {
  title: string;
  side: RepositoryContext["diff"]["unstaged"] | undefined;
  testid: string;
}) {
  const reading = describeDiff(side);
  const observed = side?.status === "observed";
  return (
    <details
      className="rounded border border-line bg-ink/60 px-3 py-2"
      data-testid={testid}
      open={observed}
    >
      <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-widest text-white/55">
        {title} · {reading}
      </summary>
      {observed && side ? (
        <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] text-white/70">
          {side.text || "— empty —"}
        </pre>
      ) : (
        <p className="mt-2 text-xs text-white/45">{reading}</p>
      )}
    </details>
  );
}

export function LabRepositoryContext() {
  const view = useHydration<RepositoryContext>(endpoints.labRepository, (p) =>
    apiRequest<RepositoryContext>(p),
  );

  // Narrow once: everything below renders only from a confirmed reading.
  const data = view.state === "ready" ? view.data : null;
  const changes = data ? data.changes : null;
  const unobserved = Boolean(data) && (changes === null || changes.status !== "observed");
  const files = changes && changes.status === "observed" ? changes.files : [];

  return (
    <Panel className="mb-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">
          Repository context · observed read-only
        </p>
        <button
          type="button"
          onClick={view.reload}
          disabled={view.state === "loading"}
          data-testid="lab-repository-refresh"
          className="font-mono text-[10px] uppercase tracking-widest text-white/40 hover:text-white/80 disabled:opacity-30"
        >
          Re-observe
        </button>
      </div>

      {!data ? (
        <ContractState state={view.state} error={view.error?.message} onRetry={view.reload} />
      ) : (
        <div data-testid="lab-repository-panel">
          <Facts rows={buildRepositoryFacts(data)} />

          {unobserved ? (
            <p
              className="mt-3 rounded border border-amber-400/40 bg-amber-400/5 px-3 py-2 text-xs text-amber-200/90"
              data-testid="lab-repository-unobserved"
            >
              The working tree was NOT observed — this is not a clean-tree claim.{" "}
              {changes?.reason ? <span className="font-mono">{changes.reason}</span> : null}
            </p>
          ) : null}

          <div className="mt-4">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/40">
              Changed files · {describeCoverage(changes)}
            </p>
            {files.length === 0 ? (
              <p className="text-xs text-white/45" data-testid="lab-repository-changes-empty">
                {changes?.status === "observed"
                  ? "Working tree observed clean — git status printed no entries."
                  : "No inventory observed."}
              </p>
            ) : (
              <ul className="space-y-1.5" data-testid="lab-repository-changes">
                {files.slice(0, MAX_RENDERED_CHANGES).map((entry) => (
                  <ChangeRow key={`${entry.code}:${entry.path}`} entry={entry} />
                ))}
              </ul>
            )}
            {files.length > MAX_RENDERED_CHANGES ? (
              <p className="mt-2 text-xs text-white/40">
                Showing the first {MAX_RENDERED_CHANGES} entries; the observation is capped at{" "}
                {files.length}.
              </p>
            ) : null}
          </div>

          <div className="mt-4 space-y-2">
            <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
              Diff · against the source revision above
            </p>
            <DiffSide title="Staged" side={data.diff?.staged} testid="lab-repository-diff-staged" />
            <DiffSide
              title="Unstaged (working tree)"
              side={data.diff?.unstaged}
              testid="lab-repository-diff-unstaged"
            />
          </div>

          <p className="mt-3 text-xs text-white/40">
            {data.boundary ?? "Observation boundary not stated by the handler."} · This surface
            has no stage, checkout, or reset control: reading the repository is not changing it.
          </p>
        </div>
      )}
    </Panel>
  );
}
