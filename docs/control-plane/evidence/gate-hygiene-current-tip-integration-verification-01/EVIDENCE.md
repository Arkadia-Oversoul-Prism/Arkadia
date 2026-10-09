# EVIDENCE — gate-hygiene / current-tip integration verification 01

Bounded objective: **independently re-derive** the current-tip composition
measurement that the open debt-repair cluster's merge decision rests on, and
**add the per-PR merge-order conflict inventory** the composition measurement
does not carry. Evidence-only; no product code, workflow, authority surface, or
`AGENTS.md` is changed.

Status: **VERIFIED** (repository-source measurement, reproduced).
No production claim. No merge performed or authorized by this record.

## 1. Revision under measurement

| Field | Value |
|---|---|
| BASE_MAIN | `a47ea92817436675c15d472ca80f39d7295e880a` (2026-10-09 10:56:38 +0100) |
| Subject | Add read-only operator security verification control |
| Python | 3.13 · pytest 9.1.1 · git 2.47.3 |
| Env | `PYTHONPATH=archive/legacy_python`, `-p no:randomly`, `--continue-on-collection-errors -rEf` |
| Head refs | `pr354 536a8c43` · `pr356 1bfbcc4f` · `pr357 4c3d8fb8` · `pr363 aa77f364` · `pr365 d8679b49` · `pr347 3f3024d9` |

## 2. Baseline fingerprint — independently reproduced

Full-suite run on the unmodified tip (`main` @ `a47ea928`):

```
15 failed, 1839 passed, 20 skipped, 2 warnings, 1 error in 148.62s
```

Derived with `scripts/baseline_fingerprint.py --json`:

- **16** failing/error nodes
- outcomes `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733`
- ids `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833`

This reproduces — **byte-for-byte** — the baseline recorded by PR #375
(`docs/control-plane/evidence/gate-hygiene-current-tip-composition-batch-01/`)
at the same revision, from an independent clone and operator. The measurement is
not inherited; it was re-derived before being relied on.

The node set is also **exactly** the fixture proposed by PR #361
(`tests/fixtures/baseline_node_set.txt` @ `pr361`), compared node-to-node with
`diff` → identical (16/16). #361 (recorded 10-node fixture → live 16-node set)
therefore carries the correct reconciliation content; it is a **disjoint
workstream** from the product-repair cluster measured below.

Superseded baseline prose (`804 passed / 54 failed`, `main := 6038989`) does not
reproduce; the measured 16-node set is the current truth at `a47ea928`.

### Ownership of the 16 baseline nodes

