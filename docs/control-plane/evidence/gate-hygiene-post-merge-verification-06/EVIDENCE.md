# EVIDENCE — gate-hygiene/post-merge-verification-06

Bounded objective: re-derive, from live evidence, whether the `main` movement that
followed the sovereign merge of the GATE-07 batch is behaviour-preserving, and record the
resulting state of the still-open GATE-07 work.

This pass is **evidence only**. No source, test, workflow, or policy change. No merge. No
push to `main`.

## 1. Provenance

| Item | Value |
| --- | --- |
| Repository | `Arkadia-Oversoul-Prism/Arkadia` |
| Observation time (UTC) | 2026-10-07T17:35–17:50 |
| BASE_MAIN (previous pass) | `74e8ea53a30213db8783e6733679d2f11903de0b` |
| MERGED_MAIN (this pass) | `1a9d5ce5646534bb24727bba81711accca885606` |
| Branch | `gate-hygiene/post-merge-verification-06` @ `1a9d5ce` |
| Working tree at branch point | clean (`git status --porcelain` empty) |

`origin/main` was re-fetched during the pass. The batch that the previous pass composed
and reviewed (PR #341, `gate07/batch-integration-review-01`) was **merged by the sovereign
at 17:34–17:35 UTC**, so this pass measures the integration result rather than the
pre-merge union.

### Merge commits landed (first parents verified locally)

| Merge | SHA | First parent |
| --- | --- | --- |
| #344 | `7f5ec610` | `74e8ea53` (BASE_MAIN) |
| #341 | `a8f336ba` | `7f5ec610` |
| #340 | `ca896de2` | `a8f336ba` |
| #336 | `0569ca00` | `ca896de2` |
| #335 | `53560fb5` | `0569ca00` |
| #332 | `0301adab` | `53560fb5` |
| #331 | `1a9d5ce5` | `0301adab` |

The chain is **linear**: each merge's first parent is the previous merge, so the cluster
landed in a single documented order and the pass-2 review evidence in #341 (`base
74e8ea5`) remains bound to a real ancestor of live `main`.

### Merge method and orphaned commit

#341 was merged as a **merge commit** (`a8f336ba`), not squashed: its second parent is the
reviewed head `21be12a`. The CI-attribution commit `c8b20817` was created at 17:34:40,
**after** the merge commit at 17:34:40 — a race between this pass's push and the
sovereign's merge. It is therefore **orphaned** (`git merge-base --is-ancestor c8b20817
origin/main` → false) and did not land. It changed a single documentation line in
`EVIDENCE.md` §7.4; its content is superseded by §4 of this document. No reviewable
content was lost.

## 2. Baseline test-debt fingerprint (node set unchanged)

Full suite, `-q -rEf --continue-on-collection-errors`,
`PYTHONPATH=<repo>/archive/legacy_python`:

| Tree | Result | Nodes | Node-set sha256 |
| --- | --- | --- | --- |
| `74e8ea5` (BASE_MAIN) | 10 failed, 1703 passed, 20 skipped, 1 error | 11 | `92d344d0fbeb…` |
| `1a9d5ce` (MERGED_MAIN) | 10 failed, 1743 passed, 21 skipped, 1 error | 11 | `92d344d0fbeb…` |

Both trees were measured in this pass — the baseline was **re-measured, not inherited**.

**Node-set sha256 is identical on both sides** (`92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413`).
The load-bearing claim is node identity, not counts: `+40 passed` is the batch's new guard
tests, not a repair or a regression. **Zero regression introduced by the seven merges.**

## 3. Guard set on merged main

The GATE-07 guards that the batch wired into CI, run together on `1a9d5ce`:

```
tests/test_worker_attention_composition.py
tests/test_attention_truthfulness.py
tests/test_router_clean_stop_contract.py
tests/test_gate07_strict_xfail_composition_reconciliation.py
tests/test_engineering_router_status_truthfulness.py
tests/test_scheduler_trajectory_conformance.py
tests/test_voice_authority_boundary.py
```

→ **74 passed, 1 skipped, 0 failed**.

The composition seam guard survives on `main`: the merged
`.github/workflows/weaver-mvp2-validation.yml` selects and executes
`tests/test_worker_attention_composition.py` (path filter ×2 + the `run:` list). The merge
did not drop the guard the union resolution existed to protect.

| Check | Result |
| --- | --- |
| `tests/architecture` (merged main) | **11 passed** |
| `api/main.py` line count | **2434** (budget 2600) |
| `python -m py_compile api/main.py` | OK |
| CP10 mutation boundary judge (merged main) | PASS |

## 4. CI on the merged batch

The combined status of #341's head read **failure** before merge, driven solely by
`Vercel – console`. That check is **pre-existing on `main` itself** — the commit status on
`main` @ `74e8ea5` already carried `Vercel – console: failure` alongside
`Vercel – arkadia-prism: success`. It is therefore not attributable to the batch. The
checks that are attributable read: `Full-history secret scan` pass, `Vercel Preview
Comments` pass, `Vercel – arkadia-prism` pass.

## 5. Remaining open GATE-07 work — #334

After the merge, exactly one GATE-07 PR remains open: **#334**
(`gate07/router-schema-vocabulary-closure`), head `3a29fdea`, base `17e626cd` — a base
that is now **stale** (behind live `main` by the whole batch).

The pass-2 review predicted that #334 would conflict with the merged workflow. That
prediction is **confirmed by measurement**: applying #334's diff onto `1a9d5ce` yields a
three-region textual conflict in `.github/workflows/weaver-mvp2-validation.yml`.

The conflict is **resolvable as a union** — the two PRs append to different places:

| Region | `main` (ours) | #334 (theirs) | Union resolution |
| --- | --- | --- | --- |
| `push` path filter | composition-guard lines | closure-guard line | ours **then** theirs |
| `pull_request` path filter | composition-guard lines | closure-guard line | ours **then** theirs |
| `run:` step | new composition-seam **step** (sibling) | one test line for the truthfulness step | theirs line joins the run list, ours step follows |

Composition probe on `1a9d5ce` with the union resolution applied:

| Check | Result |
| --- | --- |
| `git apply --3way` | conflict (expected, resolved by hand) |
| guard set incl. closure guard | **53 passed, 1 skipped, 0 failed** |
| YAML parse | OK |
| CP10 judge on #334's 4 paths | PASS (`JUDGE_EXIT=0`) |

No conflict markers remain after resolution. The union keeps **both** guards — the
truthfulness step gains `tests/test_router_schema_vocabulary_closure.py` and the
composition-seam step is preserved as a sibling.

## 6. What this pass changes for the sovereign

- The seven-PR batch merged as a **linear, behaviour-preserving** cluster: node-set
  fingerprint identical to BASE_MAIN, architecture 11/11, budget 2434/2600, boot code
  compiles.
- The only surviving GATE-07 PR, **#334**, needs a **rebase onto `1a9d5ce`** before it can
  merge; its workflow conflict is a mechanical union, proven to pass 53/53 with the
  closure guard in the CI step.
- #334 was **not** touched by this pass. Rebasing it is the next bounded task and requires
  a fresh PR head — an act of mutation on that PR's own branch, which this pass does not
  perform.

## 7. Authority boundary

- No merge. No push to `main`. No force-push.
- No change to `api/main.py`, to any workflow, or to any test in this pass.
- Evidence artifacts confined to `docs/control-plane/evidence/gate-hygiene-post-merge-verification-06/`.
- The next permitted action is **sovereign review**; the next bounded engineering task is
  the #334 rebase, to be performed on a dedicated branch and offered as a PR.
