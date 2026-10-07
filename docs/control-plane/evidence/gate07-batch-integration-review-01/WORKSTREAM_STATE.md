# WORKSTREAM_STATE — gate07 / batch integration review 01

| field | value |
|---|---|
| workstream | `gate07/batch-integration-review-01` |
| subject | open GATE-07 batch: PRs #329, #331, #332, #334, #335, #336 (plus #330, verification companion) |
| base | `main` @ `74e8ea53a30213db8783e6733679d2f11903de0b` |
| pass | 1 |
| status | **IMPLEMENTED** — integration measured; candidate ready for sovereign review |
| authority required | sovereign review; sovereign merge of the batch (or of the individual PRs) |

## State

- The six open GATE-07 PRs were composed, the single real conflict (`weaver-mvp2-validation.yml`,
  #329 × #334, three regions) resolved by union, and the composed tree measured end-to-end.
- Composed tree: GATE-07 guard set **81 passed, 1 xfailed**; full suite **10F/1737P/20S/1X/1E**
  vs baseline **10F/1703P/20S/1E**. Failing/error node set sha256
  `92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413` — **identical** on both
  sides. `tests/architecture` **11 passed**. Regression: **unchanged**.
- Two stale readings corrected: #336 is a 4-file change against its own base (32 files against
  `main` only because `main` re-added the deleted `solspire/voice_*` tree); #331 and #335 are
  disjoint, not redundant — the proposed "dedup verification" workstream is `CONTRADICTED` and
  was not created.

## Next bounded task

Sovereign reviews this packet. If the batch (or any superset containing both #329 and #334) is
to be merged, use the §3 union resolution so neither PR's guard is dropped from the workflow's
`push`/`pull_request` path filters. Individually, every subject PR merges cleanly today.

After that, the two recorded router defects remain their own bounded workstreams (do not fold
them in here): the `select_next_move` clean-stop contract (flips #329's strict xfail), and
executing the status-vocabulary decision recorded in #332 for the live trajectory.

## Deterministic next-action block

- **Current state:** integration review complete; evidence + resolved workflow committed on this branch.
- **Evidence:** this directory (`EVIDENCE.md`, `WORKSTREAM_STATE.md`, `weaver-mvp2-validation.resolved.yml`).
- **Blockers:** none for review. A batch merge is serialization-constrained (#329 × #334 conflict).
- **Authorized action:** sovereign review; sovereign merge.
- **Forbidden:** merge, self-authorize, push to `main`, mutate any subject PR, expand scope.
- **Completion condition:** sovereign merges the batch (or the individual PRs); `main` advances;
  next pass reconstructs state from the new `main`.
