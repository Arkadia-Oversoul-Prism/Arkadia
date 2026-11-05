/**
 * Typed artifact rendering for the Solariun canvas.
 *
 * The rendering pipeline is: semantic response → artifact selection → render →
 * provenance. This module owns the *render* step for the typed artifacts a
 * response can carry (code, diff, table, chart, diagram, trace).
 *
 * Two rules are structural, not stylistic:
 *
 * 1. **SVG is a rendering format, not an authority layer.** A diagram node is
 *    never a control. `DiagramArtifact` renders `<g>` elements with no click
 *    handler, no `onClick`, no `role="button"` — so a node cannot silently
 *    trigger a privileged operation. Interactive affordances live in the
 *    composer and the inspector, where the authorization boundary is explicit.
 *
 * 2. **A visualization is never fabricated.** `selectArtifact` returns `null`
 *    for an ordinary answer, and the canvas then renders plain Markdown. A chart
 *    is only produced when the response actually carried structured series data.
 */
import { type ReactNode } from "react";

export type ArtifactKind = "code" | "diff" | "table" | "chart" | "diagram" | "trace";

export interface CodeArtifact {
  kind: "code";
  language?: string;
  content: string;
  path?: string;
}

export interface DiffArtifact {
  kind: "diff";
  path: string;
  hunks: Array<{ header: string; lines: Array<{ type: "add" | "del" | "ctx"; text: string }> }>;
}

export interface TableArtifact {
  kind: "table";
  columns: string[];
  rows: Array<Array<string | number>>;
  caption?: string;
}

export interface ChartArtifact {
  kind: "chart";
  chart: "bar" | "line";
  series: Array<{ label: string; value: number }>;
  unit?: string;
  caption?: string;
}

export interface DiagramArtifact {
  kind: "diagram";
  nodes: Array<{ id: string; label: string; x: number; y: number; tone?: "gold" | "teal" | "neutral" }>;
  edges: Array<{ from: string; to: string; label?: string }>;
  caption?: string;
}

export interface TraceArtifact {
  kind: "trace";
  steps: Array<{ label: string; state: "done" | "running" | "pending" | "refused"; detail?: string }>;
  caption?: string;
}

export type Artifact =
  | CodeArtifact
  | DiffArtifact
  | TableArtifact
  | ChartArtifact
  | DiagramArtifact
  | TraceArtifact;

/**
 * Decide whether a response needs a typed artifact.
 *
 * Returns `null` for an ordinary answer — the canvas then renders Markdown
 * alone. This is the guard against "fabricate a visualization for every
 * answer": a chart requires real series data, a diagram requires real nodes.
 */
export function selectArtifact(input: {
  code?: CodeArtifact;
  diff?: DiffArtifact;
  table?: TableArtifact;
  chart?: ChartArtifact;
  diagram?: DiagramArtifact;
  trace?: TraceArtifact;
}): Artifact | null {
  if (input.diff) return input.diff;
  if (input.chart && input.chart.series.length > 0) return input.chart;
  if (input.diagram && input.diagram.nodes.length > 0) return input.diagram;
  if (input.table && input.table.rows.length > 0) return input.table;
  if (input.trace && input.trace.steps.length > 0) return input.trace;
  if (input.code) return input.code;
  return null;
}

const TONE_FILL: Record<string, string> = {
  gold: "var(--cg-gold)",
  teal: "var(--cg-teal)",
  neutral: "var(--cg-line)",
};

function CodeArtifactView({ artifact }: { artifact: CodeArtifact }) {
  return (
    <figure className="cg-artifact" data-testid="artifact-code">
      <figcaption className="cg-artifact-cap">
        <span className="font-mono text-[10px] uppercase tracking-widest text-white/45">
          {artifact.language ?? "code"}
        </span>
        {artifact.path ? (
          <span className="font-mono text-[10px] text-white/35">{artifact.path}</span>
        ) : null}
      </figcaption>
      <pre className="cg-artifact-pre">
        <code>{artifact.content}</code>
      </pre>
    </figure>
  );
}

function DiffArtifactView({ artifact }: { artifact: DiffArtifact }) {
  return (
    <figure className="cg-artifact" data-testid="artifact-diff">
      <figcaption className="cg-artifact-cap">
        <span className="font-mono text-[10px] uppercase tracking-widest text-white/45">diff</span>
        <span className="font-mono text-[10px] text-white/35">{artifact.path}</span>
      </figcaption>
      <div className="cg-artifact-diff">
        {artifact.hunks.map((hunk, hi) => (
          <div key={hi}>
            <p className="cg-diff-header">{hunk.header}</p>
            {hunk.lines.map((line, li) => (
              <p key={li} className={`cg-diff-line cg-diff-${line.type}`}>
                <span className="cg-diff-gutter" aria-hidden>
                  {line.type === "add" ? "+" : line.type === "del" ? "-" : " "}
                </span>
                {line.text}
              </p>
            ))}
          </div>
        ))}
      </div>
    </figure>
  );
}

