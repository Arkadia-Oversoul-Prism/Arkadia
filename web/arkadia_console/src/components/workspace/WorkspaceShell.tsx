/**
 * The conversational workspace layout — canvas, panels, composer, inspector.
 *
 * This used to be a *shell*: it rendered its own left rail, its own header and
 * its own composer dock, nested inside the global `Shell`. Two navigation
 * columns and two headers rendered at once, which is the structural reason the
 * console read as several applications sharing a repository.
 *
 * It is now a **layout only**, and it owns no navigation:
 *
 *   - the primary navigation, the header and the identity block belong to the
 *     one canonical `Shell`;
 *   - the orientation rail (projects, capabilities, conversations) is
 *     *published* to that shell by `WorkspacePage` through `useSurfaceChrome`,
 *     so there is exactly one rail in the product;
 *   - what remains here is the working surface: the conversation canvas, the
 *     expandable execution/inspection panels, the composer dock, and the
 *     contextual inspector.
 *
 * The inspector is not navigation — it is live state about the work in front of
 * you (project, task, authorization, evidence) — so it stays a region of the
 * workspace. On narrow viewports it becomes a sheet rather than a compressed
 * desktop column.
 *
 * Layout only. This component owns no intelligence, no persistence and no
 * authorization.
 */
import { useEffect, useId, useState, type ReactNode } from "react";
import "./workspace.css";

/**
 * Track a media query.
 *
 * The inspector has exactly one home: the inline region on wide viewports, the
 * sheet on narrow ones. Rendering both at once would put two copies of the same
 * content in the DOM — duplicate ids, duplicate test ids, and a screen reader
 * reading the state twice. This hook lets the layout mount it in one place only.
 */
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window === "undefined" ? false : window.matchMedia(query).matches,
  );
  useEffect(() => {
    const list = window.matchMedia(query);
    const onChange = () => setMatches(list.matches);
    onChange();
    list.addEventListener("change", onChange);
    return () => list.removeEventListener("change", onChange);
  }, [query]);
  return matches;
}

export function WorkspaceShell({
  inspector,
  children,
  composer,
  panels,
}: {
  inspector: ReactNode;
  children: ReactNode;
  composer: ReactNode;
  /**
   * The expandable execution/inspection panels, rendered between the canvas and
   * the composer dock.
   *
   * These are the *same* live components the standalone Weaver and Engineering
   * Lab surfaces mount (the approval ledger, the Lab repository context, the
   * session list). They are not re-implemented here: the workspace composes the
   * existing components so a user can inspect orchestration and engineering
   * evidence without leaving the conversation. Each panel keeps its own reads
   * and its own honest unavailable state.
   */
  panels?: ReactNode;
}) {
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const titleId = useId();
  // The inspector is inline at >=1280px and a sheet below it; it is mounted in
  // exactly one place.
  const inspectorInline = useMediaQuery("(min-width: 1280px)");

  useEffect(() => {
    if (!inspectorOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setInspectorOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [inspectorOpen]);

  return (
    <div className="cg-workspace" data-testid="workspace-shell">
      <div className="cg-canvas">
        {/*
          No header here. The one shell owns the header — it already shows the
          surface name, its boundary and the surface's published status line.
          A second header inside the canvas was the duplicate this change
          removes.
        */}
        <div className="cg-canvas-stage">{children}</div>

        {panels ? (
          <div className="cg-panels" data-testid="workspace-panels">
            {panels}
          </div>
        ) : null}

        <div className="cg-composer-dock">
          <div className="cg-composer-inner">{composer}</div>
        </div>
      </div>

      {inspectorInline ? (
        <aside className="cg-inspector" aria-label="Context and live state">
          {inspector}
        </aside>
      ) : (
        <button
          type="button"
          className="cg-sheet-btn cg-inspector-trigger"
          aria-expanded={inspectorOpen}
          aria-controls="cg-inspector-sheet"
          data-testid="workspace-open-inspector"
          onClick={() => setInspectorOpen(true)}
        >
          Context
        </button>
      )}

      {!inspectorInline && inspectorOpen ? (
        <div className="cg-sheet" id="cg-inspector-sheet" role="dialog" aria-modal="true" aria-labelledby={`${titleId}-i`}>
          <button
            type="button"
            className="cg-sheet-backdrop"
            aria-label="Close context"
            data-testid="workspace-close-inspector-backdrop"
            onClick={() => setInspectorOpen(false)}
          />
          <div className="cg-sheet-panel cg-sheet-panel-right">
            <div className="cg-sheet-head">
              <p id={`${titleId}-i`} className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/45">
                Context
              </p>
              <button
                type="button"
                className="cg-sheet-btn"
                data-testid="workspace-close-inspector"
                onClick={() => setInspectorOpen(false)}
              >
                Close
              </button>
            </div>
            <div className="cg-sheet-body">{inspector}</div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
