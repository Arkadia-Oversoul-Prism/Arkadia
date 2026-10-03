# MIE Gate 05 — PR #243 branch refresh (stale-branch failure repair)

Observation time: 2026-10-03T18:0x Z
Source of truth: live repository + CI check-runs (read-only inspection).

## Classification

`FAILED` → repair proposed. The failure is a **stale-branch** condition, not a defect in the
Gate 05 change loop.

## Observed defect

`feature/mie-mvp-01` (PR #243, head `813eaed34a4cb9effe12559630bde36ab01429e5`) is **308 commits
behind** `main` (`357fbd83001924e909979fbaebdedbd991a2aadb`; PR base `7f2d2657`). The branch
predates the version-catalog alias repair `1a2fc21` (`fix MIE duplicate junit catalog alias`),
which removed the duplicate `junit` alias from `sonata-android/gradle/libs.versions.toml`.

- Branch head catalog: `junit` alias present at **line 16 and line 26** → invalid TOML.
- `main` catalog: `junit` alias present at **line 16 only**.

## Why CI reports a contradictory result

Two workflows run for the same head SHA:

| Run | Event | Head | Result |
|---|---|---|---|
| 37142270132 | `pull_request` | `813eaed` | success |
| 37142267190 | `push` | `813eaed` | **failure** — `junit previously defined at line 16, column 1` |
| 37142127800 | `pull_request` | `3de223c` | success (cited by the PR body) |

The `pull_request` workflow builds the **merge result** (branch merged into current `main`), where
the alias repair is already present — so it passes. The `push` workflow builds the **branch head**
in isolation, where the duplicate is still present — so it fails. The PR's check rollup is therefore
genuinely `FAILURE` (GraphQL `statusCheckRollup.state`), even though the head commit also carries a
green check of the same name.

## Repair

Merge current `main` into the branch and push to the PR's own head branch — no rewrite, no
force-push, no new PR. The merge resolves the catalog duplicate.

Measured locally: the refreshed tree is **byte-identical** to the PR merge result GitHub already
builds and passes:

```
refreshed tree      = ff568faea3753497b5fe0bc646274ecd5862e793
refs/pull/243/merge = ff568faea3753497b5fe0bc646274ecd5862e793
```

Because the trees are identical, PR run `37142270132` (`success`) is direct evidence for the
refreshed tree; the post-push CI run is confirmatory, not the primary evidence.

Branch-only content is unchanged by the merge — the refresh introduces **no** change to the Gate 05
change loop. `git diff` between the PR head tree and the refreshed tree touches only
`sonata-android/gradle/libs.versions.toml` (1 deletion).

## Measured outcome (post-refresh)

Refreshed head `8cf28367fbf2a103def2e828024acc181b5b5b55`; PR base `357fbd8`. The `push`-event
Android run that previously failed on the duplicate alias now succeeds on the refreshed head.

| Run | Event | Result | Before refresh |
|---|---|---|---|
| 37144173474 | `push` | **success** | 37142267190 `failure` (`junit previously defined at line 16`) |
| 37144174132 | `pull_request` | success | 37142270132 success |
| 37144174123 | `pull_request` `security-secret-scan` | success | success |
| 37144173462 | `push` `Build APKs` | see PR | pre-existing / path-unrelated |

Full suite on the refreshed tree (`python -m pytest tests/ -q --continue-on-collection-errors`):
**23 failed / 1368 passed / 19 skipped / 1 error** → 24 failing+error nodes,
`sha256 b1750f96344a34194e6e83e82974518bb34438c69846d4a22736d22e9fca2dc1`.
PR #245 measured `main` @ `357fbd8` at 25 nodes; this tree is a **subset** of that set, the
difference being the order-dependent `test_agent_loop_does_not_mutate_repository` node. No
new failing node is introduced by this refresh.

Architecture fitness: `python -m pytest tests/architecture -q` → **11 passed**.
CP10 judge on the PR diff → **PASS** (`Mutation boundary PASS`).
`python -m py_compile api/main.py` → OK (2582 / 2600 budget).

Android verification is **environment-blocked locally** (no JDK present); the CI Android runs
above are the evidence source, not a local build.

## Scope / non-goals

- In scope: branch refresh + this evidence record.
- Non-goal: no change to Gate 05 logic, no test change, no scope expansion, no unrelated debt repair.
- This does **not** claim device verification. Gate 05 remains `IMPLEMENTED / DEVICE PENDING`;
  physical-device verification is the next boundary and is not asserted here.

## Authority

Human sovereign retains merge authority. This PR is not self-merged.
