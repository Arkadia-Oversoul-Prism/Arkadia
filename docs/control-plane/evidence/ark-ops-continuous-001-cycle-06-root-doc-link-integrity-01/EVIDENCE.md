# ARK-OPS-CONTINUOUS-001 — cycle 06: the root front door links a tree that no longer exists

**Contract:** `ARK-OPS-CONTINUOUS-001`, rev 2026-11-22.
**Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d` (re-fetched live this cycle; unchanged since cycle 05).
**Branch:** `gate-hygiene/root-doc-link-integrity-01`.
**Scope:** `README.md` (one list item), `tests/test_root_doc_link_integrity.py` (new guard), `.github/workflows/root-doc-link-integrity.yml` (new gate), this record.
**Disposition:** IMPLEMENTED, draft. Merge execution is human-only (GOV-03). No deployment, no acceptance.

## 1. The defect, measured

`README.md`'s "How to inspect Arkadia" list — the first navigation a newcomer follows — carried:

```
6. [web/public_prism/](web/public_prism/) — current frontend
```

That tree was archived by `c081d200` (2026-10-11). Measured on this base:

```
$ ls web/
arkadia_console  console
```

So the repository's front door linked a path that does not exist **and** described it
as the *current* frontend, while the active console is `web/arkadia_console/`.

Nothing judged it. The guard domain was empty:

```
$ grep -rn "README.md" .github/workflows/
(no match)
```

A scan of every relative markdown link in every root narrative document (`*.md`,
28 files) found **exactly one** broken target, the one above. The defect is real,
single, and bounded — it is not a symptom of general doc rot.

## 2. The change

| file | change |
|---|---|
| `README.md` | item 6 now links `web/arkadia_console/` ("active console") and names the retired Prism tree as the archive at `archive/frontend/arkadia-prism/` (both targets exist) |
| `tests/test_root_doc_link_integrity.py` | new guard: every relative link in every root `*.md` must resolve; the domain is derived from the tree at test time |
| `.github/workflows/root-doc-link-integrity.yml` | new gate that executes the guard; `paths` names every input the guard reads (`*.md`, the guard, itself) and it is dispatchable |

The invariant is stated over the **document set**, not the one file the defect happened
to be in, so the next stale link fails CI instead of surviving the next archive move.
`*.md` in GitHub's filter syntax does not cross a directory boundary, so it selects
exactly the root-level documents the guard enumerates.

Scope is stated in the guard, not implied: external URLs, `mailto:`/`tel:`, in-page
anchors, fenced code blocks and inline code spans are not repository paths and are not
judged.

## 3. Proof, bound to this tree

**The guard.**

```
python -m pytest tests/test_root_doc_link_integrity.py -q
35 passed
```

(4 detector controls + 1 domain test + 28 parametrized root documents + 1 README pin +
2 gate-wiring tests.)

**Live negative control — the exact defect shape must redden the guard.** Restoring
`main`'s README line in the working tree:

```
FAILED tests/test_root_doc_link_integrity.py::test_root_documents_link_only_to_paths_that_exist[README.md]
FAILED tests/test_root_doc_link_integrity.py::test_the_readme_links_the_active_console
2 failed, 33 passed
```

Restored byte-identically, re-run: `35 passed`. The detector is not vacuous, and it is
not over-broad (only the two README-facing nodes move).

**A new workflow must not redden the generic scanners.** Measured, not assumed:

```
python -m pytest tests/test_ci_gate_trigger_coverage.py \
  tests/test_ci_gate_trigger_coverage_ci_wiring.py tests/test_workflow_injection_boundary.py \
  tests/test_ci_suite_collection_continuation.py tests/test_gate_filter_selection.py \
  tests/test_ci_verdict_step_integrity.py tests/test_ci_verdict_step_integrity_ci_wiring.py \
  tests/test_history_depth_ci_wiring.py -q
373 passed
```

**Node attribution is measured per file, not inferred from the total.**

```
collect-only, generic scanner files:  main-equivalent 347  ->  branch 354   (+7)
collect-only, new guard file:                                            35
                                                                       ----
                                                                          +42
