/**
 * Personal Echofeild read model — the Solariun `memory` lens.
 *
 * One read of `GET /api/me/field` (handler `api/echofeild.py::get_my_field`,
 * `require_auth`): the authenticated user's personal read model — notes,
 * knowledge graph, timeline, knowledge projects, SolSpire projects,
 * conversations, messages, executions — composed with **per-source
 * provenance**: `meta.sources` states, for every source, whether it was
 * actually included or came back unavailable. This panel renders that
 * provenance verbatim: when a source is unavailable the counts that depend on
 * it are shown as degraded, never as a confident zero.
 *
 * Recovery relationship: the archived Prism's Personal Echofeild / observatory
 * lens (`/personal-echofeild` → solariun observatory in the archived route
 * table) surfaces this same capability; the console reads the canonical
 * contract under the `memory` lens. Read-only: no control here writes
 * anything, and no record content is fetched or invented — counts only.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";

export interface FieldSource {
  source: string;
  primitive: string;
  included: boolean;
  detail?: string;
}

export interface PersonalField {
  notes: unknown[];
  graph: { nodes?: unknown[]; edges?: unknown[] };
  timeline: unknown[];
  projects: unknown[];
  solspire_projects: unknown[];
  conversations: unknown[];
  messages: unknown[];
  executions: unknown[];
  meta: {
    owner_uid: string;
    generated_at: string;
    sources: FieldSource[];
  };
}

const COUNTS: Array<{ key: keyof PersonalField; label: string; source?: string }> = [
  { key: "notes", label: "notes", source: "notes" },
  { key: "timeline", label: "timeline events", source: "timeline" },
  { key: "projects", label: "knowledge projects", source: "projects" },
  { key: "solspire_projects", label: "SolSpire projects", source: "solspire_projects" },
  { key: "conversations", label: "conversations", source: "conversations" },
  { key: "messages", label: "messages", source: "conversations" },
  { key: "executions", label: "executions", source: "executions" },
];

function count(value: unknown): string {
  return Array.isArray(value) ? String(value.length) : "—";
}

export function PersonalFieldPanel() {
  const field = useHydration<PersonalField>(endpoints.field, (p) => apiRequest<PersonalField>(p));

  if (field.state !== "ready" || !field.data) {
    return <ContractState state={field.state} error={field.error?.message} onRetry={field.reload} />;
  }

  const data = field.data;
  const sources = data.meta?.sources ?? [];
  const available = new Set(sources.filter((s) => s.included).map((s) => s.source));

  return (
    <div data-testid="personal-field-panel" className="flex flex-col gap-3">
      <Panel>
        <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Personal field · read model
        </p>
        <p className="mb-3 font-mono text-[10px] text-white/30">
          generated {data.meta?.generated_at ?? "—"}
        </p>
        <Facts
          rows={COUNTS.map(({ key, label, source }) => {
            const degraded = source !== undefined && !available.has(source);
            return {
              label,
              value: degraded ? (
                <span className="text-white/40">unavailable · not counted</span>
              ) : (
                count(data[key])
              ),
            };
          })}
        />
        <p className="mt-3 text-xs text-white/40">
          Counts only — no record content is read onto this surface.
        </p>
      </Panel>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Sources · reported by the contract, not inferred here
        </p>
        <ul className="flex flex-wrap gap-2">
          {sources.map((s) => (
            <li
              key={s.source}
              className={`rounded px-2 py-1 font-mono text-[10px] uppercase tracking-widest ${
                s.included
                  ? "border border-emerald/30 text-emerald/80"
                  : "border border-dashed border-white/20 text-white/40"
              }`}
              data-testid={`field-source-${s.source}`}
            >
              {s.source}
              {s.included ? "" : ` · ${s.detail || "unavailable"}`}
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
