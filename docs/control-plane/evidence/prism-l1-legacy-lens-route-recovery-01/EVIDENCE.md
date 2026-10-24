# PRISM-L1-LEGACY-LENS-ROUTE-RECOVERY-01 — FU-1 deep-link recovery

**Lane:** 1 — shell / navigation / design system / integration seam
**Branch:** `feat/prism-l1-legacy-lens-route-recovery-01` (branched from live `main`)
**Scope:** `web/arkadia_console/src/lib/router.ts` + two lane-1 guard files
**Status:** `IMPLEMENTED` — targeted guards green, build green, architecture 11/11
**Authorization:** none required. Draft PR only; no merge, no deploy, no acceptance.

---

## 1. The defect (FU-1, restated from its own entry condition)

`/encyclopedia` and `/spiral-codex` are distinct inbound paths in the archived Prism's
`direct`/`compatibility` route maps. Both were routed to `NexusSpiralCodex`, which the
console expresses as the NovaNet **`codex`** lens. On this revision neither had any route
in the console, so `resolvePath` fell through its final `return { surface: "home", path: "/" }`
and both deep links landed on Home — a real archived link silently discarded.

The disposition ledger recorded both as reconciliation **gaps** with an explicit reason:

> "the alias table maps one path segment to a surface, and this path needs a default lens"

That is the whole defect. `PATH_ALIASES: Record<string, SurfaceId>` cannot express
*surface + lens*: an entry would resolve `/encyclopedia` to NovaNet **without** selecting the
`codex` lens — the right surface showing the wrong view, which is a different bug wearing the
shape of a fix. FU-1 explicitly forbids that entry.

## 2. The repair

`router.ts` gains a second, differently-shaped alias table:

```ts
export const LENS_ALIASES: Record<string, { surface: SurfaceId; section: string }> = {
  "/encyclopedia": { surface: "novanet", section: "codex" },
  "/spiral-codex": { surface: "novanet", section: "codex" },
};
```

and `resolvePath` resolves it **before** the segment branch (a lens alias carries a section,
so it must not reach the surface-default branch first):

```ts
const lens = LENS_ALIASES[path];
if (lens) {
  return { surface: lens.surface, section: lens.section,
           path: routeForSurface(lens.surface, lens.section) };
}
```

`routeForSurface` is used rather than string concatenation so the emitted path is exactly the
one the resolver reads back — `useRouter` writes that path to the address bar on load, and an
emitted form the resolver cannot re-read would reintroduce the silent rewrite this slice
prevents.

**Exact paths only.** The archive declared these as exact routes with no sub-paths, so
`/encyclopedia/x` matches nothing and still falls through to `home`. The new branch cannot
become a catch-all.

## 3. Evidence

### 3.1 Resolver behaviour (executed in Node against the real module, not pinned as text)

| probe | resolves to | note |
|---|---|---|
| `/encyclopedia` | `/novanet/codex` | was `/` |
| `/spiral-codex` | `/novanet/codex` | was `/` |
| `/encyclopedia/` | `/novanet/codex` | trailing slash normalises as for every other alias |
| `/encyclopedia/x` | `/` | control: exact paths only |
| `/spiral-codex/a/b` | `/` | control |
| `/invented` | `/` | control: branch is not a catch-all |
| `/oracle`, `/nexus` | `/arkana`, `/novanet` | pre-existing aliases unchanged |

### 3.2 Guards and their negative controls

`tests/test_console_legacy_route_coverage.py`
- `LEGACY_GAP_DISPOSITIONS` **pruned** of `/encyclopedia` and `/spiral-codex` — the recorded
  gap is closed, and `test_deferred_legacy_paths_are_neither_aliased_nor_declared` would have
  failed had the ledger been left stale.
- `_lens_aliases()` parses the new table; the disposition partition
  (`test_every_legacy_path_has_a_reconciliation_disposition`) now names it as a bucket, with
  new assertions that a lens alias duplicates neither a declared surface path nor a plain
  alias key.
- `test_lens_aliases_reconcile_a_path_that_would_otherwise_be_silent_loss` binds the table to
  the two paths and asserts each is no longer recorded as a gap.
- The shadowing guard now checks lens-alias paths too — `/encyclopedia` and `/spiral-codex`
  were verified against `app.openapi()`: neither is a served route, and neither shares a root
  segment with one (`/encyclopedia ok []`, `/spiral-codex ok []`).
- `test_detector_flags_an_unaccounted_legacy_path` **caught the omission on first run**: its
  restated partition lacked the lens-alias bucket and reported a false gap. That is the
  control working, and the fix names every bucket the live assertion uses.

`tests/test_console_shell_nav_contract.py`
- New probes threaded through the existing resolver harness: `/encyclopedia`, `/spiral-codex`,
  `/encyclopedia/`, `/encyclopedia/x`, `/spiral-codex/a/b`, plus the re-read canonical-path list.
- `test_legacy_lens_routes_resolve_to_the_lens_they_addressed` asserts the **whole** route
  (surface *and* section), and that neither path is in `PATH_ALIASES` or `SURFACES`.
