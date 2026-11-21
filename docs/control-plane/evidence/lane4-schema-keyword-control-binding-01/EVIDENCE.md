# EVIDENCE — lane 4: bind the schema-keyword extractor to a control

**Pulse:** Weaver hourly bounded execution, 2026-11-20T14:22Z
**Base:** `main` `4b91c2f416a104589283c3846a0766e252a08900` (PR #670)
**Branch:** `lane4/schema-keyword-coverage-control-binding-01`
**Lane:** 4 (Arkana / Weaver / Engineering Lab)
**Owned paths touched:** `tests/test_arkana_signal_schema_guard.py` (lane-4 owned: Arkana
feature tests), this evidence record.
**Disposition:** IMPLEMENTED. Merge execution is human-only (GOV-03); this PR stays draft.

---

## 1. Defect — a generator's silent-pass direction made a coverage guard vacuous

`test_the_stdlib_validator_covers_every_keyword_the_schema_uses` exists to stop a
schema rewrite from introducing a keyword the stdlib validator silently ignores. Its
own failure message names the failure mode it guards against: *"extend the validator or
the pin would pass vacuously"*.

It decides that question through one helper:

```python
used = set(_iter_schema_keywords(_load_schema()))
unsupported = used - _SUPPORTED_KEYWORDS
assert not unsupported, ...
```

`_iter_schema_keywords` is a **generator**. A body that yields nothing makes `used`
the empty set, `unsupported` the empty set, and the assertion **pass**. The node then
reports success while judging no keyword at all — the vacuity it is named to prevent,
one level down: the node could be disarmed by disarming its extractor.

Measured by replacing the body of `_iter_schema_keywords` with `return []`:

```
on this branch (control present):   13 passed, 1 failed   <-- the new control reddens
on `main` `4b91c2f4` (pre-PR):      13 passed             <-- the coverage node still passes
```

The module collects **13** nodes on `main` `4b91c2f4` and **14** on this branch
(`--collect-only`, measured 2026-11-21). In both runs the coverage node
`test_the_stdlib_validator_covers_every_keyword_the_schema_uses` still passes with a dead
extractor, so the module had **zero** nodes that called the extractor in a way that would
notice. The single node that notices now is the control this PR adds.

**Correction — supersedes the first draft of this section.** It read `14 passed` for the
branch mutation and `11 passed` for the pre-PR measurement. Both were wrong: `14` is this
branch's node *count*, not its pass count — the mutation fails one node on this branch —
and the pre-PR module collects 13 nodes, not 11. The PR body's left-hand column carried
the same `11` and is corrected with it. The substantive claim is unchanged and is
re-measured above.

### Why the existing controls could not catch it

The module is otherwise well controlled — four negative controls on the *validator* and
a positive control, plus `test_guard_does_not_import_jsonschema`. Every one of them
exercises `_validate`, never `_iter_schema_keywords`. A control that binds one helper
cannot bind its neighbour, and the uncovered helper was the one whose failure mode is
silent.

## 2. Repair

One new test, `test_the_keyword_extractor_is_bound_in_both_polarities`, plus a docstring
on the helper recording the measured defect so the next reader does not delete the
control as redundant.

- **Positive polarity** — the extractor must report a non-trivial set, must reach a
  nested keyword, and must descend into `$defs`. This is the silent-pass direction: a
  dead extractor is now reported rather than absorbed.
- **Negative polarity** — a property *name* under `properties` must **not** be reported
  as a keyword. This binds the `properties`/`$defs` name-map special case, whose removal
  would otherwise only surface as a false alarm in the coverage node.
- **Live schema** — the real schema must report at least five keywords and they must all
  be inside `_SUPPORTED_KEYWORDS`, so the control is bound to the artifact the coverage
  node actually reads rather than only to a synthetic dict.

Both polarities are asserted in one node because they are two halves of one property: an
extractor that is dead and an extractor that over-reports are the two ways this helper
can stop being a keyword extractor.

## 3. Verification

```
tests/test_arkana_signal_schema_guard.py   14 passed   (was 13; +1 new control)
--collect-only                             14 collected
```

### The control bites, measured against the pre-repair shape

| Mutation of `_iter_schema_keywords` | Result | Reading |
|---|---|---|
| body → `return []` (dead extractor) | **1 failed, 13 passed** | the new node reports it; the coverage node alone passes vacuously |
| `properties`/`$defs` name-map case removed (over-eager) | **2 failed, 12 passed** | both the new node and the coverage node report it |
| restored byte-identically | **14 passed** | |

The first row is the load-bearing one: it is the shape that passed on `main`.

### Regression boundary

No file outside `tests/test_arkana_signal_schema_guard.py` and this record is touched.
No source, schema, route, authority, identity, or governance surface changes. The
schema (`schemas/arkana/signal/1.0/…`) and the producer (`api/arkana_signal_routes.py`)
are unmodified; this is a test-side binding only.

Full-suite baseline recorded on `main` `4b91c2f4` in the same environment:
**19 failed, 4234 passed, 22 skipped, 1 error**, failing/error node set **20 nodes**,
sha256 `d6101722f624c0eedb48a957375f0b8abbef398f20e93e55e889dd8d9e0893ce`.
The single ERROR is the sovereign-reserved CE-01 `weaver.autonomy` module-vs-package
collision. None of the 20 nodes is in this file.

## 4. Limitations and non-claims

- This binds one extractor. It does **not** establish that the module's other helpers
  are all bound; a scan of this module found no other silent-pass direction, but that is
  a measurement of this module at this revision, not a general claim.
- `jsonschema` is absent in this environment, so
  `tests/test_arkana_signal_schema_conformance.py` skips its conformance assertions here
  (the exact gap this guard exists to cover). No conformance claim is made.
- No merge, deployment, or production-acceptance claim is made. The PR remains a draft
  and its merge is human-only under GOV-03.

## 5. Reconciliation context for this pulse

The three open lane PRs (#671 lane 1, #672 lane 3, #673 lane 2) were assessed
`ELIGIBLE_TO_MERGE` (advisory) and are **not** merged by this pulse. Composition of all
three was measured green in a detached worktree: zero conflicted files, 64 targeted tests
passing, lane guard `exit 0`, architecture 11/11. This PR is the lane-4 continuation
under §11 (N1–N8); it was opened only because lane 4 held no open PR.

**Recorded, not repaired** — a separate defect this pulse measured and did not fix:
`scripts/lane_state_refresh.py::LANE_OWNERSHIP` omits `tests/test_prism_novanet_engagement_readings.py`
(lane 2) and `tests/test_knowledge_graph_provenance_boundary.py` (lane 3), so the
derivation reports #673 and #672 as `unassigned_open_prs` while `--check` stays green
(the snapshot under-reports, so the guard judges nothing). Repairing it forces the three
lane docs to be re-pointed at #671/#672/#673 in the same change, which is a lane-doc
ownership question rather than a lane-4 one. See the pulse report.
