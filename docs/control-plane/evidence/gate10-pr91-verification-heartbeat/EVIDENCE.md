# GATE-10 — PR #91 Independent Verification Heartbeat — Evidence

**Gate:** GATE-10 (Governed Execution) — CP10 + Weaver MVP2 CI gate integrity
**Authorization:** Human sovereign (review/merge retained exclusively by sovereign)
**BASE_MAIN:** `6038989dc57e871331107b7dde9fc3d749d4d4aa`
**Verified PR head:** `d7bf69c0ebb1bcaf2a5334681fa3c9deb075d2a9`
**Branch:** `gate10/cp10-weaver-ci-gate-integrity` → PR #91
**Verification branch:** `continuity/vault-leak-ledger` (this record; based directly on `main`)
**Merge:** not performed. Any merge is human-only.

This pass is a read-and-verify heartbeat. It re-derived PR #91's claims from live
repository and CI evidence rather than accepting the prior session's summary.

## Repository binding

- `origin/main` = `6038989dc57e871331107b7dde9fc3d749d4d4aa`, real commit
  ("Merge PR #90: GATE-00 closure — recover EDEN-OPS-02 onto canonical main").
- PR #91: `state=open`, `draft=false`, `mergeable=true`, `mergeable_state=clean`,
  3 commits, base `6038989`. This satisfies contract step 03 (PRESERVE CONTINUITY).

## Independent baseline fingerprint

Both suites run from a clean checkout with `--continue-on-collection-errors`,
same interpreter, same dependency set.

| Tree | Result |
|---|---|
| `main` @ `6038989` (clean clone of `origin/main`) | **804 passed / 54 failed / 12 skipped / 2 errors** |
| PR #91 head `d7bf69c` | **813 passed / 51 failed / 12 skipped / 2 errors** |

The `main` figure reproduces the contract's recorded baseline exactly
(`main := 6038989`, `804 passed / 54 failed / 12 skipped / 2 collection errors`).

### Failure-set delta (set difference, not count arithmetic)

Full failing-test name sets were diffed:

