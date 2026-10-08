# GATE-10 — CP10 allowlist omission: tracked `deploy/` surface

Gate: GATE-10 (Governed Execution) · CP10 mutation boundary
Pass: hourly bounded execution, 2026-10-07T22:06Z
Branch: `gate10/cp10-allowlist-deploy-surface-01`
Base main: `2c6f6f1e` (also the observed HEAD at start of pass)

## Objective

Restore `main` to green on the CP10 mutation-boundary gate and on the three
fitness tests that assert the allowlist is a complete inventory of tracked
surfaces, by admitting the tracked `deploy/` tree that PR #352 merged while it
was absent from the policy's `LEGIT` allowlist.

Explicit non-goals: no change to the CP10 denylist (`FORBID_V2` / `FORBID_V3`),
no change to any other allowlist entry, no change to the Lab substrate or its
route surface, no change to the N-ATLaS workflows, no baseline-debt repair.

## Evidence-backed defect

`deploy/n-atlas-server/` (`Dockerfile`, `app.py`, `requirements.txt`,
`README.md`) is tracked on `main` but is not matched by any rule in
`scripts/cp10_mutation_boundary_policy.py::LEGIT`. The generic `Dockerfile$`
rule matches root-level only; these files are nested.

Observed on the merge's own `push` run — **the gate failed on `main` itself**:

```
gh run view 37695297845   # sg-02-fe-2-v.yml, push, main, a27c6c80, conclusion=failure
Unexpected path outside legitimate repository surfaces:
Unexpected path outside legitimate surfaces: deploy/n-atlas-server/Dockerfile
##[error]Process completed with exit code 1.
```

The same omission is asserted by the fitness tests against the live tracked
corpus (`git ls-files`), so `main` @ `2c6f6f1e` carries three red nodes:

- `tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix`
- `tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface`
- `tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface`

