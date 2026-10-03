# gate-hygiene — SH-05 retirement boundary: HOLD (sovereign call required)

**Workstream:** `gate-hygiene-sh05-retirement-boundary-hold-01`
**Branch:** `gate-hygiene/stale-gate-fixture-retirement-01`
**Base main:** `162f574b05dd839540d803aadda7608342618a84` (recorded `BASE_MAIN` for this pass)
**Pass:** hourly bounded execution, 2026-10-03
**Classification:** `BLOCKED` — the bounded task is exactly a sovereign-only decision
**Authority:** merge + `SH-05` disposition = **sovereign**; this pass makes no product decision.

---

## 1. What this branch does

`f1404f0` (tip) carries three commits on top of `main @ 162f574`:

| commit | subject |
|---|---|
| `bb8a901` | gate-hygiene: retire stale gate fixture tests asserting archived surface |
| `6acf3bc` | gate-hygiene: republish canonical fingerprint pair across docs |
| `f1404f0` | gate-hygiene: prove superseded fingerprint origin across the retirement |

Changed paths (vs `main`):

- `tests/test_gate_serve_script.py` — **deleted**
- `tests/test_gate_status.py` — **deleted**
- `tests/fixtures/baseline_node_set.txt` — 20 → 18 nodes
- `tests/fixtures/superseded_baseline_node_set.txt` — new, 20 nodes
- `tests/test_baseline_fingerprint.py` — adds `SUPERSEDED_NODE_SET` (hash-only guard)
- `.bootstrap/01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md`,
  `docs/phase1/CONTINUATION_LEDGER.md` — fingerprint/state republish

The two deleted files contain exactly the nodes named by the SH-05 ledger rows 47–48:

```
tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists
tests/test_gate_status.py::test_gate_files_and_fetch_handling
```

---

## 2. Premise verification (is there a real defect?)

The retirement premise is that both nodes assert a root `gate/` + root `index.html`
surface that no longer exists. Measured on `main @ 162f574`:

```
tests/test_gate_status.py::test_gate_files_and_fetch_handling     FAILED
tests/test_gate_serve_script.py::test_report_export                PASSED
```

- `Path('gate') / 'index.html'` does not exist — root `gate/` was archived by `f6718b9`.
- `test_gate_serve_script.py` carries **two** tests; only
  `test_root_index_redirect_and_script_exists` is failing. The file is not wholly dead.
- `index.html` exists at `static/index.html` and `archive/legacy_python/index.html`;
  `gate/` exists only at `archive/legacy_frontend/gate/`. All four artifacts survive
  byte-identical (`06ada00a…`, `197924c0…`, `555afbcf…`, `eb8abdb6…`).

So the defect is real **and** narrower than a whole-file deletion implies.

---

## 3. The boundary finding — why this is a HARD STOP

The SH-05 evidence pass explicitly declined to make this change and named it as a
sovereign-gated follow-up. Verbatim from
`docs/control-plane/evidence/gate-hygiene-sh05-gate-artifact-provenance-01/EVIDENCE.md` §4/§6:

> **No test edit and no artifact restoration.** Repairing the assertion to accept
> `archive/legacy_frontend/gate/` would ratify the archiving; restoring the artifact would
> ratify the launcher. Those are opposite product answers. Choosing one inside a hygiene
> pass would be a product decision taken by stealth.

> | `SH-05` | **Decide the Gate UI's fate** — retired, relocated into `web/public_prism`, or restored to root? | product decision | **sovereign** |
> | `SH-05a` | *If* the Gate UI is retired: re-point both assertions at the archived path (or delete the nodes) and drop the stale `/gate/` URL from `scripts/serve-gate.sh`. | hygiene | sovereign gate on `SH-05` |

Deleting `tests/test_gate_serve_script.py` and `tests/test_gate_status.py` **is `SH-05a`** —
the "retire the Gate UI" branch of a three-way product question (retire / relocate /
restore). Its own evidence table marks it *"sovereign gate on `SH-05`."*

`SH-05`'s disposition was never decided:

- PR #142 (the SH-05 evidence PR) is **MERGED** `2026-10-01T15:18Z`, evidence-only, at
  classification `IMPLEMENTED` / "READY FOR SOVEREIGN MERGE" — authority = merge only.
- PR #142's comment thread contains only the Vercel bot; **no sovereign disposition landed.**
- `docs/control-plane/evidence/gate-hygiene-open-pr-queue-merge-order-map-02/`
  `WORKSTREAM_STATE.md` §3 records SH-05 as **EXHAUSTED** and directs: *"do not open new
  work on SH-05."* (Documentation edits, if any, belong on PR #142, not a new branch.)

