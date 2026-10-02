import { STAGES, SPINE_EDGES, FEEDBACK_EDGES } from "../lib/grammar";
import { edgeStatusTone, type EdgeStatus } from "../lib/posture";
import { PostureChip } from "../components/ui";
import { Link } from "react-router-dom";

/** The witnessed status of the edge between two stages (defaults to unresolved). */
function statusBetween(from: string, to: string): EdgeStatus {
  const e = SPINE_EDGES.find((x) => x.from === from && x.to === to);
  return e ? e.status : "UNRESOLVED";
}

/**
 * 01 · Spine — the causal system view.
 *
 * Renders the grammar as a causal spine with explicit feedback edges. It never
 * implies that every edge is currently traversable: each stage carries its
 * posture, and each EDGE carries its own witnessed status — a PRODUCTION-VERIFIED
 * stage can still emit a CONTRADICTED edge (EXECUTION → WORK_EVENT).
 */
export function Spine() {
  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card">
        <p className="small dim" style={{ marginTop: 0 }}>
          The grammar is a cycle with a causal spine, not a linear wizard. Moving forward does not
          imply completion — REVIEW can change what is AUTHORIZED, EVIDENCE can expose an EXECUTION
          problem, and VERIFICATION can leave a boundary unresolved. Edges are labelled with their
          runtime witness; a stage being production-verified does not make its outgoing edge
          traversable.
        </p>
      </div>

      <div className="spine">
        {STAGES.map((s, i) => {
          const next = STAGES[i + 1];
          const edge = next ? statusBetween(s.id, next.id) : null;
          const tone = edge ? edgeStatusTone(edge) : null;
          return (
            <div key={s.id} className="spine-step">
              <Link to={`/boundary/${s.id.toLowerCase()}`} className="spine-node">
                <div className="spine-index mono">{String(i + 1).padStart(2, "0")}</div>
                <div className="spine-body">
                  <div className="spine-label">{s.label}</div>
                  <div className="spine-q">{s.question}</div>
                  <PostureChip posture={s.posture} compact />
                </div>
              </Link>
              {edge && (
                <div className={`spine-edge ${tone === "demonstrated" ? "" : tone}`} aria-hidden />
              )}
            </div>
          );
        })}
      </div>

      <div className="card">
        <h3 className="card-title">Causal edges — with witness</h3>
        <p className="tiny faint" style={{ marginTop: 0 }}>
          Each edge carries its own status. CONTRADICTED and UNRESOLVED edges are drawn with a
          different glyph, never as a plain causal arrow.
        </p>
        <div className="edge-list">
          {SPINE_EDGES.map((e) => {
            const tone = edgeStatusTone(e.status);
            const glyph = e.status === "CONTRADICTED" ? "⊣" : e.status === "UNRESOLVED" ? "?" : "→";
            return (
              <div key={`${e.from}-${e.to}`} className={`edge edge-${tone}`}>
                <span className="mono edge-line">
                  {e.from} <span className="edge-arrow">{glyph}</span> {e.to}
                </span>
                <span className={`edge-status ${tone}`}>{e.status}</span>
                <span className="edge-witness">{e.witness}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card">
        <h3 className="card-title">Feedback edges</h3>
        <p className="tiny faint" style={{ marginTop: 0 }}>
          Not continuations. These are the paths by which a later stage changes an earlier one.
        </p>
        <div className="edge-list">
          {FEEDBACK_EDGES.map((e) => (
            <div key={`${e.from}-${e.to}`} className="edge edge-feedback">
              <span className="mono">
                {e.from} <span className="edge-arrow feedback">⟲</span> {e.to}
              </span>
              <span className="tiny faint">{e.why}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
