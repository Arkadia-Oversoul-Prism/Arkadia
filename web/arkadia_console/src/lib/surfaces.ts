/**
 * The Arkadia product architecture.
 *
 * These are product boundaries over one canonical backend — not separate
 * deployments. A surface appears here only when the contract it consumes is
 * known to exist; a surface with no verified contract renders an explicit
 * "not yet wired" state rather than decorative data.
 */

export type SurfaceId =
  | "workspace"
  | "home"
  | "novanet"
  | "arkana"
  | "solariun"
  | "projects"
  | "engineering-lab"
  | "solspire"
  | "knowledge"
  | "weaver"
  | "settings"
  | "operator"
  | "n-atlas"
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
  /**
   * The name of a second-level path segment this surface accepts — for example a
   * boundary instance id at `/operator/boundary/<id>`. Absent means the surface
   * addresses only `<surface>/<section>`.
   *
   * This is a declaration, not a convention: `lib/router.ts` resolves a nested
   * path only for a surface that sets it, so one surface cannot silently begin
   * accepting a deeper shape it never declared.
   */
  param?: string;
  /**
   * True for a surface that renders as its own document rather than inside the
   * shared shell. Only the external N-ATLaS tester declares it: that surface's
   * contract is "no Arkadia architecture knowledge required", so the product
   * shell around it would contradict the promise it makes.
   */
  standalone?: boolean;
  /**
   * The navigation group this surface is listed under.
   *
   * This is a *reading order* dimension, not a second navigation model: the
   * shell still derives its item list from this one table, and a surface with
   * no group renders in the trailing group rather than disappearing. Grouping
   * exists because thirteen flat destinations is a list, not a map — the four
   * governed capabilities (Arkana, Weaver, Engineering Lab, Solariun) were
   * indistinguishable from Settings in a flat column.
   */
  group?: SurfaceGroupId;
}

/**
 * The navigation groups, in reading order.
 *
 * `workspace` is the entry point; `converse`, `build` and `cognition` are the
 * governed capabilities the product is organised around; `field` and `system`
 * are the surrounding surfaces. The ids are stable because the shell orders by
 * them — a group is a declaration here, never a hardcoded list in a component.
 */
export type SurfaceGroupId = "workspace" | "converse" | "build" | "cognition" | "field" | "system";

export interface SurfaceGroupDef {
  id: SurfaceGroupId;
  label: string;
}

export const SURFACE_GROUPS: SurfaceGroupDef[] = [
  { id: "workspace", label: "Workspace" },
  { id: "converse", label: "Converse" },
  { id: "build", label: "Build" },
  { id: "cognition", label: "Cognition" },
  { id: "field", label: "Field" },
  { id: "system", label: "System" },
];

export const SURFACES: SurfaceDef[] = [
  {
    id: "workspace",
    requiresAuth: true,
    name: "Workspace",
    boundary: "Arkana + Solariun",
    summary:
      "The conversational workspace \u2014 one conversation reaching every capability, rendered into a living canvas.",
    // The default destination. It is declared at `/workspace` rather than `/`
    // because `/` is the home surface's own path and a second surface cannot
    // claim it (one canonical path per surface). The router's fallback for an
    // unrouted path is unchanged, so an unknown link still lands on Home.
    path: "/workspace",
    accent: "text-teal",
    group: "workspace",
  },
  {
    id: "home",
    name: "Home",
    boundary: "ARKADIA",
    summary: "Unified shell, identity, and navigation across the product.",
    path: "/",
    accent: "text-gold",
    group: "workspace",
  },
  {
    id: "novanet",
    name: "NovaNet",
    boundary: "NovaNet",
    summary: "Public field and hub — transmissions, echoes, and the shared Nexus surface.",
    // The legacy hub lived on `/nexus` (an alias of `novanet`). The console
    // declares one canonical path per surface (directive §5.1); `/nexus` is
    // reconciled as an alias to this route, never a second surface.
    path: "/novanet",
    accent: "text-azure",
    group: "field",
  },
  {
    id: "arkana",
    name: "Arkana",
    boundary: "Arkana",
    summary: "Conversational intelligence and synthesis over the shared spine.",
    path: "/arkana",
    accent: "text-emerald",
    group: "converse",
  },
  {
    id: "solariun",
    requiresAuth: true,
    name: "Solariun",
    boundary: "Solariun",
    summary: "Personal workspace and cognitive canvas — projects and continuity.",
    path: "/solariun",
    accent: "text-violet",
    group: "cognition",
  },
  {
    id: "projects",
    requiresAuth: true,
    name: "Projects",
    boundary: "ARKADIA",
    summary: "Discovery and navigation across projects, files, tasks, and activity.",
    path: "/projects",
    accent: "text-emerald",
    group: "build",
  },
  {
    id: "engineering-lab",
    requiresAuth: true,
    name: "Engineering Lab",
    boundary: "Knowledge OS + Engineering Lab",
    summary: "Technical operations, task state, provider status, and evidence.",
    path: "/engineering-lab",
    accent: "text-azure",
    group: "build",
  },
  {
    id: "solspire",
    requiresAuth: true,
    name: "SolSpire",
    boundary: "SolSpire",
    summary: "Team and enterprise workspace over the shared substrate.",
    // `/solspire` is a reserved backend API namespace (the SolSpire console
    // kernel mounts there), so the SPA cannot be served on that path -- a hard
    // load would fall through to the API and 404. The surface lives on a
    // non-colliding route; the API contract still speaks `/solspire/*`.
    path: "/enterprise",
    accent: "text-gold",
    group: "field",
  },
  {
    id: "knowledge",
    requiresAuth: true,
    name: "Knowledge OS",
    boundary: "Knowledge OS + Engineering Lab",
    summary: "Continuity, memory, and the knowledge graph.",
    path: "/knowledge",
    accent: "text-emerald",
    group: "cognition",
  },
  {
    id: "weaver",
    requiresAuth: true,
    name: "Weaver",
    boundary: "Weaver",
    summary: "Governed execution and orchestration. Proposal, approval, execution, verification.",
    path: "/weaver",
    accent: "text-violet",
    group: "build",
  },
  {
    id: "settings",
    requiresAuth: true,
    name: "Settings",
    boundary: "ARKADIA",
    summary: "Identity, preferences, integrations, security, and workspace configuration.",
    path: "/settings",
    accent: "text-gold",
    group: "system",
  },
  {
    id: "operator",
    name: "Operator",
    boundary: "ARKADIA",
    summary: "Reconciled operator console — boundary posture, evidence, and authority.",
    // Reconciled from the retired standalone operator application. It is a
    // section-addressed surface of THIS shell, not a second application; its
    // worked boundary instances are addressed one level deeper.
    path: "/operator",
    accent: "text-gold",
    param: "id",
    group: "system",
  },
  {
    id: "n-atlas",
    name: "N-ATLaS",
    boundary: "Knowledge OS + Engineering Lab",
    summary: "External N-ATLaS developer test — run a prompt, inspect the evidence.",
    // The established direct route the retired operator bundle answered.
    // `/n-atlas-tester` is reconciled to it as an alias, so the inbound links a
    // tester may hold keep resolving to the same view on the same origin.
    path: "/n-atlas-lab",
    accent: "text-azure",
    nav: false,
    standalone: true,
  },
  {
    id: "about",
    name: "About",
    boundary: "ARKADIA",
    summary: "Architecture, lineage, and principles.",
    path: "/about",
    accent: "text-azure",
    group: "system",
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
