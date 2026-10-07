# WORKSTREAM_STATE — gate07 / batch integration review 01

| field | value |
|---|---|
| workstream | `gate07/batch-integration-review-01` |
| subject | open GATE-07 batch, **pass 2 union**: PRs #331, #332, #334, #335, #336, #340, #344 (pass 1 six: #329, #331, #332, #334, #335, #336 + #330) |
| base | `main` @ `74e8ea53a30213db8783e6733679d2f11903de0b` |
| pass | 2 |
| status | **IMPLEMENTED** — integration measured; candidate ready for sovereign review |
| authority required | sovereign review; sovereign merge of the batch (or of the individual PRs) |

## State

- Pass 2 (EVIDENCE §7) **supersedes the pass-1 batch scope**. #344
  (`gate07/strict-xfail-reconciliation-companion-01` @ `0127780c`) carries #342 and #343
  **byte-identically** and supersedes #329 (removes its `strict=True` xfail, re-materializes the
  assertion as a live invariant). Merge set is now
  **{#331, #332, #334, #335, #336, #340, #344}**; #329/#330/#342/#343 are superseded.
- The serialization seam is **#334 × #344** — the same three conflict regions pass 1 found
  between #334 and #329, because #344's workflow contribution is byte-identical to #329's. The
  pass-1 `weaver-mvp2-validation.resolved.yml` union is **byte-identical** to the resolution for
  the new union; it was not regenerated.
- Composed tree (union): GATE-07 guard set **91 passed, 1 skipped** (no xfail — #344 resolves
  it); full suite **10F/1760P/21S/1E** vs baseline **10F/1703P/20S/1E**. Failing/error node set
  sha256 `92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413` — **identical** on
  both sides. `tests/architecture` **11 passed**. CP10 `--judge` **PASS**. Regression: **unchanged**.

## Next bounded task

Sovereign reviews this packet. If the batch (any superset containing both #334 and #344) is to be
merged, use the §3/§7.3 union resolution so neither PR's guard is dropped from the workflow's
`push`/`pull_request` path filters. #329/#330/#342/#343 should be closed as superseded by #344.
**Re-measure #344's head immediately before merging it** — it is under an active session and may
have moved past `0127780c`.

After that, the two recorded router defects remain their own bounded workstreams (do not fold
them in here): the `select_next_move` clean-stop contract (now repaired by #344, so this is
closing), and executing the status-vocabulary decision recorded in #332 for the live trajectory.

## Deterministic next-action block

- **Current state:** integration review complete (pass 2); evidence + resolved workflow committed on this branch.
- **Evidence:** this directory (`EVIDENCE.md` §1–§6 pass 1, §7 pass 2; `WORKSTREAM_STATE.md`, `weaver-mvp2-validation.resolved.yml`).
- **Blockers:** none for review. A batch merge is serialization-constrained (#334 × #344 conflict).
- **Authorized action:** sovereign review; sovereign merge.
- **Forbidden:** merge, self-authorize, push to `main`, mutate any subject PR, expand scope.
- **Completion condition:** sovereign merges the batch (or the individual PRs); `main` advances;
  next pass reconstructs state from the new `main`.
