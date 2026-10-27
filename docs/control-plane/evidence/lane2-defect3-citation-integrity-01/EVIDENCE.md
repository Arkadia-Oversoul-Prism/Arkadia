# Lane 2 — a repaired defect stayed cited as live on three surfaces

**Slice:** `gate10/lane2-defect3-citation-integrity-01`
**Base revision:** `36f53be22d753ffe269f05cbf3fb39212f744207` (measured live 2026-10-25)
**Lane:** 2 (NovaNet + Project Opportunity Radar)
**Disposition:** draft PR; no merge, deployment, or acceptance.

## 1. Objective

Stop lane 2's own contract surfaces from asserting that a defect repaired on 2026-10-15 is
still open, and pin the class so the wording cannot silently return.

## 2. The defect, measured

`8f4a6ea0` (2026-10-15 18:58) repaired MEASURED DEFECT 3 in `solspire/buyer_recon.py`:
`update_entry` had validated `status.upper()` and then persisted the value it was sent, so
`PATCH {"status": "conversation"}` answered `200` and stored a status outside the declared
vocabulary, while `create_entry` normalized. The repair normalizes into a local mapping
before the write.

Three surfaces still carried the pre-repair claim:

| Surface | Stale claim |
|---|---|
| `docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md` | the defect bullet asserted it was still live |
| `web/arkadia_console/src/components/opportunities/opportunityRadarContract.ts` | `offVocabulary` doc-comment: the backend "writes the value it was sent" |
| `tests/test_prism_opportunity_entry_flow.py` | two docstrings citing the defect as unrepaired |

The bullet also named a pinning test, `test_update_does_not_normalize_a_lowercase_status`,
that **does not exist in the repository**: `grep -rn` over `tests/` returns 0 matches, and the
identifier never appears in the file's history. The repair actually carries
`test_update_normalizes_a_lowercase_status` (line 919) plus a create-path control at 992. A
citation to a non-existent test is not reconcilable — it is recorded and corrected.

## 3. Why the client counter remains load-bearing

The repair **migrated no existing row**, so a row written before `8f4a6ea0` can still hold an
off-vocabulary status. `byStatus` is keyed on the declared tuple, so such a row has no column
and would silently fail to total. `offVocabulary` and the two seeding tests therefore stay.
The *premise* the citations asserted was wrong; the capability is not redundant. Correcting
the citations without deleting the capability is the whole point of the slice — deleting it
would have been the naive repair.

## 4. Repair

- Corrected the three surfaces, keeping the capability and recording the corrected history.
- Added a guard to `tests/test_prism_opportunity_entry_flow.py`:
  - `find_live_defect_citation` is **window-scoped (3 lines)**, not line-scoped. The measured
    stale form in `AGENT-02` wrapped the identifier and the claim onto separate lines, so a
    line-scoped detector would have missed the very instance it was written for.
  - The identifier and stale tokens are built by concatenation, so the guard's own prose can
    neither satisfy nor trip its detector.
  - `test_no_surface_still_cites_the_repaired_defect_as_live` runs it over all five surfaces.
  - **Negative control** feeds the verbatim pre-correction form; **positive control** feeds the
    repaired form. A guard silent on both is not a guard.

## 5. Evidence

**Measured at head** (base `36f53be2`):

