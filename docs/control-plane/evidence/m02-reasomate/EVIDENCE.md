# M02 — ReasoMate Truth · Evidence

Trajectory: ARKADIA-TRUTHFULNESS-01
Move: M02 — reasomate-truth
Packet: conversational-field
Branch: `m02-reasomate-truth`
Repository SHA at start: `13df5f75348c313acef88504cbfcd1ea474c8f3c`
PR: #40
Implementation SHA: `742b2d3f64a8ca13f48e07bd11231b41fdc4d51c`
Merge SHA: `f3af072ae0d2f3a998cd9aa0528319046fa47983`
Status: **ACCEPTED / COMPLETE** — see `docs/control-plane/M02-CLOSURE.md`

> This artifact was written at `READY_FOR_REVIEW` and is preserved as written. The
> sections below describe the state at review time. Post-merge outcomes, the CI
> finding, and the closure basis are recorded in `M02-CLOSURE.md` and `ACCEPT.json`.

---

## 1. Authorization

| Field | Value |
|---|---|
| Move | M02 — ReasoMate Truth |
| Authority | Architect (explicit execution authorization, this session) |
| Scope ceiling | `docs/control-plane/moves/M02-reasomate.md` |
| Depends on | M01 — CLOSED / MERGED / ACCEPTED |
| Authorizes M03 | **No** |

No `ACCEPT.json` was written **at review time**. In this repository that file is the
*closure* marker (see `evidence/m01-persistence/ACCEPT.json`, written after merge).
Acceptance requires human review and a merge; writing it during review would have
misrepresented verification as acceptance. It was written after the merge, in the
separate closure commit, per the M01 precedent.

---

## 2. Orientation

| Item | Value |
|---|---|
| Trajectory manifest | `docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml` (M02 `pending`, `depends_on: [M01]`) |
| Weaver protocol | `docs/control-plane/WEAVER-RUN-PROTOCOL.md` |
| AEAS | `docs/control-plane/AEAS-v0.1.1.md` |
| M02 specification | `docs/control-plane/moves/M02-reasomate.md` |
| M01 closure | `docs/control-plane/M01-CLOSURE.md`, `evidence/m01-persistence/ACCEPT.json` |
| `main` HEAD | `13df5f75348c313acef88504cbfcd1ea474c8f3c` (matches stated M01 closure state) |
| Working tree at start | clean |
| First incomplete legal move | **M02** — derived from repository state, consistent with the router's expectation |

`git fetch origin main` confirmed `origin/main` == local HEAD; nothing newer existed.

---

## 3. Defect — verified, not assumed

Three independent collapses existed. All were read from the source at
`13df5f7` before any edit:

1. **Route alias.** `App.tsx` `resolvePath()` carried `'/reasomate': {view:'commune'}`
   in its *compatibility* map — the table reserved for legacy redirects. So
   `/reasomate` resolved to the **Oracle** view.
2. **Navigation collapse.** `App.tsx` `handleNavigate()` carried
   `if (requested === 'reasomate') next = {view:'commune', path:'/oracle'}` —
   the drawer entry and the Prism rail button both landed on Oracle.
3. **Wrong surface.** `ReasoMatePage.tsx` was a one-line re-export of
   `SocialFieldVerified` — the *public social field*, which renders the
   node-to-node messenger as its `reasomate` tab. `NovaNetPage.tsx` re-exported
   the same component, so the public feed and the private messenger were the same
   surface.

### 3.1 Repository history (why the surface was wrong)

The file's real history was retrieved via the GitHub API (the local clone is
grafted, depth 1):

```
b947afa2d6 2026-09-06  fix(reasomate): use verified compile-safe relationship field
1a0744854f 2026-09-06  fix(reasomate): use final self-contained relationship field
078c2ab3d2 2026-09-06  fix(reasomate): point messenger route at stable social field
a854c8250c 2026-09-06  fix(social): point ReasoMate route at canonical SocialField
c136990e25 2026-09-06  refactor(reasomate): route messenger through unified social field
7c728d22bf 2026-08-26  CONSOLIDATION PASS 09R: restore .../ReasoMatePage.tsx
```

At `7c728d22bf` the file was a 24.5 KB standalone Arkana messenger using the
canonical spine (`arkanaSessionId(profile?.uid)` + `/api/commune/resonance`) and
the real `/api/messages` DM substrate. A chain of five compile-error-driven
commits replaced it with a re-export of the social field. M02 restores the
**declared architecture**, using existing components rather than reinstating the
deleted page.

