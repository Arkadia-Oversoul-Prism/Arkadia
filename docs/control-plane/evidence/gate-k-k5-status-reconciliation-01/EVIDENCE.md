# EVIDENCE — Workstream K / K5 status reconciliation

**Pass:** Weaver hourly bounded execution — `gate-k/k5-status-reconciliation`
**Date:** 2026-09-30
**BASE_MAIN:** `002b189dd95e41c9b4f4cca33d08b4121453d289`
(`Merge pull request #141 from Arkadia-Oversoul-Prism/gate-hygiene/f02-steward-filter-provenance-01`, 2026-09-30 02:22:31 +0100)
**Authority:** documentation/state reconciliation only. No implementation code changed.
No merge, no push to `main`, no force-push, no self-authorization.

---

## 1. Objective (bounded)

Reconcile the checkpoint status carried in the repository's own state documents with the
state actually present on `main`. Completion condition: the three state documents agree
with live evidence and with each other, and the K5 checkpoint record required by
`MISSION.md` §Deliverables exists.

## 2. Contradiction found

`.bootstrap/01_STATE.md:16` declared:

```
**K5 — Static Ingestion** (READY TO BEGIN)
```

K5 had in fact already shipped on `main`. Verified from git history and working tree:

| Evidence | Value |
|---|---|
| K5 module | `knowledge/static_ingestion.py` (`_SOURCES`, `run_static_ingestion`) |
| First commit | `606510f` (2026-08-03) |
| Follow-on commits | `4ca0442`, `0852068`, `31818e3` (final: 2026-09-29, "make static ingestion a checksum fixed point") |
| Lifespan wiring | `api/main.py` lines 204–207 — `schedule_static_ingestion()` in a guarded `try/except`; `knowledge/static_ingestion.py:317-329` launches a daemon thread so startup is not blocked |
| Tests | `tests/test_static_ingestion_sources.py`, `tests/test_static_ingestion_idempotency.py` → **12 passed** |

So the bootstrap marker was **STALE**, not the code. The classification doc's own warning
applied: do not trust stale prose over live repository evidence.

A second, independent divergence: `NEXT_AGENT.md` recommended **CS2** (reusable
conversational UI) while `.bootstrap/01_STATE.md` / `MISSION.md` tracked the live
Workstream K sequence. Both could not be "next". Workstream K is the active sequence, so
K4 is the next checkpoint and CS2 is recorded as deferred — not discarded.

## 3. K3 / K4 status re-derived from live evidence

Correcting K5 without re-deriving the rest would simply move the staleness one checkpoint
forward, so both were re-verified:

| Checkpoint | Verdict | Evidence |
|---|---|---|
| K3 — Context Engine Wiring | **COMPLETE** | `assemble_context` is consumed by `api/oracle_spine.py:60-63` and `api/knowledge_routes.py:257-261,407-415`. K3-A/B/C checkpoint records present in `docs/checkpoints/`. |
| K4 — Response Provenance | **ABSENT → NEXT** | No Oracle response path returns a `sources` array. `api/oracle_spine.py` reports only `notes_retrieved` (a count) and `source` (a provenance label) — note identities are available but never propagated to the client. |

`grep -rn '"sources"' api/*.py` returns `api/echofeild.py:213`, `api/main.py:805`
(`/api/keys/pool`), `api/source_routes.py:19,79` — none of which is the Oracle
response path. K4 is genuinely unimplemented.

## 4. Changes (documentation only)

| File | Change |
|---|---|
| `.bootstrap/01_STATE.md` | K5 marked complete with evidence; K3 marked complete; next checkpoint set to K4; Repository Health section updated with the measured baseline and its derivation |
| `MISSION.md` | Status table updated; Mission rewritten for K4; Objective section rewritten for K4 with verified starting state and explicit out-of-scope list; Deliverables paths updated for the next checkpoint |
| `NEXT_AGENT.md` | Status table updated (K1/K5 complete, K4 next); CS2 demoted to a preserved "Deferred" section; K4 recommendation added with the spine seam named |
| `docs/checkpoints/K5_static_ingestion.md` | **NEW** — the checkpoint record `MISSION.md` §Deliverables required but which was never created |

No source file, test, workflow, ADR, ROADMAP, or governance document was modified.
`api/main.py` was not touched.

## 5. Verification

