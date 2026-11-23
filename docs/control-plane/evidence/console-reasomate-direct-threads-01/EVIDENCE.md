# ReasoMate direct threads — recovering an unsurfaced capability

**Workstream:** Prism UI reconciliation (lane 1 seam + recovered feature surface)
**Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d`
**Branch:** `feat/console-reasomate-direct-threads-01`
**Authority:** implementation, tests, evidence. No merge, no deployment, no acceptance
(GOV-03; ADR-016). Merge execution and production acceptance remain human-only.

## 1. The gap, measured

The archived Prism surface carried two lenses (`archive/frontend/arkadia-prism/web/public_prism/src/components/ReasoMateSurface.tsx`):

| lens | legacy behaviour | console before this change |
|---|---|---|
| Arkana conversation | shared Oracle spine, Knowledge OS memory | **present** as its own `/arkana` surface |
| Direct threads | private node-to-node messages over `/api/messages` | **absent** — no surface, no reader, no route |

The backend contract for the second lens is live and authenticated today
(`api/messages.py`, mounted in the canonical app; the startup log line is
`[MESSAGES] ReasoMate messaging router mounted at /api/messages`):

| handler | auth | response |
|---|---|---|
| `POST /api/messages` | `require_auth` | `{"message": {...}}` |
| `GET /api/messages/inbox` | `require_auth` | `{"conversations": [...]}` |
| `GET /api/messages/thread/{peer_uid}` | `require_auth` | `{"messages": [...], "peer_uid": ...}` |

So the capability was **UNSURFACED, not absent**: a user-facing product feature
with a working, authorization-gated backend and no way to reach it.

Two inventory rows describe the same capability as `Defer / MISSING`
(`docs/control-plane/overnight/PRISM-UI-INVENTORY.md`, `/reasomate`), which is
the status this change moves.

## 2. What changed

| path | change |
|---|---|
| `web/arkadia_console/src/pages/ReasoMatePage.tsx` | **new** — inbox, thread reader, composer |
| `web/arkadia_console/src/pages/reasomate/reasomateContracts.ts` | **new** — payload guards + thread semantics |
| `web/arkadia_console/src/pages/reasomate/reasomateContracts.test.ts` | **new** — 8 vitest nodes |
| `web/arkadia_console/src/lib/endpoints.ts` | `messages`, `messagesInbox`, `messagesThread()` |
| `web/arkadia_console/src/lib/surfaces.ts` | `reasomate` surface on `/reasomate`, `requiresAuth`, group `converse` |
| `web/arkadia_console/src/App.tsx` | one route case |
| `web/arkadia_console/src/components/Icons.tsx` | `IconReasoMate` (the icon map is `Record<SurfaceId, …>`, so a new surface cannot ship iconless) |
| `tests/test_console_reasomate_direct_threads_contract.py` | **new** — 14 guard nodes |

No backend change, no new dependency, no new store. The surface reads and writes
only the substrate `api/messages.py` already owns.

### Design decisions that are load-bearing

1. **Protected surface, not a redirect.** `requiresAuth: true` means the shell
   renders the sign-in threshold before the page mounts; the page itself never
   offers an anonymous view of private threads.
2. **Validate before render.** `GET /api/messages/inbox` and the thread handler
   both answer JSON; a failure envelope (`{"detail": ...}`) would otherwise be
   read as "no conversations". The guards reject it, and the page renders
   `ContractState` for every non-ready hydration state and `EmptyState` only for
   a *genuine* empty read — the two facts stay distinguishable.
3. **The thread base is derived, not declared.** `/api/messages/thread` is not a
   served route (the handler is templated on the peer uid), so declaring it in the
   endpoint registry would be an invented endpoint. `messagesThread(peerUid)`
   composes from `endpoints.messages`, and the guard asserts the bare prefix is
   *unserved* while `…/thread/<peer>` is served.
4. **The peer is taken from the handler's response.** `POST /api/messages` returns
   the stored message, so the surface opens the thread the backend named
   (`payload.message.recipient_uid`) rather than guessing how a `@handle` resolved.
5. **Direction is derived from the pair.** The substrate is pairwise
   (`data/messages/{pair_key}.jsonl`), so within one thread a message sent by the
   peer is inbound and everything else is the viewer's. No invented "current uid".

## 3. Verification (measured on this tree)

```
$ cd web/arkadia_console && corepack pnpm build
tsc --noEmit && vite build
✓ 172 modules transformed.
dist/assets/index-D-1VhPeq.js  433.34 kB │ gzip: 113.24 kB
✓ built in 2.29s

