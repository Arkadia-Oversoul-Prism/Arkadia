# gate-hygiene — Arcana Weaver merge-loss restoration

Pass: `gate-hygiene/arcana-weaver-merge-loss-restore-01`
BASE_MAIN at reconstruction: `451e41a30fcbff4a65326e897a84818cc623b769`
("docs(control-plane): advance convergence frontier after G12 merges (#317)")
Reconstructed: 2026-10-06 · canonical clone `main`, non-shallow (2142 commits), ancestry intact.

This pass authored none of the PRs it measures. Every claim below is a reproduced
measurement from a fresh clone on `main`.

## 1. Why this pass exists — a merged PR whose headline feature is absent from `main`

PR **#273** (`feat: fuse Weaver and Canvas into Arkana Weaver`, merge
`6c8e7f45126440ab868e080f22bb7ea1abca32d2`, `2026-10-05 04:58:46 +0100`) is MERGED
and is an ancestor of `main`. Its title claims a fused Weaver/Canvas surface. On
current `main` that fusion is **absent**.

| artifact | on `main` (`451e41a`) | on the PR head (`39b5d66`) |
|---|---|---|
| `ArkanaWeaverCanvas.tsx` | tracked (`156854e`) | tracked |
| dashboard import of it | **absent** | present in the branch's own v3 commit |
| dashboard mount of it | **absent** | present in the branch's own v3 commit |
| `label: 'Arkana Weaver'` in dashboard `TABS` | **absent** (`label: 'Weaver'`) | present |
| `tests/test_arcana_weaver_fusion.py` | tracked (`be400e2`) | tracked |
| fusion test result | **FAIL** | (branch form) |

The fusion test landed and the feature did not.

## 2. The defect is merge-loss, and it is mechanically demonstrable

