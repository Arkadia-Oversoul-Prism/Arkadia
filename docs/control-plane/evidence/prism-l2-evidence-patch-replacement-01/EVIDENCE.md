# LANE 2 — `update_entry` silently drops an `evidence` patch

Bounded objective: repair `BuyerReconManager.update_entry` so that a PATCH which
supplies `evidence` replaces the stored list, and a PATCH which omits it leaves the
stored list untouched.

Base revision: `1a36f23536c6387dc7e460888f4637d2bfb94759` (PR #538 head, Lane-2
`prism-l2-buyer-recon-status-normalization-01`). PR #538 repaired DEFECT 3 (status
normalization) in this same function and left `evidence` in the broken state
recorded here.

## 1. The defect

`update_entry` builds a generic `UPDATE` from the `current` row plus the caller's
`patch`. `evidence` is the one entry field whose **column name differs**
(`evidence` in the dataclass, `evidence_json` in SQLite) and whose value is a
**list**, so the generic `current[key] = str(value)` loop cannot carry it. The
pre-repair code therefore had two separate paths for it:

```python
if "evidence" in normalized:
    current["evidence_json"] = json.dumps(normalized["evidence"] or [])   # dead: no such key
...
if dbkey == "evidence_json":
    value = json.dumps(current.get("evidence") or patch.get("evidence") or [])
```

The first line writes `current["evidence_json"]`, but the row read back by
`_entry`-shaped `SELECT *` exposes `evidence`, not `evidence_json` — so the key
never exists and that branch **cannot** take effect. The second line falls back to
`current.get("evidence")` **first**, and the stored list is truthy whenever the
entry has any evidence, so the patch's list is never reached.

Net effect: a PATCH that supplied `evidence` was silently ignored whenever the
stored list was non-empty. The caller received `200` and a response body echoing
the **old** list — a write that reports success and does not happen.

Note that the first line is present in PR #538's diff. It is dead code in that
diff, not a repair; #538's tests do not cover an `evidence` PATCH.

## 2. Measurement (pre-repair, at the base revision)

Probe against a temp `SOLSPIRE_DATA_DIR` with `br._DB_PATH` patched:

```
A stored-nonempty patch: [{'ref': 'old'}]     # patch [{'ref': 'new'}] DROPPED
B stored-empty patch:    [{'ref': 'fresh'}]   # only the empty case worked
```

Case A is the defect. Case B is why a naive test can miss it: the write path
happens to work when the stored list is empty, so a single "patch the evidence"
test on a fresh entry passes while the defect stands.

## 3. Repair

```python
# `current` carries the *stored* list, so presence must be tracked separately:
# deriving it from `current` lets the stored list outrank the patch.
evidence_supplied = "evidence" in normalized
...
if evidence_supplied:
    current["evidence"] = list(normalized["evidence"] or [])
...
if dbkey == "evidence_json":
    value = json.dumps(current.get("evidence") or [])
```

Three properties, all asserted:

- **replace** — `evidence` in the patch replaces the stored list;
- **preserve** — `evidence` absent from the patch leaves the stored list alone
  (the `current` row already carries it; nothing rewrites it);
- **clear** — an explicit `[]` clears the list, distinct from omitting the field.

`evidence` is popped from the generic loop by the existing `allowed` filter, so the
repair does not widen the writable field set.

## 4. Proof

New tests in `tests/test_prism_opportunity_entry_flow.py`:

| test | property |
|---|---|
| `test_edit_replaces_stored_evidence_when_the_patch_supplies_it` | replace (the defect) |
| `test_edit_populates_evidence_on_an_entry_that_had_none` | populate |
| `test_edit_that_omits_evidence_preserves_the_stored_list` | **negative control** |
| `test_edit_can_clear_evidence_with_an_explicit_empty_list` | clear |
| `test_an_evidence_edit_cannot_reach_another_projects_board` | board scope on the evidence column |

Targeted run (lane-2 files, post-repair): **102 passed**.

Live negative controls, each mutating the real source and restoring byte-identically:

- revert `solspire/buyer_recon.py` to the base revision -> **2 failed, 53 passed**
  (`test_edit_replaces_stored_evidence_when_the_patch_supplies_it`,
  `test_edit_can_clear_evidence_with_an_explicit_empty_list`). The repair's absence
  is detected.
- over-eager variant, `json.dumps(normalized.get("evidence") or [])` in the loop
  (unconditional rewrite) -> **1 failed, 54 passed**
  (`test_edit_that_omits_evidence_preserves_the_stored_list`). A repair that fixes
  replacement by wiping every other entry's evidence is detected.

Both directions bite, so neither the defect nor its over-correction can pass.

## 5. Regression boundary

- `python -m pytest tests/architecture -q` -> **11 passed**.
- `python -m py_compile solspire/buyer_recon.py solspire/buyer_recon_router.py api/main.py` -> OK.
- `api/main.py` untouched; line budget unaffected.
- Field set written by `update_entry` unchanged (`allowed` filter untouched).

## 6. Not repaired here (separate bounded workstream)

`evidence_status` remains **unvalidated**: `update_entry` accepts an arbitrary
string, and a probe stored `TOTALLY_BOGUS` with no error. `create_entry` is
likewise permissive. A validation rule needs a vocabulary decision — the backend
defines none (`grep EVIDENCE_STATUS solspire/buyer_recon.py` -> no constant) while
the frontend uses `NONE` as a sentinel (`opportunityRadarContract.ts:62`) and the
schema default is `'NONE'`. Choosing that vocabulary changes the write contract, so
it is recorded and proposed, not executed under this slice.

## 7. Authority

Human sovereign retains merge, production deployment, and acceptance. This slice is
repository-source evidence only; no runtime or production claim is made.
