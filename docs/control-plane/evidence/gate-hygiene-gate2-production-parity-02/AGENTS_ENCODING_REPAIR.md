# GATE-02 — `AGENTS.md` encoding corruption: measured, repaired, proven encoding-only

Pass: `gate-hygiene/gate2-agents-md-encoding-repair`
Date: 2026-09-30 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Carrier PR: **#143** (`gate-hygiene/gate2-production-parity-02`) — this repair is based on
that branch and lands inside the carrier, it does not race it.
Repair PR: **#147**

## 1. Why this pass exists

PR #143 reported a large `AGENTS.md` diff. The question this pass answers is narrow:
**is that diff authored content, or pipeline damage?** If damage, the pre-existing region
is at risk and the carrier must not be merged carrying it.

## 2. The defect is a *rewrite*, not an append (measured)

| | `main` | PR #143 |
|---|---|---|
| bytes | 27301 | 35811 |
| lines | 381 | 480 |
| `U+2014` em-dash | 24 | **2** |
| `U+2192` arrow | 17 | **0** |

`difflib.SequenceMatcher(autojunk=False)` over the two line lists yields:

```
58 x ('replace', 1..5, 1..5)     <- equal-length blocks
 1 x ('insert',  0,   99)        <- the only real content addition
 0 x ('delete', ...)
```

Every `replace` block has **equal length on both sides**, and stripping non-ASCII from
both sides makes them **equal**. Therefore the edit changed *only non-ASCII characters*
across 58 pre-existing blocks — 83 lines in total, matching GitHub's reported
*182 insertions / 83 deletions* against a 99-line append.

### The transform

```
U+2014                  -> U+0106 U+014C U+00F6
U+2192                  -> U+014C U+00E5 U+00C6
U+0442 U+0410 U+0424    -> U+010D U+00E9 U+0105 U+00C9 U+0105 U+017C   (double-encoded)
```

Byte-level sample:

```
main  : '# Arkadia \u0442\u0410\u0424 Agent Memory'
pr143 : '# Arkadia \u010d\u00e9\u0105\u00c9\u0105\u017c Agent Memory'
```

### The transform is LOSSY — this is the load-bearing fact

13 distinct characters in `main` fall **outside `cp1252`**, so no candidate table reverses
it. Verified failures: `cp1250`, `iso8859_2`, `cp1251`, `mac_latin2`, `cp1254`, `cp1257`,
`iso8859_4`, `cp437`, `latin_1`.

**Consequence:** the pre-existing region cannot be recovered by re-decoding. It is
restored **verbatim from `main`** instead. Do not attempt a decode-based repair; it is a
dead end and was already walked.

## 3. The repair

Take `main`'s `AGENTS.md` bytes unchanged and append only PR #143's 99 new lines, with
non-ASCII characters written correctly.

* pre-existing region byte-identical to `main`: **True** (0 of 83 lines altered)
* `diff vs main` → **99 insertions, 0 deletions**
* `diff vs #143` → **110 / 110**

Two sequences in the *new* section could not be learned from `main`, because `main` never
contains them. Resolved by context, and recorded so the next pass does not re-derive them:

| corrupt | context | resolved to |
|---|---|---|
| `U+014C U+00E5 U+00F6` | ``alias<SHA>`` note | `U+2194` (left-right arrow) |
| `U+252C U+00A6` | `§10.1`, 2 occurrences | `U+00A7` (section sign) |

## 4. Proof the repair is encoding-only

The strongest available proof is a **skeleton identity**: strip every non-ASCII character
from both files and compare.

```
skeleton(repair) == skeleton(pr143)   ->  True
chars: 34865 (repair) vs 35203 (pr143)
lines: 481    (repair) vs 481   (pr143)
```

Identical skeleton over identical line counts means **wording, structure and line count are
unchanged**; only non-ASCII characters differ. This is what "encoding-only" means, and it is
asserted, not assumed.

## 5. Verification

```
pre-existing region byte-identical to main : True
new region free of Cyrillic/mojibake chars  : True
decodes as valid UTF-8                      : True
87 passed  test_gate2_backend_observation.py, test_gate2_browser_observation.py,
           test_m02a_ci_gate_integrity.py, test_engineering_lab.py
11 passed  tests/architecture
CP10 policy judge on all 8 changed paths     : PASS (exit 0)
```

`AGENTS.md` is agent memory only. No test asserts on its encoding: the only tests
referencing it are `test_m02a_ci_gate_integrity.py` (asserts its *presence* among tracked
root docs) and `test_engineering_lab.py` (writes its own temp file). No behavioural
surface changed.

## 6. Independent reproduction of PR #143's own claim

The carrier's central `VERIFIED` claim was reproduced from live production, not accepted
from prose:

```
main SHA        : 002b189dd95e41c9b4f4cca33d08b4121453d289
schema          : HTTP 200  operations=274
deployed digest : d1797f9c38b5d707d0c7
main:002b189dd95e -> d1797f9c38b5d707d0c7   == deployed
cand:2525811      -> 846748380cde21badef4
distinct signatures: 2  => discriminating: true
```

Full-suite fingerprint, node-by-node against baseline:

```
#143 head : 20 failed, 1071 passed, 13 skipped, 2 errors  (122.84s)
main      : 20 failed, 1039 passed
```

`+32` passed is exactly the two new test files; the failing node set is identical.
**No regression. #143's claim HOLDS.**

### Two process corrections, recorded so they are not re-learned

* The harness only becomes discriminating when the control is passed as **`--compare`**.
  Run without it, it correctly self-reports `discriminating: false`. The first pass omitted
  the flag; the harness caught it, the author did not.
* The Actions API `?head_sha=` **silently returns `total_count: 0` for an abbreviated
  SHA**. Read a `0` as *unproven*, not *absent*. Always pass the full 40-char SHA.

## 7. Regression boundary

No source, route, script, or test file touched. `AGENTS.md` is memory only.
Gate 2's status is **unchanged** by this repair — it neither advances nor weakens the gate.

## 8. Remaining uncertainty

* `main`'s own `AGENTS.md` still carries **pre-existing mojibake** (32× `тАФ`, 24× `тЖТ`, …).
  This repair **preserves it verbatim** rather than silently fixing it: repairing it is a
  separate, unrelated bounded workstream. Recorded here so it is not re-discovered as new.
* The new section's factual prose claims were not verified against live provider APIs.
  Only the mechanically reproducible claim (#143's route-set oracle) was reproduced.

## 9. Authority boundary

No merge. No push to `main`. Sovereign review and merge required.
Merge order: **#147 → #143**, or fold #147 into #143 and close it.
