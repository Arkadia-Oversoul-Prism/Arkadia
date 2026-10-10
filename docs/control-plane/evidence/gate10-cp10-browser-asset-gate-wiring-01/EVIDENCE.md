# GATE-10 · CP10 browser-asset gate wiring — EVIDENCE

**Workstream:** gate10/cp10-browser-asset-gate-wiring-01 (stacked on PR #384)
**Base:** `f744e36b78a28661017cf32942568c34e9b6cd2d` (PR #384 head) → `main` `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Observation time:** 2026-10-10
**Status:** IMPLEMENTED — repository-source claim only; no production-parity claim.

## 1. Defect (measured, not inferred)

`main` `f9ced6b6` CP10 `validate` job run `37954341298` / job `113900901998`
concludes **failure**. The job's step list shows **exactly one** failing step:

| step | id | conclusion |
|------|----|-----------|
| 19 | `lab` | success (despite 2 failing lab nodes) |
| 21 | `backend` | success (despite an interrupted full suite) |
| 23 | `backend_ready` | success |
| **29** | **`browser`** | **failure** |
| 32 | `mutation` | success |
| 35 | `Enforce CP10 executable gates` | failure |

Step 35's script is a sequence of `test '${{ steps.<id>.outcome }}' = success` lines.
In the CI log exactly one renders as a real failure —
`test 'failure' = success` — the 14th `test` line, i.e. `steps.browser.outcome`.
All 38 other gates render `success = success`. The browser step therefore fails on
the browser-journey assertion, and the four `failedRequests` are all
`http://127.0.0.1:5000/firebase-config.js :: net::ERR_ABORTED`.

Root cause: commit `d8eae1d` added `<script src="/firebase-config.js"></script>` to
`web/public_prism/index.html:16`, but no file was committed under
`web/public_prism/public/`. Vite `build` succeeds (it copies `public/` verbatim and does
not validate HTML `src`), and the Vite dev server used by the browser step serves the
dangling path as the SPA `index.html` fallback (`200 text/html`, reproduced locally),
which the browser refuses to execute as a script → `net::ERR_ABORTED` → non-empty
`failedRequests` → browser step fails.

`/firebase-config.js` is the **sole** dangling root-absolute script asset
(`/arkadia-mark.svg` resolves; `/src/main.tsx` is the Vite module graph). PR #384 adds
the committed `public/firebase-config.js` default and
`tests/test_frontend_script_assets_resolve.py`, a complete repair for the browser step.

## 2. Defect this PR fixes (the follow-on gap)

PR #384's guard is referenced by **no workflow** — `grep -rn
test_frontend_script_assets_resolve .github/workflows/` → 0 matches, and the two
`sg-02-fe-2-v.yml` trigger filters do not name it. A guard no workflow executes is
decoration: the `/firebase-config.js` class of defect can reappear and reach `main`
without any test failing.

Additionally, the CP10 enforcement masks piped failures: steps 18 (`Grove`), 19 (`lab`)
and 21 (`backend`) stream through `| tee …` **without `set -o pipefail`**, so the step
exit code is `tee`'s (0) and their `continue-on-error` conclusion is `success` even when
pytest fails (measured: `lab` reports success with `2 failed, 9 passed`). Steps that
declare `set -o pipefail` (`browser`, `solspire_runtime`) do surface failures.

## 3. Change (bounded)

| file | change |
|------|--------|
| `.github/workflows/sg-02-fe-2-v.yml` | two new steps running the guard, without `continue-on-error`; both named in `Enforce CP10 executable gates`; both trigger filters gain `tests/test_frontend_script_assets_resolve.py` and `tests/test_frontend_script_asset_ci_wiring.py` |
| `tests/test_frontend_script_asset_ci_wiring.py` | new generic wiring guard + negative controls |

Not changed: `api/main.py` (2450 lines, unwrapped by this work, `py_compile` OK),
`web/public_prism/index.html`, the guard itself (owned by #384), any governance /
identity / authority surface.

The wiring guard states the invariant generically over **every** workflow that runs the
guard, with negative controls proving the detector bites: a filter that selects only
`api/**` is rejected; a `continue-on-error` guard step is reported.

## 4. Evidence

| check | result |
|-------|--------|
| `tests/test_frontend_script_assets_resolve.py` + `tests/test_frontend_script_asset_ci_wiring.py` | **10 passed** |
| `tests/architecture -q` | **11 passed** |
| `tests/test_m02a_ci_gate_integrity.py` + `tests/test_ci_gate_trigger_coverage.py` + `tests/test_baseline_fingerprint_ci_wiring.py` | 124 passed / **3 failed** |
| the 3 failures on base `f744e36b` | identical 3 failures (pre-existing) |
| `yaml.safe_load(sg-02-fe-2-v.yml)` | parses |
| `python -m py_compile api/main.py` | OK |

The 3 failures are the CP10 `deploy/n-atlas-server/` allowlist omission
(`test_allowlist_admits_every_tracked_top_level_prefix`,
`test_allowlist_covers_every_tracked_surface`,
`test_delegated_verdict_admits_every_tracked_surface`), owned by open PR #354. They
exist on base `f744e36b` unchanged — this branch introduces **zero** new failures.

`git ls-files | python scripts/cp10_mutation_boundary_policy.py --judge` on the proposed
changed-path list → `Mutation boundary PASS`.

## 5. Remaining uncertainty

This is a repository-source claim. Whether `main`'s CP10 gate goes green requires a
post-#384 deployment/run of the workflow with both #384 and this branch merged. No
production-parity claim is made here.

## 6. Authorization required

**Human merge.** Merge order: PR #384 (repairs the browser step) must merge before or
with this branch (stacked on it) — this branch depends on the guard file existing.
