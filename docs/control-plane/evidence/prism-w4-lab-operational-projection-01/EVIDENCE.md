# Workstream 4 — Engineering Lab operational read projection

**Slice:** Lab operational projection (integrations · android · voice)
**Branch:** `feat/prism-l4-lab-operational-projection-01`
**Base `main` at start:** `dfbd2304db27746b22f0cda9b6961d1e37fda313`
**Authority:** implement, test, commit, report. **No merge, no deployment, no acceptance.**

---

## 1. Why this slice, and the ownership boundary

`GET /api/lab/engineering/overview` returns truthful sub-reports built by the
Lab's own modules. `EngineeringLabPage.tsx` previously folded the whole overview
into `Object.entries(...).slice(0, 12)` and rendered it as an opaque JSON string,
so the distinctions those reports exist to state were collapsed or truncated past
the tenth key.

Two sibling Lane-4 PRs are open against this same seam at the time of writing:

| PR | Branch | Touches |
|---|---|---|
| #493 | `feat/prism-next8-04-automation-grammar` | `LabAutomationGrammar.tsx`, `labAutomationGrammar.ts`, `EngineeringLabPage.tsx` |
| #501 | `feat/prism-next9-04-canonical-loop-mount` | `EngineeringLabPage.tsx` |

`SHARED-CONTRACTS.md` §4 forbids duplicate ownership. #493 already owns the
**automation-grammar** render on the Lab surface, so this slice deliberately does
**not** render the grammar. It renders the three sub-reports #493 does not touch:

- `integrations` — `adapters.describe_integrations()`
- `android` — `android.android_capability_report()`
- `voice` — `voice.voice_boundary_report()`

`tests/test_prism_w4_lab_operational_projection.py::test_surface_stays_out_of_the_sibling_grammar_territory`
pins that the slice does not take the grammar territory.

## 2. Verified data contract (handler-derived, not invented)

`lab/engineering_lab/` modules were imported in this environment and their output
keys were read directly; the test re-measures them at run time so a rename on
either side fails loudly instead of degrading to a healthy-looking blank.

| Sub-report | Module | Keys read |
|---|---|---|
| integrations | `adapters.describe_integrations()` | `adapters[].{provider,state,detail,credential_source}`, `note` |
| android | `android.android_capability_report()` | `surface`, `execution_location`, `capabilities[].{capability,state,human_only_never_exposed}`, `authority.{android_is_not_an_authority_layer,merge_exposed,deploy_exposed}` |
| voice | `voice.voice_boundary_report()` | `surface`, `recognizer_state`, `recognizer_configured`, `intents`, `human_only_intents`, `non_collapse` |

No endpoint is declared or invented here — the page keeps its existing overview
fetch and only changes how the already-fetched object is presented.

## 3. Files changed

| Path | Change |
|---|---|
| `web/arkadia_console/src/components/lab/labOperational.ts` | Pure projection over the overview object; `readOperationalReadings`, `scalarOverview`, `OPERATIONAL_KEYS` |
| `web/arkadia_console/src/components/lab/LabOperationalSurfaces.tsx` | Labelled read-only surface for the three sub-reports, with distinct absent states |
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | Uses `scalarOverview()` for facts and `LabOperationalSurfaces` for the sub-reports; raw `slice(0, 12)` dump removed |
| `tests/test_prism_w4_lab_operational_projection.py` | Contract test — executes the real `.ts` under Node; negative controls |

## 4. Verification

- Targeted: `python -m pytest tests/test_prism_w4_lab_operational_projection.py -q -rEf` → **12 passed**.
- Frontend: `corepack pnpm build` (tsc --noEmit + vite) → **built, 0 type errors**.
- CP10 boundary judge over changed paths → **PASS**.
- Full suite (once): `8 failed, 2985 passed, 20 skipped, 1 error`.
  Failing/error **node set** sha256
  `c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`.
  Every failing node is pre-existing drift unrelated to this slice (Lab auth
  pins, Landing copy, identity spine, solspire r1/r3); **none** references a file
  this slice touches.

## 5. Negative controls

- `test_negative_control_an_off_vocabulary_state_is_stated_not_dropped` — an
  unknown adapter state renders as itself; a `null` credential source renders
  `UNKNOWN`, not blank.
- `test_negative_control_an_absent_sub_report_is_null_not_a_healthy_default` —
  an overview missing a sub-report yields `null`, never an empty shell.
- `test_negative_control_a_missing_field_reads_unknown_not_blank` — every
  undeclared field reads the `UNKNOWN` sentinel.
- `test_page_uses_the_projection_and_drops_the_raw_slice_dump` — verified to
  fail on the injected defect, then restored.

## 6. Original handoff boundary

At the initial handoff, `EngineeringLabPage.tsx` was shared with #493 and #501.
This slice's page change is additive (`LabOperationalSurfaces` beside the
existing facts render) and does not remove their hooks. The original "route to
integrator; do not merge" note described that handoff state and is superseded by
the founder's later instruction to repair the integration gates and integrate
eligible work. It is not a current prohibition on integration.

## 7. Integration correction and current acceptance boundary

- **Current integration base:** `main` at
  `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`. This branch is being reconciled
  against that base rather than the original `dfbd2304` baseline.
- **Design-token guard correction:** the reported `#493` matches were pull-request
  references inside TS/TSX comments, not colour literals. The guard now removes
  block and full-line comments before scanning. Regression controls prove that a
  comment reference does not trip the guard and an actual page-local hex colour
  still does. The guard was not weakened and the component's original PR reference
  wording is preserved.
- **Production 503 attribution:** the original seven-route smoke began at the same
  time as a Render deployment and finished before that deployment became live.
  After the deployment completed, the exact-revision smoke observed
  `source_revision=24e5894992709847a67acb3a04954dbd871d3feb`; all seven routes
  returned HTTP 200 with non-empty content and zero browser console/page errors.
  The readiness workflow now requires the expected main SHA and allows up to
  300 seconds for Render rollout. The current main deployment gate is checked
  separately; a successful source test alone is not deployment acceptance.
- **Acceptance remains pending** until the final candidate head's required CI
  checks pass and the post-deploy smoke observes the exact deployed SHA and
  validates all seven routes. No authenticated Solariun interaction has been
  claimed from the unauthenticated route smoke.
