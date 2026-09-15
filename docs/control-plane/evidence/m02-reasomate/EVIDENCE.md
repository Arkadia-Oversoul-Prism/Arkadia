# M02 — ReasoMate Truth · Evidence

Trajectory: ARKADIA-TRUTHFULNESS-01
Move: M02 — reasomate-truth
Branch: `weaver/arkadia-truthfulness/m02-reasomate`
Base: `main` @ `13df5f75348c313acef88504cbfcd1ea474c8f3c`
Status: **READY_FOR_REVIEW** (not accepted — human review remains mandatory)

Authorization: Architect granted explicit execution authorization for **M02 only**
following M01 closure. Merge and deployment were explicitly withheld.

---

## 1. The defect, established from repository state

`ReasoMatePage.tsx` was a two-line re-export of `SocialFieldVerified`, and the
router retargeted the ReasoMate surface at Oracle in two places:

| location | code (before) | effect |
|---|---|---|
| `App.tsx` compatibility map | `'/reasomate': {view:'commune'}` | deep-link `/reasomate` silently became Oracle |
| `App.tsx` `handleNavigate` | `if (requested === 'reasomate') next = {view:'commune',path:'/oracle'}` | every in-app ReasoMate navigation became Oracle |
| `App.tsx` `routeForView` | *(no `reasomate` entry)* | ReasoMate had no canonical path of its own |

Consequence: the `view === 'reasomate'` render branch at `App.tsx:151` was
**unreachable** from both deep-link and in-app navigation. `/reasomate` resolved
to Oracle, violating the first required invariant of the M02 specification:
*"`/reasomate` must not silently resolve to Oracle."*

The NovaNet hub tab (`NexusPage.tsx:899`) rendered `ReasoMatePage` correctly, so
the surface worked *inside* the hub but not on its own canonical route — the exact
asymmetry the M02 acceptance criterion targets.

## 2. What was changed (minimum set)

| file | change | why |
|---|---|---|
| `web/public_prism/src/App.tsx` | removed the `'/reasomate'` → `commune` compatibility alias | stop the silent Oracle redirect |
| `web/public_prism/src/App.tsx` | removed the `handleNavigate` ReasoMate → `/oracle` redirect | navigation resolves to ReasoMate |
| `web/public_prism/src/App.tsx` | added `reasomate: '/reasomate'` to `routeForView` | give the view its own canonical path |
| `web/public_prism/src/App.tsx` | added `'/reasomate': 'reasomate'` to the direct map | deep-links land on ReasoMate |
| `web/public_prism/src/pages/ReasoMatePage.tsx` | mounts `SocialFieldVerified` with `initialMode="reasomate"` | route lands on the *messenger* surface, not the public field |
| `web/public_prism/src/pages/SocialFieldVerified.tsx` | accepts an optional `initialMode` (default `'field'`) | one component, two windows |
| `tests/test_m02_reasomate_truth.py` | 10 focused assertions | lock the invariant |

`NovaNetPage.tsx` is **unchanged** — it still mounts the public field by default.

## 3. Architectural truth preserved

```text
Arkadia Identity (api/auth.py, Firebase)
        ↓
Shared Runtime (api/main.py)
        ↓
Knowledge OS (knowledge/)
        ↓
ReasoMate (api/messages.py — existing authenticated DM runtime)
        ↓
Persistent human ↔ Arkana thread
```

ReasoMate is a **lens over the existing Social Field component and the existing
`api/messages` runtime** — not a second one:

- no new component was created; `ReasoMatePage` and `NovaNetPage` mount the *same*
  `SocialFieldVerified`;
- no backend route, table, or file was added — `git diff main` touches **zero**
  files under `api/`, `kernel/`, `providers/`, `knowledge/`, or `solspire/`;
- conversation persistence remains `api/messages.py` → `data/messages/{pair}.jsonl`
  (JSONL over the existing filesystem, as already shipped);
- shared relational context remains derived (`api/social.py`
  `/api/relationships/{peer_uid}/context` reports
  `shared_memory_source: "reasomate.messages"` and returns nothing persisted);
