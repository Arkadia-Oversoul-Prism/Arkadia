import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { useAuth } from "../contexts/AuthContext";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { NodeProfile, ProjectList } from "../lib/types";

const LENSES = [
  { id: "projects", label: "Projects" },
  { id: "knowledge", label: "Knowledge" },
  { id: "memory", label: "Memory" },
  { id: "weaver", label: "Weaver" },
];

export function SolariunPage({ section = "projects" }: { section?: string }) {
  const { profile, isAuthenticated, identityState } = useAuth();
  const projects = useHydration<ProjectList>(
    endpoints.solspireProjects,
    (p) => apiRequest<ProjectList>(p),
    [isAuthenticated],
  );

  return (
    <Page title="Solariun" subtitle="Your personal workspace and cognitive canvas — projects, knowledge, and continuity.">
      <div className="mb-4 flex gap-1">
        {LENSES.map((l) => (
          <span
            key={l.id}
            className={`rounded px-3 py-1 font-mono text-[11px] uppercase tracking-widest ${
              section === l.id ? "bg-white/5 text-violet" : "text-white/40"
            }`}
          >
            {l.label}
          </span>
        ))}
      </div>

      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Identity</p>
        {identityState === "ready" && profile ? (
          <Facts
            rows={[
              { label: "name", value: (profile as NodeProfile).display_name },
              { label: "role", value: `${profile.role_sigil} ${profile.role}` },
              { label: "node", value: profile.node_key ?? "—" },
              { label: "access", value: String(profile.access_level) },
            ]}
          />
        ) : (
          <div>
            <ContractState
              state={identityState === "ready" ? "error" : identityState === "loading" ? "loading" : "auth-required"}
              error={identityState === "auth-error" ? "Identity was rejected." : null}
            />
          </div>
        )}
      </Panel>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Projects</p>
        {projects.state === "ready" && projects.data ? (
          projects.data.count === 0 ? (
            <p className="text-sm text-white/50">No projects yet in this workspace.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {projects.data.projects.map((p) => (
                <li key={p.id} className="rounded border border-line bg-ink/40 p-3">
                  <p className="text-sm text-white/85">{p.name}</p>
                  <p className="font-mono text-[11px] text-white/40">{p.status ?? "active"}</p>
                </li>
              ))}
            </ul>
          )
        ) : (
          <ContractState state={projects.state} error={projects.error?.message} onRetry={projects.reload} />
        )}
      </Panel>

      <div className="mt-4">
        <NotYetWired
          contract="/api/solspire/projects/{id}/runtime-context"
          note="The cognitive canvas and continuity views are scaffolded as lenses of this workspace."
        />
      </div>
    </Page>
  );
}