This is the documented **allowlist-omission** class (`AGENTS.md` → "CP10 mutation
boundary — the allowlist is an inventory, not a filter"): the gate is not too
strict, the inventory is incomplete. The remediation the repository prescribes is
to add the tracked surface to the policy, not to weaken the gate.

## Change

One rule added to `LEGIT` in `scripts/cp10_mutation_boundary_policy.py`, with a
comment recording the omission class and the merge that exposed it:

```python
    r"|deploy/"
```

The change is additive and admit-only. It cannot remove an existing admission or
alter the denylist.

## Verification (measured, this environment)

Environment: `PYTHONPATH=<repo>/archive/legacy_python`, clone not shallow.

Policy decision — the admitted surface now passes, and the gate keeps its teeth:

| input | result | exit |
|---|---|---|
| `deploy/n-atlas-server/Dockerfile`, `…/app.py` | `Mutation boundary PASS` | 0 |
| `unknown_scratch/x.py` (negative control: unknown root) | `Unexpected path outside legitimate surfaces` | 1 |
| `web/public_prism/src/components/SolSpireExperienceV3.tsx` (negative control: denylist) | `Forbidden V3 dual shell` | 1 |

Fitness suite: `python -m pytest tests/test_m02a_ci_gate_integrity.py -q` →
**64 passed** (was 61 passed / 3 failed at `2c6f6f1e`).

## Baseline comparison

`main` @ `ff3f6d42` (before the #352 merge): 10 failed / 1760 passed / 21 skipped
/ 1 error; fingerprint `f3e73647…` / `92d344d0…` (11 nodes).
`main` @ `2c6f6f1e` (after the merge): 15 failed / 1 error; fingerprint
`a652f81e…` / `b584b2a6…` (16 nodes).

The delta is **exactly +5 nodes, all introduced by the #352 merge** (zero nodes
disappeared; the recorded `tests/fixtures/baseline_node_set.txt` — 10 nodes — is a
strict subset of both live runs):

| new node | cause | addressed here |
|---|---|---|
| `test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix` | `deploy/` omission | yes |
| `test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface` | `deploy/` omission | yes |
| `test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface` | `deploy/` omission | yes |
| `test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` | 3 new N-ATLaS mutating routes not in `ALLOWED_MUTATION_ENDPOINTS` | **no — see below** |
| `test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]` | new workflow path filter omits its own file | **no — see below** |

This PR is expected to reduce the failure node set by exactly 3
(16 → 13 nodes) and introduce nothing.

## Boundary classification of the two held nodes

Both remaining nodes concern the N-ATLaS developer-lab surface merged by #352.
They are **not** a new repository/authority mutation path and **not** a HARD STOP,
but they are also **not** in this workstream's envelope:

- The three new Lab routes (`/engineering/n-atlas/{test-session,run,catalog}`) call
  `runtime.record_authorization(...)`, which is the *human* authorization path
  (`originated_by` is fixed to `"human"`; the store rejects anything else) — the
  same primitive the pre-existing `/sessions/{id}/authorize` route already used
  (call sites `api/lab_routes.py:176` and `:403`). No repository/git/subprocess
  surface was introduced (`lab/engineering_lab/natlas.py` and `gateway.py` use
  only `urllib.request`). The test that fails is an inventory test pinning the set
  of mutating endpoints, not a boundary assertion.
- The N-ATLaS workflow path filter omits `.github/workflows/n-atlas-developer-lab.yml`,
  which is the trigger-coverage invariant (a gate that runs pytest must be selected
  by its own file).

Widening either pin is a governance/CI-surface decision about the N-ATLaS
workstream and is therefore **recorded as proposed work**, not executed here
(`AGENTS.md` §3: do not expand scope to repair adjacent failures). The substantive
question — whether three new Lab mutation endpoints should be added to
`ALLOWED_MUTATION_ENDPOINTS` — is left for sovereign/owner review.

## Authorization boundary

Repository-source change only, on a dedicated branch, via pull request. No merge,
no push to `main`, no authority-model change, no scope expansion. Human merge
authority is required.

---

# Pass 2 — composition onto current main (`f96d5fd2`) and refined classification

Pass: hourly bounded execution, 2026-10-07T23:0xZ
Base main at start of pass: `f96d5fd2` ("Fix N-ATLaS Lab public tester onboarding (#353)")
Branch head after composition: `c9ef3664` (merge of `f96d5fd2` into `57e4716c`)

## Why the branch was composed with current main

`main` advanced by one commit (`f96d5fd2`, PR #353) after this branch was created.
The branch's merge-base with `main` was `2c6f6f1e`, which **is** an ancestor of
`f96d5fd2`, so GitHub's three-dot diff was already the correct 3-file change set —
but CI would have judged a tree that did not contain #353. Merging `main` into the
branch makes CI test the true composition and keeps the PR mergeable.

The merge was conflict-free: this branch touches `scripts/cp10_mutation_boundary_policy.py`,
`AGENTS.md` and this evidence doc; #353 touched `api/auth.py`, `api/lab_routes.py`,
`tests/test_natlas_developer_lab.py`, `web/console/src/api/client.ts`,
`web/console/src/surfaces/NAtlasTester.tsx`. Disjoint file sets, so no hand
resolution — and therefore no merge-loss risk (see `AGENTS.md` → "Merge-loss
forensics").

## Verification on the composed tree (measured, this environment)

- `python -m pytest tests/test_m02a_ci_gate_integrity.py -q` → **64 passed**
  (was 61 passed / 3 failed at `f96d5fd2`).
- `python3 scripts/cp10_mutation_boundary_policy.py --judge` on the branch's own
  diff (`AGENTS.md`, this evidence doc, `scripts/cp10_mutation_boundary_policy.py`)
  → `Mutation boundary PASS`, **exit 0**.
- Negative controls re-run on the composed tree and still reject:
  unknown root → exit 1; `SolSpireExperienceV3.tsx` → exit 1.
  `deploy/n-atlas-server/*` → PASS (exit 0, newly admitted).

## Full-suite node-identity delta (the load-bearing measurement)

Both runs: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`, this
environment. `-rEf` is required — the documented `-rf` suppresses pytest's `ERROR`
summary lines and yields a subset fingerprint (`AGENTS.md` → "Baseline fingerprint").

| tree | result | node set |
|---|---|---|
| `main` @ `f96d5fd2` | 16 failed / 1770 passed / 22 skipped / 1 error | 17 nodes · `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` |
| this branch @ `c9ef3664` | 13 failed / 1773 passed / 22 skipped / 1 error | 14 nodes · `0143dc4df4291b848fa00ca59ddca426985c0c7b0f77d9f4245c951c87793e38` |

Removed (3), all `tests/test_m02a_ci_gate_integrity.py` allowlist-inventory nodes
repaired by this PR. **Introduced: zero** (`comm -13` empty). The remaining 14
nodes are baseline debt plus the two held #353 nodes below; none is attributable to
this change.

## Corrected classification of the two held #353 nodes

The Pass 1 note above classified both held nodes as "not a HARD STOP". Re-measured
on `f96d5fd2`, that is **too weak for one of them** and is superseded here.

Both nodes are introduced by #353 (verified: `git show 2c6f6f1e:api/lab_routes.py`
contains zero `n-atlas` occurrences; `f96d5fd2` adds the routes):

1. `test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set`
   — two new mutating routes, `/api/lab/engineering/n-atlas/test-session` and
   `/api/lab/engineering/n-atlas/run`, are absent from `ALLOWED_MUTATION_ENDPOINTS`.
   The endpoints are Lab-state operations (no git/subprocess surface), so this is an
   inventory-completion question, not a boundary breach.

2. `test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated`
   — **this is an authentication-boundary change.** #353 replaced the router-level
   `dependencies=[Depends(require_auth)]` with `Depends(require_lab_auth)`, and
   `require_lab_auth` returns `None` — *no authentication at all* — for every path in
   `_PUBLIC_NATLAS_PATHS`:

   ```python
   _PUBLIC_NATLAS_PATHS = {
       "/api/lab/engineering/n-atlas/catalog",
       "/api/lab/engineering/n-atlas/test-session",
   }

   async def require_lab_auth(request: Request) -> None:
       if request.url.path in _PUBLIC_NATLAS_PATHS:
           return None            # <- unauthenticated
       await require_auth(request)
   ```

   `/api/lab/engineering/n-atlas/test-session` is a **POST** that mints a signed
   `natlas-tester.` capability token (new credential type,
   `api/auth.py::mint_natlas_tester_token`) and records a human authorization via
   `runtime.record_authorization(...)`. `require_auth` additionally gained an
   acceptance branch for that token type (`api/auth.py:454`).

## Why this is HELD, not repaired here

The change is **intentional** — the sovereign merged #353, whose title is "Fix
N-ATLaS Lab public tester onboarding". So this is not an accidental regression to
be reverted. It is a tension between a human-authorized design and an older guard
test that pins the previous design, and it engages the contract's own HARD STOP
list ("a new authorization path appears", "identity boundary changes unexpectedly").
It also contradicts the repository's standing invariant (`AGENTS.md`): *"THE LAB IS
OWNER-ONLY. AUTHENTICATION := SOVEREIGN_IDENTITY_ONLY."*

Resolving it requires a sovereign choice between two options, neither of which an
agent may take unilaterally:

- **A.** Accept the public tester path as designed, and update the guard test +
  `ALLOWED_MUTATION_ENDPOINTS` to reflect it (with the public surface narrowed and
  the capability's scope explicitly bounded); or
- **B.** Keep the Lab owner-only, and re-express tester onboarding behind
  authentication (or a separate non-Lab surface).

Editing the guard test to make it pass would weaken the boundary; editing
`api/lab_routes.py` to restore `require_auth` would silently revert sovereign-approved
design. Both are forbidden without authorization. **Not touched in this PR.**

## Pass 2 authorization boundary

Repository-source change only, on a dedicated branch, via pull request. No merge, no
push to `main`, no force-push, no authority-model change, no scope expansion. The
`api/auth.py` / `api/lab_routes.py` boundary question above is reported, not resolved.
Human merge authority is required.
