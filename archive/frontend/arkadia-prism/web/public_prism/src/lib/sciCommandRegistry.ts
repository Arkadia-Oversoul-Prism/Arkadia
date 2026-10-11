/**
 * SCI Command / Capability Registry
 *
 * Descriptive UI metadata only.
 * Does NOT grant authorization, mutation rights, or execution authority.
 * Backend governance (PassSpec, PatchApproval, K15, K3) remains authoritative.
 *
 * SURFACE OWNERSHIP (WEAVER-SCI-BOUNDARY-01)
 * -----------------------------------------
 * SCI          owns: global operator navigation, discovery, capability metadata,
 *                    domain selection, topology presentation. NOT authorization.
 * SolSpire     owns: project/workspace operating context (via routeView solspire).
 * Knowledge    owns: knowledge surfaces (via routeView knowledge-os / SolSpire).
 * Weaver       owns: engineering workflow inside project context (WeaverPanel).
 * Governance   owns: PassSpec / PatchApproval visibility (backend-authoritative).
 * Execution    owns: K15 readiness display only - mutation path remains K15->K3.
 * Verification owns: post-execution result visibility (backend-authoritative).
 * System       owns: architecture health / registry presentation (descriptive).
 *
 * SCI REGISTRY != AUTHORIZATION
 * SCI_DISCOVERY_WITHOUT_AUTHORITY
 */

/**
 * WEAVER-SCI-CONTRACT-01 - frozen surface ownership contract.
 * Discovery is not ownership. Ownership is not authorization.
 * SCI_REGISTRY_IS_DESCRIPTIVE_NOT_AUTHORIZING
 */

/** Canonical surface owners. Descriptive classification only. */
export type SurfaceOwner =
  | 'product'
  | 'sci'
  | 'solspire'
  | 'weaver'
  | 'knowledge'
  | 'governance'
  | 'system';

/**
 * Frozen contract: who owns what.
 * Values are documentation for operators and tests - not runtime authority.
 */
export const SURFACE_CONTRACT = {
  sci: {
    owner: 'sci' as SurfaceOwner,
    role: 'global operator command and discovery',
    may: ['discover', 'orient', 'navigate', 'observe'],
    mustNot: [
      'authorize',
      'mutate',
      'createPassSpec',
      'createPatchApproval',
      'callK15',
      'callK3',
      'commit',
      'push',
      'ownProjectState',
    ],
  },
  solspire: {
    owner: 'solspire' as SurfaceOwner,
    role: 'project workspace operating surface',
    may: ['projectSelection', 'projectState', 'projectKnowledgeEntry', 'projectWeaverHost'],
    mustNot: ['globalCommandShell', 'globalCapabilityRegistry', 'secondSci', 'secondAuthAuthority'],
  },
  weaver: {
    owner: 'weaver' as SurfaceOwner,
    role: 'project-scoped engineering workflow',
    path: 'SCI -> SolSpire -> Project -> Weaver',
    mutationGate: 'K15',
    transactionBoundary: 'K3',
    mustNot: ['globalProductNavigation', 'duplicateInsideSci'],
  },
  knowledge: {
    owner: 'knowledge' as SurfaceOwner,
    role: 'knowledge and context surface',
    mustNot: ['authorization', 'execution'],
  },
  governance: {
    owner: 'governance' as SurfaceOwner,
    role: 'authorization boundary (backend-authoritative)',
    chain: ['PassSpec', 'PatchApproval', 'K15', 'K3'],
  },
  product: {
    owner: 'product' as SurfaceOwner,
    role: 'public product experience',
    examples: ['NovaNet', 'ReasoMate', 'Offerings', 'LivingGate'],
    mustNot: ['operatorCommandRail', 'mergeWithSci'],
  },
} as const;

/** Explicit invariant: registry metadata never grants authority. */
export const SCI_REGISTRY_IS_DESCRIPTIVE_NOT_AUTHORIZING = true as const;

/**
 * WEAVER-SCI-DISCOVERY-01 - capability discovery vocabulary.
 * DISCOVERABLE != AVAILABLE != AUTHORIZED != EXECUTED != VERIFIED
 */
export type SciAvailability =
  | 'AVAILABLE'
  | 'LIMITED'
  | 'NOT_AVAILABLE'
  | 'NOT_IMPLEMENTED'
  | 'PROPOSAL_ONLY'
  | 'DISABLED';

export type SciAuthorityClass =
  | 'READ_ONLY'
  | 'OWNER'
  | 'AUTH'
  | 'MUTATION'
  | 'DERIVED'
  | 'CONTEXT';

/** Operator-facing mutation class for discovery UI. */
export type SciMutationClass =
  | 'READ_ONLY'
  | 'PROPOSAL_ONLY'
  | 'GOVERNED_MUTATION'
  | 'DISABLED';

export type SciDomain =
  | 'command'
  | 'projects'
  | 'knowledge'
  | 'weaver'
  | 'governance'
  | 'execution'
  | 'verification'
  | 'system';

