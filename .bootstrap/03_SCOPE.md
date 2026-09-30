# 03 — Scope
> Rewritten every session. This is the session scratchpad.
> Current session: **none selected** — see "Session state" below.

---

## Session state

**No checkpoint is authorized by this file right now.**

This file previously carried a `B1.1 — SQLite Schema` session brief. That checkpoint was
**closed on `main` long ago** and the brief was never rewritten, so it has been asserting a
session that no longer exists. Reconciled 2026-09-30 (Weaver pass
`gate-hygiene/bootstrap-scope-reconciliation-01`).

Verified state of B1.1 on `main` @ `002b189`:

| B1.1 success criterion | live evidence |
|---|---|
| `kernel/storage/__init__.py` exists | present |
| `kernel/storage/schema.py` contains `create_tables(db_path)` | present |
| `create_tables()` idempotent — safe to call twice | `create_tables()` twice → no error |
| Schema matches `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` | `jobs` + `goals` match; `corpus_*` added later by C1.1 |
| WAL mode enabled | `PRAGMA journal_mode = WAL` (`kernel/storage/schema.py:31`) |
| `tests/test_sqlite_schema.py` passes | **11 passed** |
| `pytest tests/architecture/ -v` → 11/11 | **11 passed** |
| No new layer violations | architecture suite green |
| `data/runtime.db` NOT committed | not tracked |

B1.2 (`sqlite_job_store.py`, `sqlite_goal_store.py`) is also already implemented and closed —
see `docs/phase1/CONTINUATION_LEDGER.md` (B1.1 CLOSED, commit `1a38633`).

**Do not begin B1.1.** It is done.

---

## Selecting the next checkpoint

This file is a **session scratchpad, not a plan**. It must not select a checkpoint by itself.

`.bootstrap/01_STATE.md` is the single source of truth for *what is next*, and it is already
being reconciled to live evidence by the open PR `gate-k/k5-status-reconciliation` (#146).
Until that lands, derive the next checkpoint from the repository, not from prose:

```bash
pytest tests/architecture/ -q        # expect 11/11
git log --oneline -10                # what actually landed
curl -s "https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/pulls?state=open"
```

The next genuine checkpoint per live evidence is **K4 — Response Provenance**, and an
implementation is already carried by the open PR `gate-k/k4-response-provenance-01` (#153).

---

## Files to Read (and only these)

None — no checkpoint is selected.

## Files to Create (and only these)

None — no checkpoint is selected.

## Files Forbidden This Session

```
tests/architecture/     — never in Build mode
LAYER_MAP.py            — never in Build mode
Any ADR or governance doc — check 02_DECISIONS.md instead
```

## Stop Condition

Not applicable — no checkpoint is selected. A checkpoint brief must be written here, and
`01_STATE.md` must name it, before any Build session begins.
