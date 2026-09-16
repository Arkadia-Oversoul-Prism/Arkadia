# M03 — NovaNet Public Field — Acceptance-Readiness Verification

**Move:** M03 — novanet-public-field
**Trajectory:** `ARKADIA-TRUTHFULNESS-01`, version 4 (`authorized-for-review-gated-execution`)
**Verification authority:** Architect authorization (verification / acceptance-readiness pass only)
**Repository SHA inspected:** `9a0859468a88d7b84f30be3078582a1c00ab08fb` (`origin/main`)
**Verdict:** `READY_FOR_REVIEW`

> This record does **not** accept M03. Acceptance is a human (Architect) action. No
> `ACCEPT.json` was created for M03 by this pass.

---

## 1. Implementation / merge evidence

| Fact | Value |
|---|---|
| PR | #43 — "M03 — NovaNet Public Field" (merged) |
| Branch | `weaver/arkadia-truthfulness/m03-novanet` |
| Implementation commit | `773fcd9fbda71a5358528e3f0288c896f45bd2fb` |
| Merge commit | `17dc63d540246cd6dd0997487337c284de88268b` |
| Declared base | `8b26f990290470608a15814ea24ce9f9de605986` |
| Merged at | 2026-09-16T01:55:55Z |
| Moves merged after M03 | M04 (#44), M05 (#45), M06–M08 (#46), M09 (#47), trajectory v4 (#48) |

M03's complete change set (three files, 432 insertions / 49 deletions):

```
docs/control-plane/evidence/m03-novanet/EVIDENCE.md
tests/test_m03_novanet_public_field.py
web/public_prism/src/pages/SocialFieldVerified.tsx
```

`NovaNetPage.tsx` remains a one-line re-export of `SocialFieldVerified`, so the
routed surface and the implemented surface are the same file.

Repository status note: M03 is `status: pending` in the trajectory and
`reconciliation.merged_without_repository_acceptance_marker` lists M03 among
moves that "must not be promoted to accepted/completed for router purposes
without recorded acceptance evidence." This pass confirms that is still the
correct state.

---

## 2. Verification commands

Run at `9a0859468a88d7b84f30be3078582a1c00ab08fb`, and at baseline
`8b26f990290470608a15814ea24ce9f9de605986` (true pre-M03 `main`, the declared
PR #43 base) in a separate git worktree.

```bash
# focused
python3 -m pytest tests/test_m03_novanet_public_field.py -q

# related boundary suites
python3 -m pytest tests/test_m02_reasomate_truth.py tests/test_m02a_ci_gate_integrity.py \
                 tests/test_reasomate_handles.py tests/test_transmissions_ownership.py -q

# architecture
python3 -m pytest tests/architecture -q -p no:cacheprovider

# full regression (two modules fail to collect in this environment, see §4)
python3 -m pytest tests/ -q -p no:cacheprovider \
  --ignore=tests/test_autonomy.py --ignore=tests/test_render_codex.py

# build
cd web/public_prism && pnpm install --frozen-lockfile && pnpm build
```

---

## 3. Test / build results

| Check | Result |
|---|---|
| M03 focused suite | **8 passed** |
| Full suite @ main `9a08594` | **46 failed, 740 passed, 12 skipped** |
| Full suite @ baseline `8b26f99` | **46 failed, 705 passed, 10 skipped** |
| New failures introduced by M03 | **0** (failure sets identical: `comm -13` empty) |
| Frontend build | **PASS** — vite v5.4.21, 3422 modules, `dist/assets/index-IWK4pVbs.js` 1919.12 kB |
| Architecture layer boundaries | 1 failed / 10 passed — **pre-existing**, identical at baseline |

The full-suite comparison is the load-bearing result: the failing set at `main`
is byte-identical to the failing set at pre-M03 `main`, while 35 additional
tests pass. M03 introduces no regression.

Two failures appear only relative to the M02A-*merge* commit `634413e`, not
relative to the true pre-M03 parent `8b26f99`. Both are caused by the M02A
closure commit, not by M03, and both are present in the pre-M03 baseline:

- `tests/test_m02a_ci_gate_integrity.py::test_trajectory_next_move_is_m02a`
  asserts the router's next move is `M02A`; it now returns `M03` because M02A is
  marked `completed`. The assertion is stale by design of its own move.
- `tests/test_engineering_scheduler_bootstrap.py::test_dry_run_evidence` raises
  `TypeError: 'in <string>' requires string as left operand, not bool` — an
  operator-precedence bug in the test itself
  (`assert isinstance(...) and (...).startswith("M") in human.read_text()`).

---

## 4. Required-verification findings

**1. NovaNet renders as the public social field — PASS.**
`App.tsx` routes `view === 'novanet'` (and `/nexus`) to `NovaNetPage`, which
re-exports `SocialFieldVerified`. That component renders
`data-testid="novanet-public-field"` with a `PUBLIC FIELD` banner and a
`novanet-public-feed` region.

**2. Public posts/transmissions/interactions use existing social infrastructure — PASS.**
The feed reads and writes `/api/transmissions` (`GET`/`POST`), `/api/transmissions/{id}`
(`PATCH`/`DELETE`), and `/api/transmissions/{id}/react` and `/comment`. That
router (`api/transmissions.py`) is mounted from `api/main.py` under
`/api/transmissions`. No new feed endpoint or storage layer was introduced by M03.

**3. ReasoMate remains private and user-scoped — PASS.**
The NovaNet "ReasoMate (private)" tab (`data-testid="novanet-tab-reasomate"`)
mounts the same `ReasoMateSurface` component used by the `/reasomate` route, so
the two entry points cannot drift. `ReasoMateSurface` requires
`useAuth().isAuthenticated`, uses the canonical Arkana spine, and scopes its
Arkana session to the authenticated human via `arkanaSessionId(uid)` →
`arkana-{uid}` (`lib/arkanaSession.ts`). Unauthenticated users get an explicit
"ReasoMate is private" notice rather than the surface.

**4. Private memory / Knowledge OS state does not become public feed state — PASS (structural).**
`api/transmissions.py` persists only human posts plus a server-side profile
projection; there is no Knowledge OS read path in the public feed. Its module
docstring states the invariant: *"Human posts only… Private memory never
becomes a transmission implicitly."* `SocialFieldVerified.tsx` contains no
Knowledge OS import or `knowledge-os` reference. Knowledge OS is reached only
through the private `ReasoMateSurface`/Arkana path, which is the intended
boundary.

**5. No second social substrate — PASS for routed surfaces; residual dead code (see §6).**
The only reachable public-field surface is `SocialFieldVerified`. No dynamic or
lazy imports of any other social field exist, and `dist/assets/*.js` contains
zero references to `SocialFieldPage`. `SocialFieldPage.tsx` (16906 bytes) and
three re-export wrappers (`SocialFieldFinal`, `SocialFieldStable`,
`GovernedSocialField`) are unreachable and tree-shaken out of the bundle.

**6. No second identity substrate — PASS.**
Public author identity is projected server-side from the canonical profile
store: `api/transmissions.py::_profile_identity` calls
`api.auth.load_user_profile_store(uid)`, and `_author_block` treats
client-supplied identity as advisory ("Use verified profile identity when
available; client identity is advisory"). M03 added no profile store and the
composer passes `profile?.display_name` / `role_sigil` / `role` from the
existing `useAuth()` context.

**7. Authenticated users can distinguish public from private — PASS.**
Persistent tab strip "Public Field" / "ReasoMate (private)"; subtitle "Public
social field · private ReasoMate remains separate"; distinct testids
(`novanet-tab-public` / `novanet-tab-reasomate`); the private slot is
`novanet-private-reasomate-slot`; transmission vs. edit/delete affordances are
gated on ownership (`mine`).

**8. Existing M02 ReasoMate boundaries intact — PASS.**
`tests/test_m02_reasomate_truth.py`, `tests/test_reasomate_handles.py`, and
`tests/test_transmissions_ownership.py` all pass at `main`. `ReasoMateSurface`
retains its private markers and is still shared by both entry points.

**9. Build and focused tests — PASS.** See §3. The two modules that fail to
*collect* in this sandbox (`test_autonomy.py` needs `codex_brain`;
`test_render_codex.py` needs the same) are environment gaps, not M03 failures,
and were excluded identically from both the `main` and baseline runs.

**10. No protected-boundary changes — PASS.**
M03's three files touch no `weaver/` (K15/K3), `solspire/workevent*`,
provenance, `knowledge/`, `governance/`, `api/main.py`, or `kernel/` path
(verified by per-prefix match count = 0). No AEAS, authority, identity, memory,
or architectural-boundary semantics were modified.

---

## 5. CI state (context, not an M03 defect)

`main` currently carries a red `SG-02-FE.2-V` workflow, but **not** for the
mutation-boundary reason that motivated M02A.

- The **`CP10 mutation boundary` step now passes** — the M02A allow-list repair
  (PR #42) is effective. The harness-only allow-list defect no longer rejects
  product commits.
- The remaining failure is step `34 Enforce CP10 executable gates`. Its cause is
  the `browser` step logging `Error: /solspire auth threshold failed`: on push
  runs Firebase web config is absent, so the authenticated browser lens reports
  DEFERRED, `/solspire` cannot satisfy the `PRIVATE WORKSPACE` assertion, and
  `steps.browser.outcome` becomes `failure` while `Enforce` requires `success`.
- Note the `outcome` vs `conclusion` distinction: `browser` is declared
  `continue-on-error: true`, so the jobs API reports its **conclusion** as
  `success` and only the raw **outcome** (`failure`) trips `Enforce`. The failing
  assertion is visible in the run log as `test 'failure' = success` at the
  14th comparison, which is `steps.browser.outcome`.
- This is **pre-existing**: the identical `browser`/`Enforce` failure appears in
  runs 264 (M02A branch), 265 (M02A merge), and 266 (M03 branch) — i.e. before
  M03 landed. Across runs 264–273, `CP10 mutation boundary` is `success` in every
  run; only `Enforce CP10 executable gates` fails.

M03 neither caused nor repaired this. It is a Control Plane gate issue and is
out of scope for this verification pass.

---

## 6. Known limitations / unresolved risks

1. **M03's test suite is source-string-level, not behavioral.**
   All eight tests in `tests/test_m03_novanet_public_field.py` assert on
   `read_text()` output (8 `read_text()` calls). They prove that markers, imports,
   and the `/api/transmissions` string are present — not that the feed renders,
   posts, or that privacy holds at runtime. The privacy and no-second-substrate
   conclusions in §4 rest on this pass's independent code inspection, not on the
   committed tests.
2. **M03's own `EVIDENCE.md` is thin.** It records a base SHA but no
   implementation SHA, no verification commands, no test transcript, no baseline
   comparison, and no explicit verdict token. This record supplies those; the
   original remains unedited.
3. **Dead second social surface remains in the tree.** `SocialFieldPage.tsx` plus
   `SocialFieldFinal` / `SocialFieldStable` / `GovernedSocialField` wrappers are
   unreachable and tree-shaken. They do not affect runtime behaviour, but they
   are a standing invitation to reintroduce a second social substrate and are not
   covered by any test. Recommended for a later, separately-authorized cleanup.
4. **A stale test asserts the router's next move.** `test_trajectory_next_move_is_m02a`
   now fails because the router correctly advanced to `M03`. Left as-is because
   repairing it is M02A territory and is not an M03 defect.
5. **`main` is red for the pre-existing browser-auth reason** in §5. This is
   unrelated to M03 but means "CI green" cannot currently be used as acceptance
   evidence for any move.
6. The authenticated browser lens (`Authenticated Engineering Lab lens: PASS`) was
   never exercised on push runs, so no runtime browser confirmation of NovaNet
   exists in CI. Verification of §4 items 1 and 7 is therefore static (source +
   build) rather than runtime.

---

## 7. North-star test

1. **What human problem disappears?** A person no longer faces an undifferentiated
   "social" surface where public posting and private conversation occupy the same
   space without a stated boundary; the public field and the private messenger are
   now visibly different things.
2. **Which existing Arkadia surface becomes more truthful?** NovaNet. Previously
   the routed surface was a chain of compatibility wrappers over an unreachable
   `SocialFieldPage`; NovaNet now routes to the surface whose declared purpose is
   the public field.
3. **Which existing substrate does it reuse?** The `/api/transmissions` feed
   router and the canonical user profile store for public identity projection; the
   existing Arkana spine and `/api/messages` for private ReasoMate. No new storage,
   identity, or social substrate.
4. **What new continuity does it create?** One `ReasoMateSurface` instance is now
   shared by `/reasomate` and the NovaNet tab, so the private lens cannot diverge
   between entry points; public identity renders consistently from the profile
   store across all transmissions.
5. **What boundary must remain untouched?** The public/private line: Knowledge OS
   and private memory must never become public feed state, ReasoMate must stay
   user-scoped via `arkana-{uid}`, and K15/K3, provenance, WorkEvent semantics,
   authority and identity substrates must be unchanged. §4 items 3, 4, 6 and item
   10 confirm each.
6. **What observable evidence proves it works?** Routed-surface identity
   (`NovaNetPage → SocialFieldVerified`), the `novanet-public-field` /
   `novanet-public-feed` / `novanet-private-reasomate-slot` testids, reuse of
   `/api/transmissions` and `ReasoMateSurface`, absence of any Knowledge OS
   import on the public surface, absence of `SocialFieldPage` from the built
   bundle, 8 passing focused tests, a clean production build, and a full-suite
   failure set identical to the pre-M03 baseline.

---

## 8. Acceptance-readiness conclusion

**`READY_FOR_REVIEW`**

The implementation landed in `main` satisfies each invariant declared in
`docs/control-plane/moves/M03-novanet.md`, as independently verified above. All
acceptance-relevant checks pass, the production build succeeds, and M03
introduces zero new test failures relative to its own base SHA. No K15/K3,
provenance, WorkEvent semantic, authority, identity, memory, or architectural
boundary was touched.

M03 is **not** accepted by this record, and no `ACCEPT.json` was written. The
limitations in §6 — principally that the committed tests are source-string
assertions rather than behavioral ones, and that no runtime browser
confirmation exists in CI — are recorded so the Architect can decide whether
they must be addressed before granting acceptance.

**Not done by this pass:** no merge, no deploy, no trajectory edit, no M04+
work, no scope expansion, no self-authorization.

---

## 9. Next legal move

M03 remains the first legal incomplete move:
`select_next_move` returns **M03** (`test_trajectory_next_move_is_m02a` failing
on `assert 'M03' == 'M02A'` is independent corroboration). M04–M09 are landed in
`main` but likewise carry no repository acceptance marker and remain `pending`.

**Trajectory is unchanged.** M03 stays `pending` until the Architect acts.