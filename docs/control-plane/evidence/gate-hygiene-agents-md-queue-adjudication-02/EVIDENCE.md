# GATE-02 / gate-hygiene — `AGENTS.md` encoding-repair queue: independent adjudication

Pass: `gate-hygiene/agents-md-queue-adjudication-02`
Date: 2026-09-30 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Authority: no merge, no push to `main`, no force-push. Human-only merge.

## 1. Why this pass exists

Five open pull requests (#143, #147, #150, #151, #152) claim to repair or adjudicate the
`AGENTS.md` encoding corruption. #151 adjudicated the question with a byte-oracle and
instrument; this pass re-derives the verdict **independently**, by a different method
(per-codepoint alphabet membership plus an in-place run of #152's own guard), and adds one
finding #151 does not cover: the disposition of **#152**.

Two questions are answered here:

1. **Which candidate is the correct repair?** (corroborates #151)
2. **Is #152's guard safe to merge, and in what order?** (new)

## 2. Method

No candidate list and no history are needed. Three measurements:

- **M1 — alphabet membership.** The corruption is total over the document's non-ASCII
  content, so recovering the file yields its true alphabet. The established alphabet is
  twelve codepoints:
  `U+00A7 §  U+00B7 ·  U+2013 –  U+2014 —  U+201C “  U+201D ”  U+2026 …  U+2192 →  U+2194 ↔  U+2260 ≠  U+2B06 ⬆  U+1F512 🔒`
  A correct candidate's recovered text stays inside this set. Cyrillic look-alikes,
  box-drawing glyphs, or an invented `U+21D2` fall outside it.
- **M2 — round-trip exactness.** `recover` applies the inverse per line and must be
  invertible on its own domain; a repair built on the wrong codec is not.
- **M3 — the guard itself, executed in place.** #152's `tests/test_agents_md_repair_fingerprint.py`
  was copied into `tests/` and run against each candidate's `AGENTS.md` in the working tree,
  so `REPO_ROOT` resolves to the repository.

M1/M2 reproduce #151's oracle conclusion; M3 is the disposition test for #152.

## 3. Result

| candidate | bytes | non-ASCII | recovered lines | recovered alphabet | outside established set | verdict |
|---|---|---|---|---|---|---|
| `main` (`002b189`) | 27301 | 517 | 50 | 12 | 0 | corrupted — **recoverable** |
| **#150** | 29528 | 364 | 0 | 12 | **0** | **CORRECT** |
| #143 | 35811 | 1209 | 0 | 28 | **26** | WRONG (double-encoded) |
| #147 | 36650 | 630 | 50 | 19 | **7** | SUPERSEDED (restores main verbatim) |
| #152 | 27301 | 517 | 50 | 12 | 0 | guard only — no `AGENTS.md` change |

`main` recovers cleanly to the established twelve-codepoint alphabet in 50 lines, which is
why #150 — a faithful CP866 round-trip — is the correct repair.

Verified separately: `repair(main)` is a byte-prefix of `#150`'s file, with `#150` appending
an authored section at EOF. **This pass endorses #150's bytes, not the wording of its
appended section** — that is a presentational call for the sovereign, and #151 says the same.

### Why #147 is not the repair

#147's title says *repair*; its file restores `main`'s corrupted region **verbatim** and
therefore re-introduces the corruption into a repaired base. Its recovered alphabet still
contains `U+0410 А  U+0416 Ж  U+0422 Т  U+0424 Ф  U+0442 т` — 7 codepoints outside the set.
#147's premise is that `main` is ground truth; §3 shows `main` is itself recoverable, so the
premise is false. A file titled "repair" that leaves the corruption in place is
`CONTRADICTED`, not merely superseded.

## 4. Disposition of #152 (the new finding)

#152 adds no `AGENTS.md` change; it adds a history-free guard. Its docstring states:

> The subset test is monotone under merging: it **passes on `main`**, on the correct
> candidate, and on the file after the correct repair merges; it fails on each incorrect
> candidate both before and after merge.

Executed in place against each candidate's working-tree `AGENTS.md`:

```
origin/main                                     -> 2 passed
gate-hygiene/gate2-production-parity-02  (#143)  -> 1 failed, 1 passed
gate-hygiene/gate2-agents-md-encoding-repair (#147) -> 1 failed, 1 passed
gate-hygiene/gate2-agents-md-cp866-repair-01 (#150) -> 2 passed
```

The guard is **sound and merge-safe**. It passes on `main`, rejects both wrong candidates,
and passes on the correct repair — so it stays green before *and* after #150 merges. Its
claimed monotonicity holds. **It may merge in any order relative to #150.** Its prose is
also accurate about `main`: the guard recovers `main` and tests the *recovered* alphabet,
which is why a corrupted tree passes.

**A mis-diagnosis, recorded rather than repeated.** An earlier step of this pass ran the
guard from `/tmp`, where `REPO_ROOT = parents[1]` resolved outside the repository and the
guard raised `FileNotFoundError`. That failure was read as "the guard fails on `main` — a
merge hazard". Re-run in place, both tests pass. The `/tmp` failure was a **path artifact of
the harness, not a property of the guard**. The guard is not a hazard and must not be
described as one. (Its assertion that "today's `main` is neither" of the two competing byte
streams is imprecise — `#152`'s `AGENTS.md` is byte-identical to `main`'s — but the
observation is inert: no test depends on it.)

## 5. Authorization required (sovereign decisions — none taken here)

Order matters: **#150 and #152 are both green on their own, and #150 is the repair.** If the
guard merges before the repair it passes on the still-corrupted tree; if after, it passes on
the repaired tree. Either way the queue converges.

1. **Merge #150** — the correct repair.
2. **Close #147 as superseded** (classification `CONTRADICTED`: it re-introduces the
   corruption its title claims to remove).
3. **Merge #152** — the guard, once #150 is in.
4. **#143** — carries the same damage class as #147; it must **not** merge with its current
   `AGENTS.md`. Its non-`AGENTS.md` Gate-2 parity content is a separate question for the
   sovereign.
5. **#151** — adjudication evidence; merge or close as the sovereign prefers.

No merge, closure, or production action was taken by this pass.

## 6. Scope and regression boundary

Evidence-only. This pass adds **one** file; it changes no code, no test, and no
`AGENTS.md` byte. It therefore cannot alter any suite's outcome.

- `python -m py_compile api/main.py` — not applicable (boot code untouched).
- Baseline fingerprint unchanged by construction: 20 failed / 1045 passed / 13 skipped /
  2 collection errors on `main` at `002b189`.
- CP10 mutation boundary — PASS (`--judge` exit 0).

## 7. Remaining uncertainty

- The adjudication reads git objects, not a running deployment. It makes **no**
  production-parity claim.
- The correct codec is established from `main`'s own bytes. If some earlier revision of
  `AGENTS.md` contained a non-CP866 character, the 50 recovered lines would be the affected
  surface; #151's independent oracle reaches the same twelve-codepoint alphabet, which is
  the corroboration this pass relies on.
