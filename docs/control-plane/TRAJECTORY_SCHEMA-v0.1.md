# ARKADIA TRAJECTORY SCHEMA

Specification ID: TRAJECTORY-SCHEMA-v0.1
Status: DRAFT FOR REVIEW
Parent: AEAS-v0.1.1
Scope: Constitutional trajectory representation used by the Engineering Lab
Authority Ceiling: Architect-authored trajectory only
Implementation: NOT AUTHORIZED
Runtime Mutation: NONE
Autonomous Trajectory Mutation: PROHIBITED
Human Authorization: REQUIRED FOR ALL TRAJECTORY CHANGE

## 0. PURPOSE

This schema defines the minimum inspectable representation of Arkadia's trajectory under AEAS-v0.1.1.

The trajectory is architectural direction. It is not an execution queue, worker instruction stream, scheduler, or authorization record.

AEAS establishes the governing distinction:

- The architect authors and maintains the trajectory.
- The Lab holds, reads, validates, and operationalizes trajectory into bounded planning artifacts.
- The worker executes authorized tasks within the trajectory.
- The worker may propose trajectory changes but may not apply them.

The trajectory therefore answers **where the system is going** without itself granting permission to execute.

## 1. AUTHORITY AND INVARIANTS

The following are normative:

1. The human architect is the sole constitutional source of trajectory authority.
2. A trajectory record without architect provenance is not canonical.
3. A proposal to change trajectory is not a trajectory change.
4. Trajectory direction does not constitute task authorization.
5. A mission must derive from an applicable trajectory node.
6. A task must derive from an approved mission and separately satisfy AEAS authorization requirements.
7. The Lab may validate consistency and expose conflicts but may not redefine trajectory.
8. The worker may report evidence and propose changes but may not mutate trajectory.
9. Historical trajectory records remain inspectable; changes are additive/versioned rather than silently overwritten.
10. No trajectory field may grant merge, deployment, credential, authority, K15/K3, provenance, or WorkEvent modification capability.
11. Trajectory governance decisions are distinct from AEAS execution authorization. A trajectory decision approves or rejects directional state; an AEAS authorization permits bounded execution.

## 2. TRAJECTORY LAYERS

The canonical trajectory hierarchy is:

```text
ANNUAL
  ↓
BIANNUAL
  ↓
QUARTERLY
  ↓
MONTHLY
  ↓
WEEKLY
  ↓
DAILY
  ↓
SESSION
  ↓
TASK
```

The layers provide progressively narrower direction. They do not create progressively greater execution authority.

| Layer | Purpose | Typical horizon | Authority |
|---|---|---|---|
| Annual | Long-range architectural direction | Year | Architect |
| Biannual | Six-month directional commitment | Six months | Architect |
| Quarterly | Major system objective | Quarter | Architect |
| Monthly | Near-term objective | Month | Architect |
| Weekly | Current operating direction | Week | Architect |
| Daily | Immediate directional focus | Day | Architect |
| Session | Direction for one bounded engineering window | Session | Architect-derived |
| Task | Specific bounded operation | One session | Architect-authorized through AEAS |

A lower layer may refine a higher layer but may not contradict or silently replace it.

## 3. ROOT TRAJECTORY RECORD

```yaml
trajectory:
  id: TRJ-YYYY-NNN
  schema_version: TRAJECTORY-SCHEMA-v0.1
  version: N
  status: draft | active | superseded | archived
  title: <one line>
  direction: <architect-authored statement of where Arkadia is going>
  purpose: <why this direction exists>
  horizon: annual | biannual | quarterly | monthly | weekly | daily | session | task
  parent_id: TRJ-...
  priorities: []
  constraints: []
  non_goals: []
  dependencies: []
  success_conditions: []
  review_conditions: []
  provenance:
    authored_by: architect
    trajectory_decision: TRJDEC-...
    source_revision: <repository ref or canonical source>
    created_at_utc: <iso8601>
    supersedes: TRJ-... | null
```

`direction` is the constitutional core of the record. `priorities`, `constraints`, and `non_goals` make that direction operationally inspectable without turning it into authorization.

`trajectory_decision` is a trajectory-governance decision reference. It is not an AEAS execution authorization record.

## 4. TRAJECTORY NODE

Each layer is represented as a node that can be linked to a parent trajectory node.

```yaml
trajectory_node:
  id: TRJ-<LAYER>-YYYY-NNN
  layer: annual | biannual | quarterly | monthly | weekly | daily | session | task
  parent_id: TRJ-... | null
  title: <one line>
  objective: <what direction is being pursued>
  rationale: <why this objective exists>
  priorities: []
  constraints: []
  non_goals: []
  dependencies: []
  success_conditions: []
  state: proposed | active | superseded | archived
  provenance:
    trajectory_id: TRJ-...
    version: N
    authored_by: architect
    trajectory_decision: TRJDEC-...
    created_at_utc: <iso8601>
```

