# Lane 4 — Lab PR-state surface (EL-10) — evidence

## Objective

Give the Engineering Lab's read-only PR-state handler console coverage.

`GET /api/lab/engineering/pr/{number}` (`api/lab_routes.py::pr_state`, EL-10) was
served but referenced by **no** console module — the Lab's own PR-state read was
reachable only by hand. This change surfaces it as a read-only panel, projected
through a pure module so the projection's behaviour is measurable rather than
merely readable.

## Base

- Base branch: `main`
- Base SHA: `4ff76c152f057795bf57c3abeb8de9b0e772f67b` (live `origin/main` at the
  time the branch was cut)

## Scope (lane 4 owned paths)

| Path | Change |
|---|---|
| `web/arkadia_console/src/components/lab/labPrState.ts` | New — pure projection |
| `web/arkadia_console/src/components/lab/LabPrState.tsx` | New — read-only surface |
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | Mount `<LabPrState />` |
| `tests/test_prism_w4_lab_pr_state.py` | New — 15 contract tests |

No backend change. No `api/main.py` change. No workflow change (see below).

## Why the handler's shape, not an invented one

The handler answers with exactly two states and never a third:

- `AVAILABLE` → `pr` is the record read from GitHub
- `UNAVAILABLE` → `pr` is `None` and `detail` says why (no token / HTTP status /
  transport failure)

`tests/test_prism_w4_lab_pr_state.py::test_handler_emits_the_keys_the_projection_reads`
invokes the handler directly and asserts the keys it emits, so the fields the
projection reads are measured rather than inferred from an interface.

## Non-collapses preserved

The Lab's doctrine is that distinct facts must not render alike. Each of these is
an asserted property, not a comment:

- **UNAVAILABLE is not AVAILABLE.** An unavailable read yields no state, no draft
  flag and no mergeability — `lifecyclePhrase` returns `not reported`.
- **Reachability is not mergeability.** `mergeable_state` is reported only when
  the payload carries it; an omitted value reads as `not reported`, never as
  `clean`.
- **`closed` is not `merged`.** GitHub returns `closed` for both a merged and an
  abandoned PR, and the handler does not read GitHub's `merged` field. The
  projection therefore reports the outcome as *not reported* rather than guessing.
- **No answer is not an absence.** A `null` payload reads as `UNKNOWN`, so "we did
  not get an answer" cannot render as "there is no pull request".
- **A declared AVAILABLE with no record is malformed, not a PR.**

## Verification (all measured on this head)

| Check | Result |
|---|---|
| `python -m pytest tests/test_prism_w4_lab_pr_state.py -q -rEf` | **15 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python -m pytest tests/test_prism_console_ci_wiring.py -q` | **30 passed** |
| `python scripts/console_contract_domain.py` | **65 → 66** (the new guard enters the derived domain) |
| `git status --porcelain \| ... \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** — every path admitted |
| `corepack pnpm install --frozen-lockfile && corepack pnpm build` | **success** — `tsc --noEmit` clean, `✓ 148 modules transformed` |

`web/arkadia_console/dist/` is untracked and gitignored, so the build left no
tracked artifact.

### No workflow edit was required

`scripts/console_contract_domain.py::derive_domain` derives the executed
inventory from `git ls-files` **at call time**, and
`.github/workflows/prism-console-contract.yml` runs
`python -m pytest -q $(python scripts/console_contract_domain.py)`. The new guard
enters that derived domain on its own (65 → 66), so it is executed by the gate
without the hand-maintained list this class of change used to require.

### Negative controls (live, on the real module)

Each control mutated the shipped file, observed the guard redden, then restored
it byte-identically.

| Control | Mutation | Result |
|---|---|---|
| C1 — no invented mergeability | an absent `mergeable_state` defaulted to `"clean"` | `test_partial_record_reports_absent_fields_as_unreported` **FAILED** (1 failed, 14 passed) |
| C2 — the path validator bites | the `isValidPrNumber` guard removed | `test_invalid_numbers_issue_no_request` + `test_negative_control_path_builder_can_fail` **FAILED** (2 failed, 13 passed) |

After restoration: `diff` against the pre-control copy is empty, and the suite
returns to **15 passed**. A guard that cannot redden on the defect it names is not
a guard.

## Boundaries preserved

- The surface issues **GET only**. A test asserts no `POST`/`PUT`/`PATCH`/`DELETE`
  appears in it.
- The handler is already gated by `require_lab_auth` on the router
  (`api/lab_routes.py:63`), and the console's `engineering-lab` surface is
  `requiresAuth: true`.
- No authority, identity, K15/K3 governance, approval-enforcement, constitutional
  architecture or deployment configuration is touched.
- The handler performs a live GitHub read, so the surface issues its request on
  submit rather than on every keystroke.

## Status

`IMPLEMENTED` and locally `VERIFIED`. This is a **draft** PR. It is not a merge,
deployment, or acceptance claim; merge authority is reserved to the human
sovereign.
