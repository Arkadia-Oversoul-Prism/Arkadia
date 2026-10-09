# PHASE 1 · Runtime Stabilization — PASS 2 · queue reconciliation and live baseline fingerprint

**Status:** OBSERVED — measurement + reconciliation record (no product code repaired here)
**Date:** 2026-10-09
**Measured at:** `main` `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Gate:** Phase 1 (runtime stabilization) · feeds GATE-10
**Predecessor:** `docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md`

This artifact continues the Phase 1 workstream. It (a) records the live
`main` baseline test-debt fingerprint, (b) classifies every currently failing /
erroring node by identity against the recorded debt, and (c) reconciles the open
PR queue that carries those repairs. It repairs nothing. No product code, test,
workflow, authority path, or mutation path is changed.

## 1. Environment (required for reproduction)

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ \
    --continue-on-collection-errors -rEf -q
```

`pyyaml` and `archive/legacy_python` are required for full-suite reproducibility.
Always run with `-rEf`: `-rf` alone suppresses pytest's `ERROR` summary lines and
yields a **subset** fingerprint (recorded lesson, `AGENTS.md`
"Baseline fingerprint — a recorded node set drifts").

## 2. Measured baseline on `main` @ `f9ced6b6`

```
15 failed, 1854 passed, 20 skipped, 2 warnings, 1 error in 148.01s
```

| | value |
|---|---|
| failing/error node set | **16** (15 failed, 1 error) |
| outcomes fingerprint | `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733` |
| ids fingerprint | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` |
| architecture suite (`tests/architecture`) | **11 passed** |
| CP10 gate integrity (`tests/test_m02a_ci_gate_integrity.py`) | **3 failed, 61 passed** |

**Independent corroboration.** PR #375 (`gate-hygiene/current-tip-composition-batch-0`,
base `a47ea928`, an ancestor of `f9ced6b6`) independently records the **same**
outcomes/ids fingerprint pair at `a47ea928`. The node set is unchanged across
`a47ea928..f9ced6b6`, whose commits are Firebase-config / economic-seam work that
touches no test. The fingerprint is therefore stable across the recent range, and
the synthetic baseline debt (54 failed / 9-of-10 architecture) is superseded by
this measurement, as `AGENTS.md` already documents.

### 2.1 How to attribute a regression

Counts are **not** an oracle. `test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
snapshots global `git status` and is order-dependent under the full suite, so the
*passed* count moves between runs of the same tree. Attribution must use the
sorted `FAILED`/`ERROR` **node set**, never totals.

## 3. Node classification at `f9ced6b6`

### 3.1 CP10 policy omission — real, repository-owned (3 nodes)

- `test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix`
- `test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface`
- `test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface`

**Class:** allowlist omission (real). `main` tracks `deploy/n-atlas-server/*`
(added by `e074a63b`) and the CP10 policy `LEGIT` does not admit `deploy/`. The
failure message is explicit: `deploy/n-atlas-server/app.py: Unexpected path
outside legitimate repository surfaces`.
**Owner:** PR #354 (see §5).

### 3.2 Browser-asset defect — real, repository-owned (0 test nodes; 1 enforced CI step)

`web/public_prism/index.html:16` loads `<script src="/firebase-config.js">`, but
`web/public_prism/public/firebase-config.js` is **not committed** (verified absent
on `main`). The CI frontend server 404s the path and the `validate` job's
`CP10 browser route verification` step fails (`Browser runtime errors observed`),
reddening `main`'s required gate. `entrypoint.sh` generates the file in the Render
dist at container start but the CI server does not.
**Owner:** PR #384 (see §5).

### 3.3 Test-side literal-pin drift — not a regression (3 nodes)

- `test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points`
- `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`
- `test_steward_filter.py` (3 nodes: `test_blocks_identity_claims`,
  `test_allows_mythic_with_action`, `test_compress_to_choices`)

**Class:** the recurring "test-side literal pin / substring match" defect class
(`AGENTS.md` "Test-side literal pins are a recurring defect class"). The
`test_steward_filter` trio is a **substring-matching** defect.
**Owners:** PR #347 (landing/identity copy pins), PR #365 (steward-filter repair).

