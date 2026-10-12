# GATE-10 — shared Knowledge OS connection contamination (test-hygiene)

Test-side repair. No application code, no authority surface, no merge.

- **BASE_MAIN** := `6109c72ab9eedc2593d2cc6c50ebd01596c80072` (`gate10: select executed
  tests and enforce CI verdict steps`, 2026-10-12T06:36:48+01:00)
- **Branch** := `gate10/sqlite-shared-connection-contamination-01`
- **Measured** 2026-10-12 in the canonical clone, pytest 9.1.1, Python 3.13.
- **Primary task** := PR #479 (`reconcile/security-lab-redaction-status-01`, open, non-draft,
  CLEAN, 11/11 checks green) is left untouched — this is a separate bounded workstream.

## 1. Defect

`knowledge/db.py` keeps **one SQLite connection per thread** in `threading.local()`:

```
_local = threading.local()
def get_connection():
    conn = getattr(_local, "conn", None)
    if conn is None:          # `None` means "not created yet"
        ... create, tune, store ...
    return conn               # anything else is returned AS-IS
```

`None` is the only sentinel for "needs creating", so a **closed** `sqlite3.Connection`
stored in the slot is handed back unchanged and every later query in that thread raises
`sqlite3.ProgrammingError: Cannot operate on a closed database`.

`tests/test_sqlite_busy_timeout.py::test_connection_waits_for_concurrent_sqlite_writers`
closes the session connection (correctly — it wants an isolated database) and then
**restored the closed handle** into the shared slot:

```python
old_conn = getattr(db._local, "conn", None)
if old_conn is not None:
    old_conn.close()
monkeypatch.setattr(db._local, "conn", None, raising=False)   # set None ...
...
monkeypatch.setattr(db._local, "conn", None, raising=False)
```

`monkeypatch` records the value present at the first `setattr` — which is the
**already-closed** `old_conn` — and `undo()` reinstates it at teardown. The `None` is a
transient the teardown erases. The defect is therefore *not* the close; it is the
restore.

## 2. Attribution

The failure is **order-dependent and therefore invisible to per-file runs**: the file
that poisons the slot is not the file that fails. The voice suites were the visible
cluster (8 nodes) and passed in isolation (34 passed).

Deterministic proof, priming a live connection first:

```
$ python -m pytest tests/test_zzz_probe.py::test_aaa_prime_a_live_connection \
    tests/test_sqlite_busy_timeout.py \
    tests/test_zzz_probe.py::test_zzz_probe_knowledge_ingest -q -s
PRIME conn id=139785974719936 live
..PROBE-INGEST-BROKEN: ProgrammingError: Cannot operate on a closed database.
```

Without the priming test the same probe printed `PROBE-INGEST-OK` — a passing case that
hides the defect, because no session connection existed yet for the teardown to restore.

Landed: `tests/test_sqlite_busy_timeout.py` in `717b622f` (2026-10-09); the voice suites
it breaks in `74e8ea53` (2026-10-07) — pre-existing, not branch-caused.

## 3. Repair

Clear the slot instead of restoring a dead handle (`tests/test_sqlite_busy_timeout.py`):

```python
db._local.conn = None      # after closing; `None` makes the next call create one
```

`monkeypatch` is still used for `db._DB_PATH`, so that patch is undone normally. The
explicit `None` at the end is not tracked by `monkeypatch` and survives teardown, so the
next `get_connection()` in the thread builds a fresh, tuned connection.

## 4. Guard

`tests/test_knowledge_shared_connection_lifecycle.py` runs the busy-timeout test for real
under its own `MonkeyPatch`, undoes it, and asserts the shared slot is still usable. It is
a **negative control**: it fails on the unrepaired revision and passes on the repaired one.

```
$ python -m pytest tests/test_knowledge_shared_connection_lifecycle.py -q   # pre-repair
1 failed, 1 passed
E  sqlite3.ProgrammingError: Cannot operate on a closed database.
$ python -m pytest tests/test_knowledge_shared_connection_lifecycle.py -q   # post-repair
2 passed
```

## 5. Regression boundary

Failing/error node **set** (never raw counts), same environment, same tree:

- `main` `6109c72a` : **18** nodes — `8 failed, 2864 passed, 20 skipped, 1 error` in 197s
- branch           : **9** nodes — `8 failed, 2875 passed, 20 skipped, 1 error` in 197s
- `comm -23 main branch` → the 9 recovered nodes; `comm -13` → **empty** (no new failures)

Recovered (all pre-existing debt on `main`):

```
tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip
tests/test_voice_context.py::test_ask_is_informational_and_known
tests/test_voice_context.py::test_search_is_known_and_lists_matches
tests/test_voice_context.py::test_transfer_clarification_resolves_to_known
tests/test_voice_context.py::test_transfer_with_multiple_recipients_is_ambiguous_on_recipient
tests/test_voice_context.py::test_transfer_with_multiple_reports_is_ambiguous
tests/test_voice_context.py::test_transfer_with_unknown_recipient_is_unknown
tests/test_voice_pipeline.py::test_informational_request_needs_no_proposal_or_approval
tests/test_voice_pipeline.py::test_unsupported_executor_is_explicit_not_silent
```

`tests/test_static_ingestion_idempotency.py` was an earlier-ordered victim that the first
pass did not list; the node-set diff found it.

Protected surfaces: `tests/architecture` **11 passed**; `python -m py_compile api/main.py`
OK (`api/main.py` = 2505 lines, budget 2600, untouched).

Composition hazard checked: the new file is a `tests/**/test_*.py`, admitted by CP10
(`--judge` exit 0), and adds **no** new workflow, so no content-derived guard domain grows.
The executes-to-selects and wiring guards were re-run and stay green (201 passed).

## 6. Not claimed

- The remaining **9** nodes are pre-existing, unrelated debt, left untouched:
  `ERROR tests/test_autonomy.py` (CE-01 module-vs-package collision, sovereign-reserved),
  the two `tests/test_engineering_lab_api.py` pins (authority surface, sovereign-only),
  and the SolSpire/identity/AIS pins. Repaired here only where the fingerprint changed.
- **Defect A** (bare `pytest tests/` aborting before reaching the suite) is **already
  repaired on this main**: `provider-routing.yml:42` carries
  `-q -rEf --continue-on-collection-errors`. `sg-02-fe-2-v.yml:239` still runs a bare
  `pytest tests/ -q` under `continue-on-error: true`; that is a **separate proposed
  workstream** (mutating a CP10 workflow needs sovereign authorization), not executed here.
- No runtime/deployment claim. Repository-source and test-execution evidence only.
