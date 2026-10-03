# The live-file adjudication fixture must come from an immutable revision, not `origin/main`

**Workstream:** `gate-hygiene` / GATE-2 trajectory
**Bounded question:** `tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified`
reads a corrupted fixture from `origin/main` when the working tree is clean, and asserts
`exit_code(audit(corrupted, oracle)) == 0`. On current `main` that test fails; the audit is
correct, the fixture is not. Why, and what is the minimal repair?
**Classification:** `IMPLEMENTED` (repository-layer, test-side fixture pin).
**Base:** `main` @ `162f574b05dd839540d803aadda7608342618a84`
**Branch:** `gate-hygiene/live-file-fixture-revision-pin-01`

---

## 1. Answer

The test's fallback fixture is `_rev("AGENTS.md", "origin/main")` — a **moving branch**. That
was sound when the test was written: `main` still carried the CP866 mojibake and was the
canonical corrupt sample. The repair then landed (`2365a89`, ancestor of current `main`), so
`origin/main`'s `AGENTS.md` is now **clean**. A clean file has nothing to recover, so
`audit()` reports `oracle_reproduced=True` with `decidable=False` and `exit_code()` returns
**1**, not the asserted **0**.

The premise "`origin/main` is corrupted" expires with the very repair this instrument exists
to guard. The repair is to read the fixture from the **pinned revision that carried the
corruption** (`CORRUPTION_COMMIT`, already imported into the test), while still preferring the
working tree when it is itself corrupted.

## 2. Measurements (all on base `162f574b`)

```
origin/main AGENTS.md  Cyrillic codepoints  0     (repaired)
                       lines                670
git merge-base --is-ancestor 2365a89 origin/main   YES   (repair is an ancestor)
working tree AGENTS.md Cyrillic codepoints  0

audit(origin/main AGENTS.md, oracle)
  cyrillic_before=0  corrupted_lines=0  oracle_reproduced=True  decidable=False  -> exit 1
```

The failure is therefore **test-side**, not an audit defect: the audit correctly refuses to
call a clean-but-otherwise-unverifiable file a *repair*.

## 3. The pinned fixture is a valid corrupt sample

`CORRUPTION_COMMIT = e0dde9ad9c5e` (first revision whose `AGENTS.md` carried the mojibake),
already exported by the instrument and already imported by this test file:

```
AGENTS.md @ e0dde9ad9c5e  Cyrillic codepoints  182
audit(corrupt, oracle)     exit 0  decidable=True  oracle_reproduced=True  alterations=0
```

That is exactly the input the assertion requires — a genuinely corrupted file whose recovery
is decidable and corroborated by the oracle. It is immutable, so it survives every future
change to `main`.

## 4. Change

One test, one edit: the fallback becomes the pinned revision, and a clean guard fails loudly
if neither the tree nor the pinned revision can supply a corrupt sample (rather than silently
asserting `1 == 0` — the current, opaque failure mode).

```python
live = AGENTS_MD.read_text(encoding="utf-8")
corrupted = live if cyrillic_count(live) else _rev("AGENTS.md", CORRUPTION_COMMIT)
assert corrupted is not None and cyrillic_count(corrupted) > 0, (...)
assert exit_code(audit(corrupted, oracle)) == 0
```

No instrument logic, no evidence document, and no fingerprint record is touched.

## 5. Regression boundary — node-set delta, not counts

Full suite, base vs. branch (bare clone; `pytest tests/ -q
--continue-on-collection-errors`, `PYTHONPATH=archive/legacy_python`):

```
base   19 failed, 1306 passed, 19 skipped, 1 error
branch 19 failed, 1306 passed, 18 skipped, 1 error   (skips: 19 -> 18 — see below)
```

| | node |
|---|---|
| removed by this change | `FAILED tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified` |
| added by this change | `FAILED tests/test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` |

Exactly one replacement, and no unexplained node appears. The added node is the
**clone-depth-dependent sibling** already documented in PR #216's
`CLONE_DEPENDENT_SIBLING_NODE`: in a bare clone it dereferences an absent `GATE2_PARENT_REV`
and reports `AttributeError` instead of skipping. It is a pre-existing clone-artifact, not
produced by this change, and it disappears in any clone carrying that revision (or once
PR #215's guard merges). The canonical **recorded** baseline node set is a fixed fixture on
disk and is unaffected, so the published fingerprints do not change.

The target test passes in isolation after the change; `_rev` returns `None` for an
unavailable revision, so the pinned path degrades to the explicit guard rather than a crash.

## 6. Relationship to open PRs (no duplication, no merge-order coupling)

- **PR #215** (`gate-hygiene/baseline-node-depth-stability-01`) guards the *other* file
  `test_shadow_…` against the same absent-revision crash. This change is complementary: it
  fixes the depth-*stable/moving-branch* defect in a *different* test. Together they turn the
  bare-clone `AttributeError` crash into a clean skip — independent, order-free, no shared
  lines.
- **PR #216** (`gate-hygiene/superseded-fingerprint-origin-01`) owns the recorded-baseline
  and fingerprint documents. This change deliberately does **not** touch them; the recorded
  fixture (`tests/fixtures/baseline_node_set.txt`) is unchanged, so #216's fingerprints stay
  valid. This branch does not depend on either PR.

## 7. Remaining uncertainty

- The 18 other pre-existing failures and the `tests/test_autonomy.py` collection error are
  baseline debt, unchanged by this pass, and are not addressed here.
- This is a repository-layer verdict (`IMPLEMENTED`). It carries no production/runtime claim.
