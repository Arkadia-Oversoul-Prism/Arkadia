/**
 * The shared project-scoped context object.
 *
 * One object answers "which project am I in" for the whole console. Before this
 * module each surface held its own copy: `WorkspacePage` kept a local
 * `projectId` state, `ProjectsPage` derived a selection from its route section,
 * and the Engineering Lab had no project binding at all. Three copies of one
 * fact is how a conversation ends up scoped to a different project than the
 * session it produced.
 *
 * This is a *context*, not a store. It owns no persistence and no authority:
 *
 *  * the project list is a real read of `GET /solspire/projects` (the same
 *    contract `ProjectsPage` and the Solariun `projects` lens already read);
 *  * the canonical workspace is a real read of `GET /solspire/workspace`, which
 *    the Lab requires as `workspace_ref` whenever a `project_ref` is present
 *    (`api/lab_routes.py` refuses a mismatch with 409);
 *  * the active project is a *selection*, and selecting a project grants
 *    nothing. Authorization remains a separate human act recorded against a
 *    session, exactly as before.
 *
 * The object carries only what the real contracts publish. `Project.to_dict()`
 * (`solspire/project_manager.py`) yields id / name / status / created_at /
 * updated_at / metadata / conversations / owner_uid — there is no branch or
 * revision field on a project, so none is invented here. The repository
 * revision the Lab observes is a *session* fact (`repository_ref`) and stays
 * where the server reports it.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { apiRequest } from "./apiClient";
import { endpoints } from "./endpoints";
import { useAuth } from "../contexts/AuthContext";
import { useHydration, type Hydration } from "./useHydration";

/** One project, as the canonical contract publishes it. */
export interface ProjectRef {
  id: string;
  name: string;
  status: string;
  description?: string;
}

/** The canonical workspace bound to the authenticated subject. */
export interface WorkspaceRef {
  id: string;
  displayName: string;
  workspaceType: string;
}

export interface ProjectContextValue {
  /** The project list read, with its own hydration state. */
  projects: Hydration<unknown>;
  /** The projects this identity can see, normalised. */
  projectRows: ProjectRef[];
  /** The count the contract reports, or the row count when it reports none. */
  projectCount: number;
  /** The canonical workspace read, with its own hydration state. */
  workspace: Hydration<unknown>;
  /** The canonical workspace, or null when it could not be read. */
  workspaceRef: WorkspaceRef | null;
  /** The active project id, or null when the console is unscoped. */
  activeProjectId: string | null;
  /** The active project record, or null. */
  activeProject: ProjectRef | null;
  /** Select a project, or clear the selection with null. */
  selectProject: (projectId: string | null) => void;
  /** True when a project is selected and the canonical workspace is known. */
  canBindProject: boolean;
}

const ProjectContext = createContext<ProjectContextValue | null>(null);

/**
 * Session key for the remembered project selection.
 *
 * Session-scoped on purpose: a project selection is a working context, not a
 * preference. A new browser session starts unscoped, and the value is always
 * re-validated against the live project list before it is trusted.
 */
const ACTIVE_PROJECT_KEY = "arkadia.activeProjectId";

/** Persist the selection, tolerating storage being unavailable. */
function rememberProject(projectId: string | null): void {
  try {
    if (projectId) window.sessionStorage.setItem(ACTIVE_PROJECT_KEY, projectId);
    else window.sessionStorage.removeItem(ACTIVE_PROJECT_KEY);
  } catch {
    // Storage unavailable (private mode, disabled cookies): the selection still
    // works for this page's lifetime, it just does not survive a reload.
  }
}

function readProjectRows(data: unknown): ProjectRef[] {
  const payload = data as { projects?: unknown[] } | unknown[] | null;
  if (!payload) return [];
  const list = Array.isArray(payload)
    ? payload
    : Array.isArray((payload as { projects?: unknown[] }).projects)
      ? ((payload as { projects?: unknown[] }).projects as unknown[])
      : [];
  return list
    .filter((row): row is Record<string, unknown> => typeof row === "object" && row !== null)
    .map((row) => ({
      id: String(row.project_id ?? row.id ?? ""),
      name: String(row.name ?? row.title ?? "Untitled project"),
      status: String(row.status ?? "unknown"),
      description: typeof row.description === "string" ? row.description : undefined,
    }))
    .filter((row) => row.id);
}

