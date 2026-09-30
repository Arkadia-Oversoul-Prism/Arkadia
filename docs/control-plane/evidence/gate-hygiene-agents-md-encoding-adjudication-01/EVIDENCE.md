# AGENTS.md CP866 encoding corruption — adjudication of two competing repairs

**Workstream:** `gate-hygiene` / GATE-2 trajectory (production parity)
**Bounded question:** two open PRs each claim to repair the `AGENTS.md` encoding corruption.
PR #147 (`gate-hygiene/gate2-agents-md-encoding-repair`) and PR #150
(`gate-hygiene/gate2-agents-md-cp866-repair-01`) cannot both be right. Which one actually
reproduces the file's own last clean state?
**Classification:** `IMPLEMENTED` (repository-layer). Instrument + tests published in PR #151.
**Base:** `main` @ `002b189dd95e41c9b4f4cca33d08b4121453d289`
**Adjudication PR:** #151 (`gate-hygiene/agents-md-encoding-adjudication-01`), commit `4bad447`.

---

## 1. Answer

**PR #150 is the correct repair. PR #147 is superseded — it does not reproduce the oracle.**

The damage is a **per-line CP866 reinterpretation of UTF-8**. The transform is exactly
reversible, so the repair is decidable from the bytes alone. There are 382 lines in `main`'s
`AGENTS.md`; 50 are corrupted, 299 are clean.

## 2. The oracle, and why it is the right one

The oracle is `6c43218a48a4` — the last revision whose `AGENTS.md` carried **no mojibake**.
Recovery is judged by whether it *reproduces that revision*, not by whether it looks plausible.

Two candidate criteria are traps, and both would reject the correct repair:

1. **`cruft_after == 0` is wrong.** The file legitimately carries `U+00B7` (in `Ark Y1 · D140`)
   and `U+00A7` (in `§2`). Recovery lands at `cruft_after == 2`, exactly equal to the oracle's
   own count of 2. The criterion is `cruft_after <= cruft_oracle`, i.e. no *new* cruft.
2. **Prefix equality is wrong.** The oracle predates later appended sections, so recovered text
   cannot equal the oracle byte-for-byte. The load-bearing property is **insertions only** —
   no oracle line replaced, none deleted. Any alteration in a pre-existing byte means the
   recovery invented or dropped content.

## 3. Result

```
input            AGENTS.md @ main (002b189d)
lines            382 (clean 299, corrupted 50)
Cyrillic         182 -> 0
Latin-1/Ext      0 -> 2            (== oracle 2; delta 0)
line count       preserved  True
only corrupt     changed    True
round-trip       holds      True
oracle           6c43218a48a4  inserted=164  alterations=0  reproduced=True
decidable        True
recovered sha256 470bb5156b335fea78830ba815604be625f50725ce97a058d9aae54c82b3aa75
```

Verdict against each candidate:

| candidate | lines | reproduces oracle | disposition |
|---|---|---|---|
| recovery of `main` | 382 | yes (`alterations=0`) | the ground truth |
| PR #150 tip | 411 | yes — `recovered[:382] == pr150[:382]` + 29-line EOF append | **CORRECT** |
| PR #147 tip | 497 | no — diverges | **SUPERSEDED** |

PR #150's file is the recovered text plus one purely additive section in the last line
(`recovered[382:382] -> pr150[382:411]`, count 29). That section is **authored content, not
recovered bytes**: the adjudication proves it is additive, not that it is well worded.

## 4. Verification

- `tests/test_agents_md_encoding_adjudication.py` — 17/17 passed on the corrupted tree;
  15 passed / 2 skipped on a synthetic `#150`+`#151` merge (see §9). (Pass 1 recorded
  16/16; the merge-safety correction in §9 changed the test set.)
- `tests/architecture` — 11/11 passed
- CP10 mutation boundary judge — PASS (`--judge` exit 0)
- commit `4bad447` check-runs — `Vercel Preview Comments` success, `Full-history secret scan` success

## 5. Defect found and fixed in this pass

