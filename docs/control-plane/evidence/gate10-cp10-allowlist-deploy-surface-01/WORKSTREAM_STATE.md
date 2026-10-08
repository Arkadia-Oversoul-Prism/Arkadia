# WORKSTREAM STATE — gate10/cp10-allowlist-deploy-surface-01

**Gate:** GATE-10 (Governed Execution) — CP10 mutation boundary / M02A CI gate integrity
**BASE_MAIN:** `f96d5fd27d40110196ec22b114808efc0eb9dc05`
**Branch:** `gate10/cp10-allowlist-deploy-surface-01`
**PR:** #354
**Head at record:** `e7ce1d0fcecf11187876e06f08f63cefcf24a38d`
**Status:** VERIFIED — READY FOR SOVEREIGN MERGE
**Authority:** merge and authorization retained exclusively by the human sovereign.

## Deterministic next action

- **Current state:** `deploy/` (4 tracked paths, added by PR #352 / merge `a27c6c80`) is
  enumerated in `LEGIT`. The CP10 boundary step passes on the full PR range at the current
  head, and the three completeness fitness nodes pass on the branch and fail on `main`.
- **Evidence:** `docs/control-plane/evidence/gate10-cp10-allowlist-deploy-surface-01/EVIDENCE.md`
  (Passes 1–3c).
- **Authorized action:** sovereign review and merge of PR #354.
- **Forbidden actions:** merge, force-push, self-authorization, weakening the gate,
  reclassifying `REGISTERED_ARCHITECTURAL_DEBT`, widening scope into unrelated baseline debt.
- **Completion condition:** PR #354 is merged by the sovereign and
  `test_allowlist_admits_every_tracked_top_level_prefix`,
  `test_allowlist_covers_every_tracked_surface`, and
  `test_delegated_verdict_admits_every_tracked_surface` are green on the resulting `main`.

## Measured state at this record

| Check | Result |
|---|---|
| `tests/test_m02a_ci_gate_integrity.py` (branch) | 64 passed |
| three completeness nodes (`main` `f96d5fd2`, detached worktree) | 3 FAILED |
| `SG-02-FE.2-V` @ `e7ce1d0f` | success — `Mutation boundary PASS`, range `f96d5fd2..HEAD` |
| `security-secret-scan` @ `e7ce1d0f` | success |
| `N-ATLAS external beta validation` @ `e7ce1d0f` | success |
| Vercel (both contexts) | failure — identical on `main` `f96d5fd2`; provider rate limit, not attributable |
| `api/main.py` | untouched (not in the diff) |
| tracked corpus | 1955 paths |

`mergeable=MERGEABLE`; `mergeStateStatus=UNSTABLE` is caused solely by the pre-existing Vercel
rate-limit status.

## Predecessor and open follow-on

- Predecessor: `gate10/cp10-allowlist-economic-seams-mie-01` (merge of `economic_seams/` +
  `musical-intention-engine/`). Its WORKSTREAM_STATE explicitly named this recurrence class:
  "A future tracked top-level tree re-triggers the same defect class; the completeness
  invariant in `tests/test_m02a_ci_gate_integrity.py` is the guard." That prediction fired
  here, at `deploy/`.
- The guard is the point: a new tracked top-level tree must be enumerated, not admitted by a
  broadened rule. Do not replace the enumerated `deploy/` entry with a generic pattern.
- Reported, not resolved (separate workstreams): the `test_engineering_lab_api.py`
  Lab-endpoint-set failure, and the Lab authentication-boundary question.