- `test_lens_alias_round_trips_through_the_surface_route_helper` executes `routeForSurface`.
- Three negative controls, each mutating the **real** `router.ts` text and asserting the
  detector fires: a lens-losing entry (`section: ""` → resolves `/novanet`, the exact shape
  FU-1 forbids), a section that is actually a surface id, and a lens alias to an undeclared
  surface. Each asserts the mutation landed, so a detector cannot pass vacuously.
- `test_an_unknown_legacy_path_still_falls_through_to_home` is the catch-all control.

### 3.3 Commands

| command | result |
|---|---|
| `python -m pytest tests/test_console_shell_nav_contract.py -q -rEf` | **44 passed** |
| `python -m pytest tests/test_console_legacy_route_coverage.py -q -rEf` | **9 passed** |
| both files together | **53 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build` | **exit 0** (`dist/assets/index-DmlGhg5F.js`) |

## 4. Ownership and collision check

Lane 1 owns `lib/router.ts` (`SHARED-CONTRACTS.md`). Measured against the live open-PR queue:
of the 17 open PRs, **one** touches a lane-1 shell file — #550
(`integration/console-arkana-shell-recovery-01`) touches `App.tsx`. **No open PR touches
`lib/router.ts`.** This slice touches `router.ts` and two lane-1 test files, so it collides
with nothing in flight.

## 5. What this does NOT claim

- **Not** production acceptance. No deployment was made or observed. `/encyclopedia` on the
  canonical origin is unchanged until an authorized merge and Render's auto-deploy.
- **Not** a claim about the NovaNet `codex` lens's own rendering — that capability was
  reconciled in #560 and is out of this slice's scope.
- The remaining `LEGACY_GAP_DISPOSITIONS` entries are **untouched**: FU-2 (`/api/ims/*`),
  `/codex`, `/dashboard`, `/loops`, `/settings`, `/account`, `/personal-echofeild`,
  `/echofeild-matrix`, `/sci`, `/pulse`, `/reset`, `/reasomate`, `/challenge`,
  `/future-skills`, `/offerings`, and the four `/nexus/*` sub-views all stay product decisions
  or UNKNOWN contracts. This slice closes exactly one recorded gap.

## 6. Next bounded task

Lane 1, next pulse: the **deferred instruction-doc drift repair** — `AGENT-01-SHELL.md` §1
still points at a lane-state refresh against `base_main 7580bd8f`, which is now behind live
`main` `68acf89f`. `scripts/lane_state.py --check` currently passes (23 passed in
`tests/test_lane_instruction_doc_currency.py`), so the repair is a snapshot refresh, not a
failing guard — measure before editing.

---

## 7. Baseline attribution (measured, not inherited)

One full-suite pass at branch head `ff799cf9`, the only one this pulse:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
-> 8 failed, 3435 passed, 20 skipped, 3 warnings, 1 error in 246.95s
```

**Failing/error node set — 9 nodes**, sorted, `sha256 c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`:

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

**Every one of the nine was reproduced on `main` in a detached worktree** (targeted runs, not a
second full pass):

| node group | on `main` `68acf89f` |
|---|---|
| `test_engineering_lab_api.py` (2) | `2 failed, 15 passed` |
| `test_ais_w2…`, `test_identity_spine_w1…`, `test_m02_reasomate_truth…`, `test_solspire_r1…` (2), `test_solspire_r3…` | `6 failed, 3 passed` |
| `test_autonomy.py` | the CE-01 `weaver.autonomy` module-vs-package collection error, sovereign-reserved |

**Attribution: zero delta.** None of the nine is caused by this slice, and this slice repairs
none of them — they are recorded pre-existing debt, not silently fixed. The `+53` on the two
guard files is exactly this slice's own tests (`--collect-only`: 44 + 9).

## 8. Collision check, measured against the live queue

18 open PRs at the time of measurement (17 before this one). A per-PR `gh pr diff --name-only`
sweep over every open PR:

| lane-1 shell file | open PRs touching it |
|---|---|
| `web/arkadia_console/src/lib/router.ts` | **none** before this PR; #562 is the only one |
| `web/arkadia_console/src/App.tsx` | #550 only |
| `lib/surfaces.ts`, `lib/endpoints.ts`, `lib/types.ts`, `components/SurfaceLenses.tsx` | none |

So this slice collides with nothing in flight: `router.ts` is uncontended, and the one
contended lane-1 file (`App.tsx`, #550) is untouched here.

## 9. CI, at head `98e8b01b` (runtime-observed, not asserted)

`gh pr checks 562` -> **15 successful, 0 failing, 0 pending**. The load-bearing ones:

| check | meaning for this slice |
|---|---|
| `Prism Console Contract/console-contract` | executes the lane-1 shell/nav contract in CI, so the new guards are gated, not local-only |
| `SG-02-FE.2-V/validate` | CP10 mutation boundary — the changed paths are legitimate repository surfaces |
| `N-ATLAS Developer Lab/frontend` | the console builds in CI, not only locally |
| `security-secret-scan/Full-history secret scan` | clean |

The remaining checks (`boot-syntax`, `backend`, `test`, `provider-forensics`, the N-ATLAS beta
and Render-image jobs) pass and are untouched by a router-only change.

This is a **repository-source** claim: CI proves the guards and the build. It is **not** a
production observation — the codex lens's served rendering is FU-3, after a merge.
