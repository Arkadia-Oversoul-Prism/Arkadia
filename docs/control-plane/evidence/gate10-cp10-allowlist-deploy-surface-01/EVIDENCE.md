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

> **CORRECTED -- see Pass 4 (below).** This verifier is **false**: `2c6f6f1e`
> contains **three** `n-atlas` routes (lines 362/427/440). Only the *authentication*
> node is #353; the *mutating-endpoint inventory* node is #352 (`a27c6c80`), inherited
> by #353. The original sentence is retained as the record of what was claimed; the
> corrected attribution is in Pass 4.

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

---

# Pass 4 — correction: the two held nodes are NOT both attributable to #353

Pass: hourly bounded execution, 2026-10-08
Base main at start of pass: `f96d5fd2` ("Fix N-ATLaS Lab public tester onboarding (#353)")
Branch head before this pass: `04662703`
Working tree: detached HEAD on `04662703`, branch `gate10/cp10-allowlist-deploy-surface-01`

## What this pass corrects

Pass 2/3 recorded, in two places, the attribution:

> "Both nodes are introduced by #353 (verified: `git show 2c6f6f1e:api/lab_routes.py`
> contains zero `n-atlas` occurrences; `f96d5fd2` adds the routes)."

**That parenthetical verifier is false.** `git show 2c6f6f1e:api/lab_routes.py` contains
**three** `n-atlas` occurrences, not zero:

| line | route |
|---|---|
| `362` | `@router.post("/engineering/n-atlas/test-session")` |
| `427` | `@router.get("/engineering/n-atlas/catalog")` |
| `440` | `@router.post("/engineering/n-atlas/run")` |

It was never true. The measurement that produced "zero" was taken against the wrong
revision or the wrong file; either way the recorded verification does not reproduce, and
an evidence doc must not keep a non-reproducible verifier standing. This is a correction
of record, not a change to any classification below it.

## Re-derived attribution (measured this pass)

The two held `tests/test_engineering_lab_api.py` nodes have **two different origins**.
They are not a single #353 change.

| node | origin | revision evidence |
|---|---|---|
| `::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` | **#352** (`a27c6c80`, "Merge pull request #352 … feat/n-atlas-developer-lab") | `git merge-base --is-ancestor a27c6c80 2c6f6f1e` → **true**; the three `n-atlas` routes are already present at `2c6f6f1e` (lines 362/427/440), and `2c6f6f1e` is the merge-base of the branch with `main` |
| `::test_lab_router_is_read_only_and_authenticated` | **#353** (`f96d5fd2`) | `git log -S"require_lab_auth" -- api/lab_routes.py` returns exactly one commit: `f96d5fd2`. `2c6f6f1e` still reads `dependencies=[Depends(require_auth)]` at line 48; `f96d5fd2` replaces it with `require_lab_auth` + `_PUBLIC_NATLAS_PATHS` |

So the correction is narrow and material: the **authentication-boundary** node (node B) is
a #353 change, as recorded; the **mutating-endpoint inventory** node (node A) is a #352
change that #353 inherited. Calling both "#353" over-attributed node A to the wrong PR.

`git show 2c6f6f1e:api/lab_routes.py:48` and `git show f96d5fd2:api/lab_routes.py:48`
respectively, side by side:

```python
# 2c6f6f1e — node A's routes already exist, router still requires auth
router = APIRouter(prefix="/api/lab", tags=["Engineering Lab"], dependencies=[Depends(require_auth)])

# f96d5fd2 — node B's change: router auth is bypassed for two public paths
_PUBLIC_NATLAS_PATHS = {
    "/api/lab/engineering/n-atlas/catalog",
    "/api/lab/engineering/n-atlas/test-session",
}
async def require_lab_auth(request: Request) -> None:
    if request.url.path in _PUBLIC_NATLAS_PATHS:
        return None
    await require_auth(request)
```

## Node-set re-measurement, end to end (this environment)

All runs: `python -m pytest tests/ -q -rEf --continue-on-collection-errors -p no:randomly`.
Fingerprints via `scripts/baseline_fingerprint.py` (outcomes convention).

