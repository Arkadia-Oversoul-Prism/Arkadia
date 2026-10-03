# test-hygiene/review-route-boundary-false-positive-01

Bounded workstream: repair a **test-side false positive** in the Gate 05
(`VERIFICATION != REVIEW`) boundary assertion. No production/backend code
changes; `api/main.py` untouched.

## 1. Defect (reproduced)

`tests/test_verification_review_boundary.py::test_no_http_surface_exposes_review_as_a_first_class_record`
enumerated route decorators and flagged any decorator line whose text contained
the substring `review`. Measured on `main @ 357fbd8`:

```
AssertionError: review route exists:
  ['solspire/console_router.py: @router.post("/projects/{project_id}/patches/preview")']
```

The flagged route is `/projects/{project_id}/patches/preview` — a patch
**preview** endpoint. The match is the substring `review` inside `preview`, not
a Review route. This is the recurring test-side defect class recorded in
`AGENTS.md` ("source-level literal pins / regex false positives"): the
assertion does not measure the property it names.

The boundary itself is intact: the review-boundary file's other 8 tests pass,
and the independent Gate 05 measurements (no `review` table, no `ew_review`,
no `class Review`, no `review_id` in backend source) hold.

## 2. Repair

Match the route **path segment** rather than the decorator-line substring:

- `_review_path_segments(line)` extracts the route path string literal, splits
  on `/`, and returns segments equal to `review` / `reviews` (case-insensitive).
  `preview` is not a segment `review`, so it no longer matches.
- `_enumerate_review_routes()` shares the enumeration between the boundary
  assertion and its control.

Dry run over the live corpus before editing: **298 route decorators, 0
review-segment hits** — the corrected detector does not weaken the boundary.

## 3. Negative control (proves the detector can fail)

`test_review_route_detector_matches_the_resource_not_a_substring`:
detects `"/review"`, `"/projects/{id}/reviews"`, `"/reviews/{review_id}/decide"`;
does **not** flag `"/projects/{project_id}/patches/preview"` or
`"/authorizations/{authorization_id}/execute"`.

Because `"review" in "preview"` is `True`, reverting the detector to substring
matching fails this control — the assertion cannot go vacuously green.

## 4. Verification

| check | before (`main 357fbd8`) | after |
|---|---|---|
| `tests/test_verification_review_boundary.py` | 1 failed / 8 passed | **10 passed** |
| `tests/architecture` | 11/11 | 11/11 |
| `tests/test_m02a_ci_gate_integrity.py` | 55/55 | 55/55 |
| full suite `tests/ -q --continue-on-collection-errors` | 23F / 1368P / 19S / 1E | 22F / 1370P / 19S / 1E |
| failing+error **node set** | 24 nodes | 23 nodes |

Node-set diff is exactly one line: the repaired node is removed; **no new
failure node appears**. `python -m py_compile api/main.py` → OK (2582 lines,
under the 2600 budget; file untouched).

## 5. Scope / authority boundary

- Changed: `tests/test_verification_review_boundary.py` only.
- Non-goals: repairing the two sibling route-regex false positives
  (`test_evidence_verification_boundary.py`, `test_workevent_evidence_boundary.py`),
  the `conftest.py`-strict `test_m02a_ci_gate_integrity.py` nodes, the `AGENTS.md`
  encoding adjudication nodes, frontend literal pins, or the sovereign-reserved
  `test_autonomy.py` `weaver.autonomy` collection error. Each is a separate
  bounded workstream; none is a dependency of this one.
- Authority: test-only change on a dedicated branch to a PR. Human merges.
