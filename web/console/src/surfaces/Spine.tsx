import { STAGES, SPINE_EDGES, FEEDBACK_EDGES } from "../lib/grammar";
import { PostureChip } from "../components/ui";
import { Link } from "react-router-dom";

/**
 * 01 · Spine — the causal system view.
 *
 * Renders the grammar as a causal spine with explicit feedback edges. It never
 * implies that every edge is currently traversable: each stage carries its
 * posture, and the feedback edges are drawn distinctly from the causal ones.
 */
export function Spine() {
  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card">
        <p className="small dim" style={{ marginTop: 0 }}>
          The grammar is a cycle with a causal spine, not a linear wizard. Moving forward does not
          imply completion — REVIEW can change what is AUTHORIZED, EVIDENCE can expose an EXECUTION
          problem, and VERIFICATION can leave a boundary unresolved.
        </p>
      </div>

      <div className="spine">
        {STAGES.map((s, i) => (
          <div key={s.id} className="spine-step">
            <Link to={`/boundary/${s.id.toLowerCase()}`} className="spine-node">
              <div className="spine-index mono">{String(i + 1).padStart(2, "0")}</div>
              <div className="spine-body">
                <div className="spine-label">{s.label}</div>
                <div className="spine-q">{s.question}</div>
                <PostureChip posture={s.posture} compact />
              </div>
            </Link>
            {i < STAGES.length - 1 && <div className="spine-edge" aria-hidden />}
          </div>
        ))}
      </div>

      <div className="card">
        <h3 className="card-title">Causal edges</h3>
        <div className="edge-list">
          {SPINE_EDGES.map(([a, b]) => (
            <div key={`${a}-${b}`} className="edge mono">
              {a} <span className="edge-arrow">→</span> {b}
            </div>
          ))}
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
