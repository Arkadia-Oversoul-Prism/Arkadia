# ARK-OPS-CONTINUOUS-001 — cycle 23: the home portal grid printed five labels twice

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Base:** `main` @ `aef655423433070e581b42c246fa9298234eb460` (`#724`, 2026-11-25)
**Measured:** 2026-11-26, this workspace
**Authority:** read-only against GitHub and production, plus one local source change, one local
test run, and one local build. No merge, no push to `main`, no deployment, no acceptance. Merge
authority is `NONE` under this contract; `#679`'s green checks are not a merge authorization and
were not acted on.

---

## 1. Reconstructed state — `main` moved one commit since cycle 22

| fact | measured value | how |
|---|---|---|
| canonical `main` | `aef655423433070e581b42c246fa9298234eb460` | `git rev-parse origin/main` |
| previous cycle's `main` | `fd0a4fdc…` | cycle 22 evidence |
| open PRs | **61** — **60** drafts, **1** ready (`#679`) | `GET /pulls?state=open` |
| `scripts/lane_state.py --check --verify-live` | exit **0**; doc-guard lanes `['1','2','3','4']`; none deferred | live run against GitHub |
| full suite | `22 failed, 4251 passed, 22 skipped, 1 error in 290s` — **23** failing/error nodes | `-q -rEf --continue-on-collection-errors` |

The failing/error set is **identical to cycle 22's**, and every node is owned, reserved, or
environmental (section 4). `main` moved by one docs commit, so that classification carries.

## 2. Production — source revision and served artifact

```
GET /api/version   200
  source_revision   aef655423433070e581b42c246fa9298234eb460
  revision_source   RENDER_GIT_COMMIT
  revision_conflict false
```

The canonical origin serves the build of current `main`. This is **revision consistency**, not
application correctness and not acceptance.

Anonymous surface reachability, probed with `Accept: text/html,…` (SPA mode):

| path | status | note |
|---|---|---|
| `/`, `/workspace`, `/novanet`, `/arkana`, `/solariun`, `/projects`, `/engineering-lab`, `/knowledge`, `/weaver`, `/settings`, `/operator`, `/about`, `/login`, `/n-atlas-lab`, `/enterprise` | 200 | every declared surface path serves the SPA |
| `/solspire` | **404** | **expected**: reserved backend namespace; the surface path is `/enterprise` |

`/engineering-lab` renders `Protected surface` / `Sign in to continue` anonymously — the honest
threshold, not a blank page. This is the first cycle since 22 to drive the canonical origin in a
browser.

## 3. The defect this cycle closes — a duplicated label on the home portal grid

Observed on `https://arkadia-qzu4.onrender.com/` at `aef65542`, then traced to source.

`web/arkadia_console/src/lib/surfaces.ts` declares `boundary` as "the product boundary this
surface belongs to" and `name` as the surface name. `HomePage.tsx`'s `Portal` card rendered the
boundary as an eyebrow above the name unconditionally:

```tsx
<p className={…}>{surface.boundary}</p>
<p className="mt-1 …">{surface.name}</p>
```

For every surface that *is* its own boundary the two strings are equal, so the card printed the
same word twice:

| surface id | `name` | `boundary` | rendered before |
|---|---|---|---|
| `novanet` | NovaNet | NovaNet | `NOVANET` / `NovaNet` |
| `arkana` | Arkana | Arkana | `ARKANA` / `Arkana` |
| `solariun` | Solariun | Solariun | `SOLARIUN` / `Solariun` |
| `solspire` | SolSpire | SolSpire | `SOLSPIRE` / `SolSpire` |
| `weaver` | Weaver | Weaver | `WEAVER` / `Weaver` |

Five of the fourteen cards on the canonical landing page. The other nine name a real boundary
(`Arkana + Solariun`, `ARKADIA`, `Knowledge OS + Engineering Lab`) and are unaffected.

### The change

