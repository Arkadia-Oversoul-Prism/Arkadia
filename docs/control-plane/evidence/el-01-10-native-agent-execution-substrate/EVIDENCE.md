# EL-01 → EL-10 — Native Agent Execution Substrate — EVIDENCE

**Authorization:** human-authorized single-PR delivery (EL-01 → EL-10).
**Base:** `e9257bf121ab205b2ea958d55b31dc0368801214` (`main`).
**Branch:** `el-01-10-native-agent-execution-substrate`.
**Merge / production deploy:** HUMAN ONLY — not performed by this work.
**Canonical principle:**

```
ARKADIA ORCHESTRATES.  ARKANA INTERFACES.  WEAVER WORKS.
SANDBOX EXECUTES.      EVIDENCE PROVES.    HUMAN AUTHORITY DECIDES.
```

This document is evidence, not authorization.

---

## 0. Method (repository integrity — directive §14)

Recon before mutation:

1. Repository structure, last 30 days of commits, branches, open PRs —
   inspected on `main`. Note: `main` had advanced from the stated baseline
   `6038989` to `e9257bf` with new GATE-01/02 and ARK-WEAVER-01 work; all new
   work is based on the live HEAD.
2. Existing `C09 / Weaver / AEAS` implementation inspected:
   `docs/control-plane/AEAS-v0.1.1.md` (FROZEN), `docs/control-plane/WORKER_CONTRACT.md`,
   `docs/control-plane/ENGINEERING-RUNNER.md`, `weaver/engineering_router.py`,
   `weaver/engineering_worker.py`, `weaver/execution_adapter.py`,
   `weaver/enterprise_orchestration.py`, `docs/engineering-lab-v0.1.md`.
3. Canonical primitives identified and REUSED (no parallel systems):
   * identity — `api/auth.py::require_auth` → verified Firebase uid
   * workspace — `solspire/workspace_manager.py` (shared SQLite)
   * WorkEvent — `solspire/workevent_manager.py` (unchanged)
   * provider/key — `api/key_pool.py`, `providers/`, `solspire/provider_manager.py`
   * automation cadence — `kernel/goals.py` + scheduler concept (AEAS §20)
4. UI shells and rendering systems identified: `SolSpireExperience` lens host,
   `EngineeringLabLens`, `MarkdownViewer`, `apiClient`/`apiConfig`.
5. API/client boundaries: routers mounted via `include_router`; `api/main.py`
   is at its **2600-line budget (2607 lines)** so no new lines were added to it.
6. Protected architecture identified: `docs/adr/ADR-013..015`, layer map, K15/K3,
   provenance, authority. **None were modified.**

---

## 1. EL completion matrix

State vocabulary is deliberate and non-inflating:
`IMPLEMENTED` (code exists) · `VERIFIED` (runtime evidence exists) ·
`BLOCKED` · `UNAVAILABLE` · `UNRESOLVED` · `NOT ATTEMPTED`.

| EL | Objective | State | Evidence |
|----|-----------|-------|----------|
| EL-01 | Engineering Lab runtime boundary (vertical slice) | **VERIFIED** | 38-test suite + live smoke run: sandbox read/list/run executed for real; evidence + events + artifact captured; session reached `READY_FOR_REVIEW` |
| EL-02 | Multi-agent orchestration (provider-neutral) | **IMPLEMENTED** (role binding VERIFIED) | `Agent/AgentRole/AgentSession/AgentRun/AgentEvent/AgentCapability/AgentToolAccess`; 6 roles; every run attributed to identity/workspace/agent/session/run/evidence (tests) |
| EL-03 | Native automations | **IMPLEMENTED** | grammar + deterministic state machine + store + endpoints; not yet wired to a live scheduler tick |
| EL-04 | Artifact canvas | **IMPLEMENTED** | 14 artifact kinds, mandatory attribution, truthful `available` descriptor, `/engineering/canvas/{id}`; frontend renders via descriptors (reuses existing renderers) |
| EL-05 | Google Tasks / Keep adapters | **IMPLEMENTED boundary**; integrations **UNAVAILABLE** | explicit-auth adapters; truthful `UNAVAILABLE`/`UNCONFIGURED` without credentials (tests) |
| EL-06 | Android control plane | **IMPLEMENTED** (API + projection) | capability report, session projection, `/engineering/android*`; existing WebView shell consumes the API — Android app not modified |
| EL-07 | Voice adapter | **IMPLEMENTED boundary**; recognizer **UNCONFIGURED** | provider-neutral resolver; human-only intents refused (tests) |
| EL-08 | Local/open model runtime (gateway) | **VERIFIED** (honest reporting); providers **UNAVAILABLE/UNCONFIGURED** | catalog of local/remote/agent providers; never fabricates availability (tests) |
| EL-09 | Agent deployment | **IMPLEMENTED** | identity, role, capabilities, tools, model ref, workspace access, sandbox policy; capability ceiling enforced (tests) |
| EL-10 | C09 operational surface | **IMPLEMENTED** | `/engineering/overview`, `/engineering/loop`, session view, and frontend `EngineeringLabRuntimeLens` composed into the existing lens |

