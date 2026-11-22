# Repair two stale R1 governance pins; reconcile the recorded baseline set

**Workstream:** `test-hygiene/solspire-r1-governance-pins-01`
**Base:** `main` `034d8879d68ecf8ed4c291eb0ab07432657a06a1` (2026-11-22, observed)
**Authority:** implementation + evidence only. No merge, no deployment, no acceptance.
**Status:** PASS locally (targeted + full suite); merge and production acceptance are human-only (GOV-03).

## 1. Observation at pass start

| Fact | Value |
|---|---|
| `origin/main` | `034d8879d68ecf8ed4c291eb0ab07432657a06a1` (local `main` identical, 0 ahead / 0 behind) |
| Open PRs | 17, all `draft`, all `MERGEABLE`; 12 branched from `034d8879`, 5 one commit behind |
| Check-runs on `034d8879` | `Full-history secret scan`, `boot-syntax`, `console-contract`, `engineering-scheduler`, `lane-doc-currency`, `posture-currency`, `test`, `weaver_evolution` → all `success`; 4 `weaver_evolution` → `skipped` |
| Lane currency | `python scripts/lane_state.py --check` → exit 0, "lane instruction docs consistent with snapshot (4 guarded lanes)" |
| `AGENTS.md` encoding | Cyrillic count `0`; audit `alterations=0`, `oracle_reproduced=True` |
| Local full suite (app deps installed) | `35 failed, 4218 passed, 35 skipped, 1 error`; 36 failing/error nodes, sha256 `f37765c78e72fae4b332031f07e70dbbf25da3883920efb2aa3f31f9d439fbce` |

Most local failures are environment-shaped, not repository debt (`node_modules/typescript` absent →
10 nodes in `test_mission_lifecycle_adapter_contract.py`; `google`/ASR extras absent → voice and
arkana-signal clusters). Those were classified, not repaired.

## 2. The defect (verified, unowned)

`tests/test_solspire_r1_governance_convergence.py` failed **2 of 5** on unmodified `main`:

```
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
3 passed, 2 failed
```

Both are **test-side pins**, not product debt:

1. `test_r1_weaver_governance_is_canonical` asserted `"execute_patch" in` the source of
   `weaver/governance.py`. `36bdcf01` — *"refactor(weaver): keep governance module narrowly
   scoped"* — deliberately removed the `execute_patch` re-export from that module:

   ```
   -from .execution import PatchApproval, execute_patch, pass_spec_hash, patch_content_hash
   +from .execution import PatchApproval, pass_spec_hash, patch_content_hash
   ```

   The canonical executor is `weaver/execution.py::execute_patch` (line 173), and
   `weaver/capabilities.py` declares `"entrypoint": "weaver.execution.execute_patch"`.
   The test predates the split (`git merge-base --is-ancestor 9b06d693 36bdcf01` → true), so the
   assertion pins a **location** that was intentionally retired, not the property that Weaver
   owns execution.

2. `test_r1_solspire_builders_delegate_to_weaver` compared the adapter's spec against a canonical
   spec built with `pass_id="mvp1-r1-patch"` while calling the adapter with **no** `pass_id`, so
   the adapter derived `mvp1-50c0ee9b89`. Two different requests were compared, and the
   delegation property was never actually exercised.

Neither node was attributable to any open PR (`GET /pulls/{n}/files` across all 17 open PRs shows
no change to this test file), and both were already carried as accepted debt in
`tests/fixtures/baseline_node_set.txt`.

## 3. Repair

`tests/test_solspire_r1_governance_convergence.py` (test-only):

- The canonical-executor assertion now resolves the symbol where it lives and asserts it is
  callable: `weaver.execution.execute_patch`, with a comment naming `36bdcf01`.
- Both builders receive the same explicit `pass_id` / `objective`, so the key-by-key comparison
  compares two builders rather than two requests.
- A **non-vacuity control** was added: changing the patch's file set must change the adapter's
  `allowed_paths`. A constant-strip adapter would satisfy the equality assertions but fail this.

Measured: `5 passed` (was `3 passed, 2 failed`).

## 4. Baseline-set reconciliation (the repair must not leave the fixture over-reporting)

The recorded set is the repository's *live* debt, so repaired nodes leave it:

- `tests/fixtures/baseline_node_set.txt`: 10 → **8** nodes (2 removed).
- Canonical pair re-derived with `scripts/baseline_fingerprint.py`:
  - outcomes `9a54f5b4…` → **`0ec3c1102fd4e978bd11dd1b2544e80a42568b04974f9ca1ebe039d9492a14b9`**
  - node set `124bfdfd…` → **`e7405d233288b59c3f3456386de02c6607e0c270a4a09da5ae0f7b084a520967`**
- The prior 10-node pair is retained as **superseded** in `tests/test_baseline_fingerprint.py`
  (appended, so `SUPERSEDED_*[3]` still indexes the 18-node pair and
  `test_superseded_18_node_set_reproduces_the_superseded_pair` keeps its position).
- Both repaired nodes were added to `LIVE_RED_SHOULD_NOT_PASS_NODES`, so re-recording either one
  reddens the guard instead of silently restoring the stale expectation.
- The four published documents that carry the fingerprint (`.bootstrap/01_STATE.md`, `MISSION.md`,
  `NEXT_AGENT.md`, `docs/phase1/CONTINUATION_LEDGER.md`) were updated to the new canonical pair,
  with a dated supersession note naming the repair. The doc-agreement guard fails if a superseded
  value remains anywhere in those files.

