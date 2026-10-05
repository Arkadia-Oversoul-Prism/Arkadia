# EVIDENCE — gate-hygiene/independent-queue-verification-06

Bounded objective: independently re-derive, from live repository and CI evidence, the
verification state of the open PR cluster **#267 / #268 / #270 / #271 / #273 / #274**,
and record the defects and CI-gate coverage that the earlier gate-hygiene passes
(PR #267, PR #271) did not capture.

This pass is **evidence only**. No source, test, or policy change. No merge. No push to
`main`. No PR is modified. Every claim below was re-measured on the exact revisions
named; nothing is carried over from a previous pass's prose.

## 1. Provenance

| Item | Value |
| --- | --- |
| Repository | `Arkadia-Oversoul-Prism/Arkadia` |
| Observation time (UTC) | 2026-10-04T22:06–22:45 |
| LIVE_MAIN (this pass) | `89f9e78063f9c2a9a9931e305a2195035d205309` |
| Previous-pass anchor | `ca67b006e57c0247d1db0f9d337ed34cc0a51cce` (ancestor of live main) |
| Branch | `gate-hygiene/independent-queue-verification-06` @ `89f9e78` |
| Working tree at branch point | clean (`git status --porcelain` empty) |

`git fetch origin main` re-run during the pass. Live `main` advanced **3 commits** past
`ca67b006`:

```
89f9e78 rebuild(mie): restore Web Lab from native gate baseline   <- LIVE_MAIN
ca67b00 fix(mie): repair history repeat / duplicate gate labels
0eae7f0 repair Prism UI repeat
a5adf9f add Prism UI entry surface
58b981d place MIE in Prism UI
e3b89f2 label Prism Web Lab as Gate 05
```

`ca67b006` remains an ancestor of live `main` (`git merge-base --is-ancestor` → true), so
the PR #271 evidence stays bound to a real revision of history.

**Correction of a carried-over claim.** The prior run's work-log stated the context anchor
`89f9e78` was STALE and that `main` had advanced to `ca67b00`. That is backwards: the
re-measurement above shows `89f9e78` **is** live `main` and `ca67b00` is its ancestor.
Anchor drift was inferred, not measured. Recorded here so the next pass does not inherit it.

## 2. Baseline test-debt fingerprint (measured at the START of this pass)

Full suite on live `main` `89f9e78`, `-q -rEf --continue-on-collection-errors`,
`PYTHONPATH=<repo>/archive/legacy_python`, `python = /workspace/project/.venv/bin/python`:

```
9 failed, 1425 passed, 18 skipped, 1 error in 124.94s
```

Failing/error node set (10 nodes, `scripts/baseline_fingerprint.py`):

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_compress_to_choices
```

```
outcomes fingerprint: 9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38
ids fingerprint     : 124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f
```

This is **byte-identical** to the canonical pair recorded for `1b7c089` / `296d741` /
`ca67b006` in PR #271 §2 — the node set has not moved across four `main` revisions. The
passed count rose (1422 → 1425) because the later `main` commits added their own tests;
only the failing/error **node set** is load-bearing and it is unchanged. The baseline is
reproducible, and the tests below are attributed against this set by **identity, never by
count**.

## 3. Open-PR inventory (live, at observation time)

Six PRs open. Nothing else. All bases are ancestors of live `main`.

| PR | Title | Head SHA | Base | Files | Head CI |
| --- | --- | --- | --- | --- | --- |
| #267 | gate-hygiene: independently verify open PR cluster #262–#266 | `51b0a3f4` | `296d741b` | 2 docs | secret-scan ✅ |
| #268 | feat(console): complete governed Arkadia Console | `ab427481` | `296d741b` | 1 doc | secret-scan ✅ |
| #270 | feat: add project opportunity radar to Weaver field | `1a264efe` | `296d741b` | 5 (2 code) | 3/3 ✅ |
| #271 | docs(gate-hygiene): post-merge verification of #262–#266 movement | `6598c26d` | `ca67b006` | 2 docs | secret-scan ✅ |
| #273 | feat: fuse Weaver and Canvas into Arkana Weaver | `93ea1954` | `296d741b` | 5 (4 code) | **❌ 2 of 3** |
| #274 | Arcana: canonical semantic conversation threads | `0239ff11` | `296d741b` | 3 (2 code) | 2/2 ✅ |

**Baseline-fingerprint guard on the inventory itself.** The abbreviated-SHA trap recorded
in the repo memory is real and was hit and corrected in this pass: querying CI with
`?head_sha=1a264efe72d0` returned `total_count: 0` for PR #270, while the **full** 40-char
SHA returned **3** runs. Every CI row above was taken with the full SHA. A `0` is read as
*unproven*, not *absent*.

## 4. Defect A — PR #270: `ImportError` on the module `api/main.py` mounts (silent route loss)

**Status: CONFIRMED, re-derived from scratch on the PR's own tree.** The carried-over
claim was re-proved rather than accepted.

`solspire/buyer_recon_router.py:14` on PR #270's head:

```python
from api.auth import require_auth, require_project_owner
```

`require_project_owner` is **not defined in `api/auth.py`** — `grep -n
require_project_owner api/auth.py` returns no match (exit 1). It is defined once, at
`solspire/console_router.py:68`:

```python
async def require_project_owner(project_id: str, user: dict = Depends(require_auth)) -> dict:
```

Empirical import test on the PR's own worktree (`/tmp/wt270`):

```
api.auth:                       IMPORT OK
solspire.buyer_recon_router:    IMPORT FAILED -> ImportError: cannot import name 'require_project_owner' from 'api.auth'
solspire.console_router:        IMPORT FAILED -> ImportError: cannot import name 'require_project_owner' from 'api.auth'
```

`solspire/console_router.py:45` imports `buyer_recon_router` and `:64` includes it, so the
ImportError propagates up to the console router itself.

### 4.1 Blast radius — the mount is silently skipped

`api/main.py:333` mounts the console router inside a broad `try/except` that only logs a
warning:

```python
try:
    from solspire.console_router import router as _solspire_router
    app.include_router(_solspire_router)
    logger.info("[SOLSPIRE] Console kernel router mounted at /solspire")
except Exception as _ss_err:
    logger.warning(f"[SOLSPIRE] Console router mount skipped: {_ss_err}")
```

On `main` the same import succeeds and the router carries **80 routes**. Merging PR #270 as
it stands would therefore drop all 80 `/solspire` routes from the running app while the
process still boots — a silent production regression, not a crash.

### 4.2 A `main`-passing test already catches it (negative control run)

`tests/test_solspire_ownership.py:42` imports the router directly, so it is a real
detector — not a source-level string assertion:

| Tree | `tests/test_solspire_ownership.py` |
| --- | --- |
| `main` `89f9e78` (control) | **51 passed** |
| PR #270 head `1a264efe` | **collection ERROR** — `Interrupted: 1 error during collection` |

Classification: **the defect is caught by the repository's own suite; it is not caught by
CI.** The three workflows that ran on PR #270's head — `security-secret-scan`,
`Weaver MVP2 validation`, `SG-02-FE.2-V` — all report **success**. `SG-02-FE.2-V` is
path-filtered to `web/public_prism/**`, `spiral_grove/**`, `lab/**`, `api/lab_routes.py`
and named test files; it does not run the SolSpire Python tests. This PR touches only two
Python files plus frontend, so no gate exercised the import. This is a **gate-coverage
gap**, recorded as such — a green head is scoped to the checks that actually ran.

## 5. Defect B — PR #273: build-breaking import mismatch, and a guard test that cannot pass

**Status: CONFIRMED on CI logs and on the PR's own tree.**

PR #273 adds `web/public_prism/src/components/solspire/**Arcana**WeaverCanvas.tsx` (and
`arcana-weaver.css`), but `src/pages/ProjectDashboard.tsx` imports the module as
`**Arkana**WeaverCanvas`:

```
error during build:
Could not resolve "../components/solspire/ArkanaWeaverCanvas" from "src/pages/ProjectDashboard.tsx"
```

The same one-letter divergence is baked into the PR's own guard test,
`tests/test_arcana_weaver_fusion.py`:

```python
CANVAS = ROOT / "web/public_prism/src/components/solspire/ArkanaWeaverCanvas.tsx"
...
assert "ArkanaWeaverCanvas" in dashboard
```

Measured on PR #273's head worktree:

```
FileNotFoundError: '/tmp/wt273/web/public_prism/src/components/solspire/ArkanaWeaverCanvas.tsx'
FAILED tests/test_arcana_weaver_fusion.py::test_arcana_weaver_fuses_project_canvas_weaver_and_arkana_runtime
1 failed
```

So PR #273 fails **two independent ways**: the Vite build cannot resolve the import, and
its own regression test cannot find the file it asserts on. CI agrees —
`SG-02-FE.2-V` job `validate` fails at the steps **Build Prism** and **Enforce CP10
executable gates** (run `37237565057`). The sibling workflow `Weaver (MVP2 validation)`
also failed on the same head.

This is the intended behaviour of the CP10 / build gate: the failure is visible in CI, the
PR is not mergeable, and no `main` regression results. Recorded as **caught**, not as a
gate gap.

## 6. PRs with no executable head gate

- **#267, #268, #271** are documentation-only (2, 1, 2 files respectively, all under
  `docs/control-plane/evidence/`). Only `security-secret-scan` ran on each head, and each
  passed. Their bases (`296d741b`, `ca67b006`) are ancestors of live `main`. There is no
  code to regress, and the CP10 boundary policy admits the paths (verified locally for the
  #06 path in §7). **No defect found.**
- **#268** is one document (`console-complete-build/OVERNIGHT-BUILD.md`) that *describes*
  a G11→G12→G14 Console build plan. It contains no implementation, so its stated
  objectives are **NOT CLAIMED** — the document is a plan, not evidence of the gates it
  names.
- **#274** passes its own guard tests (15 passed: `test_cal05_first_class_threads.py`,
  `test_solspire_project_instantiation_ui.py`, `test_solariun_thread_navigation_01.py`) and
  both head workflows are green. It removes a hardcoded literal thread id and reads the
  real thread `uuid` from the API (`api/commune_threads.py::_public_thread` does emit
  `uuid`), with `GET /{thread_uuid}/messages` present. **No defect found** within this
  pass's bounded scope; note that the repo's frontend tests are source-level string
  assertions, so "green" here means "the pinned literals still hold", not "the UI was
  exercised at runtime".

## 7. Protected surfaces and policy boundary

| Check | Command | Result |
| --- | --- | --- |
| Boot-code compile | `python3 -m py_compile api/main.py` | **OK** (2582 lines, under the 2600 budget) |
| CP10 boundary (this pass's path) | `cp10_mutation_boundary_policy.py --judge` | **PASS** (exit 0) |
| Ancestry, PR #267 base | `git merge-base --is-ancestor 296d741b 89f9e78` | **true** |
| Ancestry, PR #271 base | `git merge-base --is-ancestor ca67b006 89f9e78` | **true** |

CP10 judge input was exactly the two paths this pass adds:
`docs/control-plane/evidence/gate-hygiene-independent-queue-verification-06/{EVIDENCE.md,WORKSTREAM_STATE.md}`.
Verdict: `Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)`.

## 8. Classification summary

| Item | Classification |
| --- | --- |
| `main` baseline fingerprint | **VERIFIED** — identical node set to the recorded canonical pair |
| PR #270 ImportError + 80-route loss | **CONFIRMED DEFECT** (caught by suite, not by CI) |
| PR #270 CI green | **OBSERVED** — scoped to 3 workflows that do not run SolSpire tests |
| PR #273 build break + guard-test mismatch | **CONFIRMED DEFECT** (caught by CI) |
| PR #274 | **NO DEFECT FOUND** in bounded scope; runtime UI **NOT CLAIMED** |
| PRs #267 / #268 / #271 | **NO DEFECT FOUND** (documentation-only) |
| Gate-2 production parity | **BLOCKED** — unchanged; needs a Vercel credential / Deployment Protection relaxation (see `gate-hygiene-gate2-production-parity-02`) |

## 9. Required sovereign action

No merge of PR #270 or PR #273 in their current form. The smallest corrective actions,
neither of which this evidence pass performs:

- **#270** — either move `require_project_owner` into `api/auth.py` (and export it), or
  import it from `solspire.console_router` where it is defined. A test that imports
  `solspire.console_router` must run in a gate that covers Python changes, or the same
  silent-mount failure will recur on a future PR.
- **#273** — reconcile the `Arkana` / `Arcana` spelling across
  `ProjectDashboard.tsx`, the new component file, and `tests/test_arcana_weaver_fusion.py`.

## 10. Next bounded task (proposed, not executed)

`gate-hygiene/ci-gate-coverage-01` — determine whether a workflow should run the SolSpire
Python test subset on PRs that touch `solspire/**` or `api/**`, given that PR #270 reached
three green checks with a collection-breaking import. This is a **proposal only**; changing
CI trigger scope touches the governed gate surface and needs sovereign authorization.

## 11. Limits of this pass

- This is **source + CI evidence**. No frontend build was run locally for #273 or #274;
  the build failure is quoted from the CI job log for run `37237565057`.
- No runtime/device observation was performed. Nothing here is a production claim.
- No PR was modified, no merge performed, no push to `main`.
