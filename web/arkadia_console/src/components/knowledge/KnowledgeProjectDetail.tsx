/**
 * Knowledge OS — single-project reader.
 *
 * Backed by the *verified* handler contract
 * `GET /api/knowledge/projects/{name_or_uuid}` (`api/knowledge_routes.py::get_project`
 * -> `knowledge.vault.get_project`). The path is composed from the collection
 * entry in the canonical registry (`endpoints.knowledgeProjects`) so the base
 * cannot drift; the identifier is percent-encoded so an id containing `/`, `?`
 * or `#` cannot address a different route. No page-local registry entry, no
 * second API base.
 *
 * The read is fail-closed: the handler answers `404` both when a project does
 * not exist *and* when it is not readable by the caller, and it does not
 * distinguish the two. This reader reports that boundary as a boundary — never
 * as an ordinary transport fault, and never by guessing which case it was.
 */
import { ContractState, Facts, Panel } from "../../components/ui";
import { apiRequest, ApiError } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import { useHydration } from "../../lib/useHydration";
import {
  isKnowledgeProject,
  projectRefusalNotice,
  projectTags,
  type KnowledgeProject,
} from "../../pages/knowledge/knowledgeContracts";

async function readProject(path: string): Promise<KnowledgeProject> {
  const payload = await apiRequest<unknown>(path);
  if (!isKnowledgeProject(payload)) {
    throw new ApiError("The knowledge project contract returned an unrecognised shape.", {
      kind: "UNKNOWN",
      path,
    });
  }
  return payload;
}

export function projectDetailPath(identifier: string): string {
  return `${endpoints.knowledgeProjects}/${encodeURIComponent(identifier)}`;
}

export function KnowledgeProjectDetail({ identifier }: { identifier: string }) {
  const path = projectDetailPath(identifier);
  const project = useHydration<KnowledgeProject>(path, readProject, [identifier]);

  return (
    <Panel data-testid="knowledge-project-detail">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Project detail · {identifier}
      </p>
      {project.state === "ready" && project.data ? (
        <ProjectReading project={project.data} />
      ) : project.state === "error" && project.error?.kind === "NOT_FOUND" ? (
        <p data-testid="knowledge-project-refused" className="text-sm text-white/50">
          {projectRefusalNotice()}
        </p>
      ) : (
        <ContractState state={project.state} error={project.error?.message} onRetry={project.reload} />
      )}
    </Panel>
  );
}

function ProjectReading({ project }: { project: KnowledgeProject }) {
  const tags = projectTags(project);
  return (
    <div className="flex flex-col gap-4">
      <Facts
        rows={[
          { label: "name", value: project.name },
          { label: "description", value: project.description || "—" },
          { label: "uuid", value: project.uuid },
          { label: "owner", value: project.user_id ? "private" : "public" },
          { label: "status", value: project.status },
          { label: "updated", value: project.updated_at },
        ]}
      />
      {tags.length > 0 && (
        <ul className="flex flex-wrap gap-1">
          {tags.map((tag) => (
            <li key={tag} className="rounded border border-line px-2 py-0.5 font-mono text-[10px] text-white/50">
              {tag}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
