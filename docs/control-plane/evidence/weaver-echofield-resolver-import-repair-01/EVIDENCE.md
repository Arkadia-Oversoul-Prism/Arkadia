# Weaver Echofield Resolver Import Repair — EVIDENCE

Bounded workstream: `gate-hygiene/weaver-echofield-resolver-import-repair-01`
Base: `main` @ `357fbd83001924e909979fbaebdedbd991a2aadb` (`Merge pull request #244`)
Branch head: see PR.
Classification: **VERIFIED** (repository evidence; no runtime/production claim).

## 1. Defect (measured, not inferred)

`weaver/echofield/resolver.py` annotated both `ConflictResolver` methods with `Dict`
without importing it:

```
$ python -c "import weaver.echofield.resolver"
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
```

`pyflakes` reported `undefined name 'Dict'` at lines 25, 26, 68. The failure is
**import-time only** — `python -m py_compile weaver/echofield/resolver.py` passes, so a
byte-compile gate cannot see it (same defect class as the P1-A boot break, at module scope).

`weaver/echofield/__init__.py` declares `resolver.py` as part of the package
("resolver.py: Conflict resolution engine"). Six of the seven declared modules imported
cleanly; `resolver` did not:

```
node           OK
vector_stack   OK
edge           OK
field          OK
decay          OK
retrieval      OK
resolver       NameError: name 'Dict' is not defined.
```

No production consumer imports the module today (the only in-repo reference outside the
package is the `__init__.py` docstring), so this is a latent correctness defect rather
than an active outage. It is repaired because the module is a declared, tested package
surface, not because a consumer is currently broken.

## 2. Change (allowed paths only)

| path | change |
|---|---|
| `weaver/echofield/resolver.py` | +1 line: `from typing import Dict, Optional, Tuple` |
| `tests/test_echofield_core.py` | +6 behavioral tests + 1 package-import invariant |
| `docs/control-plane/evidence/weaver-echofield-resolver-import-repair-01/EVIDENCE.md` | this record |

No other path touched. `Tuple` remains in the import list (pre-existing unused import,
left as-is — not this defect).

## 3. Verification (run on this tree)

| check | command | result |
|---|---|---|
| import | `python -c "import weaver.echofield.resolver"` | OK (was NameError) |
| pyflakes (module) | `python -m pyflakes weaver/echofield/resolver.py` | only the pre-existing `Tuple` unused notice |
| echofield suite | `pytest tests/test_echofield_core.py -q` | **13 passed** (was 7) |
| boot compile | `python -m py_compile api/main.py` | OK, 2582 / 2600 lines |
| architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| CP10 gate integrity | `pytest tests/test_m02a_ci_gate_integrity.py -q` | **55 passed** |
| fingerprint guard | `pytest tests/test_baseline_fingerprint.py -q` | **19 passed** |
| CP10 judge (corpus) | `git ls-files \| python scripts/cp10_mutation_boundary_policy.py --judge` | RC 0, PASS |
| CP10 judge (diff) | `git diff --name-only \| … --judge` | RC 0, PASS |

## 4. Negative control

The repair is one line; reverting it must redden the new tests, or the suite would pass
vacuously:

```
$ git stash push -- weaver/echofield/resolver.py     # revert only the fix
$ pytest tests/test_echofield_core.py -q
6 failed, 7 passed
```

The 6 new resolver tests fail without the import and pass with it. The import-invariant
test is written lazily (`importlib.import_module` inside the function) so a regression
fails that node instead of erroring the whole file at collection.

## 5. Baseline comparison (node-set, not counts)

Counts are order-dependent in this repo
(`test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
snapshots global `git status`), so attribution uses the sorted failing/error **node set**.

| tree | result |
|---|---|
| `main` @ `357fbd8` (repair stashed) | 23 failed / **1368** passed / 19 skipped / 1 error — 24 nodes |
| branch | 23 failed / **1374** passed / 19 skipped / 1 error — 24 nodes |

`diff` of the two node sets: **identical**. The `+6 passed` is exactly the six new tests.
**Zero new failing nodes; zero repaired baseline nodes.** `weaver/echofield` appears in
neither `tests/fixtures/baseline_node_set.txt` nor `tests/fixtures/superseded_baseline_node_set.txt`,
so this repair cannot move the canonical fingerprint.

## 6. Authority boundary

Repository-source change only. No merge, no push to `main`, no authority-path change, no
production or runtime claim. The four pre-existing HTTP-boundary failures are **not**
touched — resolving them encodes an authority-model decision reserved to the sovereign.
Human merges.