### 3.4 Remaining pre-existing recorded debt (7 nodes)

| node(s) | class / owner |
|---|---|
| `test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated`, `::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` | **authority boundary** — `api/lab_routes.py` mutation surface; **sovereign-only** |
| `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | recorded pre-existing debt |
| `test_solspire_r1_governance_convergence.py` (2 nodes) | PR #357 (R1/R3 contract re-pin) |
| `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | PR #357 |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | recorded pre-existing debt |
| `test_autonomy.py` (`ERROR`, collection) | `weaver.autonomy` module-vs-package collision (CE-01) — **sovereign-reserved** |

The `test_engineering_lab_api.py` pins are unowned drift on an authority surface
(changed by `72432353` / `f96d5fd2`); repairing them edits `api/lab_routes.py` and
is sovereign-only. Proposed, not executed.

## 4. Changed paths

```
docs/control-plane/evidence/phase1-runtime-stabilization-02/EVIDENCE.md   (this file)
docs/control-plane/evidence/phase1-runtime-stabilization-02/WORKSTREAM_STATE.md
```

No product code, test, workflow, mutation path, or authorization path.

## 5. Open-PR queue reconciliation

28 open PRs at `f9ced6b6`. The load-bearing findings:

1. **#354 ⊃ #384.** PR #354 absorbed PR #384's browser-asset repair after #384
   was opened. The two shared files are **byte-identical** across the two heads:
   `git diff pr384:web/public_prism/public/firebase-config.js pr354:...` → empty;
   same for `tests/test_frontend_script_assets_resolve.py`. #354 additionally
   carries the CP10 `deploy/` allowlist rule and evidence. A **single** sovereign
   merge of #354 closes both real defects (§3.1 + §3.2).
2. **Composition-conflict PRs.** Several PRs re-measure the same 16→? cluster
   (#358 dirty, #361, #375, #376, #377). They are evidence-only and overlap; they
   should be reconciled as one record, not merged in parallel.
3. **Stale bases.** #365/#366 base `24a00f85`, #347 base `af3a3541`, #361/#368
   base `43c3e2b1` — all older than `f9ced6b6`. Merge order and re-base are a
   sovereign decision; this artifact only records the fact.

## 6. Independent verification of PR #354 (per the review contract)

Verified here, not trusting the author's PR body:

- Head `b6eec36b55ac7b7b125c777bcb030df03a699981`; 9 check-runs, all
  `completed/success` (incl. `validate`, `Build canonical Render image`,
  `Full-history secret scan`).
- Worktree at the head: `tests/test_frontend_script_assets_resolve.py` → **3 passed**;
  `tests/test_m02a_ci_gate_integrity.py` → **64 passed**; `tests/architecture` → **11 passed**.
- **Negative control on `main`:** `tests/test_m02a_ci_gate_integrity.py` → **3 failed**
  (the `deploy/` omission) and both `tests/test_frontend_script_assets_resolve.py`
  and `web/public_prism/public/firebase-config.js` are **absent**. The repair is
  genuinely needed and genuinely fixes its target.
- **Full-suite node-set delta, `main` → #354:** exactly the three
  `test_m02a_ci_gate_integrity.py` nodes are fixed; **zero** nodes newly introduced.
  (16 nodes → 13 nodes attempted; the 3-node delta is the repaired set.)

## 7. Authority boundary

Read-only measurement, classification, and in-repo evidence persistence on a
dedicated branch. **No merge, no push to `main`, no force-push.** Human authority
is required to merge. This pass does not claim production parity and does not
promote its own fitness result to acceptance.

## 8. Proposed next bounded workstreams (not authorized here)

1. **Merge #354** (sovereign) — closes §3.1 + §3.2 in a single merge; drop #384 as
   superseded.
2. `test-hygiene/boundary-pin-reconciliation-01` — repair the §3.3 nodes with a
   negative control per repair (partially covered by #347/#365; reconcile before
   duplicating).
3. `gate-hygiene/baseline-node-set-refresh-02` — refresh
   `tests/fixtures/baseline_node_set.txt` to the live 16-node set (§2), retiring
   stale entries. Overlaps #361; reconcile first.
