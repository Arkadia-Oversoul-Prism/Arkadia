# WORKSTREAM_STATE — gate-hygiene / CE-01 `weaver.autonomy` collision disposition

**Gate:** GATE-00 baseline hygiene (pre-gate engineering envelope)
**Workstream:** `gate-hygiene` → collection-error disposition (`CE-01`)
**Pass:** heartbeat, `BASE_MAIN` = `002b189dd95e41c9b4f4cca33d08b4121453d289`
**Branch:** `gate-hygiene/ce01-autonomy-collision-disposition-01`
**Classification:** `VERIFIED` (repository-layer) — **READY FOR SOVEREIGN MERGE**
**Authority required:** yes — one decision (§10 of `EVIDENCE.md`), but the merge of *this*
docs-only artifact is independently safe.

---

## Objective (bounded)

The queue recorded that CE-01 *"needs a sovereign decision"* — `CONTINUATION_LEDGER.md:393,1331`
and PR #149 — but **no artifact carried the disposition**. Every open PR was checked; none
claims it. This pass writes the disposition down, with the decision-relevant facts measured
rather than restated.

**Result:** the ledger's `CONTRADICTED as autonomous work` is **confirmed and strengthened**,
and the bounded action is **no repair**. Evidence: `EVIDENCE.md`.

---

## State reconstructed this pass (from live evidence, not memory)

| item | value |
|---|---|
| `main` / `origin/main` | `002b189` (merge of #141) — agree |
| open PRs | **22** (#142–#160) |
| full suite | `20 failed / 1039 passed / 13 skipped / 2 collection errors` |
| `tests/architecture` | **11/11** |
| `api/main.py` | 2519 / 2600 lines, `py_compile` clean |
| `vite build` | environment-blocked (no npm registry) — unchanged |

Fingerprint **identical** to the recorded `002b189` baseline (PR #149 §"State reconstructed").
No drift attributable to any open PR.

## Finding — the collision is a defect, and un-shadowing does not repair it

1. `from weaver.autonomy import load_autonomy_config` → `ImportError`; the package shadows the
   module. Both sides are **blob-identical to Genesis `9ab26fc`** — no history to break the tie.
2. **Decisive:** loading the legacy module *directly* (bypassing the shadow) and running the
   test's own assertion gives `{'ran': False, 'reason': 'disabled'}` → `assert res['ran'] is
   True` **still fails**. The collection error *masks* a substantive failure; un-shadowing
   converts 1 red node into 2. There is no hygiene case for the repair.
3. The module drives `RecursiveEngine` → `weaver.agent.agent_run` → commit messages. Dormant
   behind **three config barriers** (`enabled:false`; `approved_by:"governance"` absent from
   `roles.json`; `require_env`), each invertible by a JSON edit. Nothing invokes the path today.
4. `weaver/session_kernel.py:11` imports `weaver.autonomy.guard` in **production** — so the
   package cannot be deleted either. Neither side is disposable.

## Explicitly NOT done, and why

- **No un-shadowing, no deletion, no rename.** Every candidate action mutates an autonomous
  mutation path or a governance surface (§6 of `EVIDENCE.md`) — reserved to the sovereign.
- **No touch of CE-02.** `tests/test_render_codex.py` is owned by open PR **#149**; it is named
  here only so the "two collection errors" pairing stays accurate.
- **No fix of any other baseline debt.** 20 failing nodes remain as classified by the ledger
  (`BASELINE_TEST_DEBT_CLASSIFICATION.md`). The SG-04 set (`test_spiral_grove_activity_runtime.py`,
  4 nodes) stays escalated — it needs a `web/public_prism/**` capability change, outside the
  test-only boundary and CP10 path-filtered.
- **No bootstrap edits.** `.bootstrap/03_SCOPE.md` staleness is owned by open PR **#157**.

## Authority boundary

No merge, no authorization, no identity change, no new mutation path, no new authorization path,
no governance/constitutional change, no boot-file change. Docs-only, under
`docs/control-plane/evidence/`. `api/main.py` untouched (2519/2600).

## Next bounded task (for the next heartbeat — re-derive, do not trust this line)

CE-01 is now **dispositioned**; it must not be re-litigated. The queue's remaining unclaimed
`gate-hygiene` work is the SG-04 escalation (escalated, needs a frontend capability decision)
and the 20 classified failures. The next heartbeat should first check whether the #149/#157/#144/#145
queue has moved, since several of those close nodes this artifact treats as open.
