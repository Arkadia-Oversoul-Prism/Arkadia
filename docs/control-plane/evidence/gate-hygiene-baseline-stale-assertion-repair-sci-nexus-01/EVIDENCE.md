# EVIDENCE — Gate hygiene: stale-assertion repair (SCI / nexus family)

- **Gate / workstream:** GATE-10 context — test-suite hygiene
- **Bounded task:** `SH-02`, first batch (the 6-node "nexus→novanet" family, baseline nodes 30–35)
- **BASE_MAIN:** `67a660c251af43159ea130b127fdc7040495501f`
- **Branch:** `gate-hygiene/baseline-stale-assertion-repair-sci-nexus-01`
- **Authority:** test-hygiene only. No source, policy, governance, or architecture mutation.
- **Status:** IMPLEMENTED (all targeted tests pass; full-suite delta verified; sovereign merge pending)

---

## 1. Scope

Repoints six string-level assertions whose targets were **relocated** by earlier
architecture passes. Each assertion's *governance intent* is preserved; only the
file-location assumption changed. Per `BASELINE_TEST_DEBT_CLASSIFICATION.md`
§§4.5 / Appendix A these were already classified `STALE_ASSERTION` (nodes 30–35);
this pass independently re-verified that classification against live source before
editing, then repaired the batch.

| file | nodes |
|---|---|
| `tests/test_weaver_sci_contract_01.py` | 2 |
| `tests/test_weaver_sci_boundary_01.py` | 3 |
| `tests/test_weaver_mvp2_08.py` | 1 |

## 2. Root causes (verified against live source, not assumed)

1. **Relocated workspace surface.** `SolSpireConsole.tsx` is now a 4-line re-export of
   `EnterpriseConsole` (`return <EnterpriseConsole {...props}/>`). The project
   workspace surface moved to `components/solspire/SolSpireExperience.tsx`, which
   mounts `ResilientProjectDashboard` → `pages/ProjectDashboard.tsx` (the canonical
   implementation, still asserted successfully by `test_m04_projects.py`).
   → re-point the two `"ProjectDashboard" in SolSpireConsole` assertions at
   `SolSpireExperience.tsx`.

2. **Ternary → explicit redirect.** `App.tsx` no longer contains
   `v === 'nexus' ? 'novanet'`. It now reads
   `if (requested === 'nexus') next = {view:'novanet',path:'/nexus'};`
   (line 114). Same mapping, different expression.
   → accept either expression.

3. **Marker relocation.** `WEAVER-SCI-BOUNDARY-01` is declared once, in
   `lib/sciCommandRegistry.ts` (the descriptive SCI registry, the canonical home for
   surface-ownership declarations), not in `components/ArkadiaNavigation.tsx`.
   → assert presence in either the nav component or the registry.

4. **Component reference change in `App.tsx`.** The canonical `novanet` view renders
   `NovaNetPage`; `NexusPage.tsx` (the hub hosting the tab surfaces) remains present as
   a file but is no longer imported by `App.tsx`.
   → assert `NovaNetPage` is rendered and that both page files exist.

## 3. Files changed

```
tests/test_weaver_mvp2_08.py         |  7 +++++--
tests/test_weaver_sci_boundary_01.py | 22 ++++++++++++++++++----
tests/test_weaver_sci_contract_01.py | 14 ++++++++++++--
3 files changed, 35 insertions(+), 8 deletions(-)
```

No production/source file was modified. `git status` after the pass lists exactly
those three test files.

## 4. Proof

### 4.1 Targeted

```
$ pytest tests/test_weaver_sci_contract_01.py tests/test_weaver_sci_boundary_01.py \
         tests/test_weaver_mvp2_08.py -q
35 passed in 0.12s          # was: 6 failed, 29 passed
```

### 4.2 Negative controls — the repaired assertions still have teeth

Each control mutates the *source* the assertion now watches, and the assertion must fail.
All three were run against the edited tests and then reverted (`git checkout --`).

| # | mutation | expected | observed |
|---|---|---|---|
| NC1 | delete the `requested === 'nexus'` redirect from `App.tsx` | 3 nodes fail | **3 failed** |
| NC2 | rename `WEAVER-SCI-BOUNDARY-01` in `sciCommandRegistry.ts` | 1 node fails | **1 failed** |
| NC3 | rename `ProjectDashboard` in `SolSpireExperience.tsx` | 2 nodes fail | **2 failed** |

This guards against the failure mode where a "stale assertion repair" quietly becomes
an assertion that can never fail.

### 4.3 Protected regression

```
$ pytest tests/architecture -q
11 passed in 1.19s
```
No architecture fitness test regressed (`LAYER_MAP` / registered-debt invariants intact).

### 4.4 Full-suite fingerprint — attributable, zero regressions

Both runs: `PYTHONPATH=<repo>/archive/legacy_python`, `-p no:cacheprovider`,
`--continue-on-collection-errors`, executed within the same hour.

| | main `67a660c` | this branch | delta |
|---|---|---|---|
| failed | 54 | 48 | **−6** |
| passed | 964 | 970 | **+6** |
| skipped | 10 | 10 | 0 |
| collection errors | 2 | 2 | 0 |
| failing/error nodes | 56 | 50 | **−6** |

Node-set diff (`comm` on sorted `FAILED`/`ERROR` node lists):

- **nodes removed — exactly the six targeted nodes**, nothing else;
- **nodes added — none** (no regression, no new flaky node).

## 5. Baseline reconciliation (recorded, not silently altered)

This pass measured the *live* `main` fingerprint at `67a660c`:

```
main := 67a660c   54 failed / 964 passed / 10 skipped / 2 collection errors   (56 nodes)
architecture := 11/11
```

Three documented baseline figures in the automation contract are **stale** and are
recorded here rather than edited:

| documented | measured at `67a660c` | note |
|---|---|---|
| `main := 6038989` | `67a660c` | many merges of drift; `6038989` is no longer `main` |
| `804 passed / 54 failed / 12 skipped` | `964 passed / 54 failed / 10 skipped` | passed count +160 (tests added since) |
| `architecture := 9/10` | `11/11` | now 11 checks, all passing |

The previously-run baseline at `a26af408` (49F/905P/12S/2E; 51 nodes) is consistent with
the trend: the repository has since *added* tests and nodes, and the fail count is stable
at 54 across the `a26af408`-era → `67a660c`.

`api/main.py` line budget: **2519 / 2600** (untouched). `python -m py_compile api/main.py`
passes.

## 6. Remaining uncertainty / not done here

- `SH-02` covers **35** stale-string nodes; this pass repairs **6** (the SCI/nexus
  family). The remaining **29** are untouched — `test_prism_pass_c_surface_ownership.py`
  (6), `test_ais_w2_living_gate_grove_handoff.py` (6),
  `test_solariun_experience_consolidation_01.py` (3), the spiral-grove copy family,
  `test_steward_filter.py` (3), and others.
- The `vite build` front-end check remains **environment-blocked** (no npm registry
  access in this sandbox). These are source-level string assertions over `.tsx` files,
  so they are inspection-verified here; the changed tests do not require a build.
- `SH-01` (`SOLSPIRE_PROJECTS_DB` env leak in `tests/test_echofeild_aggregator.py`) is
  **already resolved** on `main` (the file uses a module constant + `monkeypatch`), so
  the classification doc's "recommended first" item is closed. Not re-done.

## 7. Authorization

Test-hygiene only. No merge, no authorization, no identity-boundary change, no
governance or architecture reinterpretation. The sovereign decides whether this
becomes canonical.
