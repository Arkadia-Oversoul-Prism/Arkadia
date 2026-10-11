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
  | "about";

export interface SurfaceDef {
  id: SurfaceId;
  name: string;
  /** The product boundary this surface belongs to. */
  boundary: string;
  summary: string;
  path: string;
  accent: string;
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
    name: "Solariun",
    boundary: "Solariun",
    summary: "Personal workspace and cognitive canvas — projects and continuity.",
    path: "/solariun",
    accent: "text-violet",
  },
  {
    id: "engineering-lab",
    name: "Engineering Lab",
    boundary: "Knowledge OS + Engineering Lab",
    summary: "Technical operations, task state, provider status, and evidence.",
    path: "/engineering-lab",
    accent: "text-azure",
  },
  {
    id: "solspire",
    name: "SolSpire",
    boundary: "SolSpire",
    summary: "Team and enterprise workspace over the shared substrate.",
    path: "/solspire",
    accent: "text-gold",
  },
  {
    id: "knowledge",
    name: "Knowledge OS",
    boundary: "Knowledge OS + Engineering Lab",
    summary: "Continuity, memory, and the knowledge graph.",
    path: "/knowledge",
    accent: "text-emerald",
  },
  {
    id: "weaver",
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
];

export const SURFACE_BY_ID: Record<SurfaceId, SurfaceDef> = Object.fromEntries(
  SURFACES.map((s) => [s.id, s]),
) as Record<SurfaceId, SurfaceDef>;
