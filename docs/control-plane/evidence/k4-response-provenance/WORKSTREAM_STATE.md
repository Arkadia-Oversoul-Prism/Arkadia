# Workstream state — persisted for the next heartbeat

Written: 2026-09-30 (UTC) · Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Rebuilt from evidence, not memory. Supersedes the prior pass's recorded figures where they disagree.

## Canonical state

- **main** = `002b189dd95e41c9b4f4cca33d08b4121453d289` (merge of #141). Working tree clean at pass start.
- **Baseline fingerprint (live `main`, re-measured):** 1039 passed / 20 failed / 13 skipped /
  2 collection errors; architecture 11/11.
  **The execution contract's stated baseline (`6038989`, 804/54/12/2, arch 9/10) is STALE.**
  Do not attribute the difference to new work.
- Pre-existing collection errors: `test_autonomy.py`, `test_render_codex.py`.

## Corrections to the previous pass's record (recorded, not silently overwritten)

1. **`tests/test_k4_response_provenance.py` has 6 tests, not 13.** Measured: `6 passed`.
   The "13 passed" figure in the prior pass record was wrong. No test was deleted.
   *Reconciliation:* 13 is the count for `test_k4_response_provenance.py` **plus**
   `test_oracle_spine.py` run together (6 + 7 = 13). The figure is a two-file aggregate
   reported as a single-file count. Both are green; the file itself contains 6 tests.
2. **The `/tmp` guard failure was a harness path artifact, not a guard defect.**
   `REPO_ROOT = parents[1]` resolves outside the repository when the guard runs from `/tmp`.
   Executed in place, #152's guard passes 2/2 on `main`. The guard is not a merge hazard.
3. **#152 does not touch `AGENTS.md`** — it is byte-identical to `main`. It is guard-only,
   not a repair.

## PR queue (open, non-draft)

| PR | branch | disposition |
|---|---|---|
| **#153** | `gate-k/k4-response-provenance-01` | **NEW this pass** — K4. IMPLEMENTED. CI green (3/3). |
| **#155** | `gate-hygiene/agents-md-queue-adjudication-02` | **NEW this pass** — adjudication evidence. IMPLEMENTED. CI green (2/2). |
| #150 | `gate-hygiene/gate2-agents-md-cp866-repair-01` | **CORRECT repair** — merge first |
| #147 | `gate-hygiene/gate2-agents-md-encoding-repair` | **CONTRADICTED** — restores main's corruption verbatim; close |
| #143 | `gate-hygiene/gate2-production-parity-02` | `AGENTS.md` must not merge as-is; Gate-2 parity content separate |
| #152 | `gate-hygiene/agents-md-repair-fingerprint-01` | guard-only; sound and merge-safe |
| #151 | `gate-hygiene/agents-md-encoding-adjudication-01` | byte-oracle adjudication; corroborated by #155 |
| #146 | `gate-k/k5-status-reconciliation` | owns `.bootstrap/01_STATE.md` — do not edit that file elsewhere |
| #154 | `gate-hygiene/production-health-route-provenance-01` | separate Gate-2 workstream (another pass) |
| #144, #145, #148, #149, #142 | gate-hygiene | independent, untouched |

## Active workstream

**Workstream K (Knowledge OS Integration).** K5 static ingestion is SHIPPED on `main`.
**K4 response provenance is IMPLEMENTED and now carried by PR #153** (was uncommitted at
pass start — a continuity gap this pass closed).

## Next bounded task

K4 is with the sovereign for merge. The next K checkpoint is **K6** (per `.bootstrap/01_STATE.md`
"Next Checkpoints After K2"). Do **not** begin K6 until K4 merges — a K6 built on unmerged K4
would assume provenance that `main` does not yet have.

Interim safe work, if the sovereign wants the queue cleared first: the merge order in #155.

## Authority

No merge, no push to `main`, no force-push. Human-only merge.