function TableArtifactView({ artifact }: { artifact: TableArtifact }) {
  return (
    <figure className="cg-artifact" data-testid="artifact-table">
      {artifact.caption ? <figcaption className="cg-artifact-cap">{artifact.caption}</figcaption> : null}
      <div className="cg-artifact-scroll">
        <table className="cg-artifact-table">
          <thead>
            <tr>
              {artifact.columns.map((column) => (
                <th key={column} scope="col">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {artifact.rows.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

function ChartArtifactView({ artifact }: { artifact: ChartArtifact }) {
  const max = Math.max(...artifact.series.map((s) => s.value), 1);
  const width = 520;
  const height = 200;
  const pad = 28;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;
  const step = innerW / Math.max(artifact.series.length, 1);

  return (
    <figure className="cg-artifact" data-testid="artifact-chart">
      {artifact.caption ? <figcaption className="cg-artifact-cap">{artifact.caption}</figcaption> : null}
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="cg-artifact-svg"
        role="img"
        aria-label={`${artifact.chart} chart: ${artifact.series
          .map((s) => `${s.label} ${s.value}${artifact.unit ?? ""}`)
          .join(", ")}`}
      >
        {artifact.chart === "bar"
          ? artifact.series.map((s, i) => {
              const barH = (s.value / max) * innerH;
              return (
                <g key={s.label}>
                  <rect
                    x={pad + i * step + step * 0.2}
                    y={pad + innerH - barH}
                    width={step * 0.6}
                    height={barH}
                    rx={3}
                    fill="var(--cg-teal)"
                    opacity={0.75}
                  />
                  <text
                    x={pad + i * step + step * 0.5}
                    y={height - 8}
                    textAnchor="middle"
                    className="cg-svg-label"
                  >
                    {s.label}
                  </text>
                </g>
              );
            })
          : (
            <polyline
              fill="none"
              stroke="var(--cg-gold)"
              strokeWidth={2}
              points={artifact.series
                .map((s, i) => `${pad + i * step + step * 0.5},${pad + innerH - (s.value / max) * innerH}`)
                .join(" ")}
            />
          )}
        <line
          x1={pad}
          y1={pad + innerH}
          x2={width - pad}
          y2={pad + innerH}
          stroke="var(--cg-line)"
        />
      </svg>
      <p className="cg-artifact-note">
        Rendered from {artifact.series.length} structured data point(s) returned by the response.
      </p>
    </figure>
  );
}

/**
 * A diagram node is inert by construction: no handler, no button role, no
 * tabindex. Clicking a node cannot dispatch anything — the only way to act is
 * through the composer or the inspector, where authorization is explicit.
 */
function DiagramArtifactView({ artifact }: { artifact: DiagramArtifact }) {
  const byId = Object.fromEntries(artifact.nodes.map((n) => [n.id, n]));
  return (
    <figure className="cg-artifact" data-testid="artifact-diagram">
      {artifact.caption ? <figcaption className="cg-artifact-cap">{artifact.caption}</figcaption> : null}
      <svg
        viewBox="0 0 520 240"
        className="cg-artifact-svg"
        role="img"
        aria-label={`Diagram: ${artifact.nodes.map((n) => n.label).join(" → ")}`}
      >
        {artifact.edges.map((edge, i) => {
          const from = byId[edge.from];
          const to = byId[edge.to];
          if (!from || !to) return null;
          return (
            <g key={i}>
              <line
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke="var(--cg-line)"
                strokeWidth={1.5}
                markerEnd="url(#cg-arrow)"
              />
              {edge.label ? (
                <text
                  x={(from.x + to.x) / 2}
                  y={(from.y + to.y) / 2 - 6}
                  textAnchor="middle"
                  className="cg-svg-label"
                >
                  {edge.label}
                </text>
              ) : null}
            </g>
          );
        })}
        <defs>
          <marker id="cg-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 z" fill="var(--cg-line)" />
          </marker>
        </defs>
        {artifact.nodes.map((node) => (
          <g key={node.id}>
            <rect
              x={node.x - 62}
              y={node.y - 18}
              width={124}
              height={36}
              rx={8}
              fill="rgba(255,255,255,0.03)"
              stroke={TONE_FILL[node.tone ?? "neutral"]}
              strokeWidth={1.2}
            />
            <text x={node.x} y={node.y + 4} textAnchor="middle" className="cg-svg-node-label">
              {node.label}
            </text>
          </g>
        ))}
      </svg>
      <p className="cg-artifact-note">
        Nodes are inert: a diagram renders state, it never dispatches an operation.
      </p>
    </figure>
  );
}

const TRACE_TONE: Record<string, string> = {
  done: "text-emerald",
  running: "text-gold",
  pending: "text-white/40",
  refused: "text-red-300",
};

function TraceArtifactView({ artifact }: { artifact: TraceArtifact }) {
  return (
    <figure className="cg-artifact" data-testid="artifact-trace">
      {artifact.caption ? <figcaption className="cg-artifact-cap">{artifact.caption}</figcaption> : null}
      <ol className="cg-trace">
        {artifact.steps.map((step, i) => (
          <li key={i} className="cg-trace-step">
            <span className={`cg-trace-dot ${TRACE_TONE[step.state] ?? "text-white/40"}`} aria-hidden />
            <div className="min-w-0">
              <p className="text-xs text-white/80">
                {step.label}
                <span className="ml-2 font-mono text-[10px] uppercase tracking-widest text-white/35">
                  {step.state}
                </span>
              </p>
              {step.detail ? <p className="mt-0.5 text-[11px] text-white/45">{step.detail}</p> : null}
            </div>
          </li>
        ))}
      </ol>
    </figure>
  );
}

export function ArtifactView({ artifact }: { artifact: Artifact }): ReactNode {
  switch (artifact.kind) {
    case "code":
      return <CodeArtifactView artifact={artifact} />;
    case "diff":
      return <DiffArtifactView artifact={artifact} />;
    case "table":
      return <TableArtifactView artifact={artifact} />;
    case "chart":
      return <ChartArtifactView artifact={artifact} />;
    case "diagram":
      return <DiagramArtifactView artifact={artifact} />;
    case "trace":
      return <TraceArtifactView artifact={artifact} />;
    default:
      return null;
  }
}
