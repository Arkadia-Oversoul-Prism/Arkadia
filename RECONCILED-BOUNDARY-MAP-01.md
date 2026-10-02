# RECONCILED-BOUNDARY-MAP-01

**Workstream:** RECONCILED-BOUNDARY-01 — Arkadia-native boundary remediation
**Branch:** `reconciliation/verified-boundary-01` @ `1700b36`
**Base:** `Arkadia-Oversoul-Prism/Arkadia` `main` @ `2035d2696119`
**Home:** this artifact belongs to the **Arkadia** workstream (source monorepo), not
the extracted `relational-substrate` repo. See §8.
**Companion artifact:** `REPOSITORY-RECONCILIATION-01.md` (topology, transferable state)
**Status:** boundary changes authored + evidenced **locally**. **STOP gate observed** — no console design below.

---

## 0. Claim status — read this first

Every claim in this map carries one of four statuses. They are **not**
interchangeable, and the whole point of this section is that a claim may be
*implemented* and *tested* while remaining **unverified in production**.

| Status | Meaning |
|---|---|
| **IMPLEMENTED (local)** | Code exists on `reconciliation/verified-boundary-01` @ `1700b36`. |
| **TESTED (local)** | A test on the branch exercises the boundary and passes. |
| **DEPLOYED** | The code is running on a live host. |
| **PRODUCTION-VERIFIED** | The running host was probed and the boundary observed to hold. |

**Current disposition of the boundary changes:**

| Item | Implemented | Tested | Deployed | Production-verified |
|---|---|---|---|---|
| BC-1 authentication at tool boundary | ✅ local | ✅ local | ❌ | ❌ |
| BC-2 approval authority / separation / self-approval | ✅ local | ✅ local | ❌ | ❌ |
| BC-3 kernel loop + plan-execution auth / import repair | ✅ local | ✅ local | ❌ | ❌ |

**Nothing in this workstream is deployed. Nothing is production-verified.**
The branch is a *controlled delivery artifact*, held unpushed until the console
architecture is complete.

**Explicit non-claims:**

- **Render — UNVERIFIED.** The live host `https://arkadia-kw64.onrender.com` runs
  pre-hardening code. It was last probed anonymously and answered `200` on
  `/api/tools`, `/api/approvals`, `/api/goals`, `/api/jobs` (AB-1: anonymous
  `execute_shell/run {"command":"whoami"}` → `200 root`). This branch changes no
  host. **Render posture is UNVERIFIED.**
- **Flamekeeper — UNPROVISIONED.** The role is *declared* in `governance/roles.json`
  and *enforced* by BC-2, but no principal is seated in that role. However — see
  §6 item 5 — the enforcement layer also admits the `access_level >= 3` sovereign
  tier, which **existing node principals occupy**. Approvals are therefore
  decidable today by a sovereign principal; the declared role is unseated, but
  governing authority is not absent. The declared/enforced gap is unresolved.
- **AUTHORITY-CLOSURE-01 — PRE-PRODUCTION.** The authority model (who may approve,
  and how authority is granted) is not yet closed. BC-2 enforces the *rule*; it
  does not provision the *role*. Authority closure remains pre-production.

---


## 1. Purpose

The operator-console workstream (Arkadia Substrate Console) was blocked on a
question of authority: *which* repository owns the execution perimeter, and
*what* that perimeter is. `REPOSITORY-RECONCILIATION-01.md` established the
topology — Arkadia is the source monorepo (frontend + backend); `relational-substrate`
is the extracted backend-only repo, already hardened. This artifact records the
reconciliation of the *boundary itself*: the Arkadia-native changes that bring
the source monorepo to the same perimeter posture the extracted backend already
holds, with the evidence that pins each one.

Nothing here is a port of substrate code. Each change is authored against
Arkadia's own governance model, module layout, and route set. Where the
substrate and Arkadia disagree, the disagreement is recorded rather than
silently flattened.

---

## 2. The boundary, restated

The execution perimeter has four checks that compose; none substitutes for
another:

| Check | Establishes | Fails to |
|---|---|---|
| **Authentication** | *who* is calling | anonymous access |
| **Authorization** | the caller may reach this operation | an authenticated stranger |
| **Approval** | a recorded, unconsumed, same-subject decision exists | self-service on a consequential tool |
| **Separation** | deciding ≠ doing | a single handler that both authorizes and executes |
| **Governance** | the decider holds the `Govern` permission | a non-authority approving |

