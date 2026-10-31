# Evidence — lane currency after the #601 merge

**Workstream:** gate-hygiene / lane-doc-currency
**Branch:** `gate-hygiene/lane-currency-post-601-refresh-01`
**Base:** `main` `6776ee103525c9d097d73e3a47493748ff3efc2c` (PR #601 merge)
**Observed:** 2026-10-31T23:19Z–23:5xZ
**Authority:** human retains merge, production-deployment and acceptance. No merge,
deployment or acceptance is claimed here.

## 1. Defect

`main` `afb9b6d7` is **red** on its own lane gate. Re-measured live, read-only:

```
$ python scripts/lane_state.py --check --verify-live
  DRIFT PR #601 (lane 4 open_prs) is recorded as open but is MERGED (merge commit 6776ee10); re-measure the lane PRs and re-point the lane
  DRIFT lane 4 (AGENT-04-ARKANA-WEAVER-LAB.md) declares PR #601, which is MERGED -- the lane instruction points a successor agent at a dead thread; re-point it at a live lane PR
EXIT=1
```

Cause, not intent: PR #602 (merge `afb9b6d7`) refreshed the snapshot at `6ccb021f`
and recorded lane 4's PR #601 as open. The **human sovereign** then merged #601 as
`6776ee10`, so that recorded claim became stale. No single PR could observe this —
#602 was green against the tree it was built on.

This is the composition hazard already recorded in `AGENTS.md`: a snapshot written
against one `main` cannot be validated by the branch that wrote it once `main` moves.

## 2. Repair

Re-derived, not hand-edited:

```
$ python scripts/lane_state_refresh.py --write --base-main 6776ee10
lane 4: doc_guard=idle  active=#None open=[] merged=[422, 428, 601]
unassigned open PRs: []
```

- `lane-state.json` — `base_main` `6776ee10`; lane 4 `open_prs` empty, #601 moved to
  `merged_prs` with `merge_commit_sha 6776ee103525c9d097d73e3a47493748ff3efc2c`.
- `AGENT-04-ARKANA-WEAVER-LAB.md` — an idle declaration appended *after* the #601
  pointer block, so the guard's last-wins rule reads the idle state. The #601 pointer
  is retained verbatim rather than rewritten (the `AGENTS.md` insertion-only rule).

The merge is recorded as the human sovereign's act, not this workstream's. The
governing documents reserve merge authority to the human:

- `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md:148` — "Agents may inspect,
  implement, test, document, commit to their assigned branch, and update their PR.
  They may not merge any PR, deploy production, or declare product acceptance."
- `AGENTS.md` — "Human merge, production-deployment, and acceptance authority remains final."

`AGENTS.md` grants Weaver a bounded standing merge authority, and the binding
SHARED-CONTRACTS/PRISM-UI-RECONCILIATION documents forbid it. **The conflict was not
resolved by an agent.** It is resolved by the record: the human merged #601 and #602
directly (`merged_by = Arkadia-Oversoul-Prism`, 0 reviews), consistent with the
incident record `docs/control-plane/evidence/unauthorized-merge-3a1088c5-01/INCIDENT.md`,
which classifies an agent-issued merge as a breach and states that "authorization
cannot be retroactively inferred from a subsequent green result." No merge was
performed by this workstream.

## 3. Proof

| Check | Command | Result |
|---|---|---|
| Lane gate (final tree) | `python scripts/lane_state.py --check --verify-live` | **exit 0** — "lane instruction docs consistent with snapshot (4 guarded lanes)" |
| Lane gate (main `afb9b6d7`) | same | **exit 1** — the two DRIFT lines in §1 |
| Targeted suite | `pytest tests/test_lane_instruction_doc_currency.py -q -rEf` | **49 passed** |
| Path admissibility | `printf '<path>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | PASS |

Environment note: `--check --verify-live` must run on a tree whose HEAD descends from
the snapshot's `base_main`. On the un-merged branch it correctly reports
`base_main ... is not an ancestor of HEAD ... freshness is UNKNOWN` — a fail-closed
reading, not a defect.

## 4. Boundaries

- No `main` write, no force-push, no bypass of repository protection. `main` is
  unprotected with zero rulesets (`GET /branches/main` → `"protected": false`), so the
  `AGENTS.md` instruction is the only control in force — recorded, not repaired here;
  it is sovereign-only.
- No protected authority, identity, K15/K3 governance or deployment configuration touched.
- `api/main.py` untouched (line budget unaffected).
- Lane 4 at zero open PRs is a **deficit**, not a resting state: the next action is lane
  4's next bounded draft PR from freshly fetched `main`. Opening it is deliberately not
  done here — this slice repairs the gate that would judge it.
