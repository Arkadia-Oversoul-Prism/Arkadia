/**
 * Solariun `overview` lens — the archived Home cockpit ("What matters now?").
 *
 * The archived Prism's primary navigation opened on `overview` (label "Home",
 * question "What matters now?"), and the legacy `/dashboard` path addressed it.
 * The console reconciled the Solariun vocabulary to four lenses and dropped the
 * cockpit, so `/solariun` had no "what matters now" reading at all. This lens
 * restores that capability **without** a new store, a new read model, or a
 * second project/field system.
 *
 * It composes only contracts the console already reads elsewhere:
 *
 *   projects   the page's own `GET /solspire/projects` hydration (passed in, so
 *              the overview does not issue a second read of the same contract)
 *   field      `GET /api/me/field` — the personal Echofeild read model, with the
 *              contract's own per-source provenance (a degraded source is shown
 *              as degraded, never as a confident zero)
 *
 * and it points at the two governed capabilities whose authority lives on their
 * own canonical surfaces (Engineering Lab, Weaver) rather than re-reading them.
 *
 * Read-only: nothing here mutates project, field, lab or weaver state.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import type { HydrationState } from "../../lib/useHydration";
import type { ProjectList } from "../../lib/types";
import type { SurfaceId } from "../../lib/surfaces";
import type { PersonalField } from "./PersonalFieldPanel";

/** The counts the cockpit shows from the personal field, with their source key. */
const FIELD_COUNTS: Array<{ key: keyof PersonalField; label: string; source: string }> = [
  { key: "notes", label: "notes", source: "notes" },
  { key: "timeline", label: "timeline events", source: "timeline" },
  { key: "conversations", label: "conversations", source: "conversations" },
  { key: "executions", label: "executions", source: "executions" },
];

function count(value: unknown): string {
  return Array.isArray(value) ? String(value.length) : "—";
}

export function SolariunOverview({
  projects,
  activeProjectName,
  onNavigate,
}: {
  /** The page's existing project-list hydration — reused, not re-read. */
  projects: { state: HydrationState; data: ProjectList | null; error: { message?: string } | null; reload: () => void };
  activeProjectName: string | null;
  onNavigate: (id: SurfaceId, section?: string) => void;
}) {
  const field = useHydration<PersonalField>(endpoints.field, (p) => apiRequest<PersonalField>(p));

  const sources = field.state === "ready" && field.data ? (field.data.meta?.sources ?? []) : [];
  const available = new Set(sources.filter((s) => s.included).map((s) => s.source));

  return (
    <div data-testid="solariun-overview" className="flex flex-col gap-3">
      <Panel>
        <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
          What matters now
        </p>
        <p className="mb-4 text-xs text-white/40">
          A cockpit over the same canonical reads the rest of the console uses — no second store.
        </p>
        <Facts
          rows={[
            {
              label: "active project",
              value: activeProjectName ?? "none selected",
            },
            {
              label: "projects",
              value:
                projects.state === "ready" && projects.data
                  ? String(projects.data.count)
                  : projects.state === "loading"
                    ? "reading…"
                    : "unavailable",
            },
          ]}
        />
      </Panel>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Personal field · counts only
        </p>
        {field.state === "ready" && field.data ? (
          <Facts
            rows={FIELD_COUNTS.map(({ key, label, source }) => {
              const degraded = !available.has(source);
              return {
                label,
                value: degraded ? (
                  <span className="text-white/40">unavailable · not counted</span>
                ) : (
                  count(field.data![key])
                ),
              };
            })}
          />
        ) : (
          <ContractState state={field.state} error={field.error?.message} onRetry={field.reload} />
        )}
      </Panel>

      <div className="grid gap-3 md:grid-cols-2">
        <Panel>
          <p className="font-display text-[15px] text-white/85">Engineering Lab</p>
          <p className="mt-1 text-xs leading-relaxed text-white/50">
            How Arkadia is doing — task state, provider status, and evidence. The authority lives on
            the canonical Engineering Lab surface; this cockpit points there rather than re-reading it.
          </p>
          <button
            type="button"
            onClick={() => onNavigate("engineering-lab")}
            data-testid="solariun-overview-open-engineering-lab"
            className="mt-3 rounded border border-white/15 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-white/60 hover:text-white/85"
          >
            Open Engineering Lab
          </button>
        </Panel>
        <Panel>
          <p className="font-display text-[15px] text-white/85">Weaver</p>
          <p className="mt-1 text-xs leading-relaxed text-white/50">
            What is being reasoned, proposed and worked on. Proposal, approval, execution and
            verification are read from the canonical Weaver surface; this cockpit does not fork it.
          </p>
          <button
            type="button"
            onClick={() => onNavigate("weaver")}
            data-testid="solariun-overview-open-weaver"
            className="mt-3 rounded border border-white/15 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-white/60 hover:text-white/85"
          >
            Open Weaver
          </button>
        </Panel>
      </div>
    </div>
  );
}
