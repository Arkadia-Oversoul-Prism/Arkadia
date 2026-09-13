# Engineering Runner

The Engineering Runner is the deterministic routing and bounded-session orchestrator for the Arkadia Engineering Lab.

## Role

The Runner serves as the interface between the Scheduler (which provides cadence) and Weaver (which provides routing). It is not a decision maker and does not originate authority.

```
SCHEDULER (timing)
    ↓
ENGINEERING RUNNER (load → route → dispatch)
    ↓
WEAVER (deterministic move selection)
    ↓
WORKER (bounded execution)
    ↓
REPOSITORY (evidence)
    ↓
HUMAN (review & acceptance)
```

## Responsibilities

### 1. Load Phase
- Read the trajectory manifest from canonical location (`docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml`)
- Validate trajectory structure and version
- Inspect current repository state (HEAD SHA, branch status, recent commits)
- Load previous evidence (checkpoints, PR references, move status)

### 2. Route Phase (Weaver Integration)
- Invoke the existing Weaver routing algorithm
- Determine the first incomplete legal move from repository state alone
- Verify:
  - Move status is `pending` or `revision_required`
  - All dependencies are complete
  - Authorization is valid
  - Scope is defined
  - No blocking failures exist
- Return exactly one selected move or a blocking condition

### 3. Plan Phase
- Load the selected move specification
- Inspect current system state for that move's domain
- Create a bounded execution plan
- In dry-run mode, report the plan without executing

### 4. Dispatch Phase
- Create a bounded worker session
- Define execution boundaries (files, operations, time, tokens)
- Pass the move spec and plan to the worker
- Monitor for termination at review boundary

### 5. Evidence Phase
- Collect durable evidence:
  - Repository state before and after
  - Branch created/modified
  - Files changed
  - Tests run and results
  - Acceptance criteria evaluation
  - Next legal move calculation
- Store evidence in repository-native format (PR, commit, structured file)

### 6. Report Phase
- Produce human-readable and machine-readable reports
- Stop at the review boundary
- Do not auto-merge or deploy
- Do not advance to next move without human acceptance

## Key Invariants

### No Second Authority
The Runner does not:
- Redefine the trajectory
- Rewrite move specifications
- Invent new moves
- Reorder the move sequence
- Bypass authorization
- Expand scope
- Collapse state distinctions

### Deterministic Routing
- Routing is derived from repository state, not chat history or session memory
- The same repository state always produces the same next move
- A later scheduler wake recalculates from evidence, not from prior session context

### Bounded Execution
- One active move at a time (`max_active_moves: 1`)
- Worker sessions have hard stop boundaries
- No autonomous continuation to next move
- Failed/revision-required moves remain active

### Evidence Preservation
Every session produces durable evidence sufficient to answer:
- What trajectory?
- What move?
- What repository SHA?
- What branch?
- What files changed?
- What tests ran?
- What passed / failed?
- What acceptance criteria were evaluated?
- What is the next legal move?

## Dry-Run Mode

The first invocation must support dry-run / orientation mode without modifying any application code.

In dry-run mode, the Runner must prove:
- Repository detected
- Trajectory detected and valid
- Current state determined
- Next legal move identified (M01 for current state)
- Scope defined
- Acceptance criteria understood
- No code changes made
- Durable report produced

This allows verification of the routing mechanism before real engineering mutation.

## Execution Adapter

The Runner does not directly execute code or run tests. Instead, it delegates to a provider-neutral Worker contract.

The Worker interface abstracts:
- Coding agents (Claude, GPT, local, etc.)
- Build systems
- Test runners
- Git operations
- PR management
- Deployment systems

The Worker is replaceable. The Runner protocol is not.

## State Model

The Runner preserves the canonical state distinctions defined in AEAS-v0.1.1:

```
PROPOSED
  ↓
AUTHORIZED
  ↓
QUEUED
  ↓
RUNNING
  ↓
CHECKPOINTED
  ↓
VERIFYING
  ↓
READY_FOR_REVIEW
  ├→ REQUEST_CHANGES → REVISION_REQUIRED → [return to RUNNING]
  └→ ACCEPT → [next scheduler wake recalculates]
```

