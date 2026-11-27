# GOV-04 governance guard is red on `main` — two near-miss literals, repaired test-side

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`, cycle 14
- **Observed:** 2026-11-24T18:07Z onward
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Change:** `tests/test_gov04_bounded_merge_delegation.py` only. No application code, no
  governance document, no authority surface.

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` | `git rev-parse origin/main`; local `HEAD` agrees |
| production `source_revision` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`, `revision_conflict: false` | `GET https://arkadia-qzu4.onrender.com/api/version` x3 |
| open PRs | **46**, **45** draft | `GET /pulls?state=open` |
| `main` check-runs | `boot-syntax`, `console-contract`, `lane-doc-currency`, `posture-currency`, `test`, `Full-history secret scan` — all `success` | `GET /commits/<sha>/check-runs` |
| `api/main.py` | 2597 lines (budget 2600) | `wc -l` |

Production revision is sha-identical to `main`: **VERIFIED** source↔runtime. That is consistency
evidence, not acceptance.

## 2. Defect — measured, unowned

Full suite at `main`:

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
-> 20 failed, 4253 passed, 22 skipped, 1 error in 287.88s
```

Sorted failing/error set: **21** nodes, outcomes sha256
`4118e2ff698f90bb018a8f396c7c729be8cb55cb6d816683a2cd1feb4c8ee916`.

Removing exactly one node from that set reproduces the canonical recorded baseline
**`8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb`** (20 nodes, outcomes
form). The removed node is:

```
tests/test_gov04_bounded_merge_delegation.py::test_bounded_merge_is_exact_head_and_protected_fail_closed
```

So the governance amendment merged as `fd0a4fdc` (#722, 2026-11-24) added **exactly one** failing
node to `main` — its own guard — and nothing else in the set moved. Attribution is by node
identity, not by count.

The assertion failure is a **test-side literal pin**, the recurring class recorded in `AGENTS.md`:

```
AssertionError: assert 'no auto-merge' in '# gov-04 — bounded merge delegation ...'
```

The authorization document states the prohibition twice, but never in the pinned wording:

| obligation | pinned literal | what the document actually says |
|---|---|---|
| no auto-merge | `no auto-merge` | `**No authorization:** auto-merge, …` and `This amendment does not enable auto-merge, …` |
| post-merge reconciliation | `post-merge` | `GitHub confirms the merge; record … and reconcile main afterward.` |

A second pinned literal, `post-merge`, was equally absent. Both properties **are** stated; only
the assertion's spelling was wrong. The defect is the assertion, not the governance content, so
the repair is test-side and the document is untouched.

No open PR touches `tests/test_gov04_bounded_merge_delegation.py` or the GOV-04 evidence
directory (checked across all 46 open PRs via `GET /pulls/<n>/files`), and `#724` edits the
authorization document without adding either literal. The node is unowned.

## 3. Repair

Two named detectors replace the two near-miss literals; the eight literals the document does carry
stay pinned verbatim:

```python
def _states_no_auto_merge(text):
    text = text.lower()
    return "auto-merge" in text and (
        "no authorization" in text or "does not enable auto-merge" in text)

def _records_post_merge_reconciliation(text):
    text = text.lower()
    return "post-merge" in text or ("reconcile main" in text and "afterward" in text)
```

This is not a weakening. `_states_no_auto_merge` requires the word `auto-merge` **and** an explicit
prohibition, so a document that merely mentions auto-merge fails; `_records_post_merge_reconciliation`
requires a post-merge act, so "merge the PR" alone fails. A new control node binds both detectors.

## 4. Controls — live, against the real document

Each mutation was applied to the real `AUTHORIZATION.md`, the guard run, then the file restored and
its sha256 verified (`sha256sum -c` → `OK`).

| control | mutation | result |
|---|---|---|
| auto-merge prohibition removed | deleted `auto-merge, ` from `**No authorization:** …` and from `does not enable …` | `2 failed, 3 passed` — both nodes red |
| post-merge reconciliation removed | `and reconcile main afterward.` → `and record the merge time.` | `2 failed, 3 passed` — both nodes red |
| restored | `cp` back + `sha256sum -c` | `AUTHORIZATION.md: OK` |

Both controls redden the guard; neither leaves it silent. A guard that stays green when the
obligation is deleted would not be a guard.

## 5. Result

```
python -m pytest tests/test_gov04_bounded_merge_delegation.py -q -rEf
-> 5 passed in 0.07s          (was 1 failed, 4 passed)
```

`--collect-only`: **4 → 5** nodes. The `+1` is the control node, measured per file rather than
inferred from a total.

The file is selected by a gate: `economic-seam-engine.yml` triggers on `tests/**`, so a change to
this file executes a gate rather than waiting for a human to run it.

### 5.1 CI on this branch head (`6056ad40`)

| check | conclusion |
|---|---|
| `test`, `boot-syntax`, `Full-history secret scan`, `posture-currency`, `provider-forensics`, `beta-beta-02-hausa` | `success` |
| `beta-beta-01-english` | `failure` — `external runtime did not return usable inference`, `errors: []` |
| `bundle-beta-evidence` | `failure` — consequential: it asserts `beta-01-english.json` has `status == "PASS"` |
| `native-arkadia-golden-workflow` | `skipped` |

