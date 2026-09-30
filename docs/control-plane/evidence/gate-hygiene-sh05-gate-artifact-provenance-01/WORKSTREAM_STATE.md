# WORKSTREAM STATE — `gate-hygiene` / `SH-05` gate-artifact provenance 01

Persisted so the next heartbeat reconstructs from evidence, not memory.

## Pass identity

| field | value |
|---|---|
| clock | HOURLY (one bounded pass) |
| base main | `df7a99a067382401c00de5e7bbaaac0125ba2088` |
| branch | `gate-hygiene/sh05-gate-artifact-provenance-01` |
| classification | `IMPLEMENTED` (evidence-only) |
| authority required | merge only; `SH-05` disposition is sovereign |
| changed files | 2 new markdown artifacts — no test / source / workflow / governance file |

## Established this pass

- `main` = `df7a99a`; `origin/main` == `main`; tree clean; **history complete** (1393 commits,
  root `9ab26fc`). The clone arrived shallow; `git fetch --unshallow` restored ancestry.
- Full-suite fingerprint **unchanged** and independently reproduced:
  `32 failed / 1025 passed / 13 skipped / 2 collection errors` (111 s).
- `tests/architecture`: **11/11**. `api/main.py`: **2519 / 2600**, `py_compile` clean.
- All 8 open PRs: `mergeable / clean`, each with `Full-history secret scan` **pass** and
  `Vercel Preview Comments` **pass**. No red CI anywhere in the queue.

## `SH-02` queue — closed, do not reopen

Re-derived independently this pass and consistent with PRs #140 / #141:

| disposition | count | action |
|---|---|---|
| green on `main` | 19 | none, ever |
| in open PRs (#133 ×5, #135 ×3, #136 ×2, #137 ×2) | 12 | finish by **merging** |
| sovereign decisions (`F-01`, `F-02` ×3) | 4 | decide |
| unowned `STALE_ASSERTION` batch | **0** | — |

`F-02` (rows 27–29, `test_steward_filter.py`) — **independently reproduced**, not taken on
reading: both files are **blob-identical to Genesis** (`893871f8…`, `29598982…`), exactly one
commit touches each (`9ab26fc`), and the negative control at Genesis returns
`3 failed, 5 passed` — **no green revision exists**. PR #141 is correct; PR #138 §7 is
superseded. Still a sovereign product decision.

## `SH-05` — the finding this pass adds

Ledger rows 47–48 (`test_gate_serve_script.py`, `test_gate_status.py`) are bucketed
`ENV / ARTIFACT` ("depends on something outside the repository"). **That bucket is wrong.**

- Root `index.html` and `gate/` were **tracked at Genesis** (`9ab26fc`), added by the *same*
  commit as the two test files.
- **Negative control:** the nodes were **green at Genesis** — `3 passed`. A green revision
  exists and was lost. (Contrast `F-02`, where none ever existed.)
- They regressed at **two different commits**: row 47 on **2026-03-23** (`377cdb3`), row 48 on
  **2026-07-15** (`f6718b9`) — verified by running the set at `377cdb3^` (3 passed) and
  `f6718b9^` (1 failed, 2 passed).
- Both removals were deliberate `archive` relocations. All four artifacts survive
  **blob-identical** (`archive/legacy_python/index.html`, `archive/legacy_frontend/gate/*`).
- `scripts/serve-gate.sh` is **blob-identical to Genesis** and still points at `/gate/` — a
  stale launcher left dangling by `f6718b9`.
- `f6718b9` is also the commit `AGENTS.md` records as first reddening the CP10 boundary.
  Context only; no action.

**Disposition remains sovereign** (retire / relocate into `web/public_prism` / restore). Both
repairs are opposite product answers, so neither was taken inside a hygiene pass.

## Corrections to prior heartbeat state

- Prior state (task context) listed `SH-05` only as *"review evidence/queue docs"* with no
  provenance. It now has provenance; the disposition is still open.
- Prior state carried the clone as **grafted/shallow**, so ancestor claims were `UNKNOWN`. The
  clone is now **complete**; the Genesis and regression-point claims above are **verified**,
  not inferred.
- The task context's baseline (`main := 6038989`, `804 passed / 54 failed`, `arch := 9/10`) is
  **stale**. Live: `df7a99a`, `1025 passed / 32 failed / 13 skipped / 2 errors`, `arch := 11/11`.
  Do not attribute the difference to new work — the recorded fingerprint drifted.
- The task context framed the active item as the `#141` vs `#138` contradiction. That is
  **settled** (#141 correct) and awaits only a sovereign merge.

## Next bounded task

**None inside `gate-hygiene`** until the queue drains or a decision lands.

1. **Merge sequencing (sovereign).** Carriers #133/#135/#136/#137 retire 12 rows; `#138`, `#139`,
   `#140`, `#141` are evidence-only. PR #139 measured that **every** ordering of #135/#136/#137
   conflicts on the shared ledger and `#137` must be last. Flagged, not acted on.
2. **`SH-05` (sovereign).** Decide the Gate UI's fate, then `SH-05a` (retire) or `SH-05b`
   (restore) becomes a bounded hygiene task.
3. **`F-02` (sovereign/product).** `transcend*` stem-match; Rule 4 vs Rule 3 precedence;
   `compress_to_choices` sentence-splitting.
4. **`SH-08` (sovereign/product).** Which Spiral Grove activity surface is canonical. CP10-fenced
   (`sg-02-fe-2-v.yml`) → out of scope for this workstream.
5. **`SH-03`** (`"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"`) — awaits product decision.

Do **not**: invent an `SH-02` batch; repair green nodes; touch `DRIFT`/`ENV` nodes beyond the
evidence recorded here; touch the `R1/R2/R3` recon nodes; reclassify the ledger from this branch.

## Constraints honoured

Evidence-only. No test, source, workflow, governance or constitutional file modified.
`api/main.py` untouched and under budget. CP10 mutation-boundary judge: **PASS** on this change
set. No merge, no push to `main`, no force-push, no self-authorization, no new mutation or
authorization path.
