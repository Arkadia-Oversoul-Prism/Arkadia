# VERIFICATION — gate-hygiene/scheduler-session-result-ignored-01

Environment: `/workspace/project/Arkadia`, Python 3.13.15, `fastapi` and other web deps
absent (pre-existing; inflates the failure/error debt on **both** trees equally).
Base main worktree: `/tmp/wtmain` @ `1775f3e1271842688f5026b59bfb0d393db6db04`.

## 1. Guard file — `tests/test_repo_hygiene_gitignore.py`

Command: `python -m pytest tests/test_repo_hygiene_gitignore.py -q`

| tree | result |
|---|---|
| base main `1775f3e` | 1 failed, **5 passed** |
| branch | 1 failed, **7 passed** |
| branch, `engineering-session-result.json` rule stripped | 2 failed, 6 passed |
| branch, rule restored | 1 failed, 7 passed |

- `+2 passed` on the branch is exactly `test_scheduler_session_result_is_never_stageable`
  and `test_session_result_ignore_is_scoped_to_the_run_result`.
- **Negative control proven:** removing the ignore rule makes
  `test_scheduler_session_result_is_never_stageable` FAIL. The guard can detect the defect it
  claims to detect; it is not a tautology.
- The 1 failure on both trees is pre-existing and environmental:
  `test_no_module_resolves_the_repository_canonical_store` raises
  `ModuleNotFoundError: No module named 'fastapi'` at `solspire/enterprise_router.py:21`.

## 2. Defect reproduction (base main `1775f3e`)

Exact scheduler writer body (`EngineeringWorker(repo_root=".", dry_run=True).run()` →
`Path("engineering-session-result.json").write_text(json.dumps(result, indent=2))`):

```
git check-ignore --no-index -q engineering-session-result.json   → rc=1   (not ignored)
git ls-files engineering-session-result.json                     → 0 paths (untracked)
git status --porcelain                                           → ?? docs/control-plane/evidence/attention-events.jsonl
                                                                   ?? engineering-session-result.json
git add -A --dry-run                                             → add 'engineering-session-result.json'
```

Worker status at base main: `NO_LEGAL_MOVE`.

## 3. Full suite — node-set comparison

Command: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`

| tree | passed | failed | skipped | errors | node-set sha256 |
|---|---|---|---|---|---|
| base main `1775f3e` | 1005 | 69 | 20 | 48 | `16493ff39e67ff9a55dfffbad585b8226b9b0db46c4b2ff6d444c5496c5d3c43` |
| branch | 1007 | 69 | 20 | 48 | `16493ff39e67ff9a55dfffbad585b8226b9b0db46c4b2ff6d444c5496c5d3c43` |

```
$ diff main_nodes.txt branch_nodes.txt      # sorted, unique FAILED/ERROR lines
(no diff)                                    # 117 nodes each side
```

**Zero regression.** The only delta is `+2 passed`, which is the two new assertions. The
69F/48E is pre-existing main debt in this environment, recorded not fixed.

> Note: `-rEf` is used deliberately. `-rf` alone suppresses pytest's `ERROR` summary lines,
> which would silently drop 48 nodes from the fingerprint.

## 4. Protected surfaces

| check | command | result |
|---|---|---|
| architecture fitness | `python -m pytest tests/architecture -q` | **11 passed** |
| boot code compiles | `python -m py_compile api/main.py` | **OK** |
| `api/main.py` budget | `wc -l < api/main.py` | **2432** (< 2600) |
| CP10 mutation boundary | `git diff --name-only origin/main \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** (exit 0) |

`api/main.py` is untouched by this branch.

## 5. What was NOT run / NOT claimed

- No frontend build (`pnpm`) — irrelevant to a `.gitignore` + pytest change; not attempted.
- No production/deployment observation. This is a repository-source claim only.
- The trajectory-structure defect (worker `FAILED` → hourly job exit 1) is **not** repaired
  here; PR #319 owns it.
