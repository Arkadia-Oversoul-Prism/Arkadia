# Workstream 4 — Lab substrate overview read surface, and a credential-disclosure finding

**Slice:** 08 — `GET /api/lab/overview`
**Branch:** `feat/prism-next2-04-run-evidence-trace`
**PR:** #432 (draft)
**Authority:** implement, test, commit, report. **No merge, no deployment, no acceptance.**

---

## 1. Why this surface

`endpoints.labOverview` is declared in the shared registry
(`web/arkadia_console/src/lib/endpoints.ts:29`) and was **unwired**. Like slice 07, it
needs no registry change. It is also the Lab's self-description, and it carries the
substrate's own governance ceiling — the one place the Lab states what it refuses to do.

---

## 2. Verified route / auth / data contract

| | |
|---|---|
| Method + path | `GET /api/lab/overview` |
| Router | `APIRouter(prefix="/api/lab", dependencies=[Depends(require_lab_auth)])` (`api/lab_routes.py:61`) |
| Handler | `lab_overview() -> build_overview(".")` (`api/lab_routes.py:67`) |
| Auth | Lab router default `require_lab_auth`. **Live check:** anonymous `GET https://arkadia-qzu4.onrender.com/api/lab/overview` → **401** `{"detail":"Authentication required"}` |
| Response | `{schema_version, collector_version, analysis_version, observed_at, system, repository, architecture, trajectory, canon, patterns, graph, deployments, security, governance, errors, status}` |

Measured in this environment: `status: observed`, `errors: []`, architecture
`159 components / 968 modules / 41 services / 198 routes`, graph `2348 entities`,
48 security observations, 4 patterns.

**`governance` (the load-bearing block):**
`{"maximum_authority": 2, "autonomous_mutation": false, "production_mutation": false, "approval_required": true}`

---

## 3. Security finding — `repository.remote` discloses remote userinfo

**What it is.** `build_overview()` returns `repository.remote`, which is the verbatim
output of `git remote get-url origin`
(`lab/observatory/git.py:21`: `_run(root, ["remote", "get-url", "origin"])`). Git
stores the remote URL including any `user:token@` userinfo, so wherever the remote was
configured with a credential the response carries it.

**Measured, this environment** (shape only — the value is never printed):

```
remote is None:               False
has userinfo '@':             True      # e.g. https://<userinfo>@github.com/...
scheme:                       https
security.values_redacted:     True      # <-- scoped to observations only
```

**Why the handler's own flag does not cover it.** `security.values_redacted: true`
reads as a blanket assurance, but `security_observations()` only classifies *file
paths* that mention credential-ish **names** (`GEMINI_API_KEY`, `AIza`, …) and returns
`"value redacted"` for those paths. It never inspects `repository.remote`, so the flag
is silent about it. The response therefore asserts redaction while carrying an
unredacted remote.

**Reachability.**

* Live canonical origin: **401** unauthenticated — not anonymously readable. Confirmed
  by direct probe, not inferred.
* The endpoint *is* exercised in CI: `.github/workflows/sg-02-fe-2-v.yml:245` fetches
  `/api/lab/overview` with a synthetic unsigned token and asserts `200`. The step prints
  only status codes and its secret-scan list (`AIza`, `PRIVATE KEY`, `GEMINI_API_KEY`,
  `FIREBASE_SERVICE_ACCOUNT_JSON`) does **not** include a GitHub token shape, so the
  response body is neither printed nor screened for this class.
* Deployed image: the runtime stage of `Dockerfile` does **not** install `git`
  (`apt-get install` list: build-essential, gcc, wget, ca-certificates), and
  `python:3.11-slim` ships no `git` — **verified by running the base image**
  (`command -v git` → `NO_GIT`). `_run` returns `(None, str(exc))` on `OSError`, so in
  the canonical Render runtime `repository.remote` resolves to `None`.
* **Conclusion:** the disclosure is real and handler-level, and its effect in the
  canonical deployment is currently **masked by the absence of `git`** — not by any
  redaction. It becomes live the moment `git` is installed in the runtime image (a
  plausible change: `repository_state` also uses it for branch/HEAD) or the endpoint is
  served from a git-bearing host. That is a latent, not an active, exposure — recorded
  as such rather than overstated.

**Classification:** concrete security/privacy finding → **escalated**, per the
workstream's escalation rule. Repairing it means editing `lab/service.py` (and
possibly `lab/observatory/git.py`), which is a substrate change outside this slice's
UI scope; the UI boundary is hardened here instead.