| tree | result | nodes | outcomes fingerprint |
|---|---|---|---|
| `pre-#352` `ff3f6d42` | 5 passed (target file only) | — | — |
| `2c6f6f1e` (merge-base: #352 merged, #353 absent) | 17 failed / 1768 passed / 21 skipped / 1 error | 18 | `8ee5308020d665378bb57f047bcd585db9c444d59aedc8cd2eaad8f12ae3b545` |
| `main` @ `f96d5fd2` | 18 failed / 1769 passed / 21 skipped / 1 error | 19 | `ec5d4f6d478def902f0f5e0957250473209c49f1decc974d02d0533386e7a086` |
| `main` + #354 + #355 (composed, this pass) | 14 failed / 1773 passed / 21 skipped / 1 error | 15 | `61ed0c5e1929dc34c005a4024ebd3b947f5955d505e19aa761ea68ef525907f1` |

**#353's node delta** (`comm -13` / `comm -23` between `2c6f6f1e` and `f96d5fd2`):
- added: `tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` (node B)
- removed: zero

This is the decisive confirmation: #353 added **exactly one** held node, not two. Node A
(`::test_lab_mutation_endpoints_are_exactly_the_lab_state_set`) is already failing at
`2c6f6f1e`, i.e. it was introduced by #352.

**Composed delta** (`main` → `main`+#354+#355): zero introduced (`comm -13` empty), four
removed — the three `test_m02a_ci_gate_integrity.py` allowlist-inventory nodes plus
`test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]`.
The composed tree is strictly better than `main` and adds no debt.

## Composition re-check (this pass)

The composition was re-built from the current PR tips, not reused:
- `/tmp/compose2` = `#354` head `04662703` + `#355`'s workflow diff applied. Applied cleanly.
- `.github/workflows/n-atlas-developer-lab.yml` at the composed tree hashes to
  **`efd88e1f0238…`**, identical to the previously recorded #355 head workflow hash —
  the #355 head has not drifted.
- `scripts/cp10_mutation_boundary_policy.py` differs between `/tmp/compose2` and the
  checked-out `/tmp/compose` (`730953a1…` vs `f767b24f…`); this is the expected #354-vs-#355
  divergence in that file's upstream content and did not block the workflow patch.

## What is unchanged

- The **authentication-boundary** classification of node B stands: #353 introduced a public
  path (`/api/lab/engineering/n-atlas/test-session`, a POST that mints a `natlas-tester.`
  token and records a human authorization) reachable without authentication. It engages the
  contract HARD STOP list ("a new authorization path appears") and contradicts the standing
  `AGENTS.md` invariant *"THE LAB IS OWNER-ONLY. AUTHENTICATION := SOVEREIGN_IDENTITY_ONLY."*
- The **sovereign A/B decision remains open and must not be taken by an agent**:
  - **Option A** — accept the public tester onboarding path; update the guard test and add
    the three `n-atlas` endpoints to `ALLOWED_MUTATION_ENDPOINTS`.
  - **Option B** — keep the Lab owner-only; re-express tester onboarding behind
    authentication.
- No merge, no push to `main`, no edit to `api/lab_routes.py` / `api/auth.py`, no edit to
  the `test_engineering_lab_api` guard, no change to `ALLOWED_MUTATION_ENDPOINTS` or
  `REGISTERED_ARCHITECTURAL_DEBT`.

## Deterministic next action

- **Current state:** #354 (`04662703`) and #355 (`73104fdf`, workflow hash `efd88e1f0238`)
  open and mergeable; both measured; both `READY FOR SOVEREIGN MERGE` for their own bounded
  scope. This correction is documentation-only on #354's existing branch.
- **Blockers:** none for either PR's own scope. The two held Lab nodes remain a separate
  proposed workstream gated on the A/B sovereign choice; the attribution error above is now
  corrected so that workstream does not proceed from a false premise.
- **Authorized action:** sovereign review and merge of #354 and #355.
- **Completion condition:** #354 and #355 merged by the sovereign, then a fresh pass
  reconstructs `main` and re-derives the node set from live evidence.

---

# Pass 4 — head-SHA correction and full-clone re-measurement

Pass: hourly bounded execution, 2026-10-08T02:0xZ
Base main: `f96d5fd2` (unchanged; still `origin/main`). #354 head: `ba187124`.
#355 head: `73104fdf` (still open, not merged).

## Head SHA corrected

Every earlier section of this document (and the PR body) cited `f7c212bd`, then `e90a5769`,
then `696cc07b` as the branch head. The **live** head at this pass, `GET /pulls/354 →
head.sha`, is:

```
ba187124f29a248be5a98c21ddb4d0d6836879c6
```

`git diff --name-only` from each cited SHA to `ba187124` returns only
`AGENTS.md` and the two `gate10-cp10-allowlist-deploy-surface-01/` evidence files — the
advance is documentation-only, so every policy/file measurement below binds to the current
head unchanged. A stale head citation is a defect to correct in place; this section
supersedes them.

## The clone WAS shallow — and it made one node a false positive

Earlier sections state "clone not shallow". That was **wrong for this environment**:
`git rev-parse --is-shallow-repository` returned `true`. With a shallow clone, `main`
exposed only **1** `AGENTS.md` revision vs **35** on the branch, so
`tests/test_agents_md_encoding_adjudication.py::test_corruption_origin_is_re_derivable` —
which walks `git log -- AGENTS.md` looking for the first corrupt revision and skips only when
that history is *empty* — found no corrupt revision and **asserted**, rather than skipping.

After `git fetch --unshallow --filter=blob:none origin` (full history, **32** `AGENTS.md`
revisions), the node does **not** appear in the failure set. It was a shallow-clone artefact,
**not** a repair attributable to this branch. This also refutes the archived claim (recorded
in `AGENTS.md`) that #354 "fixes it": the branch touches no test, fixture, or source that the
node reads.

## Re-measured node sets (full clone)

`pytest tests/ -q -rEf --continue-on-collection-errors`, full clone, this environment:

| tree | result | nodes | node-set sha256 |
|---|---|---|---|
| `main` @ `f96d5fd2` | 27F / 1763P / 18S / 1E | 28 | `d12b3aae9bbc1980961d473cedbea7b6790e93cd0ec880fdb2193f60b9aa9b8f` |
| #354 @ `ba187124` | 24F / 1766P / 18S / 1E | 25 | `153246a92d9ffd5bfaaa65a215ced6a9f0fb0023b1ee33e7a0f7ea46cf1f7ace` |

- `main(28) − branch(25)` = exactly the **3** `test_m02a_ci_gate_integrity.py`
  allowlist-inventory nodes → fixed.
- `branch(25) − main(28)` = **∅** → **zero introduced**.

The earlier `17 → 14` / `16F → 13F` figures were shallow-clone and/or `PYTHONPATH`-contended
artefacts; the invariant they asserted (three CP10 nodes removed, nothing introduced) is
confirmed here on a full clone. The trigger-coverage node
(`test_ci_gate_trigger_coverage.py::…[n-atlas-developer-lab.yml]`) is repaired by **#355**,
not by this branch; it is red on `main` and stays red on #354 alone, as Pass 3 recorded.

## Current CI state at the true head `ba187124`

`GET /commits/ba187124…/check-runs` → six runs, all `success`: `validate`, `SG-02-FE.2-V`
(run 37714998141), `Full-history secret scan`, `N-ATLAS external beta validation`
(37714998120), `native-arkadia-golden-workflow`, `bundle-beta-evidence`. Combined commit
status is `failure` solely from the two pre-existing Vercel rate-limit contexts (identical on
`main`). `mergeable=MERGEABLE`, `mergeStateStatus=UNSTABLE`.

Tracked corpus at `ba187124`: **1956** blobs (earlier section recorded 1955 for
`e7ce1d0f`; the doc-only advance does not change the tree, so read this as a one-blob
enumeration difference, not a corpus change).

## Pass 4 authorization boundary

Documentation-only, on the existing dedicated branch, via the existing PR #354. No policy
change, no denylist change, no test change, no `AGENTS.md` change, no merge, no push to
`main`, no force-push, no authority-model change, no scope expansion. The Lab
authentication-boundary A/B question remains reported, not resolved.

## Pass 5 — composed onto current `main` and unblocked (2026-10-09)

Measured at `main` `f9ced6b6` (2026-10-09). The PR had drifted to `CONFLICTING/DIRTY`
because its base (`6e3e1dac`, 2026-10-07) predated the intervening `AGENTS.md` ledger
appends. The conflict was **ledger-only**: `scripts/cp10_mutation_boundary_policy.py` was
unchanged on `main` since the merge base
(`git log <base>..main -- scripts/cp10_mutation_boundary_policy.py` → empty), and the three
additive `deploy/` lines merge cleanly.

- **Composed merge:** `7c0c83ad`, parents `536a8c43` (previous PR tip) + `f9ced6b6` (`main`).
  The sole conflict was `AGENTS.md`, an append-only collision of two private ledger
  sections. Resolved by keeping **both** sections — only the three conflict marker lines
  were removed (markers gone, both section headings present once, Cyrillic count `0`, so no
  cp866 mojibake was reintroduced). No text was dropped or rewritten.
- Diff vs `main` is exactly the 4 intended files: `scripts/cp10_mutation_boundary_policy.py`,
  `EVIDENCE.md`, `WORKSTREAM_STATE.md`, `AGENTS.md`.
- **Proof of the repair:** `tests/test_m02a_ci_gate_integrity.py` -> **64 passed** (was
  61P/3F). `tests/architecture` -> **11 passed** (11/11).
  `scripts/cp10_mutation_boundary_policy.py --judge` -> PASS (exit 0).
  `python -m py_compile api/main.py` -> OK; `api/main.py` = **2450** lines (budget 2600).
- **Regression boundary (node identity, not counts), full clone, `-rEf
  --continue-on-collection-errors`:** `main` `f9ced6b6` -> **16** nodes,
  `facc29a91e12fa3437362c6c4d40ac837393da7f4856c1bf018795d1032f87ed`; branch `7c0c83ad` ->
  **13** nodes, `1212cbd96dbb3002d85c44ddde6aff85d064d4ae87f4119ec6344ea95e57f827`.
  `main - branch` = exactly the 3 `test_m02a_ci_gate_integrity` nodes; `branch - main` =
  **empty**. Zero nodes introduced. 12 pre-existing failures + 1 collection error
  (`tests/test_autonomy.py`, the CE-01 module-vs-package collision) remain — recorded debt,
  not repaired here.
- `gh pr view 354` after the push: `mergeable=MERGEABLE`, `mergeStateStatus=UNSTABLE`
  (was `CONFLICTING/DIRTY`).

## Pass 5 authorization boundary

Merge composition (`main` into the PR branch) plus `AGENTS.md` conflict resolution and
in-repo evidence/state recording, on the existing dedicated branch, via the existing PR #354.
No policy change beyond the already-present additive `deploy/` rule, no denylist change, no
test change, no merge to `main`, no push to `main`, no force-push, no authority-model change,
no scope expansion. The Lab authentication-boundary A/B question remains reported, not
resolved. Merge remains the sovereign's action.

---

# Pass 6 (2026-10-09) — what actually reddens CP10 on `main` now

The Pass 1 objective ("restore `main` to green on the CP10 mutation-boundary gate") is
**partly correct and partly superseded by later drift**. Both claims below are measured at
`main` @ `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`, this environment.

## Correction 1 — the *executed* gate already passes on `main` today

`gh run view 37954341298` (push, `main`, `f9ced6b6`): the failing job `validate` fails on a
**single** step — `Enforce CP10 executable gates`. The CP10 mutation-boundary step itself
printed `Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)`, and the
fitness job `m02a` ran green in that range. So on the current tip the executed decision is
**green**; the earlier framing that "the executed gate is red on main HEAD" was already
corrected in Pass 2 and is re-confirmed here. What remains red is the *inventory invariant*
asserted by three fitness tests, which is a real defect (a latent red for any future commit
touching `deploy/`), not the executed gate.

## Correction 2 — the current CP10 `main` red has ONE cause, and it is not the browser step

`validate` is red because one step failed, and the enforcement step is now the *only* failure.
Enumerating every failing step of run `37954341298` yields exactly:

```
validate
  FAILED STEP: Enforce CP10 executable gates
```

The `browser` step (`CP10 browser route verification`) **passed**. Its `continue-on-error`
means it cannot redden the job by itself; its failure is only *promoted* by the enforcement
step, which was already going to exit non-zero on `mutation` (the three fitness nodes).

The browser step's historical failure was a **separate, already-repaired** cause: the dangling
`<script src="/firebase-config.js">` added by `d8eae1d`, served by the Vite dev server as an
SPA fallback, produced `failedRequests=["http://127.0.0.1:5000/firebase-config.js :: net::ERR_ABORTED"]`
x4 and `Error: Browser runtime errors observed`. That is owned by **PR #384**
(`web/public_prism/public/firebase-config.js` + `tests/test_frontend_script_assets_resolve.py`),
**not** by the allowlist workstream. It must not be folded into #354.

## The live `main` failing/error node set (16 nodes, `facc29a9…`)

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

```
ERROR   tests/test_autonomy.py
FAILED  tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points
FAILED  tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED  tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED  tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED  tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED  tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED  tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix
FAILED  tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface
FAILED  tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface
FAILED  tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED  tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED  tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED  tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED  tests/test_steward_filter.py::test_blocks_identity_claims
FAILED  tests/test_steward_filter.py::test_compress_to_choices
```

This branch's tree yields the **same set minus the three `m02a` allowlist nodes** — 13 nodes,
`1212cbd96dbb3002d85c44ddde6aff85d064d4ae87f4119ec6344ea95e57f827`. **Introduced: zero.**

## Correction 3 — the trigger-coverage node is no longer red on `main`

The Pass 2 section "The two PRs do not individually restore `main` to green — they compose"
lists `test_ci_gate_trigger_coverage::test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]`
as the fourth composition-blocking node. It is **absent from the current 16-node `main` set**:
`grep -c trigger_coverage` over the live node list is `0`. That node was repaired by a later
merge, so #355 (`.github/workflows/n-atlas-developer-lab.yml`) is no longer required to green
the CP10 fitness suite at this revision. Whether #355 is still wanted on its own merits is a
separate question; it is not a CP10 composition dependency today.

## Composition evidence (measured on a worktree from `main` `f9ced6b6`)

- **#354 policy admits the `deploy/` surface:** applying only the `scripts/cp10_mutation_boundary_policy.py`
  diff onto `main` and judging the four `deploy/n-atlas-server/*` paths -> `Mutation boundary PASS`.
- **#384 composes cleanly with #354:** both `web/public_prism/public/firebase-config.js` and
  `tests/test_frontend_script_assets_resolve.py` are admitted by the composed policy
  (`Mutation boundary PASS`), and `tests/test_frontend_script_assets_resolve.py` runs
  **3 passed** on the composed tree. The two PRs are textually and semantically independent.

## Bounded next action

The allowlist workstream is complete and self-contained. The remaining CP10 `main` red is
closed on the sovereign's merge of **#354** (repository policy) and **#384** (browser asset) —
two disjoint, independently-measured surfaces. No further allowlist work is warranted. No
merge, no push to `main`.


# Pass 7 (2026-10-09) — correction to Pass 6 Corrections 1 and 2

This pass was asked to consider composing the *browser-asset* repair (PR #384) onto this
branch, because CP10 is red on `main`. Doing that required an independent re-measurement of
the failing step, and that measurement **contradicts the literal step-attribution recorded in
Pass 6 Corrections 1 and 2**. Both claims below are measured at `main` @
`f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8` and branch head `79192891`, this environment.

## What Pass 6 got wrong

Pass 6 Correction 2 asserted that "the `browser` step (`CP10 browser route verification`)
**passed**" and that the enforcement step was checking the `mutation` step's `failure`
outcome. That reading came from grepping the *echoed* command strings, which are always
`test 'success' = success` for quiet steps. It is false.

`steps.<id>.outcome` **is** resolvable inside the enforcement `run:` block (it emits `success`
for quiet steps and `failure` for `continue-on-error` steps). The non-echo stdout of the
enforcement step resolves the question unambiguously. Run `37954341298` (push, `main`,
`f9ced6b6`) and run `37967556608` (this branch head, `79192891`) both print:

```
14 x test 'success' = success
 1 x test 'failure' = success          <- the browser step
echo 'Executable CP10 gates: PASS (browser step outcome success).'
```

So the **single** enforced failing step is `CP10 browser route verification`. The `mutation`
step **passed** on both runs (`Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)`),
and the fitness suite that asserts the allowlist inventory is **not a step in
`sg-02-fe-2-v.yml` at all** — `tests/test_m02a_ci_gate_integrity.py` is only a *trigger path*
(workflow lines 28/59), never executed by a `run:` step.

## The real `main` CP10 red, from the log

```
CP10 browser route verification  [route] /solspire status=200 final=http://127.0.0.1:5000/solspire
CP10 browser route verification  [route] /solspire/projects status=200 final=http://127.0.0.1:5000/
CP10 browser route verification  [route] /solspire/engineering-lab status=200 final=http://127.0.0.1:5000/
CP10 browser route verification  consoleErrors=[...404 (Not Found) x4]
CP10 browser route verification  Error: Browser runtime errors observed
CP10 browser route verification  pageErrors=[]
CP10 browser route verification  failedRequests=["http://127.0.0.1:5000/firebase-config.js :: net::ERR_ABORTED" x4]
CP10 browser route verification  ##[error]Process completed with exit code 1.
```

Root cause: `d8eae1d` ("Load runtime Firebase config before app bootstrap", 2026-10-09 15:17)
added `<script src="/firebase-config.js">` to `web/public_prism/index.html`, but
`web/public_prism/public/firebase-config.js` has **never been committed** (`git log --all --
web/public_prism/public/firebase-config.js` -> only the #384 commit `f744e36b`, not an ancestor
of `main`). The Vite dev server (`pnpm dev`, SPA fallback) 404s it.

## Consequence for Pass 6's conclusion

Pass 6's *conclusion* (the allowlist workstream does not close the CP10 `main` red; #384 owns
the browser half) is correct. Its *reasoning* was inverted: the executed gate is **not** green
on `main` — the browser step legitimately fails on `main`, and the three `m02a` allowlist
nodes are latent test-fitness debt, not the executed red. Corrections 1 and 2 are superseded.

## Re-measured node sets (this environment) — Pass 6's `facc29a9...` is superseded

Full suite: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`.

- `main` `f9ced6b6`: **15 FAILED + 1 ERROR = 16 nodes**,
  `sha256(sorted node list) = bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733`.
  The Pass 6 set (`facc29a9...`) omitted `tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key`
  and the two `tests/test_solspire_r1_governance_convergence.py` nodes; it is superseded.
- composed (#354 policy + #384 files on `main`): **12 FAILED + 1 ERROR = 13 nodes**,
  `sha256 = bae53864cab9d99b9a3b0a0a9eddacb7fa9f092809d3b8508abdb3abf58d9a6f`.
  Delta vs `main`: **-3**, exactly the three `m02a` allowlist nodes. **Introduced: zero.**

## Bounded fix on this branch

Compose #384's two files (`web/public_prism/public/firebase-config.js`,
`tests/test_frontend_script_assets_resolve.py`) onto this branch, so a single sovereign merge
of #354 closes both CP10 reds on `main`. Measured on the composed tree:

- `python -m pytest tests/test_frontend_script_assets_resolve.py -q` -> **3 passed**
- `python -m pytest tests/test_m02a_ci_gate_integrity.py -q` -> **64 passed**
- boundary judge over the composed change set (`deploy/n-atlas-server/*`, `firebase-config.js`,
  the asset test) -> `Mutation boundary PASS`, exit 0

This does not change policy beyond the already-present additive `deploy/` rule, does not touch
the denylist, does not change any existing test, and does not alter the authority model. Merge
is the sovereign's action.

## CI verification (branch head `5fdb7f49`, run `37969257307`)

`validate` job -> **success**, including the previously-red step:

```
CP10 browser route verification  [route] /solspire status=200
CP10 browser route verification  [route] /solspire/projects status=200
CP10 browser route verification  [route] /solspire/engineering-lab status=200
CP10 browser route verification  consoleErrors=[]  pageErrors=[]  failedRequests=[]
CP10 browser route verification  Unauthenticated route threshold PASS
CP10 mutation boundary           Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
Enforce CP10 executable gates    Executable CP10 gates: PASS (browser step outcome success).
```

`failedRequests=[]` is the direct proof the `d8eae1d` `/firebase-config.js` 404
(`net::ERR_ABORTED` x4 on `main`) is repaired by the composed asset. This closes the CP10
`validate` job on the branch; the sovereign merge of #354 is the remaining step.
