# ARKADIA ENGINEERING AUTONOMY SPECIFICATION

Specification ID: AEAS-v0.1.1
Status: FROZEN
Supersedes: AEAS-v0.1
Scope: The governed execution substrate that gives the Engineering Lab hands
Parent: Arkadia Control Plane · Lab Phases 1–10 · CP-10.x vocabulary
Location: docs/control-plane/AEAS-v0.1.1.md
Authority Ceiling: LEVEL 2 (specification only)
Implementation: NOT AUTHORIZED
Runtime Mutation: NONE
Repository Mutation: NONE UNTIL FREEZE AND MERGE
Autonomous Architecture Mutation: PROHIBITED
Autonomous Merge: PROHIBITED
Autonomous Production Release: PROHIBITED
Human Authorization: REQUIRED FOR ALL EXECUTION

# Freeze declaration

AEAS-v0.1.1 is frozen in content. This repository artifact is the canonical frozen specification on the `aeas-v0.1.1-freeze` branch. No implementation is authorized by this freeze.

## 0. PURPOSE

The Engineering Lab has eyes. It can observe, reconstruct, analyse, propose, prepare, and record. It has phases. It has vocabulary. It has a cockpit. It has continuity. It has governance.

It has no governed hands.

Every engineering operation that should have been carried by the Lab has instead been carried by the architect, manually, from a phone, through a terminal. This is not the destination the arc was building toward. It is the bottleneck the arc was meant to remove.

AEAS defines the minimum governed execution substrate that gives the Lab hands without granting it authority.

Precise role of the Lab:

The Lab records, enforces, and orchestrates bounded execution through the worker.

The Lab does not execute. The Lab does not edit files. The Lab does not run tests. The Lab does not open PRs. The Lab does not merge. The Lab does not deploy.

The Lab:

· Holds the trajectory and the missions
· Decomposes missions into tasks
· Records and enforces architect-originated authorization
· Dispatches authorized tasks to the worker
· Observes the worker's output
· Reviews the resulting evidence
· Presents the review to the architect

The worker executes.

The hands have no authority. The trajectory belongs to the architect. The Lab is the architect's governed surface for turning trajectory into evidence.

Canonical phrase (normative):

The Lab has eyes. The worker gives it hands. The hands have no authority.

## 1. SOVEREIGNTY MODEL

Invariant: The human architect is the sole constitutional source of authority for every engineering operation. No machine actor may originate, redefine, or authorize architectural change.

The authorization-provenance chain (normative):

ARCHITECT → AUTHORIZATION RECORD → ENGINEERING LAB → WORKER → EVIDENCE

The Lab does not originate authority. The Lab records, enforces, and dispatches authority that has been originated by the architect. Every task executed by the worker must trace back to an architect-originated authorization record. A task without such a record is not authorized and must not be dispatched.

Authorization is the act of permitting a bounded task or bounded task class. The architect originates it; the Lab records and enforces it. Within the authorized scope, the worker may execute the contained operations without atomic re-approval. Operations outside the envelope require architect authorization.

Example authorization:

```yaml
authorization:
  id: AUTH-YYYY-NNNN
  originated_by: architect
  task: T-M-YYYY-QN-NNN-XX
  files_allowed: [A, B, C]
  operations_allowed: [read, edit, test, commit_branch, open_pr]
  duration_minutes: 60
  acceptance: [tests X, tests Y, build Z]
  merge: prohibited
  production: prohibited
  expires_at: <iso8601>
```

Forbidden reductions include capability→authorization, proposal→execution, successful test→merge, preview→production, prior approval→future approval, authorization→scope redefinition, and Lab dispatch→Lab origination.

The switch belongs to the architect. The worker holds the tool, not the switch.

## 2. TRAJECTORY MODEL

The trajectory is the source of architectural truth. It is authored, maintained, and versioned by the architect. It defines where Arkadia is going. The worker does not define it. The worker advances within it.

Trajectory layers: Annual, Biannual, Quarterly, Monthly, Weekly, Daily, Session, Task. The worker may propose trajectory changes. It may not apply them.

## 3. MISSION MODEL

A mission is a bounded unit of engineering intent defined by the architect and refined by the Lab.

```yaml
mission:
  id: M-YYYY-QN-NNN
  title: <one line>
  horizon: quarterly | monthly
  objective: <what should change in the system>
  rationale: <why this matters>
  canon_alignment: <which constitutional principles apply>
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

An unapproved mission is a proposal, not a mission.

## 4. TASK MODEL

A task is a bounded engineering operation completable in a single engineering session.

```yaml
task:
  id: T-M-YYYY-QN-NNN-XX
  parent_mission: M-...
  title: <one line>
  objective: <what should change>
  repository: <repo>
  base_ref: <branch or sha>
  scope:
    files_allowed: []
    files_forbidden: []
    directories_allowed: []
    directories_forbidden: []
  operations_allowed:
    - read
    - edit
    - create
    - delete
    - test
    - build
    - commit_branch
    - open_pr
  operations_forbidden:
    - merge
    - force_push
    - modify_production_config
    - modify_credentials
    - modify_k15_k3
    - modify_provenance
    - modify_authority
  acceptance:
    tests: []
    lints: []
    builds: []
  checkpoint_required: true
  human_authorization_required: true
  estimated_duration_minutes: N
