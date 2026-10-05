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