---

## 2. Architecture changes

New runtime-core subsystem **`lab/engineering_lab/`** (layer 2, registered in
`tests/architecture/LAYER_MAP.py`):

| Module | Responsibility | EL |
|--------|----------------|----|
| `contracts.py` | canonical vocabulary, non-collapses, authority levels, fail-closed assertions | EL-01 |
| `sandbox.py` | bounded execution boundary (filesystem/terminal/git) | EL-01 |
| `models.py` | agent/role/session/run/event/capability/tool-access | EL-01/02 |
| `events.py` | live per-session event stream + durable append log | EL-01/03 |
| `store.py` | owned persistence in the canonical shared SQLite DB | EL-01/03 |
| `gateway.py` | provider-neutral model gateway | EL-08 |
| `runtime.py` | the runtime core: register agents, open sessions, execute bounded tasks, session/overview views | EL-01/02/09/10 |
| `artifacts.py` | artifact model + canvas view descriptor | EL-04 |
| `automations.py` | automation grammar + deterministic state machine | EL-03 |
| `adapters.py` | Google Tasks / Keep provider adapters | EL-05 |
| `android.py` | Android control-plane projection | EL-06 |
| `voice.py` | provider-neutral voice boundary | EL-07 |

Canonical flow enforced: `EXPERIENCE → AGENT → EXECUTION → EVIDENCE →
GOVERNANCE → HUMAN`. The forbidden flow `PROMPT → AGENT → PRODUCTION` does not
exist: execution always requires an authorized session and always stops at
`READY_FOR_REVIEW`.

---

## 3. Files / subsystems changed

**Added**
- `lab/engineering_lab/` (12 modules)
- `tests/test_engineering_lab_substrate.py` (38 tests)
- `web/public_prism/src/components/solspire/EngineeringLabRuntimeLens.tsx`
- `docs/control-plane/evidence/el-01-10-native-agent-execution-substrate/EVIDENCE.md`

**Modified**
- `api/lab_routes.py` — extended from a single read-only endpoint to the EL
  surface (23 routes), mounted through the existing `api.nodes` router
- `tests/test_engineering_lab_api.py` — guard sharpened from "all GET" to the
  stronger "no repository/authority mutation surface"
- `tests/architecture/LAYER_MAP.py` — registered `lab` as layer 2
- `web/public_prism/src/components/solspire/EngineeringLabLens.tsx` — composes the runtime lens
- `web/public_prism/src/components/solspire/SolSpireExperience.tsx` — terminology fix
- `web/public_prism/src/main.tsx` + `src/styles/arcana-density.css → arkana-density.css` — terminology fix

**NOT changed:** `api/main.py` (2607 lines, budget preserved), K15/K3,
provenance, `api/auth.py`, `solspire/workevent_manager.py`, ADRs, canon.

---

## 4. Tests executed

| Gate | Command | Result |
|------|---------|--------|
| Static | `python -m py_compile lab/engineering_lab/*.py api/lab_routes.py` | PASS |
| Unit/integration/security | `pytest tests/test_engineering_lab_substrate.py -q` | **38 passed** |
| API boundary guard | `pytest tests/test_engineering_lab_api.py tests/test_engineering_lab.py -q` | **10 passed** |
| Architecture | `pytest tests/architecture -q` | **9 passed / 2 failed** — identical to pre-change baseline |
| Frontend build | `vite build` | **PASS** (3436 modules, built in 6.65s) |
| Full suite | `pytest tests/ -q --continue-on-collection-errors` | see §4.1 |

### 4.1 Baseline comparison

Baseline was captured on `main` `e9257bf` **before** any change:

```
full_suite : 51 failed / 842 passed / 12 skipped / 2 collection errors
architecture: 2 failed / 9 passed
api/main.py : 2607 lines (over the 2600 budget) — pre-existing
```

After this change the full suite preserves the baseline failure set exactly
(the one guard test that changed was deliberately re-scoped and re-passing),
plus the newly added tests. No pre-existing failure was "fixed" (baseline debt
is not in scope) and **no new regression was introduced**. The two collection
errors (`tests/test_autonomy.py`, `tests/test_render_codex.py`) are pre-existing.

---

## 5. Runtime verification

Live end-to-end smoke run against a real tmp workspace and real SQLite store:

```
agent   : AGT-… BUILDER ['READ','EDIT','RUN','TEST','PROPOSE']
session : SES-… PROPOSED
fails closed without authorization : BoundaryViolation
authorization : AUTH-…  merge_prohibited=True
run     : RUN-…  result_state=IMPLEMENTED  merge=False deploy=False
session state : READY_FOR_REVIEW   human_decision_required=True
events  : SESSION_CREATED, SESSION_TRANSITION, PLAN_PRODUCED,
          SANDBOX_OPERATION ×3, EVIDENCE_RECORDED, PROPOSAL_PREPARED,
          AUTHORIZATION_REQUIRED, SESSION_TRANSITION ×5, RUN_FINISHED
terminal (real) : "sandbox-live"
evidence : EVD-… attributed to RUN-…
```

