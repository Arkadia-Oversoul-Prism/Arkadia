# GATE-HYGIENE / GATE-02 — `AGENTS.md` cp866 encoding repair — EVIDENCE

**Authorization:** human (standing gate-hygiene envelope; bounded, docs-only).
**Base:** `002b189dd95e41c9b4f4cca33d08b4121453d289` (production `main`).
**Branch:** `gate-hygiene/gate2-agents-md-cp866-repair-01`.
**PR:** #150 (base `main`). **Merge / production deploy: HUMAN ONLY. Neither performed.**
**Status:** READY FOR MERGE (evidence complete; human decision outstanding).

---

## 1. The defect

`main`'s `AGENTS.md` carried **179 mojibake characters** across **50 lines**: Cyrillic
look-alike sequences occupying positions where `—` (U+2014), `→` (U+2192) and emoji belong.

## 2. The contradicted prior claim (PR #147)

PR #147 concluded *"a decode-based repair is a dead end"* after sweeping
`cp1250, iso8859_2, cp1251, mac_latin2, cp1254, cp1257, iso8859_4, cp437, latin_1`.

**The sweep omitted `cp866`.** cp866 is the codec. The supporting observation in #147 —
*"13 distinct characters in `main` fall outside `cp1252`"* — is true but irrelevant: the codec
was never cp1252.

Measured on #147's own head:

| revision | mojibake chars |
|---|---|
| `main` | 179 |
| PR #147 head (`20d184b8…`) | **188** |

#147's head restores the corrupted region *"verbatim from `main`"*, so it **preserves** the 179
and adds 9. Its "encoding-only" proof is *skeleton identity* (non-ASCII stripped), which is
satisfied by leaving the corruption untouched: it proves the transform is encoding-only, not
that it is correct.

## 3. The transform

**UTF-8 bytes decoded as cp866**, applied **line-wise**, only to lines fully cp866-decodable:

```python
line.encode('cp866').decode('utf-8')
```

50 lines are pure mojibake and are repaired. 33 non-ASCII lines carry genuine `—`/`→`/`§` that
were never corrupted and are left **byte-identical**. A whole-file `bytes.decode('cp866')` is
wrong — it destroys the genuine characters and *increases* the Cyrillic count. 0 of the 12
distinct non-ASCII codepoints in the corrupted region fall outside cp866.

## 4. Four independent proofs

```
ORACLE    repaired[:205] == 6c43218a4:AGENTS.md[:205]      -> True
INVERSE   corrupt(repair(x)) == x on the corrupted domain  -> True   (50 lines)
UNTOUCHED 332 non-corrupted lines byte-identical           -> True
SHAPE     line count preserved (382)                       -> True
```

- **ORACLE** — the repair reproduces the **last clean revision byte-exactly** (`6c43218a4`,
  the commit before corruption entered `main`). Ground truth is "output equals the known-good
  file", not "my candidate table is plausible".
- **INVERSE** — `corrupt(repair(x)) == x` on the corrupted domain. Decidability comes from the
  invariant, not from a remembered codec list — the exact thing #147's sweep lacked.
- **UNTOUCHED / SHAPE** — the repair is surgical: 332 lines byte-identical, line count preserved.

Result: mojibake `179 → 0`.

## 5. Verification commands

```
python -c "t=open('AGENTS.md',encoding='utf-8').read(); print(sum(1 for c in t if '\u0400'<=c<='\u04ff'))"
# must print 0
python -m py_compile api/main.py     # OK
git diff --name-only                 # AGENTS.md only
```

## 6. Regression boundary

| check | result |
|---|---|
| CP10 mutation boundary (`--judge`) | **PASS**, exit 0 |
| `python -m py_compile api/main.py` | **OK** |
| `api/main.py` line count | 2519 — untouched, under the 2600 budget |
| CP10 path filter (`sg-02-fe-2-v.yml`) | `AGENTS.md` not in filter — CP10 not required for this PR |
| Full suite | not re-run; docs-only change, fingerprint rule makes it non-attributable |
| Protected surfaces / governance / identity / mutation / authorization paths | untouched |

## 7. Remaining uncertainty

- The full suite was not re-run on this branch. Single markdown file; the contract's
  fingerprint rule makes a suite run non-attributable here.
- The diff is large in *line* terms (79 insertions / 50 deletions) while being semantically
  ~zero. Inherent to encoding repair — which is why the proofs are stated as byte-level
  identities rather than left to diff review.

## 8. Reconciliation with PR #147 — sovereign decision

This PR **supersedes #147's approach**. Two options, one decision:

1. Merge #150, close #147; or
2. Fold the #150 commit into #147 and drop its dead-end claim.

**No push was made to #147's branch.** Rewriting another PR's head would destroy its author's
evidence and pre-empt the sovereign's choice. The contradiction is recorded as a comment on
#147 so it is visible where the decision is made.

## 9. Authorization boundary

Merge, production acceptance, and closure remain **human-only**. The agent inspected,
diagnosed, implemented, tested, and prepared evidence only. No merge, no self-authorization, no
scope expansion, no new mutation or authorization path.