## 5. Verification

| Check | Result |
|---|---|
| `pytest tests/test_solspire_r1_governance_convergence.py -q` | **5 passed** (pre-repair: 3 passed, 2 failed) |
| `pytest tests/test_baseline_fingerprint.py tests/test_baseline_fingerprint_ci_wiring.py tests/test_solspire_r1_governance_convergence.py -q` | **38 passed** |
| Live negative control: re-append one repaired node to the fixture | **2 failed** — exactly `test_live_node_set_reproduces_the_canonical_fingerprint` and `test_recorded_set_excludes_the_live_reconciled_repairs`; fixture restored byte-identically and the file re-hashes to `0ec3c110…` |
| `pytest tests/architecture -q` | see §6 |

`sha256sum tests/fixtures/baseline_node_set.txt` equals the canonical **outcomes** fingerprint,
because the fixture *is* the sorted `FAILED|ERROR <nodeid>` lines — an independent confirmation
that the recorded set and the published value describe the same thing.

## 6. Full-suite delta (same environment, node identity)

Same tree, same dependencies, one full-suite run per side
(`pytest tests/ -q -rEf --continue-on-collection-errors`).

| Tree | Summary | Nodes | Node-set sha256 |
|---|---|---|---|
| `main` `034d8879` | 35 failed / 4218 passed / 35 skipped / 1 error | 36 | `f37765c78e72fae4b332031f07e70dbbf25da3883920efb2aa3f31f9d439fbce` |
| branch | 33 failed / 4220 passed / 35 skipped / 1 error | 34 | `76922be43a9e037bf3b66115792c965ad51115177f72d7a2c16bf35142d2555e` |

`comm -3` over the two sorted node lists:

- **removed (2):** the two repaired `test_solspire_r1_governance_convergence.py` nodes.
- **added (0).**

The `+2 passed` is exactly the two repaired nodes; no node was introduced. `tests/architecture`
is **11 passed**. `api/main.py` is untouched and remains at 2597 lines (budget 2600).

## 7. Production observation (read-only, separate from this change)

Boundary pulse at `main` `034d8879`, canonical origin `https://arkadia-qzu4.onrender.com`:

| Probe | Result | Classification |
|---|---|---|
| `GET /api/version` → `source_revision` | `034d8879…`, `revision_conflict: false`, source `RENDER_GIT_COMMIT` | **VERIFIED** source↔runtime consistency (`scripts/version_reconciliation.py` → `MATCH`) |
| `GET /health` | `200` | reachable |
| `GET /` (browser `Accept`) | `200` after 3 × `503` | the 503s were Render's "Application loading" interstitial (258,535 B, `server: cloudflare`, `x-render-origin-server` absent), i.e. a **cold start**, not an application error |
| `scripts/gate2_production_observation.py` | `alias reachable: FAILED` | harness sampled during the cold start; PR #687 (`gate-hygiene/gate2-alias-cold-start-classification-01`) owns that classification |
| `scripts/production_runtime_probe.py` | 300 OpenAPI paths / 344 operations; **344/344** source↔runtime method+path match; 39 reachable, 105 protected, 6 present-but-404, 9 request-shape-rejected, **1 failing** | see below |

**The one failing route is real and is NOT repaired here:**
`GET /api/codex/github-tree` → **502**, body
`{"error":"Client error '401 Unauthorized' for url 'https://api.github.com/repos/…/git/trees/main?recursive=1'…"}`.
Two distinct defects: (a) the deployed runtime presents a rejected GitHub credential, and (b) the
handler echoes the upstream error text — including the upstream API URL — to an anonymous caller
(`api/main.py:1777`, `JSONResponse(status_code=502, content={"error": str(e)})`).

Recorded, not repaired, because the repair is bounded by the `api/main.py` **2600-line budget**
(the file is at **2597**) and because `api/main.py` is a shared surface; a one-line change would
consume the remaining headroom with no room for the accompanying guard. Proposed as a separate
bounded change: stop echoing `str(e)`, log server-side, and (optionally) retry unauthenticated when
a credential is rejected for a public repository.

## 8. CI at the branch head

All checks pass at `b03ee0b0` (11 checks; `baseline-fingerprint` among them, which is the runtime
proof that the reconciled guard is wired and green rather than merely asserted in source).

`beta-beta-01-english` / `bundle-beta-evidence` failed on the **first** run
(`45050020369`, 2026-11-22T17:32Z) and were re-run: `beta-beta-01-english` then passed.

Classification, from the log rather than the conclusion: the job reported
`RUN_FAILED ... "external runtime did not return usable inference"`, and **in the same run, on the
same tree, in the same minute, `beta-beta-02-hausa` passed**. A tree-caused failure cannot pass one
language and fail the other. `bundle-beta-evidence` then failed only because it asserts that both
evidence files are `PASS`. Neither job is selected by this diff, and neither ran on `main`
`034d8879` (path-filtered), so this is an external-provider flake, not a branch signal.

## 9. Non-claims

- No merge executed; no deployment triggered; no production acceptance claimed.
- The Gate-2 `deployment build output observed` boundary remains **UNKNOWN/BLOCKED**; this pass did
  not close it.
- The local suite's environment-shaped failures (TypeScript, Google/ASR extras) are **not**
  attributed to this change and were not repaired.
- `/api/codex/github-tree` is **FAILED** in production at the observed revision; the finding is
  recorded here and is not fixed by this PR.
