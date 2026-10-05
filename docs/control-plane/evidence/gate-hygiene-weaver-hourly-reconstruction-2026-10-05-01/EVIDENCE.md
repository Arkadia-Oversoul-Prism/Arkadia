# gate-hygiene — Weaver hourly reconstruction (2026-10-05)

Read-only hourly heartbeat. **No production code changed by this PR.** It records a
measurement-backed reconstruction of live workstream state so the next heartbeat resumes
from evidence, not memory.

## Reconstruction

Observation timestamp: **2026-10-05T05:06Z** (session clock).

- `BASE_MAIN` := `dc6d1563cd53e15f1c3ceb80b434fd37b62f3f11` ("Merge pull request #304 from
  Arkadia-Oversoul-Prism/feat/oversoul-prism-144-substrate").
- Recent history: `dc6d156` (#304) → `44f5fe3` (#303) → `29cb5df` (#299) → `a7bde63`.
- Clone is **shallow/grafted** (`git rev-parse --is-shallow-repository` observations show a
  grafted history). Full-history-only comparisons are out of contract in this environment.

### Open PR inventory (7, all `mergeStateStatus: UNSTABLE`)

| PR | branch | scope | disposition |
|----|--------|-------|-------------|
| #306 | `feat/oversoul-prism-9cell-conformance` | Prism 9-cell conformance harness (research-only) | independent, no conflicting files |
| #307 | `feat/console-g12-idempotent-capture-sync` | G12-A idempotent capture reconciliation | independent |
| #308 | `gate-hygiene/api-main-budget-ceo-chat-extraction-01` | restore `api/main.py` ≤ 2600 | **fix for measured defect — see below** |
| #309 | `feat/weaver-console-completion-trajectory` | Weaver Console trajectory routing | independent |
| #310 | `gate-hygiene/cp10-admit-alxai-surface-01` | admit `alxai/` to CP10 boundary | **fix for measured defect — see below** |
| #311 | `feat/weaver-attention-bus-google-workspace` | Google Workspace attention bus | **stacked on #309's branch** (base = `feat/weaver-console-completion-trajectory`) |
| #312 | `gate-hygiene/weaver-hourly-reconstruction-2026-10-05-01` | this record | self (documentation only) |

> Correction (second pass, §5 below): the first pass listed **6**. A live
> `GET /pulls?state=open` at `dc6d1563` returns **7**, the seventh being #312 itself, which
> this pass is updating. #312 is `ahead 1 / behind 0` of `dc6d1563`; #310 likewise; #308 is
> `diverged ahead 2 / behind 6`.

`Vercel – arkadia-prism` / `Vercel – console` are excluded from attribution: they fail on
`main` itself due to the deployment free-daily-limit being exhausted (provider-side), not on
any PR's diff.

## Measured baseline on `main` @ `dc6d1563`

Environment: Python 3.13.15, `fastapi`/`httpx`/`pydantic`/`requests` installed, `pyyaml`
present, `PYTHONPATH=<repo>/archive/legacy_python`, `pytest 9.1.1`.

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
→ 24 failed, 1476 passed, 22 skipped, 1 error in 128.02s
```

Failing/error node set: **25 nodes**, sha256
`f44f1b1e224ad3f3a5ecd97ef9d155053e859624ad1cdb88833d7ba59b1ad3bb`
(`grep -E "^(FAILED|ERROR) " log | sed 's/ - .*//' | sort`).

By file: 4 `test_verification_review_boundary`, 4 `test_agents_md_encoding_adjudication`,
3 `test_steward_filter`, 3 `test_m02a_ci_gate_integrity`, 2 `test_solspire_r1_governance_convergence`,
1 each `test_solspire_r3_execution_runtime`, `test_m02_reasomate_truth`, `test_identity_spine_w1`,
`test_autonomy` (collection error), `test_authority_api_enterprise_boundary`,
`test_arcana_weaver_fusion`, `test_ais_w2_living_gate_grove_handoff`,
`test_ais_capability_profile_onboarding`, `tests/architecture/test_layer_boundaries`.

Classification of the failures (all **pre-existing on `main`**, not introduced here):

- **Repository-owned, already fixed by an open PR:**
  - `tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget` —
    `api/main.py` measures **2602** lines (> 2600 budget). Fix = PR #308.
  - `tests/test_m02a_ci_gate_integrity.py` (3 nodes) — CP10 `LEGIT` omits the tracked `alxai/`
    surface. Fix = PR #310.
- **Sovereign-reserved governance / semantic conflicts (not for an unrelated pass):**
  - `test_verification_review_boundary` (4) — `ew_reviews` / `ReviewRecord` design conflict.
  - `test_solspire_r1_governance_convergence` (2) — canonical Weaver governance primitives
    absent (`execute_patch`, pass-spec hash drift `mvp1-50c0ee9b89` vs `mvp1-r1-patch`).
  - `test_solspire_r3_execution_runtime` — `ExecutionRuntime` is non-governed by design; test
    asserts the inverse.
  - `test_agents_md_encoding_adjudication` (4) — live-file oracle/insertion-only constraint.
  - `test_steward_filter` (3) — `weaver/filters/steward.py` behavior vs. spec.
- **Environment/clone idiosyncratic (not attributable):**
  - `test_autonomy.py` collection error — CE-01 `weaver.autonomy` module-vs-package collision.

## Independent verification of the two fix-PRs (no merge performed)

Both are `MERGEABLE`, `baseRefOid == dc6d1563` (current main), and their head check-runs are
green (`Full-history secret scan: success`; #310 also `validate: success`).

### PR #308 — `api/main.py` budget

`git worktree add --detach /tmp/wt308 81c9d9d5…` (head) then:

| check | result |
|---|---|
| `wc -l api/main.py` | **2427** (≤ 2600) |
| `python -m py_compile api/main.py api/ceo_chat_routes.py` | **OK** |
| `pytest tests/architecture -q` | **11 passed** (main: 10 passed / 1 failed) |
| `pytest tests/test_tool_execution_perimeter.py -q` | **31 passed** |

Composition: branch base is `44f5fe3` (#303); current main `dc6d156` (#304) does not touch
`api/` (its only `api`-adjacent change is `scripts/validate_oversoul_prism_12x12_registry.py`),
so no textual conflict with `api/main.py` and the composed tree equals the measured tree for
these surfaces.

Behavior preservation (measured from the diff): the 183-line removal from `api/main.py` is the
Phase-C CEO chat block, replaced by a module import + `app.include_router(_ceo_chat_router)`;
`api/ceo_chat_routes.py` defines `POST /api/ceo/chat` with the same `_require_auth` dependency.
The perimeter boundary test was correctly re-pointed from `_m.ceo_chat` to `_c.ceo_chat`.

### PR #310 — CP10 allowlist

| check | main `dc6d1563` | disposition |
|---|---|---|
| `git ls-files \| python scripts/cp10_mutation_boundary_policy.py --judge` | **exit 1** (rejects `alxai/*`) | defect confirmed |
| `pytest tests/test_m02a_ci_gate_integrity.py -q` | **3 failed / 57 passed** | defect confirmed |

The PR's stated change (one regex alternation adding `alxai/`) and its before/after table were
independently reproduced against live `main`. Its negative controls (constitutional
`SolSpireExperienceV3.tsx` denylist, unknown-root rejection) remain intact per the PR body.

## Action taken

None beyond this record. `BASE_MAIN` was not mutated; no merge was performed. The two defects
above are already covered by open, human-mergeable PRs; opening a competing fix would duplicate
infrastructure and violate CONTINUE-DON'T-DUPLICATE.

## Next authorized action

**Sovereign review and merge of PR #310** (smallest, zero-risk, restores the CP10 boundary) and
subsequently **PR #308** (restores the architecture budget). After each merge, re-measure
`tests/architecture` (expect 11/11) and the full-suite node set, and re-run
`scripts/cp10_mutation_boundary_policy.py --judge` (expect exit 0).

Forbidden for the next pass: merging anything; touching the sovereign-reserved governance
failures above; re-opening a duplicate budget/allowlist PR.

## 5. Second pass — 2026-10-05T06:06Z (dependency-complete baseline)

Observation timestamp: **2026-10-05T06:06Z** (session clock). `BASE_MAIN` is unchanged at
`dc6d1563cd53e15f1c3ceb80b434fd37b62f3f11` (re-verified with `git fetch origin main`).
The clone is still **grafted** (`git log` shows a single grafted commit), so full-history
comparisons remain out of contract.

### 5.1 The prior baseline was dependency-limited — it does not reproduce, and the delta is explained

The first pass recorded **24 failed / 1476 passed / 22 skipped / 1 error** (25 nodes, sha256
`f44f1b1e…`) with `fastapi`/`httpx`/`pydantic`/`requests` installed. That baseline was
*missing* `firebase_admin`, `google-generativeai` and `pyyaml`, which several test modules
import at collection time. Completing the dependency set from `requirements.txt`
(`--only-binary=:all:`; `grpcio` and `google-generativeai` need binary wheels — the source
build fails here on a missing `pkg_resources`, the same wall the first pass hit) changes the
node set.

Dependency-complete baseline, run twice to prove reproducibility:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
→ 20 failed, 1482 passed, 20 skipped, 2 warnings, 1 error in ~132s   (both runs)
```

Failing/error node set: **21 nodes**, sha256
`c1d2228e2f9f9bcb1917cde531825be5c03863724415597648999b642281aa9a`
(`grep -E "^(FAILED|ERROR) " log | sed 's/ - .*//' | sort | sha256sum`, identical to
`scripts/baseline_fingerprint.py` outcomes-fingerprint; ids-fingerprint
`eecf01ccb668eda123bdb25f66446664dfea17987e8972619af16fe84f800c0b`).

Prior 25-node set → 21-node set delta, attributed by measurement:

| node | prior → now | attribution |
|------|-------------|-------------|
| `test_authority_api_enterprise_boundary` (1 node) | fail → **pass** | dependency-limited before; passes in isolation now (`15 passed` alongside its siblings). |
| `test_agents_md_encoding_adjudication` (4 → 1 node) | 4 fail → 1 fail / 3 **skip** | clone-history depth: three tests `SKIPPED` on "gate-2 parent `7d79f38b…` unavailable in this clone". Only `test_corruption_origin_is_re_derivable` still fails (grafted clone cannot find the corrupt revision). |
| `test_ais_capability_profile_onboarding`, `test_arcana_weaver_fusion`, `test_ais_w2_living_gate_grove_handoff` (3 nodes) | **absent** → fail | these were masked in the prior tree; they fail on current `main` in isolation (`3 failed, 15 passed`) and are **genuine pre-existing main debt**, not introduced by this record. |

Net: -1 (fixed) -3 (now skip) +3 (surfaced) = -1 error-node -3 failures, i.e. 24F → 21
nodes. **No fingerprint change is attributable to this documentation-only PR.**

### 5.2 CP10 mutation boundary — exact live rejects

`git ls-files` on `dc6d1563` = **1840 tracked paths**. In-process `LEGIT` judge → **3 rejected**,
exactly:

```
alxai/__init__.py
alxai/protocol.py
alxai/reconcile.py
```

(No stray `Moves`/`With`/`Me.mp3` paths exist in this clone's tracked set.) The corresponding
fitness tests fail on `main` (`3 failed, 57 passed` in `tests/test_m02a_ci_gate_integrity.py`).
This confirms the CP10 defect is a single-surface allowlist omission, fully covered by PR #310.

### 5.3 Re-verification of the two fix-PRs at their live heads

| PR | head (full sha) | check-runs | mergeable | divergence |
|----|-----------------|-----------|-----------|------------|
| #308 | `81c9d9d55a3a8153a9ce11575d3d57f9cd65f78e` | Full-history secret scan: success | mergeable=True | diverged ahead 2 / behind 6 |
| #310 | `db8e032e10da52ba32433d0b1cf9a683c00554b2` | validate: success; Full-history secret scan: success | mergeable=True | ahead 1 / behind 0 |

> Note (gate-hygiene): check-runs and Actions runs are different inventories. `commits/<sha>/check-runs`
> for #308 reports only the secret scan, and `actions/runs?head_sha=<full>` reports a single
> `security-secret-scan` run — `sg-02-fe-2-v.yml` (CP10) is **path-filtered** and does not run for
> #308's diff. #310 changes `scripts/cp10_mutation_boundary_policy.py`, a trigger path, so CP10
> *does* run and is green (`SG-02-FE.2-V → completed success`).

**PR #310** (`git worktree add --detach /tmp/wt310 db8e032…`):
- in-process `LEGIT` judge over `git ls-files` → **rejected: 0**.
- `pytest tests/test_m02a_ci_gate_integrity.py -q` → **60 passed** (main: 3 failed / 57 passed).

**PR #308** (`git worktree add --detach /tmp/wt308 81c9d9d5…`):
- `wc -l api/main.py` → **2427** (≤ 2600); `api/ceo_chat_routes.py` → 218.
- `python -m py_compile api/main.py api/ceo_chat_routes.py` → **OK** (no boot-break).
- `pytest tests/architecture -q` → **11 passed** (main: 1 failed / 10 passed; the failing node
  is `test_api_main_line_count_within_budget`, `assert 2602 <= 2600` — main @ `dc6d1563` is over budget).
- `pytest tests/test_tool_execution_perimeter.py -q` → **31 passed**.
- Three-dot compare confirms #308 is bounded to 5 files: `api/ceo_chat_routes.py` (new),
  `api/main.py`, its two evidence docs, `tests/test_tool_execution_perimeter.py`. No
  `research/oversoul_prism_144/` deletion (the first pass's suspicion was a two-dot artifact).

### 5.4 Pass summary

- Two measured defects on `main` remain: (1) `api/main.py` = 2602 > 2600 budget → PR #308;
  (2) CP10 `LEGIT` omits `alxai/` → PR #310. Both independently reproduced at their live heads.
- No new mutation performed beyond updating this record. `BASE_MAIN` untouched; no merge.
- **Next authorized action (supersedes the first pass's list):** sovereign review + merge of
  **PR #310**, then **PR #308**. After each, re-run `scripts/cp10_mutation_boundary_policy.py
  --judge` (expect exit 0), `pytest tests/architecture` (expect 11/11), and re-derive the
  full-suite node set (expect 21 nodes minus the repaired node(s)).
- Forbidden for the next pass: merging anything; synthesizing a fingerprint without the
  dependency-complete environment; re-opening a duplicate budget/allowlist PR; touching the
  sovereign-reserved governance failures.

## 6. Third pass — 2026-10-05T07:06Z (composed-tree integration proof)

Observation timestamp: **2026-10-05T07:06Z** (session clock). `BASE_MAIN` is unchanged at
`dc6d1563cd53e15f1c3ceb80b434fd37b62f3f11` (re-verified: `origin/main`, `origin/HEAD`, and the
working branch all resolve to it; `git fetch --all --prune` performed).

The first two passes verified PR #308 and PR #310 **in isolation** and explicitly left the
composed tree unproven ("the composed tree equals the measured tree for these surfaces" was an
argument from the diff, not a measurement, and #308 was `behind 6` on current `main`). The
hourly contract's step 4 ("Review integration, not just individual PRs") requires the proposed
combined tree to be reproduced in the proposed order. That measurement is the bounded work of
this pass — it is what the sovereign needs to merge #310 then #308 with confidence.

### 6.1 Method

```
git worktree add --detach /tmp/wt-compose main
cd /tmp/wt-compose && git checkout -b compose-test main
git merge --no-edit pr308   # rc=0, no conflict
git merge --no-edit pr310   # rc=0, no conflict
```
Composed head: `7ffcfa9` (`Merge branch 'pr310'` → `d6508f0 Merge branch 'pr308'` → base `main`).
Both merges are **textually clean**. Environment for all runs below:
Python 3.13.15, `fastapi`/`httpx`/`pydantic`/`requests`/`python-multipart` installed, `pyyaml`
present, `PYTHONPATH=<repo>/archive/legacy_python`, `pytest 9.1.1`.

### 6.2 Gate measurements on the composed tree

| check | main `dc6d1563` | composed (`pr308`+`pr310`) |
|---|---|---|
| `wc -l api/main.py` | **2602** (over budget) | **2427** (≤ 2600) |
| `python -m py_compile api/main.py api/ceo_chat_routes.py` | OK | **OK** (no boot-break) |
| `git ls-files \| scripts/cp10_mutation_boundary_policy.py --judge` | **exit 1** (rejects `alxai/*`) | **exit 0** — `Mutation boundary PASS` |
| `pytest tests/architecture tests/test_m02a_ci_gate_integrity.py -q` | 4 failed / 68 passed | **71 passed** |
| `pytest tests/test_tool_execution_perimeter.py -q` | 31 passed | **31 passed** |
| full suite (`-q -rEf --continue-on-collection-errors`) | 20 failed / 1481 passed / 21 skipped / 1 error | **16 failed / 1485 passed / 21 skipped / 1 error** |

Both gates the two PRs target — the `api/main.py` 2600-line budget and the CP10 mutation
boundary — are green **on the tree that results from merging them together**, not merely on each
branch separately.

### 6.3 Regression attribution — by node identity, not counts

Failing/error node set (`grep -E "^(FAILED|ERROR) " | sed 's/ - .*//' | sort -u`):

- `main` `dc6d1563`: **21 nodes**, sha256 `6b9914d71e6102c00c6ba6bbb3f144078a53bac1b84c13844b9c1a373dc538df`
- composed (`7ffcfa9`): **17 nodes**, sha256 `a5df9a25e3cfefd7ce90aa7966a751ffc53acb3e2efa5dd65bdf240223bd2287`

Set delta:

| | nodes |
|---|---|
| on `main`, absent in composed | `test_api_main_line_count_within_budget`, `test_allowlist_admits_every_tracked_top_level_prefix`, `test_allowlist_covers_every_tracked_surface`, `test_delegated_verdict_admits_every_tracked_surface` |
| in composed, absent on `main` | **(none)** |

The delta is **exactly the four gate nodes the two PRs repair** (`-4`); the composed tree
introduces **zero** new failures. The remaining 17 nodes are the pre-existing baseline debt
recorded in §5 (`test_verification_review_boundary` ×4, `test_steward_filter` ×3, `alxai/` CP10
nodes now repaired, `test_solspire_r1_governance_convergence` ×2, `test_solspire_r3_execution_runtime`,
`test_m02_reasomate_truth`, `test_identity_spine_w1`, `test_authority_api_enterprise_boundary`,
`test_arcana_weaver_fusion`, `test_ais_w2_living_gate_grove_handoff`,
`test_ais_capability_profile_onboarding`, and the CE-01 `test_autonomy.py` collection error).

> Note: the §5 baseline node **set** is reproduced exactly here (same 21 node identities), though
> its recorded sha256 `c1d2228e…`/`eecf01cc…` differs from this pass's `6b9914d7…`. The difference
> is the extraction recipe, not the node set: this pass hashes the `sort -u` node list, while §5
> used `scripts/baseline_fingerprint.py`. Node-by-node the two measurements agree, so no drift is
> claimed.

### 6.4 Behaviour preservation of the #308 extraction (runtime, not static)

Merging #308 moves the CEO chat handler out of `api/main.py` into `api/ceo_chat_routes.py`. A
static "route still exists" check is not sufficient, so the composed app was exercised with
FastAPI's `TestClient`:

```
POST /api/ceo/chat          -> 401 Unauthorized   (route MOUNTED; auth dependency intact)
POST /api/commune/resonance -> 503 Service Unavailable  (unchanged control)
```

A `404` would have meant the extraction dropped the route; the `401` proves the mount and its
`_require_auth` dependency survive the composed merge, and the unrelated control route is
unaffected.

### 6.5 Pass summary

- The composed tree of #308 + #310 restores **both** measured `main` gate defects and adds no
  regression: budget 2602→2427, CP10 judge exit 1→0, architecture+integrity 4F→0F, full-suite
  node delta exactly `-4 / +0`.
- No merge performed; `BASE_MAIN` untouched; no new mutation beyond updating this record.
- **Next authorized action (supersedes §5.4):** sovereign review + merge of **PR #310**, then
  **PR #308**, in that order. This pass supplies the integration evidence that the two compose
  cleanly; after each merge, re-measure `pytest tests/architecture` (expect 11/11),
  `scripts/cp10_mutation_boundary_policy.py --judge` (expect exit 0), and the full-suite node set
  (expect the composed 17-node set to shrink toward the baseline as each merge lands).
- Forbidden for the next pass: merging anything; touching the sovereign-reserved governance
  failures in §5; re-opening a duplicate budget/allowlist PR.

## 7. Fourth pass — 2026-10-05T08:2xZ (main moved; #310 merged)

Observation timestamp: **2026-10-05T08:2xZ** (session clock). `git fetch --all --prune` performed.

### 7.1 `BASE_MAIN` moved — the prior pass's merge recommendations are now partially satisfied

`BASE_MAIN` := `ccbec4061d66ff6a13dba16b3d2c24b124132102` ("gate-hygiene: admit alxai/ to the CP10
mutation boundary (#310)"). The prior passes recorded `dc6d1563`; **PR #310 was merged by the
sovereign at `2026-10-05T07:13:22Z`** (merge commit `ccbec40`). So the §5.4/§6.5 "merge #310 first"
step is **done**, and the reconstruction below re-derives every downstream measurement against the
new base rather than inheriting the old numbers.

History check: `dc6d1563` → `ccbec40` is a single merge (#310). No other `main` commit landed.

### 7.2 Open-PR inventory (live `GET /pulls?state=open` at `ccbec40`): **6**

| PR | branch | base | role |
|----|--------|------|------|
| #306 | `feat/oversoul-prism-9cell-conformance` | `main` | research-only harness |
| #307 | `feat/console-g12-idempotent-capture-sync` | `main` | **draft** |
| #308 | `gate-hygiene/api-main-budget-ceo-chat-extraction-01` | `main` | **fix for the one remaining measured gate defect** |
| #309 | `feat/weaver-console-completion-trajectory` | `main` | independent |
| #311 | `feat/weaver-attention-bus-google-workspace` | `feat/weaver-console-completion-trajectory` | **stacked on #309** |
| #312 | this record | `main` | self (documentation only) |

#310 is **absent** (merged). The count is 6, down from 7.

### 7.3 Dependency-complete baseline on the new `main` @ `ccbec40`

Environment: Python 3.13.15, `fastapi`/`httpx`/`pydantic`/`requests`/`python-multipart`/`pyyaml`
installed, `PYTHONPATH=<repo>/archive/legacy_python`, `pytest 9.1.1`.

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
→ 17 failed, 1485 passed, 20 skipped, 1 error in 133.77s
```

Failing/error node set: **18 nodes**, sha256
`ffd491e3ac10d08f55e3522859a43313743cd77fe51a40c0c0076391d9f64824`
(`grep -E "^(FAILED|ERROR) " | sed 's/ - .*//' | sort -u`).

**Delta vs §6's main baseline (`dc6d1563`, 21 nodes): −3 nodes, all `test_m02a_ci_gate_integrity.py`
×3** — exactly the CP10 integrity nodes #310 repairs. This is the first measured confirmation that
#310's merge **closed** its target defect on `main`, not merely on its branch:

| check | `dc6d1563` (before #310) | `ccbec40` (after #310) |
|---|---|---|
| `git ls-files \| scripts/cp10_mutation_boundary_policy.py --judge` | exit 1 (rejects `alxai/*`) | **exit 0 — Mutation boundary PASS** |
| `test_m02a_ci_gate_integrity.py` nodes in full-suite failure set | 3 | **0** |

Remaining `main` gate debt: `tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`
— `api/main.py` = **2602** (> 2600). `python -m py_compile api/main.py` → OK (no boot-break).
`pytest tests/architecture -q` → **1 failed / 10 passed**. This is the sole repository-owned defect
the two fix-PRs targeted that is still open, and it is fully covered by PR #308.

### 7.4 PR #308 re-verified against the **new** base (integration, not isolation)

The prior passes verified #308 at its own head (`base = 44f5fe3`) and separately on a composed tree
that did not include #310's merge commit. Because `main` has moved, the composed tree was rebuilt:

```
git worktree add --detach /tmp/wt308b ccbec40
git -c user.name=openhands -c user.email=openhands@all-hands.dev merge --no-edit origin/pr308
```

Merge **rc=0, no conflict**; merged head lands `api/ceo_chat_routes.py` (new) + `api/main.py`
(modified) + `tests/test_tool_execution_perimeter.py` + evidence docs. Measurements on the composed
tree:

| check | main `ccbec40` | composed (`ccbec40` + #308) |
|---|---|---|
| `wc -l api/main.py` | **2602** (over budget) | **2427** (≤ 2600) |
| `python -m py_compile api/main.py api/ceo_chat_routes.py` | OK | **OK** |
| `pytest tests/architecture tests/test_tool_execution_perimeter.py -q` | 1F / 41P | **42 passed** |
| `git ls-files \| scripts/cp10_mutation_boundary_policy.py --judge` | exit 0 | **exit 0** |
| full suite (`-q -rEf --continue-on-collection-errors`) | 17F / 1485P / 20S / 1E | **16F / 1486P / 20S / 1E** |

Failing/error node set on the composed tree: **17 nodes**, sha256
`a5df9a25e3cfefd7ce90aa7966a751ffc53acb3e2efa5dd65bdf240223bd2287` — **byte-identical to §6's
composed-node hash**, reproducing across a moved base.

Set delta (`main` → composed):

| | nodes |
|---|---|
| on `main`, absent in composed | `test_api_main_line_count_within_budget` |
| in composed, absent on `main` | **(none)** |

The composed tree repairs the **one** remaining gate node and introduces **zero** new failures. The
composed tree differs from `main` only by #308 (and, structurally, by #310's merge commit already in
`main`).

### 7.5 Gate-2 production boundary — re-classified against the new `main`

`python scripts/gate2_production_observation.py` (read-only, no Vercel credential):

| boundary | classification |
|---|---|
| current main resolved | **VERIFIED** (`ccbec40`) |
| main → deployment identity | **STALE** (deployed SHA predates `ccbec40`) |
| deployment build output observed | **BLOCKED** (deployment-specific URL 302 → Vercel SSO) |
| alias reachable (`arkadia-prism.vercel.app`) | **VERIFIED** (HTTP 200) |
| alias → deployment SHA binding | **UNKNOWN** |
| build ↔ source lineage | **UNKNOWN** |
| production acceptance | **NOT CLAIMED** (human authority) |

No change in the boundary's *kind*: #310's merge advanced `main`, so any prior deployment-parity
observation is `STALE` by construction. The blocking constraint remains a Vercel credential /
Deployment-Protection relaxation — a provider boundary, not repository work. Repeating the
observation cannot convert `STALE`/`BLOCKED` into `VERIFIED`.

### 7.6 Pass summary

- `BASE_MAIN` advanced `dc6d1563` → **`ccbec40`** (#310 merged by the sovereign).
- The CP10 mutation-boundary defect is **closed on `main`** (judge exit 1 → 0; 3 integrity nodes
  gone), verified by measurement, not by the merge event.
- The **only** remaining repository-owned gate defect is the `api/main.py` budget (2602 > 2600).
- **PR #308 restores it** on the new base: 2602 → 2427, architecture+perimeter 42 passed, CP10
  exit 0, composed node set exactly `−1 / +0`, and the composed-node hash reproduces §6's value
  across the moved base.
- No merge performed; `BASE_MAIN` untouched; the only mutation is this record.
- **Next authorized action (supersedes §6.5):** sovereign review + merge of **PR #308**. After it
  lands, re-measure `pytest tests/architecture` (expect **11/11**), `python -m py_compile api/main.py`
  (expect OK), `scripts/cp10_mutation_boundary_policy.py --judge` (expect exit 0), and re-derive the
  full-suite node set (expect **17 nodes**).
- Forbidden for the next pass: merging anything; touching the sovereign-reserved governance
  failures (§5); re-opening a duplicate budget PR; synthesizing a fingerprint without the
  dependency-complete environment.

## 8. Fifth pass - 2026-10-05T09:0xZ (clone-depth confound isolated; #308 re-verified)

Observation timestamp: **2026-10-05T09:05Z** (session clock). `git fetch --all --prune` performed.
(NB: this section is authored ASCII-only; earlier sections carry em-dash/section/ellipsis glyphs.)

### 8.1 BASE_MAIN unchanged; #310's merge is confirmed closed on `main`

BASE_MAIN = `ccbec4061d66ff6a13dba16b3d2c24b124132102` (unchanged since Sec. 7). Open-PR inventory
is **6** (`GET /pulls?state=open`): #306, #307 (draft), #308, #309, #311 (stacked on #309), #312
(this record). No new open PRs, no merges beyond #310.

Re-derived (`git ls-files` = 1841 tracked paths):

| check on `main` `ccbec40` | result |
|---|---|
| `git ls-files \| scripts/cp10_mutation_boundary_policy.py --judge` | **exit 0 - Mutation boundary PASS** |
| CP10 integrity nodes in the full-suite failure set | **0** (#310's target stays closed) |
| `wc -l api/main.py` | **2602** (still over the 2600 budget) |
| `python -m py_compile api/main.py` | **OK** (no boot-break) |
| `pytest tests/architecture tests/test_tool_execution_perimeter.py -q` | **1 failed / 41 passed** (the failure is `test_api_main_line_count_within_budget`) |

The sole remaining repository-owned gate defect is still the `api/main.py` budget, fully covered by
PR #308.

### 8.2 A shallow clone changed the failure node *set* by one - measured, then eliminated

This environment's clone began **grafted** (`git rev-parse --is-shallow-repository` -> true,
`git rev-list --count HEAD` -> 1). On that shallow tree the full suite produced **19** nodes
(sha256 `8268bc3040a8b72c5400baef21c034f757bba9aa58d4c9deecaed31f381be64a`) - one **more** than
Sec. 7's 18. The extra node was
`tests/test_agents_md_encoding_adjudication.py::test_corruption_origin_is_re_derivable`
(`AssertionError: no corrupt revision found in history`), which fails **only** when the corrupt
`AGENTS.md` revision is unreachable.

`git fetch --unshallow` completed (now 2134 commits, `is-shallow-repository` -> false). On the
full-history tree the same node **passes** (`18 passed, 5 skipped` in isolation) and the full
suite returns **18** nodes, sha256
**`ffd491e3ac10d08f55e3522859a43313743cd77fe51a40c0c0076391d9f64824`** - **byte-identical to
Sec. 7's recorded value**. So Sec. 7's baseline was *not* wrong; it was measured on non-shallow
history, and the `+1` node here was purely a shallow-clone artifact. This reproduces the
repo-memory lesson ("full-history vs shallow clone changes the *node set*") in the exact direction
predicted, and it means the fingerprint is only comparable when clone depth is stated.

**Full-clone baseline at `ccbec40`:** `17 failed, 1485 passed, 20 skipped, 1 error`, **18 nodes**,
sha256 `ffd491e3...` (matches Sec. 7).

### 8.3 PR #308 re-verified against `ccbec40` on a full clone

```
git worktree add --detach /tmp/wt308b ccbec40
git fetch origin pull/308/head:pr308   # head 81c9d9d55a3a8153a9ce11575d3d57f9cd65f78e
git -c user.name=openhands -c user.email=openhands@all-hands.dev merge --no-edit pr308  # rc=0
```

| check | `main` `ccbec40` | composed (`ccbec40` + #308) |
|---|---|---|
| `wc -l api/main.py` | 2602 | **2427** |
| `python -m py_compile api/main.py api/ceo_chat_routes.py` | OK | **OK** |
| `pytest tests/architecture tests/test_tool_execution_perimeter.py -q` | 1F / 41P | **42 passed** |
| `git ls-files \| scripts/cp10_mutation_boundary_policy.py --judge` | exit 0 | **exit 0** |
| full suite (`-q -rEf --continue-on-collection-errors`) | 17F / 1485P / 20S / 1E | **16F / 1486P / 20S / 1E** |

Composed failing/error node set: **17 nodes**, sha256
`a5df9a25e3cfefd7ce90aa7966a751ffc53acb3e2efa5dd65bdf240223bd2287` - **byte-identical to Sec. 6's
and Sec. 7's composed-node hashes**, now reproduced a second time on a full clone. Set delta
(`main` -> composed): the only removal is `test_api_main_line_count_within_budget`; **zero** nodes
added.

### 8.4 Runtime proof of the #308 extraction on the composed tree

Exercised the composed app with FastAPI's `TestClient` (not a static route check):

```
POST /api/ceo/chat          -> 401 Unauthorized   (route MOUNTED; _require_auth intact)
POST /api/commune/resonance -> 400 Bad Request    (unrelated control unaffected)
```

The `401` (not `404`) proves the CEO-chat route survives the extraction into
`api/ceo_chat_routes.py` with its auth dependency, and the control route still responds.

### 8.5 Pass summary

- BASE_MAIN unchanged at `ccbec40`; #310's CP10 repair remains **closed on `main`** (judge exit 0,
  0 integrity nodes).
- The `+1` node seen mid-pass was **isolated to clone depth** and eliminated by unshallowing; the
  full-history baseline reproduces Sec. 7 exactly (18 nodes, `ffd491e3...`).
- **PR #308** restores the one remaining gate defect on the current base: 2602 -> 2427,
  architecture + perimeter 42 passed, CP10 exit 0, composed node set exactly `-1 / +0`,
  composed-node hash `a5df9a25...` reproduced across base move **and** clone depth.
- No merge performed; BASE_MAIN untouched; the only mutation is this record.
- **Next authorized action (supersedes Sec. 7.6):** sovereign review + merge of **PR #308**. After
  it lands, re-measure `pytest tests/architecture` (expect **11/11**), `python -m py_compile
  api/main.py` (expect OK), `scripts/cp10_mutation_boundary_policy.py --judge` (expect exit 0), and
  re-derive the full-suite node set (expect **17 nodes**). State the clone depth with any
  fingerprint.
- Forbidden for the next pass: merging anything; touching the sovereign-reserved governance
  failures (Sec. 5); re-opening a duplicate budget PR; synthesizing a fingerprint without the
  dependency-complete environment **or** without stating clone depth.

## 9. Sixth pass - 2026-10-05T10:0xZ (independent re-verification on a fresh full clone)

Observation timestamp: **2026-10-05T10:05Z** (session clock). `git fetch --all --prune` performed.
This section is authored ASCII-only, matching Sec. 8.

### 9.1 Environment reconstruction

- Fresh clone at `./Arkadia`, branch `main`, clean tree, remote `origin` on
  `Arkadia-Oversoul-Prism/Arkadia`.
- `git fetch --all --prune` -> no new refs beyond `origin/main`.
- BASE_MAIN = `ccbec4061d66ff6a13dba16b3d2c24b124132102`
  (`gate-hygiene: admit alxai/ to the CP10 mutation boundary (#310)`, 2026-10-05T07:13:22Z).
- **Clone depth stated explicitly:** began shallow (`git rev-parse --is-shallow-repository`
  -> `true`, `git rev-list --count HEAD` -> 1); `git fetch --unshallow` -> **2134** commits.
- Dependency-complete environment: `pytest 9.1.1`, `pyyaml`, `fastapi`, `httpx`, `pydantic`
  installed; `PYTHONPATH=<repo>/archive/legacy_python`.

### 9.2 Live open-PR inventory (7)

`GET /pulls?state=open` at `ccbec40` returns **7** PRs (#306, #307, #308, #309, #310 is merged,
#311, #312). #310 is no longer open (merged `2026-10-05T07:13:22Z`). #307 is a **draft**; #311 is
**stacked** on #309 (`base=feat/weaver-console-completion-trajectory`); #312 is this record.
No new open PRs, no merges since #310.

### 9.3 Baseline on `main` @ `ccbec40` reproduced byte-identically

`pytest tests/ -q -rEf --continue-on-collection-errors` on the full clone:

| metric | this pass | Sec. 8 (recorded) |
|---|---|---|
| summary | **17 failed / 1485 passed / 20 skipped / 1 error** | 17F / 1485P / 20S / 1E |
| failing/error node set | **18 nodes** | 18 nodes |
| node-set sha256 | `ffd491e3ac10d08f55e3522859a43313743cd77fe51a40c0c0076391d9f64824` | `ffd491e3...` |

Byte-identical. The single collection error is the pre-existing CE-01 `weaver.autonomy`
module-vs-package collision (`tests/test_autonomy.py`), reserved to the sovereign.

### 9.4 PR #308 independently re-verified on the current base (integration, not isolation)

Method (isolated worktree, no mutation of `main`):

```
git worktree add --detach /tmp/wt308 ccbec40
git fetch origin refs/pull/308/head:refs/remotes/pr/308   # head 81c9d9d55a3a8153a9ce11575d3d57f9cd65f78e
git -c user.name=openhands -c user.email=openhands@all-hands.dev merge --no-edit refs/remotes/pr/308   # rc=0, auto-merge, no conflict
```

| check | `main` `ccbec40` | composed (`ccbec40` + #308) |
|---|---|---|
| `wc -l api/main.py` | 2602 | **2427** |
| `python -m py_compile api/main.py api/ceo_chat_routes.py` | OK | **OK** |
| `pytest tests/architecture -q` | 10 passed / 1 failed | **11 passed** |
| `pytest tests/test_tool_execution_perimeter.py -q` | (part of 41P) | **31 passed** |
| `git ls-files \| scripts/cp10_mutation_boundary_policy.py --judge` | exit 0 | **exit 0** |
| full suite | 17F / 1485P / 20S / 1E | **16F / 1486P / 20S / 1E** |

Composed failing/error node set: **17 nodes**, sha256
`a5df9a25e3cfefd7ce90aa7966a751ffc53acb3e2efa5dd65bdf240223bd2287` - **byte-identical to Sec. 6,
7 and 8's composed-node hash**. Set delta (`main` -> composed): the only removal is
`tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`; **zero**
nodes added, **zero** new errors. This reproduces the recorded hash a third time on a fresh clone.

### 9.5 Gate-2 production boundary (re-derived, unchanged)

`python scripts/gate2_production_observation.py` (read-only, no Vercel credential):

| boundary | classification |
|---|---|
| current main resolved | **VERIFIED** |
| `main` -> deployment identity | **STALE** (deployed SHA predates `ccbec40`) |
| deployment build output observed | **BLOCKED** (deployment URL 302 -> Vercel SSO) |
| alias reachable (`https://arkadia-prism.vercel.app/`) | **VERIFIED** (HTTP 200) |
| alias -> deployment SHA binding | **UNKNOWN** |
| build <-> source lineage | **UNKNOWN** |
| browser-rendered UI correctness | **UNKNOWN** |
| production acceptance | **NOT CLAIMED** (human authority) |

Marker-set lineage, SG-04 gate and the source-lineage closure all behave as recorded in Sec. 7-8.
This remains a **provider boundary** (no Vercel credential), not repository work. Repeating the
pass cannot convert `STALE`/`BLOCKED`/`UNKNOWN` into `VERIFIED`.

### 9.6 Repository guards

| guard | result |
|---|---|
| CP10 mutation boundary judge (`git ls-files` on `main`) | **exit 0 - PASS** |
| `scripts/agents_md_encoding_audit.py` | **Cyrillic 0, alterations 0, oracle reproduced=True, exit 1** (clean-and-corroborated status) |
| `api/main.py` line count | 2602 (budget defect covered by #308) |

### 9.7 Pass summary

- BASE_MAIN unchanged at `ccbec40`; no merge; no new open PR; the only mutation in this pass is
  this record.
- Baseline reproduced **byte-identically** (18 nodes, `ffd491e3...`) on a full clone with the
  dependency-complete environment.
- **PR #308** independently re-verified on the current base: 2602 -> 2427, architecture **11/11**,
  perimeter **31 passed**, CP10 exit 0, composed node set exactly **-1 / +0**, composed-node hash
  `a5df9a25...` reproduced a **third** time.
- Gate-2 production boundary remains `STALE`/`BLOCKED` at the provider boundary.
- **Next authorized action:** sovereign review + merge of **PR #308** (the sole remaining
  repository-owned gate defect). After it lands, re-measure `pytest tests/architecture` (expect
  **11/11**), `python -m py_compile api/main.py` (expect OK),
  `scripts/cp10_mutation_boundary_policy.py --judge` (expect exit 0), and re-derive the full-suite
  node set (expect **17 nodes**).
- **Forbidden for the next pass:** merging anything; touching the sovereign-reserved governance
  failures; re-opening a duplicate budget PR; synthesizing a fingerprint without the
  dependency-complete environment **or** without stating clone depth.

## 10. Seventh pass — integration composition of #308 + #311 (new finding)

Observation timestamp: **2026-10-05T11:05Z** (session clock). `BASE_MAIN` unchanged at
`ccbec4061d66ff6a13dba16b3d2c24b124132102`; no merge; no push; no production code touched.

### 10.1 Base re-verified

- `main` @ `ccbec40`; local HEAD == origin/main; 0 ahead / 0 behind; working tree clean.
- `api/main.py` = **2602** lines (budget **2600**) — defect unchanged, still carried solely by #308.
- `python -m py_compile api/main.py` → OK.
- `git ls-files | python scripts/cp10_mutation_boundary_policy.py --judge` → **exit 0 (PASS)**.
- `pytest tests/architecture -q` → **1 failed, 10 passed** (the budget node only).
- `pytest tests/test_m02a_ci_gate_integrity.py -q` on `main` → **60 passed** (so any m02a failure
  below is attributable to a candidate, not to `main`).
- Full suite `python -m pytest tests/ -q -rEf --continue-on-collection-errors` →
  **17 failed, 1485 passed, 20 skipped, 1 error**; node set **18 nodes**, sha256
  `ffd491e3ac10d08f55e3522859a43313743cd77fe51a40c0c0076391d9f64824`.
  This reproduces the sixth pass **byte-identically** on a **full** (unshallowed) clone.

### 10.2 PR inventory correction (live, `state=open`)

The sixth pass (§9) still listed **7** open PRs including #310. A live query at `ccbec40` returns
**6**; #310 merged as commit `ccbec40` itself ("admit alxai/ to the CP10 mutation boundary"), so it
is no longer open. Open: **#306, #307, #308, #309, #311, #312** (this record).

Stacking: **#309** base=`main` (mergeable), **#311** base=`feat/weaver-console-completion-trajectory`
— i.e. #311 is **stacked directly on #309's head branch**, not on `main`. Any integration analysis
of #311 must compose it with #309 in that order.

### 10.3 New integration finding — `api/main.py` composes, but CP10 does not

Both **#308** (`api/main.py` +4−179, extracting `ceo_chat_routes.py`) and **#311**
(`api/main.py` +5, mounting `api.google_workspace_routes`) edit `api/main.py` in disjoint regions
(#311 at ~line 373, near the top lifespan mounts; #308 removes the CEO-chat handlers). Composed in
the reachable order **main → #308 → #311** in a scratch worktree (`443aeda2`):

| measurement | result |
|---|---|
| textual merge conflicts | **none** (both merges clean) |
| `api/main.py` after both | **2432** lines ≤ **2600** — budget holds |
| `py_compile api/main.py` + workspace routes | OK |
| `pytest tests/architecture -q` | **11 passed** (budget defect cleared by #308) |
| **CP10 judge over composed `git ls-files`** | **exit 1 — FAIL** |
| `pytest tests/test_m02a_ci_gate_integrity.py -q` composed | **3 failed, 57 passed** |

CP10 rejects two paths: `google_workspace/Code.gs`, `google_workspace/appsscript.json`. #311
introduces a **new tracked top-level prefix `google_workspace/`** that is absent from
`LEGIT` in `scripts/cp10_mutation_boundary_policy.py`. The failing nodes are exactly:

- `test_allowlist_admits_every_tracked_top_level_prefix`
- `test_allowlist_covers_every_tracked_surface`
- `test_delegated_verdict_admits_every_tracked_surface`

**Reachability — this is a real gate, not theoretical.** `.github/workflows/sg-02-fe-2-v.yml`
triggers on `pull_request.paths` including `api/**` (and `tests/**`); #311 touches `api/main.py`,
so the CP10 gate is expected to run on #311 **and on `main` after it merges**. This is the same
GATE-10 omission class the repository has already recorded four times (`alxai/`, `knowledge/`,
`spiral_grove/`, root docs) — and #310 (`ccbec40`) is the immediately preceding instance of it.

**Consequence for the queue:** #311 is currently `mergeable=True`, meaning GitHub reports no
*textual* conflict, yet merging it would red `main`'s CP10 gate. This is precisely the
"git conflict-free is not proof of semantic compatibility" case. #311 needs a **companion CP10
allowlist change** (admit `google_workspace/`) *before* it is safe to merge, or the allowlist
omission will be repaired in a follow-up.

### 10.4 Runtime proof of #308 re-confirmed

`from api.main import app` + `TestClient` on the composed #308 tree:
`POST /api/ceo/chat` → **401** (routed, auth-gated exactly as on `main`), against
`POST /api/commune/resonance` → **400**. The magnitude-179 removal of `api/main.py` changes no
observable route behaviour — the extraction is a pure relocation.

### 10.5 Classification

| item | class |
|---|---|
| `main` @ `ccbec40` resolved | **VERIFIED** |
| #308 fixes the budget defect, no regression | **VERIFIED** (independent, current base) |
| #308 + #311 `api/main.py` budget composes (2432) | **VERIFIED** |
| #311 introduces a CP10 allowlist omission | **VERIFIED** (judge exit 1 + 3 failing nodes, runnable gate) |
| #311 safe to merge as-is | **CONTRADICTED** (needs companion CP10 admission) |
| Gate-2 deployment parity | **STALE / BLOCKED** (unchanged; provider boundary) |
| production acceptance | **NOT CLAIMED** (human authority) |

### 10.6 Next authorized action

1. **Sovereign review + merge of PR #308** — the sole remaining repository-owned gate defect on
   `main` (`api/main.py` 2602 > 2600). Build `main` → #308 → #311 and expect the budget to hold at
   **2432**.
2. **PR #311 requires a companion CP10 admission of `google_workspace/`** before merge. This is a
   bounded, pre-authorized gate-hygiene change in the established `gateNN/<slug>` form:
   add `google_workspace/` to `LEGIT`, extend the fitness coverage, verify
   `python scripts/cp10_mutation_boundary_policy.py --judge` → exit 0 over a tree containing
   `google_workspace/`, and confirm `test_m02a_ci_gate_integrity.py` → 60 passed. Do **not** merge
   #311 without it.
3. Re-measure after #308 lands: `pytest tests/architecture` (expect **11/11**), `py_compile`
   (OK), CP10 judge (exit 0), full-suite node set (expect **17 nodes**).

**Forbidden for the next pass:** merging anything; pushing to `main`; touching the
sovereign-reserved governance failures (`test_verification_review_boundary`,
`test_agents_md_encoding_adjudication`, `test_steward_filter`, `weaver/autonomy`); re-opening a
duplicate budget PR; weakening the CP10 gate by removing a genuinely-tracked surface; synthesizing
a fingerprint without the dependency-complete environment **or** without stating clone depth.