- identity remains `api/auth.py` (Firebase) — no new identity path.

Backend audit for duplicate conversational substrates returned only the three
existing `/api/messages*` routes. No second chatbot, identity, memory, reasoning
system, database, or filesystem was introduced.

## 4. Private conversation remains user-scoped

Every ReasoMate route depends on `require_auth`, and the sender is always taken
from the authenticated principal:

- `POST /api/messages` — `sender = user["uid"]`; a caller-supplied `sender_uid` is
  ignored (covered by `tests/test_reasomate_handles.py`).
- `GET /api/messages/thread/{peer_uid}` — thread keyed on `{me, peer}`.
- `GET /api/messages/inbox` — filters to threads containing `me`.
- `GET /api/social/nodes` / `/api/relationships/{peer_uid}/context` — auth-gated.

The routing change does not widen this boundary; it only stops the UI from
presenting ReasoMate as Oracle.

## 5. Verification

| check | command | result |
|---|---|---|
| M02 focused suite | `pytest tests/test_m02_reasomate_truth.py -q` | **10 passed** |
| Route semantics (extracted from source) | see §5.1 | all correct |
| Frontend build | `pnpm build` | **exit 0**, built in 7.25s |
| Full suite | `pytest tests/ -q --continue-on-collection-errors` | 45 failed, 683 passed, 10 skipped |
| Routing test subset vs baseline | `diff` of failure sets | **identical (15 / 15)** |

### 5.1 Route resolution (asserted, not assumed)

| path | resolves to | note |
|---|---|---|
| `/reasomate` | `reasomate` | its own view — was `commune` |
| `/oracle` | `commune` | Oracle unchanged |
| `/nexus` | `novanet` | NovaNet unchanged |

Oracle and NovaNet are demonstrably **unaffected**: the M02 edit removed only the
ReasoMate entries and added only the ReasoMate path.

### 5.2 Regressions — distinguished honestly

Routing-related tests that fail on `main` (weaver SCI/W5 boundary, `test_prism_*`,
`test_weaver_sci_*`) fail **identically before and after** this change: the failing
set is byte-identical to the baseline (15 vs 15, `diff` empty). These are
pre-existing and unrelated to M02.

One additional failure appears in the full suite that is **not** caused by M02:
`tests/test_engineering_scheduler_bootstrap.py::test_dry_run_evidence` asserts
`next_move["id"] == "M01"`.

Proven provenance — reproduced by checking out the two commits:

| revision | M02 changes | result |
|---|---|---|
| `167a1a1` (M01 merge, before closure record) | absent | `1 passed` |
| `13df5f7` (M01 closure record committed) | absent (stashed) | `1 failed` |
| `13df5f7` + M02 working tree | present | `1 failed` |

The assertion is **stale by construction**: it hardcodes M01 as the next move, and
correct routing advanced to M02 precisely because M01 was accepted. It is an
expected consequence of the authorized M01 closure record, outside M02 scope, and
was deliberately **not** repaired — the M02 authorization forbids repairing
unrelated defects. It is recorded here for human review.

## 6. Constitutional non-claims

This move does **not** claim:

- that the M02 PR is merged or accepted (human review is the boundary);
- that M03 may begin (`docs/control-plane/moves/M02-reasomate.md`: *"Stop at
  review. Do not advance to M03 until M02 is accepted."*);
- that deployment occurred or is authorized;
- that ReasoMate was verified against a live backend — verification is
  source-level, test-level, and build-level; live conversational behaviour
  requires deployment authorization, which was not granted;
- that the stale `test_dry_run_evidence` assertion was resolved;
- that K15/K3, provenance semantics, WorkEvent semantics, AEAS, or trajectory
  authority changed — none were touched.

```text
EXECUTED  ≠ VERIFIED BY HUMAN
VERIFIED  ≠ ACCEPTED
ACCEPTED  ≠ MERGED
MERGED    ≠ DEPLOYED
```

**Next legal move:** M03 — subject to its own authorization, dependencies, scope,
and review gate. Not started.