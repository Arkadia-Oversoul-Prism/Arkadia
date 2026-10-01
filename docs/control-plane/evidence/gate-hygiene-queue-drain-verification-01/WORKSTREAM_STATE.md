# WORKSTREAM_STATE — gate-hygiene / queue drain verification

Pass: `gate-hygiene/queue-drain-verification-01`
Date: 2026-10-01 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
PR: **#163** (`gate-hygiene/queue-drain-verification-01`)
Status: **READY FOR SOVEREIGN REVIEW**
Authority: no merge, no push to `main`, no force-push. Human-only merge.

## Canonical state

| item | value |
|---|---|
| `main` | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| open PRs at pass start | **21** (#142–#162) |
| queue conflicts | **one** — `AGENTS.md`, surfaced at **#150** by #143/#147 |
| drain set | **18 PRs** (#143, #147 excluded) |
| drain-set conflicts | **none, at every step** |

## Baseline fingerprint (re-measured this pass)

| tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| clean `main` `002b189` | 20 | 1039 | 13 | 2 |
| drain set, **unpatched** | **19** | **1090** | 15 | 1 |
| drain set + #159 repair | **18** | **1091** | 15 | 1 |

`tests/architecture` → **11 passed**. `api/main.py` → 2519 / 2600, `py_compile` OK.

## Findings this pass adds over #159 / #162

1. **#162 §6's headline is the patched tree.** Unpatched, the drain set is 19 failed / 1090
   passed, not 18 / 1091. #162 §7 says the same thing correctly; §6 reads as green-on-merge.
2. **The unpatched drain set carries 1 introduced failure**, not zero:
   `test_documented_route_contract.py::test_health_route_documentation_matches_the_served_app`
   (#154 serves `/health`; #156's guard requires a guide row; neither PR alone is wrong).
3. **Gate 2 deployment identity is answered.** Production serves `main` @ `002b189`
   (`ref == sha == main`); alias→SHA is UNKNOWN but *immaterial* — all 12 candidate SHAs
   descend from the last frontend-build-input commit `b377a01`.
4. **A real source-side defect found and root-caused**, using #143's own harness:
   `CapabilityChamber.tsx` imports `ActivityRuntime` but never renders it — the render was
   dropped at `44e1c99` and never restored, while the import was re-added at `ff80b8c`.
   The deployed bundle matches `main`; this is **not** a stale deployment. Confirmed by
   grepping the deployed bundle: `CapabilityChamber`'s literals present ×1 each,
   `ActivityRuntime`'s ×0.
5. **The four `test_spiral_grove_activity_runtime.py` failures are the repository's own
   assertion of finding 4** — pre-existing baseline debt, unchanged by the queue, and not
   attributable to any drain PR.
6. **#143's harness is separable and already useful.** Eight files, no `AGENTS.md`
   dependency; re-cuttable onto #150's bytes.
7. **CP10 admits every drain path** (`--judge` exit 0 over the 21-path union).

## Drain order (merge order is free within the set)

```
157  156  155  151  152  153  154  142  144  145  146  148  149  150  158  159  160  161
```

**Merge #150. Do not merge #143. Close #147 as superseded.**
**Apply `health-row-doc-repair.patch` at the #154 step** (or in a hygiene PR before #159).

## Next bounded task

Sovereign review + merge decisions. No further engineering is required to make the queue
mergeable. Two candidates for a **separate** bounded pass, both requiring authorisation:

- Re-cut #143's Gate 2 harness onto `#150`'s `AGENTS.md` bytes (§8 of EVIDENCE).
- Classify (not repair) the remaining baseline failure clusters; `test_steward_filter.py` ×3
  and `test_spiral_grove_*` ×6 are product decisions, not hygiene.

## Open boundary

Deployment build-output observation and browser-rendered UI correctness remain **BLOCKED**
(no Vercel credential; no browser runtime in this sandbox). This pass does **not** claim
production acceptance. All 20 queue PRs had green CI at their heads per #159/#162; not
re-verified here.
