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

- `tests/test_agents_md_encoding_adjudication.py` — 16/16 passed
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
