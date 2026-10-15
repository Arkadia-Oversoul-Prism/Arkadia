# Candidate acceptance state — three validated, publication NOT authorized

**Frozen base:** `7580bd8f0ca2925518d78775f9a323ff0df8bc66` (unchanged)
**Recorded:** 2026-10-15

## Control state

| Control | Required state | Observed |
|---|---|---|
| `main` | Frozen at `7580bd8f` | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` |
| Three resolution commits | Local-only until push authorized | `git branch -r --contains` → **empty for all three** |
| #525 | Hold | not integrated |
| #535 | Draft, unchanged | `8b6eadd77aa1`, draft |
| Production | No deployment | no deploy performed |
| Other PR dispositions | Unchanged | none closed/retargeted |

## Candidate acceptance (candidate-level only)

The sovereign recommends acceptance of the three commits as **validated candidates**. This is
not evidence that they are published, that remote CI has passed, or that they are
production-ready. Publication remains unauthorized; merge remains a separate decision.

| Candidate | Commit | Recommendation |
|---|---|---|
| #482 repair | `c770df2021226331fb31f10e833462f2bd43d1fb` | accept as candidate |
| #497 + #505 | `53f5ac6144857616f487bb4e32c5a08b71bbc525` | accept as candidate; publish as ONE unit |
| #511 + #514 | `e679c3bb4ba0343dcef555f36eb36c4ca0e15d38` | accept as candidate; publish as ONE unit |

## What remote CI would confirm on publication (pre-verified triggers)

The repair branch's `provider-routing.yml` `pull_request.paths` is **self-selecting** — it names
the workflow file, `tests/test_history_depth_ci_wiring.py`, and `AGENTS.md`. A PR from this
branch therefore runs the very gate the repair modifies, and the repair's own guard is selected.
The filter grew 8 → 10 entries.

| Workflow | Triggers | PR filter paths |
|---|---|---|
| `provider-routing.yml` | `pull_request`, `workflow_dispatch` | 8 → **10** (repair branch) |
| `prism-console-contract.yml` | `pull_request`, `push`, `workflow_dispatch` | 5 |
| `sg-02-fe-2-v.yml` | `push`, `pull_request`, `workflow_dispatch` | 30 |

Note: `provider-routing.yml` carries **no `continue-on-error`** on its suite step, so a red
result is a real signal, not a suppressed one. It is also expected to remain red on pre-existing
debt unrelated to this repair — the repair removes the four clone-depth nodes, it does not clear
the repository's baseline failures. The CI verdict must be read as a **node-set delta against
baseline**, not as a green/red binary.

## Unresolved records (unchanged)

- **#501** — 84-line evidence document absent from `main` and from #535. Gap retained explicitly.
- **#503** — `.github/workflows/eaa-base-baseline.yml` absent from `main`, present in #535.
  Workflow ownership and its dependency on #535 stay unresolved until the source-PR disposition
  is finalized.
- **#525** — hold. Arrangement D (scratch worktree, not committed) shows a single-mount delivery
  is plausible but duplicates presentation logic; it is **not** an accepted implementation. Next
  iteration must define the stage-list rendering contract once, preserve exactly one mount, and
  avoid duplicating presentation between the Lab and Weaver read models. The original #525 branch
  stays unchanged until a replacement design is independently validated.
- **#535** — draft at `8b6eadd7`; the allowlist decision remains separate.
- Remaining inventory: no blanket merge or closure authorization follows from these three
  candidate decisions.

## Independent-verification caveat (recorded, not resolved)

The acceptance recommendation above rests on this session's reported evidence. The sovereign
states they have not independently inspected the commit diffs or reproduced the tests. Every
claim is reproducible from the artifacts:

```
git show c770df2021226331fb31f10e833462f2bd43d1fb
git show 53f5ac6144857616f487bb4e32c5a08b71bbc525
git show e679c3bb4ba0343dcef555f36eb36c4ca0e15d38

# #482's decisive reproduction (shallow vs full history)
git clone --depth 1 <repo> /tmp/s && cd /tmp/s
python -m pytest -q tests/test_agents_md_encoding_adjudication.py   # 4 failed, 13 passed, 6 skipped
git fetch --unshallow && python -m pytest -q tests/test_agents_md_encoding_adjudication.py  # 18 passed, 5 skipped

# the two units
python -m pytest -q tests/test_console_shell_nav_contract.py        # 38 passed
python -m pytest -q tests/test_console_return_to_contract.py \
  tests/test_console_surface_error_boundary.py \
  tests/test_prism_w4_weaver_approval_ledger.py                     # 38 passed
```

## Next authorized action

Explicit push authorization for the three exact commits as review branches. `main` does not move.
Merge authorization remains separate and subsequent to the published CI results.
