# 04 — Success Criteria
> Binary. No interpretation. If any item is unchecked, the session is not done.

---

## Session state

**No session is active.** There is no current checkpoint, so there are no live success
criteria. Reconciled 2026-09-30 (Weaver pass
`gate-hygiene/bootstrap-scope-reconciliation-01`).

---

## B1.1 — SQLite Schema — **CLOSED** (historical record)

Closed on `main`; recorded in `docs/checkpoints/B1.1.md` (commit `1a38633`) and in
`docs/phase1/CONTINUATION_LEDGER.md`. All criteria below were re-verified against
`main` @ `002b189` on 2026-09-30.

- [x] `kernel/storage/__init__.py` exists
- [x] `kernel/storage/schema.py` exists and contains `create_tables(db_path)`
- [x] `create_tables()` is idempotent — safe to call twice
- [x] Schema matches `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` for `jobs` / `goals`
      (`corpus_sync_state` / `corpus_file_state` are later additions from C1.1)
- [x] WAL mode enabled in `create_tables()`
- [x] `tests/test_sqlite_schema.py` exists and passes — **11 passed**
- [x] `pytest tests/architecture/ -v` → 11/11 (no regressions)
- [x] No new layer violations introduced
- [x] `data/runtime.db` is NOT committed (runtime state, not source)
- [x] `01_STATE.md` updated: B1.1 complete, B1.2 ready
- [x] `03_SCOPE.md` rewritten for B1.2
- [x] `04_SUCCESS.md` updated for B1.2
- [x] `NEXT_AGENT.md` rewritten for B1.2
- [x] `docs/phase1/CONTINUATION_LEDGER.md` updated with session record

B1.2 is likewise already implemented and closed (`kernel/storage/sqlite_job_store.py`,
`kernel/storage/sqlite_goal_store.py` both present).

---

## How to Check

```bash
pytest tests/test_sqlite_schema.py -q    # 11 passed
pytest tests/architecture/ -q            # 11 passed
python -c "from kernel.storage.schema import create_tables; create_tables('data/test_runtime.db'); create_tables('data/test_runtime.db'); print('idempotent OK')"
```
