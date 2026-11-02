/**
 * Operator surface paths — one source.
 *
 * The migrated operator views used `react-router-dom` `Link`, which resolves
 * against its own `BrowserRouter` basename. There is now exactly one routing
 * authority (`lib/router.ts` over `lib/surfaces.ts`), so a link is expressed as
 * the declared surface path plus a section, and the component navigates through
 * the shared router instead of a second history.
 *
 * These helpers read `SURFACE_BY_ID.operator.path` rather than repeating
 * `/operator`, so moving the surface is a one-line change in the registry and
 * every operator href follows.
 */
import { SURFACE_BY_ID } from "../lib/surfaces";

const BASE = SURFACE_BY_ID.operator.path;

/** A section of the operator surface, e.g. `/operator/inspector`. */
export function operatorSectionPath(section: string): string {
  return `${BASE}/${section}`;
}

/** A boundary instance, e.g. `/operator/boundary/approval-not-execution`. */
export function operatorBoundaryPath(id: string): string {
  return `${BASE}/boundary/${id}`;
}
