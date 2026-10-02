import type { ReactNode } from "react";
import {
  deploymentLadder,
  postureTone,
  type Posture,
  type PostureTone,
} from "../lib/posture";
import type { StandingState } from "../lib/standing";

/**
 * Shared primitives. The PostureChip is the console's most important control:
 * it makes the four deployment rungs individually visible so they can never be
 * collapsed into a single "✓".
 */

export function Card({
  title,
  actions,
  children,
  className,
}: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card ${className ?? ""}`}>
      {(title || actions) && (
        <div className="row between" style={{ marginBottom: title ? 12 : 0 }}>
          {title && <h3 className="card-title" style={{ margin: 0 }}>{title}</h3>}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function Pill({ tone = "muted", children }: { tone?: string; children: ReactNode }) {
  return <span className={`pill ${tone}`}>{children}</span>;
}

export function Chip({ children }: { children: ReactNode }) {
  return <span className="chip">{children}</span>;
}

/**
 * The two-axis posture display. Renders mechanism + each deployment rung as a
 * separate lamp. This is the primitive that replaces a bare status badge.
 */
export function PostureChip({ posture, compact }: { posture: Posture; compact?: boolean }) {
  const tone: PostureTone = postureTone(posture);
  const mech =
    posture.mechanism === "ENFORCED"
      ? "ENFORCED"
      : posture.mechanism === "ENFORCED_UNTESTED"
        ? "ENFORCED (untested)"
        : "DECLARED";
  const rungs = deploymentLadder(posture.deployment);

  return (
    <div className={`posture posture-${tone}`}>
      <div className="posture-mech">
        <span className="posture-key">MECHANISM</span>
        <span className="posture-val">{mech}</span>
      </div>
      <div className="posture-ladder">
        {rungs.map((r) => (
          <span key={r.key} className={`rung ${r.reached ? "on" : "off"}`} title={r.label}>
            <span className="rung-lamp" />
            {!compact && <span className="rung-label">{r.label}</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

export function StandingBanner({ state }: { state: StandingState }) {
  return (
    <div className={`standing standing-${state.tone}`}>
      <div className="standing-head">{state.headline}</div>
      <div className="standing-detail">{state.detail}</div>
    </div>
  );
}

export function Kv({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="kv">
      {items.map(([k, v], i) => (
        <div key={i} style={{ display: "contents" }}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json">{JSON.stringify(value, null, 2)}</pre>;
}
