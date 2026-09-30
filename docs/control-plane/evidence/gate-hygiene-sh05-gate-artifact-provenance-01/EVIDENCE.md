# `SH-05` — provenance of the `gate/` artifact regression (ledger rows 47–48)

**Workstream:** `gate-hygiene` (standalone test-hygiene; explicitly *not* an architectural gate)
**Classification:** `IMPLEMENTED` (evidence-only) — **READY FOR SOVEREIGN MERGE**
**Authority required:** merge only. The *disposition* of `SH-05` is a sovereign call; this pass
does not make it.
**BASE_MAIN:** `df7a99a067382401c00de5e7bbaaac0125ba2088`
**Branch:** `gate-hygiene/sh05-gate-artifact-provenance-01`

> This PR is **evidence only**. It modifies **no test, source, workflow, governance, or
> constitutional file**. `api/main.py` is untouched (2519 / 2600). CP10 mutation-boundary
> judge: **PASS**.

---

## 1. Why this artifact exists

`SH-02` (the `STALE_ASSERTION` migration) is **exhausted**: 19 nodes green on `main`, 12 carried
by four open PRs, 4 sovereign decisions, **0 left to batch** (PR #140). PR #141 then settled the
`F-02` contradiction with PR #138 §7. With both settled, the `gate-hygiene` queue's only
unclaimed, non-sovereign items are the two `ENV / ARTIFACT` rows — registered as `SH-05`, whose
fate every `WORKSTREAM_STATE.md` in this workstream lists as *"sovereign call"* with **no
evidence attached**.

`SH-05` has therefore been carried, unresolved, across at least six evidence passes. This pass
supplies the missing evidence: **what happened to the `gate/` artifact, when, and by whose
commit.** It does not decide what should happen next.

## 2. The two nodes, and why `ENV / ARTIFACT` is the wrong bucket

| ledger row | node |
|---|---|
| 47 | `tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists` |
| 48 | `tests/test_gate_status.py::test_gate_files_and_fetch_handling` |

The classification ledger (row 47–48) buckets these as **`ENV / ARTIFACT`** — *"the test depends
on something outside the repository working tree"* — and states:

> Neither `index.html` nor `gate/` exists at the repository root. They exist only under
> `static/index.html` and `archive/legacy_frontend/gate/index.html`. `conftest.py` does not
> `chdir`. These tests reference a served-artifact layout that is not in the tree.

That is **true of the current tree but false of the repository's history**, and the difference
changes the disposition.

## 3. Finding: this is a *tracked-artifact regression*, not an environment mismatch

Both paths **were** tracked at the repository root, **added at Genesis**, and were **deleted by
two ordinary commits**. Provenance is exact and complete.

### 3.1 Both paths were added at the root commit

```
$ git log --all --oneline --diff-filter=AD -- index.html gate/
f6718b9 Recalibration: archive dead execution stacks …, orphaned duplicates (gate, …)   D  gate/gate.css
                                                                                        D  gate/gate.js
                                                                                        D  gate/index.html
377cdb3 Day 36: fix stale URLs, archive legacy Python                                   D  index.html
9ab26fc Genesis: Stone 5 Ascension Finalized                                            A  gate/gate.css
                                                                                        A  gate/gate.js
                                                                                        A  gate/index.html
                                                                                        A  index.html
```

All four paths are `A` (added) at `9ab26fc`, the root commit — the same Genesis commit that
added the two test files themselves:

```
$ git log --follow --oneline -- tests/test_gate_serve_script.py
9ab26fc Genesis: Stone 5 Ascension Finalized
$ git log --follow --oneline -- tests/test_gate_status.py
9ab26fc Genesis: Stone 5 Ascension Finalized
```

Test and artifact were introduced **together**, at the same commit, asserting the same layout.

### 3.2 Negative control — the nodes were green at Genesis

The test set has a **green revision**. Reproduced in a detached worktree at the root commit:

```
$ git worktree add /tmp/wt_gen 9ab26fc && cd /tmp/wt_gen
$ PYTHONPATH=…/archive/legacy_python python -m pytest \
      tests/test_gate_serve_script.py tests/test_gate_status.py -q
3 passed in 0.17s
```

This is the decisive discriminator against the sibling finding `F-02` (`tests/test_steward_filter.py`,
rows 27–29), where the negative control at Genesis returns `3 failed, 5 passed` — i.e. **no green
revision ever existed**, so that node set cannot be a drift. Here a green revision exists and was
**lost**. `ENV / ARTIFACT` ("something outside the repository") does not describe a path the
repository itself tracked and then deleted.

### 3.3 Exact regression points — the two nodes were lost by two *different* commits

```
$ git log -1 --format='%h | %ad | %s' --date=short 377cdb3
377cdb3 | 2026-03-23 | Day 36: fix stale URLs, archive legacy Python
$ git log -1 --format='%h | %ad | %s' --date=short f6718b9
f6718b9 | 2026-07-15 | Recalibration: archive dead execution stacks (engine/parsers/schemas),
                     orphaned duplicates (gate, legacy Java sonata, GovernanceSpirit nested dup); …
```

Running the same test set immediately **before** each removal isolates the regression to each
commit:

| revision | `test_root_index_redirect_and_script_exists` | `test_gate_files_and_fetch_handling` |
|---|---|---|
| `9ab26fc` (Genesis) | passed | passed |
| `575232e` (`377cdb3^`) | **passed** | passed |
| `377cdb3` — removes root `index.html` | **FAILED** | passed |
| `c3fa6cd` (`f6718b9^`) | FAILED | **passed** |
| `f6718b9` — removes `gate/` | FAILED | **FAILED** |
| `df7a99a` (current `main`) | FAILED | FAILED |

So ledger row **47** regressed on **2026-03-23** (`377cdb3`) and row **48** on **2026-07-15**
(`f6718b9`). They are two independent regressions that the ledger collapsed into one bucket.

Both commits are **deliberate** — their subjects say `archive`, and both are working-tree
relocations, not accidents:

### 3.4 The artifacts were relocated, not destroyed — byte-identical

Every removed artifact survives in an `archive/` path, and each is **blob-identical to its
Genesis blob**:

| Genesis path (removed) | current path | blob comparison |
|---|---|---|
| `index.html` | `archive/legacy_python/index.html` | **IDENTICAL** |
| `gate/index.html` | `archive/legacy_frontend/gate/index.html` | **IDENTICAL** |
| `gate/gate.js` | `archive/legacy_frontend/gate/gate.js` | **IDENTICAL** |
| `gate/gate.css` | `archive/legacy_frontend/gate/gate.css` | **IDENTICAL** |

Verified by blob hash (`git rev-parse 9ab26fc:<path>` vs `git rev-parse HEAD:<path>`). The Gate
UI is **not lost**. It was intentionally archived.

### 3.5 The launcher was not updated — an unambiguously stale reference

`scripts/serve-gate.sh` is also **blob-identical to Genesis**, so it still points at the path
that no longer exists:

```
URL="http://localhost:${PORT}/gate/"
```

The script serves the repository root (`python -m http.server`) and opens `/gate/` — a 404 today.
`f6718b9`'s own subject records that it archived the *"orphaned duplicates (gate, …)"*; the
launcher was left dangling by that same change.

## 4. What this does and does not establish

**Established (facts, re-runnable):**

1. `gate/` and root `index.html` were tracked at Genesis, added by the same commit as the two
   tests.
2. The two tests passed at Genesis — a green revision exists.
3. The two nodes regressed at two different commits (`377cdb3` 2026-03-23; `f6718b9` 2026-07-15).
4. Both removals were deliberate `archive` relocations; all four artifacts survive byte-identical.
5. `scripts/serve-gate.sh` is stale — it still targets the removed `/gate/` path.
6. `ENV / ARTIFACT` mis-buckets this pair: the dependency is *inside* the repository's history.

**Not established — this pass makes no such claim:**

- **No disposition.** Whether the Gate UI is retired, relocated into `web/public_prism`, or should
  be restored is **not decided here**. This is exactly the sovereign question
  `docs/phase1/CONTINUATION_LEDGER.md` §"Carried forward" item 2 poses, and it remains open.
- **No test edit and no artifact restoration.** Repairing the assertion to accept
  `archive/legacy_frontend/gate/` would ratify the archiving; restoring the artifact would ratify
  the launcher. Those are opposite product answers. Choosing one inside a hygiene pass would be a
  product decision taken by stealth.
- **No ledger reclassification.** `BASELINE_TEST_DEBT_CLASSIFICATION.md` is another workstream's
  artefact and is append-only in flight (three open PRs edit it). The proposed correction to rows
  47–48 is recorded **here** for a follow-up, **not applied**.

## 5. Note on the CP10 gate that caused one of these deletions

`f6718b9` — the commit that removed `gate/` and regressed row 48 — is also recorded in
`AGENTS.md` as the pass that first turned the CP10 mutation boundary red on `main`, because
`scripts/cp10_mutation_boundary_policy.py`'s allowlist had never enumerated the `archive/` tree
it was creating. The same commit produced both a deleted served artifact and a gate-allowlist
omission. Recorded as context; no action proposed.

## 6. Proposed next bounded tasks (NOT executed)

| id | task | bucket | authority |
|---|---|---|---|
| `SH-05` | **Decide the Gate UI's fate** — retired, relocated into `web/public_prism`, or restored to root? Options and their consequences: `docs/phase1/CONTINUATION_LEDGER.md` §2. | product decision | **sovereign** |
| `SH-05a` | *If* the Gate UI is retired: re-point both assertions at the archived path (or delete the nodes) and drop the stale `/gate/` URL from `scripts/serve-gate.sh`. Test-only + one script line. | hygiene | sovereign gate on `SH-05` |
| `SH-05b` | *If* the Gate UI is live: restore the four artifacts to root (byte-identical blobs already exist) and re-verify `test_gate_status.py`'s `/sanctum/status.json` contract. | product | sovereign gate on `SH-05` |
| ledger | Correct rows 47–48 from `ENV / ARTIFACT` to *tracked-artifact regression (relocated)*, in a pass that owns the ledger. | docs | deferred — ledger is in flight |

## 7. Non-claims

- **No production or runtime claim.** This is repository-history evidence only. The Gate-2
  `main → deployment → runtime` boundary recorded in `AGENTS.md` is untouched.
- **No gate status changes.** No gate is opened, closed, or promoted.
- **No baseline change.** Fingerprint re-measured this pass and **unchanged**:
  `32 failed / 1025 passed / 13 skipped / 2 collection errors`; `tests/architecture` **11/11**.
- **No merge, no push to `main`, no force-push, no self-authorization.**
- **No scope expansion.** No `DRIFT` node, no `R1/R2/R3` recon node, and no green `SH-02` node is
  touched.

## 8. Environment / reproduction

```
repo    : Arkadia-Oversoul-Prism/Arkadia
base    : df7a99a067382401c00de5e7bbaaac0125ba2088   (origin/main == main, tree clean)
history : COMPLETE — 1393 commits; root = 9ab26fc9f82f2672e770bf81dc2294d8230bac71
          (the clone was shallow at pass start; `git fetch --unshallow` restored ancestry so
           the Genesis comparison below is verifiable, not inferred)
python  : /usr/local/bin/python (pytest 9.1.1)
invoke  : PYTHONPATH=<repo>/archive/legacy_python python -m pytest <nodes> -q
```

Every command in §3 is re-runnable against the full clone. `git rev-parse 9ab26fc:<path>` vs
`git rev-parse HEAD:<path>` reproduces §3.4 without any worktree.
