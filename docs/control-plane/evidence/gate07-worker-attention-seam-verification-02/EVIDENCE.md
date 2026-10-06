# Gate-07 — independent verification of PR #329 (worker→attention composition seam)

**Workstream:** `gate07/worker-attention-seam-verification-02`
**Subject:** PR #329 `gate07: pin the worker→attention composition seam` (head
`9c7c57644f1b383ca644fc2cd99d3375e6133112`; pass 2 verified `58ac44b`, superseded — see §9)
**Base:** `main` @ `4587890efe0a4090aa9ffbf55413bcb4fe01e2bd` (#327)
**Authority:** verification + evidence only. No merge, no push to `main`, no code change to
the subject PR, no scope expansion.
**Status:** VERIFIED — candidate ready for sovereign merge.

## 1. Why this pass exists

PR #329 claims three things that are easy to assert and hard to check:

1. the worker→attention seam (what the hourly scheduler actually invokes) is pinned
   end-to-end, not just its two halves;
2. the guard is **non-vacuous** — it fails when the seam breaks;
3. the guard is **executed** by a workflow, not merely triggered.

A guard can be green and still prove nothing (the repository has already paid for this
lesson twice: a `run:`-block guard that read an unavailable `steps.<id>.outcome`, and a
job that executed zero tests because a collection error interrupted the session). This
pass re-derives each claim from live evidence rather than from the PR body.

## 2. Reconstruction (live, this pass)

| item | measured value |
|---|---|
| `main` | `4587890efe0a4090aa9ffbf55413bcb4fe01e2bd` (#327) |
| PR #329 base / head (pass 2) | `main` / `58ac44b1963ff0250aa34bc7bdcc48efc5c711ae` |
| PR #329 head (pass 3, current) | `9c7c57644f1b383ca644fc2cd99d3375e6133112` |
| PR state | open, not draft, `mergeable: true`, `auto_merge: none` |
| changed paths | `.github/workflows/weaver-mvp2-validation.yml`, `docs/control-plane/evidence/gate07-worker-attention-composition-guard-01/{EVIDENCE.md,WORKSTREAM_STATE.md}`, `tests/test_worker_attention_composition.py` |
| `api/main.py` | not touched; `py_compile` OK; **2432** lines (< 2600 budget) |
| CP10 mutation-boundary judge over the changed paths | **PASS** |

### 2.1 Baseline re-measured (dependencies installed)

The repository's declared baseline is stale (contract §BASELINE DEBT cites
`804/54/12/2` at `6038989`; repo memory records `~20F/1039P`). Neither reproduces here.
Measured with `pip install -r requirements.txt` so the result is not dominated by
`ModuleNotFoundError` noise:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
main     : 10 failed, 1585 passed, 20 skipped, 1 error        (134.03s)
PR #329  : 10 failed, 1590 passed, 20 skipped, 1 xfailed, 1 error  (135.48s)
```

Failing/error **node set** (identity, not counts) sha256:

```
f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48   (11 nodes, both sides)
```

This is byte-identical to the fingerprint PR #329 documents in its own evidence, and the
node-set delta is **zero**. The `+5 passed` is exactly the new guard file (5 pass + 1
strict xfail). Regression: **unchanged**.

`tests/architecture`: **11 passed** on `main` and on the PR head.

> Counts are not the invariant. The environment-dependent absolute baseline does not
> match the contract, so attribution is made from the sorted `FAILED`/`ERROR` node list
> only — the technique the repository already records as the correct one.

## 3. Non-vacuity — proven by mutation, not inspection

The guard drives the real `EngineeringWorker.run()` (the function the scheduler calls)
against a synthetic trajectory inside a `tmp_path` sandbox. To test whether the
assertions are bound to **production** code and not to the guard's own monkeypatch, three
independent source-level mutations were applied to a throwaway copy of
`weaver/engineering_worker.py` and the guard re-run:

| # | mutation | guard result |
|---|---|---|
| 1 | `_record_attention` returns the route result unchanged (seam never consults the builder) | **3 failed** |
| 2 | event built but never appended to the outbox (non-durable stop) | **2 failed** |
| 3 | event built and recorded but not projected onto the result (silent stop) | **2 failed** |

Every realistic way the chain can break at the seam reddens the guard. The detector is
not disarmed by the seam's own test doubles.

## 4. The recorded defect is real, not asserted

The strict xfail documents a router-side defect. It was reproduced independently against
the PR head:

```
trajectory: moves: [{id: DONE, status: completed}]   # a genuine clean completion
select_next_move -> (None, ['no legal pending move (all complete or dependencies unresolved)'])
worker.run()     -> status NO_LEGAL_MOVE
                    event_type  WEAVER_BLOCKED
                    severity    HIGH
                    action_required True
                    push_delivery   True
                    channels    ('tasks', 'keep', 'push')
```

`_engineering_result_is_blocked()` treats `NO_LEGAL_MOVE` **with any blockers** as
blocked, and `select_next_move()` always emits the `no legal pending move` blocker when it
finds no routable move. So a healthy idle session composes a pushed HIGH `WEAVER_BLOCKED`
— a false alert every hour. The guard's negative control pins exactly this, and the
`strict=True` xfail flips to a failure when the router's blockers contract is repaired in
a separate bounded workstream.

The live trajectory (`TRAJECTORY-CONSOLE-COMPLETION-01.yaml`) currently routes to
`NO_LEGAL_MOVE` for the same class of reason (two moves sit at `merged_acceptance_pending`,
a status the router does not recognize), so the defect is not hypothetical.

## 5. CI wiring

Run `37453491606` at head `58ac44b` — **success**, including the new step
*Worker→attention composition seam guard*. Both guard files appear in the `push` **and**
`pull_request` path filters, which the guard itself asserts are identical sets (a guard
absent from the `pull_request` filter is judged by nothing until after the merge).

Note: the earlier claimed run `37444871122` was at head `076230f9…`, not `58ac44b` — it
is a real green run of the same workflow but not evidence about the current head. The
current-head run is the one cited above.

## 6. Result

**VERIFIED.** The guard is end-to-end, non-vacuous, executed by CI, and records a real
defect with a strict xfail. No repository change is proposed for PR #329; it is ready for
sovereign merge.

## 7. Newly recorded, not executed (proposed workstream)

The two evidence documents that PR #329's own record defers to are **encoding-corrupted**,
and — unlike the single-encoding cases the repository has repaired before — they are
**double-encoded**, with a *mixture* of double-encoded and single-encoded sequences in the
same file:

| document | raw mojibake | after 1 CP1252 pass | after 2 passes |
|---|---|---|---|
| `gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md` | 403 | 10 | 10 |
| `gate-hygiene-queue-drain-verification-01/WORKSTREAM_STATE.md` | 14 | 0 | 0 |

The sequence `U+00E2 U+20AC U+0161 U+00C3 U+201E U+00C3 U+00AE` (a double-encoded `—`) needs
**two** CP1252 passes, while `U+00E2 U+20AC U+201D` (a single-encoded `—`) on the same file
needs one. A
uniform single-pass repair therefore leaves residual mojibake in the first document and is
lossy (5 line-decode errors) in both; a uniform two-pass repair is worse. The correct
transform is a bounded-fixpoint decode applied per line, and its correctness invariant
(`corrupt(repair(x)) == x` on the corrupted domain, untouched lines byte-identical) has not
been established for these files.

Because the repair is **not decidable by a uniform rule**, it is classified as its own
bounded workstream and **not** attempted here. Attempting it inside a verification pass
would be scope expansion and would risk writing guessed text into evidence documents.

## 8. Authority

- Merged: **no**. Pushed to `main`: **no**. Force-pushed: **no**.
- This pass produced a verification record and a PR comment. The subject PR (#329) is
  untouched.
- Next authorized action: sovereign review and merge of PR #329.

## 9. Pass 3 — reconciliation against the current subject head (2026-10-06)

Pass 2 verified PR #329 at `58ac44b`. The subject PR then advanced to head
`9c7c57644f1b383ca644fc2cd99d3375e6133112`. This section re-derives the three claims
against that head and reconciles the citations above. It is an append, not a rewrite of
pass 2's measurements, which stand for the revision they name.

| item | pass-2 value | pass-3 measured value |
|---|---|---|
| PR #329 head | `58ac44b196…` | `9c7c57644f1b383ca644fc2cd99d3375e6133112` |
| diff `58ac44b..9c7c5764` | — | docs only (`…composition-guard-01/{EVIDENCE.md,WORKSTREAM_STATE.md}`); no `.py`/`.yml` |
| guard file (seam + attention + router halves) | 4 passed, 1 xfailed | `23 passed, 1 xfailed` |
| `tests/architecture` | 11 passed | 11 passed |
| full suite | 10F/1590P/20S/1X/1E | 10 failed, 1590 passed, 20 skipped, 1 xfailed, 1 error |
| failing/error node-set sha256 | `f3e7364703…` | `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` |
| CP10 mutation-boundary judge | PASS | **PASS** (exit 0) |

Because the pass-3 delta touches documentation only, pass 2's non-vacuity proof transfers
to `9c7c5764` unchanged; it was nevertheless re-run against that head to confirm:

| # | mutation of `weaver/engineering_worker.py` | guard result |
|---|---|---|
| 1 | `_record_attention` returns the route result unchanged | **3 failed**, 2 passed, 1 xfailed |
| 2 | event built but never appended to the outbox | **2 failed**, 3 passed, 1 xfailed |
| 3 | event built and recorded but not projected onto the result | **2 failed**, 3 passed, 1 xfailed |

Identical to pass 2. **Non-vacuity re-confirmed at `9c7c5764`.**

### 9.1 CI execution re-observed at the current head

Run `37465288949` (*Weaver MVP2 validation*, `pull_request`) at head
`9c7c57644f1b383ca644fc2cd99d3375e6133112` — **success**. Its job log shows the
*Worker→attention composition seam guard* step executing and reporting
**`14 passed, 1 xfailed in 0.22s`** — a non-zero test count, so the step ran tests rather
than being green on an empty selection. The run cited in §5 (`37453491606`) is correct for
`58ac44b`; the current-head evidence is this run.

### 9.2 Encoding hygiene of this pass's own artifacts

Both documents changed by this PR are **Cyrillic-free** (U+0400–U+04FF count = 0) at this
head, as are PR #329's four changed paths — so this pass neither introduces nor carries
forward the mojibake class recorded in §7.

### 9.3 Result

**VERIFIED at `9c7c57644f1b383ca644fc2cd99d3375e6133112`.** The three claims hold at the
current subject head; the only delta from pass 2 is documentary. PR #329 remains ready for
sovereign review and merge; this pass proposes no change to it.
