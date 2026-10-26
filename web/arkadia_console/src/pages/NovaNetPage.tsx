/**
 * NovaNet — the public field and Nexus hub.
 *
 * Two halves over one backend: the public field (`/api/transmissions`, the
 * legacy `NovaNetPage` social feed) and the unified echoes stream
 * (`/api/echoes`, the public Crystal-Matrix aggregation). Both contracts are
 * public reads, so this surface is reachable without an identity — but it never
 * fabricates content: an unavailable read renders the honest contract state.
 *
 * The field renders the archived product's author-only Edit / Delete controls
 * (`AuthorControls`): the public read is open, but the mutation is offered only
 * to the verified owner whose uid equals the post's `owner_uid`, mirroring the
 * backend's own 401/403 boundary rather than deciding ownership client-side.
 *
 * The legacy hub carried sub-views (`/nexus/ims`, `/nexus/grove`,
 * `/nexus/larder`, `/nexus/distribution`). They are not reconciled yet, so they
 * are **not** rendered as controls: a lens that does nothing is a decorative
 * control (directive §4).
 *
 * The `codex` lens **is** reconciled. The archive's `/encyclopedia` and
 * `/spiral-codex` routes both read `GET /api/codex` — the shared public corpus,
 * an open read serving 661 documents and 4.4M characters on the canonical
 * deployment — and the console referenced it nowhere. Unlike the deferred
 * sub-views it needs no identity, so the earlier blanket claim that the hub's
 * contracts are "unverified or sovereign-key gated" was wrong for it and is
 * corrected in the note below.
 */
import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { SurfaceLenses } from "../components/SurfaceLenses";
import { AuthorControls } from "../components/novaNet/AuthorControls";
import { EngagementBar } from "../components/novaNet/EngagementBar";
import { TransmissionComposer } from "../components/novaNet/TransmissionComposer";
import { SpiralCodexPanel } from "../components/novaNet/SpiralCodexPanel";
import { StellarCartographyPanel } from "../components/novaNet/StellarCartographyPanel";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { useAuth } from "../contexts/AuthContext";
import { endpoints } from "../lib/endpoints";
import type { SurfaceId } from "../lib/surfaces";
import type { EchoesFeed, TransmissionList } from "../lib/types";

const LENSES = [
  { id: "field", label: "Field" },
  { id: "echoes", label: "Echoes" },
  { id: "codex", label: "Encyclopedia Galactica" },
  { id: "hub", label: "Nexus Hub" },
];

/** The lens ids this surface declares; a section outside this set is not a lens. */
const LENS_IDS = new Set(LENSES.map((l) => l.id));

/**
 * The echoes panel renders at most this many public entries per read. The
 * bound is single-sourced here so the rendered subset, the stated total, and
 * the truncation notice can never drift apart: a reader must be able to see
 * that the panel is showing a subset, not the whole stream.
 */
const ECHO_DISPLAY_LIMIT = 8;

type HubSubView = { contract: string; disposition: string };

/**
 * The legacy Nexus hub sub-views that are declared in the reconciliation
 * inventory but not reconciled here, each with the contract *measured on this
 * revision*. The table is the single source for both the panel's `contract` and
 * its note, so the rendered claim cannot drift from the measurement.
 *
 * A sub-view is listed only after its handler (or the measured absence of one)
 * was read. `UNKNOWN` is deliberately not a value here: leaving the whole lens
 * as UNKNOWN is what this table replaces.
 */
const HUB_SUBVIEWS: Record<string, HubSubView> = {
  ims: {
    contract: "GET /api/ims/inquiries",
    disposition:
      "Sovereign-only. The handler requires an x-sovereign-key header and answers 403 'Sovereign key required' without it; the Bearer-only client cannot satisfy that, so the archive is not reconciled.",
  },
  grove: {
    contract: "none — no HTTP surface on this revision",
    disposition:
      "spiral_grove/ is a capability registry and learning-path domain layer; it declares no router and is not mounted in api/main.py, so there is no contract to reconcile against.",
  },
  larder: {
    contract: "POST /api/orders (open) · GET /api/orders (sovereign-only)",
    disposition:
      "Order intake is open, but the read is gated on the same x-sovereign-key header as the IMS archive. A lens could accept an order and then never list what it submitted, which is a worse state than not rendering one.",
  },
  distribution: {
    contract: "GET /api/distribution/releases/{artist_id} (open)",
    disposition:
      "The read is open, but the archived DistributePage drives upload, covenant/sign and submit — all write paths. No release-creation authority was verified, so no decorative control is rendered.",
  },
};

/** Sub-views in the inventory that this revision does not classify. */
const UNCLASSIFIED_HUB_SUBVIEWS: readonly string[] = [];

const HUB_SUBVIEW_IDS = Object.keys(HUB_SUBVIEWS);

const HUB_CONTRACT_SUMMARY = HUB_SUBVIEW_IDS.map(
  (id) => `${id}: ${HUB_SUBVIEWS[id].contract}`,
).join(" · ");

const HUB_NOTE = [
  "The legacy Nexus hub's remaining sub-views are declared in the reconciliation inventory but not reconciled in the console, so no decorative controls are rendered for them.",
  "Each was measured on this revision rather than left as a blanket 'unverified' claim:",
  ...HUB_SUBVIEW_IDS.map((id) => `${id} — ${HUB_SUBVIEWS[id].disposition}`),
  "The shared corpus (/api/codex) was measured as an open read and IS reconciled on the Encyclopedia Galactica lens.",
].join(" ");

