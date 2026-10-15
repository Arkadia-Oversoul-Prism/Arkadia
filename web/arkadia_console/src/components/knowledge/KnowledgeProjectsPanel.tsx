/**
 * Knowledge OS — readable project corpus.
 *
 * Backed by the *verified* handler contract `GET /api/knowledge/projects`
 * (`api/knowledge_routes.py::list_projects` -> `knowledge.vault.list_projects`).
 *
 * Ownership on this reader differs from the timeline's: the predicate is
 * `(user_id = ? OR user_id IS NULL)` authenticated and `user_id IS NULL`
 * anonymous, so there *is* a public corpus and an anonymous caller legitimately
 * reads projects. A `[]` here is therefore always a genuine empty read, while a
 * public-only answer to a signed-in viewer means their private projects are
 * absent — the boundary working, not a partial result. The panel reports which
 * of the two scopes it received and never substitutes mock data.
 */
import { useState } from "react";
import { Panel, Facts, ContractState } from "../../components/ui";
import { useAuth } from "../../contexts/AuthContext";
import { useHydration } from "../../lib/useHydration";
import { apiRequest, ApiError } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import { KnowledgeProjectDetail } from "./KnowledgeProjectDetail";
import {
  classifyProjectScope,
  isKnowledgeProjects,
  projectNotice,
  projectTags,
  type KnowledgeProject,
  type ViewerKind,
} from "../../pages/knowledge/knowledgeContracts";

async function readProjects(path: string): Promise<KnowledgeProject[]> {
  const payload = await apiRequest<unknown>(path);
  if (!isKnowledgeProjects(payload)) {
    throw new ApiError("The knowledge projects contract returned an unrecognised shape.", {
      kind: "UNKNOWN",
      path,
    });
  }
  return payload;
}

export function KnowledgeProjectsPanel() {
  const { isAuthenticated } = useAuth();
  const viewer: ViewerKind = isAuthenticated ? "authenticated" : "anonymous";

  const projects = useHydration<KnowledgeProject[]>(endpoints.knowledgeProjects, readProjects, [isAuthenticated]);

  return (
    <Panel data-testid="knowledge-projects-panel">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Projects</p>
      {projects.state === "ready" && projects.data ? (
        <ProjectsReading projects={projects.data} viewer={viewer} />
      ) : (
        <ContractState state={projects.state} error={projects.error?.message} onRetry={projects.reload} />
      )}
    </Panel>
  );
}

function ProjectsReading({ projects, viewer }: { projects: KnowledgeProject[]; viewer: ViewerKind }) {
  const scope = classifyProjectScope(projects);
  const notice = projectNotice(scope, viewer);
  const [selected, setSelected] = useState<string | null>(null);

  if (projects.length === 0) {
    return (
      <p data-testid="knowledge-projects-empty" className="text-sm text-white/50">
        No projects are readable in this scope. The public corpus is visible to every reader, so
        this is an empty read, not a filtered one.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4" data-testid="knowledge-projects-list">
      <Facts
        rows={[
          { label: "projects", value: String(projects.length) },
          { label: "scope", value: scope },
          { label: "viewer", value: viewer },
        ]}
      />

      {notice && (
        <p data-testid="knowledge-projects-scope" className="text-sm text-white/50">
          {notice}
        </p>
      )}

      <ul className="flex flex-col gap-2">
        {projects.map((project) => {
          const tags = projectTags(project);
          const isOpen = selected === project.name;
          return (
            <li key={project.uuid} className="border-l border-line pl-3" data-testid={`knowledge-project-${project.uuid}`}>
              <button
                type="button"
                aria-expanded={isOpen}
                onClick={() => setSelected(isOpen ? null : project.name)}
                className="text-left"
              >
                <span className="text-sm text-white/85">{project.name}</span>
              </button>
              {project.description && <p className="mt-1 text-xs text-white/50">{project.description}</p>}
              <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-white/35">
                {project.status} · {project.user_id ? "private" : "public"} · {project.updated_at}
              </p>
              {tags.length > 0 && (
                <ul className="mt-1 flex flex-wrap gap-1">
                  {tags.map((tag) => (
                    <li key={tag} className="rounded border border-line px-2 py-0.5 font-mono text-[10px] text-white/50">
                      {tag}
                    </li>
                  ))}
                </ul>
              )}
              {isOpen && (
                <div className="mt-3">
                  <KnowledgeProjectDetail identifier={project.name} />
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