Critical non-collapses:
- `AUTHORIZED ≠ RUNNING`
- `RUNNING ≠ COMPLETED`
- `COMPLETED ≠ APPROVED`
- `APPROVED ≠ MERGED`
- `MERGED ≠ DEPLOYED`
- `DEPLOYED ≠ ACCEPTED`

## Integration Points

### Trajectory
```yaml
# docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml
trajectory:
  id: ARKADIA-TRUTHFULNESS-01
  max_active_moves: 1
  review_gate: required_after_every_move
  moves:
    - id: M01
      status: pending
      depends_on: []
      spec: docs/control-plane/moves/M01-persistence.md
```

### Weaver
```python
# weaver/engineering_router.py
class EngineeringRouter:
    def route(self) -> dict:
        """
        Returns: {
            "next_move": Move object,
            "dependencies_met": bool,
            "authorization_valid": bool,
            "scope_defined": bool,
            "blocking_failures": list,
            "status": "READY" | "BLOCKED" | "NO_LEGAL_MOVE"
        }
        """
```

### Worker
```python
# kernel/worker.py (existing)
def execute_bounded_session(
    session_id: str,
    move_spec: dict,
    execution_plan: dict,
    dry_run: bool = False
) -> dict:
    """
    Returns: {
        "status": "READY_FOR_REVIEW" | "REVISION_REQUIRED" | "BLOCKED" | "FAILED",
        "branch": "weaver/...",
        "files_changed": [...],
        "tests": {...},
        "evidence": {...},
        "next_legal_move": "M02"
    }
    """
```

## Failure Behavior

If any of the following occur:

- Trajectory cannot be loaded
- Weaver cannot determine a legal move
- Authorization is missing or invalid
- Dependencies are unresolved
- Scope is ambiguous
- Repository state is inconsistent
- Evidence cannot be persisted
- Worker session times out or crashes

Then:

1. STOP immediately
2. REPORT the failure with full context
3. PRESERVE all state for human inspection
4. Do NOT guess, retry, or continue
5. Wait for human authorization to proceed

## Testing

Tests must verify:

1. ✅ Trajectory loads successfully
2. ✅ Weaver selects M01 from current repository state
3. ✅ Weaver does not select M02 while M01 is incomplete
4. ✅ Blocked dependencies prevent execution
5. ✅ Revision-required moves remain active
6. ✅ No legal move produces a clean STOP state
7. ✅ Dry-run produces durable evidence without code changes
8. ✅ Worker cannot merge PRs or deploy production
9. ✅ Worker stops at review boundary
10. ✅ Later scheduler wakes recalculate state from repository evidence
11. ✅ Concurrent scheduler runs cannot create overlapping sessions
12. ✅ Session state is reconstructed from durable evidence

## Documentation

This module is governed by:
- AEAS-v0.1.1 (sovereignty model, checkpoint model, task model, session model)
- WEAVER-RUN-PROTOCOL.md (routing algorithm, bootstrap protocol, review gate)
- TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml (move definitions, dependencies, acceptance)
- Individual move specifications (M01–M09)

The Engineering Runner itself is NOT a specification artifact. It is infrastructure that makes the specifications executable.

---

**Version:** 1.0  
**Status:** BOOTSTRAP  
**Authority:** Scheduler/Worker lifecycle only  
**Modification:** Only to improve routing fidelity or worker interface; never to redefine trajectory, move scope, or acceptance criteria

## Scheduler (GitHub Actions)

Workflow: `.github/workflows/arkadia-engineering-scheduler.yml`

- **Manual:** `workflow_dispatch` with `dry_run` (default `true`)
- **Scheduled:** hourly cron `0 * * * *` (wake only; default dry-run)
- **Concurrency:** group `arkadia-engineering-session`, `cancel-in-progress: false` (max one active session)
- **Permissions:** `contents: read`, `actions: read` — no write, no merge, no deploy

## Bootstrap modules

- `weaver/engineering_router.py` — trajectory load + deterministic routing
- `weaver/engineering_worker.py` — bounded session, stops at review
- `weaver/execution_adapter.py` — provider-neutral; `NullExecutionAdapter` for orientation

Live M01 mutation requires an approved non-null adapter and explicit non-dry-run dispatch after human acceptance of this bootstrap.
