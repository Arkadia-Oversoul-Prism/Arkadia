/**
 * Engineering Lab — deployed-agent registry read surface (Workstream 4).
 *
 * `GET /api/lab/engineering/agents` lists the owner-scoped bounded agents this
 * identity has deployed. Each record carries a `role`, its declared
 * `capabilities`, and the `tool_access` envelope a run would be granted.
 *
 * The backend contract is explicit that these are *discovery metadata, not
 * authorization* and that a deployed agent "never receives implicit authority".
 * The surface must not imply otherwise: a `capabilities` list is a declared
 * ceiling, and `tool_access.write_allowed` is the envelope the substrate would
 * enforce — neither is a grant the UI can confer. No control here mutates Lab
 * state; deploying an agent (`POST /engineering/agents`) is a mutating act and
 * stays unwired.
 *
 * Read-only by construction: GET only.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";

export interface LabAgentToolAccess {
  tools: string[];
  write_allowed: boolean;
  network_allowed: boolean;
  allowed_paths: string[];
  forbidden_paths: string[];
}

export interface LabAgent {
  agent_id: string;
  role: string;
  display_name: string;
  capabilities: string[];
  tool_access: LabAgentToolAccess;
  model_ref?: string | null;
  policy_ref?: string | null;
  created_at?: string;
}

export function LabAgentRegistry() {
  const agents = useHydration<{ agents: LabAgent[] }>(
    endpoints.labAgents,
    (p) => apiRequest<{ agents: LabAgent[] }>(p),
  );
  const rows = agents.data?.agents ?? [];

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Deployed agents
      </p>
      <p className="mb-4 text-xs text-white/40">
        Deploying an agent is a declaration of bounded capability, not authority. A capability is a
        declared ceiling for a role; a tool envelope is what the substrate would enforce. Neither
        grants this surface any power to act.
      </p>

      {agents.state === "ready" ? (
        rows.length === 0 ? (
          <p className="text-sm text-white/50" data-testid="lab-agents-empty">
            No agents deployed for this identity.
          </p>
        ) : (
          <ul className="flex flex-col gap-2" data-testid="lab-agents">
            {rows.map((agent) => (
              <li
                key={agent.agent_id}
                className="rounded border border-line bg-ink/40 p-3"
                data-testid={`lab-agent-${agent.agent_id}`}
              >
                <p className="mb-2 font-mono text-xs text-white/80">
                  <span className="text-azure/80">{agent.role}</span> ·{" "}
                  {agent.display_name || "unnamed"}
                </p>
                <Facts
                  rows={[
                    { label: "model", value: agent.model_ref ?? "—" },
                    { label: "write allowed", value: agent.tool_access?.write_allowed ? "yes" : "no" },
                    { label: "network", value: agent.tool_access?.network_allowed ? "yes" : "no" },
                    { label: "tools", value: (agent.tool_access?.tools ?? []).join(" · ") || "—" },
                  ]}
                />
                <p className="mt-2 text-[11px] text-white/45">
                  declared capabilities (ceiling, not a grant):{" "}
                  {(agent.capabilities ?? []).join(" · ") || "none"}
                </p>
              </li>
            ))}
          </ul>
        )
      ) : (
        <ContractState state={agents.state} error={agents.error?.message} onRetry={agents.reload} />
      )}
    </Panel>
  );
}
