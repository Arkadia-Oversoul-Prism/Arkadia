# EVIDENCE — gate-hygiene-gate2-instrument-composition-verification-01

Gate: GATE-02 (production parity) / gate-hygiene
Branch: `gate-hygiene/gate2-instrument-composition-verification-01`
Role: **independent verification** of the active Gate-2 PR **#378**
(`gate-hygiene/gate2-instrument-composition-01`, head `19dca5057793f954dd017c630bff846b992bcd63`)
Base main: `a47ea92817436675c15d472ca80f39d7295e880a`
Environment: Python 3.13 · pytest 9.1.1 · git 2.47.3 ·
`PYTHONPATH=<repo>/archive/legacy_python`, `--continue-on-collection-errors -rEf -p no:randomly`

Evidence-only. No product code, test, workflow, `api/main.py`, authority path, mutation
path, or governance surface is changed. `AGENTS.md` carries one append-only lesson.

---

## 1. Only-history claims in the #378 body

The #378 body makes three claims that are **history** claims, not measurements of the
composition. Each was checked against live git objects.

| #378 body claim | Checked value | Verdict |
|---|---|---|
| `#368`'s head blobs are the **pre-#366 base** (`scripts/gate2…` = `9b481812…`) | #368 head `aa6f4d2c` blob = **`4db47217…`** | **FALSE** |
| "a plain Merge of #368 then **loses one repair**" | plain `git merge pr368` onto `main` is conflict-free and yields `4db47217…` (both repairs) | **FALSE** |
| composed blob = `cf09b073…` (#370's recorded composed blob) | `cf09b073` is **not a valid object** in the clone; measured composed blob = `4db47217…` | **UNRESOLVED / contradicts measurement** |

`9b481812…` is the blob of the **base**, i.e. `origin/main:scripts/gate2_production_observation.py`
and **PR #370's head** — not #368's head.

## 2. Why the premise went stale before #378 was opened

PR #368 **merged #366 into its own branch** — the first of #370's two paths — before #378
was authored:

```
pr368 head aa6f4d2c ... 2026-10-09 08:16:09 +0000  docs(gate2): record the #366 composition into #368
pr368     9837213f ... 2026-10-09 08:12:01 +0000  Merge ... gate2-marker-oracle-soundness-01 into ... deployment-window-01
#378 created            2026-10-09T13:22:22Z        (~5 h later)
```

`git merge-base --is-ancestor pr366 pr368` → **true**. #368 head tree carries both repairs:

```
ref           script blob                                KNOWN_FRONTENDS  DEPLOYMENT_SCAN_PAGES
origin/main   9b481812d54d7440ff8fe45843f5a9fb2e63cbd5   0                0
pr366         82907d6e25165880b04c86cbf912c7f68a9bf529   3                0
pr368         4db472176da1a389c358442bfd1b4b12b4f3a12d   3                4
pr378         4db472176da1a389c358442bfd1b4b12b4f3a12d   3                4   (identical to #368)
```

`tests/test_gate2_production_observation.py` and `AGENTS.md` blobs are **also identical**
between #368 and #378 (`41273478…`, `4d311be1…`). The *only* file #378 adds over #368 is
its own `gate-hygiene-gate2-instrument-composition-01/EVIDENCE.md`:

```
pr368^{tree} 160f87571f7aa2564667c9855a681bb43ff45ae6
pr378^{tree} deb99ffeb5abc4192e9456cd6fe0fa8508fe301d
```

## 3. Both recorded merge paths now reproduce cleanly (real merge, detached worktree)

Fresh worktree at `a47ea928`; git identity set; `git merge --no-ff`:

| Path | Result |
|---|---|
| **A** — merge `pr366` then `pr368` | conflict-free both steps; final blob `4db47217…` |
| **Direct** — merge `pr368` alone | **conflict-free**; blob `4db47217…`; `KNOWN_FRONTENDS=3`, `DEPLOYMENT_SCAN_PAGES=4` |

The conflict #378 was authored to route around exists only if #368's branch is read at its
pre-`9837213f` state. At the live head it does not exist, and a plain merge of #368 **keeps
both repairs**.

## 4. Independent reproduction of #378's *measured* content (unchanged from its body)

The composition content itself is sound and was reproduced independently:

| Command | Result |
|---|---|
| `pytest tests/test_gate2_production_observation.py -q` (branch) | **39 passed** (`main`: 19 passed) |
| `pytest tests/architecture -q` | **11 passed** (same as `main`) |
| `python -m py_compile api/main.py` | OK (boot code untouched) |
| `scripts/cp10_mutation_boundary_policy.py --judge` (branch diff) | **PASS** (exit 0) |
| `python scripts/agents_md_encoding_audit.py` | `alterations=0`, `Cyrillic 0 -> 0`, `reproduced=True`, exit **1** |

Full suite, aligned to the repo convention:

| Tree | failing/error nodes | node-set sha256 (outcomes) | sha256 (ids) | counts |
|---|---|---|---|---|
| `main` `a47ea928` | 16 (15F/1E) | `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733` | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` | 15 failed, 1823 passed, 36 skipped, 1 error |
| branch `19dca505` | 16 (15F/1E) | `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733` | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` | 15 failed, 1843 passed, 36 skipped, 1 error |

**Node set byte-identical** (`diff` empty). `+20 passed` is the composed harness file's
added nodes (39 − 19) plus generic-scanner pass-through; counts are environment-dependent,
node identity is load-bearing.

### Baseline reconciliation (environment delta vs recorded set)

The canonical record for `a47ea928` is **16 nodes / `bfcfe592…` / `ed5e4714…`** (PRs
#375, #376, #377) — this environment reproduces it exactly. The #378 body counts it as
`1859 passed` vs its `1839` baseline; this clone measures `1843` vs `1823`. The 16-node
failing set is identical; only the passed tally differs, confirming the delta is
environmental (optional deps, e.g. `pytest-asyncio` for the async ARK-01 conformance
tests), not a repository regression.

## 5. Harness behaviour on the composed tree (the repair works)

```
main SHA                : a47ea928… ;  newest Production deploy a47ea9281743 id=6957911584
  deploy SHA == main    : True
alias https://arkadia-prism.vercel.app/ -> HTTP 200   <title>Arkadia Console</title>
artifact app: console   harness markers describe: arkadia-prism
  !! the served artifact is a DIFFERENT application than the marker list
SG-04 REGRESSION
  in source: True   NOT EVALUABLE against artifact: the 'console' app, which has no SG-04 surface.
boundaries:
  main -> deployment identity      VERIFIED
  deployment build output observed BLOCKED   (deployment-specific URL -> 302 SSO)
  marker-set oracle                NOT OBSERVED (artifact is 'console'; markers describe 'arkadia-prism')
  build <-> source lineage         UNKNOWN    (source_lineage_closed = false)
  production acceptance            NOT CLAIMED (human authority)
```

The #366 repair is confirmed: the false `SG-04 REGRESSION` and the phantom marker
`VERIFIED` are gone; the app mismatch is named instead of mis-scored. `build <-> source
lineage` correctly reads `false`: the two candidate Production SHAs `a47ea928` and
`d2dd0e75` do not share the last frontend build-input commit (`b3834ecf`), so the artifact
*could* differentiate them — an honest `UNKNOWN`, not a defect.

## 6. Regression boundary

- `api/main.py` **untouched** (2600-line budget intact).
- No workflow, governance, identity boundary, authority path, mutation path, or merge path.
- No product/frontend code.

## 7. Disposition (recommendation — a human decision, not an action taken here)

The composed content of #378 is **correct and verified**. Its *premise and mechanism* are
now stale: #368 already absorbed #366 at `9837213f`, so a plain merge of #368 onto `main`
is conflict-free and keeps both repairs. Recommended sovereign options:

1. **Merge #368 directly** (it contains both repairs), then close #366/#370/#378 as
   superseded; or
2. **Merge #378** for the extra composition record, then close #366/#368/#370. Landing
   #378 while #368 stays open leaves two PRs that patch the identical blob — merge one of
   the pair, not both.

Either way, the #378 body's claims "`#368`'s head blobs are the pre-#366 base" and "a
plain Merge of #368 loses one repair" should be **corrected**; this pass does not edit
#378 (evidence-only).

## 8. Pass 2 addendum (2026-10-09) — main drift + precision

`main` advanced from `a47ea928` to `d466e13786a3925d26fd3f7eafb631c9cdc9dad1` (5
Firebase-config commits; none touch the Gate-2 instrument). The newest Production
deployment is still `a47ea9281743` (id `6957911584`), so `main → deployment identity`
is **STALE**, and the deployment URL remains **BLOCKED** (SSO). The pass-1
"blob-identical except EVIDENCE.md" line is corrected to "the Gate-2 instrument files
are blob-identical (`scripts/gate2_production_observation.py` `4db472176d`,
`vercel.json` `ccebe6abbd`, `tests/test_gate2_production_observation.py` `412734789f`);
the other head differences are main-drift." Independent reproduction: composed suite
16-node set byte-identical to `main` (`bfcfe592…`/`ed5e4714…`), CP10 judge PASS,
AGENTS.md audit `alterations=0`. Details in `WORKSTREAM_STATE.md` (Pass 2).

## 9. Not claimed

Not production parity, not production acceptance, not Gate-2 closure. The standing
boundary *deployment build output observed* remains **BLOCKED** on Vercel Deployment
Protection (SSO). Repeating a pass cannot convert `BLOCKED`/`UNKNOWN` into `VERIFIED`.
