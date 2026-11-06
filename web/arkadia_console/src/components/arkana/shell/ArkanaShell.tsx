/**
 * Arkana conversation layout — A1.
 *
 * This used to be a *shell*: it rendered its own sidebar, its own topbar and its
 * own composer dock, nested inside the global `Shell`. That produced a second
 * navigation column and a second header on the Arkana surface — the same
 * duplication `WorkspaceShell` had.
 *
 * It is now a **layout only**:
 *
 *   - the primary navigation, the header and the identity block belong to the
 *     one canonical `Shell`;
 *   - the conversation-history rail is *published* to that shell by
 *     `ArkanaPage` through `useSurfaceChrome`, so there is exactly one rail;
 *   - what remains here is the conversation canvas and the composer dock.
 *
 * Layout only. Does not own intelligence, persistence, or authorization.
 */
import { type ReactNode } from "react";
import "../design/arkana.css";

export function ArkanaShell({
  children,
  composer,
}: {
  children: ReactNode;
  composer: ReactNode;
}) {
  return (
    <div className="arkana-shell" data-testid="arkana-shell">
      <div className="arkana-main">
        {/*
          No topbar here. The one shell owns the header — it already shows the
          surface name, its boundary and the surface's published status line.
        */}
        <div className="arkana-stage">{children}</div>

        <div className="arkana-composer-dock">
          <div className="arkana-composer-inner">{composer}</div>
        </div>
      </div>
    </div>
  );
}
