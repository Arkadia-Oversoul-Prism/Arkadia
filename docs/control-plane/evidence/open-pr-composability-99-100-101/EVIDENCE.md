# Open-PR composability matrix — #99 × #100 × #101 — EVIDENCE

**Type:** bounded verification pass. **No source change.** Mirrors the
established evidence-only pattern of PR #96 (`gate02+gate07: verify PR #94 x PR #95
composability`).

**Branch:** `gate-verify/open-pr-composability`. **Base:** `main` @
`1d4ed0362aae88e2a5c7bfa8db90fb143f065964` (merge of PR #98) — recorded here as
BASE_MAIN.

**Authority boundary:** no merge, no push to `main`, no source/test/governance edit,
no scope expansion. This pass answers one question only: *if a human sovereign merges
the three open PRs, in what order, and does the combined tree stay green?* The merge
decision remains HUMAN.

---

## 1. Reconstructed state (live evidence)

| Item | Evidence |
|------|----------|
| Clone / branch | clean working tree, on `main` |
| BASE_MAIN | `1d4ed03` (merge PR #98) — real commit, ancestry intact |
| Open PRs | #99, #100, #101 — all `open`, `merged=False`, base `main` |
| Merged PRs | #94, #95, #96, #97, #98 — all `closed`, `merged=True` |
| PR #99 head | `gate-vault/gitignore-hardening` |
| PR #100 head | `state-honesty/doc-fitness-count-reconciliation` |
| PR #101 head | `gate-k/k5-adr-static-ingestion` |
| CI on open PRs | Vercel Preview Comments only — **no Python test workflow runs on PRs** |
| `api/main.py` | 2519 lines (budget 2600; headroom 81) |
| `wc -l knowledge/static_ingestion.py` | 194 |

---

## 2. Pairwise composability (real Git merges, not dry runs)

Each pair was merged with two commits (`--no-ff`) onto a branch cut from `origin/main`,
so the *second* merge is a true three-way merge against the first.

| Pair | Result |
|------|--------|
| #99 × #100 | CLEAN |
| #99 × #101 | CLEAN |
| #100 × #101 | **CONFLICT** — `docs/phase1/CONTINUATION_LEDGER.md` only |

### 2.1 The #100 × #101 conflict is append-order only

Both PRs *append a new session block at the tail* of `CONTINUATION_LEDGER.md`. The
conflict spans lines 911–1052 and contains **no clashing content** — the two blocks
are adjacent, not overlapping. Inspection of the conflict region shows the marker is
purely positional: `=======` separates the #100 session (`## Session: STATE-HONESTY …`)
from the #101 session (`## Pass — K5 Static Ingestion …`).