/** Existing App View targets that SCI may navigate to (do not invent). */
export const KNOWN_ROUTE_VIEWS = [
  'solspire',
  'knowledge-os',
  'novanet',
  'sci',
] as const;

export type KnownRouteView = (typeof KNOWN_ROUTE_VIEWS)[number];

export interface SciCommand {
  id: string;
  label: string;
  description: string;
  domain: SciDomain;
  /** Surface that owns the capability (not SCI merely for listing it). */
  owner: SurfaceOwner;
  availability: SciAvailability;
  authority: SciAuthorityClass;
  mutation: boolean;
  mutationClass: SciMutationClass;
  /** Existing App View target when navigable; null = no bound operator surface. */
  routeView: string | null;
  notes?: string;
  limitations?: string;
}

/** Canonical SCI rail categories (discovery order). */
export const SCI_CATEGORIES: { id: SciDomain; label: string; sigil: string }[] = [
  { id: 'command', label: 'Overview', sigil: 'C' },
  { id: 'projects', label: 'Projects', sigil: 'P' },
  { id: 'knowledge', label: 'Knowledge', sigil: 'K' },
  { id: 'weaver', label: 'Weaver', sigil: 'W' },
  { id: 'governance', label: 'Governance', sigil: 'G' },
  { id: 'execution', label: 'Execution', sigil: 'E' },
  { id: 'verification', label: 'Verification', sigil: 'V' },
  { id: 'system', label: 'System', sigil: 'S' },
];

/** Lifecycle stages for Weaver (display only). Do not invent new ones. */
export const WEAVER_LIFECYCLE = [
  'PROJECT',
  'KNOWLEDGE',
  'OBJECTIVE',
  'SCOPE',
  'EVIDENCE',
  'ANALYSIS',
  'PLAN',
  'CHANGESET',
  'PATCH',
  'REVIEW',
  'PASSSPEC',
  'PATCH APPROVAL',
  'K15',
  'K3',
  'VERIFICATION',
] as const;

export const WEAVER_STATE_LABELS = [
  'PROPOSED',
  'REVIEWED',
  'APPROVED',
  'READY',
  'EXECUTED',
  'VERIFIED',
  'LOCKED',
  'NOT_RUN',
  'NOT_AVAILABLE',
] as const;

/**
 * Canonical descriptive capability registry for SCI discovery.
 * Presence here means DISCOVERABLE only - never AUTHORIZED or EXECUTED.
 */