```

## 5. CHECKPOINT MODEL

A checkpoint is an immutable record of task state at a meaningful boundary. Every meaningful execution transition must have a durable checkpoint boundary. Execution and repository checkpoints are written as a coordinated pair; neither is authoritative alone.

Canonical states:

PROPOSED, AUTHORIZED, QUEUED, RUNNING, CHECKPOINTED, VERIFYING, READY_FOR_REVIEW, REVISION_REQUIRED, BLOCKED, FAILED, COMPLETED, ABORTED, EXPIRED.

Semantic non-collapses:

AUTHORIZED ≠ RUNNING; RUNNING ≠ COMPLETED; COMPLETED ≠ APPROVED; APPROVED ≠ MERGED; MERGED ≠ DEPLOYED; DEPLOYED ≠ ACCEPTED.

```yaml
checkpoint:
  id: CP-NNNN
  task_id: T-...
  sequence: N
  state: PROPOSED | AUTHORIZED | QUEUED | RUNNING | CHECKPOINTED | VERIFYING | READY_FOR_REVIEW | REVISION_REQUIRED | BLOCKED | FAILED | COMPLETED | ABORTED | EXPIRED
  execution:
    plan_version: N
    canon_version: N
    authority_level: <level>
    provider_used:
      provider: <provider>
      model: <model>
      tokens_in: N
      tokens_out: N
  repository:
    ref: <branch or sha>
    dirty: true | false
    head: <sha>
    diff_hash: <sha256>
  evidence:
    tests_run: []
    tests_passed: N
    tests_failed: N
    artifacts: []
  human_authorizations: []
  timestamp_utc: <iso8601>
  notes: <free-form>