### 3.2 The declared architecture (in-repo doctrine)

- `docs/ARKADIA_CANONICAL_RUNTIME_CONTRACT.md` — the frozen path is
  `SURFACE (Oracle Chat | ReasoMate | NovaNet) → POST /api/commune/resonance`,
  with `session_id` "identical across all three surfaces".
- `docs/checkpoints/CS1_conversational_spine.md` — "ONE INTELLIGENCE SPINE.
  MANY INTERFACES"; authenticated surfaces resolve the same `session_id`, so a
  conversation begun in Oracle continues in ReasoMate.
- `docs/KNOWLEDGE_GRAPH_SPEC.md` — every product, ReasoMate included, is a
  **lens over the same underlying knowledge model**.
- `docs/verification/P1-A_PERSONAL_PRODUCTIZATION.md` — "ReasoMate gains a real
  A↔B message path", marked CODE-VERIFIED via `api/messages.py`.

M02 acceptance ("message send/load ... resolve to ReasoMate") therefore requires
**both** of ReasoMate's existing paths to be live behind its own route: the Arkana
conversation (shared spine) and private node-to-node messages (existing DM
substrate).

---

## 4. Implementation

Smallest change consistent with the existing architecture. No new backend, no new
store, no new identity, no new transport.

| File | Change |
|---|---|
| `web/public_prism/src/components/ReasoMateSurface.tsx` | **New.** The ReasoMate lens: composes the existing `ArkanaCommune` (canonical Oracle runtime) and the existing `SocialMessenger` (canonical `/api/messages` substrate). Auth-gated via existing `useAuth`. Owns no transport, no memory, no identity. |
| `web/public_prism/src/pages/ReasoMatePage.tsx` | Delegates to `ReasoMateSurface` (was a re-export of the public social field). |
| `web/public_prism/src/App.tsx` | Removed the `/reasomate → commune` compatibility alias; registered `/reasomate` as a direct route; added `reasomate: '/reasomate'` to `routeForView` (it previously fell through to `'/'`); deleted the `handleNavigate` Oracle collapse. |
| `web/public_prism/src/pages/NexusPage.tsx` | Public `novanet` tab no longer advertises "ReasoMate messenger"; ReasoMate has its own hub tab (already present). |
| `tests/test_m02_reasomate_truth.py` | **New.** 16 focused M02 tests. |

The NovaNet hub tab (`NexusPage`) and the direct route (`App.tsx`) now render the
**same** `ReasoMateSurface`, so the two entry points cannot drift apart.

### 4.1 Invariants honoured

- ReasoMate conversation uses the existing runtime: `ArkanaCommune` →
  `/api/commune/resonance`, keyed on `arkanaSessionId(uid)` → the shared
  `arkana-{uid}` thread in the existing Knowledge OS.
- Private messages use the existing `api/messages.py` JSONL substrate.
- No second chatbot, memory store, identity system, database, or conversational
  runtime. `ReasoMateSurface` contains no `localStorage`, no `fetch(`, and no
  auth-provider calls — asserted by test.
- Oracle remains Oracle: `/oracle` → `commune` → `ArkanaCommune`, unchanged.
- No backend file was modified.

---

## 5. Tests

Frontend has **no JSX test runner** (`web/public_prism/package.json` defines no
`test` script). The repository's established convention for asserting frontend
structure is source inspection — `tests/test_prism_interior_shell.py` does exactly
this. Backend authentication/isolation is exercised for real via `TestClient`.

### 5.1 Focused suite

`python3 -m pytest tests/test_m02_reasomate_truth.py -q` → **16 passed**

Covers: direct `/reasomate` route registration; `routeForView` mapping; absence of
the navigation collapse; Oracle separation; view mount distinct from Oracle; NovaNet
hub mounting the shared surface; both entry points sharing one surface; the public
feed tab not claiming the private messenger; reuse of the canonical runtime with no
second chat/message path; shared session key; no second memory store; no second
identity system; unauthenticated 401 on all three message endpoints; conversation
persistence (send → recipient thread → recipient inbox); cross-user isolation
(uninvolved node sees no conversation and no contents; sender always from auth).

