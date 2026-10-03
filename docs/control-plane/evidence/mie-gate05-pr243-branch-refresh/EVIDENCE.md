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

## Scope / non-goals

- In scope: branch refresh + this evidence record.
- Non-goal: no change to Gate 05 logic, no test change, no scope expansion, no unrelated debt repair.
- This does **not** claim device verification. Gate 05 remains `IMPLEMENTED / DEVICE PENDING`;
  physical-device verification is the next boundary and is not asserted here.

## Authority

Human sovereign retains merge authority. This PR is not self-merged.
