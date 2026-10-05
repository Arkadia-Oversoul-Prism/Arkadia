# WORKSTREAM_STATE — gate-hygiene/independent-queue-verification-06

## State (measured 2026-10-04T22:45Z)

| Field | Value |
| --- | --- |
| LIVE_MAIN | `89f9e78063f9c2a9a9931e305a2195035d205309` |
| Branch | `gate-hygiene/independent-queue-verification-06` |
| Base | live `main` (branch point == LIVE_MAIN) |
| Baseline node set | 10 nodes — `9a54f5b4…` / `124bfdfd…` |
| Baseline counts | 9 failed, 1425 passed, 18 skipped, 1 error |
| Open PRs | 6 (#267, #268, #270, #271, #273, #274) |
| Classifications | VERIFIED (baseline); CONFIRMED DEFECT (#270, #273); NO DEFECT FOUND (#267, #268, #271, #274) |
| Gate-2 production parity | BLOCKED (provider auth) — unchanged |

## Gate status

- **GATE-10 governed execution** — open. The CP10 boundary is intact (judge PASS on this
  pass's paths). PR #273 correctly reddens it; PR #270 reaches it green because the
  workflow's path filter does not include the Python it changed.
- **Gate-2 production parity** — BLOCKED on Vercel Deployment Protection. Not advanced this
  pass and not advanced by anything in the open queue.

## Blocker — PR #270

`solspire/buyer_recon_router.py` imports `require_project_owner` from `api.auth`, which
does not define it. `api/main.py:333` mounts the affected router inside a logging
`try/except`, so the app boots with **80 `/solspire` routes silently absent**. No CI gate
on the PR ran a SolSpire Python test, so the head shows three green checks.

Reproduction:

```
git worktree add /tmp/wt270 origin/pr270
cd /tmp/wt270 && PYTHONPATH=archive/legacy_python:. <venv>/python -m pytest tests/test_solspire_ownership.py -q
# -> Interrupted: 1 error during collection (ImportError)
# control: same command on main -> 51 passed
```

## Blocker — PR #273

`ProjectDashboard.tsx` imports `ArkanaWeaverCanvas`; the PR adds `ArcanaWeaverCanvas.tsx`.
Vite cannot resolve it (CI run `37237565057`, step *Build Prism*) and the PR's own
`tests/test_arcana_weaver_fusion.py` pins the same wrong path and fails with
`FileNotFoundError`. Two independent failures, both visible.

## Deterministic next-action block

**Current state.** Live main `89f9e78`, baseline fingerprint reproducible and unchanged.
Two open PRs carry confirmed defects; neither is mergeable. Four open PRs are clean.

**Evidence.** `EVIDENCE.md` in this directory; CI runs `37237565057` (SG-02-FE.2-V on
#273) and the three-run green set on #270 head `1a264efe72d0…`; local control runs on
`main` and on `/tmp/wt270`, `/tmp/wt273`.

**Blockers.** (1) PR #270 ImportError → silent 80-route loss. (2) PR #273 build break +
guard-test path mismatch. (3) Gate-2 parity blocked on provider auth.

**Authorized action.** Sovereign review of #270 and #273; return them to their authors with
the corrective action in §9 of `EVIDENCE.md`.

**Forbidden actions.** Merge any PR. Push to `main`. Fix the PRs inside this evidence
branch. Widen the CP10 allowlist. Weaken a test to make #270 or #273 green. Modify the
`sg-02-fe-2-v.yml` path filter without authorization. Attempt deployment.

**Exact completion condition.** This pass is complete when the evidence branch is pushed
and a PR is open against `main` containing only the two files in this directory. It is
**not** complete as a workstream: the queue returns to the sovereign with two defects
outstanding, and no claim of production parity is made.

## Superseded / corrected

- The prior run's log recorded `89f9e78` as a STALE anchor and `ca67b00` as `main`. Both
  are wrong; re-measured: `89f9e78` is live `main`, `ca67b00` is its ancestor. Superseded
  by §1 of `EVIDENCE.md`.
- PR #271's §2 fingerprint is confirmed unchanged, not contradicted: the same 10-node set
  reproduces at `89f9e78` with a higher passed count.
