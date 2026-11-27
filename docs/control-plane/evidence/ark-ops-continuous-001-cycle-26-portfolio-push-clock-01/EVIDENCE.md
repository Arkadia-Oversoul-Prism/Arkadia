# ARK-OPS-CONTINUOUS-001 — cycle 26: the fairness clock is a push clock, not a comment clock

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Fix record for:** `docs/control-plane/evidence/hourly-weaver-portfolio-state-ledger-01/` (PR #744)
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471`
**Branch:** `gate-hygiene/portfolio-state-ledger-01`, entered at `dae447fe400cf5d527e1d114de3739bba360c86e`
**Pulse:** `PORTFOLIO-WEAVER-2026-11-26-01`, 2026-11-27T05:0xZ
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
`main`, no deployment, no acceptance, no draft conversion. No new pull request was opened;
the existing PR #744 was extended.

This is a **fix** record. The two-record convention
(`docs/control-plane/evidence/ark-ops-continuous-001/LEDGER.md`) puts a reconciliation
record at the bare `…-cycle-NN` path and a fix record at `…-cycle-NN-<slug>`; this cycle
produced a fix, so it takes the slugged path and is carried by the PR that makes the fix.

---

## 1. Why this pulse touched Arkadia

Reconstruction at 2026-11-27T05:05Z, live from GitHub, not from memory:

| repository | default branch | head | open PRs | `pushed_at` |
|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 1 | 2026-11-27T04:17:56Z |
| `family-safety-network` | `main` | `18c729735fd4` | 5 | 2026-11-27T03:14:30Z |
| `Arkadia` | `main` | `8f746f9eab6d` | **63** | 2026-11-27T02:13:18Z |

Arkadia carries the oldest verified progress, so §4.1 selects it. The selection was
reached twice independently: by hand from the pull list, and by
`scripts/portfolio_state_refresh.py` after the repair (§4). Two derivations agreeing is
the point of a ledger.

`sonata`'s default branch is `feature/sonata-tts-app`, not `main` — recorded because a
portfolio tool that assumes `main` silently drops the repository (already guarded by
`test_refresh_reads_the_declared_default_branch_not_main`).

## 2. The defect: a conversation resets the fairness clock

`last_progress_at()` took the maximum of the default-branch head commit and
`latest_open_pull.updated_at`. The module's own docstring states the invariant it was
supposed to hold:

> A pulse that produced nothing did not progress, and letting a no-op pulse reset the
> clock is how a stalled repository is starved forever -- the exact failure this fairness
> rule exists to prevent.

`updated_at` is not a push clock. GitHub advances it on a comment, a label, or a title
edit. Measured at `main` `8f746f9e`:

| PR | `updated_at` | head commit | apparent progress |
|---|---|---|---|
| #741 | 2026-11-26T08:37:43Z | 2026-11-25T22:13:53Z | **+10h24m** |
| #747 | 2026-11-26T08:37:40Z | 2026-11-26T07:24:15Z | +1h13m |
| #744 | 2026-11-27T02:13:19Z | 2026-11-27T02:13:16Z | +3s (a real push) |

The cause is decidable rather than inferred — `issues/741/timeline` carries exactly one
event at that second:

```
2026-11-26T08:37:43Z commented Arkadia-Oversoul-Prism
```

and #747's timeline likewise:

```
2026-11-26T08:37:40Z commented Arkadia-Oversoul-Prism
```

Both are comments. So the fairness input could be advanced by *talking about* a
repository, which is the starvation the rule exists to prevent — the same class already
recorded in `AGENTS.md` ("a field that is derived and printed but never judged"), in its
fairness form.

## 3. Repair: derive the clock from `pushed_at`

`pushed_at` is repository-level, already present in the `GET /repos/{r}` response the
refresh already makes, and it cannot be moved by a comment, a label, or an edit.

```python
def last_progress_at(row: dict) -> str | None:
    candidates = []
    if row.get("head_committed_at"):
        candidates.append(row["head_committed_at"])
    if row.get("pushed_at"):
        candidates.append(row["pushed_at"])
    if not candidates:
        return None
    return max(candidates, key=parse_iso)
```

`latest_open_pull.updated_at` is still **recorded** — a reviewer wants to see which pull
was touched — but it is explicitly not an input, and
`test_a_comment_does_not_reset_the_fairness_clock` pins that.

`pushed_at` is now also required for a `VERIFIED` row, so a row that could not be measured
fails closed instead of silently falling back to the head commit.

Schema `arkadia.portfolio-state/1.0` -> `1.1`: a derived field's *meaning* changed, so a
reader of an old snapshot is told the field is not the same field. The offline guard
recomputes `last_progress_at` from the row (`_check_row`), so a snapshot derived under the
old rule cannot pass as a new one.

### Known limitation, stated rather than papered over

`pushed_at` covers pushes to *any* branch, not only branches with an open pull. A push to
an abandoned branch therefore counts as progress. That is still push-bearing activity, and
it is the widest sound signal available without one request per open pull (63 for Arkadia
this pulse). It is strictly narrower than `updated_at` in the direction that matters: it
cannot be moved by conversation.

## 4. Measured effect — live re-derivation

`python scripts/portfolio_state_refresh.py --write`, live at 2026-11-27T05:12:20Z:

```
sonata:                VERIFIED branch=feature/sonata-tts-app head=7c4e6a64e39e pulls=1 issues=1 progress=2026-11-27T04:17:56Z
family-safety-network: VERIFIED branch=main                  head=18c729735fd4 pulls=5 issues=3 progress=2026-11-27T03:14:30Z
Arkadia:               VERIFIED branch=main                  head=8f746f9eab6d pulls=63 issues=10 progress=2026-11-27T02:13:18Z
next: Arkadia-Oversoul-Prism/Arkadia -- oldest verified last_progress_at among unblocked repositories (2026-11-27T02:13:18Z)
```

`python scripts/portfolio_state.py --check` -> `portfolio state PASS (3 repositories, next:
Arkadia-Oversoul-Prism/Arkadia)`, exit 0.

The committed snapshot it replaces recorded `selection: family-safety-network` at
`derived_at 2026-11-27T02:12:53Z`. That was correct for its instant and is now superseded:
FSN's #16 was pushed at 03:14:30Z and sonata's #9 at 04:17:56Z, both after it. Recorded as
a superseded measurement, not reconciled by argument.

## 5. Verification

```
python -m pytest tests/test_portfolio_state_ledger.py -q   -> 22 passed
python scripts/portfolio_state.py --check                  -> PASS (exit 0)
```

Five nodes are new: the file carried **17** `def test_` functions at the branch head
`dae447fe` and carries **22** now (`grep -c '^def test_'` on both revisions), and
`--collect-only` on the branch reports `22 tests collected`.

| node | polarity |
|---|---|
| `test_a_comment_does_not_reset_the_fairness_clock` | negative control — the measured #741 shape must yield the push time |
| `test_a_push_moves_the_fairness_clock` | positive control — a push *is* progress |
| `test_a_comment_time_recorded_as_progress_is_a_finding` | the offline guard rejects a hand-typed comment clock |
| `test_a_verified_row_without_a_push_time_is_reported` | fail closed when the clock input is missing |
| `test_refresh_derives_the_clock_from_the_push_not_the_comment` | drives the real `observe()`; `updated_at` is *later* than `pushed_at` so the node discriminates the two implementations |

### Live negative controls, run against the real module and restored byte-identically

`scripts/portfolio_state.py` sha256 before and after each control:
`c218fab6ed1aa7770a4ec9114673fe0d565e1e9c801761fa2f54ad9157e0952b`.

| control | mutation | observed |
|---|---|---|
| clock reverted to `latest_open_pull.updated_at` | the repair's two `pushed_at` lines replaced by the pre-repair block | **4 failed, 18 passed** — `test_committed_artefacts_support_their_own_selection`, `test_a_comment_does_not_reset_the_fairness_clock`, `test_a_push_moves_the_fairness_clock`, `test_refresh_derives_the_clock_from_the_push_not_the_comment` |
| `pushed_at` dropped from the VERIFIED-required list | one loop tuple | **1 failed, 21 passed** — `test_a_verified_row_without_a_push_time_is_reported` |

Restored and re-measured: `sha256sum -c` OK, `22 passed`.

## 6. Cursor reconciliation (authored half)

The cursor named **merged** PRs as active, measured 2026-11-27:

- sonata: `#7` and `#8` are both `MERGED` (`main` `7c4e6a64` is the #8 merge); the only
  open pull is `#9`.
- family-safety-network: five open drafts (`#16`, `#15`, `#14`, `#12`, `#10`), not two.
- Arkadia: 62 -> 63 open.

`last_pulse_at` for Arkadia is set to this pulse. It is deliberately **not** a fairness
input (`test_a_noop_pulse_does_not_reset_fairness` pins that), so recording it cannot move
the clock.

## 7. Not claimed

- **No merge, no draft conversion, no deployment, no acceptance.** PR #744 stays a draft.
- The hosted automation is still **NOT LINKED** to the three-repository portfolio (PR #744,
  "Hosted automation linkage"); that is a runtime configuration change reserved to a human.
  This pulse changes the ledger, not the automation.
- `sonata` and `family-safety-network` were **inspected only** this pulse. No branch, PR, or
  file in either was touched.
- Branch protection on all three repositories is **UNKNOWN**: `GET
  /branches/main/protection` answers `403 Resource not accessible by integration` for this
  token, which is an absence of permission, not an absence of protection.

## 8. A property of the repair worth naming: the refresh push advances its own clock

`pushed_at` is repository-level, so the commit that carries a refreshed snapshot is itself a
push and moves the row it just recorded. At `derived_at 2026-11-27T05:12:20Z` the Arkadia row
reads `pushed_at 2026-11-27T02:13:18Z`; the commit carrying it was pushed later, so by the
time a reader loads the snapshot the Arkadia clock is already behind live. `--check` still
passes, because it validates the snapshot's *internal* arithmetic (`last_progress_at` must be
the maximum of the row's own fields) and never claims the row is current.

This is the same class already recorded for `lane-state.json` — a snapshot cannot both be
written by a commit and describe the state after that commit. The mitigations are the ones
this ledger already has and they are not accidental:

- `derived_at` is recorded, so staleness is visible in review rather than inferred;
- the selection is a function of the *snapshot*, so it is reproducible offline and never
  silently re-derived;
- the next pulse re-derives before acting, which is what §4.1 requires anyway.

Do **not** "fix" this by having the refresh subtract its own push, or by treating a refresh
commit as not-progress: the second is exactly the no-op-pulse-resets-fairness failure in
reverse, and the first would make the clock unmeasurable. A future slice could record
`observed_at` per row and let `--check` scope the claim, which is the same reasoning
recorded for `head_sha` in the lane snapshot. Proposed, not implemented.

## 9. Next action

Current state: PR #744 (draft) carries the ledger, the selector, the gate, and this repair.
Evidence: this record, `--check` PASS, 22 passed, two live negative controls.
Blockers: none for the ledger. Merge remains human-only (GOV-04).
Authorized action: continue #744 on a later pulse if a further gap is measured.
Forbidden: merging, pushing to `main`, converting the draft, deploying, or editing the
hosted automation prompt.
Completion condition: a human reviews and merges #744; until then the ledger records the
next repository and nothing acts on it.
