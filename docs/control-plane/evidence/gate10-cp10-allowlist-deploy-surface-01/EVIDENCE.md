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

## Pass 2 — PR linkage and measured node sets

- **PR #354** — `gate10/cp10-allowlist-deploy-surface-01`, head `f7c212bd`, base `f96d5fd2`.
  This is the CP10 allowlist repair. (An earlier revision of this section cited head
  `7b9f3309`; that was the head at the time of writing. `7b9f3309` is an ancestor of
  `f7c212bd` and the advance is **docs-only** — `git diff --name-only 7b9f3309 f7c212bd`
  returns only this evidence doc — so the node-set measurements below bind to the current
  head unchanged. Corrected here rather than left standing.)
- **PR #355** — `gate10/n-atlas-workflow-self-trigger-01`, head `73104fdf`, base `f96d5fd2`.
  Isolated bounded branch for held item 3 (n-atlas workflow self-selection), because this PR
  declares "no change to the N-ATLaS workflows" as a non-goal and contract §11 requires
  non-consequential follow-on work to be isolated rather than widening scope. One additive
  trigger-path entry; `tests/test_ci_gate_trigger_coverage.py` **48 passed** (was 1F/47P);
  CP10 judge on its diff → PASS, exit 0.

Measured node sets, `pytest tests/ -q -rEf --continue-on-collection-errors` (the `-rEf` is
required — `-rf` alone suppresses pytest's `ERROR` summary lines and yields a subset):

| tree | result | nodes | sha256 |
|---|---|---|---|
| `main` @ `f96d5fd2` | 16F / 1770P / 22S / 1E | 17 | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` |
| #354 @ `7b9f3309` | 13F / 1773P / 22S / 1E | 14 | `0143dc4df4291b848fa00ca59ddca426985c0c7b0f77d9f4245c951c87793e38` |

`main(17) − branch(14)` = the 3 CP10 completeness nodes → fixed.
`branch(14) − main(17)` = ∅ → nothing introduced.

Composition onto `main` was conflict-free: #354's file set and #353's file set are disjoint,
so the merge had no hand resolution and carries no merge-loss risk.

---

# Pass 3 — reconciliation of the "main is red on CP10" premise, and measured composition

Pass: hourly bounded execution, 2026-10-07T23:0xZ
Base main: `f96d5fd2`. #354 head: `f7c212bd`. #355 head: `73104fdf`.

## Reconciliation: the premise does reproduce — the earlier run was mis-scoped

Pass 2 recorded an unresolved item: *"the judge on `main`'s tracked corpus (f96d5fd2) also
returned PASS (main_judge_exit=0), so the 'main is red on CP10' premise did not reproduce."*

That observation was an artefact of **which judge script was executed against which corpus**.
A judge is only the gate for the tree that *carries* it:

| judge script | corpus | result | exit |
|---|---|---|---|
| `f96d5fd2` (main's own policy) | `f96d5fd2` (main's own tree) | `Unexpected path … deploy/n-atlas-server/Dockerfile` | **1** |
| `f7c212bd` (branch policy) | `f96d5fd2` (main's tree) | `Mutation boundary PASS` | 0 |
| `f7c212bd` (branch policy) | `f7c212bd` (branch tree) | `Mutation boundary PASS` | 0 |
| `73104fdf` (#355 policy — `deploy/` not admitted) | `73104fdf` (#355 tree) | `Unexpected path … deploy/n-atlas-server/Dockerfile` | **1** |

The Pass 2 run executed the **branch's already-repaired policy** against main's corpus, which
is why it passed: the branch policy admits `deploy/`, so it cannot reproduce the defect it
repairs. Main's own script on main's own tree is red — **exit 1**, failing on
`deploy/n-atlas-server/Dockerfile`, the first of the four `deploy/n-atlas-server/*` files.
Corpora here are derived directly from git (`git ls-tree -r --name-only <rev>`), not from a
working tree, so the main corpus contains no branch-only paths.

## Precise scope of "red on main": the gate judges a RANGE, not a tree

This distinction was understated in the first revision of this pass and is corrected here.

`sg-02-fe-2-v.yml` step `mutation` does **not** judge a tree. It calls
`python scripts/cp10_mutation_boundary_policy.py --resolve-range` and then judges
`git diff --name-only "$base" HEAD` — `pull_request.base.sha` for a PR (the full PR range),
`push.before` for a push. A tracked path that no commit in the range touched is **not judged**,
even though it is present in the tree.

The live CI record shows exactly that:

| main push | run | CP10 range | result |
|---|---|---|---|
| `a27c6c80` (#352, added `deploy/n-atlas-server/`) | 37695297845 | `…a27c6c80` — includes the new path | **failure** — `Unexpected path outside legitimate surfaces: deploy/n-atlas-server/Dockerfile` |
| `f96d5fd2` (#353) | 37697169171 | `2c6f6f1e..HEAD` — `api/auth.py`, `api/lab_routes.py`, `tests/test_natlas_developer_lab.py`, `web/console/src/**` | **success** |

So the executed gate is **green on main at `f96d5fd2`**, because that push's range contained no
`deploy/` path. The red state on main is therefore:

- **Real and historical** on the merge that introduced the surface — `a27c6c80`, run
  37695297845, conclusion `failure`. That is the defect.
- **Latent** on main HEAD: any future push whose range includes a `deploy/` path is rejected,
  and any PR whose range includes one is rejected. #354 removes this latent red by admitting
  the surface.
- **Red now, range-independently,** through the fitness tests. `test_m02a_ci_gate_integrity.py`
  asserts the *tree* invariant against `git ls-files` (`test_allowlist_admits_every_tracked_top_level_prefix`,
  `test_allowlist_covers_every_tracked_surface`, `test_delegated_verdict_admits_every_tracked_surface`),
  so those three nodes are red on main's HEAD tree even though main's HEAD push was green.

An earlier revision of this pass said only "main's own script on main's own tree exits 1", which
is true of the fitness-test invariant but must not be read as "the executed gate is red on main
HEAD". It is not; it is red at `a27c6c80` and latent thereafter. Both readings support the same
remedy, but the executed decision is the one CI acts on.

The premise stands. No correction to the Pass 1 defect claim is needed.

## The two PRs do not individually restore `main` to green — they compose

Measured on the four target nodes
(`tests/test_m02a_ci_gate_integrity.py` + `tests/test_ci_gate_trigger_coverage.py`):

| tree | result | remaining red |
|---|---|---|
| `main` @ `f96d5fd2` | 4 failed / 108 passed | 3 allowlist-inventory + 1 trigger-coverage |
| `#354` @ `f7c212bd` alone | 1 failed / 111 passed | trigger-coverage only |
| `#355` @ `73104fdf` alone | 3 failed / 109 passed | allowlist-inventory only |
| **composed (#355 + #354)** | **0 failed / 115 passed** | **none** |

`git apply --3way` of both PR diffs onto `f96d5fd2` applied cleanly (the two PRs share no
file), so there is no textual conflict and no merge-loss risk. **Both PRs must land for the
CP10 gate and its fitness tests to be green on `main`; neither alone suffices.** Merge order
is immaterial — the file sets are disjoint and the trigger-coverage and allowlist nodes are
independent.

## Composed full-suite node-identity delta

`python -m pytest tests/ -q -rEf --continue-on-collection-errors`, this environment.

| tree | result | nodes | outcomes fingerprint |
|---|---|---|---|
| `main` @ `f96d5fd2` | 16F / 1770P / 22S / 1E | 17 | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` |
| composed (#355 + #354) | 12F / 1774P / 22S / 1E | 13 | `bae53864cab9d99b9a3b0a0a9eddacb7fa9f092809d3b8508abdb3abf58d9a6f` |

Removed (4): the three `test_m02a_ci_gate_integrity` allowlist-inventory nodes and
`test_ci_gate_trigger_coverage::test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]`.
**Introduced: zero.** The remaining 13 nodes are baseline debt plus the two held #353 Lab
nodes (`test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated`,
`::test_lab_mutation_endpoints_are_exactly_the_lab_state_set`) — the authentication-boundary
question recorded above and **not** touched here.

`tests/fixtures/baseline_node_set.txt` (10 nodes) is a strict subset of main's live 17-node
set, confirmed by set difference — consistent with its documented role as a partial ledger.

## Trigger-path note — corrected

An earlier revision of this section claimed the docs-only commit "does not re-trigger the CP10
job". **That was wrong, and it was wrong in the direction of assuming an untested gate.**

`sg-02-fe-2-v.yml` does not list `docs/**` or `AGENTS.md` in its `paths:` filters, but the
filter is evaluated against the **whole PR diff** on `pull_request`, and the PR diff contains
`scripts/cp10_mutation_boundary_policy.py` (a listed path). SG-02 therefore ran on the docs-only
head as well, and passed:

| head | SG-02-FE.2-V run | conclusion |
|---|---|---|
| `7b9f3309` | 37709354794 | success |
| `f7c212bd` | 37710023311 | success |
| `5f52ddab` (this docs-only commit) | 37711825051 | success |

So the CP10 evidence for this branch is the **green run at the current head**, not merely at
`f7c212bd`. The current head `e90a5769` ran SG-02 in
run 37712478063 with range `f96d5fd2..HEAD` and the boundary step printed
`Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)`.

## Vercel status is pre-existing, not attributable

Both Vercel commit statuses read `failure / Deployment rate limited - retry in 24 hours.` on
`main` at `f96d5fd2`, identically to this branch head. Provider rate limit, not this change.
Recorded so a later pass does not attribute it to #354.
 Corrected because "the gate did not run" is exactly the kind of claim that must not
be left standing — the honest statement is that it ran and passed.

## Pass 3 authorization boundary

Evidence-documentation only, on the existing dedicated branch, via the existing PR #354. No
policy change, no denylist change, no test change, no merge, no push to `main`, no
force-push, no authority-model change, no scope expansion. The
`api/auth.py` / `api/lab_routes.py` boundary question remains **reported, not resolved**.
Human merge authority is required.

## Deterministic next action

- **Current state:** #354 (`f7c212bd`) and #355 (`73104fdf`) both open, both `CLEAN` /
  `MERGEABLE`, both measured, both `READY FOR MERGE` for their own bounded scope. The CP10
  gate and its fitness tests go green only when **both** are merged. No merge performed; no
  push to `main`.
- **Blockers:** none for either PR's own scope. The two held `test_engineering_lab_api` nodes
  are a **separate proposed workstream** requiring a sovereign choice (accept the public
  tester path and update the guard + `ALLOWED_MUTATION_ENDPOINTS`, or keep the Lab owner-only
  and re-express tester onboarding behind authentication).
- **Authorized action:** sovereign review and merge of #354 and #355.
- **Forbidden:** merging, pushing to `main`, editing `api/lab_routes.py` / `api/auth.py`,
  editing the `test_engineering_lab_api` guard, changing `ALLOWED_MUTATION_ENDPOINTS` or
  `REGISTERED_ARCHITECTURAL_DEBT`.
- **Completion condition:** #354 and #355 merged by the sovereign, then a fresh pass
  reconstructs `main` and re-derives the node set from live evidence.