Arkadia declared most of this in prose (`governance/roles.json`, the
`auth.py` production guard) but did not *enforce* it at the tool boundary. The
reconciliation makes the declaration executable.

---

## 3. Boundary changes (Arkadia-native)

### BC-1 — Authentication at the tool boundary

**Files:** `api/main.py`, `api/loop_routes.py`, `api/plan_routes.py`

Before: `GET /api/tools`, `POST /api/tools/{tool_name}/run`, `POST /api/agent/spawn`,
`POST /api/ceo/chat`, and the entire kernel-loop router (`/api/jobs`, `/api/goals`)
were reachable with no identity. `grep -c require_auth api/main.py` returned `0`.

After:
- each surface declares `Depends(require_auth)`;
- `api/loop_routes.py` carries router-level auth — every job/goal route mutates or
  exposes kernel-loop state (the job queue executes tools; the goal scheduler
  starts recurring runs), so the whole router is gated;
- `/api/plan/run` is served by a new, authenticated `api/plan_routes.py`;
- **fail-closed fallback:** if `api.auth` fails to import outside production, the
  module's `_require_auth` shim raises `503` rather than degrading to an
  unauthenticated route. A route that depends on authentication never runs
  unauthenticated merely because its dependency is missing.

### BC-2 — Approval authority, separation, and self-approval prevention

**File:** `api/approval_routes.py` (rewritten)

Before, the module was pre-hardening and *worse* than the substrate baseline:
no auth on any route; `GET /api/approvals` returned **all** approvals to anyone;
and `api_approve` **executed the tool inside the approval handler** — a single
event that both decided and acted.

After:
- every route requires auth;
- listing is **subject-scoped** — an ordinary caller sees only approvals it
  originated; a `Govern` principal (reviewer) sees all pending approvals, since
  a reviewer must be able to see what it is entitled to decide;
- **approve records a decision and does not execute.** Execution is a distinct
  act at `POST /api/tools/{tool_name}/run`. The recorded authorization and the
  permitted action are separate events;
- approve/reject require the **`Govern` permission** — the `Flamekeeper` role, or
  the sovereign `access_level >= 3` tier. This is Arkadia's own model
  (`governance/roles.json`: Flamekeeper holds Govern; Weaver is explicitly
  "non-authoritative for governance"), enforced rather than assumed;
- **self-approval is prohibited** — the principal that requested an approval
  cannot also decide it. A distinct authority must render the decision;
- approvals are **single-use** and **same-subject**: `consumed_at`/`consumed_by`
  are stamped at execution, and the tool-run boundary requires the approval's
  `subject_ref` to match the executing caller.

### BC-3 — Kernel loop and plan-execution auth, plus a latent import repair

**Files:** `api/loop_routes.py`, `api/plan_routes.py`, `api/main.py`

- the kernel-loop router is authenticated (see BC-1);
- plan execution runs the planner and then executes the resulting steps — a
  consequential operation — so it requires auth;
- the plan is validated against the tool registry (`validate_plan`) before
  execution: an unregistered tool in a plan is refused rather than run;
- **latent defect repaired:** `main.py` imported `execute_plan` from
  `kernel.execution`, which does not define it, so `/api/plan/run` raised
  `ImportError` → 500 even when reached. The import now resolves to
  `kernel.planner`, where `execute_plan` actually lives.

---

## 4. Reconciled surface map

`Sub` = extracted backend (`relational-substrate`) posture after its hardening.
`Ark` = Arkadia posture after `1700b36`.

