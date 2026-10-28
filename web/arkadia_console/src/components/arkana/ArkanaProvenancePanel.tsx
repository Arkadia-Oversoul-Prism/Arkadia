/**
 * Arkana — response provenance panel (read-only).
 *
 * Renders the three retrieval channels `POST /api/commune/resonance` already
 * returns for each reply: the corpus scrolls scored into the prompt, the
 * Knowledge OS notes actually injected, and the memory turn metadata. This
 * recovers a capability the archived Prism projected — a reader could see what
 * informed a reply — without inventing a single reference.
 *
 * The panel is pure display: it issues no request of its own and exposes no
 * control. When a reply reported no retrieval, it says so plainly rather than
 * implying the Oracle "found nothing" or rendering an empty decoration.
 */
import type { ReactNode } from "react";
import type {
  ArkanaProvenance,
  ArkanaRagRef,
  ArkanaSourceRef,
} from "./arkanaProvenanceContract";
import { hasRetrieval, ragLabel, sourceTitle } from "./arkanaProvenanceContract";

function Channel({
  title,
  count,
  children,
}: {
  title: string;
  count: number;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">
        {title} · {count}
      </p>
      {children}
    </div>
  );
}

function RagRow({ ref }: { ref: ArkanaRagRef }) {
  return (
    <div className="flex flex-wrap items-baseline gap-2" title={ref.label ? String(ref.label) : undefined}>
      <span className="text-emerald/50">◆</span>
      <span className="font-mono text-[10px] text-white/55">{ragLabel(ref)}</span>
      {ref.category && (
        <span className="font-mono text-[9px] text-white/25">{String(ref.category)}</span>
      )}
    </div>
  );
}

function SourceRow({ ref }: { ref: ArkanaSourceRef }) {
  return (
    <div className="flex flex-wrap items-baseline gap-2" title={ref.excerpt || sourceTitle(ref)}>
      <span className="text-emerald/50">◆</span>
      <span className="font-mono text-[10px] text-white/55">{sourceTitle(ref)}</span>
      <span className="font-mono text-[9px] text-white/25">
        {ref.type ?? "note"}
        {ref.via === "graph" ? " · linked" : ""}
      </span>
    </div>
  );
}

export function ArkanaProvenancePanel({ provenance }: { provenance: ArkanaProvenance }) {
  const memory = provenance.memory;

  return (
    <div className="mt-2 flex flex-col gap-2 rounded border border-line/60 bg-ink/30 p-2" data-testid="arkana-provenance">
      <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">Response provenance</p>

      {!hasRetrieval(provenance) ? (
        <p className="text-[11px] text-white/40" data-testid="arkana-provenance-none">
          This reply was synthesised without retrieved corpus or memory context — it is general reasoning, not a
          citation of stored material.
        </p>
      ) : (
        <>
          <Channel title="Corpus scrolls" count={provenance.ragRefs.length}>
            {provenance.ragRefs.length === 0 ? (
              <p className="text-[11px] text-white/35">No corpus scrolls scored into this turn.</p>
            ) : (
              provenance.ragRefs.map((ref, i) => <RagRow key={`${ref.id ?? "rag"}-${i}`} ref={ref} />)
            )}
          </Channel>

          <Channel title="Knowledge OS notes" count={provenance.sources.length}>
            {provenance.sources.length === 0 ? (
              <p className="text-[11px] text-white/35">No Knowledge OS notes were injected into this turn.</p>
            ) : (
              provenance.sources.map((ref, i) => <SourceRow key={`${ref.id ?? "src"}-${i}`} ref={ref} />)
            )}
          </Channel>
        </>
      )}

      {memory && (
        <p className="font-mono text-[9px] text-white/25" data-testid="arkana-provenance-memory">
          memory: {memory.notes_retrieved ?? 0} note(s) retrieved · {memory.source ?? "knowledge_os"}
          {memory.thread_id != null ? ` · thread ${memory.thread_id}` : ""}
        </p>
      )}
    </div>
  );
}
