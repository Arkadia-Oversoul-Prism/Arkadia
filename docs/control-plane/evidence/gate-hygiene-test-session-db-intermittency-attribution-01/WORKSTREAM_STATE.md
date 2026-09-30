# WORKSTREAM STATE — gate hygiene / test-session DB intermittency attribution

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.
>
> Continues the gate-hygiene workstream. Supersedes nothing; it *completes* an open
> finding recorded in `docs/control-plane/evidence/gate-hygiene-gate2-production-parity-02/WORKSTREAM_STATE.md` §2.

## Pass record — 2026-09-30 (heartbeat)

- **Reconstructed:** `origin/main` = `002b189dd95e41c9b4f4cca33d08b4121453d289`.
  Three open PRs, all `MERGEABLE` / `CLEAN`:
  - #142 `gate-hygiene/sh05-gate-artifact-provenance-01` @ `59fbb531` — docs only
  - #143 `gate-hygiene/gate2-production-parity-02` @ `7d79f38` — `AGENTS.md`, evidence, `scripts/gate2_backend_observation.py`
  - #144 `gate-hygiene/test-session-db-isolation-01` @ `09521d2` — `.gitignore`, `tests/conftest.py`
- **Authority:** ambient `github_token` resolved `permissions.push = true` for the repo.
  No credential HARD STOP. (Contrast: repo memory records a read-only token incident — that
  is **not** the case this pass; verify per-run, do not inherit the memory.)
- **Continuity:** PR #142's remote-ref contradiction (reported by the prior audit) is
  **resolved** — the remote branch exists and matches the PR head exactly. No duplicate work
  created; no workstream reset.
- **Selected task:** attribute the intermittent node PR #143 §2 recorded as unexplained.
  Smallest valid next task: it is documentation-only, has no regression boundary, and needs
  no authority beyond this pass.

## Finding — the intermittency is un-ignored SQLite sidecars (see EVIDENCE.md §3)

On `main`, `.gitignore` ignores `data/solspire_projects.db` but **not** its `-wal`/`-shm`
sidecars, which `git status --porcelain` reports. The guard in
`tests/test_engineering_lab_agent_loop.py:313-338` snapshots global `git status`; a sidecar
materializing between its `before` and `after` flips the assertion. Reproduced
deterministically: on `main` the sidecars appear in `git status`; on PR #144 they are
invisible (`check-ignore` → `.gitignore:25`). **PR #144 is the correct fix and removes the
exposure regardless of ordering.** No fix authored in this pass.

## Fingerprint (measured this pass, not remembered)

```
main 002b189, clean tree        : 20 failed / 1041 passed / 11 skipped / 2 errors   (×2 identical)
main 002b189, store pre-created : 20 failed / 1047 passed / 11 skipped / 2 errors   (+6 pass, 0 new fail)
PR #144 09521d2, clean tree     : 20 failed / 1047 passed / 11 skipped / 2 errors   (store NOT created)
architecture (main 002b189)     : 11 passed
py_compile api/main.py          : OK, 2519 lines (budget 2600)
```

The 20 failures are the **pre-existing baseline set**, identical by name and count across
every run. The 20↔21 flip is a **pass/fail count artefact of ambient store state**, not a
regression — do not attribute a 21-failure run to new work without re-reading this file.

## Next bounded task

1. **Sovereign merge of #144** — highest-value queue item; restores fingerprint stability.
2. **Then** reconcile PR #143 §2 with this attribution (one-line evidence edit on #143).
   Deliberately **not** done here: it widens scope across PRs.
3. Baseline debt remains its own bounded workstream; do not fix under an unrelated gate.

## Observation, not touched

- `AGENTS.md` baseline prose still cites `main := 6038989 / architecture 9/10`; live state is
  `002b189` / 11-11. Recorded for the sovereign; **not** edited (crosses into PR #143's diff).
