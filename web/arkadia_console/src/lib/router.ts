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
 *
 * `/oracle` and `/commune` are the same case for the Oracle view. The archived
 * Prism declared `commune: '/oracle'` and accepted both `/oracle` and `/commune`
 * as direct routes, and its home surface sent the Oracle portal to `commune`.
 * The console names that surface `arkana`, so both inbound paths reconcile to it
 * — without an alias they fell through `resolvePath` to `home`, silently
 * discarding the link. Neither path collides with a declared surface path or a
 * backend route (verified against `app.openapi()`), so no surface may claim them.
 *
 * `/home` and `/knowledge-os` were both entry points in the archived Prism's
 * `direct`/`compatibility` maps and both name a surface the console **declares**.
 * `/home` was an alternate spelling of the home route (`/`), and `/knowledge-os`
 * names the console's own `knowledge` surface literally ("Knowledge OS"). The
 * console rejects `/knowledge-os` as a section of anything (`SECTION_PATTERN`
 * needs two segments) and finds no surface at that path, so without the alias it
 * fell through `resolvePath` to `home` — a real archived deep link silently
 * landed on Home instead of the Knowledge OS. Neither path collides with a
 * declared surface path or a backend route (verified against `app.openapi()`).
 *
 * Deliberately **not** aliased (product decisions, not routing ones — §3/§4
 * forbid inventing a destination for an absent surface):
 *   - `/codex` — the archive routed it to `solariun`'s `knowledge` *lens*, but
 *     the console now has both a `solariun` `knowledge` lens **and** a distinct
 *     `knowledge` surface, so choosing between them is a capability decision this
 *     alias table cannot make.
 *   - `/gate` + `/living-gate` — the archived `gate` view has no console surface.
 *   - `/dashboard`/`/loops`/`/settings`/`/account`/`/personal-echofeild`/
 *     `/echofeild-matrix` — each addressed a Solariun lens (`overview`/`tasks`/
 *     `settings`/`observatory`) the console does not declare.
 */
export const PATH_ALIASES: Record<string, SurfaceId> = {
  "/nexus": "novanet",
  "/oracle": "arkana",
  "/commune": "arkana",
  "/home": "home",
  "/knowledge-os": "knowledge",
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

  // An inbound legacy alias (`/nexus`), a trailing slash, or an unrouted path
  // renders the correct surface but leaves the address bar disagreeing with it,
  // so a copied or shared link keeps propagating a path the console does not
  // declare. The archived Prism normalised once on load
  // (`App.tsx:102 history.replaceState`); the console owns that here, in the one
  // module that resolves a pathname. `replaceState` rather than `pushState`: the
  // inbound path is not a navigation the user can go back to.
  useEffect(() => {
    const canonical = resolvePath(window.location.pathname).path;
    if (window.location.pathname !== canonical) {
      window.history.replaceState({}, "", canonical);
    }
  }, []);

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
