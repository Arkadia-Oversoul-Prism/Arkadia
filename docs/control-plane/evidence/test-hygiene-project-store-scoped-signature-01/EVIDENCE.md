# Test hygiene — the project-file store's tests call a superseded signature

**Date:** 2026-11-22
**Base:** `main` @ `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Branch:** `test-hygiene/project-store-scoped-signature-01`
**Authority:** bounded test repair. No production code, route, authority, or deployment change.

## 1. Defect

Two tests called `solspire/project_store.py` with its pre-scoping signatures, so they
failed with `TypeError` before asserting anything:

```
tests/test_m05_files.py:45:      ps.update_file(f["id"], "x", name="b.txt")
  TypeError: update_file() missing 1 required positional argument: 'content'

tests/test_m01_persistence.py:208:  store_mod.delete_file(a["id"])
  TypeError: delete_file() missing 1 required positional argument: 'file_id'
```

The store is project-scoped (`solspire/project_store.py:283,356`):

```python
def update_file(project_id: str, file_id: str, content: str, name: str | None = None) -> dict
def delete_file(project_id: str, file_id: str) -> bool
```

Both call sites pass the file id in the `project_id` position, so the assertions never
ran. This is the repository's documented recurring class — a test pinned to a shape the
source no longer has — and the direction matters: the **source is the stricter** contract
(project-scoped), so the repair belongs in the tests, not in the store.

Only two call sites existed in the whole test tree:

```
$ grep -rn "update_file(\|delete_file(" tests/
tests/test_m01_persistence.py:208:    store_mod.delete_file(a["id"])
tests/test_m05_files.py:45:    ps.update_file(f["id"], "x", name="b.txt")
```

## 2. Change

`tests/test_m05_files.py` — pass the owning project, and pin the scoping it relies on:

```python
f = ps.create_file("p2", "a.txt", "x")
ps.update_file("p2", f["id"], "x", name="b.txt")
got = ps.get_file(f["id"])
assert got and got["name"] == "b.txt"
# `update_file` is project-scoped: the wrong project id must not rename it.
assert ps.update_file("other", f["id"], "x", name="c.txt") == {"ok": False, "error": "File not found"}
assert ps.get_file(f["id"])["name"] == "b.txt"
```

`tests/test_m01_persistence.py` — delete under the owning project, after proving a
foreign project id cannot:

```python
assert store_mod.delete_file("other-project", a["id"]) is False
assert any(c["row"]["id"] == a["id"] for c in _corpus()["children"])
assert store_mod.delete_file(seeded["pid"], a["id"]) is True
assert not any(c["row"]["id"] == a["id"] for c in _corpus()["children"])
```

The added assertions are deliberate: re-pointing a stale call is not the same as proving
the boundary it now crosses. Without them the repair would be indistinguishable from
silently dropping the project argument.

## 3. Negative control (live, on the real source)

Project scoping removed from `solspire/project_store.py` in the working tree — both
`WHERE` clauses reduced to `id=?` — and the two nodes re-run:

```
2 failed in 0.59s
FAILED tests/test_m05_files.py::test_update_file_supports_rename
FAILED tests/test_m01_persistence.py::test_deletion_propagates_to_durable_corpus
E  assert True = delete_file('other-project', '95137681-…')
```

The source file was then restored byte-identically (`git diff --stat solspire/project_store.py`
→ empty). The new assertions therefore detect the loss of project scoping rather than
passing unconditionally.

## 4. Verification

Environment: Python 3.13, `pyyaml`, `pytest` 9.2, `pytest-asyncio`, `pyjwt`,
`google-generativeai`, `fastapi`/`httpx`/`requests`/`pydantic` installed;
`PYTHONPATH=<repo>/archive/legacy_python`; `-p no:randomly`.

| Tree | Command | Result |
|---|---|---|
| `main` `034d8879` | `python -m pytest tests/ -q -rEf --continue-on-collection-errors -p no:randomly` | **9 failed, 4241 passed, 38 skipped, 1 error** (10 nodes) |
| branch (this change) | same | **7 failed, 4243 passed, 38 skipped, 1 error** (8 nodes) |

Failing/error **node sets** (`comm -3` shows only the two repaired nodes):

```
FAILED tests/test_m01_persistence.py::test_deletion_propagates_to_durable_corpus
FAILED tests/test_m05_files.py::test_update_file_supports_rename - TypeError:...
```

- `main` node set sha256: `076b178e5f51facc5301fe819631d2d7adaad9fdfd7c3250304c9073760fc6b8`
- branch node set sha256: `9c330fedd223edc7dc5219d8cad77b76ef910c0bb396e0772eb06bddebfeb4f1`

Zero new failing nodes; `+2 passed` is exactly the two repaired nodes. Architecture suite:
**11 passed**. `tests/test_m05_files.py tests/test_m01_persistence.py` together: **18 passed**.

The eight nodes that remain red on the branch are pre-existing on `main` and are **not**
repaired here:

| Node | Classification |
|---|---|
| `ERROR tests/test_autonomy.py` | CE-01 `weaver.autonomy` module-vs-package collision — sovereign-reserved |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | deliberately left failing pending a sovereign persistence-boundary decision (documented in `gate-hygiene-baseline-stale-assertion-repair-living-gate-06`) |
| `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | unowned drift |
| `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | unowned drift — see §5 |
| `test_solspire_r1_governance_convergence.py` (2) | unowned drift |
| `test_solspire_r3_execution_runtime.py` (1) | unowned drift |
| `test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` | order-dependent under the full suite; passes in isolation (recorded class) |

## 5. Recorded, not repaired (out of scope)

`tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key`
requires the literal `arkanaSessionId` in the archived
`archive/frontend/arkadia-prism/web/public_prism/src/components/ArkanaCommune.tsx`. The
component imports `createArkanaThreadId` from `../lib/arkanaSession` and keys its thread on
a persisted per-context `activeThreadId`; it never calls the exported
`arkanaSessionId()` (`lib/arkanaSession.ts:42`). So this is not a near-miss literal — the
shared-session property the test asserts is genuinely absent from that surface.

Repairing it changes the Oracle conversation key, which is the Arkana/Oracle surface
owned by lane 4 (`SHARED-CONTRACTS.md` §1) and is an architectural decision about thread
identity, not test hygiene. It is recorded as a separate proposed workstream.

## 6. Non-claims

- No merge, deployment, production change, or acceptance is claimed.
- The two repaired nodes are asserted green in this environment; CI confirmation is a
  separate observation.
- Nothing here changes `solspire/project_store.py`, any route, or any authority boundary.
