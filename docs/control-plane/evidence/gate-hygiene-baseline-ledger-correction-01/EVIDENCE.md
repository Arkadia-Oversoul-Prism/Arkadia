# EVIDENCE — Gate hygiene: baseline ledger correction (SG-04 + live drift)

- **Gate / workstream:** GATE-10 context — test-suite hygiene
- **Bounded task:** correct the classification ledger's SG-04 causally-inverted
  `STALE_ASSERTION` call, and reconcile the ledger's 51-row inventory with the live baseline
  nodes. Documentation/evidence only.
- **BASE_MAIN:** `4164573586860b9c7e04e1815bca4957559046a2` — `main` after PR #128
- **Branch:** `gate-hygiene/baseline-ledger-correction-sg04-01`
- **Authority:** test-hygiene / evidence only. No source, test, policy, governance, workflow,
  identity, authority-model, or architecture mutation.
- **Status:** IMPLEMENTED (targeted regression green, negative control recorded, full-suite
  fingerprint measured; no runtime claim made; sovereign merge pending)

---

## 1. Scope — and what this pass deliberately did NOT do

The previous heartbeat's own open queue named *"repair SG-04 contradictory artifacts"* as the
next task. This pass **stop-checks that intent** rather than executing it, because closer
inspection showed the task as stated is both **larger than its label** and **outside this
workstream's authority boundary**.

Per the automation contract's HARD STOP clause (*"task scope becomes ambiguous"*, *"evidence
contradicts implementation"*) and the rule *"DO NOT PATCH AROUND IT — RECORD BLOCKER, UPDATE
EVIDENCE, NOTIFY SOVEREIGN, STOP THIS PASS"*, the SG-04 repair is **escalated, not applied**.

The bounded, safe, in-envelope substitute is the **classification correction**: the ledger
currently mislabels SG-04, and the next heartbeat would inherit that error.

---

## 2. Finding A — SG-04 is a merge CONTRADICTION, not stale drift

`tests/test_spiral_grove_activity_runtime.py` expects a mounted `ActivityRuntime` **and**
chamber-level inline surfaces. Two mutually exclusive expectations:

1. **The "inline surface" expectations were never implemented, ever.** No revision of
   `CapabilityChamber.tsx` satisfies them alongside the runtime mount.

   ```
   74f5494 mount=1   1b63994 mount=1   06ad5f2 mount=1   main mount=0
   ```

   `learning-activity-work-surface` appears only in pre-SG-04 SG-03/AIS revisions and in
   current `main`; **never** in an SG-04 revision.

2. **The branch tip was red before the merge.** In a worktree at `06ad5f2`:
   `7 failed, 25 passed` on the SG-04 set. The merge did not regress a green branch.

3. **The merge kept the wrong side.** `ff80b8c` (a commit on **main's own history**) and
   `origin/main @ 4164573` carry the **identical** `CapabilityChamber.tsx` blob `0cde2f78…`,
   which drops the `<ActivityRuntime/>` mount and retains the legacy inline draft capture
   (declaration present, zero uses). The branch had produced `cef5a593…` (mount present).

4. **`activity-surface-research` was never implemented** in any revision of
   `ActivityRuntime.tsx` (`74f5494`, `1b63994`, `06ad5f2` are the only ones) — so
   `test_spiral_grove_activity_runtime.py:41` never had a passing state.

**Why "just restore the mount" is not a safe bounded repair:**
- It is a **frontend capability change** (`web/public_prism/**`), not a test edit. It would
  break the other assertions that require the inline surface, so it also requires
  **choosing between two activity surfaces** — a product decision.
- `web/public_prism/**` is inside the **CP10 boundary's path filter**
  (`.github/workflows/sg-02-fe-2-v.yml:7,33`). Any edit there is judged by the mutation
  boundary and would put this PR inside the CP10 workflow's trigger set.
- The gate would then also demand a **frontend build** as evidence, which is
  environment-blocked in this sandbox (no npm registry) — an unprovable claim, which the
  contract forbids (`NEVER DECLARE VERIFIED WITHOUT RUNTIME EVIDENCE`).

Governance-invariant check: the properties the SG-04 tests exist to protect are **intact**.
`generateExercise` and `createEvidence` are absent from the chamber; the SG-03 downstream
boundary is still enforced by `test_ais_w5_evidence_capture.py`, which **passes** on the shape
main carries.

**Escalation:** `SH-08` (new) — sovereign decides which activity surface is canonical. Until
then the seven SG-04 nodes stay red and must **not** be repaired from this workstream.

---

## 3. Finding B — four live failing nodes are absent from the ledger

Live fingerprint at `4164573`: **39 failed / 1018 passed / 13 skipped / 2 errors (41 nodes)**.

`tests/test_solspire_r{1,2,3}_*.py` are forked-recon **file copies**; their suites post-date
`a26af408` and were never classified. All four failing nodes are **REAL_DEFECT** in the
contract-drift sense — in each case the safety boundary still holds and it is the *error
contract* that moved:

| node | observed | boundary still holds? |
|---|---|---|
| R1 `…builders_delegate_to_weaver` | `'mvp1-50c0ee9b89' == 'mvp1-r1-patch'` | yes — delegation shape, `pass_id` not forwarded |
| R1 `…weaver_governance_is_canonical` | `'execute_patch'` absent from `weaver/governance.py` | yes — no second governance path exists |
| R2 `…legacy_commit_file_fails_closed_without_network_write` | `KeyError: 'code'` | **yes** — it *does* fail closed; only the result contract drifted |
| R3 `…runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | `PermissionError` raised synchronously | **yes** — it *does* refuse; only the refusal channel drifted |

Their workflows (`solspire-r{1,2,3}-validation.yml`) trigger **only** on
`push` to `recon/solspire-r0`, so they are **inert for `main` CI** but do execute in the local
suite. Recorded, not repaired (they are unrelated to a test-hygiene correction pass).

---

## 4. Verification

```
python -m pytest tests/architecture -q                     -> 11 passed
python -m pytest tests/test_m02a_ci_gate_integrity.py -q    -> pass (CP10 integrity intact)
python -m py_compile api/main.py                            -> OK (2519 / 2600 lines)
full suite                                                  -> 39 failed / 1018 passed /
                                                               13 skipped / 2 errors
                                                               (unchanged vs pre-pass)
```

**Negative control.** The correction is *falsifiable*: §4.1's original text is left verbatim
and the correction is an additive annotated block plus a new §11. Re-reading §4.1 without the
annotation reproduces the original, wrong classification. `git diff --stat` on this branch
confirms the ledger edit is **additive only** — no sentence deleted or reworded.

**Regression boundary.** Zero test files, source files, policies, or workflows are touched, so
the full-suite fingerprint is *expected* to be identical in node names; it was re-measured
rather than assumed.

---

## 5. Remaining uncertainty

- The `DRIFT` nodes and `SH-03`/`SH-06`/`SH-07`/`F-01` are untouched and still await product or
  architectural decisions. None is a defect.
- The SG-04 surface decision (`SH-08`) is a genuine open product question, not a hygiene task.
- `vite build` remains environment-blocked; no frontend claim is made or implied.

## 6. Authorization

No merge, no authorization change, no identity-boundary change, no authority-model change, no
new mutation or authorization path, no scope expansion into `web/public_prism/**`. Human
merge only.