`6c8e7f4` has parents `752aaff` (main at merge time, post-#270 opportunity-radar) and
`39b5d66` (PR #273 head).

- `git diff 6c8e7f4^2 6c8e7f4 -- web/public_prism/src/pages/ProjectDashboard.tsx` → **empty**
- `git diff 6c8e7f4^1 6c8e7f4 -- web/public_prism/src/pages/ProjectDashboard.tsx` → **empty**

The merge's dashboard blob is **byte-identical to both parents**. Yet the branch's own
tip lineage shows the fusion was composed and then lost:

| commit | dashboard line 7 (import) | mount |
|---|---|---|
| `33c9ed1` | `import ArcanaWeaverCanvas from '…/ArcanaWeaverCanvas'` | `(tab === 'weaver' \|\| tab === 'canvas')` |
| `26887fd` | `import ArkanaWeaverCanvas from '…/ArkanaWeaverCanvas'` | `(tab === 'weaver' \|\| tab === 'canvas')` |
| `51e21ce` (PR head) | `import ArkanaWeaverCanvas from '…/ArkanaWeaverCanvas'` | `(tab === 'weaver' \|\| tab === 'canvas')` |
| `39b5d66` (`Merge branch 'main' into …`) | **removed** | reverted to `tab === 'weaver'` → `<WeaverPanel>` |
| `6c8e7f4` (merge to main) | **removed** | `<WeaverPanel>` |

The in-branch merge `39b5d66` resolved `ProjectDashboard.tsx` to the pre-fusion `main`
side. Because that resolution then propagated unchanged into the PR merge, the
dashboard arrived at `main` in a state the fusion work never intended — while the
import-satisfying file (`ArkanaWeaverCanvas.tsx`) and the asserting test
(`test_arcana_weaver_fusion.py`) both landed.

The branch's mount carried `key="arcana-weaver"` while its import and component file
were named `ArkanaWeaverCanvas` — an inconsistent key inside the branch's own v3
commit. That key is **not** present on `main` (measured: `git grep arcana-weaver
origin/main -- web/public_prism/src/` matches only `ArkanaWeaverCanvas.tsx`'s own
testid and CSS class names, never `ProjectDashboard.tsx`), so it is not a residue on
`main` — see §7 for the correction of an earlier claim to the contrary.

## 3. The bounded repair

`web/public_prism/src/pages/ProjectDashboard.tsx`:

- re-add `import ArkanaWeaverCanvas from '../components/solspire/ArkanaWeaverCanvas';`
- mount the canvas on the **`canvas` tab**, keeping `WeaverPanel` on the `weaver` tab
- rename the `weaver` tab label `Weaver` → `Arkana Weaver`

**Correction to an earlier draft of this document.** An earlier revision stated the
label was "already `Arkana Weaver` on `main` — unchanged". That was **false**: measured
`git show origin/main:…/ProjectDashboard.tsx` → `label: 'Weaver'`, and the rename to
`Arkana Weaver` is one of this branch's changes. The claim was corrected in place
rather than left standing; the assertion it justified is unaffected, because the pin
is `assert "label: 'Arkana Weaver'" in dashboard` against the **repaired** tree.

Design note — why not restore the branch's literal form. The branch form is a
**replacement, not a stack** (measured on the branch blob `51e21ce`): the single
combined line is the *only* `<ArkanaWeaverCanvas` mount, and `<WeaverPanel` is
mounted **0** times in that file while `function WeaverPanel` is still defined **1**
time — the panel became dead code. On current `main` that panel is a governed surface
(`K15_READY`, `BIND PASSSPEC`, `UI STATE ≠ AUTHORIZATION`, `Mutation: K15 → K3 ONLY`).
Restoring the combined condition would therefore have deleted a governed lifecycle
surface as a side effect of a naming repair. The composition here keeps the governed
panel on `weaver` and surfaces the fused canvas on `canvas`, the tab whose id the
branch had already added to `ProjTab`, `TABS` and `PRIMARY_TABS`.

`tests/test_arcana_weaver_fusion.py`:

The test's last pin `assert "(tab === 'weaver' || tab === 'canvas')" in dashboard`
demands the *discarded* form. Per this repository's standing rule — a source-level
assertion that fails must be checked against the source literal, and a test-side
literal defect is repaired on the test side — the pin now asserts the mount actually
composed:

```
assert "tab === 'canvas'" in dashboard
assert "<ArkanaWeaverCanvas project={currentProject} />" in dashboard
assert "<WeaverPanel project={currentProject} />" in dashboard
assert "label: 'Arkana Weaver'" in dashboard
```

## 4. Verification

| check | command | result |
|---|---|---|
| fusion test | `pytest tests/test_arcana_weaver_fusion.py -q` | **1 passed** (was 1F) |
| dashboard-pin neighbours | `pytest tests/test_weaver_mvp2_07.py tests/test_weaver_mvp2_01.py tests/test_weaver_mvp2_08.py tests/test_weaver_sci_boundary_01.py tests/test_solspire_p0_execution_01.py tests/test_m05_files.py` | 54 passed, 0 failed |
| boot syntax | `python -m py_compile api/main.py` | OK |
| boot-code budget | `wc -l api/main.py` | 2432 (≤ 2600) |
| frontend build | `corepack pnpm install --frozen-lockfile && corepack pnpm build` | **exit 0**, 3446 modules, 7.77s |
| CP10 boundary | `python scripts/cp10_mutation_boundary_policy.py --judge` | PASS |

### Full-suite fingerprint (node identity, not counts)

Both runs: `pytest tests/ -q -rEf --continue-on-collection-errors`.

| tree | counts | failing-node sha256 |
|---|---|---|
| baseline `main` `451e41a` (clean) | 11 failed, 1509 passed, 20 skipped, 1 error | `2dafe6a8b471527b96fa645b2c3cf979f7b53c95a830ecce9c767d4ee6655886` (12 nodes) |
| this branch | 10 failed, 1510 passed, 20 skipped, 1 error | `92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413` (11 nodes) |

Node-set delta, both directions:

```
3d2
< tests/test_arcana_weaver_fusion.py::test_arcana_weaver_fuses_project_canvas_weaver_and_arkana_runtime
```

Exactly one node removed, none added. The `-1 failed / +1 passed` is that node; no
baseline debt was touched.

### Build-level evidence (presence/absence contrast)

`dist/` is untracked (`git ls-files web/public_prism/dist` → 0 paths), so the build
leaves a clean tree. Minified-chunk markers, convention stated explicitly
(`grep -o | wc -l` = occurrences):

| marker | occurrences in `dist/assets/ProjectDashboard-*.js` |
|---|---|
| `arcana-weaver-canvas` (the canvas's own testid) | 2 |
| `K15_READY` | 2 |
| `BIND PASSSPEC` | 1 |
| `UI STATE ≠ AUTHORIZATION` | 1 |
| `Mutation: K15 → K3 ONLY` | 1 |

The fused canvas testid and the governed `WeaverPanel` markers coexist in one built
chunk — the fusion is real and the governed surface was not displaced.

**Pre-change control.** On `main`, `ArkanaWeaverCanvas` has **zero** importers
(`git grep ArkanaWeaverCanvas origin/main -- web/public_prism/src/` matches only its
own definition file), so `arcana-weaver-canvas` is structurally absent from any
`main`-built dashboard chunk. On this branch `ProjectDashboard.tsx` references it
exactly **2** times (import + mount) and the built chunk carries exactly **2**
occurrences. The contrast is presence/absence, and the count matches the reference
count — the marker measures this branch's composition, not a pre-existing string.

Caveat on the governed-panel markers (`K15_READY` etc.): they are **not** a
presence/absence control for this change, because `main` also mounts `WeaverPanel` and
would show them too. They are recorded only to show the governed surface still exists
in the composed build; the discriminating control is the canvas testid above.

## 5. What this is not

- **Not** a production-parity claim. This is repository-source + build evidence only.
  No deployment identity is established for this branch, and Gate 2's observation
  boundary is unchanged.
- **Not** a claim about the historical pre-#273 state. #273's description is
  consistent with the branch's own v3 commits; the loss occurred in resolution.
- **Not** a re-litigation of #273's design. The repair restores the feature #273
  claims to have shipped, in the composition that preserves the governed surface.

## 6. Next bounded task

Sovereign review of this PR.

A separate candidate workstream is **recorded but not executed** (no self-expansion),
and is weaker than an earlier draft of this section implied. The `motion.div
key="arcana-weaver"` inconsistency exists only inside the **discarded branch** blob
`51e21ce`; it never reached `main` (measured in §2), and this repair's mount uses
`key="canvas"`. So there is no live residue to chase here. The remaining, genuinely
open question is narrower: whether *other* two-of-three rename sites from the same
hand-resolution are live on `main`. That has **not** been measured, so it is stated as
an unmeasured hypothesis rather than a finding.