`Portal` now suppresses the eyebrow when it would repeat the name, and drops the `mt-1` that the
spacing assumed. The registry is **not** edited: `surfaces.ts` is workstream 1's exclusive file
and open PR `#704` holds it, so the repair is confined to `HomePage.tsx`, which no open PR
touches. The rule is expressed over the data rather than over a list of surface names, so a
surface added later is judged by the same rule.

## 4. Verification

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/test_prism_home_entry_contract.py -q
  -> 10 passed            (was 7; +3 = the new nodes)
```

Live negative control — with the source reverted, the new assertions must redden:

```
git checkout -- web/arkadia_console/src/pages/HomePage.tsx
  -> 2 failed, 8 passed
     FAILED …::test_portal_suppresses_an_eyebrow_that_repeats_the_name
     FAILED …::test_negative_control_flags_the_unconditional_eyebrow
restore
  -> 10 passed
```

`_portal_eyebrow_is_conditional` is a pure source reader, its negative control feeds it the shape
that shipped the defect, and `test_no_portal_renders_a_repeated_label` judges the **live
registry** rather than a literal list, so the rule cannot pass by agreeing with itself.

Type-check and bundle, on this tree:

```
cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build
  > tsc --noEmit && vite build
  ✓ 170 modules transformed.
  dist/assets/index-CprTE_pN.js            425.24 kB
  dist/assets/index-BJojPKi_.css            91.92 kB
  EXIT:0
```

The emitted JS hash differs from the served `index-CYGHeCpJ.js` **because the source changed** —
it is not a parity claim in either direction.

### Failing-node set is unchanged

23 failing/error nodes on `main` `aef65542`, all owned, reserved, or environmental; none is
touched by this change:

| failing file | nodes | disposition |
|---|---|---|
| `test_mission_lifecycle_adapter_contract.py` | 10 | environment: `web/arkadia_console/node_modules/typescript` absent in a bare clone |
| `test_autonomy.py` (ERROR) | 1 | CE-01 `weaver.autonomy` module-vs-package collision, sovereign-reserved |
| `test_ais_w2_living_gate_grove_handoff.py` | 1 | F-01 persistence boundary, sovereign decision |
| `test_identity_spine_w1.py`, `test_m02_reasomate_truth.py` | 2 | `#700` |
| `test_m01_persistence.py`, `test_m05_files.py` | 2 | `#690` |
| `test_prism_w4_lab_pr_state.py` | 2 | `#683` |
| `test_solspire_r1_governance_convergence.py` | 2 | `#693` |
| `test_solspire_r3_execution_runtime.py` | 1 | `#691` |
| `test_static_ingestion_idempotency.py` | 1 | `#698` |
| `test_gov04_bounded_merge_delegation.py` | 1 | `#725` |

Ownership was derived by intersecting the failing file list with the changed-file inventory of
all 61 open PRs, not by title.

## 5. What this cycle establishes, and what it does not

**Established:** `main` is `aef65542` and production serves that revision; every declared surface
path resolves on the canonical origin and `/solspire` correctly does not; the home portal grid
printed five duplicated labels and now does not; the new assertions bite on the pre-fix source;
the console type-checks and builds.

**Not established:** the rendered behaviour of the fix on the canonical origin — it is not
deployed, and a source change plus a source-level test is not a browser observation of the new
output. Also not established: merge eligibility, review sufficiency, or acceptance.

## 6. Next action

1. **Human:** merge authority for the queue. 61 open PRs, one ready (`#679`), no merge since
   `#722`; this cycle adds one more. Under this contract Weaver may not merge and did not.
2. **Human:** the composition conflicts handed off by cycles 20 and 22 (`#681`/`#687` and the
   earlier three) remain open.
3. **Weaver:** no other unowned defect was found. The failing-node set is fully accounted for, the
   lane-currency guard is green against live GitHub, and the remaining queue work is owned.

## 7. Reproduce

```
git rev-parse origin/main
curl -s https://arkadia-qzu4.onrender.com/api/version
curl -s -o /dev/null -w '%{http_code}\n' -H 'Accept: text/html' https://arkadia-qzu4.onrender.com/solspire   # 404
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/test_prism_home_entry_contract.py -q
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build
```
