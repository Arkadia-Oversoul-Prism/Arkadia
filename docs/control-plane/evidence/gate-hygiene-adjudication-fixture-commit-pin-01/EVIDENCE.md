# The gate-2 adjudication fixture must come from a pinned revision, not `origin/main`

**Workstream:** `gate-hygiene` / GATE-2 trajectory
**Bounded question:** `tests/test_agents_md_encoding_adjudication.py::test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`
asserts `healed.startswith(_rev("AGENTS.md", "origin/main"))`. On current `main` it fails
(`got False`) while the audit itself is correct. Why, and what is the minimal repair?
**Classification:** `IMPLEMENTED` (repository-layer, test-side fixture pin).
**Base:** `main` @ `162f574b05dd839540d803aadda7608342618a84`
**Branch:** `gate-hygiene/adjudication-fixture-commit-pin-01`

---

## 1. Answer

`origin/main` no longer carries the mojibake. The repair landed at `2365a89`, an ancestor of
current `main`, so `_rev("AGENTS.md", "origin/main")` returns a **clean** file. `heal_shadow`
(the outer CP775 undo) reproduces the corrupt text the file grew from — a superset prefix of
every corrupt revision, but **not** a prefix of a clean file. Therefore
`healed.startswith(clean_main)` is `False` and the test fails.

The premise "`origin/main` is corrupted" expires with the very repair this instrument exists to
guard. The sibling node in the same file (`test_exit_code_does_not_call_a_divergent_clean_file_verified`)
has the identical moving-branch defect and is repaired by PR #217; this pass repairs the
remaining node so the file's fixtures are uniformly pinned to immutable revisions.

## 2. Measurements (all on base `162f574b`)

```
git merge-base --is-ancestor 2365a89 origin/main   YES   (repair is an ancestor of main)
origin/main AGENTS.md            Cyrillic 0     (clean)
002b189 (2365a89^, last corrupt) Cyrillic 182   bytes 27017
e0dde9ad9c5e (first corrupt)     Cyrillic 182   bytes 16543

heal_shadow(AGENTS.md @ 7d79f38)  changed=110   Cyrillic 182   bytes 34865
  .startswith(origin/main AGENTS.md)          False   <- the failure
  .startswith(AGENTS.md @ e0dde9ad9c5e)       True
  .startswith(AGENTS.md @ 002b189)            True
```

The healed text is an append-only descendant of the corrupt lineage, so it is a **superset
prefix** of both the first and the last corrupt revision — which is why either pinned revision
is a valid target and the moving branch is not.

## 3. Change

One test, one edit: the reference becomes the immutable first-corrupt revision
(`CORRUPTION_COMMIT = e0dde9ad9c5e`, already imported into the test file), with a loud skip if
that revision is absent from the clone rather than an opaque `False`.

```python
corrupted_main = _rev("AGENTS.md", CORRUPTION_COMMIT)
if corrupted_main is None or cyrillic_count(corrupted_main) == 0:
    pytest.skip(f"pinned corrupt revision {CORRUPTION_COMMIT} unavailable in this clone")
healed, changed = heal_shadow(text)
assert changed > 0
assert healed.startswith(corrupted_main), "the cp775 undo restores the pinned corrupt bytes"
assert cyrillic_count(healed) == cyrillic_count(corrupted_main), (...)
```

No instrument logic, no evidence document, and no fingerprint record is touched.

## 4. Evidence

```
tests/test_agents_md_encoding_adjudication.py -q   1 failed, 20 passed, 2 skipped
  FAILED test_exit_code_does_not_call_a_divergent_clean_file_verified
```

The single remaining failure is the **recorded baseline node** and is repaired by PR #217
(`gate-hygiene/live-file-fixture-revision-pin-01`). This pass is the orthogonal remainder:
node `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` moves
FAILED → PASS. With both PRs applied, the file would report 21 passed / 2 skipped.

## 5. Relationship to the other gate-hygiene PRs

- **#215** (`baseline-node-depth-stability-01`) — touches this same file
  (`test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`, ~line 361) with a
  non-overlapping hunk; auto-merges clean. Does not touch this node.
- **#216** (`superseded-fingerprint-origin-01`) — edits `tests/test_baseline_fingerprint.py`
  and docs. Different file; no conflict.
- **#217** (`live-file-fixture-revision-pin-01`) — repairs the *sibling* node. Same file, but
  non-overlapping hunk and different assertion. Git-clean; semantically complementary.
- Composed tree (#215 + #217 + this PR) merges cleanly and yields
  `tests/test_agents_md_encoding_adjudication.py -q` → **21 passed, 2 skipped, 0 failed**.

This pass deliberately does not duplicate #217's repair, edit the sibling hunk, or touch any
fingerprint record. It completes the file's fixture pinning for the node no open PR covers.

## 6. Residual uncertainty / blocked

- Production/runtime parity (GATE-2) remains `BLOCKED` on provider auth for the deployment URL
  — unchanged by this repository-layer change.
- The full-suite fingerprint is unstable on `main` (cross-test contamination in
  `test_engineering_lab_agent_loop`), so attribution here is by failing-node *name*, not count.

## Authorization

Human review/merge only. No merge performed. No consequential external action.