Both failures are the external N-ATLAS inference provider, not this tree: the job's own event log
shows `RUN_FAILED` with an empty `errors` list, i.e. no usable inference returned. This change
touches one test file and one document and cannot affect an outbound inference call. A rerun of the
failed job was dispatched to distinguish intermittent provider behaviour from a deterministic
failure; the outcome is recorded on the PR, not asserted here.

### 5.2 Environment-only nodes — measured, not assumed

`web/arkadia_console/node_modules` was absent when the baseline above was measured, so the ten
`tests/test_mission_lifecycle_adapter_contract.py` nodes failed on
`AssertionError: the repository TypeScript compiler is missing at
…/node_modules/typescript/lib/typescript.js`.

After `corepack pnpm install --frozen-lockfile` in `web/arkadia_console` (exit 0, `typescript`
present), the same file reports:

```
10 passed in 3.27s
```

Those ten nodes are therefore **environment artifacts**, measured rather than classified by
inspection. Of the 21 failing/error nodes at `main` `fd0a4fdc`, ten are this class, one is the node
this PR repairs, and ten are owned or sovereign-reserved.

## 6. Composition

- `#690` also touches `tests/test_m05_files.py` (a different node: the `update_file` scoped
  signature). No overlap with this change.
- `#724` touches `docs/control-plane/evidence/gov-04-bounded-merge-delegation/AUTHORIZATION.md`
  and four governance documents; this change touches neither, so the two compose without conflict.
- This change is docs + one test file; `api/main.py` is untouched and stays at 2597 lines.

### 6.1 Finding (measured, unowned, **proposed not executed**) — the beta bundle gate cannot
### recover from a partial rerun

The rerun in §5.1 recovered `beta-beta-01-english` to `success`, and `bundle-beta-evidence`
then failed on a head where **both** legs had passed:

```
evidence files: ['evidence/beta-01-english.json']
statuses: {'beta-01-english.json': 'PASS'}
```

Only one of the two files arrived, so `expected - seen` was non-empty and the step exited 1. The
artifacts are not missing from the run — `GET /actions/runs/45458874109/artifacts` lists **both**
`beta-01-english-evidence` and `beta-02-hausa-evidence`. The bundle job's
`actions/download-artifact@v4` therefore resolved only artifacts uploaded in the **current
attempt**; the leg that succeeded in the earlier attempt was never re-run, so its artifact was not
re-uploaded and was not seen.

Consequence: after `gh run rerun --failed`, this gate is deterministically red on a head whose beta
validation passed, and a reviewer reading the red X cannot tell "validation failed" from "the
bundle was assembled from a partial attempt". Recovery currently requires a full rerun or a new
push, which is an undocumented operator dependency.

Proposed repair (not executed here — it edits a workflow this PR does not otherwise touch):
fetch the evidence through the run's artifacts API (which is attempt-agnostic, as measured above)
instead of `download-artifact@v4`, and split the single `exit 1` into `INCOMPLETE_ATTEMPT` and
`FAILED_EVIDENCE` verdicts so the red says which one it is. No open PR touches
`.github/workflows/n-atlas-external-beta.yml`; the item is unowned.

**Second observation, same head `24b8e999`.** On the push that carried this record, the *other* leg
failed — `beta-beta-02-hausa`, again `RUN_FAILED` / `external runtime did not return usable
inference` with `errors: []` — while `beta-beta-01-english` passed. The legs alternate which one
fails across attempts, which is provider-side intermittency rather than a tree property. The bundle
job failing when a leg genuinely fails is correct behaviour; the defect recorded above is the
separate case where both legs pass and the bundle still cannot be assembled.

## 7. Next-action block

**Current state.** `main` = `fd0a4fdc…`; production identical, `revision_conflict: false`; `main`
CI green; 21 failing/error nodes, of which one (this one) was the sole regression introduced by
`#722` and is repaired here. The other 20 decompose as recorded: 1 CE-01 (sovereign), 2 FINDING
F-01 (sovereign), 10 environment-only (`web/arkadia_console/node_modules/typescript` absent), 7
owned by open PRs (`#700` ×2, `#693` ×2, `#690` ×2, `#691`, `#698`).

**Evidence.** This record; the full-suite log and node-set hashes in §2; the two live controls in §4.

**Blockers.** (a) Merge execution is human-only; 45 drafts await human review, and `main` has not
advanced past `#722` in this workstream. (b) Branch protection and rulesets are absent. (c) CE-01
and FINDING F-01 are sovereign-reserved.

**Authorized next action.** Human review of the queue, including this PR and `#724`.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; editing the GOV-04
authorization to satisfy a test; weakening either detector; opening a PR with no measured defect.

**Completion condition.** This cycle is complete when this PR is reviewable, the GOV-04 guard
passes on its own tree, `main` is unmodified, and no merge, deployment or acceptance is claimed.
