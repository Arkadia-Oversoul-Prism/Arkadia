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

---

## §3.1 defect — the surface inlined its own endpoint path (repaired)

The first head (`642d79d1`) inlined the prefix:

```ts
const BASE = "/api/lab/engineering/pr";
```

`console-contract` failed on exactly this. The job's failing assertion is
`test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path`
(run `41968228008`, job `127050130430`), which reported:

```
page-local endpoint path(s): ['components/lab/LabPrState.tsx: useHydration path argument \'path ?? ""\'']
```

That is a correct report, not a false positive: the gate's contract is that a
read path is **derived from** `src/lib/endpoints.ts`, and a page-local prefix is
a second, unreviewed endpoint contract (SHARED-CONTRACTS §3.1).

### Why this is a Lane 1 interface request, not a Lane 4 edit

`web/arkadia_console/src/lib/endpoints.ts` is Lane 1's exclusive file (§1), and
§4 requires a feature agent whose slice depends on a shared change to **pause the
dependent slice and record the blocker** rather than edit another lane's file.
Lane 1's registry declares eight Lab engineering endpoints
(`labSessions`, `labAgents`, `labArtifacts`, `labAutomations`, `labGateway`,
`labNAtlasCatalog`, `labRepository`, `labEngineeringOverview`) and **no**
`labEngineeringPr` entry. So the repair is bounded to the two Lane 4 files:

- `labPrState.ts` — `prStatePath(base, number)` composes onto a caller-supplied
  base instead of owning a constant. The trailing-slash case is covered.
- `LabPrState.tsx` — reads the prefix from the registry
  (`basePath ?? registry.labEngineeringPr`) and holds no literal. The registry is
  `as const` and the entry is not yet declared, so the lookup is typed optional;
  with the entry absent the surface renders a **non-interactive not-wired state**
  (`lab-pr-not-wired`) and issues no request (§3.6), instead of a control that
  cannot work.

**Interface request to Lane 1 (not performed here):** declare

```ts
labEngineeringPr: "/api/lab/engineering/pr",
```

in `src/lib/endpoints.ts`. The handler is served (`GET
/api/lab/engineering/pr/{number}`), so the entry would satisfy
`test_every_declared_endpoint_is_served_by_the_canonical_app`. Until it lands the
surface is honestly blocked rather than wired by a second path.

### Proof

| Check | Result |
|---|---|
| `test_console_endpoint_registry_contract.py::test_every_page_read_uses_the_registry_not_an_inline_path` | **1 passed** (was failing) |
| `tests/test_prism_w4_lab_pr_state.py` | **17 passed** |
| `tests/test_console_endpoint_registry_contract.py` | **passed** |
| `tests/architecture` | **11 passed** |
| `tests/test_prism_console_ci_wiring.py` | **30 passed** |
| `tsc --noEmit` | exit 0 |
| `pnpm build` | ✓ built |
| CP10 mutation boundary | PASS |
| `git check-ignore web/arkadia_console/dist` | ignored |

Negative controls (both bite, then the file was restored byte-identically):

- **A — inline the path:** `useHydration<…>("/api/lab/engineering/pr/" + target, …)`
  → `2 failed` (this lane's guard *and* the authoritative registry guard).
- **B — import the registry but do not read it:** `const base = basePath;`
  → `1 failed` (`test_surface_takes_its_prefix_from_the_shared_registry`). The
  first cut of that assertion was silent on this shape — a guard that cannot
  redden on the defect it names is not a guard, so it now asserts the entry is
  read, not merely imported.

## Exact route-template integration — 2026-11-05

The first integration request asked Lane 1 to declare the prefix `/api/lab/engineering/pr`. The canonical endpoint registry guard requires every entry to be a served route, while this handler serves only the parameterized path. The shared entry therefore uses the exact OpenAPI template instead:

`labEngineeringPr: "/api/lab/engineering/pr/{number}"`

Lane 1 has added that entry and a contract test in its existing PR #623. This PR consumes the exact template:

- `prStatePath(template, number)` validates the positive integer, requires exactly one terminal `{number}` placeholder, URL-encodes the value, and returns no path for a bare prefix or malformed template.
- `LabPrState` reads `registry.labEngineeringPr` and remains non-interactive while the entry is absent; no fallback literal or request is introduced.
- The projection tests now exercise template substitution and refusal states.

**Dependency:** PR #623 must merge before the shared endpoint is present on `main`. Until both this feature and the registry entry are present in the composed application, the panel must remain `NOT WIRED`; this branch does not claim a live PR-state read.

**Verification:** source/test changes committed; fresh CI for the current head is pending. Authenticated browser acceptance, desktop/mobile visual acceptance, preview verification and production verification remain separate and unclaimed.

No backend, authorization, identity, approval, WorkEvent, persistence or production configuration change.