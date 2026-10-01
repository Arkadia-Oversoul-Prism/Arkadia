# `SH-05` — independent verification of PR #142 (heartbeat pass, 2026-09-30 ~02:06Z)

**Workstream:** `gate-hygiene` / `SH-05`
**Classification:** `VERIFIED` (the evidence in `EVIDENCE.md` is independently reproduced)
**Authority required:** merge only. The `SH-05` **disposition** remains a sovereign call.
**BASE_MAIN at this pass:** `002b189dd95e41c9b4f4cca33d08b4121453d289`
**PR #142 base:** `df7a99a067382401c00de5e7bbaaac0125ba2088` · **head:** `466538cc8ef56a3e7a58275f0af072683f22f309`
**Branch:** `gate-hygiene/sh05-gate-artifact-provenance-01`

> Evidence-only. This file adds no test, source, workflow, governance, or constitutional change.
> It records a **second, independent** reproduction of this PR's load-bearing claims — the PR's
> own `EVIDENCE.md` is preserved unmodified.

---

## 1. What this pass verified, and why it was worth doing

PR #142 has been open and green (`mergeable / clean`) but had **not been independently
reproduced**. Its claims are historical (`git log`/blob archaeology) and therefore cheap to
confirm and expensive to get wrong: a mis-stated regression point would send `SH-05a`/`SH-05b`
down the wrong repair. Every claim below was re-run against the full clone in this pass.

## 2. Independent reproduction of `EVIDENCE.md` §3

| claim | method used here | result |
|---|---|---|
| §3.1 both paths added at Genesis `9ab26fc` | `git ls-tree -r 9ab26fc` | **CONFIRMED** — `index.html`, `gate/index.html`, `gate/gate.js`, `gate/gate.css` all present |
| §3.2 negative control — nodes green at Genesis | `git archive 9ab26fc` → pytest both files | **CONFIRMED** — `3 passed` |
| §3.3 row 47 regressed at `377cdb3` (2026-03-23) | pytest at `377cdb3^` | **CONFIRMED** — `3 passed` |
| §3.3 row 48 regressed at `f6718b9` (2026-07-15) | pytest at `f6718b9^` | **CONFIRMED** — `1 failed, 2 passed` |
| §3.3 the two removals are distinct commits | `git log --diff-filter=D` per path | **CONFIRMED** — `377cdb3` → root `index.html`; `f6718b9` → `gate/` |
| §3.4 all four artifacts survive byte-identical | `git rev-parse 9ab26fc:<p>` vs `HEAD:<p>` | **CONFIRMED** — 5/5 blobs identical |
| §3.5 `scripts/serve-gate.sh` stale, points at `/gate/` | `cat` + blob compare | **CONFIRMED** — blob `b83f208d…` identical to Genesis; still targets `/gate/` |