| # | Surface | Sub | Ark (before) | Ark (after) | Evidence |
|---|---|---|---|---|---|
| 1 | `GET /api/tools` | auth | open | auth | perimeter:31 |
| 2 | `POST /api/tools/{tool}/run` | auth + approval | open | auth + approval | perimeter:31 |
| 3 | `POST /api/approvals/request` | auth | open | auth (subject-attributed) | perimeter:31 |
| 4 | `GET /api/approvals` | auth + scoped | open, all rows | auth + subject-scoped | perimeter:31 |
| 5 | `POST /api/approvals/{id}/approve` | auth + Govern; decision only | open; executes | auth + Govern; decision only | perimeter:31 |
| 6 | `POST /api/approvals/{id}/reject` | auth + Govern | open | auth + Govern | perimeter:31 |
| 7 | `POST /api/plan/run` | auth | open; broken import | auth; validated | plan:7 |
| 8 | `POST /api/agent/spawn` | auth | open | auth | perimeter:31 |
| 9 | `POST /api/ceo/chat` | auth | open | auth (queues subject-scoped approvals) | perimeter:31 |
| 10 | `/api/jobs`, `/api/job/create`, `/api/job/{id}`, `…/trace` | auth | open | auth (router-level) | perimeter:31 |
| 11 | `/api/goals` (GET/POST/PATCH/DELETE) | auth | open | auth (router-level) | perimeter:31 |
| 12 | Production auth guard | fail-closed | present in `auth.py` | unchanged, pinned | posture:3 |

Concordant by construction: rows 1–11 now hold the substrate posture; row 12 was
already correct in Arkadia and is pinned so it cannot regress.

---

## 5. Evidence

**Tests added (Arkadia-native, 82 total):**

| Module | Tests | Pins |
|---|---|---|
| `tests/test_tool_execution_perimeter.py` | 31 | anonymous denial; approval gating; decision≠execution; Govern authority; self-approval prohibition; subject scoping; single-use; containment survives approval |
| `tests/test_authority_boundary.py` | 17 | **AUTHORITY ≠ AUTHORIZATION** — authorized-to-reach ≠ authoritative-to-decide; 403 vs 401; authority does not confer reach; authority is a principal property |
| `tests/test_kernel_plan_perimeter.py` | 7 | plan/spawn auth; router extraction; `validate_plan`; repaired import |
| `tests/test_evidence_verification_boundary.py` | 10 | **EVIDENCE ≠ VERIFICATION** — evidence is created alone and creates no verification; verification is a separate call requiring evidence; the link is a correlation (`evidence_refs`), not a foreign key; evidence can exist unverified; a verification cannot reference absent evidence; both records are append-only; no route creates or lists them |
| `tests/test_workevent_evidence_boundary.py` | 7 | **WORK EVENT ≠ EVIDENCE** — a WorkEvent carries only opaque references and produces no evidence/verification; no table joins a WorkEvent to evidence; the WorkEvent manager and the enterprise evidence store are disjoint; evidence binds to an execution attempt, not a WorkEvent; verification references evidence ids; no route exposes evidence/verification |
| `tests/test_execution_workevent_boundary.py` | 7 | **EXECUTION ≠ WORK EVENT** — a gated run creates no job and no WorkEvent; execution evidence lands on the approval; a kernel job records its own events but references no WorkEvent; the WorkEvent model has no execution field; the execution path never imports the spine; the enterprise graph has no HTTP route |
| `tests/test_auth_deployment_posture.py` | 3 | production refuses to start without/invalid credentials; dev-mode fallback |

Anonymous-denial cases exercise the **real** dependency (no override), so the
assertion is about the boundary itself. Authenticated cases override
`require_auth` so authorization/approval logic is tested deterministically
without Firebase credentials — the override is the identity under test, not a
stand-in for the boundary being verified.

**`AUTHORITY ≠ AUTHORIZATION` (Boundary Expansion Gate 01).** The dedicated test
the map previously flagged as missing. It isolates the authority layer from the
self-approval prohibition by deciding as a principal *distinct* from the
requester, so a 403 can only be the authority gate. Verified by mutation: making
`_has_govern_authority` always true fails 4 authority tests while leaving the
rest green — the tests bite on the gate itself, not on an incidental 403.

**`EXECUTION ≠ WORK EVENT` (Boundary Expansion Gate 02).** Measured, not
assumed. A gated tool run (`execute_shell`) succeeds and consumes its approval
while creating **no** kernel job and **no** WorkEvent. A kernel job
(`POST /api/job/create`) records its own `execution.events` (lease, checkpoints)
but references no WorkEvent. The WorkEvent model carries no `job_id` / `task_id`
/ `execution_ref` field, and the only creator of a WorkEvent in the codebase is
the `/solspire/workevents` router — no execution or job module constructs one.
Verified by mutation: inserting a `_job_store().create(...)` call into
`run_tool_endpoint` fails the "no job" assertion while leaving the rest green —
the test bites on the absence of the join, not on an incidental condition. The
richer `weaver/enterprise_orchestration.py` graph (`forward_walk` /
`reverse_walk`) has no HTTP route for its traversal and is recorded as
*implemented, unexposed* (its counters and verified evidence are read only
through the control-room projection).