| Check | Command | Result |
|---|---|---|
| Architecture fitness | `python3 -m pytest tests/architecture -q` | **11 passed** |
| CP10 gate-integrity invariant | `python3 -m pytest tests/test_m02a_ci_gate_integrity.py -q` | **49 passed** |
| K5 tests | `python3 -m pytest tests/test_static_ingestion_sources.py tests/test_static_ingestion_idempotency.py -q` | **12 passed** |
| CP10 judge on the actual diff | `git diff --cached --name-only \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS**, exit 0 |
| Full suite | `PYTHONPATH=<repo>/archive/legacy_python python3 -m pytest tests/ -q --continue-on-collection-errors` | **20 failed / 1039 passed / 13 skipped / 2 errors** |

### Baseline comparison — no regression

Recorded baseline at the start of this pass was
`20 failed / 1039 passed / 13 skipped / 2 collection errors`, 22 failing/error nodes.
This pass reproduces **the same counts and the same 22 node ids**. The change set is
documentation-only, so no fingerprint delta is expected or observed.

The 22 nodes are pre-existing, environment-dependent debt already classified in
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/` and
reconciled against the merged SH-02 stale-assertion repair PRs (#124–#137). None is
attributable to this pass.

**Fingerprint honesty note.** The prior pass recorded
`d7ff35b29968a354a611d417034079663a3bd151388c1c7f0b41738b03687036` without documenting
its derivation. That value **could not be reproduced** from the node list by any of the
plausible derivations tested (lines/ids × sorted/as-run × four separators × trailing
newline or not). The *counts and node set* are consistent with the prior pass; only the
hash string is unverifiable. Recorded as **UNKNOWN provenance**, not as agreement.

This pass therefore publishes its own derivation explicitly, so the next pass can
reproduce it. Verified this pass against the live run output:

```
PYTHONPATH=<repo>/archive/legacy_python python3 -m pytest tests/ -q \
  --continue-on-collection-errors 2>&1 \
  | grep -E "^(FAILED|ERROR)" | sort > nodes.txt
sha256( "\n".join(sorted(nodes.txt)) + "\n" )
  = a7687fadaa25ad5f8aa283747bbffa85d304d516ae2b6c53b3849dc54479434c
```

Two details matter for reproducibility, and both were confirmed rather than assumed:

- **The hash is over the full `FAILED`/`ERROR` summary lines, not the node ids alone.**
  Hashing node ids only yields a different value (`9b86a1ae…`), which is *not* the
  fingerprint; do not substitute it.
- **The `sort` is load-bearing, not idempotent.** pytest emits its short summary in
  *report* order, which is not lexicographic (`tests/test_static_ingestion_sources.py`
  sorts before `tests/test_autonomy.py`). As-emitted hashing yields `794755b7…`; sorted
  yields `a7687fad…`. An earlier draft of this note claimed the two coincide — that was
  wrong and is corrected here.

A fingerprint is only meaningful if its derivation is pinned this precisely; an
unpinned hash cannot distinguish "unchanged" from "differently computed".

## 6. Gaps recorded, not fixed (out of scope by construction)

Recorded in `docs/checkpoints/K5_static_ingestion.md` §Known gaps and surfaced in
`MISSION.md` as explicit K4 non-scope:

1. **`static:spiral_codex` matches zero files.** Root `static/**/*.md`; `static/` contains
   no markdown at all (`find static -name '*.md'` → 0) — only HTML/JS/CSS assets. The
   declared "Spiral Codex scroll" corpus is empty, so this source ingests nothing.
2. **`static:docs` is non-recursive.** `glob="*.md"` covers the 16 top-level markdown
   files in `docs/`, while `docs/` holds 290 markdown files in total — 126 under
   `docs/control-plane/` and 22 under `docs/recon/` are unscanned by this source, though
   `MISSION.md` scoped "any other structured markdown in `docs/`". `docs/adr` (6),
   `docs/collective` (5) and `docs/creative` (7) are each scanned non-recursively by
   their own declared source, so they are covered — but only at their top level, which
   is currently equivalent since none has nested markdown.
   This is **not** test-pinned: no test references `static:docs` (the only pinned filename
   set is the six ADRs, `tests/test_static_ingestion_sources.py:20`). It is a
   **corpus-curation** decision reserved to the sovereign, already recorded as such in
   `docs/control-plane/evidence/k5-open-loop-corpus-coverage/EVIDENCE.md` §6, which
   explicitly declined to bundle it. Widening it is a decision, not a one-line fix —
   but the reason is authority, not a test.
3. **`note_type` divergence.** `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` §K5 specifies
   `"event"` for open loops; the implementation uses `"task"`. Both are valid
   `NODE_TYPES` members; the ontology is frozen, so this is recorded, not changed.

Each is a candidate for its own bounded workstream. None is executed here — discovery
does not authorize execution.

## 7. Open-PR / gate state at this pass

Four open PRs against `main`, all `CLEAN`, none duplicating this workstream:

| PR | Head | Created | Scope |
|---|---|---|---|
| #142 | `59fbb531` | 2026-09-30T01:28Z | gate/ artifact rows 47–48 provenance |
| #143 | `7d79f38b` | 2026-09-30T03:48Z | Gate 2 production parity chain |
| #144 | `09521d2f` | 2026-09-30T06:06Z | test-session DB isolation |
| #145 | `dcebc95b` | 2026-09-30T10:46Z | full-suite intermittency attribution |

**CP10 check-run absence is expected, not a gap.** `sg-02-fe-2-v.yml` is path-filtered to
`web/public_prism/**`, `spiral_grove/**`, `lab/**`, `api/lab_routes.py`, named test files,
`scripts/cp10_mutation_boundary_policy.py`, `tests/test_m02a_ci_gate_integrity.py`,
`requirements.txt`, and the workflow itself. A docs-only PR matches none of those paths,
so no CP10 check-run is produced — for #142–#145 as much as for this pass. The
`Full-history secret scan` job *does* run on every `pull_request` and reports success on
all four heads.

This pass does **not** claim those PRs are ungated; it records that the gate is
path-filtered by design and that the CP10 *invariant* (every tracked path admitted) is
independently proven by `tests/test_m02a_ci_gate_integrity.py` → 49 passed.

## 8. Authorization boundary

- No merge performed; no push to `main`; no force-push.
- No governance, ADR, identity-boundary, or authority-model change.
- No new mutation or authorization path.
- This PR is **READY_FOR_SOVEREIGN_MERGE**. A human merges.

## 9. Result classification

**IMPLEMENTED** — the reconciliation exists, all required tests pass, the baseline is
fingerprinted with a reproducible derivation, and provenance is inspectable. Not
`VERIFIED`: no runtime/deployment observation is claimed, and none is needed for a
documentation-only change.