**Resolution (verified):** keep **both** blocks, in commit order (#100 session first,
#101 session second). No line of either session is dropped or rewritten.

---

## 3. Combined tree (all three merged, conflict resolved as §2.1)

Merges performed in order #99 → #100 → #101 on a branch from BASE_MAIN.

### 3.1 Precondition checks

| Check | Result |
|-------|--------|
| `python -m py_compile api/main.py` | **OK** (no boot SyntaxError) |
| `python -m pytest tests/architecture -q` | **11 passed** |
| Tracked `vault/` files | 14 (unchanged) |
| Untracked/stageable `vault/` files after full suite | **0** (no leak) |

### 3.2 Full suite vs. baseline

| Tree | Result |
|------|--------|
| BASE_MAIN baseline | 49 failed / 889 passed / 10 skipped / 2 errors |
| Combined (#99+#100+#101) | 49 failed / 893 passed / 10 skipped / 2 errors |

**Fingerprint:** `grep -E '^(FAILED|ERROR)'` on the combined run, sorted, is
**byte-identical** to the recorded baseline list (`diff` → no output). Verdict:
**0 new failures, 0 repaired, 0 fingerprint change.**

The +4 passing delta decomposes exactly and only into PR #101's own new test module:

- `tests/test_static_ingestion_sources.py` — 4 tests, all pass on the combined tree
  (added to `tests/test_static_ingestion_sources.py` × `knowledge/static_ingestion.py`).
- On PR #101's branch alone: `tests/test_static_ingestion_sources.py` +
  `tests/architecture` = **15 passed**.

The two baseline collection errors are unchanged and are **not** introduced by these
PRs: `tests/test_render_codex.py` imports `codex_brain`, which lives only in
`archive/legacy_python/` (archived, Day 36); `tests/test_autonomy.py` imports
`load_autonomy_config` from `weaver.autonomy`, but `weaver/autonomy.py` (module) is
shadowed by the `weaver/autonomy/` package on disk. Both are pre-existing
sovereign-gated debt recorded in the #100 and #101 ledgers.

---

## 4. Per-PR completion conditions checked

### PR #99 — GATE-VAULT `.gitignore` hardening

Reproduced the claim on the combined tree:

```
$ git check-ignore -v vault/Ideas/foo.md  ->  .gitignore:68:vault/**   (IGNORED)
$ printf … > vault/Ideas/__canary.md && git add -A -n vault/  ->  nothing staged
$ git ls-files vault | while read f; do git check-ignore -q "$f" && echo BAD; done
  -> 14/14 tracked scaffolding files remain un-ignored
```

Both halves of the completion condition hold: runtime output under `vault/` is not
stageable, and **all 14 currently tracked `vault/` files stay tracked and un-ignored**
(`.gitkeep` ×11, `Index/README.md`, `Templates/**` ×3).

### PR #100 — state-honesty count reconciliation

- Stale prose `10/10` → `11/11` is applied on the combined tree at
  `.bootstrap/00_BOOT.md`, `.bootstrap/01_STATE.md`, `.bootstrap/03_SCOPE.md`,
  `.bootstrap/04_SUCCESS.md`, `BOOTSTRAP.md`, `MISSION.md`, `PROJECT_INDEX.md`,
  `REPOSITORY_SNAPSHOT.md`, `NEXT_AGENT.md`, `docs/ARKADIA_CANONICAL_RUNTIME_CONTRACT.md`.
- These values are confirmed **correct** against the live run (§3.1: architecture
  **11 passed**), not merely changed.
- Residual `10/10` strings exist only in (a) `.md` files correctly *annotated* as
  historical archives by PR #100 (`CURRENT_STATE.md` banner) or PR #100's own session
  narrative, and (b) untracked-by-scope historical logs (`docs/phase1/CONTINUATION_LEDGER.md`
  session blocks, `docs/verification/*`, `docs/recon/*`, `docs/checkpoints/*`). Not a
  regression.

### PR #101 — K5 ADR-corpus static ingestion

- `docs/adr/` on the combined tree contains exactly the 6 records the new test asserts:
  `ADR-010` … `ADR-015`.
- `knowledge/static_ingestion.py` gains one source entry; **`api/main.py` is untouched**
  (line budget preserved — implementation correctly avoided the 2600-line file).
- New tests pass (§3.2); all use the repo's test-session vault sandbox (`conftest.py`),
  and the full-suite run left **0** untracked files in `vault/`.

---

## 5. Verdicts

| Question | Verdict |
|----------|---------|
| Do #99, #100, #101 compose? | **YES** — 1 append-only ledger conflict, trivially resolved by keeping both sessions. |
| Does the combined tree keep the baseline fingerprint? | **YES** — byte-identical; +4 = PR #101's own tests. |
| Is any single PR unsafe to merge alone? | **NO** — #99 alone is CLEAN vs `main`; #100 and #101 are each CLEAN vs `main`. |
| Recommended sovereign merge order | **#99 → #100 → #101.** Any order is safe, but this order needs no ledger conflict resolution (#101 last absorbs the append). |
| Is PR #95 still load-bearing for PR #94? | **MOOT** — #94 and #95 are both already merged (#98 is HEAD). The prior-order hazard recorded in PR #96 is historical, not live. |

---

## 6. Remaining uncertainty

1. The ledger conflict resolution in §2.1 was performed and tested **locally on the
   verification branch**; the merged PRs' own branches are untouched. If the sovereign
   merges #101 before #100 via the GitHub UI, GitHub will surface the same append
   conflict and it must be resolved the same way (keep both blocks).
2. `docs/recon/` (22) and `docs/verification/` (59) remain outside `_SOURCES` — a
   corpus-curation decision for the sovereign. **K5 must not be marked complete** on
   the strength of PR #101 (recorded identically in the #101 ledger).
3. The two baseline collection errors and ~49 stale-assertion failures remain
   sovereign-gated (repair-tests vs restore-strings). This pass changed none of them.

---

## 7. Authorization

No merge. No push to `main`. No self-authorization. No source/test/governance edit.
This PR is **evidence only**, ready for sovereign review. Merge decision: HUMAN.