**`WORK EVENT ≠ EVIDENCE` (Boundary Expansion Gate 03).** Measured from an
actual WorkEvent, not from an expected architecture. A WorkEvent created through
`POST /solspire/workevents` produces **no** evidence and **no** verification; its
reference fields (`artifact_refs`, `state_before_ref`, `state_after_ref`,
`decision_ref`, `witness_ref`) are opaque strings that no code resolves. The
runtime evidence chain that does exist (`ew_evidence` / `ew_verifications` in
`weaver/enterprise_orchestration.py`) binds evidence to an `execution_attempt_id`,
never to a `work_event_id`, and a verification's `evidence_refs` is a list of
evidence ids, not a foreign key. The WorkEvent manager has no evidence
capability and the enterprise evidence store has no WorkEvent capability — the
two modules are disjoint, and no table joins them. Verified by mutation: adding an
`evidence_refs` column to the `work_events` schema fails the no-join assertion
while leaving the rest green — the test bites on the absence of the join, not
on an incidental condition.

**`EVIDENCE ≠ VERIFICATION` (Boundary Expansion Gate 04).** Measured from an
actual persisted evidence record in the ARK-WEAVER-01 enterprise chain — the same
records the control-room projection reads over HTTP. Evidence is created only by
`EnterpriseOrchestrationStore.evidence()` and carries a durable id (`ev-<uuid>`);
creating it creates **no** verification. A verification is a separate, explicit
call (`verify()`) with its own id (`vr-<uuid>`). The link between them is a
**correlation, not a join**: `ew_verifications.evidence_refs` is a JSON text list
matched by `instr()` in the projection, with no `FOREIGN KEY` and no reverse
pointer on `ew_evidence`. The relationship is **asymmetric** — a verification
cannot be created without referencing an existing evidence record (write-time
check), but evidence can stand alone with no verification, and `forward_walk`
fabricates none. Traversal is durable in both directions when a verification
exists. Both records are append-only (no `UPDATE`/`DELETE` in the store). Verified
by mutation: making `evidence()` auto-create a verification fails the
evidence-stands-alone assertions while leaving the rest green — the test bites
on the collapse of evidence into verification, not on an incidental condition.

**Commands:**

```
# the seven new modules
pytest tests/test_tool_execution_perimeter.py tests/test_authority_boundary.py \
       tests/test_execution_workevent_boundary.py tests/test_workevent_evidence_boundary.py \
       tests/test_evidence_verification_boundary.py tests/test_kernel_plan_perimeter.py \
       tests/test_auth_deployment_posture.py -q   # 82 passed

# architecture + route contract (unchanged by this branch)
pytest tests/architecture/ tests/test_documented_route_contract.py -q   # 20 passed
```

**Regression control:** full suite run on a pristine `main` worktree and on the
branch, failure sets diffed:

| | failed | passed |
|---|---|---|
| `main` @ `2035d26` | 20 | 1130 |
| branch @ `1700b36` (BCs only) | 20 | 1171 |
| branch @ Expansion Gate 01 | 20 | 1188 |
| branch @ Expansion Gate 02 | 20 | 1157 |
| branch @ Expansion Gate 03 | 20 | 1164 |
| branch @ Expansion Gate 04 | 20 | 1174 |

New failures introduced: **none.** The 20 failures are pre-existing
(`steward_filter`, Spiral-Grove, SolSpire r1/r2/r3, ReasoMate truth, and other
legacy modules) and are out of this workstream's scope — none is in a file this
branch touches. Delta of +82 passing tests is exactly the new perimeter modules
(58 at Expansion Gate 01 + 7 at Expansion Gate 02 + 7 at Expansion Gate 03 + 10 at
Expansion Gate 04). The full-suite pass count
varies between runs because a handful of legacy modules share global state
(`weaver.*`); the *failure set* is stable. The 7 collection errors are all the
pre-existing legacy `weaver` shadowing (`ModuleNotFoundError: No module named
'weaver.agent'; 'weaver' is not a package`) in modules unrelated to this
workstream; `tests/test_execution_workevent_boundary.py` collects and passes.