function readProjectCount(data: unknown, fallback: number): number {
  if (typeof data !== "object" || data === null) return fallback;
  const count = (data as { count?: unknown }).count;
  return typeof count === "number" ? count : fallback;
}

function readWorkspaceRef(data: unknown): WorkspaceRef | null {
  if (typeof data !== "object" || data === null) return null;
  const workspace = (data as { workspace?: unknown }).workspace;
  if (typeof workspace !== "object" || workspace === null) return null;
  const record = workspace as Record<string, unknown>;
  const id = record.id;
  if (typeof id !== "string" || !id) return null;
  return {
    id,
    displayName: typeof record.display_name === "string" ? record.display_name : "Workspace",
    workspaceType: typeof record.workspace_type === "string" ? record.workspace_type : "canonical",
  };
}

export function ProjectProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  // The active project is a *selection*, not a server fact — so remembering it
  // across a reload is not inventing state, it is remembering a choice the user
  // made. Without this, a refresh silently dropped the project and the next
  // conversation was scoped to nothing while the previous one was scoped to a
  // project: the exact "navigation silently discards active work" failure.
  //
  // It is session-scoped, not durable: a new browser session starts unscoped,
  // and the selection is re-validated against the live project list below, so a
  // remembered id that no longer exists (archived, or another identity's) is
  // dropped rather than trusted.
  const [activeProjectId, setActiveProjectId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      return window.sessionStorage.getItem(ACTIVE_PROJECT_KEY);
    } catch {
      return null;
    }
  });

  // Both reads are the canonical contracts, re-run when identity settles so a
  // sign-in does not leave the console holding an unauthenticated empty list.
  const projects = useHydration<unknown>(endpoints.solspireProjects, (p) => apiRequest<unknown>(p), [
    isAuthenticated,
  ]);
  const workspace = useHydration<unknown>(endpoints.solspireWorkspace, (p) => apiRequest<unknown>(p), [
    isAuthenticated,
  ]);

  const projectRows = useMemo(() => readProjectRows(projects.data), [projects.data]);
  const projectCount = useMemo(
    () => readProjectCount(projects.data, projectRows.length),
    [projects.data, projectRows.length],
  );
  const workspaceRef = useMemo(() => readWorkspaceRef(workspace.data), [workspace.data]);

  // A selection that is no longer in the list (archived, or belonging to a
  // previous identity) must not stay active: the console would otherwise scope
  // a conversation to a project the backend will refuse.
  useEffect(() => {
    if (projects.state !== "ready") return;
    if (activeProjectId && !projectRows.some((row) => row.id === activeProjectId)) {
      setActiveProjectId(null);
      // The remembered selection is stale too — clearing only the state would
      // resurrect it on the next reload.
      rememberProject(null);
    }
  }, [projects.state, projectRows, activeProjectId]);

  const selectProject = useCallback((projectId: string | null) => {
    setActiveProjectId(projectId);
    rememberProject(projectId);
  }, []);

  const activeProject = useMemo(
    () => projectRows.find((row) => row.id === activeProjectId) ?? null,
    [projectRows, activeProjectId],
  );

  const value = useMemo<ProjectContextValue>(
    () => ({
      projects,
      projectRows,
      projectCount,
      workspace,
      workspaceRef,
      activeProjectId,
      activeProject,
      selectProject,
      canBindProject: Boolean(activeProjectId) && workspaceRef !== null,
    }),
    [
      projects,
      projectRows,
      projectCount,
      workspace,
      workspaceRef,
      activeProjectId,
      activeProject,
      selectProject,
    ],
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProjectContext(): ProjectContextValue {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProjectContext must be used within ProjectProvider");
  return ctx;
}
