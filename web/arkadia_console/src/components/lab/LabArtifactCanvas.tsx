/**
 * Engineering Lab — artifact canvas read surface (Workstream 4, feature-local).
 *
 * `GET /api/lab/engineering/artifacts` lists the owner-scoped artifacts a session
 * produced; `GET /api/lab/engineering/canvas/{artifact_id}` projects one into a
 * truthful view descriptor (`canvas_view`): a canonical `renderer` name, an
 * `available` flag, and the declared `actions`.
 *
 * Read-only by construction: GET only. The descriptor's `actions` are declared
 * UI affordances on the backend — none is an execution or authorization act —
 * and the console does not yet implement any of them, so they are rendered as
 * clearly non-interactive labels rather than buttons that would do nothing.
 *
 * Truthfulness rule from the backend contract: `available` is false when no
 * content was captured. The surface must not render a placeholder as if it were
 * a real artifact, so an unavailable artifact states *why* it is empty.
 */
import { useState } from "react";
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";

export interface LabArtifact {
  artifact_id: string;
  session_id?: string;
  run_id?: string | null;
  kind?: string;
  title?: string;
  content?: unknown;
  created_at?: string;
}

interface CanvasDescriptor {
  artifact: LabArtifact;
  renderer: string;
  available: boolean;
  kind: string;
  actions: string[];
  unavailable_reason: string;
}

/** Content is rendered as source text only when it is genuinely present and a
 * string; anything else is reported as captured-but-not-textual, never faked. */
function canvasContent(descriptor: CanvasDescriptor): { text: string | null; note: string } {
  if (!descriptor.available) return { text: null, note: descriptor.unavailable_reason };
  const { content } = descriptor.artifact;
  if (typeof content === "string") return { text: content, note: "" };
  return { text: null, note: "content captured as structured data — no text renderer wired" };
}

/**
 * `GET /engineering/canvas/{artifact_id}` is a sub-resource of the declared
 * artifacts collection. `/canvas/{id}` is not a separate registry entry
 * (Workstream 1 owns `lib/endpoints.ts`; a first-class `labCanvas(id)` is the
 * recorded request), so the path swaps the collection's terminal segment. The
 * expression stays inline at the call site so the first `useHydration` argument
 * is literally `endpoints.labArtifacts…` — the registry-contract guard requires
 * a registry member there.
 */
function CanvasDetail({ artifactId }: { artifactId: string }) {
  const canvas = useHydration<CanvasDescriptor>(
    endpoints.labArtifacts.replace(/\/artifacts$/, "/canvas/") + encodeURIComponent(artifactId),
    (p) => apiRequest<CanvasDescriptor>(p),
  );

  if (canvas.state !== "ready" || !canvas.data) {
    return (
      <div className="mt-2">
        <ContractState state={canvas.state} error={canvas.error?.message} onRetry={canvas.reload} />
      </div>
    );
  }

  const descriptor = canvas.data;
  const { text, note } = canvasContent(descriptor);

  return (
    <div className="mt-2 rounded border border-line bg-ink/40 p-3" data-testid="lab-canvas">
      <Facts
        rows={[
          { label: "kind", value: descriptor.kind },
          { label: "renderer (declared)", value: descriptor.renderer },
          { label: "content available", value: descriptor.available ? "yes" : "no" },
          { label: "run", value: descriptor.artifact.run_id ?? "—" },
        ]}
      />

      {text !== null ? (
        <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-black/40 p-2 font-mono text-[11px] text-white/70">
          {text}
        </pre>
      ) : (
        <p className="mt-3 text-xs text-white/45" data-testid="lab-canvas-unavailable">
          {note}
        </p>
      )}

      <p className="mt-3 font-mono text-[10px] uppercase tracking-wider text-white/35">
        declared actions (not wired): {descriptor.actions.join(" · ")}
      </p>
    </div>
  );
}

export function LabArtifactCanvas() {
  const artifacts = useHydration<{ artifacts: LabArtifact[]; count: number }>(
    endpoints.labArtifacts,
    (p) => apiRequest<{ artifacts: LabArtifact[]; count: number }>(p),
  );
  const [selected, setSelected] = useState<string | null>(null);
  const rows = artifacts.data?.artifacts ?? [];

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Artifact canvas
      </p>
      <p className="mb-4 text-xs text-white/40">
        Read-only. An artifact is a captured record attributed to a session and run. Rendering an
        artifact is not verification, and it is not acceptance.
      </p>

      {artifacts.state === "ready" ? (
        rows.length === 0 ? (
          <p className="text-sm text-white/50" data-testid="lab-artifacts-empty">
            No artifacts captured for this identity.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {rows.map((artifact) => {
              const active = selected === artifact.artifact_id;
              return (
                <li key={artifact.artifact_id}>
                  <button
                    type="button"
                    onClick={() => setSelected(active ? null : artifact.artifact_id)}
                    aria-expanded={active}
                    data-testid={`lab-artifact-${artifact.artifact_id}`}
                    className={`w-full rounded border p-3 text-left font-mono text-xs transition ${
                      active
                        ? "border-azure/50 bg-azure/5 text-white/90"
                        : "border-line bg-ink/40 text-white/70"
                    }`}
                  >
                    <span className="text-azure/80">{artifact.kind ?? "artifact"}</span> ·{" "}
                    {artifact.title || "untitled"}
                  </button>
                  {active && <CanvasDetail artifactId={artifact.artifact_id} />}
                </li>
              );
            })}
          </ul>
        )
      ) : (
        <ContractState state={artifacts.state} error={artifacts.error?.message} onRetry={artifacts.reload} />
      )}
    </Panel>
  );
}
