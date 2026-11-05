/**
 * Projects — discovery and navigation across the workspace's projects.
 *
 * Backed by the verified SolSpire project contracts the console already reads
 * elsewhere (`GET /solspire/projects` on the Solariun `projects` lens): the list
 * read, the per-project detail read, and the per-project tasks / files / events
 * sub-resources. The runtime-context canvas is the same component Solariun
 * renders, so the two surfaces share one reading of a project rather than
 * forking it.
 *
 * The sub-resource shapes (`tasks`, `files`, `events`) are declared
 * `additionalProperties: true` in the served OpenAPI document, so this surface
 * does not invent a schema for them: it renders the scalar fields each record
 * actually carries, and says so when a read returns a shape it cannot list.
 * Nothing here is mock data.
 *
 * A project is addressed as a *section* of this surface (`/projects/<id>`),
 * which the shared router already resolves for any declared surface — the same
 * shape `/solariun/<lens>` uses. The address bar therefore agrees with the
 * rendered view, and a project link is deep-linkable.
 */
import { useEffect, useMemo, useState } from "react";
import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { ProjectRuntimeCanvas } from "../components/solariun/ProjectRuntimeCanvas";
import { useHydration, type Hydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import {
  solspireProject,
  solspireProjectTasks,
  solspireProjectFiles,
  solspireProjectEvents,
} from "../lib/endpoints";
import { asItems, readRecord, scalarRows } from "../lib/records";
import { useProjectContext } from "../lib/projectContext";
import type { SurfaceId } from "../lib/surfaces";

const UNKNOWN_CONTRACT = "UNKNOWN";

/**
 * A sub-resource list whose record schema is not published. It renders the
 * scalar fields of each item, or an honest note when the payload is not a list.
 * Presentational: the read is owned by the caller, so the endpoint path stays a
 * registry-derived expression at the `useHydration` call site.
 */
function RecordList({ title, read, testid }: { title: string; read: Hydration<unknown>; testid: string }) {
  return (
    <Panel>
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">{title}</p>
      {read.state === "ready" ? (
        (() => {
          const items = asItems(read.data);
          if (items === null) {
            return (
              <NotYetWired
                contract={UNKNOWN_CONTRACT}
                note="This sub-resource answered with a shape the console cannot list. No fabricated list is shown in its place."
              />
            );
          }
          if (items.length === 0) {
            return <p className="text-sm text-white/50">No {title.toLowerCase()} recorded for this project.</p>;
          }
          return (
            <ul className="flex flex-col gap-2" data-testid={testid}>
              {items.map((item, index) => (
                <li key={index} className="rounded border border-line bg-ink/40 p-3">
                  <Facts rows={scalarRows(item)} />
                </li>
              ))}
            </ul>
          );
        })()
      ) : (
        <ContractState state={read.state} error={read.error?.message} onRetry={read.reload} />
      )}
    </Panel>
  );
}

function ProjectDetail({ projectId, onNavigate }: { projectId: string; onNavigate: (id: SurfaceId, section?: string) => void }) {
  const { selectProject } = useProjectContext();

  // Opening a project's detail *is* the act of selecting it. The selection is
  // shared, so "Discuss in Arkana" and "Open Engineering Lab" open on the same
  // project this page is showing rather than on whatever each surface last held.
  useEffect(() => {
    selectProject(projectId);
  }, [projectId, selectProject]);

  const detail = useHydration<Record<string, unknown>>(solspireProject(projectId), (p) =>
    readRecord(p, (q) => apiRequest<unknown>(q)),
  );
  const tasks = useHydration<unknown>(solspireProjectTasks(projectId), (p) => apiRequest<unknown>(p));
  const files = useHydration<unknown>(solspireProjectFiles(projectId), (p) => apiRequest<unknown>(p));
  const events = useHydration<unknown>(solspireProjectEvents(projectId), (p) => apiRequest<unknown>(p));

  return (
    <div className="flex flex-col gap-4">
      <Panel>
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <p className="font-display text-lg text-white/90">{projectId}</p>
          <button
            type="button"
            onClick={() => onNavigate("projects")}
            data-testid="projects-back"
            className="rounded border border-line px-3 py-1 font-mono text-[11px] uppercase tracking-widest text-white/60 transition hover:border-gold/40 hover:text-white"
          >
            All projects
          </button>
        </div>
        <div className="mt-3">
          {detail.state === "ready" && detail.data ? (
            scalarRows(detail.data).length > 0 ? (
              <Facts rows={scalarRows(detail.data)} />
            ) : (
              <p className="text-sm text-white/50">This project record carries no scalar fields.</p>
            )
          ) : (
            <ContractState state={detail.state} error={detail.error?.message} onRetry={detail.reload} />
          )}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onNavigate("arkana")}
            data-testid="projects-open-arkana"
            className="rounded border border-emerald/40 bg-emerald/10 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-emerald"
          >
            Discuss in Arkana
          </button>
          <button
            type="button"
            onClick={() => onNavigate("engineering-lab")}
            data-testid="projects-open-lab"
            className="rounded border border-azure/40 bg-azure/10 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-azure"
          >
            Open Engineering Lab
          </button>
        </div>
      </Panel>

      <ProjectRuntimeCanvas projectId={projectId} />
      <RecordList title="Tasks" read={tasks} testid="projects-tasks" />
      <RecordList title="Files" read={files} testid="projects-files" />
      <RecordList title="Activity" read={events} testid="projects-events" />
    </div>
  );
}

