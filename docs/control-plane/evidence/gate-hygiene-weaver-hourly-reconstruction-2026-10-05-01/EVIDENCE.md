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

### Open PR inventory (6, all `mergeStateStatus: UNSTABLE`)

| PR | branch | scope | disposition |
|----|--------|-------|-------------|
| #306 | `feat/oversoul-prism-9cell-conformance` | Prism 9-cell conformance harness (research-only) | independent, no conflicting files |
| #307 | `feat/console-g12-idempotent-capture-sync` | G12-A idempotent capture reconciliation | independent |
| #308 | `gate-hygiene/api-main-budget-ceo-chat-extraction-01` | restore `api/main.py` ≤ 2600 | **fix for measured defect — see below** |
| #309 | `feat/weaver-console-completion-trajectory` | Weaver Console trajectory routing | independent |
| #310 | `gate-hygiene/cp10-admit-alxai-surface-01` | admit `alxai/` to CP10 boundary | **fix for measured defect — see below** |
| #311 | `feat/weaver-attention-bus-google-workspace` | Google Workspace attention bus | **stacked on #309's branch** (base = `feat/weaver-console-completion-trajectory`) |

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
