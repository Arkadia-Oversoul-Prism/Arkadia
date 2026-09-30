# WORKSTREAM STATE — gate-hygiene / gate2-production-parity-02

Pass: `gate-hygiene/gate2-production-parity-02`
Date: 2026-09-30 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Branch head at pass start: `002b189dd95e` (branched clean from main)

## Active workstreams

| WS | Branch / PR | State |
| --- | --- | --- |
| SH-05 gate-artifact provenance | `gate-hygiene/sh05-gate-artifact-provenance-01`, PR #142 | EXHAUSTED — see §3 |
| Gate-2 production parity | `gate-hygiene/gate2-production-parity-02` (this branch), PR #143 | PARTIAL — deployment identity + build↔source lineage VERIFIED (now for **all 12** candidate SHAs, closure arg §10.1); provider observation still BLOCKED; alias→SHA UNKNOWN and immaterial; observation now reproducible via `scripts/gate2_production_observation.py` |

## 1. Baseline fingerprint recorded at pass start

Measured on `002b189dd95e` in this environment, not carried from prose.

| Suite | Result |
| --- | --- |
| `python -m pytest tests/architecture -q` | **11 passed / 0 failed** |
| `python -m pytest tests/ -q --continue-on-collection-errors` | **20–21 failed / 1038–1039 passed / 13 skipped / 2 collection errors** |
| `python -m py_compile api/main.py` | OK |
| `api/main.py` line count | 2519 (budget 2600) |

The 2 collection errors are the documented pre-existing pair (`test_autonomy.py`
`load_autonomy_config`, `test_render_codex.py` `arkadia_drive_sync`).

The previously recorded baseline in the pass contract (`804 passed / 54 failed`) does
**not** reproduce on current main. It is a stale fingerprint. Reconciled: the contract's
`6038989`-era baseline is 12 failures larger than what current main shows, and the
`test_steward_filter.py` failures were introduced by the steward-filter carrier
(`f02-steward-filter-provenance-01`, merged as `002b189`) on top of base `df7a99a`, which
carried the 32-failure fingerprint. See §2.

## 2. NEW: suite fingerprint is UNSTABLE (1 intermittent node)

`tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
is **intermittent under the full suite** and passes **8/8 in isolation**.

Observed across 4 full-suite runs on the same SHA: `20, 21, 20, 21` failures. The only
node that moves is this one.

Root cause (read from source, `tests/test_engineering_lab_agent_loop.py:313-338`): the
test snapshots **global** `git status --porcelain` on `REPO_ROOT` before and after
`execute_agent_loop`, then asserts equality. It is therefore sensitive to repository
writes made by *any other test* in the same process — not only to the agent loop it means
to constrain. The agent loop itself performs only `git_status` (allowlist `("git",)`), so
the guard's own subject is not what fails.

This is **test cross-contamination**, not a boundary violation. It is recorded here
because an unstable fingerprint makes failure attribution unreliable: a run that reports
21 failures cannot be distinguished from a real regression by count alone.

**Not fixed in this pass** — discovery does not authorize execution, and it is unrelated
to the Gate-2 scope. It is proposed below as its own bounded workstream.

## 3. SH-05 — gate-artifact provenance: EXHAUSTED

The SH-05 branch's subject was whether `gate/` artifact rows 47–48 were carried as
`ENV/ARTIFACT` without evidence.

Findings, from repository history rather than prose:

- `gate/` artifact provenance traces to the merged steward-filter carrier
  (`f02-steward-filter-provenance-01`, `002b189`).
- The 12 `test_steward_filter.py` failures on current main are attributable to that
  carrier: base `df7a99a` carried the 32-failure fingerprint, current main carries 20.
  The delta is the retired/rewritten steward-filter nodes, not new debt.
- No further provenance-bearing nodes remain to trace on that branch. SH-05 has reached
  its completion condition.

Disposition: **do not open new work on SH-05.** If the ledger rows still need a
classification change, that is a documentation edit that belongs on the existing PR #142,
not a new branch.

## 4. Gate-2 — production parity: what changed

Full detail in `docs/control-plane/evidence/gate-hygiene-gate2-production-parity-02/EVIDENCE.md`.

- **VERIFIED (new):** the main→deployment link Gate 2 was missing. GitHub Deployments
  records Production deployment `6749238709` with `ref == sha == 002b189dd95e...` —
  exactly current main — status `success`, created `2026-09-30T01:23:16Z`.
- **BLOCKED:** the deployment-specific URL
  (`https://arkadia-prism-ey2ozd5u4-arkadia-prism.vercel.app`) returns HTTP 302 to
  `vercel.com/login` — Vercel Deployment Protection (SSO). Build output not observable.
- **UNKNOWN:** alias→`002b189` binding, and browser-rendered UI correctness.
- **NOT CLAIMED:** production parity and production acceptance.

