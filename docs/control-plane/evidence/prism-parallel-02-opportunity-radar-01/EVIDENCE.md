# Evidence — Project Opportunity Radar feature module (Workstream 2, slice 1)

**Bounded objective:** verify the project/opportunity API contract against current
backend source; record a capability matrix; implement an **opportunity-only**
feature module and test in **new, non-overlapping** files if a real contract
supports it.

**Branch:** `feat/prism-parallel-02-novanet-opportunity` (draft PR #420)
**Baseline `main` observed at the start of the pass:** `8dcb78d2`
**Authority:** inspection, implementation on the owned branch, test, commit.
No merge, deployment, or acceptance. Render is canonical under ADR-016.

---

## 0. Concurrent-commit reconciliation (mid-pass branch move)

While this pass ran, the remote branch advanced `920aa110` → `dd7d174f`
("feat(opportunities): add project-scoped radar read surface"), authored by the
**coordinator account** `Arkadia-Oversoul-Prism`. It landed a **different** file
at the exact path this pass had used: a read-only, prop-driven
`ProjectOpportunityRadar.tsx` (133 lines, takes `readPath`, no capture control).

Reconciliation, per `SHARED-CONTRACTS.md` §4 ("no agent rebases or force-pushes
another agent's branch"; "preserve history"):

- The landed surface is **kept byte-identical** (blob
  `67e47b5c009ceacd5af8fe270203f33f05ac3f3f`, unchanged from `dd7d174f`). This
  pass does not overwrite another workstream's landed file.
- This pass's additive contributions are retargeted to complement it:
  `opportunityRadarContract.ts` supplies the project-scoped `readPath` the landed
  surface consumes, and the tests assert against the **landed** surface's real
  state machine and client usage.
- This pass's own full surface (capture/advance controls) was **not** re-landed
  — the landed read-only design is the coordinator's, and defect 2 below makes a
  capture control non-functional anyway. Recorded as a proposal, not re-pushed.

Result: this commit is purely additive on top of `dd7d174f` — a contract module,
a backend-verification test, and two docs.

---

## 1. Revision binding and overlap gate

| Fact | Value |
|---|---|
| `origin/main` at pass start | `8dcb78d2` |
| Branch head at pass start | `920aa110` |
| PR #418 (NovaNet slice) state | open, **draft**, unmerged, head `34c9a58b` |
| PR #419 (shared contract) state | **merged** @ `a29a9b8f`; contract read from `origin/main` |

**Overlap gate honoured.** PR #418 modifies `NovaNetPage.tsx`, `endpoints.ts`,
`types.ts`, `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, `SurfaceLenses.tsx`,
`tests/test_console_shell_nav_contract.py`. **None of those paths were touched.**
Every file added by this slice is new and outside #418's diff:

| Path | Status |
|---|---|
| `web/arkadia_console/src/components/opportunities/opportunityRadarContract.ts` | new |
| `web/arkadia_console/src/components/opportunities/ProjectOpportunityRadar.tsx` | new |
| `tests/test_prism_opportunity_radar_module.py` | new |
| `docs/control-plane/parallel-ui/CAPABILITY-MATRIX-02.md` | new |
| `docs/control-plane/evidence/prism-parallel-02-opportunity-radar-01/EVIDENCE.md` | new (this file) |

The module declares **no route and no surface**, so the canonical route registry
(`lib/surfaces.ts` / `lib/router.ts` / `App.tsx`) is untouched. Integration is a
request to Workstream 1, not an edit (§5).

## 2. Contract discovery (measured, not assumed)

Read from current backend source and cross-checked against the deployed
`GET /openapi.json` at `https://arkadia-qzu4.onrender.com`:

- `solspire/buyer_recon_router.py` — 6 project/workspace routes, `require_auth`
  and `require_project_owner`.
- `solspire/buyer_recon.py` — `STATUSES` (11), the `UNKNOWN` default for an
  unverified commercial fact, the `buyer_recon_boards` / `buyer_recon_entries`
  schema, and the manager methods.
- `solspire/console_router.py:51` — `/solspire` router carries
  `dependencies=[Depends(require_auth)]`.
- `api/auth.py:421,446` — `get_current_user` is optional; `require_auth` raises
  `401 "Authentication required"`.
- Live probe: anonymous `GET /solspire/buyer-recon` → **401**.

Full route/auth matrix: `docs/control-plane/parallel-ui/CAPABILITY-MATRIX-02.md`.

## 3. Two measured defects found during discovery

Neither was repaired: both live in `solspire/buyer_recon.py`, outside this
workstream's owned paths.

**Defect 1 — entry create arity mismatch.** `create_entry` passes 34 values into
a 33-column table → `sqlite3.OperationalError` → HTTP 500 on every create.
Reproduced directly against the manager (no HTTP) and through the route.

**Defect 2 — one board per subject.** `buyer_recon_boards.subject_ref` is
`UNIQUE` while the project board is keyed on the composite
`{workspace}:project:{id}`. The second scope read for one subject raises
`sqlite3.IntegrityError: UNIQUE constraint failed` → HTTP 500. Since the
workspace board is the natural first read, **the project radar is unreachable
for that subject** — this is the blocker for the project-level slice.

Both introduced at `5de6d476` (PR #199, 2026-10-02). Both are pinned by the new
test as the *current* measured state, so a repair is a deliberate, visible change
rather than a silent one. Full detail and the deferred register:
`CAPABILITY-MATRIX-02.md` §3.

## 4. What was implemented

**Added by this commit (all on top of the landed `dd7d174f`):**

`opportunityRadarContract.ts` — the pure contract model the landed surface
depends on:

- the backend `STATUSES` vocabulary, the `UNKNOWN` unverified-fact sentinel, and
  the `NONE` evidence sentinel, all lifted from `solspire/buyer_recon.py`;
- the declared project-scoped paths (`projectBoardPath`, `projectEntriesPath`,
  `projectEntryPath`) — the exact value the landed surface's `readPath` prop
  takes;
- handler-derived response shapes (`ProjectOpportunityBoard`, `authority`,
  `persistence`) and a `summarize()` that counts real entries only, so an empty
  board stays visibly empty.

**Already landed (not this commit):** `ProjectOpportunityRadar.tsx` — a read-only,
prop-driven surface with distinct loading / auth / unavailable / error / ready
states and no execute or spend control. It is kept byte-identical.

**Not re-landed:** this pass originally built a surface with capture/advance
controls. It was dropped in the reconciliation (§0): the landed read-only design
is the coordinator's, and defect 2 makes any capture control non-functional for a
subject who has opened the workspace board. Recorded as a proposal instead.


## 5. Integration request to Workstream 1 (not an edit)

To surface the landed read-only module inside a project view, the shell owner
would pass the contract module's path builder — no shared file change beyond one
import and one render:

```tsx
import { ProjectOpportunityRadar } from "../components/opportunities/ProjectOpportunityRadar";
import { projectBoardPath } from "../components/opportunities/opportunityRadarContract";
// <ProjectOpportunityRadar readPath={projectBoardPath(project.id)} />
```

No route, surface id, endpoint constant, or shared type is requested: the
contract module carries its own paths and types, and reads only
`/solspire/buyer-recon/*`, which is already in the deployed contract. **Do not
integrate until defects 1 and 2 are repaired** — the read path 500s for any
subject who has already opened the workspace board (defect 2).

## 6. Verification (measured in this environment)

| Check | Command | Result |
|---|---|---|
| New module tests | `python -m pytest tests/test_prism_opportunity_radar_module.py -q -rEf` | **19 passed** |
| Typecheck | `corepack pnpm exec tsc --noEmit` | exit 0 |
| Build | `corepack pnpm exec vite build` | exit 0 — 62 modules, `dist/assets/index-BEA7SQH_.js` 30.84 kB |
| Architecture fitness | `python -m pytest tests/architecture -q` | **11 passed** |
| Targeted console guards | `test_frontend_arkadia_console_rebuild_01` + `test_canonical_frontend_routing` + `test_aeas05_canonical_frontend_acceptance` + this module | **47 passed** |
| CP10 mutation boundary | `printf '<5 new paths>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | PASS (exit 0) |

Negative controls: the auth detector is proven to fire without an identity and
to pass with one (same path); the ownership pin is proven to fire for a
non-owner; the frontend source detectors were proven to bite on an injected
hardcoded origin and on a removed authority read.

### 6.1 Baseline comparison — zero node-set delta

Both trees measured in **this environment**, same command, same dependency set:

| | `main` @ `8dcb78d2` (worktree) | branch @ `c030ccfb` (rebased) |
|---|---|---|
| Failing/error nodes | 19 | 19 |
| Node-set sha256 | `204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b` | same |
| `comm -3` | — | **empty** |
| Passed | 2137 | 2156 (**+19**) |

The `+19 passed` is exactly the new file: `--collect-only` on
`tests/test_prism_opportunity_radar_module.py` → **19 collected**, and that file
does not exist on `main`. No new failing node; no repaired node. The regression
claim is the node-set identity, never the absolute count. (`dd7d174f`'s landed
surface adds no Python node — it is `.tsx`.)

The 19 pre-existing nodes (recorded, **not repaired** — none is in this slice's
paths): `tests/test_autonomy.py` (CE-01 collection error), 2 ×
`test_engineering_lab_api.py`, 6 × `test_voice_context.py`, 2 ×
`test_voice_pipeline.py`, 2 × `test_solspire_r1_governance_convergence.py`, and
one each in `test_ais_w2_living_gate_grove_handoff`, `test_identity_spine_w1`,
`test_solspire_r3_execution_runtime`, `test_static_ingestion_idempotency`,
`test_static_ingestion_sources`.

### 6.2 Reproducibility

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

Run on both trees from a clean checkout of the respective revision. `-rEf` (not
`-rf`) so a collection `ERROR` line is not silently dropped from the extractor.

## 7. Unknowns and next move

**Unknown / not tested**

- The exact behaviour of capture/advance **after** defects 1 and 2 are repaired —
  the read path is measured; the write path cannot execute today.
- Whether a repaired `subject_ref` constraint should be composite
  (`(subject_ref, workspace_ref)`) or the project board should be keyed
  differently — a design decision for the repair owner, not asserted here.
- Runtime observation of this module inside a hosted page: it is not routed, so
  there is no browser observation. That is correct for a draft slice.
- Distribution's unauthenticated routes: recorded, not repaired, not adjudicated.

**Next move (exactly one):** open the sovereign-owned repair for
`solspire/buyer_recon.py` (defect 1: drop the extra value / add the missing
column; defect 2: make the board uniqueness composite) as a separate proposed
workstream, and only then request the Workstream 1 integration for this module.
