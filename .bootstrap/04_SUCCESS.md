# 04 — Success Criteria
> Binary. No interpretation. If any item is unchecked, the session is not done.

---

## B1.1 — SQLite Schema

- [ ] `kernel/storage/__init__.py` exists
- [ ] `kernel/storage/schema.py` exists and contains `create_tables(db_path)`
- [ ] `create_tables()` is idempotent — safe to call twice
- [ ] Schema matches `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` exactly
- [ ] WAL mode enabled in `create_tables()`
- [ ] `tests/test_sqlite_schema.py` exists and passes
- [ ] `pytest tests/architecture/ -v` → 10/10 (no regressions)
- [ ] No new layer violations introduced
- [ ] `data/runtime.db` is NOT committed (runtime state, not source)
- [ ] `01_STATE.md` updated: B1.1 complete, B1.2 ready
- [ ] `03_SCOPE.md` rewritten for B1.2
- [ ] `04_SUCCESS.md` updated for B1.2
- [ ] `NEXT_AGENT.md` rewritten for B1.2
- [ ] `docs/phase1/CONTINUATION_LEDGER.md` updated with session record

Done when all items are checked. Stop immediately.

---

## How to Check

```bash
pytest tests/test_sqlite_schema.py -v
pytest tests/architecture/ -v
python -c "from kernel.storage.schema import create_tables; create_tables('data/test_runtime.db'); print('OK')"
```