**UI-boundary mitigation (this slice).** `labOverview.ts::redactRemote()` strips
userinfo before render and reports that it did; `LabOverviewSnapshot.tsx` renders only
the redacted value and never the raw field. Guarded by
`test_surface_never_renders_the_raw_remote`,
`test_redaction_is_documented_as_a_handler_gap_not_a_handler_guarantee`, and a negative
control proving the detector fires on a raw render. All tests use a **synthetic**
credential literal.

**Proposed follow-on (not executed here — needs authorization):** redact userinfo in
`repository_state()` itself, so the guarantee is the handler's rather than each
consumer's, and add a conformance test asserting no `@` userinfo appears in
`repository.remote`. That is a shared-substrate change and is left for the sovereign.

---

## 4. Non-collapses this surface preserves

| Non-collapse | Source | Reading |
|---|---|---|
| `observed` != authorized | `governance` declares a ceiling | `authority_granted: false`; the surface states the block is "not permissions this surface can confer" |
| `partial` != `observed` | handler sets `"partial" if errors else "observed"` | `reading_incomplete` + per-component `component_failures`; a failed section renders as unobserved, never as zero |
| absent governance != autonomy | handler may omit the block | a missing block reads "unknown ceiling", not "no ceiling" |
| `security.values_redacted` != blanket redaction | scoped to observations | `handler_redaction_scope: "security.observations only"` |

---

## 6. A second finding — the Workstream 4 guards executed in no CI job

While verifying this slice, I checked whether the new tests actually *run* in CI rather
than assuming the green checks implied it. They did not.