export function ProjectsPage({
  section,
  onNavigate,
}: {
  section?: string;
  onNavigate: (id: SurfaceId, section?: string) => void;
}) {
  // The list is the shared context's read, not a second one: the console makes
  // one request for projects and every surface reads the same answer.
  const { projects, projectRows, projectCount } = useProjectContext();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return projectRows;
    return projectRows.filter((p) =>
      `${p.name} ${p.status} ${p.description ?? ""}`.toLowerCase().includes(q),
    );
  }, [projectRows, query]);

  if (section) {
    return (
      <Page title="Projects" subtitle="Project detail — files, tasks, activity, and shared context.">
        <ProjectDetail projectId={section} onNavigate={onNavigate} />
      </Page>
    );
  }

  return (
    <Page title="Projects" subtitle="Discovery and navigation across the workspace's projects.">
      <Panel className="mb-4">
        <label
          className="mb-2 block font-mono text-[11px] uppercase tracking-widest text-white/40"
          htmlFor="projects-filter"
        >
          Filter
        </label>
        <input
          id="projects-filter"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          data-testid="projects-filter"
          placeholder="Search projects…"
          className="w-full rounded border border-line bg-ink/60 px-3 py-2 text-sm text-white/85 outline-none focus:border-emerald/50"
        />
      </Panel>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          {projects.state === "ready" ? `${filtered.length} of ${projectCount} projects` : "Projects"}
        </p>
        {projects.state === "ready" ? (
          projectCount === 0 ? (
            <p className="text-sm text-white/50" data-testid="projects-empty">
              No projects yet in this workspace.
            </p>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-white/50" data-testid="projects-no-match">
              No project matches “{query}”.
            </p>
          ) : (
            <ul className="flex flex-col gap-2" data-testid="projects-list">
              {filtered.map((p) => (
                <li key={p.id} className="rounded border border-line bg-ink/40 p-3">
                  <button
                    type="button"
                    onClick={() => onNavigate("projects", p.id)}
                    data-testid={`project-open-${p.id}`}
                    className="text-left"
                  >
                    <span className="text-sm text-white/85">{p.name}</span>
                  </button>
                  {p.description && <p className="mt-1 text-xs text-white/50">{p.description}</p>}
                  <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-white/35">
                    {p.status}
                  </p>
                </li>
              ))}
            </ul>
          )
        ) : (
          <ContractState state={projects.state} error={projects.error?.message} onRetry={projects.reload} />
        )}
      </Panel>
    </Page>
  );
}
