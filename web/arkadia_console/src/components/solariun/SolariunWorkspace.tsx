/**
 * Solariun — the persistent cognitive workspace for the active project.
 *
 * Solariun is the surface where a project's persistent material lives: its
 * tasks, its files, its activity, and the conversation that produced them. The
 * mission asks that this be reconciled into the same navigation and interaction
 * system as the rest of the product — without a new persistence layer.
 *
 * So this panel reads the **existing** canonical project sub-resources, the same
 * ones `ProjectsPage` already consumes:
 *
 *   tasks    `GET /solspire/projects/{id}/tasks`
 *   files    `GET /solspire/projects/{id}/files`
 *   activity `GET /solspire/projects/{id}/events`
 *
 * and the conversation collection through `lib/projectConversation.ts`, which is
 * the one write path the console uses to persist a turn. Nothing here creates a
 * store, a second task tracker, or a parallel document model.
 *
 * What it does NOT do: it does not claim a document/notes capability the
 * contracts do not publish. There is no project-document read in
 * `lib/endpoints.ts`, so the panel says so and names the smallest contract
 * change rather than rendering an empty "Documents" list that would read as
 * "you have none".
 */
import { Panel, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import {
  solspireProjectTasks,
  solspireProjectFiles,
  solspireProjectEvents,
} from "../../lib/endpoints";

/** Read a collection payload without assuming its exact envelope. */
function rowsOf(data: unknown): unknown[] {
  if (Array.isArray(data)) return data;
  if (typeof data !== "object" || data === null) return [];
  for (const key of ["items", "rows", "tasks", "files", "events", "results"]) {
    const value = (data as Record<string, unknown>)[key];
    if (Array.isArray(value)) return value;
  }
  return [];
}

/** A short, honest label for one row of an unknown-shaped collection. */
function rowLabel(row: unknown, index: number): string {
  if (typeof row === "string") return row;
  if (typeof row !== "object" || row === null) return `record ${index + 1}`;
  const record = row as Record<string, unknown>;
  for (const key of ["title", "name", "summary", "objective", "path", "id", "event_type"]) {
    const value = record[key];
    if (typeof value === "string" && value) return value;
  }
  return `record ${index + 1}`;
}

function Collection({
  title,
  testid,
  read,
  emptyNote,
}: {
  title: string;
  testid: string;
  read: ReturnType<typeof useHydration<unknown>>;
  emptyNote: string;
}) {
  const rows = read.state === "ready" ? rowsOf(read.data) : [];

  return (
    <section data-testid={testid}>
      <p className="mb-2 font-mono text-[10px] uppercase tracking-wider text-white/40">{title}</p>
      {read.state !== "ready" ? (
        <ContractState state={read.state} error={read.error?.message} onRetry={read.reload} />
      ) : rows.length === 0 ? (
        <p className="text-xs text-white/45" data-testid={`${testid}-empty`}>
          {emptyNote}
        </p>
      ) : (
        <ul className="flex flex-col gap-1">
          {rows.slice(0, 12).map((row, i) => (
            <li key={i} className="truncate font-mono text-[11px] text-white/60">
              {rowLabel(row, i)}
            </li>
          ))}
          {rows.length > 12 ? (
            <li className="font-mono text-[10px] text-white/30">+{rows.length - 12} more</li>
          ) : null}
        </ul>
      )}
    </section>
  );
}

export function SolariunWorkspace({ projectId }: { projectId: string }) {
  const tasks = useHydration<unknown>(solspireProjectTasks(projectId), (p) => apiRequest<unknown>(p));
  const files = useHydration<unknown>(solspireProjectFiles(projectId), (p) => apiRequest<unknown>(p));
  const events = useHydration<unknown>(solspireProjectEvents(projectId), (p) => apiRequest<unknown>(p));

  return (
    <Panel className="mb-4" data-testid="solariun-workspace">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Persistent workspace
      </p>
      <p className="mb-4 text-xs text-white/40">
        The active project's tasks, files and activity, read from the canonical project contracts.
        This is the same material the Projects surface shows — one store, two views.
      </p>

      <div className="flex flex-col gap-4">
        <Collection
          title="Tasks"
          testid="solariun-tasks"
          read={tasks}
          emptyNote="No tasks recorded for this project."
        />
        <Collection
          title="Files"
          testid="solariun-files"
          read={files}
          emptyNote="No files recorded for this project."
        />
        <Collection
          title="Activity"
          testid="solariun-activity"
          read={events}
          emptyNote="No activity recorded for this project."
        />
      </div>

      <div
        className="mt-4 rounded border border-line bg-ink/40 p-3"
        data-testid="solariun-documents-unavailable"
      >
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <span className="text-sm text-white/80">Documents &amp; notes</span>
          <span className="font-mono text-[10px] uppercase tracking-wider text-white/30">
            unavailable
          </span>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-white/50">
          No project-document read is published in the console's endpoint registry, so this panel
          does not render a document list — an empty list would read as "you have none", which is a
          different claim from "the contract does not exist".
        </p>
        <p className="mt-2 font-mono text-[10px] leading-relaxed text-teal/60">
          smallest contract change: a `GET /solspire/projects/&#123;id&#125;/documents` read, or a
          `documents` field on the project record.
        </p>
      </div>
    </Panel>
  );
}
