# WORKSTREAM_STATE — gate-hygiene / boundary-ruling verification + queue reconciliation

**Gate:** GATE-00 baseline hygiene (pre-gate engineering envelope)
**Workstream:** `gate-hygiene` → open-PR queue drain (companion to PR #257 / #252)
**Pass:** heartbeat, `BASE_MAIN` = `f10fef920e7ca46e6b41da82b2f9972cca0eb447`
**Branch:** `gate-hygiene/boundary-ruling-verification-and-queue-reconciliation-01`
**Classification:** `VERIFIED` (repository-layer) — **READY FOR SOVEREIGN MERGE**

---

## Objective (bounded)

Reconstruct the live queue, and answer the single question PR #257 left open: **did the sovereign
ruling on the HTTP evidence/verification boundary arrive, and does it re-point the two obsolete
route-absence nodes rather than weaken them?** Docs-only; supports, does not merge.

## State reconstructed this pass (live evidence, not memory)

| item | value |
|---|---|
| `main` / `origin/main` | `f10fef9` — agree |
| open PRs | **4** (#258, #257, #252, #246) |
| measured full suite @ `f10fef9` | 16 failed / 1405 passed / 21 skipped / 1 error (17 nodes) |
| `tests/architecture` | **11/11** |
| `api/main.py` | 2582 lines, `py_compile` clean |

## Finding — the ruling arrived and is coherent

- PR **#258** (`governance/console-evidence-boundary-option-a`, head `366812bf`) is the sovereign
  **Option A** ruling. Independently re-measured on its head (not the PR body):
  - node-set delta vs baseline: **removed 2 / added 0** — exactly the two superseded nodes;
  - the re-pointed assertions match `solspire/console_authority_router.py` **verbatim**
    (routes `:204` / `:279`, `require_auth`, `verifier=f"firebase:{user['uid']}"`, `store.evidence(`/`store.verify(`);
  - negative controls **preserved**: `forward_walk`/`reverse_walk` stay HTTP-absent, control-room
    projection stays a separate read surface;
  - workflow trigger added with **no** `${{ }}` interpolation, `contents: read` unchanged;
  - protected surfaces: architecture 11/11, `py_compile` OK, boundary tests 17 passed, exact
    workflow set **63 passed**; CI on head: `mvp2-validation` success + secret scan success.
- This satisfies the re-entry condition PR #257 recorded. **#252 is explicitly superseded by #258.**
- New, disclosed: `test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_…`
  is red on `main` and **absent from the classification ledger**; it is a mechanical
  stale-assertion repair (module contract implemented; precedent in
  `test_upstream_causal_continuity_01.py`). Recorded as **`SH-08`**, not repaired here.

## Regression boundary

Docs-only. No executable, workflow, governance, or constitutional file touched. Node set and
architecture fitness are unchanged vs baseline; no baseline failure re-attributed.

## Authority boundary

- No merge, no push to `main`, no force-push.
- No product decision made; `SH-08` recorded for the queue, not executed.
- `#258` is supported, not merged. Merge is the sovereign's act.

## Next bounded task (for the next heartbeat)

Reconstruct from live evidence first (contract §14). Dependency order:

1. **Sovereign merges #258** (the ruling). Then close/supersede **#252** and resolve **#257**
   (its blocker is now discharged) and **#246**.
2. Execute **`SH-08`** as its own bounded, test-only PR (no product decision required).
3. Do **not** re-open a boundary-contradiction repair: #258 is it.
