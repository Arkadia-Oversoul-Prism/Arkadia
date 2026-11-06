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

/**
 * The outcome of reading a collection payload.
 *
 * AO4-07: the previous `rowsOf` returned `[]` for *any* unrecognised envelope,
 * so a changed response shape rendered as "No tasks recorded for this project"
 * — telling the user a project is empty when the truth is that the console
 * could not read the answer. These five states are deliberately distinct:
 *
 *   empty        the contract was understood and genuinely holds no rows
 *   populated    the contract was understood and holds rows
 *   mismatch     the response arrived but its shape is not one we recognise
 *   unavailable  the request could not be made (no identity, no project)
 *   failed       the request was made and failed
 *
 * Only `empty` may ever be rendered as "you have none".
 */
export type CollectionRead =
  | { kind: "empty" }
  | { kind: "populated"; rows: unknown[] }
  | { kind: "mismatch"; detail: string }
  | { kind: "unavailable"; detail: string }
  | { kind: "failed"; detail: string };

/** The envelope keys the canonical project sub-resources are known to use. */
const COLLECTION_KEYS = ["items", "rows", "tasks", "files", "events", "results"] as const;

/**
 * Read a collection payload into a discriminated result.
 *
 * A bare array is a valid collection. An object is valid only when one of the
 * known envelope keys holds an array. Anything else is a `mismatch` — never an
 * empty collection.
 */
export function readCollection(data: unknown): CollectionRead {
  if (Array.isArray(data)) {
    return data.length === 0 ? { kind: "empty" } : { kind: "populated", rows: data };
  }
  if (typeof data !== "object" || data === null) {
    return {
      kind: "mismatch",
      detail: `expected a collection, received ${data === null ? "null" : typeof data}`,
    };
  }
  const record = data as Record<string, unknown>;
  for (const key of COLLECTION_KEYS) {
    const value = record[key];
    if (Array.isArray(value)) {
      return value.length === 0 ? { kind: "empty" } : { kind: "populated", rows: value };
    }
  }
  const keys = Object.keys(record);
  return {
    kind: "mismatch",
    detail: keys.length
      ? `no recognised collection key (saw: ${keys.slice(0, 6).join(", ")})`
      : "the response object is empty",
  };
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
  // The hydration state and the envelope shape are two separate questions, and
  // both must be answered before anything is rendered as a count.
  const result: CollectionRead =
    read.state === "ready"
      ? readCollection(read.data)
      : read.state === "error"
        ? { kind: "failed", detail: read.error?.message ?? "request failed" }
        : { kind: "unavailable", detail: `contract ${read.state}` };

  return (
    <section data-testid={testid}>
      <p className="mb-2 font-mono text-[10px] uppercase tracking-wider text-white/40">{title}</p>
      {result.kind === "unavailable" || result.kind === "failed" ? (
        <ContractState state={read.state} error={read.error?.message} onRetry={read.reload} />
      ) : result.kind === "mismatch" ? (
        // A shape we do not recognise is NOT an empty collection. Saying so is
        // the whole point: the user must never be told a project has no tasks
        // because the response contract changed.
        <p className="text-xs text-gold/80" data-testid={`${testid}-mismatch`}>
          The response shape was not recognised, so this list cannot be shown. This is not an empty
          list — the contract may have changed. ({result.detail})
        </p>
      ) : result.kind === "empty" ? (
        <p className="text-xs text-white/45" data-testid={`${testid}-empty`}>
          {emptyNote}
        </p>
      ) : (
        <ul className="flex flex-col gap-1" data-testid={`${testid}-rows`}>
          {result.rows.slice(0, 12).map((row, i) => (
            <li key={i} className="truncate font-mono text-[11px] text-white/60">
              {rowLabel(row, i)}
            </li>
          ))}
          {result.rows.length > 12 ? (
            <li className="font-mono text-[10px] text-white/30">+{result.rows.length - 12} more</li>
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
