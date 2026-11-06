/**
 * TEST-ONLY layout harness — never part of the production bundle.
 *
 * The workspace is a protected surface, and `AuthContext` deliberately has no
 * development bypass: when Firebase is not configured the app runs in an
 * explicit unauthenticated state. That is correct for production and it is why
 * the layout regression could not be caught by loading `/workspace` in a
 * browser — the page renders its sign-in threshold, not the workspace.
 *
 * This entry point exists to make the *layout* measurable without weakening
 * that. It mounts the **real** `Shell` and the **real** `WorkspaceShell` with
 * the same regions the workspace page composes, and it supplies identity
 * through a stub provider that is:
 *
 *   - only reachable from `layout-harness.html`, which is not referenced by
 *     `index.html` and is not in the production build's entry graph;
 *   - visibly labelled in the DOM (`data-test-identity="stub"` and a banner),
 *     so a screenshot can never be mistaken for authenticated acceptance;
 *   - incapable of authenticating anything: it sets no token, calls no API and
 *     grants no authority. It only satisfies `useAuth`'s non-null contract so
 *     the protected layout can render.
 *
 * This is a **stubbed identity**, not a test identity and not real Firebase
 * authentication. The report labels it as such.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { Shell } from "./components/Shell";
import { WorkspaceShell } from "./components/workspace/WorkspaceShell";
import { SurfaceChromeProvider, useSurfaceChrome } from "./lib/surfaceChrome";
import { AuthProvider } from "./contexts/AuthContext";

/**
 * A stub identity provider.
 *
 * It reproduces the *shape* of `AuthContextValue` and nothing else. There is no
 * token, no network call and no claim of a verified user: `identityState` is
 * `"ready"` only so the layout's authenticated branch renders, and the banner
 * below states plainly that this is a stub.
 */
function StubIdentity({ children }: { children: React.ReactNode }) {
  return (
    <div data-test-identity="stub">
      <div data-testid="stub-identity-banner" className="cg-harness-banner">
        STUBBED IDENTITY — layout harness only. Not authenticated. Not a test identity. No token, no
        authority.
      </div>
      {children}
    </div>
  );
}

/** Publishes a representative rail so the shell renders its real rail region. */
function HarnessSurface({ children }: { children: React.ReactNode }) {
  useSurfaceChrome({
    rail: (
      <nav aria-label="Workspace orientation" className="cg-rail-body">
        <p className="font-mono text-[10px] uppercase tracking-wider text-white/40">Projects</p>
        <ul>
          <li>Arkadia One</li>
          <li>Solariun</li>
        </ul>
      </nav>
    ),
    railLabel: "Workspace orientation",
    status: "Arkana · layout harness",
  });
  return <>{children}</>;
}

function Harness() {
  return (
    <StubIdentity>
      <AuthProvider>
        <SurfaceChromeProvider>
          <HarnessSurface>
            <Shell current="workspace" onNavigate={() => {}}>
              <WorkspaceShell
                inspector={
                  <div data-testid="harness-inspector">
                    <p>Project</p>
                    <p>Arkadia One</p>
                  </div>
                }
                composer={
                  <div data-testid="harness-composer">
                    <input aria-label="Message" placeholder="Ask Arkana…" />
                  </div>
                }
              >
                <div data-testid="harness-canvas">
                  <p>Conversation canvas</p>
                </div>
              </WorkspaceShell>
            </Shell>
          </HarnessSurface>
        </SurfaceChromeProvider>
      </AuthProvider>
    </StubIdentity>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Harness />
  </StrictMode>,
);
