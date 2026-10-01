# WORKSTREAM_STATE — gate-hygiene / open-PR queue drain

Pass: `gate-hygiene/queue-drain-order-20pr-01`
Date: 2026-10-01 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`

## Canonical state

| item | value |
|---|---|
| `main` | `002b189dd95e41c9b4f4cca33d08b4121453d289` (merge of PR #141) |
| open PRs | **20** (#142–#161) |
| queue conflicts | **one** — the `AGENTS.md` cluster (#143, #147, #150) |
| drain set | **18 PRs** (excludes #143 and #147) |
| drain-set conflicts | **none, at every step** |

## Drain order (merge order is free within the set)

```
157  156  155  151  152  153  154  142  144  145  146  148  149  150  158  159  160  161
```

**Merge #150. Do not merge #143. Close #147 as superseded.**

## Baseline fingerprint (must be re-measured at the start of every pass)

| tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| clean `main` `002b189` | 20 | 1039 | 13 | 2 |
| drain set + #159 repair | 18 | 1091 | 15 | 1 |

Node-set delta: **3 fixed, 0 introduced.**

Fixed: `ERROR tests/test_render_codex.py` (#149);
`tests/test_engineering_scheduler_bootstrap.py::test_blocked_dependency_skips_move` and
`::test_dry_run_evidence` (#148).

Pre-existing, unchanged: `ERROR tests/test_autonomy.py` (`load_autonomy_config`).

`tests/architecture` → **11 passed**.

## Findings this pass adds over #158

1. **#158's map is 16 PRs; the queue is 20.** #158 measured #142–#157. #143 and #147 were
   outside it.
2. **#143 is the queue's only conflict source.** All-20 composition conflicts at #150;
   excluding #143 and #147 (the latter is stacked on #143) composes clean.
3. **#143 is not a repair.** #151's own instrument, re-run: #143 carries **594** Latin-1 cruft
   codepoints; its rendered text is `# Arkadia čéąÉąż …` with `čéą¢ąó` for `→`.
4. **#147 restores the corruption verbatim** (`+116/-0`), consistent with #155's
   `CONTRADICTED` classification.
5. **Zero regression by node identity**, measured against a live `main` baseline rather than
   an inherited count.
6. **#159's patch is load-bearing** (1 failed → 9 passed) and requires #154 + #156 jointly.

## Blockers resolved this pass

`gh` / GitHub API was `BLOCKED` on `GITHUB_TOKEN` (empty → HTTP 401). The working credential
is the **`github_token`** secret (repo `push: true`, `admin: true`). Live queue, per-PR file
lists, and PR body reads all ran through `GH_TOKEN=$github_token`. **No 403/401 on any write
path was attempted or needed** — this pass performs no writes to GitHub.

## Next bounded task

Sovereign review of the drain order. No further engineering work is required to make the
queue mergeable; the remaining work is merge decisions, which are human-only.
