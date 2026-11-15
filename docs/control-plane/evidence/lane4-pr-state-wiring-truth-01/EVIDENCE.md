# Lane 4 — PR-state surface wiring truth (evidence)

**Lane:** 4 (Arkana / Weaver / Engineering Lab)
**Branch:** `feat/prism-l4-pr-state-wiring-truth-01`
**Base:** freshly fetched `main` `19697a6a358ec114265e665fcc22eea8d5018ac2`
**Opened under:** `11 — LANE NEW-PR AUTHORIZATION` (N1–N8). Draft; merge is human-only.

## The defect

`web/arkadia_console/src/components/lab/LabPrState.tsx` renders a not-wired panel whose copy read:

> This read is not wired yet: the shared endpoint registry **does not declare** the pull-request
> route template, and this surface does not inline one. No request is issued.

That was true when the surface landed. It stopped being true at `d44b26b3` (#623, Lane 1), which
registered the entry in `src/lib/endpoints.ts`:

```
labEngineeringPr: "/api/lab/engineering/pr/{number}",
```

The surface composes `registry.labEngineeringPr`, so the template resolves and the not-wired branch
is **dead**. The panel therefore states a falsehood about its own wiring: a reader who ever saw it
would be told a control is missing that is in fact mounted and usable. The surrounding comments
("Lane 1 has not declared the entry yet") carried the same stale claim.

Measured at `main` `19697a6a`:

| Fact | Command | Result |
|---|---|---|
| Registry declares the entry | `grep -n labEngineeringPr web/arkadia_console/src/lib/endpoints.ts` | `labEngineeringPr: "/api/lab/engineering/pr/{number}"` |
| Surface reads it | `grep -n registry.labEngineeringPr …/LabPrState.tsx` | present |
| Backend serves it | `app.openapi()['paths']` filter `engineering/pr` | `/api/lab/engineering/pr/{number}` |
| Mounted without an override | `grep -n "<LabPrState />" …/EngineeringLabPage.tsx` | `<LabPrState />` (no `pathTemplate`) |

So `template` is truthy on the shipped mount, and the not-wired panel cannot render.

## The repair

`LabPrState.tsx` — the claim is now conditional on the registry *losing* the entry, and the stale
comments are corrected. `pathTemplate` remains an optional override; the not-wired branch stays as
a guard for a registry that no longer declares the route (or a caller passing an empty template).

`tests/test_prism_w4_lab_pr_state.py` — adds a detector and its control:

```python
def _false_unwired_claim(surface_text: str, registry_text: str) -> list[str]:
    declared = re.search(rf'{PR_STATE_ENTRY}:\s*"([^"]+)"', registry_text)
    if not declared:
        return []
    ...
```

Module level, so the live assertion and its control call the *same* code.

## Proof — live negative control on the real file

| Step | Result |
|---|---|
| Reintroduce the pre-repair copy in the real `LabPrState.tsx` | `test_unwired_copy_agrees_with_the_registry` → **FAILED**; `1 failed, 18 passed` |
| Restore byte-identically (`md5 94b816176a601814a7997faf18643f5c` before and after) | `19 passed` |

The control also asserts the opposite polarity: a registry genuinely lacking the entry makes the
same copy truthful and must **not** be reported, so a detector that reports unconditionally cannot
pass either.

## Attribution

`--collect-only` on the file: `17` on `main` → `19` on the branch. `+2` = exactly the new guard and
its control. `tests/architecture` **11 passed**. Lane-4 and lane-currency contracts **147 passed**.
`scripts/lane_state.py --check` exit **0**.

## Boundaries

Lane-4 owned paths only: `web/arkadia_console/src/components/lab/LabPrState.tsx` and
`tests/test_prism_w4_lab_pr_state.py`. No Lane 1 registry edit; no other lane's file. No authority,
identity, governance, or deployment surface touched. Merge, production deployment and acceptance
remain human-only.