---

## 6. Open items (recorded, not resolved)

1. **Live host runs pre-hardening code.** `https://arkadia-kw64.onrender.com`
   answered anonymous `200` on `/api/tools`, `/api/approvals`, `/api/goals`,
   `/api/jobs`; the AB-1 vector returned `200 root` for an anonymous
   `execute_shell/run {"command":"whoami"}`. These are code-level boundary
   findings — this branch does not deploy. The host remains pre-hardening until
   the branch is merged **and deployed**.
2. **Deployment configuration is applied on the actual host, not locally.** The
   production guard (BC-1 / row 12) only takes effect where
   `ENVIRONMENT=production` and `FIREBASE_SERVICE_ACCOUNT_JSON` are set on the
   running host. That is an operational step on the real host, outside the
   repository.
3. **`BaseTool.requires_approval` default.** `kernel/tools.py` does not declare
   `requires_approval` on `BaseTool`; the boundary reads it with
   `getattr(tool, "requires_approval", False)`. `kernel/tools_real.py` declares it
   on the real tools. Declaring the default on `BaseTool` would make the contract
   explicit rather than assumed — deferred, as it is a `kernel/` change outside
   the three authorized boundary changes.
4. **`api/approval_routes.py` vs substrate divergence.** The substrate's
   hardened module was used as the *posture* reference, not copied. Arkadia's
   rewritten module keeps Arkadia's in-memory `PENDING_APPROVALS` state and its
   `queue_approval` signature (extended with `subject_ref`), because
   `api/main.py` CEO-chat shares that state.
5. **Declared vs enforced authority disagree (found during Expansion Gate 01).**
   `governance/roles.json` declares `Govern` for the **Flamekeeper** role only,
   and no principal is seated in that role (the node registry has no Flamekeeper
   node). But `api/approval_routes._has_govern_authority` *also* accepts
   `access_level >= 3` — the sovereign tier, which existing node principals
   (`zahrune`, `jessica`, `won`, `jay`, `eden`) occupy. The enforced model is
   therefore broader than the declared one. Verified live: a distinct sovereign
   principal (`zahrune`) approved an approval, and a subsequent gated tool run
   consumed it. **Consequence for the console:** the standing claim "approvals
   cannot currently be decided" was false and has been corrected; the console now
   states the declared/enforced gap as an unresolved boundary rather than a
   settled `UNPROVISIONED`. Whether to close this by declaring the sovereign
   tier's approval authority, or by narrowing the enforcement to the Flamekeeper
   role, is a governance decision — recorded, not resolved.