$ corepack pnpm exec vitest run
Test Files  9 passed (9)
     Tests  69 passed (69)

$ PYTHONPATH=$PWD:$PWD/archive/legacy_python python -m pytest \
    tests/test_console_reasomate_direct_threads_contract.py \
    tests/test_console_endpoint_registry_contract.py \
    tests/test_console_shell_nav_contract.py \
    tests/test_canonical_frontend_routing.py \
    tests/test_aeas05_canonical_frontend_acceptance.py \
    tests/test_prism_console_ci_wiring.py \
    tests/test_console_document_title_contract.py \
    tests/test_console_lens_landmark_contract.py \
    tests/test_console_unified_interface_contract.py \
    tests/test_prism_pass_c_surface_ownership.py \
    tests/test_console_surface_error_boundary.py \
    tests/test_m02a_ci_gate_integrity.py -q -rEf
278 passed in 10.78s

$ printf '<changed paths>' | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
```

### Negative controls (in the new guard, so the detector cannot pass by matching nothing)

| control | asserts |
|---|---|
| `test_the_negative_control_rejects_an_unprotected_declaration` | a declaration without `requiresAuth`, and one on the wrong path, both fail the same detector |
| `test_the_negative_control_flags_an_invented_path` | `/api/messages/threads` and `/api/reasomate` are **not** served — the served-path oracle is not trivially true |
| `test_the_negative_control_rejects_an_unvalidated_reader` | a reader that renders the payload without a guard is rejected |
| `test_the_negative_control_flags_a_fabricated_thread` | a hardcoded message array is rejected |

### Served-path oracle

The oracle is the app's own OpenAPI document (`app.openapi()["paths"]`), not a
route-table walk. A walk was tried first and measured wrong: the message router is
mounted through a composed wrapper whose nested routes expose no `methods`, so
the walk saw **none** of the three handlers while a Starlette `PARTIAL` match made
invented paths look served. Both defects were caught by this guard's own
assertions before the oracle was accepted.

## 4. Regression comparison

Full suite on this branch, same environment, `-rEf --continue-on-collection-errors`
(after the ledger prune described below, one node moved from FAILED to passed; the
full suite was **not** re-run after that prune — the file was):

```
$ python -m pytest tests/ -q -rEf --continue-on-collection-errors
10 failed, 4273 passed, 22 skipped, 6 warnings, 1 error in 286.36s (0:04:46)
```

The 11 failing/error nodes were:

```
ERROR   tests/test_autonomy.py
FAILED  test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED  test_console_legacy_route_coverage.py::test_deferred_legacy_paths_are_neither_aliased_nor_declared
FAILED  test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED  test_m01_persistence.py::test_deletion_propagates_to_durable_corpus
FAILED  test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED  test_m05_files.py::test_update_file_supports_rename
FAILED  test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED  test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED  test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED  test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip
```

**One of those nodes was introduced by this change, and it was the guard doing its
job:** `test_deferred_legacy_paths_are_neither_aliased_nor_declared` fails when a path
recorded as a reconciliation gap gains a route, and its message says exactly what to do
— *"prune `LEGACY_GAP_DISPOSITIONS`"*. The `/reasomate` entry was pruned (with a comment
recording the reconciliation), and the file then reads **20 passed**. A guard that
stayed green while a recorded gap gained a route would be the defect.

### Baseline, measured on the same environment

A detached worktree at `main` `bb19aabd` running the same ten files:

```
$ git worktree add --detach /tmp/ark/main-baseline bb19aabd…
$ python -m pytest <the same ten files> -q -rEf --continue-on-collection-errors
8 failed, 70 passed, 1 error in 3.46s
```

The branch reports the identical result on the identical file set:

```
8 failed, 70 passed, 1 error in 3.43s
```

Same nodes, same identities, **zero new failures**. Attribution is by node identity,
never by count.

`test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip`
fails **only** under full-suite ordering on this branch, and passes in isolation
(`2 passed in 0.12s`) and inside the ten-file set on both trees. That is the
order-dependent shared-runtime class already recorded for this suite; it is not
attributable to this change, which touches no `knowledge/` code.

## 5. Baseline node classification

| node(s) | classification | evidence |
|---|---|---|
| 10 × `tests/test_mission_lifecycle_adapter_contract.py` | **environment-only** | with `web/arkadia_console/node_modules` present the file reads `10 passed in 3.21s`; the earlier baseline without it reported ten failures |
| `tests/test_autonomy.py` (collection error) | **sovereign-reserved** | CE-01 `weaver.autonomy` module-vs-package collision |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | **sovereign-reserved** | a persistence-boundary decision recorded in the guard itself |
| `test_identity_spine_w1`, `test_m02_reasomate_truth` | covered by open PR #700 | |
| `test_m01_persistence`, `test_m05_files` | covered by open PR #690 | |
| `test_solspire_r1_governance_convergence` ×2 | covered by open PR #693 | |
| `test_solspire_r3_execution_runtime` | covered by open PR #691 | |
| `test_static_ingestion_idempotency` | order-dependent; covered by open PR #698 | |

**No uncovered repository defect remained in the test corpus at `bb19aabd`.** That is
why this cycle's implementation is a product-surface recovery rather than a test
repair: the open-PR queue already covers every attributable node.

## 6. Boundary classification (this pass)

| boundary | classification | evidence |
|---|---|---|
| current `main` resolved | **VERIFIED** | `GET /repos/.../commits/main` → `bb19aabd…`; local `HEAD` identical |
| source ↔ runtime consistency | **VERIFIED (revision only)** | `GET https://arkadia-qzu4.onrender.com/api/version` → `source_revision = bb19aabd…`, `revision_source = RENDER_GIT_COMMIT`, `revision_conflict = false` |
| served artifact ↔ local build | **OBSERVED, consistent** | served manifest `assets/index-CYGHeCpJ.js`; a clean local build of `bb19aabd` emits the same asset name |
| console build / typecheck | **PASS** | §3 |
| console unit tests | **PASS** | 61 → 69 nodes (+8, the new contract test) |
| advertised console endpoints served | **PASS** | all 44 literal registry paths resolve in `app.openapi()["paths"]` |
| Gate-2 `main -> deployment identity` | **UNKNOWN** | the harness reads GitHub *deployment records*; Vercel is disconnected, so it prints `UNAVAILABLE`. The runtime's own `/api/version` is authoritative but not consumed by that harness — see §7 |
| browser-rendered UI correctness | **NOT CLAIMED** | no browser observation this pass |
| production acceptance | **NOT CLAIMED** | human authority |

