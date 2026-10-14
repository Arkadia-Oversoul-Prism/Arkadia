# PRISM W4 — lane-4 render integrity (orphaned projection recovery)

Bounded slice. Branch `gate-lane4/render-integrity-01`, base `main` @ `3ca8582a`.
Draft PR #530. No merge, no deploy, no acceptance is claimed.

## Measured defect

At `main` `3ca8582a`:

```
$ grep -rn "ExecutionLoop" web/arkadia_console/src
web/arkadia_console/src/components/lab/ExecutionLoop.tsx:...   # the definition alone
```

`ExecutionLoop.tsx` exports the canonical `DISCOVER..RECORD` work-loop projection. No
module imported it. A defined capability with zero rendered surfaces.

Corpus scan over the lane-4 feature directories (`src/components/lab`,
`src/components/weaver`), counting a component as reached only when a *different*
module both imports the binding and renders it as JSX:

| component | verdict |
|---|---|
| `ExecutionLoop` | **ORPHAN** |
| `LabAgentRegistry`, `LabArtifactCanvas`, `LabModelGateway`, `LabSessionList` | reached (`EngineeringLabPage.tsx`) |
| `LabRunTrace` | reached (`LabSessionList.tsx`) |
| `ApprovalLedger` | reached (`WeaverPage.tsx`) |

`ExecutionLoop` was the only orphan.

## Change

- `web/arkadia_console/src/pages/EngineeringLabPage.tsx` — import and render
  `<ExecutionLoop stages={readLoopStages(...)} />`, fed from the already-hydrated
  `endpoints.labEngineeringOverview` payload. A malformed payload yields no stages
  rather than an inferred list. No new registry member.
- `tests/test_prism_w4_lane4_render_integrity.py` (new) — derives the lane-4 projection
  set from the corpus at test time.

## Why the guard is derived, not listed

A hand-maintained component list blesses the next orphan: the wave that adds a
projection is the wave whose table would need the entry. The guard reads the corpus.

The reachability predicate requires **import AND render**. An import with no render is
the merge-loss shape recorded in `AGENTS.md` (`ff80b8c`: the import line from the first
parent, the render from the second) and is still zero rendered surfaces, so it is
reported as an orphan.

## Verification (this tree)

| check | result |
|---|---|
| `pytest tests/test_prism_w4_lane4_render_integrity.py -q` | 7 passed; **4 failed** on the pre-mount tree |
| `pytest tests/test_prism_w4_lab_read_model.py tests/test_prism_w4_lane4_render_integrity.py tests/test_prism_console_ci_wiring.py -q` | 67 passed |
| derived console gate `pytest -q $(python scripts/console_contract_domain.py)` | 433 passed (domain 23 -> 24) |
| `pytest tests/architecture -q` | 11 passed |
| full suite `-q -rEf --continue-on-collection-errors` | 8 failed / 2992 passed / 20 skipped / 1 error |
| failing/error **node set** sha256 | `c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b` (9 nodes) — identical to `main` `3ca8582a` |
| `corepack pnpm install && corepack pnpm build` | built in 1.52s |
| `python -m py_compile api/main.py` | OK; 2505 lines (budget 2600) |

The `+7 passed` equals the new guard's node count, so the delta is attributable by node
identity rather than by totals.

### Negative controls

1. a component with no consumer -> reported;
2. a component that is imported but never rendered -> still reported;
3. the **real** `EngineeringLabPage.tsx` with exactly the `ExecutionLoop` lines removed ->
   `ExecutionLoop` reported again (run against the live corpus, not a fixture).

### Positive control

A component that is imported and rendered is not reported.

## Remaining uncertainty / authority

- Source-level verification only. **No runtime or production observation** accompanies
  this slice, and none is claimed.
- Lane-4 composition with the sibling lane-4 PRs (#493, #501, #504, #512 — shared base
  `49809f45`) is untouched here; that is a separate composition question for the
  sovereign.
- `ExecutionLoop` is mounted on the Engineering Lab surface, which owns the overview
  read. Mounting it on Weaver belongs to whichever PR owns that file's final shape.

## Next bounded task

Advance the next lane whose PR is oldest and unadvanced (lane selection by rotation).
Do not extend this slice.