- Present on `main`, absent on head (**repaired by PR #91**): exactly 3 —
  - `tests/test_m02a_ci_gate_integrity.py::test_trajectory_next_move_is_m02a`
  - `tests/test_weaver_mvp2_05.py::test_semantic_graph_is_read_only_and_non_authoritative`
  - `tests/test_weaver_mvp2_07.py::test_frontend_uses_existing_execution_routes_only`
- Absent on `main`, present on head (**newly failing**): **none**.
- Collection-error set identical on both: `tests/test_autonomy.py`, `tests/test_render_codex.py`.

Conclusion: +9 passed / −3 failed is fully explained by the 3 targeted repairs.
No pre-existing failure fingerprint changed. No regression, no masked failure.

## Live CI state — head `d7bf69c`

`mergeable_state: clean`. All check runs completed successfully:

| Check | Result |
|---|---|
| `validate` (CP10 / SG-02-FE.2-V) | success |
| `mvp2-validation` (Weaver MVP2) | success |
| `Vercel Preview Comments` | success |
| commit status `Vercel` | success |

## Corroboration of the root cause from live main logs

Run **`36399594533`** — `sg-02-fe-2-v.yml` on `push` to `main` @ `6038989`
(pre-PR-#91 canon, therefore main's own state): **failure**, job `108854043631`.

- Step `CP10 mutation boundary` (31) → **failure**; `Enforce CP10 executable gates` (34) → failure.
- Step `CP10 browser route verification` (28) → **success**; `Grove contracts` (18) → **success**.

The mutation-boundary log shows the diagnostic printing all 8 changed files while only one
path was the true non-allowlisted offender:

```
Unexpected path outside legitimate repository surfaces:
docs/architecture/EDEN-OPS-02_IMPLEMENTATION.md
enterprises/eden-food-systems/tasks.seed.json      <-- the only non-allowlisted surface
solspire/eden_ops_02.py
...
```

That 8-file EDEN-OPS-02 set is the exact fixture grazing PR #91's new regression test
`test_continue_on_error_gates_are_still_enforced_by_outcome`, and `enterprises/` is the
surface PR #91 adds to the policy allowlist. The root cause is therefore established from
canonical main's own CI history, independent of the PR's own narrative.

Also verified: CP10 fails on `main` on the 5 most recent `push` runs
(`36399594533`, `36372514094`, `36357932667`, `36357049827`, `36355823864`) — the gate was
red on canon before this PR.

## Assertion-substance check (guards are not weakened)

PR #91 replaces unsatisfiable/absent-surface assertions with assertions against **real
shipped source**. Spot-audited targets on canon:

- `solspire/semantic_graph.py:119` — the "not an authoritative graph store" limitation
  string the MVP2-05 assertion now matches.
- `web/public_prism/src/pages/ProjectDashboard.tsx` — composes `execBase = ${base}/execution`
  and calls `pass-spec`, `approval`, `readiness`, `execute`; MVP2-07 now asserts that
  composition instead of the non-existent literal `/execution/pass-spec`.

Prior session's mutation audit (independently re-confirmed as the basis for the guards):
removing browser enforcement → `test_continue_on_error_gates_are_still_enforced_by_outcome`
fails; reverting the retired-marker guard → `test_ci_does_not_assert_retired_private_workspace_marker`
fails. Both mutations were restored; the guards bind behaviour.

Prior session's CI evidence, consistent with this pass: Weaver MVP2 pre-fix run
`36406537033` failure (`pytest: command not found`, exit 127 — the workflow had installed
`requirements.txt`, which contains no test runner); CP10 post-fix run `36406687605`
(`pull_request`), all 34 steps success.

## Bounded continuity note — `vault/` artifact staging gap

Not part of PR #91's scope, recorded separately (see `PARKING_LOT.md`, now populated).

`pytest tests/` from the repository root writes real note files through
`knowledge/vault.py:17` (`VAULT_ROOT = Path("vault")`, cwd-relative). This pass's own
full-suite run created **35 untracked files** under `vault/Ideas/` and `vault/Projects/`,
including synthetic private-boundary canary material
(`ARKADIA_PRIVATE_CANARY_USER_A/B`, `SearchBoundaryQuartz7`, `PrivateBoundaryZephyr9`,
`user_54267acf` + "secret plans").

`vault/` is not covered by `.gitignore`. Verified directly this pass:

```
$ git check-ignore -q vault/Ideas/2026-01-01_probe.md  ->  NOT ignored
$ git check-ignore -q data/runtime.db                  ->  ignored
$ git add --dry-run vault/Ideas/2026-01-01_zz_probe.md ->  add 'vault/Ideas/...'
```

So a routine `git add -A` stages them. A pass that commits without inspecting `git status`
would fold synthetic private-vault material into canon — the same class of exposure
corrected by hand at the end of the prior GATE-10 pass.

Disposition this pass: artifacts **removed** with `git clean -fd vault/` (untracked only),
leaving the 14 tracked scaffold files (`.gitkeep` set, `vault/Index/README.md`,
`vault/Templates/*`) intact. Working tree confirmed clean afterwards. No `.gitignore`
change was made — that is a separate bounded task, deliberately not folded into a
verification pass.

## Architecture state

`python -m pytest tests/architecture -q` → **2 failed / 9 passed**, identical on `main` and on
the PR head:

- `test_no_layer_inversions`
- `test_api_main_line_count_within_budget` — `api/main.py` is 2607 lines vs a 2600 budget
  (test docstring still reads "~2506 lines"). PR #91 does not touch `api/main.py`;
  pre-existing on canon. `python -m py_compile api/main.py` OK.

`tests/architecture` is therefore 9/11 in reality; `.bootstrap/01_STATE.md`'s "10/10" and the
contract's "9/10" both disagree with the code. Code is authoritative. Recorded in
`PARKING_LOT.md`, not fixed here.

## Governance boundary

PR #91's policy change is an **allowlist widening**, not an authority change:
`FORBID_V3` remains enforced independently of the allowlist (`SolSpireExperienceV3.tsx`
still rejected; `vault/Ideas/x.md` and `unknown/path.txt` still rejected).
No new mutation path, no new authorization path, no identity-boundary change,
no constitutional reinterpretation detected.

## Authorization required

Sovereign review and merge of PR #91. No merge or other consequential action performed by
the agent.
