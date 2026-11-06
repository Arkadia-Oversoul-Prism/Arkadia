/**
 * Surface chrome — how a surface contributes to the one canonical shell.
 *
 * Before this module there were three shells: the global `Shell`, plus
 * `WorkspaceShell` and `ArkanaShell` mounted *inside* it. Each owned its own
 * rail, its own header and its own composer dock, so the product rendered two
 * navigation columns and two headers at once. That is the structural reason the
 * console read as several applications sharing a repository rather than one
 * product.
 *
 * The fix is not to delete the inner layouts — they hold real, working regions —
 * but to move *ownership* of the chrome to the one shell:
 *
 *   - `Shell` owns the primary navigation, the header, the identity block and
 *     the mobile drawer. There is exactly one of each.
 *   - A surface may contribute a **context rail** (orientation for the work in
 *     front of you: projects, capabilities, conversations) and a **status line**
 *     (what the surface is doing right now). The shell renders both.
 *
 * A surface therefore never renders a second rail or a second header; it
 * *publishes* what the shell should show. This is a context, not a store: it
 * owns no persistence and no authority, and it is cleared when the surface
 * unmounts so a stale rail can never outlive the surface that contributed it.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface SurfaceChrome {
  /** Orientation content for the secondary rail, or null for none. */
  rail: ReactNode | null;
  /** Accessible name for the rail region. */
  railLabel: string;
  /** A short live status line for the header, or null. */
  status: string | null;
}

const EMPTY: SurfaceChrome = { rail: null, railLabel: "Context", status: null };

interface SurfaceChromeContextValue {
  chrome: SurfaceChrome;
  publish: (next: SurfaceChrome) => void;
  clear: () => void;
}

const SurfaceChromeContext = createContext<SurfaceChromeContextValue | null>(null);

export function SurfaceChromeProvider({ children }: { children: ReactNode }) {
  const [chrome, setChrome] = useState<SurfaceChrome>(EMPTY);

  const publish = useCallback((next: SurfaceChrome) => setChrome(next), []);
  const clear = useCallback(() => setChrome(EMPTY), []);

  const value = useMemo(() => ({ chrome, publish, clear }), [chrome, publish, clear]);

  return <SurfaceChromeContext.Provider value={value}>{children}</SurfaceChromeContext.Provider>;
}

/**
 * Publish this surface's chrome to the shell.
 *
 * Called from a surface component. The effect re-publishes whenever the
 * contributed content changes, and clears on unmount so navigating away cannot
 * leave the previous surface's rail behind.
 */
export function useSurfaceChrome(chrome: SurfaceChrome) {
  const context = useContext(SurfaceChromeContext);
  const { rail, railLabel, status } = chrome;

  useEffect(() => {
    if (!context) return;
    context.publish({ rail, railLabel, status });
    return () => context.clear();
  }, [context, rail, railLabel, status]);
}

/** Read the currently published chrome. Used by the shell. */
export function usePublishedChrome(): SurfaceChrome {
  const context = useContext(SurfaceChromeContext);
  return context?.chrome ?? EMPTY;
}