The negative control is the decisive discriminator and it reproduces cleanly: a **green revision
exists** for these two nodes, so `ENV / ARTIFACT` ("depends on something outside the
repository") does not describe them. Contrast `F-02`, whose Genesis control is `3 failed`.

## 3. Regression accounting — the 12 retired rows, re-measured against a live baseline

The previously documented fingerprint was carried as prose. This pass **reproduced the baseline
from scratch** in a git worktree at `df7a99a` (a plain `git archive` extraction is *not*
equivalent — 19 tests need a real git repository and error with `cannot resolve HEAD`, which is
an extraction artifact, not repository debt).

| revision | fingerprint | architecture | `api/main.py` |
|---|---|---|---|
| `df7a99a` (PR base) — reproduced here | `32 failed / 1025 passed / 13 skipped / 2 errors` | — | — |
| `002b189` (`main` tip) — measured here | `20 failed / 1039 passed / 13 skipped / 2 errors` | `11/11` | `2519 / 2600`, `py_compile` clean |

The `df7a99a` figure **reproduces the documented baseline exactly**. Node-level delta:

- **retired: 12** — `test_agent_run` ×1, `test_ais_capability_profile_onboarding` ×1,
  `test_ais_w2_living_gate_grove_handoff` ×5, `test_prism_interior_shell` ×3,
  `test_solspire_p1_experience_01` ×2
- **new: 0**

All 12 were carried by PRs **#133/#135/#136/#137**, which have since **all merged**. The delta
is therefore fully attributed to merged carrier work, and the `20 failed` residue is the
sovereign-decision set (`F-01` ×1, `F-02` ×3, `SH-08` ×4, `SH-04` ×2, `SH-03`/`SH-07`/`R1–R3`,
`SH-05` rows 47–48) plus the two standing collection errors. **No unexplained regression.**

## 4. Merge-safety proof (the PR was *not* assumed safe from `mergeable/clean`)

`git diff main..head` renders this PR as *reverting* ~2400 lines of merged carrier work. That is
a **stale-base cosmetic**: PR #142 is based on `df7a99a` and therefore predates the eight
carrier merges. A three-way merge was simulated in a throwaway worktree:

```
$ git merge --no-commit --no-ff 466538c        # onto main tip 002b189
Automatic merge went well; stopped before committing as requested
$ git diff --cached --stat HEAD
 …/gate-hygiene-sh05-gate-artifact-provenance-01/EVIDENCE.md       | 216 +++++
 …/gate-hygiene-sh05-gate-artifact-provenance-01/WORKSTREAM_STATE.md | 101 ++
 2 files changed, 317 insertions(+)
```

**+317 / −0, two files, no `tests/` path touched**, and every carrier evidence directory remains
present. The PR adds only its own artifacts; it reverts nothing. Merge is safe.

## 5. Gate and scope checks

- **CP10 mutation-boundary judge:** re-run on this PR's 20-path change set → `PASS` (exit 0).
- **`sg-02-fe-2-v.yml` did not run on this PR, and that is correct** — its `pull_request` filter
  is `web/public_prism/**`, `spiral_grove/**`, `lab/**`, `api/lab_routes.py`, named test files,
  `requirements.txt`, and the boundary's own surfaces. A `docs/**`-only change matches none of
  them. Non-trigger is scope-correct, not a gap.
- **Check-runs on head `466538c`:** `Full-history secret scan` **success**,
  `Vercel Preview Comments` **success** (2 runs; `weaver_evolution` is skipped by design).
- **Boot surface untouched:** `api/main.py` not modified; `py_compile` clean; 2519 / 2600.

## 6. Corrections to carried state

- **The `SH-02` queue is closed, not merely drained of carriers.** PRs #133/#135/#136/#137 — the
  four IN_OPEN_PR carriers of the 12 rows — have **all merged**. `SH-05` is now the **only**
  open PR in the repository. Any state file still describing "12 rows in open PRs" is stale.
- **`SH-04` is recorded in the ledger narrative as "RESOLVED — no defect"** (cycle detection is
  ordered after membership validation, so `UnknownCapabilityError` legitimately precedes
  `CapabilityCycleError`), but ledger rows 43–44 still read `DRIFT`. The two
  `test_spiral_grove_registry.py` nodes remain red on `main`. The resolution is **not reflected
  in the row bucket**; that is a ledger-ownership task, not a hygiene edit.
- **Task-context baseline was stale again** (`main := 6038989`, `804 passed / 54 failed`,
  `arch := 9/10`). Live values are in §3. Do not attribute the difference to new work.

## 7. Non-claims

- **No disposition of `SH-05`.** Retire / relocate into `web/public_prism` / restore remain
  open, and the two repairs are opposite product answers. Not chosen here.
- **No test edit, no artifact restoration, no ledger reclassification** — as in `EVIDENCE.md` §4.
- **No production or runtime claim.** The Gate-2 `main → deployment → runtime` boundary is
  untouched; this is repository-history evidence only.
- **No gate status change.** No gate opened, closed, or promoted.
- **No merge, no push to `main`, no force-push, no self-authorization.**

## 8. Next bounded task

**None inside `gate-hygiene`.** The queue is exhausted; every remaining item is a sovereign or
product decision: `SH-05` (Gate UI fate), `F-01`, `F-02` ×3, `SH-08` (CP10-fenced), `SH-03`,
`SH-04` ledger-bucket correction, `SH-07`.

`SH-05a` (retire) and `SH-05b` (restore) each become a bounded hygiene task **only after** the
sovereign decides `SH-05`.
