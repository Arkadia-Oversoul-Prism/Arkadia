# WORKSTREAM STATE — `gate-hygiene/open-pr-queue-merge-order-map-01` (Pass 3)

Pass: `gate-hygiene/open-pr-queue-merge-order-map-01` (continuation; branch `-03`)
Date: 2026-10-03 (UTC)
Base main: `162f574b05dd839540d803aadda7608342618a84`
Status: **IMPLEMENTED** (evidence correction only; no code/test/governance change; sovereign review only)

Supersedes the *baseline attribution* of `WORKSTREAM_STATE_PASS2.md` §Baseline/§7. Queue
inventory, overlap, git-composability, merge order, and CP10 result all stand.

## Current state (derived from live evidence)

| item | value |
|---|---|
| `main` | `162f574b05dd839540d803aadda7608342618a84` |
| open PRs | **5** (#215, #216, #217, #218, #219) — all `MERGEABLE`, all `UNSTABLE` (Vercel rate-limit only) |
| hot file | `tests/test_agents_md_encoding_adjudication.py` — written by #215, #217, #218 |
| composed tree (5 PRs, order 215→216→217→218→219) | git-clean at every step; HEAD `a3e5111` |
| architecture suite | **11 / 11** |
| `api/main.py` | **2582 / 2600**; `py_compile` OK |
| CP10 mutation boundary | `--judge` exit 0 |

## The correction (Pass 3)

The baseline (`main`) failing-node set is **clone-depth-dependent**; the composed tree's is
**not**. Two regimes, both at `main 162f574`:

| regime | baseline failures | composed failures | composed node-set sha256[:16] |
|---|---|---|---|
| refs-present (this automation clone) | 20 | 18 | `c9ffdb6216c70314` |
| CI-like (`--single-branch`, no `refs/remotes/pr/*`) | 20 | 18 | `c9ffdb6216c70314` |

- **Fixed by composition, refs-present:** `{exit_code…divergent_clean_file…, gate2_parent…byte_identical…}`
- **Fixed by composition, CI-like:** `{exit_code…divergent_clean_file…, shadow_adjudication…oracle_not_the_codec…}`
- **Newly failing in either regime: 0.**
- In the composed tree **all three** adjudication nodes are green (PASS or legitimate SKIP) in
  **both** regimes — the regime-invariant claim.

## Merge order (advisory; merge is HUMAN)

1. **#216** — disjoint prose + fingerprint guard.
2. **#218** — pins the `gate2_parent` fixture off the moving `origin/main`.
3. **#215** — guards the `shadow_adjudication` crash/absent-revision branch.
4. **#217** — pins the `exit_code` divergent-file fixture.
5. **#219** — this evidence (safe first or last).

## Next bounded task

Sovereign merge of the five-PR cluster. No further repository work is authorized inside this
workstream; a separate bounded pass would be required for any of the pre-existing baseline debt.

## Blocker note — why every PR reads `UNSTABLE` (measured 2026-10-03)

All five PRs are `MERGEABLE` + `UNSTABLE` **solely** because of the pre-existing
**`Vercel – console` fail** check (a separate Vercel project, `dpl_… --logs`). It fails
identically on #215, #216, #217 and #218 — i.e. it is **not** caused by any of the five
diffs, and #219 is evidence-only (two markdown files). #215 additionally shows
`Vercel – arkadia-prism` **rate limited — retry in 24 hours**.

The gate that matters for this workstream, **`Full-history secret scan`, passes** on #219
(run `37086762826`). `Vercel – arkadia-prism` preview deployment also completed. Do **not**
re-diagnose `Vercel – console` as a regression of this cluster; if it needs fixing it is a
separate bounded workstream (Vercel project configuration, not repository source).
