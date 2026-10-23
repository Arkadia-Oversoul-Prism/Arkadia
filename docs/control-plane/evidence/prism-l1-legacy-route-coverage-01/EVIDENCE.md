# Prism Lane 1 — legacy-route reconciliation & alias-safety guard (Slice A)

**Lane:** 1 (Shell / Navigation / Design System / Integration Seam)
**Directive:** `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` §3 (inventory
before redesign), §5/§9 (explicit, regression-protected route/shell decisions),
§5.1 (lenses), §5.2 (address-bar agreement); `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`
(exclusive file ownership).
**Base revision:** `main` @ `49809f45274f2f81b24e01fefdfb3009e8717495` (re-measured before the slice).
**Branch:** `feat/prism-l1-legacy-route-coverage-01`.

## Objective

Close two Lane-1 integration gaps, as a **contract/boundary guard** (not a feature):

1. **No reconciliation of the archived legacy route table against the console.** The
   archived Prism `App.tsx` declares 30 distinct inbound paths across its `direct` and
   `compatibility` maps. Nothing in `tests/` bound those paths to a console disposition,
   so a legacy path could be dropped with no failing test. The existing
   `test_console_shell_nav_contract.py` pins the aliases that were *added*
   (`/nexus`, `/oracle`, `/commune`); it does not bound the *domain*.
2. **No guard on the alias-safety precondition.** The Agent-01 instruction requires every
   candidate alias be verified against the served app's route table and the reserved-prefix
   set before it becomes a UI alias. No guard enforced that: an alias placed on a live
   backend namespace (`/api`, `/solspire`, …) would shadow it and pass every existing guard.

## Scope

- **New file only:** `tests/test_console_legacy_route_coverage.py`.
- No console source, `router.ts`, `surfaces.ts`, `App.tsx`, `endpoints.ts`, types, or the
  existing shell-nav test is edited — all are contended by open lane-1 PRs
  (#497 `/nexus/*`, #505 `/home` + `/knowledge-os`).
- This slice **records** the disposition of legacy paths whose reconciliation is a product
  decision; it does not add an alias for any of them.

## Files changed

| Path | Change |
|---|---|
| `tests/test_console_legacy_route_coverage.py` | new guard (8 tests, 5 with negative controls) |
| `docs/control-plane/evidence/prism-l1-legacy-route-coverage-01/EVIDENCE.md` | this record |

## What the guard asserts

- **Domain completeness:** the transcribed legacy route table equals the archive's route
  maps (`_archive_route_keys`), so a dropped legacy path leaves the domain visibly.
- **Total disposition partition:** every legacy path is a declared surface path, a live
  legacy alias, OR a recorded gap (`LEGACY_GAP_DISPOSITIONS`). The recorded set is a
  **floor** — a sibling lane adding a real alias stays covered and does not redden the union
  assertion.
- **Alias safety:** no alias or declared surface path shadows a served backend route
  (exact served path, reserved namespace, or served root segment). Root `/` is excluded: the
  SPA owns it and no backend route lives there.
- **Resolution is executed, not restated:** `_js_route_resolver` evaluates the live,
  dependency-free router in Node, so `/oracle → /arkana`, `/nexus → /novanet` are observed
  rather than pinned as source text.
- **Stale-ledger detection:** `test_deferred_legacy_paths_are_neither_aliased_nor_declared`
  fails if a recorded gap gains a route, forcing the ledger to be pruned.

## Recorded dispositions (this revision)

Aliased (also reconciled by sibling lane-1 PRs): `/nexus` (→ novanet; #497 extends the
sub-paths), `/oracle` (→ arkana), `/commune` (→ arkana), and pending in #505 `/home`,
`/knowledge-os`. Declared-surface paths: `/`, `/about`, `/login`.
Recorded gaps (23): `/gate`, `/living-gate`, `/codex`, `/dashboard`, `/loops`, `/settings`,
`/account`, `/personal-echofeild`, `/echofeild-matrix`, `/sci`, `/pulse`, `/reset`,
`/reasomate`, `/challenge`, `/future-skills`, `/encyclopedia`, `/spiral-codex`, `/offerings`,
`/home` (*), `/knowledge-os` (*), `/nexus/{ims,grove,larder,distribution}`.
(*) pending in #505; recorded here so the partition is total on this revision.

## Evidence and commands

Environment: sandbox, Python 3.12, `node` present, deps installed once
(`pip install -q -r requirements.txt`).

```
python -m pytest tests/test_console_legacy_route_coverage.py -q -rEf
  -> 8 passed

python -m pytest -q $(python scripts/console_contract_domain.py) -rEf
  -> 409 passed     (the derived console-contract domain, now 22 files)

python -m pytest tests/architecture -q
  -> 11 passed

python -m pytest tests/test_prism_console_ci_wiring.py -q -rEf
  -> 30 passed      (the content-derived domain now includes the new file; gate covers it)

printf 'tests/test_console_legacy_route_coverage.py\ndocs/.../EVIDENCE.md\n' \
  | python scripts/cp10_mutation_boundary_policy.py --judge
  -> Mutation boundary PASS
```

### Live negative control (proves the detector bites on the real file)

Mutated the **real** `web/arkadia_console/src/lib/router.ts` to add
`"/solspire": "home"` (a reserved backend namespace), then restored byte-identically:

```
python -m pytest tests/test_console_legacy_route_coverage.py -q -rEf
  -> 2 failed, 6 passed
     FAILED test_no_alias_or_legacy_path_shadows_a_served_backend_route
     FAILED test_detector_flags_an_alias_on_a_reserved_backend_namespace
     ('/solspire is under the reserved backend namespace /solspire')
# restore: git diff --stat web/arkadia_console/src/lib/router.ts  -> empty
python -m pytest tests/test_console_legacy_route_coverage.py -q
  -> 8 passed
```

## Regression boundary

- No baseline node is touched; the guard only *adds* nodes and reads existing sources.
- Console-contract domain: 409 passed (401 without the new file's 8 nodes).
- Architecture: 11 passed (unchanged).
- `api/main.py` untouched; no boot-code change, so `py_compile` is not required for this slice.

## Remaining uncertainty / authorization

- The guard does **not** decide the deferred product questions (e.g. `/codex` → Solariun
  `knowledge` lens vs. the `knowledge` surface); §3.4/§5.1 forbid inventing those. They stay
  recorded.
- `/nexus/{ims,grove,larder,distribution}` alias *extensions* are #497's slice; this guard
  records the current state and will keep the partition total when #497 lands.
- No merge, deployment, or acceptance is claimed. Draft PR only; human merges.
