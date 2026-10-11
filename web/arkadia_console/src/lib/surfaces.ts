/**
 * The Arkadia product architecture.
 *
 * These are product boundaries over one canonical backend — not separate
 * deployments. A surface appears here only when the contract it consumes is
 * known to exist; a surface with no verified contract renders an explicit
 * "not yet wired" state rather than decorative data.
 */

export type SurfaceId =
  | "home"
  | "arkana"
  | "solariun"
  | "engineering-lab"
  | "solspire"
  | "knowledge"
  | "weaver"
  | "about"
  | "login";

export interface SurfaceDef {
  id: SurfaceId;
  name: string;
  /** The product boundary this surface belongs to. */
  boundary: string;
  summary: string;
  path: string;
  accent: string;
  /** Protected surfaces require an authenticated identity to render their content. */
  requiresAuth?: boolean;
  /** False for surfaces reachable but not shown in global navigation (for example sign-in). */
  nav?: boolean;
}

export const SURFACES: SurfaceDef[] = [
  {
    id: "home",
    name: "Home",
    boundary: "ARKADIA",
    summary: "Unified shell, identity, and navigation across the product.",
    path: "/",
    accent: "text-gold",
  },
  {
    id: "arkana",
    name: "Arkana",
    boundary: "Arkana",
    summary: "Conversational intelligence and synthesis over the shared spine.",
    path: "/arkana",
    accent: "text-emerald",
  },
  {
    id: "solariun",
    requiresAuth: true,
    name: "Solariun",
    boundary: "Solariun",
    summary: "Personal workspace and cognitive canvas — projects and continuity.",
    path: "/solariun",
    accent: "text-violet",
  },
  {
    id: "engineering-lab",
    requiresAuth: true,
    name: "Engineering Lab",
    boundary: "Knowledge OS + Engineering Lab",
    summary: "Technical operations, task state, provider status, and evidence.",
    path: "/engineering-lab",
    accent: "text-azure",
  },
  {
    id: "solspire",
    requiresAuth: true,
    name: "SolSpire",
    boundary: "SolSpire",
    summary: "Team and enterprise workspace over the shared substrate.",
    path: "/solspire",
    accent: "text-gold",
  },
  {
    id: "knowledge",
    requiresAuth: true,
    name: "Knowledge OS",
    boundary: "Knowledge OS + Engineering Lab",
    summary: "Continuity, memory, and the knowledge graph.",
    path: "/knowledge",
    accent: "text-emerald",
  },
  {
    id: "weaver",
    requiresAuth: true,
    name: "Weaver",
    boundary: "Weaver",
    summary: "Governed execution and orchestration. Proposal, approval, execution, verification.",
    path: "/weaver",
    accent: "text-violet",
  },
  {
    id: "about",
    name: "About",
    boundary: "ARKADIA",
    summary: "Architecture, lineage, and principles.",
    path: "/about",
    accent: "text-azure",
  },
  {
    id: "login",
    name: "Sign in",
    boundary: "ARKADIA",
    summary: "Authenticate against the canonical Arkadia backend.",
    path: "/login",
    accent: "text-gold",
    nav: false,
  },
];

export const SURFACE_BY_ID: Record<SurfaceId, SurfaceDef> = Object.fromEntries(
  SURFACES.map((s) => [s.id, s]),
) as Record<SurfaceId, SurfaceDef>;