**Measured in the live run `38145078942` (this PR's own CI):**

```
CP10-B broader backend regression | python -m pytest tests/ -q
  ERROR tests/test_autonomy.py
  !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
  1 skipped, 1 warning, 1 error in 6.24s
```

The only step that ran a broad suite is `continue-on-error: true` **and** invokes a bare
`pytest tests/`, which aborts at the known CE-01 `weaver.autonomy` module-vs-package
collision — so it executed **zero** tests. `provider-routing.yml`, the workflow that does
use `--continue-on-collection-errors`, is path-filtered to `weaver/**`, `providers/**`,
`tests/architecture/**` and two named files, so it was never selected by this branch.
Net effect: **all 94 Workstream 4 test nodes — including the credential-redaction guard —
executed in no CI job.** The 13 green checks were real, but none of them ran these tests.

This is the repo's documented class (`tests/test_ci_suite_collection_continuation.py`: "a
guard no workflow executes is decoration"), in its adjacent, still-open form.

**Repair (in this slice):**

* Added a **judging** step (`CP10-C Workstream 4 read surfaces`, `id: w4_surfaces`, no
  `continue-on-error`) to `sg-02-fe-2-v.yml` that runs the Workstream 4 guards by name.
* Added those files to **both** `push` and `pull_request` path filters (they are asserted
  identical), so a change to a guard reaches the workflow that judges it.
* Added `test '${{ steps.w4_surfaces.outcome }}' = success` to the enforcement step, so the
  step's failure fails the job.
* Made the Node requirement honest: the projection is a `.ts` module executed directly,
  which needs native TypeScript stripping (node >= 23.6). `_node()` now skips **with a
  stated reason** below that version instead of failing opaquely — and
  `test_the_ci_node_version_can_strip_typescript` asserts the workflow's node (24.x) can,
  because otherwise the redaction guard would silently skip while the job stayed green.
* New guard `tests/test_prism_w4_ci_wiring.py` (27 tests) states the invariant generically
  over every Workstream 4 guard, with negative controls.

**The guard bit on first run** — 9 failures, of which 2 were real pre-existing gaps in this
branch (`test_prism_w4_lab_read_model.py` and `test_prism_w4_arkana_thread_history.py`, from
slices 02–05, were executed by no workflow either) and 1 was a defect in the guard's own
path matcher (comparing a full relative path against a basename). All three are repaired.

**Proven on the real workflow, not a synthetic copy.** Mutating `sg-02-fe-2-v.yml` to add
`continue-on-error: true` to the judging step → **10 failed**; dropping one trigger path from
the `push` filter only → **2 failed** (the coverage test and the filter-symmetry test). The
file was restored byte-identically (`cmp` clean) after each.

**The judging step immediately found a second defect — in this slice's own tests.** On the
first CI run carrying the new step (run `38146498321`), `CP10-C` reported
`1 failed, 166 passed`:

```
FAILED tests/test_prism_w4_lab_overview.py::test_the_handler_really_does_carry_userinfo_on_the_remote
  AssertionError: control premise not met: this environment's remote carries no userinfo
```

The assertion passed locally and failed in CI, because **whether `git remote get-url origin`
carries userinfo depends on how the clone was made**: this sandbox's remote URL embeds a
credential, while `actions/checkout` authenticates by HTTP header and leaves the remote clean.
The assertion was testing an *environment fact*, not the code — it is now a recorded
observation that skips with that reason, and the redaction tests (which feed synthetic
token-bearing views) do not depend on it. Verified in both directions: `12 passed` with a
credentialed remote, `11 passed, 1 skipped` with a clean one.

This is exactly the value the wiring was added for: the guard ran nowhere, and the first time
it ran it caught something a green local suite had hidden.

---

## 7. Changed paths

| Path | Role |
|---|---|
| `web/arkadia_console/src/components/lab/labOverview.ts` | pure projection incl. `redactRemote` |
| `web/arkadia_console/src/components/lab/LabOverviewSnapshot.tsx` | read-only renderer |
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | mounts the surface |
| `tests/test_prism_w4_lab_overview.py` | handler oracle + execution + redaction (12 tests) |
| `tests/test_lab_overview_contract.py` | read-only ceiling + redaction wiring (13 tests) |
| `tests/test_prism_w4_ci_wiring.py` | CI execution/selection/node guards (27 tests) |
| `.github/workflows/sg-02-fe-2-v.yml` | judging step, trigger paths, enforcement assertion |

`src/lib/endpoints.ts` (shared registry) is **not** edited: `labOverview` was already
declared. The workflow edit is CI wiring for this slice's own guards, not a shared shell,
route, endpoint or type registry.

---

## 8. Measured result

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

| Tree | Summary | Failing/error node set sha256 | Nodes |
|---|---|---|---|
| `main` `f390526a` | 27F / 2342P / 17S / 1E | `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` | 28 |
| branch (slices 06 + 07 + 08 + wiring) | 27F / 2463P / 17S / 1E | `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` | 28 |

`diff` on the sorted node sets is **empty**. `+121 passed` == `--collect-only`
18 + 19 + 16 + 16 + 12 + 13 + 27 = **121**.

* `tsc --noEmit && vite build` clean; `dist/assets/index-DtxIHBST.js` 83.37 kB.
* `api/main.py` untouched (2499 lines).

---

## 7. A pre-existing `main` failure observed on this PR — not caused by this branch

PR #432's `console-contract` check went red after PR #435 merged to `main` mid-flight
(adding `.github/workflows/prism-console-contract.yml`). It is **not** attributable to this
branch. Measured, not argued:

| Tree | `tests/test_prism_console_ci_wiring.py` |
|---|---|
| `main` `17988afd` | `2 failed, 17 passed, 2 skipped` |
| this branch `511bddea` | `2 failed, 17 passed, 2 skipped` |

`diff` on the two failing-node sets is empty; the failing nodes are
`test_a_workflow_executes_the_whole_console_contract` and
`test_wiring_workflow_is_a_complete_gate_that_selects_itself`, with the same messages.
The gate is red on `main`'s **own push runs** (`bcc6a8b4`, `7b378cec`), and green only on
`18a450d0` — the commit that introduced it.

**Cause, measured:** `_console_domain()` derives its domain from `git ls-files` by needle
match, so it grows whenever a new test mentions `web/arkadia_console` or
`api/frontend_routes`. `prism-console-contract.yml` enumerates its guards as a **fixed
list**, so three domain members added after #435 are not executed by it:
`test_knowledge_projects_boundary.py`, `test_knowledge_timeline_boundary.py`,
`test_prism_opportunity_entry_flow.py` (the last from #430). `_complete_gates()` therefore
returns nothing and the guard fails. This is the repo's own documented omission class, one
level up: not a missing allowlist entry but a *derived* domain vs a *restated* list.

**Why this is not repaired here.** `prism-console-contract.yml` and
`tests/test_prism_console_ci_wiring.py` are owned by the Workstream that introduced them
(`gate10/prism-console-contract-ci-gating-01`, PR #435), and `SHARED-CONTRACTS.md` §4 says
no agent edits another workstream's owned files or rebases another agent's branch. It is
reported for its owner.

**No coverage hole for this slice.** Six of this slice's test files do mention
`web/arkadia_console`, so they join that derived domain — but they are executed by the
judging step added in §6 (`CP10-C`), which is what actually gates them. The
console-contract gate's incompleteness therefore does not leave this slice unenforced. I
verified the two are independent: this branch's own run of the wiring guard **passes**
(the file is absent from its tree, so the assertion cannot fire).

---

## 8. Limitations / next

* The disclosure above is **escalated, not repaired** — the fix is a shared-substrate
  change requiring authorization.
* Nothing here authorizes acting on the substrate. The snapshot is an observation.
* Not claimed: merge, deployment, production parity, acceptance.

**Next bounded move:** continue the Workstream 4 read-surface thread; the automations
surface remains blocked on Workstream 1's `labAutomations` registry entry.

_This document was written by an AI agent (OpenHands) on behalf of the repository owner._
