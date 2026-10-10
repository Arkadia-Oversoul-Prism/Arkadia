# EVIDENCE — gate-hygiene-gate2-instrument-composition-01

Gate: GATE-02 (production parity) / gate-hygiene
Branch: `gate-hygiene/gate2-instrument-composition-01`
Base main: `a47ea92817436675c15d472ca80f39d7295e880a`
Composes: PR #366 (`gate-hygiene/gate2-marker-oracle-soundness-01`, head `aab36a17`)
          + PR #368 (`gate-hygiene/gate2-deployment-window-01`, head `aa6f4d2c`)

## 1. Why this PR exists

PRs #366 and #368 repair **the same two files** from the **same base**
(`scripts/gate2_production_observation.py`, `tests/test_gate2_production_observation.py`).
GitHub reports each head as `MERGEABLE` against `main`, but that verdict compares each
head to `main` only and cannot see a **cross-PR** overlap. PR #370 measured the overlap
and recorded, in its own body, two executable paths:

> Merge **#366 first**, then rebase **#368** onto it keeping **both** edits — **or land
> one composed PR**. Do **not** merge the pair unreconciled.

The first path is not executable by a human merge review: after GitHub merges #366,
#368's branch carries a **conflicting** `scripts/gate2_production_observation.py`
(its head blobs are the pre-#366 base `9b481812…`, #366's are `82907d6e…`). A plain
"Merge" of #368 then loses one repair. This PR is the **second** recorded path: one
composed PR that carries both repairs, so no merge decision can silently drop one.

This PR **merges nothing and supersedes no decision**; it materializes the composition
PR #370 said not to omit. #370 remains the decision record and the mechanisms analysis.

## 2. Measured composition (real merge, not inference)

`main` has **not** touched either file since #370's base (verified):

```
git log --oneline 24a00f85..a47ea928 -- scripts/gate2_production_observation.py \
    tests/test_gate2_production_observation.py   -> (empty)
git rev-parse a47ea928:scripts/gate2_production_observation.py -> 9b481812…  (== base)
git rev-parse a47ea928:tests/test_gate2_production_observation.py -> 5d6ef978… (== base)
```

So #370's composition at `24a00f85` reproduces byte-identically at `a47ea928`. A real
`git merge pr366` then `git merge pr368` onto `a47ea928` composes **cleanly** (both
`ort` auto-merges, no conflict markers) and yields:

| Artifact | Value |
|---|---|
| composed `scripts/gate2_production_observation.py` blob | `cf09b073…` (#370's recorded composed blob) |
| `DEPLOYMENT_SCAN_PAGES` occurrences | 4 (#368's pagination repair present) |
| `KNOWN_FRONTENDS` occurrences | 3 (#366's app-identity repair present) |
| `pytest tests/test_gate2_production_observation.py -q` | **39 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile api/main.py` | OK (boot code untouched) |

## 3. Composition is semantically sound, not merely textually clean

Both repairs are independently necessary and do not contradict:

- **#366 (marker-oracle soundness):** the harness was scoring Prism `MARKERS` against
  whatever artifact the canonical alias served. The root `vercel.json` was repointed to
  `web/console` (commit `404452e0`), so the alias now serves **Console**, and every Prism
  marker legitimately reads `0`. Reporting that as *agreement* (`VERIFIED (marker set
  matches…)`) or as an SG-04 *regression* was a category error.
- **#368 (deployment window):** `/deployments` is paginated across all environments; the
  harness read a single fixed 60-record window, so a deployed-and-sha-identical `main`
  read as `UNKNOWN`.

Neither weakens the other: #366 scopes *what* may be scored; #368 guarantees *which*
deployments are enumerated before scoping.

### Live corroboration of #366's premise (independent of the harness)

Fetched the alias artifact directly and read its identity:

```
GET https://arkadia-prism.vercel.app/          -> <title>Arkadia Console</title>
GET …/assets/index-DuaRHIa2.js (236537 bytes)  -> Prism markers 0, "console" 13
```

The alias serves the Console application. This independently corroborates the
`gate2-canonical-alias-app-binding-01` finding (PR #369, merged) and confirms the
`NOT OBSERVED` classification is the sound one, not a false-negative.

### Composed harness read at `a47ea928` (post-composition)

```
artifact app: console   harness markers describe: arkadia-prism
  !! the served artifact is a DIFFERENT application than the marker list
SG-04 REGRESSION
  in source: True   NOT EVALUABLE against artifact: the 'console' app …
boundaries:
  main -> deployment identity      VERIFIED
  deployment build output observed BLOCKED
  marker-set oracle                NOT OBSERVED (artifact is 'console'; markers describe 'arkadia-prism')
  build <-> source lineage         UNKNOWN
  production acceptance            NOT CLAIMED (human authority)
```

The false `VERIFIED` (marker agreement the harness never observed) and the phantom
SG-04 regression are both gone. The live boundary remains `BLOCKED` on Vercel
Deployment Protection (SSO); **repeating a pass cannot convert `BLOCKED` into
`VERIFIED`**.

## 4. Regression boundary — zero node delta

Full suite, `main` @ `a47ea928` vs the composed tree, aligned with the repository
convention (`PYTHONPATH=<repo>/archive/legacy_python`,
`pytest tests/ -q -rEf --continue-on-collection-errors`):

| Tree | failing/error nodes | node-set sha256 |
|---|---|---|
| `main` `a47ea928` | 16 (15F/1E) | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` |
| composed | 16 (15F/1E) | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` |

The failing/error node **set** is byte-identical; `1859 passed` vs baseline `1839` is
`+20`, exactly the composed harness test file's added nodes (39 – 19 pre-existing) plus
generic-scanner pass-through. Counts are environment-dependent; only node identity is
load-bearing.

## 5. Scope / non-goals

- **In scope:** the two instrument repairs (#366 + #368) as one composed tree, plus this
  evidence doc.
- **Out of scope:** product code, `api/main.py` (untouched, 2600-line budget intact), any
  workflow, any governance/identity/authority path, any merge. `AGENTS.md` carries only
  the two append-only lessons #366/#368 already authored.
- **Not claimed:** production parity, production acceptance, Gate-2 closure.
- The landing-copy / identity / steward-filter pins in §4 are pre-existing baseline debt,
  reported not repaired.

## 6. Authorization

Sovereign review and merge decision. If this PR lands, #366/#368/#370 become
`SUPERSEDED` by it (their repairs are fully contained); close them without merging.
