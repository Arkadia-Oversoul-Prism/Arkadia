# GATE L1.1 — Boundary Hardening: Implementation Record

Status: IMPLEMENTED (pending human review)
Base SHA: 417d32d (current main, PR #126 merge)
Branch: gate-l1.1-boundary-hardening

## Why this gate exists

A post-merge audit of PR #126 found that the L1 claim *"read-only by
construction"* was **false**. This gate corrects it. It is a bounded
security/governance repair, not an architectural expansion.

## Defects confirmed (by execution, not by reading)

### D1 — `terminal.run` was a mutation capability

`Sandbox.run()` validated only `argv[0]` against `command_allowlist`. With
`command_allowlist=("git",)` and `write_allowed=False`, the following were
executed successfully against the runtime's own policy:

| Command | Result before L1.1 |
|---------|--------------------|
| `git commit --allow-empty -m "AGENT COMMIT"` | executed; commit landed |
| `git branch agent-branch` | executed; branch created |
| `git tag agent-tag` | executed; tag created |
| `git reset --hard HEAD` | executed |
| `git add -A` | executed; index mutated |

`write_allowed=False` only guarded `Sandbox.write()`; it never constrained
subprocesses. A generic terminal is a mutation capability unless its grammar
is constrained.

### D2 — the authorization envelope was decorative

`execute_agent_loop()` read `agent["tool_access"]` but then hard-coded the full
tool list, so the human authorization's `operations_allowed` never bounded the
run. Proven by `test_authorization_narrows_capability` failing before the fix.

## The repair

### 1. Git read-only subcommand policy (`sandbox.py`)

- `SandboxPolicy.enforce_git_read_only: bool = False`.
- `READ_ONLY_GIT_SUBCOMMANDS` — an explicit allow-list of observing
  subcommands (`status`, `diff`, `log`, `show`, `rev-parse`, …).
- `_git_subcommand()` extracts the subcommand while skipping global options and
  their arguments, so `git -c user.email=x commit` resolves to `commit`.
- `Sandbox.run()` refuses any non-read-only git subcommand when the flag is set.
  Denial is recorded as evidence (`reason: git_mutation_denied`).

The control is **closed by default**: an unknown subcommand is treated as
mutation, not permitted.

### 2. Effective tools = capability ∩ authorization ∩ sandbox (`runtime.py`)

`effective_tools()` derives the grant from three layers:

```
capability ceiling  ∩  agent tool envelope  ∩  human authorization
```

- `CAPABILITY_OPERATIONS` maps capabilities to sandbox operation tokens.
- `OPERATION_TOOLS` maps tokens to loop tools (read-only git observation —
  `git.status` and `git.diff` — shares one token).
- `register_agent()` now places `git_status` in `tool_access.tools` when
  `OBSERVE` is present (it was missing, so git tools were unreachable).
- A session with no linked authorization yields **no** tools.

Both `execute_agent_loop()` and `execute_bounded_task()` now default to
`enforce_git_read_only=True`, and force it on any caller-supplied policy.

Consequence, by role: `WEAVER` (`READ, OBSERVE, PROPOSE`) receives
`filesystem.*` + read-only `git.*` and **no** `terminal.run`; `BUILDER`
(`READ, EDIT, RUN, TEST, PROPOSE`) additionally receives `terminal.run`.

### 3. Closed terminal grammar (`sandbox.py`) — follow-up finding

A second audit found that forcing `enforce_git_read_only` was insufficient:
a caller could still supply `command_allowlist=("python",)` and reach mutation
through `python -c "open(...).write(...)"`. `write_allowed=False` does not
constrain subprocesses. Reproduced: `python -c` wrote `injected.txt`.

- `SandboxPolicy.enforce_command_grammar`.
- `L1_TERMINAL_BINARIES` — a closed set: `git`, `echo`, `pwd`, `true`, `false`.
  Every member either takes no path argument or is separately constrained.
- `Sandbox.run()` refuses any other binary before the caller allow-list is even
  consulted, so a caller allow-list can only **narrow**, never **widen**.

### 4. Git path-redirection rejection (`sandbox.py`) — follow-up finding

`git -C <path>`, `--git-dir=<path>` and `--work-tree <path>` change where git
operates; `_resolve()` never sees them. Reproduced: all three read a repository
outside `policy.root`.

- `_GIT_PATH_OPTIONS` = `{-C, --git-dir, --work-tree}`.
- `_git_path_redirect()` detects them; `Sandbox.run()` refuses them.
- `-c`/`--config-env` are config overrides, not paths, and are **not** refused
  (verified by `test_git_config_override_is_not_treated_as_path_escape`).

### 5. K15/K3 untouched

No new mutation mechanism was introduced. The git guard only *narrows* the
sandbox. L2 remains: agent proposal → PassSpec → K15 → PatchApproval → K3 →
mutation → WorkEvent/evidence.

## Evidence

`tests/test_engineering_lab_agent_loop.py` — 40 passed, 1 skipped. New tests:

- `test_git_mutation_is_refused_through_terminal_run` — 11 parametrised
  mutation commands, each refused with repository state unchanged.
- `test_git_reads_still_work_under_hardening` — read-only commands still run.
- `test_git_read_only_guard_blocks_real_commit` — a commit that landed before
  the fix now raises `SandboxCommandDenied` and leaves `git log` unchanged.
- `test_git_subcommand_parser_skips_global_options` — parser correctness.
- `test_git_path_redirect_is_refused` — `-C`/`--git-dir`/`--work-tree` refused.
- `test_git_config_override_is_not_treated_as_path_escape` — `-c` still allowed.
- `test_caller_allowlist_cannot_widen_terminal_grammar` — `python`/`sh`/`rm`
  injected via the allow-list are refused; no file is created.
- `test_l1_terminal_binaries_still_run_under_grammar` — closed set works.
- `test_runtime_forces_closed_grammar_on_caller_policy` — captures the policy
  the runtime actually built and asserts both flags are set.
- `test_weaver_ceiling_excludes_terminal_run` — capability bound.
- `test_authorization_narrows_capability` — authorization bound.
- `test_agent_loop_uses_git_read_only_policy_by_default` — runtime default.

Regression: Lab + architecture = 99 passed, 1 skipped. Broader sweep failure
set is **identical to base `417d32d`** (11 pre-existing failures, none in
`lab/`).

### Reproduction commands

Before: `/tmp/repro_mutation2.py` printed `AGENT COMMIT LANDED: True`.
After: `/tmp/repro_fixed.py` prints 11 refusals, 4 read successes, and
`log unchanged: True`.

## Out-of-scope observed

- This gate does not add a git "read-only" mode to `git()`; `git()` already
  guards merge/force-push. Audit whether it needs the same subcommand policy.
- `api/lab_routes.py` still accepts a caller-supplied `command_allowlist`;
  the runtime now forces `enforce_git_read_only` on it regardless.
- GATE L2 (worktree mutation through the governed boundary) remains
  unauthorised.

## Verdict

IMPLEMENTED. The two defects are closed and proven by negative tests; no state
is claimed beyond that.