Two carried-forward cautions, both re-affirmed:

1. **Asset hash is not a parity oracle.** Build output is env-dependent — injecting
   `VITE_API_BASE_URL` changes the hash with no source change. Mismatch ≠ divergence;
   match ≠ parity.
2. **Route 200 is not application correctness.** `vercel.json` rewrites `/(.*)` →
   `/index.html`, so `/api/health` (never a backend route, per `git log -S`) returns
   `200 text/html` identically to any non-existent path.

## 5. Proposed next bounded tasks (NOT authorized by this pass)

| Proposal | Scope | Authority needed |
| --- | --- | --- |
| P-1 Vercel read access for `arkadia-prism` | closes Gate-2 observation | HUMAN (provider credential) |
| P-2 Stabilize `test_agent_loop_does_not_mutate_repository` | make it path-scoped / isolate from global `git status`; restores fingerprint determinism | none beyond normal PR review |
| P-3 Refresh the stale baseline fingerprint in the pass contract | docs only | none |
| P-4 Tracked-but-stale build output `web/public_prism/dist/` | stop tracking the build dir, or pin it via a checked build step | none beyond normal PR review |

P-2 is the smallest and is independently safe: it strengthens a boundary guard rather than
weakening it, by making it assert what it actually means to assert. It should be taken as
its own branch/PR if the sovereign wants it, not folded into Gate 2.

### Finding: `web/public_prism/dist/` is tracked and drifts

`web/public_prism/dist/index.html` is tracked by git, but it is a **build output**. At pass
start the working tree already carried an uncommitted modification to it, referencing
`assets/index-DIKNxYlc.js` — the env-injected experimental build left behind by the
previous pass — while `main` commits `assets/index-CStL2fKK.js` and the live production
alias serves `assets/index-CHFFyuSc.js`. Three different hashes for the same file.

Consequence: the tracked artifact is stale relative to production at all times, and because
the hash is env-dependent (§4) it also silently drifts whenever anyone builds locally. It is
a source of exactly the misleading hash comparisons the Gate-2 cautions warn against. The
stale working-tree copy was **reverted, not committed**, by this pass — it is not part of
this change set.

## 6. Next heartbeat

Reconstruct from live evidence. The Gate-2 chain is now:

```
main SHA ✓ → deployment SHA ✓ → build↔source lineage ✓ → route resolution ✓
  → deployment observation ✗ BLOCKED → alias binding ? → UI/runtime ? → acceptance (human)
```

Resume at the first unresolved link. If no Vercel credential has been supplied, the
observation link stays BLOCKED and no further Gate-2 progress is possible — proceed with
P-2 instead.

## 7. Pass 2 update (same branch, same PR)

Full detail in `EVIDENCE.md` §8–§9. Summary:

- **New VERIFIED link: build↔source lineage.** The deployed asset carries discriminating
  source-string markers from current main (`separate explicit downstream stages`,
  `activity-draft.v1:`, `learning-activity-work-surface`, `sg03-contract-boundary`,
  `solspire-object-summary`, `opportunity-radar`), and a clean local build of `002b189`
  matches it **on every marker and count**. The pre-SG-03 control string is absent from
  both. `git log` shows **zero** commits under `web/public_prism/src/` since the production
  deployment was created (`2026-09-30T00:23:16Z`), so there is no divergence window.
- **New VERIFIED link: route resolution.** `/solariun/opportunity-radar` resolves via
  `App.tsx:51 resolvePath()` against `SOLSPIRE_LENSES`; the lens registry is present in the
  deployed bundle. This is a source-level proof, not a browser observation.
- **Unchanged BLOCKED:** deployment-specific build observation (Vercel SSO) and the
  alias→SHA binding. These need the provider credential in §6 — no repetition closes them.
- **Fingerprint this pass:** architecture 11/11, gate integrity 49/49, full suite
  **20 failed / 1039 passed / 13 skipped / 2 collection errors**, `py_compile` OK,
  `api/main.py` 2519 lines. Stable at the low end of pass 1's `20–21`; no new regression.
- **SG-04 (`ActivityRuntime`) is now bound to the deployed artifact**, not just to the test
  file: `activity-runtime-draft.v1:` is absent from the production bundle while every SG-03
  marker is present. That upgrades it from "possibly stale assertion" to **real product
  regression carried to production**. Still deliberately unfixed here — it is a product
  change outside Gate-2 hygiene scope. Tracked under `gate-hygiene` / SH-02, Gate GATE-01.

### Standing caution (re-affirmed, now with a workaround)

Hash comparison is not a parity oracle — the deployed bundle is 84,551 bytes larger than a
clean local build because Vercel injects env vars at build time. **Marker-set comparison is**
robust to that injection and is the oracle to use for future lineage checks. Do not fall
back to hash equality.
