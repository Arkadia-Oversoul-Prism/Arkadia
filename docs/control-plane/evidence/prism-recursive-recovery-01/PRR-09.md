# PRR-09 — SolSpire control-plane spine over the served `/solspire` reads

Mission: `prism-recursive-recovery-01` — recover useful Prism capabilities into the
canonical Arkadia Console (`web/arkadia_console`).
Lane: B/C boundary (SolSpire) · Work item: **PRR-09**.
Base: `main` @ `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`.

## 1. Defect (measured, not assumed)

`web/arkadia_console/src/pages/SolSpirePage.tsx` at `3ca8582` advertised four
contracts as not-yet-wired, all carrying a wrong `/api` prefix:

```
/api/solspire/workloads   /api/solspire/proposals
/api/solspire/pulses      /api/solspire/voice
```

The canonical backend mounts the SolSpire routers under the bare `/solspire`
prefix (`solspire/console_router.py:52`), with no `/api` segment
(`workload_router.py:13`, `pulse_router.py:14`, `synthesis_router.py:14`).
Three of those reads are real, owner-scoped GETs, so the page was declaring a
scaffold where a served contract already existed — the exact "advertise the
wrong thing rather than read the real one" failure the recovery mission targets.

## 2. Change

- `src/lib/endpoints.ts` — four registry entries, `/solspire/...` (no `/api`):
  `solspireWorkspace`, `solspireWorkloads`, `solspirePulses`, `solspireSyntheses`.
- `src/lib/types.ts` — `SolspireWorkspace`/`SolspireWorkspaceRead`,
  `SolspireWorkload`/`SolspireWorkloadRead`, `SolspirePulse(List)`,
  `SolspireSynthesis(List)`, derived from the served handlers' `to_dict()` shapes.
- `src/components/solspire/SolSpireControlPlane.tsx` (new) — read-only surface:
  canonical workspace facts, canonical workload facts, and the daily-pulse /
  weekly-synthesis lists, each through `useHydration` + the registry.
- `src/pages/SolSpirePage.tsx` — mounts the control plane; replaces the four
  wrong-prefix placeholders with four **served** contracts whose notes state the
  real reason each is not wired (authority act, provenance reconciliation,
  no enterprise projection, no governed-chain surface) rather than a fake one.
- `tests/test_prism_solspire_control_plane.py` (new).

No control on this surface mutates anything; no endpoint was added or changed.

## 3. The narrow states the surface must not read as failure

Verified against the real router (executed, not source-read):

| read | state | status | surface copy |
| --- | --- | --- | --- |
| `GET /solspire/workloads` | no canonical workload yet | `404` | "No canonical workload exists … a 404 here is the honest empty state" |
| `GET /solspire/workloads` | workspace not bound | `409` | "workspace is not bound yet" |
| `GET /solspire/pulses` | workspace not bound | `409` | "workspace is not bound yet" |
| `GET /solspire/syntheses` | workspace not bound | `409` | "workspace is not bound yet" |
| any read | unauthenticated | `401` | shared `ContractState` auth-required |

The `404`/`409` distinction is drawn from the response **status** via
`ApiError.kind`, never guessed from an empty body.

## 4. Verification

| check | result |
| --- | --- |
| `pnpm build` (`tsc --noEmit && vite build`) | PASS (84 modules, 1.55 s) |
| `pytest tests/test_prism_solspire_control_plane.py` | **12 passed** |
| targeted suites (control-plane + route-composition + endpoint-registry + interior-shell + `tests/architecture`) | **47 passed** |
| `pytest tests/test_prism_pass_c_surface_ownership.py tests/test_solspire_p1_experience_01.py tests/test_solspire_route_composition_ci_wiring.py` | **38 passed** |
| architecture fitness | 11 passed (baseline, unchanged) |

Baseline recorded before edits: architecture 11 passed; targeted SolSpire console
suites 24 passed. No pre-existing failure node changed fingerprint.

### Live negative control (proves the detector reads the real file)

Mutated `SolSpirePage.tsx` in the working tree, changing the mounted
`contract="/solspire/proposals"` to `contract="/api/solspire/proposals"`, and
re-ran the new suite:

```
FAILED tests/test_prism_solspire_control_plane.py::test_page_no_longer_advertises_the_wrong_api_prefix
FAILED tests/test_prism_solspire_control_plane.py::test_page_mounts_the_control_plane_and_advertises_only_served_paths
2 failed, 10 passed
```

Restored byte-identically; suite returns to 12 passed. The guard therefore bites
on the real page, not only on a synthetic string.

## 5. Review findings

- Diff = 3 edited source files, 1 new component, 1 new test, this evidence dir.
- Every read goes through the shared endpoint registry; the panel composes no
  `/solspire/...` path itself (asserted with a negative control), so there is no
  second source of truth for the contract.
- Read-only: no create/decide/execute control, no write, no new route.
- No test was weakened; no baseline debt was touched.

## 6. Limitations (explicitly not claimed)

- **NOT TESTED (browser).** No browser/e2e harness exists in this sandbox.
  Rendering and live fetch behavior are covered by the build and by the executed
  backend + source-contract suites, not by an observed browser session.
  Production parity / acceptance is **NOT CLAIMED**.
- `GET /solspire/proposals` remains advertised as not-wired on purpose: the
  decision endpoint is a human authority act, and the console offering one is an
  authority-boundary question, not a UI gap.
- Merging and deployment are outside this task's authority: the change exists on
  a branch and a draft PR only.
