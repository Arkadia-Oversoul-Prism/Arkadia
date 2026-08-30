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

export type SciDomain =
  | 'command'
  | 'projects'
  | 'knowledge'
  | 'weaver'
  | 'governance'
  | 'execution'
  | 'verification'
  | 'system';

export interface SciCommand {
  id: string;
  label: string;
  description: string;
  domain: SciDomain;
  availability: SciAvailability;
  authority: SciAuthorityClass;
  mutation: boolean;
  /** Existing App View target when navigable; null = metadata-only surface */
  routeView: string | null;
  notes?: string;
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

/** Descriptive command registry - no authority. */
export const SCI_COMMANDS: SciCommand[] = [
  {
    id: 'sci.overview',
    label: 'Architecture Overview',
    description: 'System map of Prism, SolSpire, Weaver, and governance boundaries.',
    domain: 'command',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    routeView: null,
  },
  {
    id: 'sci.projects',
    label: 'Projects (SolSpire)',
    description: 'Operational project catalogue and project workbench.',
    domain: 'projects',
    availability: 'AVAILABLE',
    authority: 'AUTH',
    mutation: false,
    routeView: 'solspire',
    notes: 'Routes to existing SolSpireConsole -> ProjectDashboard.',
  },
  {
    id: 'sci.knowledge',
    label: 'Knowledge OS',
    description: 'Knowledge graph and Knowledge OS surfaces.',
    domain: 'knowledge',
    availability: 'AVAILABLE',
    authority: 'AUTH',
    mutation: false,
    routeView: 'knowledge-os',
    notes: 'Compatibility entry -> SolSpire Knowledge section.',
  },
  {
    id: 'sci.weaver',
    label: 'Weaver Workbench',
    description: 'Governed analysis -> plan -> patch -> PassSpec -> PatchApproval -> K15 -> K3 lifecycle.',
    domain: 'weaver',
    availability: 'AVAILABLE',
    authority: 'MUTATION',
    mutation: true,
    routeView: 'solspire',
    notes:
      'WeaverPanel lives inside ProjectDashboard. Mutation only via K15->K3. SCI does not call K3.',
  },
  {
    id: 'sci.governance',
    label: 'Governance Boundary',
    description: 'PassSpec and PatchApproval are backend-authoritative. SCI displays status only.',
    domain: 'governance',
    availability: 'LIMITED',
    authority: 'READ_ONLY',
    mutation: false,
    routeView: null,
    notes: 'No PassSpec or PatchApproval authority is created in SCI.',
  },
  {
    id: 'sci.execution',
    label: 'Execution (K15)',
    description: 'K15 execute_patch is the only Weaver mutation entry. SCI does not invoke K3.',
    domain: 'execution',
    availability: 'LIMITED',
    authority: 'MUTATION',
    mutation: true,
    routeView: null,
    notes: 'Execution remains backend-authorized. SCI discovery only.',
  },
  {
    id: 'sci.verification',
    label: 'Verification',
    description: 'Post-execution verification state as reported by backend.',
    domain: 'verification',
    availability: 'LIMITED',
    authority: 'READ_ONLY',
    mutation: false,
    routeView: null,
  },
  {
    id: 'sci.system',
    label: 'System',
    description: 'Frontend topology, SCI invariant, autonomy policy.',
    domain: 'system',
    availability: 'AVAILABLE',
    authority: 'READ_ONLY',
    mutation: false,
    routeView: null,
  },
  {
    id: 'sci.autonomy',
    label: 'Autonomy',
    description: 'Autonomous mutation / commit / push is not authorized.',
    domain: 'system',
    availability: 'DISABLED',
    authority: 'READ_ONLY',
    mutation: false,
    routeView: null,
    notes: 'PROPOSAL_ONLY / DISABLED. No autonomous execution path.',
  },
];

export function commandsForDomain(domain: SciDomain): SciCommand[] {
  return SCI_COMMANDS.filter((c) => c.domain === domain);
}