6. **Enterprise orchestration traversal is not exposed over HTTP.** `weaver/
   enterprise_orchestration.py` implements a genuine proposal → authority →
   authorization → execution → evidence → verification graph with
   `forward_walk` / `reverse_walk` traversal. **The traversal has no HTTP route**
   (confirmed against the running server's OpenAPI). The graph's *data* is
   partially readable over HTTP — the enterprise control-room projection
   (`GET /solspire/workspaces/{id}/control-room` → `eden_ops_02`) reads its
   counters and promotes verified `ew_evidence` content — but the lineage walk
   itself cannot be presented as live data. The console therefore uses only what
   the substrate exposes (approvals, jobs, tools) and labels the approval↔job
   link as inferred.
   The richer graph is a candidate for a future read surface.
7. **Approval ↔ execution-job is not a persisted join; it is inferred only
   (found during Expansion Gate 01).** The approval record carries `subject_ref`,
   `decided_by`, and — once consumed — `consumed_at` / `consumed_by`. A job
   record carries `intent` and `source`. **Neither persists the other's id:**
   the job does not store `approval_id`, and the approval does not store a
   `job_id`. `api/main.run_tool_endpoint` consumes the approval and returns the
   tool envelope **synchronously, without enqueuing a job at all** — verified
   live: an approval was consumed (`decided_by=zahrune`, `consumed_by=
   console-operator`) while the job count stayed at 2. Consequently:
   - **Approval → consumption** is *recorded* (exact).
   - **Approval → job** and **Job → approval** are *inferred* by the console under
     a narrow rule (same tool + subject, within a window of consumption) and
     labelled as inferred, never drawn as a persisted join.
   - **Correlation ≠ lineage:** temporal/tool/subject correlation is not promoted
     to causal provenance.
   - **Truthful emptiness:** where no attributable record exists, the console
     renders "no attributable execution records" and fabricates nothing.

   **This absence is the evidence, not a defect to fix here.** Whether to persist
   an explicit approval↔job join (and thereby make EXECUTION → WORK_EVENT a real
   causal edge) is a later architectural decision; it is recorded, not resolved.
   Expansion Gate 02 confirmed the same absence one layer down: there is no
   execution → WorkEvent identifier either, and no code path that would create
   one (see item 8).

8. **Execution does not produce a WorkEvent; the two records are not joined
   (found during Boundary Expansion Gate 02).** The SolSpire Work Event spine
   (`solspire/workevent_manager.py`, table `work_events`) persists a distinct
   continuity record whose **only** creator in the codebase is the
   `/solspire/workevents` router. `api/main.run_tool_endpoint` executes a tool
   and returns synchronously — it creates **no** job and **no** WorkEvent. A
   kernel job (`POST /api/job/create`) records its own `execution.events`
   (`lease.acquired`, `execution.started` / `execution.completed`) but carries
   no `work_ref` / `work_event_id`, and the `WorkEvent` model has no `job_id` /
   `task_id` / `execution_ref` field. Consequently:
   - **Recorded:** execution evidence on the approval (`consumed_at` /
     `consumed_by`), kernel job execution events, and WorkEvents in their own
     spine — three separate records.
   - **Absent:** a durable execution → WorkEvent identifier, and any code path
     that would create a WorkEvent from an execution.
   - **Unexposed:** `weaver/enterprise_orchestration.py` holds a richer
     proposal → authority → authorization → execution → evidence →
     verification graph (`forward_walk` / `reverse_walk`) whose traversal has no
     HTTP route; its counters and verified evidence are read only through the
     control-room projection.

   **The absence is the measurement.** Whether to join execution and the Work
   Event spine is a later architectural decision; it is recorded, not resolved.
   Measured by `tests/test_execution_workevent_boundary.py` (7 tests, mutation-
   verified).

9. **A WorkEvent does not produce evidence; the Work Event spine and the
   evidence chain are not joined (found during Boundary Expansion Gate 03).**
   Starting from an actual WorkEvent: creating one through
   `POST /solspire/workevents` produces **no** evidence and **no** verification,
   and its reference fields (`artifact_refs`, `state_before_ref`,
   `state_after_ref`, `decision_ref`, `witness_ref`) are opaque strings that no
   code resolves to a record. The runtime evidence chain that does exist —
   `weaver/enterprise_orchestration.py`'s `ew_evidence` / `ew_verifications` —
   binds evidence to an `execution_attempt_id`, never to a `work_event_id`; a
   verification's `evidence_refs` is a list of evidence ids, not a foreign key.
   The WorkEvent manager has no evidence capability and the enterprise evidence
   store has no WorkEvent capability: the two modules are disjoint, and no table
   joins them. Consequently:
   - **Recorded:** the WorkEvent and its opaque references; `ew_evidence` bound
     to an execution attempt; `ew_verifications` referencing evidence ids.
   - **Absent:** a durable WorkEvent → Evidence identifier, and any code
     path that produces evidence from a WorkEvent.
   - **Unexposed:** no dedicated route exposes evidence or verification as
     first-class records; the enterprise chain is read only as a control-room
     projection, and its `forward_walk` / `reverse_walk` traversal has no route.

   **The absence is the measurement.** Whether a WorkEvent should produce or
   reference evidence is a later architectural decision; it is recorded, not
   resolved. Measured by `tests/test_workevent_evidence_boundary.py` (7 tests,
   mutation-verified).

10. **Evidence and verification are separate records, correlated not joined
    (found during Boundary Expansion Gate 04).** Starting from an actual persisted
    evidence record: `evidence()` creates a durable `ew_evidence` row (`ev-<uuid>`)
    and creates **no** verification. `verify()` is a separate call producing its own
    `ew_verifications` row (`vr-<uuid>`). The link is a **correlation**: 
    `ew_verifications.evidence_refs` is a JSON text list matched by `instr()` in the
    control-room projection — there is no `FOREIGN KEY` and no reverse pointer on
    `ew_evidence`. The relationship is **asymmetric**: a verification requires an
    existing evidence reference (write-time check), but evidence may stand alone
    with no verification. Consequently:
   - **Recorded:** `ew_evidence` with a durable id and a real FK to the execution
     attempt; `ew_verifications` with its own id, verdict and verifier; the citation
     `evidence_refs`.
   - **Absent:** a foreign key between evidence and verification; a reverse pointer
     on `ew_evidence`; any evidence that is *required* to be verified.
   - **Unexposed:** no route creates or lists evidence or verification; both are
     readable only through the control-room projection.

   **The asymmetry is the measurement.** Whether evidence should carry a durable
   forward pointer to its verification is a later architectural decision; it is
   recorded, not resolved. Measured by `tests/test_evidence_verification_boundary.py`
   (10 tests, mutation-verified).

---

## 7. Provenance chain

This artifact is only meaningful if it can be traced back to the code it
describes. The chain is:

```
Arkadia implementation @ 1700b36 (BC-1/2/3) + Expansion Gate 01 commit (authority test)
        │  (BCs at 1700b36f2869d534760187764d74a71f09523b9e)
        ▼
boundary evidence (82 tests, 7 modules, on the branch)
        │
        ▼
RECONCILED-BOUNDARY-MAP-01.md   ← this document
```

Verification performed (read-only, against the branch):

| # | Check | Result |
|---|---|---|
| 1 | `1700b36` is exactly the branch head | ✅ `1700b36f2869d534760187764d74a71f09523b9e` |
| 2 | The three BCs are represented accurately | ✅ §3; pre-change state confirmed on `main` |
| 3 | Every claimed enforcement boundary has a test | ✅ §5 mapping |
| 4 | Tests exercise the boundary, not a mock | ✅ zero `mock`/`patch`/`monkeypatch`; identity injected via `dependency_overrides` only |
| 5 | 20 pre-existing failures excluded and unchanged | ✅ 20 == 20, zero new |
| 6 | No claim depends on substrate-only implementation | ✅ enforcement points are Arkadia files only |
| 7 | Implemented / tested / deployed / production-verified distinguished | ✅ §0 |
| 8 | Render explicitly UNVERIFIED | ✅ §0 |
| 9 | Flamekeeper unprovisioned | ✅ §0 |
| 10 | AUTHORITY-CLOSURE-01 PRE-PRODUCTION | ✅ §0 |

**Pre-change state (verified against `main` @ `2035d26`):**

- `git show main:api/main.py | grep -c require_auth` → `0`
- `list_tools_endpoint()`, `run_tool_endpoint()`, `agent_spawn()`, `ceo_chat()`,
  `run_plan()` — all declared with **no** auth parameter
- `api/loop_routes.py` on `main` — `APIRouter(tags=["Kernel Loop"])`, no dependencies

After the branch: `api/main.py` has 7 `require_auth` references, the loop router
carries router-level auth, and `/api/plan/run` is served by an authenticated
`api/plan_routes.py`.

## 8. Artifact home

This map **belongs to the Arkadia workstream** and is committed on
`reconciliation/verified-boundary-01`, beside the code it describes. It was
initially drafted in the extracted `relational-substrate` worktree; that
placement created a provenance split (evidence in Arkadia, artifact in the
extracted repo) and is corrected here. `REPOSITORY-RECONCILIATION-01.md` remains
a topology artifact of the extraction and may live with either repo.

## 9. Stop gate

Per the current directive, boundary work **stops here**. The three boundary
changes are authored on `reconciliation/verified-boundary-01` and evidenced;
this map is produced and carries its provenance chain.

**No operator-console design is proposed, sketched, or implied in this
artifact.** Console design is a separate workstream
(`RECONCILED-CONSOLE-ARCHITECTURE-01`), derived from this verified model plus the
existing Arkadia UI plus the independently derived backend console — not from a
UI-plus-UI redesign.
