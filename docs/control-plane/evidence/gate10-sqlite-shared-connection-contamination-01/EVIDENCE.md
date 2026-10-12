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

## 7. Execution site for the guard (this pass)

The guard added in §3 was executed by **no** workflow. `grep -rln
test_knowledge_shared_connection_lifecycle .github/workflows/` returned 0: the two
workflows whose `tests/**` filter *selects* a change to it (`economic-seam-engine.yml`,
`prism-console-contract.yml`) run only their own derived domains, and
`provider-routing.yml` — the only workflow that runs the full suite — is path-filtered to
`weaver/**`, `providers/**`, `api/lab_routes.py` and named files, and is baseline-red on
`main` besides. A guard no gate executes is decoration, and this defect is
**order-dependent** — the file that poisons the shared slot is not the file that fails —
so it is invisible to per-file runs.

`.github/workflows/knowledge-connection-lifecycle-guard.yml` is the executable surface. It
runs the guard, the busy-timeout contract and the wiring guard **together**, because the
boundary can only be judged by a session that runs both sides.

`tests/test_knowledge_shared_connection_lifecycle_ci_wiring.py` keeps it executed. The
invariant is stated generically over every workflow that **names** the contract: some
workflow must execute it on `pull_request`; it must be dispatchable; every declared
`paths` filter must select every input the guard reads; an executing step must be able to
fail the run; and the job must install what it runs. Inputs are derived from the guard's
source by **AST**, not restated, so an input added without a filter entry is a defect the
guard reports instead of one it silently tolerates.

The detector bit on two real conditions before it bit on any synthetic one: the contract
imports `knowledge.db`, which resolves to `knowledge/db.py` **and** the package
`knowledge/__init__.py`, and a bare `test_sqlite_busy_timeout` import resolves under
`tests/` — neither was in the first draft's filter.

Scoped to a *mention*, not a directory-argument reach: `provider-routing.yml`'s
`pytest tests/` does execute the contract, but auditing every workflow whose directory
argument covers it would report that gate's pre-existing, baseline-red debt as a wiring
defect of this guard. A gate that names the guard is the gate that owns its execution.

### Proof

- Guard + contract + wiring guard: **12 passed**.
- Live negative controls, each on the **real** workflow file, restored byte-identically
  (`sha256 e5510a18…` after restore, 12 passed again):
  - executing step → `echo pytest <contract>`: **3 failed** (mention is not execution);
  - job-level `continue-on-error: true`: **3 failed** (gate cannot fail);
  - `tests/test_sqlite_busy_timeout.py` removed from both `paths` filters: **2 failed**
    (filter omits an input).
- Guard bites on the defect: reintroducing the pre-repair form (restoring the **closed**
  handle into the slot) reddens it with `sqlite3.ProgrammingError: Cannot operate on a
  closed database`; restored byte-identically.
- Generic workflow-scanning suites (`test_workflow_injection_boundary.py`,
  `test_ci_gate_trigger_coverage.py`, `test_ci_suite_collection_continuation.py`,
  `test_m02a_ci_gate_integrity.py`): **253 passed** — the new workflow satisfies them by
  construction.
- `tests/architecture`: **11 passed**. CP10 `--judge` for both new paths: exit **0**.
  `api/main.py` untouched (2505 lines, budget 2600).

`python -m pytest tests/ -q` is re-run with `--continue-on-collection-errors`: the CE-01
`weaver.autonomy` module-vs-package collision interrupts the session otherwise, which is
the documented pre-existing debt and not attributable to this change.