### 5.2 Regression comparison

| Suite | Baseline (`13df5f7`, pre-change) | After M02 |
|---|---|---|
| Full suite | `45 failed, 682 passed, 10 skipped` | `45 failed, 698 passed, 10 skipped` |
| Diff of failing test IDs | — | **empty** (no new failures, none fixed) |

Run as `pytest tests/ -q --ignore=tests/test_autonomy.py --ignore=tests/test_render_codex.py`.
Those two files are pre-existing **collection errors**, present on the baseline and
recorded in `M01-CLOSURE.md`. The 45 pre-existing failures are likewise pre-existing
(weaver SCI/W5 boundary, `api/nodes.py` layer inversion, etc.).

M02 adds 16 passing tests and introduces no regressions.

### 5.3 Build

| Check | Result |
|---|---|
| `pnpm build` (pre-change baseline) | ✅ built in 7.30s |
| `pnpm build` (after M02) | ✅ built in 7.59s, 0 errors |

Toolchain note: the environment provided Node v22.23.2; `package.json` declares
`node: 24.x`. The build succeeded regardless. `pnpm` was activated via corepack at
the repo-pinned `10.26.1`.

---

## 6. Acceptance criteria

| Criterion | Result | Basis |
|---|---|---|
| `/reasomate` must not silently resolve to Oracle | **MET** | Alias removed; direct route added; test |
| Navigation resolves to ReasoMate | **MET** | `handleNavigate` collapse deleted; test |
| Direct route handling resolves to ReasoMate | **MET** | `routeForView` mapping; test |
| Authentication resolves to ReasoMate | **MET** | Existing `useAuth` gate; 401 verified on all message endpoints |
| Message send/load resolve to ReasoMate | **MET** | Existing runtime + DM substrate composed; persistence/isolation tested |
| Persistence through the existing runtime | **MET** | Send → thread → inbox verified; shared session key asserted |
| Private conversation remains user-scoped | **MET** | Cross-user isolation tested |
| No second chatbot/identity/memory/reasoning subsystem | **MET** | Surface owns no transport/store/identity; asserted by test |
| Existing runtime used | **MET** | `ArkanaCommune` + `api/messages.py` reused unmodified |

---

## 7. Known limitations

1. **No JSX test runner.** Frontend route assertions are source-inspection, the
   repository's existing convention. They are structural, not behavioural: they
   cannot prove the rendered DOM. They are paired with real `TestClient` coverage
   of the backend boundary. Adding a JSX runner is out of M02 scope.
2. **No live browser verification.** The route was not exercised in a running
   browser against a deployed backend. The build compiles and the route table is
   asserted, but render-time behaviour is unverified.
3. **`vault/*.md` test artifacts.** Running the suite generated untracked
   `vault/Ideas|Projects/*.md` files. They are test-run residue, not M02 changes,
   and are excluded from the commit.
4. **Pre-existing failures untouched.** The 45 pre-existing failures and 2
   collection errors remain. Repairing them is outside M02's scope (M01 recorded
   them as accepted limitations).
5. **Node version mismatch.** Built under Node 22 against a declared 24.x engine.
6. **`SocialFieldVerified` retains a `ReasoMate` tab.** It renders `SocialMessenger`
   (real DMs), not a second chat system, so it is not a parallel runtime. Renaming
   it is M03's public-field concern and was deliberately left alone.
7. **A historical standalone page was not reinstated.** M02 composes existing
   components instead, per the directive to extend rather than duplicate.

---

## 8. Next legal move

**M03 — NovaNet Public Field** (`docs/control-plane/moves/M03-novanet.md`),
`depends_on: [M02]`.

Reported only. Not executed, not authorized by this artifact. M02's acceptance
does not carry forward.

---

## 9. Constitutional non-claims

This record does not claim that M02 is accepted, approved, merged, or deployed;
that M03 is authorized; that the known limitations above are resolved; or that any
parallel database, filesystem, identity, memory, Knowledge OS, or conversational
runtime was introduced.

```text
IMPLEMENTATION  ≠ VERIFICATION
VERIFICATION    ≠ ACCEPTANCE
ACCEPTANCE      ≠ MERGE
MERGE           ≠ DEPLOYMENT
```

Merge is human-only. Deployment is human-only.

Recorded by: WEAVER (OpenHands agent) on behalf of the Architect.