| Command | Result |
|---|---|
| `pytest tests/test_prism_opportunity_entry_flow.py -q -rEf` | **91 passed** (was 88) |
| `pytest tests/test_prism_console_ci_wiring.py -q -rEf` | **30 passed** |
| `pytest tests/architecture -q -rEf` | **11 passed** |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py tests/test_prism_solspire_control_plane.py -q -rEf` | **61 passed** |
| `python scripts/console_contract_domain.py \| wc -l` | 51 guard files |
| `corepack pnpm build` (`web/arkadia_console`) | clean, `dist/assets/index-Ct9LTJ1F.js` |

**Live negative control, on the real file** (not a synthetic fixture): this document mutated
back to the stale form reddened the guard (`1 failed`); restored byte-identically, `1 passed`.

**Gate neutrality, corrected.** An earlier draft of this record claimed
`scripts/lane_state.py --check` is "exit 0 on both" trees. That is true only of the **offline**
variant. The CI gate runs `--check --verify-live`, which consults GitHub as the authoritative
oracle, and it is **exit 1 on pristine `main` `36f53be2` itself**, with byte-identical output to
this branch:

```
DRIFT PR #508 (lane 4 open_prs) is recorded as open but is CLOSED without merging
DRIFT PR #563 (lane 3 open_prs) is recorded as open but is CLOSED without merging
```

Measured cause — the snapshot was **correct when written and decayed in place**:

| Event | Time (2026-10-25) |
|---|---|
| `lane-state.json` last written (`3a1088c5`) | 05:13:01Z |
| `main` lane-doc-currency run `40164716935` → success | 05:13:04Z |
| PR #563 closed unmerged | 05:16:10Z (+3 min) |
| PR #508 closed unmerged | 15:23:41Z (+10 h) |

The only `main` run that passed was 3 seconds after the snapshot was written and 3 minutes before
the first closure. Nothing re-measured it afterwards, so the gate went red on a tree nobody had
changed — and it stays red until the snapshot is refreshed. `git diff HEAD --stat --
docs/control-plane/parallel-ui/lane-state.json` is **0 lines**: this slice never touched the file.
Repair is owned by **#568** (`lane-guard-fixed-scope-01`) and **#569** (`lane-state-refresh-01`),
both of which modify `lane-state.json`; it is recorded here, not executed here.

## 6. What this pass did not do, and why

- **`GET /api/echoes` (`api/main.py::echoes_feed`) still takes no `limit`/`offset`.** The
  public-echoes remainder is genuinely unreachable, so the "make the disclosed remainder
  retrievable" half of #564's objective is not satisfiable client-side. That is a backend
  contract proposal, not a UI slice; recorded, not executed.
- **The lane snapshot's `base_main` is stale** (`68acf89f` recorded vs `36f53be2` live). The
  guard reports this but exits 0, so the enforcement gap is #568's scope, not this slice's.
- **PR #574** (lane-state drift audit) and **#564** (AGENT-02 header re-point) are untouched. No
  duplicate PR was opened; this slice touches a different region of `AGENT-02` and the header
  pointer is deliberately left to #564.

## 7. Remaining uncertainty

- The guard's window is 3 lines. A stale claim phrased more than 3 lines away from the
  identifier would not be caught; widening the window risks matching unrelated prose. The
  measured instances all fall inside 3 lines.
- `_STALE_TOKENS` is a small vocabulary (`not repaired`, `unrepaired`, `open,`, `(open`). A
  novel phrasing of "still live" would evade it. It is a guard against the measured
  recurrence, not a general natural-language oracle.

## 8. Authorization

Human merge authority is final. This is a draft; nothing here is merged, deployed, or accepted.

## 9. Which open PR actually clears the red lane gate — measured, not inferred

Two open PRs both modify `lane-state.json`, and only one of them clears the gate. Measured by
substituting each PR's snapshot into this tree and running the CI command
(`scripts/lane_state.py --check --verify-live`):

| Snapshot substituted | Exit | Remaining DRIFT |
|---|---|---|
| `main` `36f53be2` (unmodified) | **1** | #508, #563 |
| `#569` `lane-state-refresh-01` | **1** | **#508** |
| `#568` `lane-guard-fixed-scope-01` | **0** | none |

`#569` refreshes the snapshot but **still lists #508 as open** (it was closed unmerged at
15:23:41Z, and the refresh re-derived before that), so merging `#569` alone leaves the gate red.
`#568` removes both stale entries and is the snapshot that actually clears it.

This is a composition fact neither PR can observe alone, and it is the same class recorded in
`#564`'s slice: a per-PR gate cannot see a cross-PR outcome. Recorded here; the repair is not
performed here, and `lane-state.json` is untouched by this slice (`git diff HEAD --stat` → 0 lines).

**Useful consequence for lane 2:** with `#568`'s snapshot in place, this branch's `AGENT-02` edits
still verify — the run reports `lane instruction docs consistent with snapshot (2 guarded lanes)`.
The slice is compatible with the snapshot that clears the gate.
