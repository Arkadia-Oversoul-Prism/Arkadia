# A skipped router mount is invisible: the composed surface is asserted nowhere

Workstream: `gate-hygiene/router-mount-completeness-01`
Branch: `gate-hygiene/router-mount-completeness-01`
Base: `main` @ `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-25T15:06Z)
Contract: ARK-OPS-CONTINUOUS-001 (rev. 2026-11-22) — reconciliation, gap closure, no merge authority.

## 1. The gap

`api/main.py` mounts **12** routers inside `try: ... except Exception:` handlers that log a
warning and continue:

| include variable | module |
|---|---|
| `_nodes_router` | `api.nodes` |
| `_dist_router` | `api.distribution` |
| `_ims_products_router` | `api.ims_products` |
| `_pulse_router` | `api.pulse` |
| `_solspire_router` | `solspire.console_router` |
| `_commune_threads_router` | `api.commune_threads` |
| `_knowledge_router` | `api.knowledge_routes` |
| `_messages_router` | `api.messages` |
| `_echofeild_router` | `api.echofeild` |
| `_tx_router` | `api.transmissions` |
| `_arkana_signal_router` | `api.arkana_signal_routes` |
| `_arkana_stream_router` | `api.arkana_stream_routes` |

The fail-open shape is deliberate — one broken optional surface must not take the application
down. The defect is that **nothing asserted the composed surface**, so a failed import produces a
*healthy-looking* application with a product surface missing, and the only signal is one WARNING
line in the boot log.

`grep -rn "from api.main import app" tests/` finds 30+ modules that assert *individual* routes.
None of them asserts that the routers mounted inside a swallowing handler are present, and a test
that imports a router module directly fails on an import error — a different property from "the
composition root mounted what it declared".

`tests/test_solspire_route_composition.py` is the closest existing guard and does not cover this:
it builds its own `FastAPI()` and calls `app.include_router(solspire_router)` directly, so it
passes whether or not `api.main` mounted anything.

## 2. The defect, executed (not asserted)

Blocking one module import and re-executing `api.main`:

```
baseline /solspire/projects reachable: True
blocked: app built: True
blocked: /solspire/projects reachable: False
blocked: /health reachable: True
restored: /solspire/projects reachable: True
elapsed 0.2s
```

The application still builds and `/health` still answers while **133** SolSpire console routes are
gone. That is the fail-open behaviour working as designed and failing silently as designed.

Measured on the composed app at `fd0a4fdc`:

- flattened route table (all mounts, include prefixes resolved): **344** `(method, path)` entries,
  **0** duplicates;
- 12 fail-open modules declare **250** leaf routes, all reachable — so this is a *latent* gap, not
  a live breakage. The guard exists to keep it that way.

## 3. The repair

`tests/test_router_mount_completeness.py` (4 nodes, test-only — no production code changed,
`api/main.py` untouched):

1. `_fail_open_mounts()` derives `(include_variable, module)` from `api/main.py` **by AST**: every
   `app.include_router(...)` inside a `try` whose handlers never `raise`. The domain is derived, so
   a new fail-open mount is judged by the same rule without editing the test.
2. `test_every_fail_open_mount_carries_its_routes_on_the_composed_app` — every leaf route each
   derived module declares must `Match.FULL` on the real `api.main.app`.
3. `test_the_extractor_finds_a_swallowing_mount` / `test_the_extractor_ignores_a_loud_mount` —
   controls on the extractor itself: the swallowing shape is found, a re-raising handler is not.
4. `test_a_skipped_mount_boots_a_healthy_app_with_the_surface_missing` — the live control above,
   executed inside the suite: block the import, reload, assert the app still serves `/health` and
   that the detector reports the surface missing, then restore and assert the composition is clean.

## 4. Verification

### 4.1 The guard passes on the unmodified tree

```
$ python -m pytest tests/test_router_mount_completeness.py -q
4 passed in 1.22s
```

Route/app suites plus the architecture gate:

```
$ python -m pytest tests/test_router_mount_completeness.py \
    tests/test_canonical_frontend_routing.py tests/test_solspire_route_composition.py \
    tests/test_openapi_security_production_contract.py tests/test_production_health_route.py \
    tests/architecture -q
30 passed in 3.55s
```

### 4.2 Live negative control — the guard bites on the real file

`api/main.py` mutated in place (`from solspire.console_router_MISSING import ...`), suite re-run:

```
FAILED tests/test_router_mount_completeness.py::test_every_fail_open_mount_carries_its_routes_on_the_composed_app
FAILED tests/test_router_mount_completeness.py::test_a_skipped_mount_boots_a_healthy_app_with_the_surface_missing
E  Left contains 133 more items, first extra item: 'POST /solspire/workevents'
2 failed, 2 passed in 0.83s
```

Restored byte-identically (`cmp -s` -> identical) and re-measured clean. A synthetic fixture would
have proved only that the detector agrees with itself.

### 4.3 No regression — attributed by node identity, not counts

Both runs: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`
(`PYTHONPATH=<repo>/archive/legacy_python`).

| tree | result | failing/error nodes | node-set sha256 |
|---|---|---|---|
| `main` @ `fd0a4fdc` | 22 failed, 4251 passed, 22 skipped, 1 error | 23 | `d3ec2007ba81d6b9bcfbf6b2f35eecb6a54c51b1701674ac37bd94dfc1377c04` |
| branch head | 22 failed, 4255 passed, 22 skipped, 1 error | 23 | `d3ec2007ba81d6b9bcfbf6b2f35eecb6a54c51b1701674ac37bd94dfc1377c04` |

`comm -3` over the sorted node lists is empty — zero nodes only-on-branch, zero only-on-main. The
`+4 passed` is exactly this file's 4 collected nodes (`--collect-only` -> 4).

The 23 pre-existing failing/error nodes are unchanged by this change and each is owned by an open
PR or is environment-only; they are recorded in §5 rather than repaired here.

## 5. Pre-existing debt observed at `fd0a4fdc` (not attributable, not repaired)

- `tests/test_autonomy.py` — the sovereign-reserved CE-01 `weaver.autonomy` module/package
  collision (1 collection error).
- 10 x `tests/test_mission_lifecycle_adapter_contract.py` — environment-only: the adapter needs
  `web/arkadia_console/node_modules/typescript`, absent in a bare checkout.
- GOV-04 (`test_gov04_bounded_merge_delegation.py`), SolSpire R1/R3, Lab PR-state (2), M01/M02/M05,
  AIS W2, identity-spine W1, static-ingestion idempotency — each is touched by an open PR
  (#724/#725/#726, #693, #691, #683/#712, #700, #698).

## 6. Limitations

- The guard asserts *reachability*, not behaviour: it proves a mounted route answers the router's
  declared path, not that its handler is correct.
- The live control blocks `solspire.console_router` only. Every other fail-open mount is covered by
  the derived reachability assertion, not by an executed import failure; the reload path is shared,
  so the shape is proven once rather than twelve times.
- `api/main.py` is not modified by this change (budget: 2600 lines).

## 7. Authority

No merge, no push to `main`, no deployment, no production claim. The branch and this record are
proposed work; merge is human-only under GOV-03/GOV-04 and ARK-OPS-CONTINUOUS-001.
