# ARK-OPS-CONTINUOUS-001 — cycle 25: the fairness guard decides the rule, not the last refresh

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Fix record for:** `docs/control-plane/evidence/hourly-weaver-portfolio-state-ledger-01/` (PR #744)
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471`
**Branch:** `gate-hygiene/portfolio-state-ledger-01`, entered at `45c185669dd8e3a8a39c3872e743a5b8fab68a4e`
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
`main`, no deployment, no acceptance, no draft conversion. No new pull request was opened;
the existing PR #744 was extended.

This is a **fix** record. The two-record convention
(`docs/control-plane/evidence/ark-ops-continuous-001/LEDGER.md`) puts a reconciliation
record at the bare `…-cycle-NN` path and a fix record at `…-cycle-NN-<slug>`; this cycle
produced a fix, so it takes the slugged path and is carried by the PR that makes the fix.

---

## 1. The defect: a gate that was red on its own PR

PR #744's own check `portfolio-state` was **`failure`** on its head `45c18566`, measured
from `commits/45c18566…/check-runs`:

```
portfolio-state  completed  failure
```

The failing node, from run `45828169796` (`gh run view --log-failed`):

```
FAILED tests/test_portfolio_state_ledger.py::test_blocked_repository_does_not_consume_the_slot
AssertionError: assert 'Arkadia-Oversoul-Prism/Arkadia' == 'Arkadia-Oversoul-Prism/sonata'
1 failed, 16 passed in 0.12s
```

Twelve of the thirteen check-runs on that head were `success`; this was the only red one,
and it is the gate the PR itself adds. So the ledger shipped a fairness rule whose own
guard could not pass.

## 2. Diagnosis: the assertion, not the arithmetic

`select_next` sorts candidates by `(last_progress_at, CANONICAL_REPOS index, name)` and
skips any row the cursor marks `blocked`. That is the directive's rule (§4.1: oldest
verified `last_progress_at` among **unblocked** repositories; tie-break Sonata → FSN →
Arkadia). The tie-break is only reachable when timestamps are equal.

The test asserted the tie-break's first entry where the *arithmetic* applies:

```python
_row(FSN)["blocked"] = True
assert selection["repository"] == SONATA      # pre-repair
```

Measured, the committed snapshot's timestamps were:

| revision | FSN | Arkadia | Sonata | blocked-FSN selection |
|---|---|---|---|---|
| `1dcccdcd` (authored) | 2026-11-07T10:15:12Z | 2026-11-26T01:30:43Z | 2026-11-26T00:48:38Z | **Sonata** — test passed |
| `45c18566` (refreshed) | 2026-11-26T11:14:57Z | 2026-11-26T11:15:05Z | 2026-11-26T13:18:56Z | **Arkadia** — test failed |

So the module never changed. The **input** changed: a refresh
(`chore(weaver): refresh the portfolio ledger from live state`) replaced the recorded
timestamps with freshly measured ones, and Arkadia came out **8 seconds** older than
Sonata. The hardcoded name was a time bomb set by the very refresh the PR is designed to
run.

This is the recurring class already recorded in `AGENTS.md` — a test-side literal pinned
to a value that is not the property under test — with a specific twist worth naming: the
pinned value here is *live, refreshed data*, so the test decays on a schedule rather than
on a code change.

## 3. Repair

One test, clock pinned, rule preserved:

```python
pinned = copy.deepcopy(state)
_row(pinned, SONATA)["last_progress_at"]  = "2026-11-26T13:00:00Z"
_row(pinned, FSN)["last_progress_at"]     = "2026-11-26T11:00:00Z"
_row(pinned, ARKADIA)["last_progress_at"] = "2026-11-26T12:00:00Z"

assert portfolio_state.select_next(pinned, cursor)["repository"] == FSN   # oldest wins

_row(blocked, FSN)["blocked"] = True
selection = portfolio_state.select_next(pinned, blocked)
assert selection["repository"] == ARKADIA   # next-oldest unblocked, not the tie-break head
assert any(FSN in line and "blocked" in line for line in selection["skipped"])
```

The division of labour is now explicit and stated in the docstring: **this** node decides
the rotation rule against a pinned clock, and
`test_committed_artefacts_support_their_own_selection` remains the node that decides
whether the *committed, live-derived* snapshot is internally consistent. Neither can
absorb the other's job, and a future refresh can no longer redden the fairness rule.

`scripts/portfolio_state.py` was **not** changed. The module was correct.

## 4. Verification

| command | result |
|---|---|
| `python -m pytest tests/test_portfolio_state_ledger.py -q -rEf` (pre-repair) | `1 failed, 16 passed` |
| `python -m pytest tests/test_portfolio_state_ledger.py -q -rEf` (post-repair) | **`17 passed`** |
| `python -m pytest tests/test_ci_gate_trigger_coverage.py tests/test_workflow_injection_boundary.py tests/architecture -q` | **`164 passed`** |

### 4.1 Live negative control

The guard must fail on the defect it claims to catch, so the *real* module was mutated
rather than a synthetic fixture substituted:

```
scripts/portfolio_state.py:  if entry.get("blocked"):   ->   if False:  # NEGATIVE CONTROL
  -> 1 failed, 16 passed   (the repaired node reddens; nothing else moves)
restored byte-identically
  -> 17 passed             (git diff --stat scripts/portfolio_state.py -> empty)
```

The reddened node reports `assert 'Arkadia-Oversoul-Prism/family-safety-network' ==
'Arkadia-Oversoul-Prism/Arkadia'`, i.e. the blocked repository consumed the slot — exactly
the shape the directive forbids.

### 4.2 The gate selects its own inputs

`.github/workflows/portfolio-state.yml` executes
`python -m pytest -q tests/test_portfolio_state_ledger.py`, and its `paths:` filter (both
`pull_request` and `push`) names that test file, `scripts/portfolio_state.py`,
`scripts/portfolio_state_refresh.py`, the `hourly-weaver/**` docs directory, and the
workflow itself. The repaired node is therefore executed by a gate a change to it triggers.

## 5. What this cycle did not do

- **No full-suite run.** The contract permits at most one per pulse and this change is one
  test file in an isolated gate; the three adjacent suites above are the targeted evidence.
  A full-suite node-set comparison is therefore **not claimed** for this cycle.
- **No live refresh.** The snapshot was not re-derived, so `derived_at` still records the
  previous refresh. Staleness is visible in review and is not hidden.
- **No merge, no draft conversion.** All 63 open Arkadia PRs are drafts as measured this
  cycle, so GOV-04 delegated merge is inapplicable — a draft must be made ready by its
  owner.

## 6. Next action

1. **Human:** review PR #744. It is a draft; marking it ready and merging are the owner's
   actions.
2. **Weaver:** the fairness rule now selects by the *live* snapshot, which this cycle did
   not refresh. The next legal task is a refresh pulse in the repository the current
   snapshot names, not a further edit here.
3. **Human:** the decision the ledger records in §6.2 — whether the refresh gains a
   cross-repository token so the live oracle can be gated — is unchanged and remains a
   credential decision.

## 7. Reproduce

```bash
git rev-parse origin/main
python -m pytest tests/test_portfolio_state_ledger.py -q -rEf          # 17 passed
python -m pytest tests/test_ci_gate_trigger_coverage.py \
                 tests/test_workflow_injection_boundary.py \
                 tests/architecture -q                                 # 164 passed
sed -i 's/if entry.get("blocked"):/if False:  # NEGATIVE CONTROL/' scripts/portfolio_state.py
python -m pytest tests/test_portfolio_state_ledger.py -q -rEf          # 1 failed, 16 passed
git checkout -- scripts/portfolio_state.py
```

---

## 8. Ledger refreshed, and a selection deviation disclosed

The snapshot was re-derived after the repair (`portfolio_state_refresh.py --write`), so the
ledger records this pulse rather than the previous one:

| repository | branch | head | pulls | issues | `last_progress_at` |
|---|---|---|---|---|---|
| sonata | `feature/sonata-tts-app` | `7c4e6a64e39e` | 1 | 1 | 2026-11-27T02:11:59Z |
| family-safety-network | `main` | `18c729735fd4` | 4 | 3 | 2026-11-27T01:13:14Z |
| Arkadia | `main` | `8f746f9eab6d` | 63 | 10 | 2026-11-27T02:11:11Z |

`scripts/portfolio_state.py --check` → **PASS**, exit `0`, next
`Arkadia-Oversoul-Prism/family-safety-network`.

**This is the decisive verification of the repair.** The refresh is precisely the operation
that reddened the gate in §1. Re-running `tests/test_portfolio_state_ledger.py` against the
freshly written snapshot gives **`17 passed`** — the node is now refresh-stable by
construction, not by luck.

### 8.1 Deviation: this pulse selected Arkadia, the rule names FSN

Preserved explicitly rather than reconciled in favour of the work that was already done:

- I selected **Arkadia** by comparing the *canonical-branch head commit* timestamps —
  Arkadia `2026-11-27T00:13:03Z` against FSN `2026-11-26T08:22:33Z` and Sonata
  `2026-11-26T17:52:36Z` — and by treating Sonata as unavailable because a concurrent pulse
  had committed to `fix/s1-tier-truth-001` 30 seconds before this one started.
- The ledger's `last_progress_at` is a **different metric**: the maximum observed activity
  (head commit, PR updates, issue updates). By that metric FSN
  (`2026-11-27T01:13:14Z`) is the oldest unblocked repository and the rule names **FSN**.

The ledger's metric is the implemented one, so the rule's answer is FSN. The two metrics are
not interchangeable and the choice changed the selected repository; recording the
discrepancy is the contract's requirement (§"Cycle protocol"), not a courtesy.

**Consequence for the next pulse:** the next legal selection is
`family-safety-network`, phase F0/F1, continuing its existing draft PRs #10/#12/#14/#15 —
not another Arkadia edit. Switching mid-pulse would have put two bounded tasks in one cycle,
which §4.3 forbids, so the deviation is recorded rather than repaired by doing both.