`/api/version` matching is necessary evidence of source↔runtime consistency. It
is not proof the application behaves correctly, and it is not acceptance.

## 7. Next unresolved blocker (recorded, not repaired)

`scripts/gate2_production_observation.py` reports `main -> deployment identity :=
UNKNOWN` and `newest Production deploy: UNAVAILABLE` on `bb19aabd`, even though the
canonical runtime publishes its exact revision. The harness queries GitHub
deployment records (the retired Vercel path) and does not consume
`GET /api/version`, which is the ADR-016 canonical origin's own identity probe.

**Not repaired here, deliberately:** that file is already contended by two open
drafts — #681 (marker-oracle app binding) and #687 (cold-start classification) —
and #703 has measured their composition. Adding a third branch to the same two
files would manufacture the conflict the repository forbids. The correct action is
to compose the `/api/version` consumer into whichever of those lands second, or to
open it as a fresh slice after both merge.

## 8. Non-claims

- No merge, no deployment, no production acceptance.
- No claim that the surface renders correctly in a browser; that is unobserved here.
- No claim about `POST /api/messages` behaviour against a live production
  identity — the write path is pinned by source-level contract and by the
  handler's own response shape, not by a live send.
- The 26 open draft PRs are unchanged by this work; only one contended file pair
  (#681/#687) exists among them, and it is already measured by #703.
