# Parking Lot
> Observed issues that are outside current scope.
> No investigation. No fixing. Just record and continue.
> Issues here are picked up during planning, not during implementation sessions.

---

## Format

```
## [short title]
Observed: [what was noticed]
File: [path, if applicable]
Workstream: [which workstream should handle it, if known]
Priority: [low / medium / high]
```

---

## Open Items

## CP10 mutation-boundary allowlist omits root narrative docs (CI red on `main`)

Observed (2026-09-28): `SG-02-FE.2-V` is **red on canonical `main`** @ `a26af408` and on the
preceding `d48ad0e`. The "CP10 mutation boundary" step rejected `AGENTS.md` as an
"Unexpected path outside legitimate repository surfaces". Both merges (#97, #104) were
legitimate product work; the allowlist simply never admitted top-level `*.md`.
File: `.github/workflows/sg-02-fe-2-v.yml`, `scripts/cp10_mutation_boundary_policy.py`
Workstream: GATE-10 (governed execution) — CP10 gate integrity
Priority: high

_In flight:_ branch `gate10/cp10-allowlist-root-docs` (evidence
`docs/control-plane/evidence/gate10-cp10-allowlist-root-docs/EVIDENCE.md`) adds
`[^/]+\.md$` to both the policy and the workflow's inline copy, and widens the existing
anti-drift guard's corpus. Do not start a second fix for this.

## Baseline test debt at `a26af408` is unclassified (49 failures + 2 collection errors)

Observed (2026-09-28): full suite on `main` @ `a26af408` yields 49 failed / 903 passed /
12 skipped / 2 errors; collection errors in `tests/test_autonomy.py` and
`tests/test_render_codex.py`. Several failures look like stale assertions (e.g.
`test_ais_capability_profile_onboarding`, `test_ais_w2_living_gate_grove_handoff`) rather
than defects, but that is unverified. Fingerprint of all 51 failing/error nodes:
`sha256=256204af4082a70f062ed6004fd0c51c126a14262a072afdac9279ce158c3fca`.
File: `tests/` (repository-wide)
Workstream: unassigned — candidate standalone test-hygiene workstream
Priority: medium

_Do not fold this into an unrelated architectural gate._ Classify by real defect vs stale
assertion before repairing; the fingerprint above is the regression boundary to protect.

---

## Closed Items

## `api/main.py` exceeded its registered 2600-line budget

Observed (2026-09-28): `tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`
failed on `main` @ `6038989` — `api/main.py` was 2607 lines against a 2600 budget.

Resolved: 2026-09-28, PR #94 `gate07/main-py-line-budget-restore`. On `main` @ `1d4ed03`
`api/main.py` is **2519/2600 lines** and the architecture gate is green. Closed after
re-verification (`wc -l api/main.py` -> 2519).

## `tests/architecture` count drift (prose said 10/10, suite had grown)

Observed (2026-09-28): `tests/architecture` yielded 9/11 on `main` @ `6038989`
(`test_no_layer_inversions`, `test_api_main_line_count_within_budget`), while
`.bootstrap/01_STATE.md` claimed 10/10 and the WEAVER contract baseline recorded 9/10.
The prose disagreed with the code and with itself.

Resolved: 2026-09-28, PR #98 `gate-arch/nodes-layer-inversion-deinversion` fixed the layer
inversion, and PR #94 restored the line budget — the gate is now **11/11** on
`main` @ `1d4ed03`. The remaining stale prose (including an outdated spine-test count) was
reconciled in the `state-honesty/doc-fitness-count-reconciliation` pass, which also added
an explicit "derive live status from the repository, not this prose" banner to
`CURRENT_STATE.md`.

## Test runs write private material into the tracked-adjacent `vault/` tree

Observed: Running `pytest tests/` from the repository root wrote real note files
into `vault/Ideas/` and `vault/Projects/` (35 untracked files after a full-suite run),
including synthetic private-boundary canary material (`ARKADIA_PRIVATE_CANARY_USER_A/B`,
`SearchBoundaryQuartz7`, `PrivateBoundaryZephyr9`, `user_54267acf` + "secret plans").
`knowledge/vault.py` resolved `VAULT_ROOT = Path("vault")` relative to the process cwd,
so tests did not sandbox their writes; `test_isolation.py` swapped `ARKADIA_DB_PATH` to a
tempdir but the filesystem vault was unaffected. `vault/` is not gitignored, so the files
were stageable by any routine `git add -A`.

Resolved: 2026-09-28, branch `gate02/conftest-vault-sandbox`. A root `conftest.py` now
redirects `ARKADIA_DB_PATH` and `VAULT_ROOT` to a throwaway directory in a session-scoped
autouse fixture, before test modules are imported. Controlled A/B on the same commit
(`e9257bf`), each run starting from a cleaned `vault/`: **35 files leaked without the
fixture, 0 with it** (counted as `find vault -name '*.md' -not -path 'vault/Templates/*'
-not -path 'vault/Index/*'`; the base figure is deterministic across runs), with an
identical test outcome (842 passed / 51 failed / 12 skipped / 2 errors) and an identical
failing-node-ID hash on both sides. `.gitignore` additionally gains `tests/_spine_test.db*`
for SQLite WAL/SHM sidecars.

Evidence: `docs/control-plane/evidence/workstream-b-vault-sandbox/EVIDENCE.md`.

Defence-in-depth still available if desired: ignore patterns for `vault/*/2*.md` while
keeping the tracked scaffold (`.gitkeep`, `vault/Templates/*`, `vault/Index/README.md`).
Not applied — the fixture removes the cause rather than masking it.
