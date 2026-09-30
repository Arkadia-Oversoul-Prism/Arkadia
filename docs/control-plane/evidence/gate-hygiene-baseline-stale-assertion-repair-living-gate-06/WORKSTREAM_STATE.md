# WORKSTREAM_STATE — `gate-hygiene` / SH-02 batch 6 (Living Gate / W2)

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.

## Workstream

SH-02 baseline **STALE_ASSERTION** migration: repair failures whose fingerprint is a stale
source-level string assertion against a reworded-but-intact governance property. Scope is
test-only. It does **not** cover `DRIFT`, `SH-08` governance contradictions, or
product-decision nodes.

Classification source of truth:
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`.

## Pass record — 2026-09-29 (heartbeat)

- **Reconstructed:** `origin/main` = `df7a99a067382401c00de5e7bbaaac0125ba2088` (PR #131
  merged). **Zero open PRs** — verified: #130, #131, #132 are all **merged**, not open. The
  batch-5 ledger still described #130/#132 as open; that is now stale.
- **First branch-pick was wrong and was corrected.** The prior branch
  (`gate-k2/provider-non-mutation-contract` @ `4164573`) is based on a commit that
  **predates** #130/#132/#131. Baselining it against `df7a99a` produced seven false "new
  failures" — all seven were sibling gate-hygiene nodes the merges had already repaired.
  Re-based onto `df7a99a`; false deltas vanished. See `EVIDENCE.md` §1.
- **Publication:** branch `gate-w2/living-gate-grove-handoff`, PR to follow. Test-only +
  evidence docs. No merge, no force-push, `main` untouched.

## Fingerprint (measured this pass, not remembered)

```
main df7a99a                 : 32 failed / 1025 passed / 13 skipped / 2 errors  (34 nodes)
branch gate-w2/…             : 27 failed / 1031 passed / 13 skipped / 2 errors
  delta                       : −5 failures, all five the repaired W2 nodes; ZERO added nodes
architecture                 : 11/11
py_compile api/main.py       : pass    (api/main.py = 2519 / 2600)
vite build                   : environment-blocked
```

**Stale figures to stop repeating:** the contract's `main := 6038989` / `804 passed` /
`architecture 9/10`, and the batch-5 ledger's `39 failed / 1018 passed` at `4164573`. Both
predate the #130–#132 merges.

Node inventory (compare by **name**, and only against a base the branch is actually rebased
onto — compare-by-count alone has now produced a wrong diagnosis twice):

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

## Batch ledger

| Batch | Branch | Nodes | State |
| --- | --- | --- | --- |
| — | merged PR #124 | SCI / nexus 6-node | **merged** |
| — | merged PR #125 | Solariun consolidation 3-node | **merged** |
| — | merged PR #127 | `test_prism_pass_c_surface_ownership.py` 13-18 | **merged** |
| 3 | PR #130 | identity spine / `ais_profile` | **merged** @ `587df17` |
| 4 | PR #132 | `test_ais_w6_future_skills_challenge.py` (node 9) | **merged** @ `cefb2f5` |
| 5 | PR #131 | `spiral_grove_{chambers,frontend_projection,learning_path_projection}` (nodes 24-26) | **merged** @ `ddb30d0` |
| 6 | `gate-w2/living-gate-grove-handoff` | `test_ais_w2_living_gate_grove_handoff.py` (nodes 3-8) | **this PR** |
| d | `gate-hygiene/sh02d-prism-interior-shell` @ `8d1c386` | `test_prism_interior_shell.py` (nodes 10-12) | **unblocked** — PR #129 merged, rebase no longer collides; no PR yet |

### Batch d is now unblocked

Batch d was held because it edits
`…/BASELINE_TEST_DEBT_CLASSIFICATION.md`, which PR **#129** rewrote. **#129 has merged**, so
the collision is resolved in principle — but the local ledger is now §11-corrected and d's
diff (and its stale `/tmp/` node lists) must be rebased and re-verified before publishing.
Not attempted this pass: it needs its own base re-verification, and mixing it into batch 6
would widen scope.

## Open item — F-01 (not this workstream)

`test_no_firebase_persistence_in_gate` is left failing **as `main` carries it**. The gate
holds zero `firebase`/`firestore` references; the `sessionStorage` proxy now catches a
tab-scoped diagnostic handoff. Re-pinning would loosen a persistence boundary →
governance call. `DECISION_CACHE.md` records Living Gate as **"DEFERRED — action required"**.

**Continuity gap closed this pass:** the escalation had no in-repo record — both docstrings
cited `…-sci-nexus-01/WORKSTREAM_STATE.md`, which does not mention it. Those references now
point at `…-living-gate-06/EVIDENCE.md` §5–6.

Second, related finding (§6): `LivingGate.tsx` is **imported by nothing**; `App.tsx` routes
`gate`/`aic`/`login` to `NodeEntry`. So "NodeEntry imports the canonical catalogue" and
"LivingGate is the A.I.S surface" are mutually exclusive. `test_identity_spine_w1.py::
test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` asserts the first. Also
`DECISION_CACHE`-tracked; not patched.

## Next bounded tasks (proposed, not authorized)

1. **Batch d** (`sh02d-prism-interior-shell`, nodes 10-12) — rebase onto current `df7a99a`
   (post-#129 ledger), re-verify, publish. Cheapest genuine progress; was blocked, now is not.
2. **Un-rendered version-string assertions** from batch-5 evidence (candidate batch 7).
3. Remaining `STALE_ASSERTION` clusters not owned by open work and not `SH-08` / product
   decisions.

Each requires a bounded scope, completion condition, evidence requirement, regression
boundary, and authority boundary before execution.

## Tooling reality carried forward

- Clone is **shallow** (`.git/shallow`) — ancestry beyond the fetched window is not
  inspectable; fetch with `--depth` before any base claim.
- `tests/test_weaver_provider_non_mutation.py` is uncommitted K2 WIP, unrelated to this pass;
  it fails on `data/*.db-wal` / `-shm` sidecars — a possible `.gitignore` gap, worth its own
  bounded pass.
