/**
 * Settings — identity, preferences, integrations, security, and workspace
 * configuration.
 *
 * Every panel reads a contract the backend actually serves, and each is honest
 * about what it can and cannot do:
 *
 *  - Identity      — `GET /api/me` (the same read the auth context hydrates).
 *  - Preferences   — `GET /api/me/ais-profile`, a read-only projection here.
 *  - Integrations  — `GET /api/sources` (configured/authenticated/live) and
 *                    `GET /api/knowledge/providers` (model providers).
 *  - Security      — the identity's own role/access readings from `/api/me`.
 *  - Workspace     — `GET /solspire/workspace`, the canonical workspace binding.
 *
 * There are deliberately **no** admin controls here. The console has no verified
 * contract for changing another identity's role, mutating workspace membership,
 * or rotating credentials, and inventing one would be an unsupported control.
 * Where a write contract does exist (`PATCH /api/me`, `PATCH /api/me/ais-profile`)
 * the surface states that the edit path is not wired rather than offering a
 * button that cannot succeed.
 */
import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { useAuth } from "../contexts/AuthContext";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import { readRecord, scalarRows } from "../lib/records";

const UNKNOWN_CONTRACT = "UNKNOWN";

interface SourceEntry {
  name: string;
  configured?: boolean;
  authenticated?: boolean;
  live?: boolean;
  repo?: string;
  branch?: string;
}

interface SourcesRead {
  sources: SourceEntry[];
}

interface ProviderEntry {
  name: string;
  display_name: string;
  capabilities: string[];
  authenticated: boolean;
}

function IdentityPanel() {
  const { profile, identityState, identityError, isAuthenticated } = useAuth();
  return (
    <Panel data-testid="settings-identity">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Identity</p>
      {identityState === "ready" && profile ? (
        <Facts
          rows={[
            { label: "name", value: profile.display_name },
            { label: "email", value: profile.email },
            { label: "node", value: profile.node_key ?? "—" },
            { label: "role", value: `${profile.role_sigil} ${profile.role}` },
            { label: "status", value: profile.status },
            { label: "access level", value: String(profile.access_level) },
          ]}
        />
      ) : (
        <ContractState
          state={identityState === "ready" ? "error" : identityState === "loading" ? "loading" : "auth-required"}
          error={identityError}
        />
      )}
      {isAuthenticated && (
        <p className="mt-4 text-xs text-white/35">
          Profile edits are served by <span className="font-mono">PATCH /api/me</span>, but the console
          does not yet wire an edit form — no control is offered that cannot complete.
        </p>
      )}
    </Panel>
  );
}

function PreferencesPanel() {
  const profile = useHydration<Record<string, unknown>>(endpoints.aisProfile, (p) =>
    readRecord(p, (q) => apiRequest<unknown>(q)),
  );
  return (
    <Panel data-testid="settings-preferences">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Preferences</p>
      {profile.state === "ready" && profile.data ? (
        scalarRows(profile.data).length > 0 ? (
          <Facts rows={scalarRows(profile.data)} />
        ) : (
          <p className="text-sm text-white/50">The AIS profile carries no scalar fields yet.</p>
        )
      ) : (
        <ContractState state={profile.state} error={profile.error?.message} onRetry={profile.reload} />
      )}
    </Panel>
  );
}

function IntegrationsPanel() {
  const sources = useHydration<SourcesRead>(endpoints.sources, (p) => apiRequest<SourcesRead>(p));
  const providers = useHydration<ProviderEntry[]>(endpoints.knowledgeProviders, (p) =>
    apiRequest<ProviderEntry[]>(p),
  );
  return (
    <Panel data-testid="settings-integrations">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Integrations</p>

      <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/30">Sources</p>
      {sources.state === "ready" && sources.data ? (
        <ul className="mb-4 flex flex-col gap-2" data-testid="settings-sources">
          {sources.data.sources.map((s) => (
            <li key={s.name} className="rounded border border-line bg-ink/40 p-3">
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-sm text-white/85">{s.name}</p>
                <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
                  {s.configured ? (s.authenticated ? "authenticated" : "configured") : "not configured"}
                </p>
              </div>
              {s.repo && (
                <p className="mt-1 font-mono text-[10px] text-white/35">
                  {s.repo} · {s.branch}
                </p>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <div className="mb-4">
          <ContractState state={sources.state} error={sources.error?.message} onRetry={sources.reload} />
        </div>
      )}

      <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/30">Model providers</p>
      {providers.state === "ready" && providers.data ? (
        <ul className="flex flex-wrap gap-2" data-testid="settings-providers">
          {providers.data.map((p) => (
            <li key={p.name} className="rounded border border-line px-2 py-1 font-mono text-[11px] text-white/60">
              {p.display_name} · {p.authenticated ? "authenticated" : "no key"}
            </li>
          ))}
        </ul>
      ) : (
        <ContractState state={providers.state} error={providers.error?.message} onRetry={providers.reload} />
      )}
    </Panel>
  );
}

function SecurityPanel() {
  const { profile } = useAuth();
  return (
    <Panel data-testid="settings-security">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Security &amp; permissions</p>
      {profile ? (
        <Facts
          rows={[
            { label: "role", value: `${profile.role_sigil} ${profile.role}` },
            { label: "access level", value: String(profile.access_level) },
            { label: "tools", value: profile.access_tools.length > 0 ? profile.access_tools.join(", ") : "—" },
            { label: "status", value: profile.status },
          ]}
        />
      ) : (
        <p className="text-sm text-white/50">Sign in to read this identity's authority.</p>
      )}
      <p className="mt-4 text-xs text-white/35">
        Human authority remains the decision boundary. Consequential operations are authorized at their
        dispatch point, not from this surface.
      </p>
    </Panel>
  );
}

function WorkspacePanel() {
  const workspace = useHydration<Record<string, unknown>>(endpoints.solspireWorkspace, (p) =>
    readRecord(p, (q) => apiRequest<unknown>(q)),
  );
  return (
    <Panel data-testid="settings-workspace">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Workspace</p>
      {workspace.state === "ready" && workspace.data ? (
        scalarRows(workspace.data).length > 0 ? (
          <Facts rows={scalarRows(workspace.data)} />
        ) : (
          <p className="text-sm text-white/50">The canonical workspace record carries no scalar fields.</p>
        )
      ) : (
        <ContractState state={workspace.state} error={workspace.error?.message} onRetry={workspace.reload} />
      )}
    </Panel>
  );
}

export function SettingsPage() {
  const { profile } = useAuth();
  return (
    <Page title="Settings" subtitle="Identity, preferences, integrations, security, and workspace configuration.">
      <div className="grid gap-4 lg:grid-cols-2">
        <IdentityPanel />
        <PreferencesPanel />
        <IntegrationsPanel />
        <SecurityPanel />
        <WorkspacePanel />
        <Panel data-testid="settings-admin">
          <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Administration</p>
          <NotYetWired
            contract={UNKNOWN_CONTRACT}
            note="No admin controls are offered. The console has no verified contract for changing another identity's role, mutating workspace membership, or rotating credentials, and an unsupported control would be a decorative one."
          />
        </Panel>
      </div>
      {profile && (
        <p className="mt-4 font-mono text-[10px] uppercase tracking-widest text-white/25">
          signed in as {profile.display_name}
        </p>
      )}
    </Page>
  );
}
