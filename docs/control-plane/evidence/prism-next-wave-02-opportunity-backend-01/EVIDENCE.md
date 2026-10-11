# Workstream 2 — next wave: buyer-recon backend repair + Opportunity Radar mount

**Branch:** `feat/prism-next-02-opportunity-backend`
**Starting `main`:** `962434bed1bccb11fbf5edfcb0299317b12a8915`
**Ownership:** `SHARED-CONTRACTS.md` §1/§7.1 — scoped ownership of
`solspire/buyer_recon.py` and `solspire/buyer_recon_router.py` for exactly the two
measured defects, plus regression tests. No merge, deployment, or acceptance.

---

## 1. Defects reproduced (before any change)

Both were reproduced against a fresh database before editing:

```
$ python -c "…BuyerReconManager().create_entry(board, {'prospect': 'Test Buyer'})"
OperationalError: table buyer_recon_entries has 33 columns but 34 values were supplied

$ python -c "…get_or_create('ws-1:project:p1', 'uid-1')"   # after a workspace board exists
IntegrityError: UNIQUE constraint failed: buyer_recon_boards.subject_ref
```

* **Defect 1 — create-entry arity.** `create_entry` supplied **34** values to a
  **33**-column `buyer_recon_entries` table under a bare `VALUES (?,?…)`.
* **Defect 2 — one board per subject.** `buyer_recon_boards.subject_ref` was
  `TEXT NOT NULL UNIQUE` on the subject alone, while `_project_board` keys the
  board on the composite `"{workspace.id}:project:{project_id}"`. One subject
  could therefore hold only one board, so the project radar was unreachable for
  any subject who had opened the workspace board.

