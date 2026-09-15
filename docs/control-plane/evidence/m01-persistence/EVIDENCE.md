# M01 — Persistence Architecture · Evidence

Trajectory: ARKADIA-TRUTHFULNESS-01
Move: M01 — persistence-architecture
Branch: `weaver/arkadia-truthfulness/m01-persistence`
Status: **READY_FOR_REVIEW** (not accepted — human review remains mandatory)

---

## 1. Scheduler liveness (observed, not configured)

Workflow `arkadia-engineering-scheduler.yml` is present on `main` and **is
waking**. Evidence is from actual runs, not from the presence of a cron entry.

| field | value |
|---|---|
| workflow | Arkadia Engineering Scheduler (`.github/workflows/arkadia-engineering-scheduler.yml`) |
| runs total | 13 |
| latest scheduled run ID | `34983589725` |
| event | `schedule` |
| conclusion | `success` |
| head SHA | `0a4d79ee25a6723b0b4975d9c891db723e1be2bb` |
| branch | `main` |
| created | 2026-09-15T14:43:40Z |
| job `engineering-scheduler` | completed success, 14:43:43Z → 14:43:54Z |
| manual dispatch run | `34782913172` (2026-09-13T21:08:30Z, `workflow_dispatch`, success, 47s) |
| cadence | `0 * * * *` |
| concurrency | `group: arkadia-engineering-session`, `cancel-in-progress: false` (`max_active_moves: 1`) |
| permissions | `contents: read`, `actions: read` |

Nine consecutive successful scheduled runs were observed across
2026-09-13 → 2026-09-15. The earlier "no execution for 24h" observation was
**falsified** by repository evidence: the runs existed and succeeded. The two
`failure` entries in the list are `push`-triggered runs at 0s from the bootstrap
commits — they are not the schedule path.

## 2. Weaver routing (derived, not hardcoded)

From the runner log of run `34983589725`:

```
##[notice]status=READY_FOR_REVIEW next_move=M01
"next_move": { ... "autonomous_next_move" ... }
"continues_to_next_move": false
```

The worker derived `M01` from repository state. The workflow contains no
`run_m01()`-equivalent, no first-run branch, and no hardcoded move id.

## 3. Defects found and repaired

### 3.1 SQLite connection leak — `solspire/project_store.py`

`_db()` returned a raw `sqlite3.Connection`. Every call site uses `with _db() as
c:`, and `with` on a connection is a **transaction** context — it commits but
never closes. Every project/task/file/memory operation therefore leaked one
connection. `_db()` is now a `@contextlib.contextmanager` that commits, rolls
back on error, and always closes.

### 3.2 Corpus path not relocatable — 8 modules

`_DB_PATH` read only `SOLSPIRE_PROJECTS_DB` with a CWD-relative default. On a
platform where the writable volume is not the CWD the corpus would silently land
somewhere ephemeral. All eight modules now honour
`SOLSPIRE_DATA_DIR` (default `data`).

### 3.3 Schema creation order — cold-start restore could not run

Only `ProjectManager._db()` created the `projects` table; `project_store._db()`
created only the sub-resource tables. A restore that touches the store first hit
`no such table: projects`. The DDL is now single-sourced in
`ensure_projects_table()`, which both modules call.

### 3.4 Durable-store outage could fail a request — `project_persistence.py`

`_fb()` was invoked outside the `try` in `mirror_project()`, so an
import/init failure raised into the caller's mutation. Resolution is now
non-raising (`_resolve()`); mirroring is strictly best-effort.

### 3.5 Durable-store values were not SQLite-coercible

Restore passed structured values (dict/list) into TEXT columns.
`_coerce()` re-serialises containers and normalises booleans.

### 3.6 `api/main.py` line budget — caught by the architecture test

The first startup hook pushed `main.py` to 2604 lines against a 2600 budget.
The logic moved into `solspire/project_persistence.py::startup_restore()`; the
startup block is now a single call.

### 3.7 Evidence was entirely gitignored

`.gitignore` ignored `docs/control-plane/evidence/**/`, so a committed acceptance
record was impossible and no later wake could reconstruct a review decision from
the repository. Only the generated per-run reports remain ignored.

## 4. Implementation

One durable model, reused. No second database, filesystem, project model,
memory system, or identity system.

```
AUTHENTICATED LOCAL-FIRST WORKSPACE STORE      (solspire/project_*.py, SQLite)
                    │  mirror on every mutation (best-effort)
                    ▼
        EXISTING DURABLE CORPUS                  (api/firebase_store.py — the
                    │                             store already used for jobs/goals)
                    │  restore on startup (additive, idempotent)
                    ▼
              local SQLite again
```