A node is directional state. It does not contain an executable operation list.

## 5. PRIORITY MODEL

Priorities express ordering of attention, not permission.

```yaml
priority:
  id: PRI-YYYY-NNN
  trajectory_node_id: TRJ-...
  rank: N
  statement: <one line>
  rationale: <why this outranks lower priorities>
  status: active | deferred | closed
```

Priority rank must not be interpreted as authorization priority. AEAS authorization remains a separate control-plane record.

## 6. CONSTRAINT MODEL

Constraints protect trajectory integrity and reduce ambiguity.

```yaml
constraint:
  id: CON-YYYY-NNN
  trajectory_node_id: TRJ-...
  type: architectural | security | scope | resource | timing | dependency
  statement: <constraint>
  enforcement: inspect | block | review
  source: <canonical source or trajectory-governance decision>
```

A constraint marked `block` is a planning boundary. It does not itself execute a block; the applicable governed component enforces it.

## 7. NON-GOAL MODEL

Non-goals explicitly identify work that is outside the current directional envelope.

```yaml
non_goal:
  id: NGT-YYYY-NNN
  trajectory_node_id: TRJ-...
  statement: <what is intentionally not being pursued>
  rationale: <why>
  review_trigger: <condition that would justify reconsideration>
```

Non-goals are especially important where adjacent capabilities could otherwise be mistaken for current trajectory.

## 8. MISSION DERIVATION

Missions translate trajectory direction into bounded engineering intent.

```text
TRAJECTORY NODE
      ↓
MISSION PROPOSAL
      ↓
ARCHITECT APPROVAL
      ↓
APPROVED MISSION
      ↓
AEAS TASK AUTHORIZATION
      ↓
TASK
```

A mission must carry its originating trajectory node:

```yaml
mission:
  id: M-YYYY-QN-NNN
  trajectory_ref: TRJ-...
  title: <one line>
  objective: <what should change>
  rationale: <why this matters>
  canon_alignment: []
  systems_affected: []
  dependencies: []
  acceptance_criteria: []
  constraints: []
  out_of_scope: []
  estimated_sessions: N
  risk: low | medium | high
  approval:
    required_from: architect
    approval_state: draft | approved | in_progress | complete | archived
```

An approved mission remains subordinate to the trajectory. Mission approval does not authorize execution outside the AEAS authorization envelope.

## 9. TASK DERIVATION

Tasks inherit direction but never inherit authority merely through lineage.

```yaml
task:
  id: T-M-YYYY-QN-NNN-XX
  trajectory_ref: TRJ-...
  parent_mission: M-...
  title: <one line>
  objective: <bounded operation>
  repository: <repo>
  base_ref: <branch or sha>
  scope:
    files_allowed: []
    files_forbidden: []
    directories_allowed: []
    directories_forbidden: []
  acceptance:
    tests: []
    lints: []
    builds: []
  checkpoint_required: true
  human_authorization_required: true
```

The complete task authorization envelope remains defined by AEAS-v0.1.1. This schema does not duplicate or replace it.

## 10. SESSION AND CADENCE RELATIONSHIP

The trajectory participates in the AEAS control chain:

```text
TRAJECTORY → CADENCE → SCHEDULE → DISPATCH → SESSION → TASK
```

The distinctions are mandatory:

- Trajectory defines direction.
- Cadence defines the permitted operating rhythm.
- Schedule defines timing.
- Dispatch composes a governed execution assignment.
- Session defines the bounded worker window.
- Task defines the bounded operation.

No lower layer may mutate a higher layer implicitly.

## 11. PROPOSAL MODEL

Trajectory changes may originate as proposals from the Lab, worker, agent, or other evidence-producing surfaces. Proposal origin is not authority.

```yaml
trajectory_proposal:
  id: TPROP-YYYY-NNN
  target_trajectory: TRJ-...
  proposed_change: <specific change>
  rationale: <why evidence suggests change>
  evidence: []
  impact: <systems, missions, or constraints affected>
  originating_actor: lab | worker | agent | architect
  state: proposed | rejected | approved | applied
  review:
    required_from: architect
    decision: pending | approve | reject | revise
    decided_at_utc: <iso8601> | null
    decision_ref: TRJDEC-... | null
  applied_revision: TRJREV-... | null
```

Only an architect decision can move a proposal into an approved trajectory change. Approval of a proposal is not itself the authoritative trajectory state. `applied` is valid only when the architect-approved change has been recorded as a new authoritative trajectory revision and `applied_revision` points to that revision. It does not mean implementation has been executed.

## 12. VERSIONING AND IMMUTABILITY

Trajectory is versioned constitutional state.

A trajectory update creates a new version and records the predecessor. Historical versions remain readable. Every authoritative version must be reconstructible from durable trajectory records without chat history, worker memory, model context, or runtime process state.

