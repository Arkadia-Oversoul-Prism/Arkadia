/**
 * The conversational workspace shell — three persistent regions.
 *
 *   (A) left rail   — orientation only: home, new conversation, recent work,
 *                     projects, search, identity. It navigates; it does not act.
 *   (B) center      — the working surface: the conversation canvas.
 *   (C) right       — the contextual inspector: project/branch/revision, active
 *                     task and execution state, selected sources, permissions
 *                     and pending approvals, evidence.
 *
 * Layout only. This component owns no intelligence, no persistence and no
 * authorization — the same discipline `ArkanaShell` follows. On mobile the rail
 * and the inspector become navigable sheets rather than compressed desktop
 * panels, so the canvas keeps the full width it needs to be readable.
 */
import { useEffect, useId, useState, type ReactNode } from "react";
import "./workspace.css";

/**
 * Track a media query.
 *
 * The rail and the inspector each have exactly one home: the inline region on
 * wide viewports, the sheet on narrow ones. Rendering both at once would put two
 * copies of the same content in the DOM — duplicate ids, duplicate test ids, and
 * a screen reader reading the navigation twice. This hook lets the shell mount
 * the content in one place only.
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
  rail,
  inspector,
  children,
  composer,
  header,
}: {
  rail: ReactNode;
  inspector: ReactNode;
  children: ReactNode;
  composer: ReactNode;
  header?: ReactNode;
}) {
  const [railOpen, setRailOpen] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const titleId = useId();
  // The rail is inline at >=1024px and a sheet below it; the inspector is inline
  // at >=1280px and a sheet below it. Each is mounted in exactly one place.
  const railInline = useMediaQuery("(min-width: 1024px)");
  const inspectorInline = useMediaQuery("(min-width: 1280px)");

  useEffect(() => {
    if (!railOpen && !inspectorOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setRailOpen(false);
        setInspectorOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [railOpen, inspectorOpen]);

  return (
    <div className="cg-workspace" data-testid="workspace-shell">
      {railInline ? (
        <aside className="cg-rail" aria-label="Workspace orientation">
          {rail}
        </aside>
      ) : null}

      <div className="cg-canvas">
        <header className="cg-canvas-header">
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              className="cg-sheet-btn lg:hidden"
              aria-expanded={railOpen}
              aria-controls="cg-rail-sheet"
              data-testid="workspace-open-rail"
              onClick={() => setRailOpen(true)}
            >
              Menu
            </button>
            <div className="min-w-0">{header}</div>
          </div>
          <button
            type="button"
            className="cg-sheet-btn xl:hidden"
            aria-expanded={inspectorOpen}
            aria-controls="cg-inspector-sheet"
            data-testid="workspace-open-inspector"
            onClick={() => setInspectorOpen(true)}
          >
            Context
          </button>
        </header>

        <div className="cg-canvas-stage">{children}</div>

        <div className="cg-composer-dock">
          <div className="cg-composer-inner">{composer}</div>
        </div>
      </div>

      {inspectorInline ? (
        <aside className="cg-inspector" aria-label="Context and live state">
          {inspector}
        </aside>
      ) : null}

      {!railInline && railOpen ? (
        <div className="cg-sheet" id="cg-rail-sheet" role="dialog" aria-modal="true" aria-labelledby={titleId}>
          <button
            type="button"
            className="cg-sheet-backdrop"
            aria-label="Close menu"
            data-testid="workspace-close-rail-backdrop"
            onClick={() => setRailOpen(false)}
          />
          <div className="cg-sheet-panel cg-sheet-panel-left">
            <div className="cg-sheet-head">
              <p id={titleId} className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/45">
                Workspace
              </p>
              <button
                type="button"
                className="cg-sheet-btn"
                data-testid="workspace-close-rail"
                onClick={() => setRailOpen(false)}
              >
                Close
              </button>
            </div>
            <div className="cg-sheet-body">{rail}</div>
          </div>
        </div>
      ) : null}

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
