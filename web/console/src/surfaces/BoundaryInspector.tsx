import { Link } from "react-router-dom";
import { STAGES } from "../lib/grammar";
import { deploymentHeadline } from "../lib/posture";
import { Card, PostureChip, Pill } from "../components/ui";

/**
 * 02 · Boundary Inspector — the forensic view.
 *
 * For any boundary: what it means, its implementation, enforcement, test,
 * posture, provenance, and current limitations. This inherits the strongest
 * part of the derived console: it renders what can be proven, and names what
 * cannot.
 */
export function BoundaryInspector() {
  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card">
        <p className="small dim" style={{ marginTop: 0 }}>
          Every boundary carries two independent properties: its mechanism (enforced vs declared)
          and how far its deployment has travelled. Nothing here is rendered as a bare “✓”.
        </p>
      </div>

      {STAGES.map((s) => (
        <Card
          key={s.id}
          title={
            <span className="row" style={{ gap: 10 }}>
              {s.label}
              <Pill tone="muted">{deploymentHeadline(s.posture.deployment)}</Pill>
            </span>
          }
          actions={<Link to={`/boundary/${s.id.toLowerCase()}`} className="btn ghost sm">inspect</Link>}
        >
          <div className="grid cols-2" style={{ gap: 16 }}>
            <div>
              <div className="subhead">Question</div>
              <div className="small">{s.question}</div>
              <div className="subhead mt">Surface</div>
              <div className="mono tiny">{s.surface}</div>
              <div className="subhead mt">Enforcement</div>
              <div className="mono tiny">{s.enforcement}</div>
            </div>
            <div>
              <div className="subhead">Evidence</div>
              <ul className="evidence-list">
                {s.evidence.map((e) => (
                  <li key={e} className="mono tiny">{e}</li>
                ))}
              </ul>
              <div className="subhead mt">Posture</div>
              <PostureChip posture={s.posture} />
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
