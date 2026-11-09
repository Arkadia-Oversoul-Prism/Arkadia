# Lane 2 — the buyer-recon schema detector had no negative control

**Lane:** 2 (NovaNet + project Opportunity Radar)
**Base:** `main` `327187d23c7e4ad32efc61aed91f912de084e07d` (re-fetched; unchanged through the pass)
**Owned paths changed:** `tests/test_buyer_recon_board_contract.py`, this record
**Console source, backend contract, registry and other lanes' files:** untouched.

## The defect

`tests/test_buyer_recon_board_contract.py` decides the migration's central
property by reading SQLite's unique-index scopes:

```python
def _unique_index_column_sets(db):
    ...
    if row["unique"]:
        sets.append({r[2] for r in conn.execute(f"PRAGMA index_info({row['name']!r})")})
```

Three live assertions read it (`test_unique_scope_is_the_composite_not_the_subject`,
`test_migration_removes_the_subject_only_constraint`, plus two idempotence nodes),
and the file's own docstring states *"Negative controls accompany each detector."*
**None accompanied this one.** The three `test_negative_control_*` nodes in the file
prove the arity, the composite uniqueness and the migration — each by executing a
real SQL statement against a real database — but nothing proved the *schema oracle*
itself.

A negative control that restates a detector inline cannot fail for an edit to the
detector. That is the vacuous-control class this lane already repaired twice
(`#635`, `#640`) and lane 1 repaired in `#631`/`#634`.

## Measured — the detector is disarmable, and silently

The probe replaces the helper's body with a hardcoded answer that never reads the
database (the file is restored byte-identically afterwards; `sha256` re-checked).

| Tree | Probe | Result |
|---|---|---|
| `main` `327187d2` (pre-repair file) | helper → `return [{"workspace_ref","subject_ref"}]` | **15 passed** — the disarm is invisible |
| repaired file | helper → same hardcoded answer | **1 failed**, 15 passed — `test_negative_control_the_scope_detector_flags_the_pre_migration_schema` |

A plausible non-adversarial edit reproduces it: dropping the `if row["unique"]:`
filter (inspecting every index rather than the unique ones) also left the
pre-repair file at **15 passed**.

The failure mode matters because the *shape* of the assertion is what makes it
disarmable: `{"workspace_ref","subject_ref"} in sets` and `{"subject_ref"} not in
sets` are two membership tests over a value the helper produces, so a helper that
returns a constant satisfies both. The pre-migration legacy schema and the
post-migration schema are distinguishable only by actually reading the database —
measured at `327187d2`:

```
PRE-migration legacy: [{'subject_ref'}, {'workspace_ref'}, {'id'}]
POST-migration      : [{'subject_ref', 'workspace_ref'}, {'id'}]
```

## The repair

The two halves move into one module-level predicate that the live assertions and
the new control both call, so the control can fail for an edit to the detector it
protects:

```python
LEGACY_UNIQUE_SCOPE   = frozenset({"subject_ref"})
MIGRATED_UNIQUE_SCOPE = frozenset({"workspace_ref", "subject_ref"})

def _scope_defects(unique_sets) -> list[str]:
    present = [set(scope) for scope in unique_sets]
    problems = []
    if set(MIGRATED_UNIQUE_SCOPE) not in present: problems.append("...composite...missing")
    if set(LEGACY_UNIQUE_SCOPE)   in present:    problems.append("...subject-only...present")
    return problems
```

Both polarities are reported, so a predicate that matched nothing *or* everything
fails one half. The live assertions call it on the fresh and the migrated schema;
the control calls it on the **pre-migration** legacy schema and asserts the
repaired one is not reported.

**Node count:** 15 → 16 in this file (`--collect-only`, measured). A strengthening
plus one control, not a rewrite of the file.

## Proof the control is not vacuous

Two polarity controls on the real file, each scoped to the shared definition so
every call site is affected:

| Probe | Live nodes | Control |
|---|---|---|
| shared predicate body → `return []` | pass | **FAIL** |
| shared helper → hardcoded answer | pass | **FAIL** |

Both redden the control; both leave the live nodes passing, which is exactly the
defect: the live nodes never measured the helper.

## Proof the repaired suite still catches the real defect

Breaking the production migration (`solspire/buyer_recon.py`, composite index →
subject-only) against the **repaired** test file:

```
6 failed, 10 passed
FAILED ...::test_fresh_database_allows_workspace_and_project_boards
FAILED ...::test_unique_scope_is_the_composite_not_the_subject
FAILED ...::test_migration_removes_the_subject_only_constraint
FAILED ...::test_negative_control_the_scope_detector_flags_the_pre_migration_schema
FAILED ...::test_migration_lets_a_legacy_subject_gain_a_project_board
FAILED ...::test_negative_control_an_unmigrated_legacy_db_really_does_reject_a_second_board
```

So the repair strengthens the guard without weakening its teeth.
`solspire/buyer_recon.py` was restored byte-identically (`git status` clean for it).

## Verification

| Command | Result |
|---|---|
| `pytest tests/test_buyer_recon_board_contract.py -q -rEf` | **16 passed** |
| Lane-2 suites (9 files) | **185 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `--collect-only` on the changed file, `main` vs branch | 15 → 16 (+1, the new control) |
| `python scripts/cp10_mutation_boundary_policy.py --judge` on the changed path | **PASS** |
| `git diff --name-only` | lane-2 owned files only |

**Baseline (measured this pulse, `main` `327187d2`, one full run):**
`21 failed, 4009 passed, 18 skipped, 3 warnings, 1 error in 278.42s`.
Canonical fingerprint re-derived from that log with the repository's own script
(`python scripts/baseline_fingerprint.py /tmp/baseline_main.log --json`):

```
nodes                : 22
outcomes_fingerprint : af4ad19a53dbe0edc5dfe577bce8ebdfc147fdfd888cb394dfb027b56232b741
ids_fingerprint      : 0b1386284e944593dbb10ff8b85b7507cb3bea4f1d185f8eab78f84ca1236448
```

The `8dd24bbbe2062c44f434ad872b896e3557fdce1413a6b556f2e9836cc6d293d3` value carried
into this pass from the prior pulse's notes **does not reproduce** and is superseded
by the derivation above. It was inherited, not measured here; the counts matched, so
the discrepancy was invisible until the log was re-hashed. A fingerprint is only
usable if an independent operator can re-derive it — cite the derivation, not the
remembered value.

No full-suite re-run after the change: the change touches one test file that
appears in no derived gate domain and adds no failing node, so the node set cannot
move. Attribution is by `--collect-only`, not by a second full run.

## Scope and boundaries

- No console source, backend contract, registry, shared type, or other lane's file.
- No authority, identity, K15/K3, approval-enforcement or deployment surface.
- No endpoint, route or surface declared or changed.
- No merge, deployment or acceptance claim: merge remains Weaver's (GOV-01 §9) or
  the human sovereign's act. OpenHands holds no merge authority.
