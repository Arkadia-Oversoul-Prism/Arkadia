/**
 * Minimal history-based router.
 *
 * One `View` union, one `resolvePath`, one `routeForView` — the same shape the
 * shell uses for navigation. Every surface path is declared in `surfaces.ts`;
 * this module only maps pathname -> surface id.
 */
import { useCallback, useEffect, useState } from "react";
import { SURFACES, SURFACE_BY_ID, type SurfaceId } from "./surfaces";

export interface Route {
  surface: SurfaceId;
  path: string;
  /** Optional sub-section within a surface (for example a Solariun lens). */
  section?: string;
}

const SECTION_PATTERN = /^\/([^/]+)\/([^/]+)$/;

/**
 * Legacy inbound-link aliases, reconciled to a canonical surface (directive §5.2).
 *
 * `/nexus` was the archived Prism hub's route for the NovaNet view
 * (`routeForView: novanet -> '/nexus'`) and is referenced by archived deep
 * links. It is an *alias*, not a second surface: it resolves to `novanet` and
 * never gets its own entry in `surfaces.ts`.
 */
export const PATH_ALIASES: Record<string, SurfaceId> = {
  "/nexus": "novanet",
};

export function resolvePath(pathname: string): Route {
  const path = pathname.replace(/\/+$/, "") || "/";
  const alias = PATH_ALIASES[path];
  if (alias) return { surface: alias, path: SURFACE_BY_ID[alias].path };
  const match = path.match(SECTION_PATTERN);
  if (match) {
    const surface = SURFACES.find((s) => s.path === `/${match[1]}`);
    if (surface) return { surface: surface.id, section: match[2], path };
  }
  const surface = SURFACES.find((s) => s.path === path);
  if (surface) return { surface: surface.id, path: surface.path };
  return { surface: "home", path: "/" };
}

export function routeForSurface(id: SurfaceId, section?: string): string {
  const base = SURFACE_BY_ID[id].path;
  return section && base !== "/" ? `${base}/${section}` : base;
}

export function useRouter() {
  const [route, setRoute] = useState<Route>(() => resolvePath(window.location.pathname));

  useEffect(() => {
    const onPop = () => setRoute(resolvePath(window.location.pathname));
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((id: SurfaceId, section?: string) => {
    const next = routeForSurface(id, section);
    if (window.location.pathname !== next) window.history.pushState({}, "", next);
    setRoute({ surface: id, section, path: next });
  }, []);

  return { route, navigate };
}