full suite passed count:                              4250  ->  4292   (+42)
```

The `+7` is the generic suites parametrizing over one additional workflow file; the `+35`
is the new guard. The sum equals the passed delta exactly.

**Full suite, same environment, on this tree:**

```
19 failed, 4292 passed, 22 skipped, 1 error in 294.56s
```

Sorted failing/error node set: **20 nodes**, sha256
`8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb` — **identical to the
recorded `main` baseline at this SHA** (`8d70e46e…`, cycle 05). Zero regression, by node
identity. The 10 `test_mission_lifecycle_adapter_contract.py` nodes are the known
environment-only set (this sandbox has no `web/arkadia_console/node_modules/typescript`);
the remaining 10 are the classified debt (CE-01, FINDING F-01, and nodes repaired by open
PRs #700/#693/#690/#691/#698). None is attributable to this change.

**Mutation boundary and fitness:**

```
git diff --name-only --cached | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (exit 0)

python -m pytest tests/test_m02a_ci_gate_integrity.py tests/architecture -q
87 passed
```

## 4. What is not claimed

- No merge, deployment, production verification or acceptance. `main` is unmodified; this
  is a draft branch. Merge execution is human-only (GOV-03).
- CI execution of the new gate is not asserted here. The workflow is new, so no run exists
  at this head yet; the guard was executed locally and the workflow's own wiring is pinned
  by two source-level assertions. Read the run log once it exists rather than assuming it.
- The pre-existing failing set is unchanged debt, not repaired here.

## 5. Recorded follow-ons (measured, not repaired)

These are outside this cycle's scope. They are recorded so the next cycle does not
re-derive them.

1. **`research/oversoul_prism_144/test_substrate.py` carries a guard that cannot execute.**
   `test_authority_smuggling_is_rejected_at_transformation_boundary` calls
   `transform_node`, which the module's import block omits (`substrate.py:128` defines it).
   Measured: `1 failed, 8 passed` with `NameError: name 'transform_node' is not defined`.
   The package README claims it "rejects historical nodes that carry authority or
   executable status", so the claim has no executing proof. `grep -rn "research/"
   .github/workflows/` returns no gate, so nothing runs the module either. The fix is one
   import token plus execution wiring; it is a separate bounded change.
2. **Stale prose naming the retired frontend.** `PROJECT_INDEX.md:82,122` and
   `NEXT_AGENT.md:42,62` still describe `web/public_prism/` as the SPA. `CURRENT_STATE.md`
   is explicitly a *historical checkpoint record* (README item 2), so its references are
   provenance, not defects. Prose, not links — this guard does not judge it.
3. **A new `tests/**` file is executed by no generic gate.** `economic-seam-engine.yml`
   and `console-contract.yml` select `tests/**` but execute a *derived* guard domain; a
   new file that names neither seam is executed by neither. That is why this change ships
   its own gate. Widening a generic whole-suite execution surface remains a sovereign
   decision, as recorded in earlier cycles.

## 6. Next-action block

**Current state.** `main` = `bb19aabd…`; production `/api/version` `source_revision` =
`bb19aabd…`, `revision_conflict: false`; `main` check-runs all `success`; architecture 11
passed; full-suite failing/error set = the recorded 20-node baseline (`8d70e46e…`). **36**
open drafts, 0 non-drafts, all `base: main`.

**Evidence.** This record; the branch's three files; the measured commands in §3.

**Blockers.** (a) Merge execution is human-only (GOV-03); the draft queue awaits human
review. (b) CE-01 (`weaver.autonomy`) and FINDING F-01 remain sovereign-reserved. (c) The
`research/` guard repair and any generic whole-suite gate are separate authorizations.

**Authorized next action.** Human review of this PR alongside the existing queue. A later
cycle may take up follow-on 1 (one-token import repair + a gate) as its own bounded change.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; changing production
routing; adding an auth guard to `/api/webhook/github`; weakening any guard to manufacture
green.

**Completion condition.** This cycle is complete when this record and the three files are
reviewable, with `main` unmodified and no merge, deployment or acceptance claimed.