The branch contains **no** authorization record for this decision. Its own state docs
still say the opposite — `.bootstrap/01_STATE.md:68` (*"a recommendation, not an
authorization; beginning it requires a sovereign decision"*), `MISSION.md:101`,
`NEXT_AGENT.md:86` (*"Candidates requiring a sovereign ruling first (do not self-authorize)"*).

**Conclusion:** the branch is a coherent, well-evidenced *proposal* for `SH-05a`, but
executing it now crosses the `SH-05` sovereign boundary. Per the execution contract
(`HARD STOPS` → authority model / scope; `NO SELF-EXPANSION`), the pass stops here.

---

## 4. What is safe and remains true on this branch

- The **superseded set is byte-identical to `main`'s recorded set** — `diff` of
  `main:tests/fixtures/baseline_node_set.txt` against
  `tests/fixtures/superseded_baseline_node_set.txt` is empty. The "superseded" fixture
  correctly preserves the pre-retirement state for a future reversal.
- The retirement is **not** what fixes the recorded fingerprint. The published canonical
  pair `6c7bf821…` / `2bc35996…` already binds to an 18-node set on `main`; the retirement
  reproduces the same pair because it *removes the two nodes the recorded set already
  excluded*. The retirement and the fingerprint work are **independent**.
- `scripts/serve-gate.sh` is **untouched** by this branch, so the stale `/gate/` URL
  flagged in SH-05 §4 remains open regardless of this branch's fate.

## 5. Reproducibility check — the live fingerprint does not bind to the published pair

Measured this pass on the branch tip `f1404f0`:

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
  -> 18 failed / 1306 passed / 18 skipped / 1 error   (19 failing/error nodes)

python scripts/baseline_fingerprint.py <pytest log>
  -> outcomes 0cc09dd0bf2a966df0ee7eabd02d2c2c13476f0d8f66b578adc715524ecfa95b
  -> ids      95b155130d73672d9388bcc83604a92a5f20d620c519e365af6d13129f086050
```

The published canonical pair is `6c7bf821…` / `2bc35996…`. They differ because the
**live** clone (with PR-head revision `7d79f38…` present) carries the extra depth-dependent
node `test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`,
which the recorded 18-node set intentionally excludes. This is the known clone-depth
regime, not a regression — recorded so a later pass does not read the delta as new debt.

---

## 6. Open gate-hygiene stack (live, `2026-10-03`)

All five open PRs are `MERGEABLE` / `UNSTABLE`; the required `Full-history secret scan`
check is `success` on every head. `Vercel` console checks fail on all heads because the
`arkadia-prism` Vercel project no longer exists — a pre-existing provider fact, not a
property of these diffs.

| PR | branch | head | pinned next task |
|---|---|---|---|
| #215 | `baseline-node-depth-stability-01` | `0c18fbb4` | make the recorded set depth-stable |
| #216 | `superseded-fingerprint-origin-01` | `4747e4c6` | publish the superseded set + hash-only guard |
| #217 | `live-file-fixture-revision-pin-01` | `3b5e4cdc` | pin the adjudication fixture to the corrupt revision |
| #218 | `adjudication-fixture-commit-pin-01` | `54e2e988` | pin the gate-2 adjudication fixture |
| #219 | `open-pr-queue-merge-order-map-02` | `e60bc913` | map the queue (docs + fixtures) |

Composability: composed tree `/tmp/compose @ 0d8ba22` carries **zero** conflict markers
and `tests/test_baseline_fingerprint.py` → **19 passed**. The combined delta vs `main`'s
recorded 20-node set is **2 nodes fixed** (the retired gate pair) / **0 new** failures.
The five are order-insensitive and individually safe; **merge authority is sovereign.**

Note: `#219`'s pinned next bounded task is "repair the two adjudication fixtures" — already
covered by `#217`/`#218`. There is therefore **no uncovered bounded task** left in the
open stack; the only blocker on the queue is the sovereign merge decision.

## 7. Non-claims

- **No product decision.** Whether the Gate UI is retired, relocated, or restored is not
  decided here and must not be inferred from this branch existing.
- **No production or runtime claim.** Repository-history evidence only; the Gate-2
  `main → deployment → runtime` boundary is untouched.
- **No merge.** This PR is opened as `HOLD` and is not proposed for merge until a
  sovereign `SH-05` disposition is recorded.

## 8. Required sovereign action

One of:

1. **Retire** — record the `SH-05` disposition, then this branch (or an equivalent) may
   proceed to merge as `SH-05a`.
2. **Relocate** — point the Gate UI at `web/public_prism`; the assertions move rather than
   being deleted; this branch is superseded.
3. **Restore** — re-point the assertions at the archived path / restore the root artifact;
   this branch is rejected.

Until one is recorded, the correct state of this work is **HOLD**.