- `solspire/project_persistence.py` (new) — the bridge: `mirror_project`,
  `mirror_by_child`, `restore_project_corpus`, `restore_payload`,
  `startup_restore`, `persistence_status`.
- `api/firebase_store.py` — project-corpus functions added to the **existing**
  durable store (`fb_sync_project`, `fb_sync_project_children`,
  `fb_delete_project`, `fb_load_project_corpus`).
- `solspire/project_store.py` — mirror hooks on every create/update/delete
  across conversations, files, repositories, tasks, memory, and events.
- `solspire/project_manager.py` — mirror on create/archive; canonical
  `apply_fields()` update path so the router no longer opens its own connection.
- `solspire/console_router.py` — `update_project` routed through the manager.
- `api/main.py` — one startup restore call.

Synchronisation direction is **local-first**: SQLite stays the read/write path;
the durable corpus is written on mutation and read only to repopulate an empty
local corpus.

## 5. Acceptance evidence

`tests/test_m01_persistence.py` — 13 tests, all passing.

| acceptance criterion | test |
|---|---|
| browser refresh / session interruption | `test_project_and_subresources_survive_local_corpus_loss` |
| backend redeploy (local FS replaced) | same (SQLite file deleted, corpus restored) |
| logout/login recovery | same (owner identity recovered with the row) |
| repeated wakes do not duplicate | `test_recovery_is_idempotent_across_repeated_wakes` |
| local writes not clobbered | `test_restore_never_clobbers_local_writes` |
| deletion propagates | `test_deletion_propagates_to_durable_corpus` |
| ownership preserved | `test_ownership_travels_and_is_never_widened` |
| cross-user isolation | `test_other_user_cannot_recover_another_users_project` |
| legacy NULL-owner rows stay invisible | `test_legacy_null_owner_rows_stay_invisible_after_restore` |
| no orphan children resurrected | `test_orphan_child_rows_are_not_resurrected` |
| single project model | `test_local_sqlite_remains_the_single_project_model` |
| durable outage never fails a request | `test_mirroring_failure_never_breaks_a_mutation` |
| connection lifecycle | `test_repeated_mutations_do_not_leak_connections` |
| path relocatability | `test_db_path_honours_data_dir_env` |

Representative data exercised across every sub-resource table: a project, a
conversation with a message, a file with content, a linked repository, a task,
and a memory.

### Suite result

```
44 failed, 683 passed, 10 skipped
```

Baseline on unmodified `main` (`0a4d79e`): **51 failed, 676 passed, 10
skipped**. Differential: **zero regressions**, and the seven M01 tests that
failed in the baseline run are now green (they failed only because the module
under test did not yet exist). The 44 remaining failures are pre-existing and
unrelated to M01 (weaver SCI/W5 boundary tests, `api/nodes.py` layer inversions,
and two modules that fail to import: `test_autonomy.py`, `test_render_codex.py`).

## 6. Known limitations

- **Frontend redeploy** is structural only: the workspace corpus is server-side,
  so a frontend redeploy cannot drop it. Not exercised against a live Vercel
  deploy.
- **Backend redeploy survival is simulated**, not observed in the deployed
  environment: the test deletes the SQLite file and re-runs the real startup
  restore. Verifying against the live deployment requires deployment
  authorization, which has not been granted — see §7.
- **Firestore is not exercised.** The tests use an in-process fake of the
  durable-store interface, so `api/firebase_store.py`'s new functions are
  covered by inspection, not by a live call. The bridge and the restore path are
  the real ones.
- **Conflict handling** is last-write-wins on a per-child basis and there is no
  merge for concurrent edits on two devices. M01 does not require it; recorded
  so it is not mistaken for solved.
- **Deleted rows are not tombstoned.** Restore is additive, so a project deleted
  while the durable store was unreachable could reappear from the corpus.

## 7. Boundaries respected

- **Merge:** not performed. The worker may open a PR; it may not merge it.
- **Deployment:** not performed. No deployment config was altered.
- **Secrets:** none added, read, or logged. Ownership fields travel verbatim and
  are never widened — no identity widening was introduced.
- **Scope:** M01 only. M02 was not started.
- **Second storage systems:** none. The diff adds no database, filesystem,
  project model, memory system, or identity system.

## 8. Next legal move

Human review of this PR.

- On **accept**: M01 closes; the next legal move is M02 — reasomate.
- On **revision required**: M01 remains the active move; the dependency-aware
  sequential scheduler will not advance past it (`max_active_moves: 1`).