```

No repository mutation may be represented as completed until its corresponding checkpoint pair is durable, and no checkpoint pair may represent repository state that cannot be verified against the repository.

## 6. ENGINEERING SESSION MODEL

A session is a bounded window of worker activity with a hard stop. Session phases are Load, Plan, Execute, Verify, Checkpoint, Report, Stop. A session never exceeds its duration, token, or repository budget silently.

## 7. WORKER LIFECYCLE

The worker is a governed process, not a persistent agent. It is invoked, acts, reports, and terminates. It resumes only from a valid checkpoint pair and never re-derives state from the original prompt.

## 8. AGENT CONTRACT

The agent is the executable intelligence inside the session and is subordinate to the worker. Capabilities are declared, bounded, and inspectable. It cannot merge, force-push, read or modify secrets, modify authority, K15/K3, provenance, or call external network services outside its allowlist.

## 9. PROVIDER ROUTER

The router abstracts inference and routes by capability class and policy, not merely provider availability. Provider IDs and capability classes are normative; specific model names are implementation artifacts.

Policies include default, coding_heavy, documentation, browser_verification, recovery, and open_only. The router records tokens, cost, latency, and quality score.

## 10. MODEL FALLBACK

Provider failure and session exhaustion are distinct. Provider failure triggers fallback where policy permits; session budget exhaustion terminates the session cleanly with a checkpoint pair. Consumed usage from failed provider attempts remains recorded.

## 11. TOKEN AND BUDGET EXHAUSTION

Exhaustion is hierarchical: provider exhaustion may trigger provider switch; session exhaustion terminates; task exhaustion pauses the task; mission exhaustion pauses the mission; monthly cost ceiling stops engineering dispatch pending architect reauthorization. Every attempt records truthful token and cost usage.

## 12. GITHUB INTEGRATION

GitHub is repository truth and the medium of review, not the source of authority. Allowed operations include repository read, branch creation, branch commits, PR opening, PR comments, and PR closure. Merge, force-push, protected-branch modification, secrets access, and organization-setting changes are forbidden to the worker.

## 13. PULL REQUEST LIFECYCLE

A PR is the evidence artifact. It proceeds from DRAFT_PR through verification to READY_FOR_REVIEW. Architect review may approve, request changes, or close. Merge requires human architect approval and required checks.

## 14. PREVIEW / DEPLOYMENT LIFECYCLE

Preview deployment is evidence, not approval. Production deployment and production configuration changes are human-only.

## 15. TESTING GATES

Unit, integration, architecture-boundary, security, regression, browser, and preview-smoke gates are evidence gates. A gate that does not run is not passed; a failed required gate blocks PR opening.

## 16. HUMAN AUTHORIZATION

Authority levels:

| Level | Name | Effect |
|---|---|---|
| 0 | Observe | worker may inspect only |
| 1 | Suggest | worker may propose |
| 2 | Prepare | worker may stage patch, branch, tests |
| 3 | Build | worker may execute implementation within authorized task scope |
| 4 | Open PR | worker may open PR within authorized task scope |
| 5 | Merge | human-only |
| 6 | Deploy | human-only |
| 7 | Bounded autonomy | RESERVED / NOT ACTIVE in AEAS-v0.1.1 |

Levels 0–4 are reachable only within an architect-authorized bounded task. The Lab does not originate authorization. The authorization envelope defines files, operations, acceptance criteria, duration, prohibitions, and expiry. Outside that envelope, architect authorization is required.

Level 7 is a future governance mechanism. Its existence does not grant autonomous execution capability in v0.1.1.

## 17. FAILURE / RETRY

Failure is recorded and classified. Each failure produces a checkpoint pair and report entry. Retries are bounded and never bypass the authorization chain. Recurring failures upgrade to mission-level review.

## 18. STATE PERSISTENCE

State exists in four planes:

| Plane | Contents | Home | Authority |
|---|---|---|---|
| Constitutional | AEAS, Canon, Trajectory, Governance | Repository | Architect |
| Engineering | Missions, Tasks, Checkpoints, Reports, PR references | Repository + durable store | Architect + Lab |
| Runtime | Active session, worker lease, provider health, scheduler state, locks | Durable runtime store | Worker + Scheduler |
| Identity | Users, ownership, project scoping | Firebase Auth | Human |

Each plane has an authoritative home and must remain recoverable without volatile model context, worker memory, chat history, or local-only state. Loss of one plane must not silently destroy another plane's authoritative record.

## 19. AUDIT / EVIDENCE

Every meaningful operation produces durable, immutable evidence answering who authorized it, its task and mission, preceding checkpoint, provider/model, tokens, changes, tests, current state, and remaining work.

## 20. CADENCE, SCHEDULE, DISPATCH, SESSION

Cadence, schedule, dispatch, session, and task are distinct.

TRAJECTORY → CADENCE → SCHEDULE → DISPATCH → SESSION → TASK

The architect sets trajectory, cadence envelope, and schedule. The Lab composes and validates governed dispatches within that schedule. The worker executes within the dispatched session. The worker never schedules itself or changes cadence or schedule.

## 21. ENGINEERING LAB INTERFACE

The Lab is the governed control surface. It holds trajectory, missions, and tasks; records and enforces architect-originated authorization; composes governed dispatch; observes output; reviews evidence; presents review to the architect; and records the architect's decision.

The Lab displays real state. It is the operational surface, not the authoritative persistence layer. Architect approval remains a human act and may be recorded through any designated authoritative review surface.

## 22. FORBIDDEN ACTIONS

Forbidden to worker, agent, and router: merge PRs; direct push to main; force-push; modify K15/K3, provenance, WorkEvent semantics, authentication, authority, governance, or AEAS; read/write raw secrets; bypass authorization; change trajectory, mission, or task scope; bypass checkpoints or testing gates; production deployment/configuration; create parallel execution, filesystem, database, identity, memory, provider-router, or competing-shell systems; create V2/V3 components. Any such action is session-ending.

## 23. SECURITY BOUNDARIES

Secrets never enter worker context. Provider, Firebase, GitHub, and deployment credentials remain in a secret manager. Repository permissions are minimal, branch protection is respected, and every branch, commit, PR, and merge is traceable.

## 24. COST / TOKEN GOVERNANCE

The architect sets monthly ceilings. The Lab enforces session and mission budgets. The worker never silently exceeds budget. Telemetry records tokens, cost, quality, latency, and failed-provider consumption. Emergency stop applies at ceilings.

## 25. GLOBAL INVARIANTS

I-01 — The protocol is authoritative. The platform is replaceable.

I-02 — The Lab authorizes and orchestrates. The worker executes. For consistency with the sovereignty model, “authorizes” here means the Lab enforces architect-originated authorization; it does not originate authority.

I-03 — Authorization is of bounded tasks, not atomic operations.

I-04 — Provider exhaustion is not session exhaustion.

I-05 — State lives in four planes and survives their own failures.

I-06 — Cadence, schedule, dispatch, session, and task are distinct.

I-07 — Level 7 is reserved.

I-08 — No specific model names are normative.

I-09 — Every authorization, checkpoint, commit, PR, and merge is traceable.

I-10 — Human sovereignty remains outside the recursive loop.
The capability of the Lab may be improved only through architect-authorized engineering work governed by this specification. The Lab may not redefine its own authority, governance, trajectory, or constitutional boundaries.

I-11 — No actor owns sovereignty.
The architect owns authority. The Lab owns governed orchestration and dispatch composition. The scheduler owns timing and scheduling. The worker owns bounded execution. The agent performs bounded intelligence. The platform holds evidence and execution surfaces. No actor in the chain owns sovereignty.

## FINAL DECLARATION

This specification is the architecture of Arkadia's governed engineering autonomy.

The Lab has eyes. This specification gives the Lab hands.

The hands do not have authority. The trajectory carries direction. The architect holds authority and the switch.

The protocol is the architecture. The platform is replaceable.

The worker carries the task. The trajectory carries the direction. The architect carries the sovereignty.

---

Status: FROZEN · AEAS-v0.1.1
Implementation: NOT AUTHORIZED
K15/K3: UNTOUCHED
Provenance: UNTOUCHED
WorkEvent: UNTOUCHED
Next artifact: Trajectory Schema