export const SCI_COMMANDS: SciCommand[] = [
  {
    id: 'sci.overview',
    label: 'Architecture Overview',
    description: 'System map of Prism, SolSpire, Weaver, and governance boundaries.',
    domain: 'command',
    owner: 'sci',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: null,
    notes: 'Metadata-only orientation surface inside SCI.',
  },
  {
    id: 'sci.projects',
    label: 'Projects (SolSpire)',
    description: 'Operational project catalogue and project workbench.',
    domain: 'projects',
    owner: 'solspire',
    availability: 'AVAILABLE',
    authority: 'AUTH',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: 'solspire',
    notes: 'Routes to existing SolSpireConsole -> ProjectDashboard.',
  },
  {
    id: 'sci.knowledge',
    label: 'Knowledge OS',
    description: 'Knowledge graph and Knowledge OS surfaces. Context only - not authorization.',
    domain: 'knowledge',
    owner: 'knowledge',
    availability: 'AVAILABLE',
    authority: 'CONTEXT',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: 'knowledge-os',
    notes: 'Knowledge != Authorization. Compatibility entry -> SolSpire Knowledge section.',
  },
  {
    id: 'sci.knowledge.embeddings',
    label: 'Embeddings',
    description: 'Vector embedding pipeline for knowledge retrieval.',
    domain: 'knowledge',
    owner: 'knowledge',
    availability: 'NOT_AVAILABLE',
    authority: 'CONTEXT',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: null,
    limitations: 'Embeddings remain NOT_AVAILABLE. Do not infer readiness from discovery.',
  },
  {
    id: 'sci.weaver',
    label: 'Weaver Workbench',
    description: 'Governed analysis -> plan -> patch -> PassSpec -> PatchApproval -> K15 -> K3 lifecycle.',
    domain: 'weaver',
    owner: 'weaver',
    availability: 'AVAILABLE',
    authority: 'MUTATION',
    mutation: true,
    mutationClass: 'GOVERNED_MUTATION',
    routeView: 'solspire',
    notes:
      'WeaverPanel lives inside ProjectDashboard. Mutation only via K15->K3. SCI does not call K3.',
  },
  {
    id: 'sci.weaver.recon',
    label: 'Repository Reconnaissance',
    description: 'Read-only repository and scope inspection inside Weaver.',
    domain: 'weaver',
    owner: 'weaver',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: 'solspire',
    notes: 'READ_ONLY discovery. Owned by Weaver under project context.',
  },
  {
    id: 'sci.weaver.evidence',
    label: 'Evidence',
    description: 'Evidence collection and inspection for Weaver analysis.',
    domain: 'weaver',
    owner: 'weaver',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: 'solspire',
  },
  {
    id: 'sci.weaver.analysis',
    label: 'Analysis',
    description: 'Weaver analysis stage (read-only relative to mutation).',
    domain: 'weaver',
    owner: 'weaver',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: 'solspire',
  },
  {
    id: 'sci.weaver.plan',
    label: 'Plan',
    description: 'Weaver planning stage. Planning is not authorization.',
    domain: 'weaver',
    owner: 'weaver',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: 'solspire',
  },
  {
    id: 'sci.weaver.changeset',
    label: 'Changeset Inspection',
    description: 'Inspect proposed changesets without executing them.',
    domain: 'weaver',
    owner: 'weaver',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: 'solspire',
  },
  {
    id: 'sci.weaver.patch_review',
    label: 'Patch Review',
    description: 'Review synthesized patches. Review does not approve execution.',
    domain: 'weaver',
    owner: 'weaver',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: 'solspire',
  },
  {
    id: 'sci.governance',
    label: 'Governance Boundary',
    description: 'PassSpec and PatchApproval are backend-authoritative. SCI displays status only.',
    domain: 'governance',
    owner: 'governance',
    availability: 'LIMITED',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: null,
    notes: 'No PassSpec or PatchApproval authority is created in SCI.',
    limitations: 'Display-only. Presence is DISCOVERABLE, not AUTHORIZED.',
  },
  {
    id: 'sci.governance.passspec',
    label: 'PassSpec',
    description: 'Governed mutation prerequisite. Backend-authoritative.',
    domain: 'governance',
    owner: 'governance',
    availability: 'LIMITED',
    authority: 'MUTATION',
    mutation: true,
    mutationClass: 'GOVERNED_MUTATION',
    routeView: null,
    limitations: 'SCI does not construct PassSpec. No operator surface bound in SCI.',
  },
  {
    id: 'sci.governance.patch_approval',
    label: 'PatchApproval',
    description: 'Governed approval prerequisite before K15. Backend-authoritative.',
    domain: 'governance',
    owner: 'governance',
    availability: 'LIMITED',
    authority: 'MUTATION',
    mutation: true,
    mutationClass: 'GOVERNED_MUTATION',
    routeView: null,
    limitations: 'SCI does not construct PatchApproval. No operator surface bound in SCI.',
  },
  {
    id: 'sci.execution',
    label: 'Execution (K15)',
    description: 'K15 execute_patch is the only Weaver mutation entry. SCI does not invoke K3.',
    domain: 'execution',
    owner: 'weaver',
    availability: 'LIMITED',
    authority: 'MUTATION',
    mutation: true,
    mutationClass: 'GOVERNED_MUTATION',
    routeView: null,
    notes: 'Execution remains backend-authorized. SCI discovery only.',
    limitations: 'AVAILABLE/LIMITED in discovery does not mean AUTHORIZED or EXECUTED.',
  },
  {
    id: 'sci.verification',
    label: 'Verification',
    description: 'Post-execution verification state as reported by backend.',
    domain: 'verification',
    owner: 'weaver',
    availability: 'LIMITED',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: null,
    limitations: 'EXECUTED is not VERIFIED. No SCI-bound verification console yet.',
  },
  {
    id: 'sci.system',
    label: 'System',
    description: 'Frontend topology, SCI invariant, autonomy policy.',
    domain: 'system',
    owner: 'system',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'READ_ONLY',
    routeView: null,
  },
  {
    id: 'sci.autonomy',
    label: 'Autonomy',
    description: 'Autonomous mutation / commit / push is not authorized.',
    domain: 'system',
    owner: 'system',
    availability: 'DISABLED',
    authority: 'READ_ONLY',
    mutation: false,
    mutationClass: 'PROPOSAL_ONLY',
    routeView: null,
    notes: 'PROPOSAL_ONLY / DISABLED. No autonomous execution path.',
    limitations: 'Must not be inferred as available execution.',
  },
];

export function commandsForDomain(domain: SciDomain): SciCommand[] {
  return SCI_COMMANDS.filter((c) => c.domain === domain);
}

export function commandsForOwner(owner: SurfaceOwner): SciCommand[] {
  return SCI_COMMANDS.filter((c) => c.owner === owner);
}

/** True when routeView is an existing known surface (not invented). */
export function hasBoundRoute(cmd: SciCommand): boolean {
  return cmd.routeView != null && (KNOWN_ROUTE_VIEWS as readonly string[]).includes(cmd.routeView);
}

export function navigationLabel(cmd: SciCommand): string {
  if (hasBoundRoute(cmd)) return `Open ${cmd.routeView}`;
  return 'No operator surface currently bound';
}

/** Discovery projection: grouped by domain for SCI rail panels. */
export function discoveryByDomain(): Record<SciDomain, SciCommand[]> {
  const out = {} as Record<SciDomain, SciCommand[]>;
  for (const cat of SCI_CATEGORIES) {
    out[cat.id] = commandsForDomain(cat.id);
  }
  return out;
}
