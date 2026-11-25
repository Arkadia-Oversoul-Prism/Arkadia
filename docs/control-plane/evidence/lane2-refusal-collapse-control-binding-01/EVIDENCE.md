# Lane 2 — bind the refusal-collapse detector to a control

**Pass:** lane2-refusal-collapse-control-binding-01
**Base:** `main` `1bff8c42e78f153203641db6d8a90818f7ff6ab2`
**Lane:** 2 (NovaNet + project Opportunity Radar)
**Status:** IMPLEMENTED — draft PR, no merge, no deployment, no acceptance

## 1. The unguarded property

`web/arkadia_console/src/components/novaNet/EngagementBar.tsx` distinguishes two
refusals a write can produce:

```ts
function refusalFor(caught: unknown, fallback: string): string {
  const error = caught instanceof ApiError ? caught : null;
  if (error?.kind === "NOT_FOUND") return "This transmission no longer exists.";
  return caught instanceof Error ? caught.message : fallback;
}
```

The `NOT_FOUND` case is reachable and not hypothetical: `api/transmissions.py`
raises `404 {"detail": "post not found"}` from both write handlers
(`/react` and `/comment`), so reacting to a transmission that has been deleted
lands here.

Measured at `1bff8c42`: `tests/test_prism_novanet_engagement_readings.py` guarded
nine properties of this surface — the backend shape, the absence of a repost
handler, the exactly-two write paths, registry derivation, the reaction
vocabulary, both count readings, the repost reading's missing control, and the
page mount — and **none** of them touched `refusalFor` or the `NOT_FOUND` branch.
`grep -nE "NOT_FOUND|no longer exists|refusalFor|ApiError"` over the test file
returned **0** matches before this change.

## 2. The defect the guard must reject

Two shapes, both of which leave a reader misinformed:

1. **No branch at all** — the pre-repair form. Every failure of a write on a
   deleted transmission reads as "The reaction was not accepted.", which asserts
   the server declined a reaction when the post itself is gone.
2. **Branch present, generic message returned** — a detector that only looks for
   the presence of the `NOT_FOUND` token accepts this, so the branch can exist
   and still collapse the two facts.

## 3. The change

`tests/test_prism_novanet_engagement_readings.py` (+~60 lines):

- `_NOT_FOUND_BRANCH` / `_NOT_FOUND_LITERAL` / `_GENERIC_REFUSAL` predicates.
- `_refusal_collapse_defect(source)` — module-level, so the live assertion and
  the negative control call the *same* predicate (the convention this file
  already records for `_invented_count_defects`).
- `test_gone_transmission_is_named_not_generically_faulted` — asserts the router
  still answers `post not found` (so the guard cannot outlive its premise), that
  the branch exists, that it returns its own literal, and that the shipped
  surface is clean under the shared predicate.
- `test_detector_flags_a_collapsed_refusal` — negative control over both shapes,
  plus the positive polarity (the live surface is clean under the same predicate).
- One line added to `test_detectors_are_silent_on_the_live_tree`.

Both polarities are judged on purpose: the predicate requires the `NOT_FOUND`
literal **and** the generic `caught instanceof Error ? caught.message : fallback`
branch, so the detector is not satisfied by deleting the fallback it contrasts
against.

The message text is deliberately **not** pinned. Pinning copy is the near-miss
literal defect class this repository has already recorded; the guarded property
is "a gone transmission is named with its own message rather than the caller's
fallback".

## 4. Evidence

| Command | Result |
|---|---|
| `python -m pytest tests/test_prism_novanet_engagement_readings.py -q -rEf` | **17 passed** (15 before; +2 = the live assertion + its control) |
| live negative control (branch collapsed to `return fallback` in the real `EngagementBar.tsx`) | **3 failed, 14 passed** — `test_gone_transmission_is_named_not_generically_faulted`, `test_detectors_are_silent_on_the_live_tree`, `test_detector_flags_a_collapsed_refusal` |
| restore | `git checkout -- <file>`; `sha256sum -c` → **OK** (byte-identical), then **17 passed** |
| `python scripts/cp10_mutation_boundary_policy.py --judge` | PASS |
| `python -m py_compile api/main.py` | not required — `api/main.py` untouched |

The negative control was run against the **real** source file, not only a
synthetic fixture, so it proves the detector reads the shipped surface. The third
failing node is the control's own positive-polarity assertion; that is intended —
it states that the surface is clean, so a mutated tree reddens it.

## 5. Scope

- `tests/test_prism_novanet_engagement_readings.py` — lane 2's own contract test.
- `docs/control-plane/evidence/lane2-refusal-collapse-control-binding-01/EVIDENCE.md` — this record.

No lane instruction doc, no `lane-state.json`, no source module, no
`api/transmissions.py`, no authority surface, no deployment configuration. The
guarded surface is already correct; nothing in it was changed.

## 6. Not claimed

- No merge, no deployment, no production acceptance. Under GOV-03 merge execution
  is human-only; this is eligibility evidence, not authorization.
- `tests/test_prism_novanet_engagement_readings.py` is not yet in lane 2's
  ownership map on `main`; PR #676 adds it. Until that merges, the lane
  derivation reports this PR as unassigned. That is a known, open repair, not a
  claim made here.
- The frontend was not built in this sandbox; the change is a Python source-level
  assertion, so no bundle was produced or needed.
- `AGENT-02-NOVANET-OPPORTUNITY.md` still carries "Next bounded task on this lane:
  wire the reaction write path". That slice is **already discharged** in source
  (`EngagementBar.tsx` wires `POST /react` and `POST /comment`, guarded by this
  file). Repairing the doc requires re-deriving `lane-state.json` in the same
  change, and a snapshot that records its own PR open reddens `lane-doc-currency`
  the moment that PR merges. Recorded as a separate bounded action rather than
  executed here.