Both introduced at `5de6d476` (PR #199).

## 2. Repairs

### Defect 1 (`solspire/buyer_recon.py`)
`create_entry` now names its columns and derives them from the dataclass:

```python
_ENTRY_COLUMNS = tuple(
    "evidence_json" if field == "evidence" else field
    for field in BuyerReconEntry.__dataclass_fields__
)
…
INSERT INTO buyer_recon_entries ({columns})
VALUES ({','.join('?' * len(_ENTRY_COLUMNS))})
```

The value tuple and the column list come from the same source, so the two cannot
drift again. The one field whose column differs (`evidence` -> `evidence_json`)
is mapped explicitly; every other field is a same-named column in the same order.

### Defect 2 (`solspire/buyer_recon.py`)
The subject-only uniqueness is replaced by the composite scope:

```sql
CREATE UNIQUE INDEX idx_buyer_recon_boards_scope
ON buyer_recon_boards(workspace_ref, subject_ref)
```

`buyer_recon_boards` now declares `workspace_ref` and `subject_ref` without the
standalone UNIQUE. A subject holds one workspace board **and** one board per
project.

## 3. Migration — existing data preserved

A standalone UNIQUE table constraint cannot be dropped in SQLite, so
`_migrate_boards` rebuilds the table inside one transaction:

1. create `buyer_recon_boards_rebuilt` in the corrected shape;
2. `INSERT … SELECT` **every** row (no row added, dropped, or rewritten);
3. `DROP TABLE buyer_recon_boards`;
4. `ALTER TABLE … RENAME TO buyer_recon_boards` (with `PRAGMA legacy_alter_table=ON`
   so the `buyer_recon_entries` foreign key keeps pointing at this table by name);
5. create the composite unique index.

The migration is **detected, not assumed**: it sweeps `PRAGMA index_list` and
runs only when a UNIQUE index covers exactly `{subject_ref}`. A fresh (or
already-migrated) database is left untouched, so the guard is idempotent. The
`legacy_alter_table` pragma is restored to its prior value.

Measured on a legacy-shaped database built from the pre-fix DDL:

| Observation | Result |
|---|---|
| pre-existing board survives, same id | `legacy-b1` preserved |
| pre-existing entry survives (id, prospect, status) | preserved |
| `evidence_json` preserved | `[{"note": "kept"}]` |
| unverified default preserved | `buyer_price == "UNKNOWN"` |
| FK binding after rename | `buyer_recon_boards(id)` present, `PRAGMA foreign_key_check` empty |
| second board for the subject after migration | succeeds |
| re-open / module reload | idempotent, no rebuild, row counts unchanged |

## 4. Preserved invariants

* **Auth and owner scoping** — `require_auth` / `require_project_owner` unchanged;
  the router is byte-identical to `main` (`git diff main -- solspire/buyer_recon_router.py`
  is empty).
* **UNKNOWN / NONE defaults** — untouched; asserted in the regression tests and
  in the seeded read path.
* **Authority** — `execution_authority: NONE` / `budget_authority: NONE` unchanged.
* No broader auth, execution, budget, or authority change.

## 5. Regression tests + negative controls

* `tests/test_buyer_recon_board_contract.py` — **15 passed**. Fresh vs. legacy
  schema, migration data-preservation, FK integrity, idempotency, composite
  uniqueness, and the arity invariant.
* `tests/test_prism_opportunity_radar_module.py` — **20 passed**. The four former
  defect pins are re-pointed to the repaired contract (the module's own docstring
  instructed this).
* **Negative controls** (proven live):
  * the pre-fix bare `VALUES (?,?…×34)` statement still raises against the live
    table;
  * an unmigrated legacy database genuinely rejects a second board, and accepts it
    after the module touches it;
  * a duplicate composite scope is still rejected after the rebuild;
  * re-planting the two legacy defects in `buyer_recon.py` moves the two test files
    from **35 passed** to **12 failed / 23 passed** — the guards detect the exact
    defects they claim to. Restored byte-identically afterwards.

## 6. Projects-surface mount

`web/arkadia_console/src/components/opportunities/OpportunityRadarSection.tsx`
(WS2-owned) selects a project from the real `ProjectList` response and delegates
the read to the already-landed prop-driven `ProjectOpportunityRadar` via
`projectBoardPath(projectId)` — handler-derived, no invented route. It mounts in
`SolSpirePage.tsx` (the Projects surface, inventory Slice D — SolSpire / Radar),
only once the project list is `ready`, so a failed list read cannot be presented
as an empty opportunity board.

The surface resolves no transport of its own, exposes no execute/spend control,
and states an empty project list honestly. Shared registry/navigation integration
remains a Workstream 1 request (see the PR thread).

## 7. Build and suite

| Check | Command | Result |
|---|---|---|
| Console typecheck | `corepack pnpm exec tsc --noEmit` | exit 0 |
| Console build | `corepack pnpm build` | exit 0 — 70 modules, assets emitted |
| Targeted tests | `pytest tests/test_buyer_recon_board_contract.py tests/test_prism_opportunity_radar_module.py -q -rEf` | **35 passed** |
| CP10 admission | `scripts/cp10_mutation_boundary_policy.py --judge` on all six paths | PASS (exit 0) |
| Full suite — `main` `962434be` | `pytest tests/ -q -rEf --continue-on-collection-errors` | 19 failed / 2220 passed / 17 skipped / 1 error |
| Full suite — branch | same command | 19 failed / 2241 passed / 17 skipped / 1 error |

Failing/error **node set** is identical modulo one documented-intermittent node
(`tests/test_voice_pipeline.py::test_unsupported_executor_is_explicit_not_silent`,
which passes 3/3 in isolation), matching the repo's recorded instability of the
full-suite fingerprint. The `+21 passed` is the new tests.

The pre-existing `test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path`
failure (Workstream 4's `components/lab/LabSessionList.tsx`) is present on `main`
and is not repaired here.

## 8. Explicit non-claims

* No merge, no production deployment, no acceptance. Canonical production remains
  `https://arkadia-qzu4.onrender.com` (ADR-016).
* `solspire/buyer_recon_router.py` is unmodified.
* No shared file owned by another workstream was edited.

## 9. Defect 3 — board-scope isolation on the write routes (this pass)

Defect 2 gave one subject both a workspace board and one project board. Defect 3
is the write-side consequence, measured after Defect 2's repair:

```
workspace PATCH of a project-board entry: 200   (entry row notes -> 'MUTATED-FROM-WORKSPACE')
```

`PATCH /solspire/buyer-recon/entries/{id}` scoped `update_entry` by **subject
alone**, so an owner's workspace request reached an entry on one of their
*project* boards. The project route already enforced `entry.board_id == board.id`;
the workspace route did not. `SHARED-CONTRACTS.md` §1/§7.1 assigns
`solspire/buyer_recon_router.py` to WS2 for exactly this defect class, so
modifying it here supersedes §8's "unmodified" line.

The first cut compared boards *after* `update_entry` returned and raised
`KeyError`. Measured: status became `404` but the note **still landed** — the
manager had already committed inside its own transaction, so a post-write refusal
is a lie about the write. The repair moves the scope into the SQL:

* `BuyerReconManager.update_entry(..., board_id: str | None = None)` — the board
  id extends the `WHERE` clause of the pre-read, the `UPDATE`, and the re-select,
  all inside one `with _db()` transaction. Omitting it preserves the prior
  subject-wide behaviour for internal callers.
* Both router call sites (`update_buyer_recon_entry`,
  `update_project_buyer_recon_entry`) pass their own `board.id`.

### Measured outcomes (`/tmp/repro_scope.py`)

| Request | Expected | Observed |
|---|---|---|
| workspace PATCH of a project-board entry | 404, no mutation | 404, notes `''` |
| project PATCH of its own entry | 200 | 200 |
| workspace PATCH of a workspace-board entry (control) | 200 | 200, notes `'ws-ok'` |
| project PATCH of a workspace-board entry (control) | 404, no mutation | 404, notes `''` |

### Regression guard

`tests/test_buyer_recon_router_board_scope.py` (7 tests) asserts isolation on
**persisted state**, not on the response alone — the response was already a
`404` in the unsound first cut. Two same-board controls pass on both trees.
Proven to bite: on the pre-repair tree, 5 of the 7 fail; post-repair, 7 pass.

### Suite delta (this environment)

`pytest tests/ -q -rEf --continue-on-collection-errors`:

| Tree | Result |
|---|---|
| `main` `962434be` | 36 failed / 2190 passed / 30 skipped / 1 error |
| branch | 36 failed / 2218 passed / 30 skipped / 1 error |

The failing/error **node set** is byte-identical (`comm -3` empty, 37 nodes each).
Absolute counts differ from §7's recorded 19/2220 — that is a dependency delta
between runs of the same revision, not a regression; only the node set is
load-bearing.

## 10. Superseded in §8

`solspire/buyer_recon_router.py` **is** modified in this pass (board-scope
isolation, above), under the §7.1 ownership grant. The other §8 non-claims stand:
no merge, no deployment, no acceptance; canonical production remains
`https://arkadia-qzu4.onrender.com` (ADR-016).

