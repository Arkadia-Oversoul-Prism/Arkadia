import { Panel } from "../ui";

/**
 * Read-only projection of the loop returned by the authenticated Lab overview.
 * These are canonical stages, not evidence that a run has reached any stage.
 */
export function ExecutionLoop({ stages }: { stages: string[] }) {
  if (stages.length === 0) {
    return (
      <Panel>
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Canonical work loop</p>
        <p className="mt-2 text-sm text-white/55">The backend did not return a loop definition. No stages are inferred.</p>
      </Panel>
    );
  }

  return (
    <Panel>
      <div className="mb-3">
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Canonical work loop</p>
        <p className="mt-1 text-xs text-white/45">
          Runtime definition only — this sequence is not a live run-status indicator or authorization.
        </p>
      </div>
      <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        {stages.map((stage, index) => (
          <li key={`${stage}-${index}`} className="flex min-w-0 items-start gap-3 rounded-lg border border-line bg-ink/40 p-3">
            <span aria-hidden="true" className="font-mono text-[10px] text-white/30">{String(index + 1).padStart(2, "0")}</span>
            <span className="min-w-0 break-words font-mono text-[11px] tracking-wider text-emerald/80">{stage}</span>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-[11px] text-white/35">
        Human authorization remains a distinct gate. Listing a stage does not mean it has been completed.
      </p>
    </Panel>
  );
}