| Node(s) | Owner |
|---|---|
| `test_m02a_ci_gate_integrity.py::test_allowlist_*` (3) | #354 |
| `test_engineering_lab_api.py::test_lab_*` (2) | #356 (authority surface) |
| `test_solspire_r1_*` (2), `test_solspire_r3_*` (1) | #357 |
| `test_identity_spine_w1.py` (1), `test_m02_reasomate_truth.py` (1) | #363 |
| `test_steward_filter.py` (3) | #365 |
| `test_ais_capability_profile_onboarding.py::test_home_*` (1) | #347 |
| `test_autonomy.py` (ERROR) | CE-01 · **sovereign-reserved** |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` (1) | F-01 · **unowned** |

## 3. Composed tree — independently reproduced

The cluster **#354 + #356 + #357 + #363 + #365 + #347** was applied onto a
detached worktree at `a47ea928`, each via `git apply --3way --exclude=AGENTS.md`.

Per-PR file presence was confirmed from `git status --porcelain` after each apply
(the #375 §4 hazard: a chained `--3way` that raises `UU` on a shared file can
silently drop the remaining files). Every PR's own non-`AGENTS.md` file landed:

```
M scripts/cp10_mutation_boundary_policy.py            (#354)
M tests/test_engineering_lab_api.py                   (#356)
M tests/test_solspire_r1_governance_convergence.py    (#357)
M tests/test_solspire_r3_execution_runtime.py         (#357)
M tests/test_identity_spine_w1.py                     (#363)
M tests/test_m02_reasomate_truth.py                   (#363)
M web/public_prism/src/pages/NodeEntry.tsx            (#363)
M tests/test_steward_filter.py                        (#365)
M weaver/filters/steward.py                           (#365)
M tests/test_ais_capability_profile_onboarding.py     (#347)
```

Full suite on the composed tree:

```
1 failed, 1857 passed, 20 skipped, 2 warnings, 1 error in 149.02s
```

- **2** nodes remain — exactly the two sovereign-reserved nodes:
  `ERROR tests/test_autonomy.py` (CE-01) and
  `FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` (F-01).
- outcomes `f607dffd1abda8bc667897a4366c6afe1498ae6e5b02635ff682cbc6daeb2ad1`
- ids `48e2b758b3194bd267e7babf13609b3467ff46985a879c72a55ad5201f44b3a9`

Both fingerprints **match PR #375's record exactly**. Node delta vs baseline:
**16 → 2** (`-14`), with **0** unexplained new nodes.

Protected regressions on the composed tree:

- architecture fitness (`tests/architecture`): **11 passed**.
- CP10 mutation-boundary judge (`scripts/cp10_mutation_boundary_policy.py --judge`
  over the composed change paths): **PASS** (exit 0).

**Conclusion:** the cluster composes on the current tip and the #375 claim is
independently reproducible. This record does not merge or authorize; it supplies
the second-observer evidence the sovereign's decision needs.

## 4. Merge-order conflict inventory (net-new to this record)

GitHub reports `CONFLICTING` for the cluster PRs. The *textual* conflict surface
was isolated per PR with `git merge-tree --write-tree --name-only main <pr>`
(git 2.47), which reports conflicted paths independently of `AGENTS.md` handling:

| PR | merge-tree vs `main` | conflicted path(s) |
|---|---|---|
| #354 | rc=1 | `AGENTS.md` only |
| #356 | rc=1 | `AGENTS.md` only |
| #357 | rc=1 | `AGENTS.md` only |
| #363 | rc=1 | `AGENTS.md` only |
| #365 | rc=0 | clean |
| #347 | rc=0 | clean |
| #366 | rc=0 | clean |
| #368 | rc=0 | clean |

**Finding.** The only textual conflict any cluster PR has against `main` is the
shared `AGENTS.md` tail — a **non-code** file whose edits are governed separately
by the standing insertion-only constraint (append corrections; never rewrite an
oracle line). **Zero** cluster PRs conflict on a product, test, or authority
surface. The conflict list an operator sees on GitHub (`CONFLICTING`) is
therefore an `AGENTS.md`-only artifact and is **not** evidence that the cluster
fails to compose.

**Ordering consequence.** Because the code/test surfaces are pairwise disjoint
(no two cluster PRs touch the same non-`AGENTS.md` path), merge order is not
constrained by code conflict. The only ordering obligation is `AGENTS.md`: each
merge's resolution must keep every prior merge's appended lesson while appending
its own (insertion-only), and the last merge to land must leave the file
mojibake-clean and oracle-corroborated
(`python scripts/agents_md_encoding_audit.py` → exit 1, `alterations=0`).

## 5. Gate-2 soundness — state re-derived, not inherited

`scripts/gate2_production_observation.py` on `main` still carries the
marker-oracle soundness defect: it can wrongly report a `VERIFIED` marker verdict
while the served alias document contains none of the markers. PR **#366**
(`gate-hygiene/gate2-marker-oracle-soundness-01`, ref `aab36a17`) owns the repair.

The repair is **fail-closed** and **sound for the root-project case**: `frontend_of()`
reads the served app identity from the **deployment label** (`Production – <project>`)
— not from the root `vercel.json` — and returns `None` when the suffix is not a
known project, so an undetermined app can never be scored against a marker set:

```
if app is None:  -> NOT OBSERVED (served app undetermined; markers describe '<MARKER_APP>')
if app != MARKER_APP: -> NOT OBSERVED (artifact is '<app>'; markers describe '<MARKER_APP>')
```

`KNOWN_FRONTENDS` covers both frontends the root `vercel.json` has been pointed at
(`arkadia-prism` → `web/public_prism/`, `console` → `web/console/`). Net-new
observation for the record: at `a47ea928` the root `vercel.json` builds
**`web/console`**, so the newest Production record is labelled `Production – console`
and the marker oracle correctly reports `NOT OBSERVED (artifact is 'console')`.

The repair carries a **negative control** (`test_the_pre_repair_verdict_is_unreachable_from_the_classifier`
asserts the coercing `report.get("deployed_app") or MARKER_APP` is absent from
source), so a re-introduced fallback reddens a test rather than passing silently.
#366's own suite was reproduced in this run: **34 passed**.

Gate-2's remaining boundary is **provider-SSO** on the deployment-specific
`environment_url` (`BLOCKED`), not repository work. Per the contract, `BLOCKED`
is never promoted to `VERIFIED` by repetition.

## 6. Authority boundary

- No product code, workflow, mutation path, authorization path, governance
  surface, or `AGENTS.md` is changed by this record. It is evidence-only.
- Merging the cluster is **sovereign-only**. `#356` repairs a pin over
  `api/lab_routes.py`, an authority surface (Lab mutation boundary); `#354`
  touches the CP10 boundary policy. This document measures and reports; it does
  not merge or authorize.
- No push to `main`; the change is delivered as a branch → PR for human review.

## 7. Remaining uncertainty

- The composition was measured by patch application, not by merging the PR
  branches. A clean `--3way` proves no textual conflict on the applied surfaces;
  the tests prove the composed tree passes; but branch ancestry (`main` has moved
  since several PR bases) is not itself proven mergeable by this method. Branch
  **ancestry** and **patch composition** are different properties; this record
  proves the latter.
- The 16-node baseline includes collection-error semantics
  (`--continue-on-collection-errors`). The recorded `tests/fixtures/baseline_node_set.txt`
  fixture drift is owned by the disjoint #361 workstream.
- `#366`/`#368` compose cleanly against `main`, but #368 is stacked on #366
  (`git merge-base --is-ancestor <pr366-head> <pr368-head>` → true); #370 exists
  to record that same-instrument composition. Their own merge ordering is not
  measured here.
