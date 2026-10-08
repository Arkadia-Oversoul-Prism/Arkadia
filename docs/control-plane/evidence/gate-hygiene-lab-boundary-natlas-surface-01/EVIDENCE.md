# gate-hygiene/lab-boundary-natlas-surface-01

**BASE_MAIN**: `f96d5fd2` (merge of PR #353, "Fix N-ATLaS Lab public tester onboarding")
**Branch**: `gate-hygiene/lab-boundary-natlas-surface-01`
**Workstream**: `gate-hygiene` -> Engineering Lab boundary guard vs. a deliberate
surface change
**Scope**: one test file (`tests/test_engineering_lab_api.py`). No production code,
no `api/main.py`, no governance surface, no authority path, no workflow, no policy
module.

## Objective (bounded)

Restore the Engineering Lab's boundary guard so it describes the Lab surface that
actually exists after PR #353, without weakening the guard's teeth.

## Defect (root cause, not the symptom)

Two guards in `tests/test_engineering_lab_api.py` were written against the Lab
surface as it stood before PR #353 and were never updated when #353 deliberately
added the N-ATLaS external-tester surface. They now fail on `main` for reasons that
are *not* boundary violations:

1. `test_lab_router_is_read_only_and_authenticated` pinned the router-wide
   dependency name to the literal `"require_auth"`. PR #353 replaced the router
   dependency with `require_lab_auth` — a thin wrapper that delegates to
   `require_auth` and exempts the deliberate public N-ATLaS tester paths. The test
   asserts `"require_auth" in dependency_names`, which is now `False` even though
   authentication is intact and *stricter* about what is anonymous.

2. `test_lab_mutation_endpoints_are_exactly_the_lab_state_set` compares the mutating
   route set against a frozen `ALLOWED_MUTATION_ENDPOINTS` inventory that predates
   #353. #353 added `POST /api/lab/engineering/n-atlas/test-session` and
   `POST /api/lab/engineering/n-atlas/run`, both genuine Lab-state operations
   (a bounded tester session and a governed run through the existing runtime).
   The set therefore grew and the equality assertion failed.

Neither endpoint touches the repository, authority, provenance, or credentials. The
forbidden-surface guard (`test_lab_route_has_no_repository_mutation_surface`) still
passes, and it is the guard that actually enforces the mutation boundary.

## Change

`tests/test_engineering_lab_api.py` — test-side only:

* assert the router-wide dependency set is exactly `{"require_lab_auth"}` and that
  `require_lab_auth` still delegates to `require_auth`;
* assert the public (unauthenticated) Lab surface is exactly
  `_PUBLIC_NATLAS_PATHS == {"/api/lab/engineering/n-atlas/catalog",
  "/api/lab/engineering/n-atlas/test-session"}` — so any widening of the anonymous
  surface fails the guard;
* add the two N-ATLaS Lab-state endpoints to `ALLOWED_MUTATION_ENDPOINTS` with a
  comment stating why each is a Lab-state operation.

The guard's teeth are preserved: a *new* unexpected mutating endpoint, or a new
anonymous path, or a `require_lab_auth` that no longer delegates to `require_auth`,
all still fail.

## Evidence

Baseline (`main` `f96d5fd2`, with `pytest-asyncio` installed per `requirements.txt`):

```
$ python -m pytest tests/test_engineering_lab_api.py -q
FAILED ::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED ::test_lab_router_is_read_only_and_authenticated
3 passed, 2 failed
```

After the change:

```
$ python -m pytest tests/test_engineering_lab_api.py -q
5 passed
```

Full-suite node-set delta (the load-bearing invariant — counts move with environment):

| tree | failing/error nodes | outcomes fingerprint | ids fingerprint |
|------|--------------------|----------------------|-----------------|
| main `f96d5fd2` | 17 | `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798` | `571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224` |
| branch | 15 | `d9d7c736c0f38f48a35f48ff11ed11bebb19fc59cb00c8e9215af19099cfd74e` | `5127ffedd32c32c8ac98b21da66e1c10eee8a7ec8175633826bd2d0a9b0e3ac1` |

`diff` of the sorted node sets is exactly the two repaired nodes; **no node was added
or otherwise changed**. `14 failed, 1772 passed, 22 skipped, 1 error` vs baseline
`16 failed, 1770 passed, 22 skipped, 1 error` on the same tree class.

```
$ python -m pytest tests/ -q -rEf --continue-on-collection-errors
14 failed, 1772 passed, 22 skipped, 2 warnings, 1 error in 145.37s
```

Architecture fitness: `python -m pytest tests/architecture -q` -> **11 passed**
(unchanged; `api/main.py` is not touched, so the 2600-line budget is unaffected).

## Baseline debt — recorded, not fixed here

The canonical failure set at `f96d5fd2` is **17 nodes**, not the stale
`tests/fixtures/baseline_node_set.txt` (10 nodes). Sixteen of the 17 belong to other
workstreams and are explicitly out of scope:

* 3 x `test_m02a_ci_gate_integrity.py` — the CP10 allowlist omission for
  `deploy/n-atlas-server/Dockerfile`; repaired by open PR #354.
* 1 x `test_ci_gate_trigger_coverage.py[n-atlas-developer-lab.yml]` — repaired by
  open PR #355.
* 1 x `test_ais_capability_profile_onboarding.py` — claimed by open PR #347.
* 1 x `test_autonomy.py` (ERROR) — the CE-01 `weaver.autonomy` module-vs-package
  collision, reserved to the sovereign.
* 3 x `test_steward_filter.py` — `weaver/filters/steward.py` logic.
* 7 x AIS/identity/ReasoMate/SolSpire governance nodes — unrelated subsystems.

Note: **10 of the 17 nodes are absent from the recorded fixture**, so "fixture ==
baseline" is no longer true on `main`. Regenerating that fixture is a separate bounded
workstream and is *not* performed here.

## Remaining uncertainty

* The two AEAS SSE-transport PRs (#337, #338) both edit `api/lab_routes.py` and share
  `base = f96d5fd2`. They will each need to add their own state to the
  `ALLOWED_MUTATION_ENDPOINTS` inventory when they rebase. This PR does not pre-empt
  that; it only aligns the inventory with the surface that exists on `main` today.
* `pytest-asyncio` is required by `requirements.txt` but is not installed by the
  current CI job; without it one async node errors. That is a CI-install gap, not a
  code defect, and is out of scope here.

## Authorization required

Human merge. This is a test-only change with no production, governance, or authority
surface.
