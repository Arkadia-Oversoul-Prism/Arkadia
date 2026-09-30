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

## CP10 mutation-boundary allowlist is an incomplete inventory (CI red on `main`)

Observed (2026-09-28): `SG-02-FE.2-V` is **red on canonical `main`** @ `a26af408` and on the
preceding `d48ad0e`. The "CP10 mutation boundary" step rejected `AGENTS.md` as an
"Unexpected path outside legitimate repository surfaces". Both merges (#97, #104) were
legitimate product work; the allowlist simply never admitted top-level `*.md`.
File: `.github/workflows/sg-02-fe-2-v.yml`, `scripts/cp10_mutation_boundary_policy.py`
Workstream: GATE-10 (governed execution) — CP10 gate integrity
Priority: high

_In flight:_ branch `gate10/cp10-allowlist-root-docs`, **PR #105** (evidence
`docs/control-plane/evidence/gate10-cp10-allowlist-root-docs/EVIDENCE.md`).
Three passes, all on this one branch:
1. admit root `*.md`;
2. admit `knowledge/`, `spiral_grove/`, root `conftest.py`;
3. **stop patching symptoms** — the allowlist is now a *complete inventory* of tracked surfaces
   (1394 paths, 0 rejected), with tests asserting the invariant against `git ls-files` and
   against the workflow mirror, plus lookalike negatives and a V2/V3 `forbid` assertion.
CI on the branch is **green** - run `36515066702` @ `3a01df4`, job `validate` = success, all 34
gated steps pass including step 31 `CP10 mutation boundary` and step 34 `Enforce CP10 executable
gates`. Awaiting sovereign review and merge. **Do not start a second fix for this.**
Merge-order hazard: `docs/phase1/CONTINUATION_LEDGER.md` is appended by both #105 and #109 -
textual conflict at EOF; suggest merge #105 first, then rebase #109. Sovereign decision.

Composability risk recorded (EVIDENCE §7): the policy is duplicated in the workflow and the
module, held together only by a test. Structural fix — workflow executes the tested module,
shell literal kept as a mirror assertion — is the recommended follow-on **separate** bounded PR.
Do not fold it into #105; that would change gate execution semantics while restoring a red `main`.

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

## `weaver.autonomy` is two objects under one name — the module is shadowed and unreachable

Discovered: 2026-09-30, pass `gate-hygiene/bootstrap-scope-reconciliation-01`. Filed, not
repaired — the repair is a governance decision, not a bug fix.

`weaver/autonomy.py` (a module) and `weaver/autonomy/` (a package) both exist. Python
resolves `weaver.autonomy` to the **package**, so the module is shadowed and cannot be
imported by its dotted name. Two live consumers import from the shadowed module and both
fail:

- `tests/test_autonomy.py:2` → `ImportError: cannot import name 'load_autonomy_config' from
  'weaver.autonomy'` (one of the two collection errors in the baseline fingerprint)
- `weaver/run_autonomy.py:3` → same import path, same failure

The two objects disagree about what autonomy *is*. The package's `__init__.py` declares
`__status__ = "disabled"` and "Guards and proposal engine only. **No execution hooks.**"
The module it shadows is exactly an execution hook: `run_scheduled_once()` drives
`RecursiveEngine` and commits through `git_ops.last_commit_messages()`.

So the repair is not mechanical. Choosing the package as canonical means autonomous
execution is not reachable — consistent with `__status__ = "disabled"`, but it strands
`tests/test_autonomy.py` and `weaver/run_autonomy.py`. Choosing the module as canonical
means autonomous execution *is* reachable and the package's declaration is wrong — which is
an authority-model question (who may originate an autonomous commit?) and is reserved to the
sovereign.

**Awaiting:** a sovereign ruling on which object is canonical. Until then
`tests/test_autonomy.py` stays a collection error and `weaver/run_autonomy.py` stays broken.

Evidence: `docs/control-plane/evidence/gate-hygiene-bootstrap-scope-reconciliation-01/EVIDENCE.md` §6.

## Spiral Grove registry: declared prerequisite order ≠ returned order; cycle guard red on `main`

Discovered: 2026-09-30, pass `gate-hygiene/bootstrap-scope-reconciliation-01`. Filed, not
repaired — the repair is a product/contract decision on a CP10-fenced path.

`test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow` is
classified `DRIFT`. Measured at `002b189`: the registry declares
`cap-ai-creative-workflows → [cap-ai-prompt-engineering, cap-digital-intelligence,
cap-content-systems]`, while the graph returns
`[cap-digital-intelligence, cap-ai-prompt-engineering, cap-content-systems]` — i.e. it
topologically sorts rather than preserving declaration order. The same module's non-catalog
fixture passes (`test_registry_reports_ready_prerequisites` green), and
`test_registry_rejects_prerequisite_cycle` is red on `main`, so the catalog contains a cycle
or self-edge that the guard detects only on the catalog path.

A topological order is a defensible contract for a *learning path* and a contradiction for a
*declaration-order* contract. `SH-02`'s disposition pass already excluded these nodes ("the
behaviour itself is in question"); the ledger class is `DRIFT`.

**Awaiting:** a ruling on which contract the Spiral Grove registry means.

Evidence: `docs/control-plane/evidence/gate-hygiene-bootstrap-scope-reconciliation-01/EVIDENCE.md` §8.