```yaml
trajectory_revision:
  id: TRJREV-YYYY-NNN
  trajectory_id: TRJ-...
  from_version: N
  to_version: N+1
  change_summary: <what changed>
  reason: <why>
  trajectory_decision: TRJDEC-...
  evidence: []
  created_at_utc: <iso8601>
```

The resulting revision is the authoritative recorded trajectory state for `to_version`. Silent in-place replacement is prohibited.

## 13. CONFLICT DETECTION

The Lab may report trajectory conflicts when evidence indicates that lower-level planning or execution artifacts diverge from the active trajectory.

A conflict record is observational:

```yaml
trajectory_conflict:
  id: TCON-YYYY-NNN
  trajectory_ref: TRJ-...
  conflicting_artifact: <mission | task | schedule | dispatch | evidence>
  artifact_id: <id>
  conflict_type: scope | priority | constraint | dependency | timing | objective
  evidence: []
  severity: low | medium | high | critical
  state: detected | reviewed | resolved | accepted_risk
  resolution_authority: architect
```

Conflict detection does not grant the Lab authority to rewrite the conflicting artifact.

## 14. RECOVERABILITY

Trajectory state belongs to the Constitutional plane defined by AEAS.

Its authoritative home is the repository/canonical control-plane record. It must remain recoverable without:

- volatile model context
- worker memory
- chat history
- local-only state
- runtime process state

Derived runtime representations may cache trajectory data only if they are rebuildable and non-authoritative.

## 15. INSPECTABILITY REQUIREMENTS

A valid trajectory representation must allow an auditor to answer:

1. What direction is active?
2. Who authored it?
3. Which version is active?
4. Which higher-level node does it descend from?
5. What priorities constrain current work?
6. What is explicitly out of scope?
7. Which missions derive from it?
8. Which proposals seek to change it?
9. Which trajectory-governance decision authorized the current version?
10. What evidence supports a proposed change?
11. Which revision resulted from an approved proposal, where applicable?

If these questions cannot be answered from durable records, the trajectory representation is incomplete.

## 16. FORBIDDEN REDUCTIONS

The following equivalences are invalid:

| Invalid reduction | Correct distinction |
|---|---|
| Trajectory = schedule | Direction ≠ timing |
| Trajectory = authorization | Direction ≠ permission |
| Mission = authorization | Intent ≠ permission |
| Task lineage = execution permission | Derivation ≠ authorization |
| Proposal = trajectory change | Proposal ≠ applied change |
| Worker recommendation = constitutional decision | Evidence ≠ authority |
| Successful execution = trajectory approval | Execution evidence ≠ directional approval |
| Current task = future authorization | Present scope ≠ future scope |
| Trajectory decision = AEAS authorization | Directional governance ≠ execution permission |

## 17. GOVERNANCE BOUNDARY

This schema does not authorize implementation of the worker, router, scheduler, persistence layer, or any other AEAS component.

It defines the data contract for trajectory only.

Any implementation must separately be authorized under AEAS-v0.1.1 and must preserve the following boundaries:

- K15/K3 remain untouched unless separately authorized.
- Provenance semantics remain untouched unless separately authorized.
- WorkEvent semantics remain untouched unless separately authorized.
- Authority and governance cannot be modified by worker, agent, router, or trajectory processing.
- Level 7 bounded autonomy remains RESERVED / NOT ACTIVE.

## 18. ACCEPTANCE CRITERIA

Trajectory Schema v0.1 is structurally acceptable when:

- Every trajectory record has explicit architect provenance.
- Every lower-layer node references its parent where applicable.
- Direction is distinguishable from cadence, schedule, dispatch, session, and task.
- Missions reference trajectory without inheriting authorization.
- Tasks reference trajectory and mission without inheriting authorization.
- Proposals remain proposals until architect-approved and recorded.
- An applied proposal points to the authoritative trajectory revision it produced.
- Revisions preserve historical versions and predecessor relationships.
- Every authoritative trajectory version is reconstructible from durable records.
- Conflicts are inspectable and cannot be silently resolved by the Lab.
- The schema contains no field that grants execution authority.
- The schema introduces no persistence implementation, worker implementation, router implementation, scheduler implementation, or runtime mutation.
- The schema remains compatible with AEAS-v0.1.1.

## FINAL DECLARATION

The trajectory carries direction.

It does not carry authority.

The architect authors the direction. The Lab holds and inspects it. The worker advances only through separately authorized bounded work.

Direction remains visible. Authority remains human.

---

Status: DRAFT FOR REVIEW · TRAJECTORY-SCHEMA-v0.1
Parent: AEAS-v0.1.1
Implementation: NOT AUTHORIZED
K15/K3: UNTOUCHED
Provenance: UNTOUCHED
WorkEvent: UNTOUCHED