/**
 * A section outside `LENS_IDS` is not a lens of this surface, so this page holds
 * no contract reading for it. Named rather than inlined so the panel does not
 * read as if a per-section contract had been looked up and came back unknown.
 */
const NON_LENS_CONTRACT = "UNKNOWN";

function ago(ts: number): string {
  const delta = Date.now() - ts;
  if (delta < 60_000) return "now";
  if (delta < 3_600_000) return `${Math.floor(delta / 60_000)}m`;
  if (delta < 86_400_000) return `${Math.floor(delta / 3_600_000)}h`;
  return `${Math.floor(delta / 86_400_000)}d`;
}

export function NovaNetPage({
  section = "field",
  onNavigate,
}: {
  section?: string;
  onNavigate: (id: SurfaceId, section?: string) => void;
}) {
  const field = useHydration<TransmissionList>(endpoints.transmissions, (p) => apiRequest<TransmissionList>(p));
  const echoes = useHydration<EchoesFeed>(endpoints.echoes, (p) => apiRequest<EchoesFeed>(p), [section === "echoes"]);
  // The verified uid gates the author controls. It is the same identity the
  // backend resolves the owner from, so the client offers a mutation only where
  // the backend would accept it — it never decides ownership itself.
  const { user, profile, isAuthenticated } = useAuth();
  const myUid = user?.uid ?? null;

  return (
    <Page title="NovaNet" subtitle="The public field — transmissions, echoes, and the shared Nexus hub over one canonical backend.">
      <SurfaceLenses
        surface="novanet"
        lenses={LENSES}
        section={section}
        accent="text-azure"
        onNavigate={onNavigate}
      />

      {(section === "field" || section === "echoes") && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel>
            <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
              Public field · {field.data ? `${field.data.total} transmissions` : "—"}
            </p>
            {/* The archived field opened with a composer gated on the verified
                identity. `POST /api/transmissions` is live; on success the feed
                is re-read so the server's own list (and count) is shown. */}
            <TransmissionComposer
              isAuthenticated={isAuthenticated}
              profile={profile}
              onCreated={() => field.reload()}
            />
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
                      {/* Declared engagement readings the feed already returns,
                          made interactive against the two live write handlers
                          (react / comment) the router serves (see EngagementBar).
                          `reposts` stays a reading — no verified write path. */}
                      <EngagementBar transmission={t} onChanged={field.reload} />
                      <AuthorControls
                        transmission={t}
                        isOwn={Boolean(myUid && t.owner_uid && myUid === t.owner_uid)}
                        onChanged={field.reload}
                      />
                    </li>
                  ))}
                </ul>
              )
            ) : (
              <ContractState state={field.state} error={field.error?.message} onRetry={field.reload} />
            )}
          </Panel>

          <Panel>
            <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
              Crystal Matrix · echoes
              {echoes.state === "ready" && echoes.data
                ? ` · ${echoes.data.public.length} public`
                : ""}
            </p>
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
                  <>
                    <ul className="flex flex-col gap-2" data-testid="novanet-echoes">
                      {echoes.data.public.slice(0, ECHO_DISPLAY_LIMIT).map((e) => (
                        <li key={e.id} className="rounded border border-line bg-ink/40 p-3">
                          <p className="text-sm text-white/85">{e.title}</p>
                          <p className="font-mono text-[10px] text-white/35">
                            {e.source} · resonance {e.resonance}
                          </p>
                        </li>
                      ))}
                    </ul>
                    {echoes.data.public.length > ECHO_DISPLAY_LIMIT && (
                      <p className="font-mono text-[11px] text-white/40" data-testid="novanet-echoes-truncation">
                        Showing {ECHO_DISPLAY_LIMIT} of {echoes.data.public.length} public echoes — the
                        remainder is not rendered on this surface.
                      </p>
                    )}
                  </>
                )}
              </div>
            ) : (
              <ContractState state={echoes.state} error={echoes.error?.message} onRetry={echoes.reload} />
            )}
          </Panel>
        </div>
      )}

      {section === "codex" && (
        <>
          {/* The readout heads the lens, as it did in the archive
              (`NexusSpiralCodex.tsx:953`), above the corpus it indexes. */}
          <StellarCartographyPanel />
          <SpiralCodexPanel />
        </>
      )}

      {!LENS_IDS.has(section) && (
        <NotYetWired
          contract={NON_LENS_CONTRACT}
          note={`"${section}" is not a lens of this surface. The reconciled lenses are ${[...LENS_IDS]
            .map((id) => `"${id}"`)
            .join(", ")}.`}
        />
      )}

      {section === "hub" && (
        <>
          <NotYetWired contract={HUB_CONTRACT_SUMMARY} note={HUB_NOTE} />
          <Panel className="mt-4">
            <p
              className="font-mono text-[11px] uppercase tracking-widest text-white/40"
              data-testid="novanet-hub-classification"
            >
              Hub sub-view contracts · measured
            </p>
            <Facts
              rows={HUB_SUBVIEW_IDS.map((id) => ({
                label: id,
                value: `${HUB_SUBVIEWS[id].contract} — ${HUB_SUBVIEWS[id].disposition}`,
              }))}
            />
            {UNCLASSIFIED_HUB_SUBVIEWS.length > 0 && (
              <p className="mt-3 font-mono text-[11px] text-amber-300/80">
                Not yet classified: {UNCLASSIFIED_HUB_SUBVIEWS.join(", ")}
              </p>
            )}
          </Panel>
        </>
      )}
    </Page>
  );
}