The audit CLI printed oracle keys that had been **renamed out of the result dict**, so a plain
(non-`--json`) invocation raised `KeyError` *after* already reporting `decidable=True`. The
audit function returns fine; only end-to-end invocation catches it. This is the same class as
the F-02 lesson: a claim that outruns its own evidence. Fixed, and guarded by an end-to-end
CLI test rather than only unit tests of the result dict.

## 6. Baseline — recorded, not fixed

Full suite: **20 failed / 1055 passed / 11 skipped** plus the 2 documented collection errors.
With both new files removed the fingerprint is **identical** (20 failed / 66 passed), so this
work contributes **zero** regression. The debt is already under active repair by PR #148
(`scheduler-bootstrap-testspec-repair`) and PR #149 (`render-codex-collection-error-prove`);
per the contract it is neither silently fixed nor attributed here.

## 7. What this does not do

- It does not modify `AGENTS.md` and does not merge or close anything. Merge and closure are
  sovereign authority.
- It does not endorse the wording of PR #150's appended section.
- It does not fix the 20 baseline failures.

## 8. Authorization required

Sovereign decision: **merge PR #150**, **close PR #147 as superseded**, then decide PR #151
(adjudication evidence). No merge, closure, or production action was taken by this pass.

## 9. Merge-safety correction (pass 2)

The pass-1 adjudication asserted a verdict about the working tree while encoding the tree
state it was written against: two live-file tests treated "`main` is corrupted" as a premise.
PR #150 repairs `AGENTS.md`, so on merge those assertions fail. An adjudication branch that
only holds on the pre-repair tree cannot be merged after the repair it endorses — the same
claim-outrunning-its-evidence defect the branch was written to expose.

Corrections, and why each is needed:

- **Oracle pin.** `RECOVERED_TIP_REV` now names the immutable commit `03fe21f` rather than
  the branch `pr150`. GitHub deletes a PR branch on merge, so pinning a branch name would
  leave the oracle unresolvable exactly when the queue lands — exit 2, not a verified claim.
- **Clean-without-oracle is not decidable.** `audit()` sets `decidable=False`
  (`decidable_basis="none"`) when a file shows no corruption and no oracle was consulted.
  A clean file and a never-verified repair are the same bytes; the bytes cannot separate them.
- **Exit-code semantics.** `2` (not `1`) in that case. `1` now means "clean and
  oracle-verified" and is a real positive claim; `0` means a recovery was verified against
  the byte oracle.
- **State-scoped tests.** `test_recover_is_decidable_on_the_corrupted_live_file` asserts the
  corrupted tree and skips once repaired; `test_live_file_verdict_matches_its_state` covers
  both states so exactly one branch runs on any revision. The end-to-end CLI test (which
  guards a real `KeyError`-class defect) is retained and made order-robust.

Verification of both merge orders:

| scenario | how | result |
|---|---|---|
| corrupted `main` | `pr151` as-is | **17 passed** |
| `#150` + `#151` merged | synthetic `git merge-tree pr151 pr150` worktree | **15 passed / 2 skipped** |

Whether GitHub's own merge of #150 into `main` then #151 is byte-identical to the local
`merge-tree` was **not** established — that is a platform-level observation this pass did
not have. The monotonic status of the two is reasoned, not measured; recorded as such.

## 10. Correction — #143 also carries an unadjudicated `AGENTS.md`

Pass 1 adjudicated only #147 against #150. `#143`
(`gate-hygiene/gate2-production-parity-02`) **also** edits `AGENTS.md` (265 changed lines →
sha256 `08e2af0d`), which is a third, distinct repair. Content hashes:

| revision | `AGENTS.md` sha256 |
|---|---|
| `main` | `57bf37f9` (corrupted) |
| `#143` | `08e2af0d` |
| `#147` | `2ccde4c5` |
| `#150` | `a7ef8002` (byte-oracle recovered) |

#143 is the GATE-2 parent, so it is the most consequential of the three branches, and its
encoding repair is not the verified one. Merging it as-is lands an unadjudicated `AGENTS.md`.
Before merge, its encoding must be adjudicated against the same byte oracle, or its
`AGENTS.md` hunk dropped in favour of #150's. Recorded as the next bounded task; not started.