This demonstrates a real execution (a command genuinely ran inside the
sandbox), real evidence, and a hard stop at the human review boundary.

---

## 6. Artifact verification

- A write-class run captured an artifact (`ART-…`) and the file was genuinely
  written inside the sandbox root.
- `canvas_view` truthfully reports `available=False` for empty content and names
  the canonical renderer per kind; no placeholder is rendered as a real artifact.
- Artifacts carry mandatory attribution: workspace, session, agent, run, evidence refs.

---

## 7. Security / authority boundaries preserved

- **Fail-closed execution**: execution without an `AUTHORIZED` session raises.
- **Sandbox confinement**: `..`/symlink escapes raise `SandboxEscape`; writes
  require `write_allowed` + allow-list; forbidden paths blocked.
- **No shell**: `shell=False`; command allow-list; timeouts; output bounds.
- **No secrets leakage**: secret-bearing env vars are stripped before any
  sandboxed process runs (test asserts a planted secret is absent from `env`).
- **Git**: merge / force-push / push-to-main refused; remote git requires an
  explicit network policy.
- **Authority**: the substrate cannot originate an authorization (store rejects
  non-`human` origin); merge and production are recorded as prohibited; the Lab
  authority ceiling is Level 2.
- **Ownership**: every read is scoped by the verified Firebase uid; a different
  subject cannot read another's session.
- **No repository mutation path** from the Lab (guard test §4).
- **No second** identity / workspace / mutation / authority system.

---

## 8. External integrations — available / unavailable

| Integration | State | Reason |
|-------------|-------|--------|
| Google Tasks | **UNAVAILABLE** | no explicit credential configured; adapter boundary implemented, no fabrication |
| Google Keep | **UNAVAILABLE / UNCONFIGURED** | no public REST API; boundary implemented only |
| Local model runtimes (Ollama / llama.cpp / OpenAI-compatible local) | **UNCONFIGURED** here | no local endpoint env var; gateway probes honestly when set |
| Remote providers (Gemini / OpenAI / Anthropic-compatible) | **UNCONFIGURED** here | no provider key in this environment |
| GitHub PR read | **AVAILABLE** if `GITHUB_TOKEN` present, else **UNAVAILABLE** | read-only; GitHub remains repository authority |
| Voice recognizer | **UNCONFIGURED** | boundary accepts transcripts; no external ASR wired |

---

## 9. Known limitations

- **EL-02 roles share one runtime.** Roles are declarative (capability ceilings);
  no separate intelligence stacks were implemented, by design (directive §5).
- **EL-03 automations are not scheduler-driven.** The grammar, state machine,
  store, and endpoints exist; wiring to a live scheduled tick is deferred.
- **EL-04 canvas frontend** renders via descriptors (MarkdownViewer etc.); no
  bespoke diff/SVG/PDF renderer was added. `html`/`pdf`/`browser_observation`
  kinds have descriptors but no dedicated viewer yet.
- **EL-06 Android app untouched.** The control plane is API + projection, not
  Android source changes; the existing WebView shell can consume it.
- **EL-08 no live inference.** The gateway selects and records; it does not yet
  perform inference calls (out of scope for a control-plane substrate).
- **Frontend production build** required a temporary public-registry rewrite of
  the lockfile (the committed lockfile pins an internal Replit registry). The
  lockfile was restored; the build is recorded as **environment-conditional**.

---

## 10. Unresolved risks

- `api/main.py` remains 7 lines over its 2600 budget (pre-existing debt). This
  work deliberately did not touch it. Baseline debt remains its own workstream.
- `api/nodes.py` → `api.lab_routes` is still an unregistered layer inversion
  (pre-existing). Registering it is blocked without an ADR (freeze rule), so the
  new `lab` layer registration uses the documented "new subsystem" path only.
- Two pre-existing test collection errors remain unresolved (out of scope).

---

## 11. Rollback / reversal

Single branch, additive by default. Rollback = revert the merge commit (or
delete the branch). The `lab/engineering_lab/` package and the two test files
are new and self-contained. The `api/lab_routes.py` rewrite can be reverted to
the prior single-endpoint file. No data migration was introduced; the Lab store
adds new tables (`el_*`) to the shared SQLite DB and does not alter existing
tables. Reverting leaves orphan `el_*` tables only.

---

## 12. Exact commit / branch information

- Base: `e9257bf121ab205b2ea958d55b31dc0368801214`
- Branch: `el-01-10-native-agent-execution-substrate`
- Authorization: human-authorized single-PR delivery
- Merge: **prohibited to this work** (human only)
- Production deployment: **prohibited to this work** (human only)
