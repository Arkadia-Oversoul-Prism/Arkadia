/**
 * NovaNet — the public field and Nexus hub.
 *
 * Two halves over one backend: the public field (`/api/transmissions`, the
 * legacy `NovaNetPage` social feed) and the unified echoes stream
 * (`/api/echoes`, the public Crystal-Matrix aggregation). Both contracts are
 * public reads, so this surface is reachable without an identity — but it never
 * fabricates content: an unavailable read renders the honest contract state.
 *
 * The legacy hub carried sub-views (`/nexus/ims`, `/nexus/grove`,
 * `/nexus/larder`, `/nexus/distribution`). They are declared here as lenses and
 * render their own honest "not yet wired" state until their contracts are
 * reconciled — they are not routed as separate top-level surfaces (directive §5).
 */
import { Page, Panel, ContractState, NotYetWired } from "../components/ui";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { EchoesFeed, TransmissionList } from "../lib/types";

const LENSES = [
  { id: "field", label: "Field" },
  { id: "echoes", label: "Echoes" },
  { id: "ims", label: "IMS Archive" },
  { id: "grove", label: "Spiral Grove" },
  { id: "larder", label: "Larder" },
  { id: "distribution", label: "Distribute" },
];

const DEFERRED: Record<string, string> = {
  ims: "/api/ims/inquiries",
  grove: "UNKNOWN",
  larder: "UNKNOWN",
  distribution: "UNKNOWN",
};

function ago(ts: number): string {
  const delta = Date.now() - ts;
  if (delta < 60_000) return "now";
  if (delta < 3_600_000) return `${Math.floor(delta / 60_000)}m`;
  if (delta < 86_400_000) return `${Math.floor(delta / 3_600_000)}h`;
  return `${Math.floor(delta / 86_400_000)}d`;
}

export function NovaNetPage({ section = "field" }: { section?: string }) {
  const field = useHydration<TransmissionList>(endpoints.transmissions, (p) => apiRequest<TransmissionList>(p));
  const echoes = useHydration<EchoesFeed>(endpoints.echoes, (p) => apiRequest<EchoesFeed>(p), [section === "echoes"]);

  return (
    <Page title="NovaNet" subtitle="The public field — transmissions, echoes, and the shared Nexus hub over one canonical backend.">
      <div className="mb-4 flex flex-wrap gap-1" data-testid="novanet-lenses">
        {LENSES.map((l) => (
          <span
            key={l.id}
            data-testid={`novanet-lens-${l.id}`}
            className={`rounded px-3 py-1 font-mono text-[11px] uppercase tracking-widest ${
              section === l.id ? "bg-white/5 text-azure" : "text-white/40"
            }`}
          >
            {l.label}
          </span>
        ))}
      </div>

      {(section === "field" || section === "echoes") && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel>
            <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
              Public field · {field.data ? `${field.data.total} transmissions` : "—"}
            </p>
            {field.state === "ready" && field.data ? (
              field.data.transmissions.length === 0 ? (
                <p className="text-sm text-white/50">The field is quiet — no public transmissions yet.</p>
              ) : (
                <ul className="flex flex-col gap-2" data-testid="novanet-transmissions">
                  {field.data.transmissions.map((t) => (
                    <li key={t.id} className="rounded border border-line bg-ink/40 p-3">
                      <div className="flex items-baseline justify-between gap-3">
                        <p className="text-sm text-white/85">
                          <span className="text-azure">{t.author?.avatar ?? "◈"}</span>{" "}
                          {t.author?.name ?? "Node"}
                          {t.author?.role ? <span className="text-white/40"> · {t.author.role}</span> : null}
                        </p>
                        <p className="font-mono text-[10px] text-white/30">{ago(t.timestamp)}</p>
                      </div>
                      <p className="mt-2 whitespace-pre-wrap text-sm text-white/70">{t.content}</p>
                      {t.edited_at ? <p className="mt-1 font-mono text-[10px] text-white/25">edited</p> : null}
                    </li>
                  ))}
                </ul>
              )
            ) : (
              <ContractState state={field.state} error={field.error?.message} onRetry={field.reload} />
            )}
          </Panel>

          <Panel>
            <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Crystal Matrix · echoes</p>
            {echoes.state === "ready" && echoes.data ? (
              <div className="flex flex-col gap-3">
                <p className="font-mono text-[11px] text-white/40">
                  geometry {echoes.data.matrix.geometry} · aggregate {echoes.data.matrix.aggregate}
                </p>
                <ul className="flex flex-wrap gap-2">
                  {echoes.data.matrix.dimensions.map((d) => (
                    <li key={d} className="rounded border border-line px-2 py-1 font-mono text-[11px] text-white/60">
                      {d}
                    </li>
                  ))}
                </ul>
                {echoes.data.public.length === 0 ? (
                  <p className="text-sm text-white/50">No public echoes in the stream yet.</p>
                ) : (
                  <ul className="flex flex-col gap-2" data-testid="novanet-echoes">
                    {echoes.data.public.slice(0, 8).map((e) => (
                      <li key={e.id} className="rounded border border-line bg-ink/40 p-3">
                        <p className="text-sm text-white/85">{e.title}</p>
                        <p className="font-mono text-[10px] text-white/35">
                          {e.source} · resonance {e.resonance}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <ContractState state={echoes.state} error={echoes.error?.message} onRetry={echoes.reload} />
            )}
          </Panel>
        </div>
      )}

      {section !== "field" && section !== "echoes" && (
        <NotYetWired
          contract={DEFERRED[section] ?? "UNKNOWN"}
          note={`The legacy Nexus hub's "${section}" sub-view is declared but its contract is not reconciled in the console yet.`}
        />
      )}
    </Page>
  );
}
