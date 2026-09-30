# WORKSTREAM_STATE — AGENTS.md encoding adjudication (heartbeat record)

## Live state at this pass

| item | value |
|---|---|
| `main` (BASE_MAIN) | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| remote | `Arkadia-Oversoul-Prism/Arkadia`, branch `main` verified |
| this branch | `gate-hygiene/agents-md-encoding-adjudication-01` |
| this commit | `4bad44718fa4161ac00bd3cc44905b87e0aba04c` |
| PR | #151 (open, base `main`) |
| status | `IMPLEMENTED` — evidence complete, awaiting sovereign decision |

## Open PRs observed this pass

| PR | branch | base | head | note |
|---|---|---|---|---|
| #150 | `gate-hygiene/gate2-agents-md-cp866-repair-01` | main | `03fe21fe` | **CORRECT repair** — endorsed |
| #149 | `gate-hygiene/render-codex-collection-error-prove` | main | `00221300` | owns 1 of the 2 collection errors |
| #148 | `gate-hygiene/scheduler-bootstrap-testspec-repair` | main | `4fd05b0a` | owns baseline failures |
| #147 | `gate-hygiene/gate2-agents-md-encoding-repair` | #143 branch | `20d184b8` | **SUPERSEDED** — not closed |
| #146 | `gate-k/k5-status-reconciliation` | main | `5017da6b` | |
| #145 | `gate-hygiene/test-session-db-intermittency-attri` | main | `8a2b7048` | |
| #144 | `gate-hygiene/test-session-db-isolation-01` | main | `09521d2f` | |
| #143 | `gate-hygiene/gate2-production-parity-02` | main | `7d79f38b` | GATE-2 parent |
| #142 | `gate-hygiene/sh05-gate-artifact-provenance-01` | main | `59fbb531` | |

Note: `main` is **unchanged** since the previous pass. No movement detected.

## Resolved this pass

The PR #147 vs #150 contradiction is **decided** by byte oracle: PR #150 correct, PR #147
superseded. Verdict recorded on both PRs and in
`docs/control-plane/evidence/gate-hygiene-agents-md-encoding-adjudication-01/EVIDENCE.md`.

**Closure is not performed** — closing a PR is sovereign authority. Both PRs carry the verdict
as a comment so the decision survives without this conversation.

## Baseline fingerprint (start of pass)

- full suite: 20 failed / 1055 passed / 11 skipped / 2 collection errors
- isolated failure files: 20 failed / 66 passed (identical with the two new files removed)
- architecture: 11/11
- CP10 boundary judge: PASS
- vite build: environment-blocked

No fingerprint change attributable to this work.

## Next bounded task (proposed, not started)

**GATE-2 production parity** remains the trajectory. Its open boundary is the standing
AEAS Runtime Boundary Pulse chain: `main SHA -> deployment SHA -> production response ->
UI/runtime observation -> evidence artifact`. Current main is `002b189d`. Production parity
must **not** be claimed until that SHA is tied to a live deployment and independently observed.

Candidate next bounded task: resolve whether the production deployment's source SHA equals
`002b189d` (or the eventual post-merge SHA once #150 lands), and record the boundary as
`VERIFIED` / `BLOCKED` / `UNKNOWN` accordingly — **without** inferring parity from repository
evidence alone.

## Do not do

- Do not fix the 20 baseline failures here; PRs #148 and #149 own that debt.
- Do not re-open or re-litigate the encoding verdict; it is byte-decidable and now recorded.
- Do not merge, close, or push to `main`.

---

## Pass 2 — merge-safety correction (subsequent heartbeat)

The pass-1 suite was green only on the tree it was written against. It asserted
"`main` is corrupted" as a *premise*, then adjudicated on top of it. PR #150 repairs
`AGENTS.md`, so merging it first turns those assertions red — the adjudication would
have broken the tree it exists to bless, and the queue could not be merged in either
order without a repair afterwards.

This is the same defect class the adjudication itself was written to catch: a claim
that outruns its own evidence. It is recorded here rather than quietly patched.

Fixed on this branch:

- oracle pin `pr150` -> `03fe21f` (immutable commit; a merged branch is deleted, so the
  ref would dangle).
- `audit()` reports `decidable=False` for a clean file with no oracle (`decidable_basis`
  `"none"`): a clean file and a never-verified repair are identical bytes.
- CLI exit `2` (not `1`) in that case; exit `1` now means "clean **and** oracle-verified".
- live-file tests are state-scoped; `test_live_file_verdict_matches_its_state` covers
  both trees so exactly one branch runs per revision.

### Verification (both merge orders)

| scenario | how | result |
|---|---|---|
| corrupted `main` | `pr151` as-is | **17 passed** |
| `#150` + `#151` merged | synthetic `git merge-tree pr151 pr150` worktree | **15 passed / 2 skipped** |

The 2 skips are the corrupted-tree assertions, which correctly do not bind on a repaired
tree. Regression boundary: no production module, no `api/main.py`, no `AGENTS.md` change.

### Effect on the queue

PR #151 is now independent of merge order with #150. The sovereign may merge **either
first** without a red suite. The queue adjudication itself is unchanged:

| PR | verdict |
|---|---|
| #150 | **merge** — correct cp866 repair |
| #147 | **close as superseded** (it also edits `AGENTS.md`, so #150 and #147 conflict) |
| #143 | parent GATE-2 branch; its `AGENTS.md` edit is a *third*, different repair — see below |
| #152 | test-only (fingerprint guard); independent |

### Correction to a pass-1 omission

Pass 1 compared only #147 against #150. `#143` also modifies `AGENTS.md` (265 changed
lines) and produces a **third distinct** content hash:

| revision | `AGENTS.md` sha256 |
|---|---|
| `main` | `57bf37f9` (corrupted) |
| `#143` | `08e2af0d` |
| `#147` | `2ccde4c5` |
| `#150` | `a7ef8002` (byte-oracle recovered) |

#143 is the GATE-2 parent carrying the production-parity work, so it is the most
consequential branch of the three, and its repair is not the verified one. Merging #143
as-is lands a fourth, unadjudicated `AGENTS.md`. Its encoding must be adjudicated against
the same byte oracle before merge, or the `AGENTS.md` hunk must be dropped from it in
favour of #150's.

**Pass 3: discharged.** #143's `AGENTS.md` is adjudicated — a third corruption class (CP775
outer pass, Cyrillic 0 / Latin-1-Ext 594, not the CP866 class). Two-stage heal →
`af67aad45631d130d1c352efdea75a20e16cb829a3620d527c07e31f2772415f`, `oracle_reproduced=True`,
`oracle_alterations=[]`. Sound but disjunct from #150's `a7ef8002`; treat #143's `AGENTS.md`
hunk as **superseded by #150's** rather than merging both rewrites. Full detail in
`EVIDENCE.md` §11. Instrument gained `--shadow`/`audit_shadow`/`heal_shadow` (codec named by
the oracle, not preference). Tests: 23 passed on corrupted `main`; 21 passed / 2 skipped on
the synthetic #150+#151 merge. Fingerprint unchanged (1060 passed both trees; the single
failing-set delta is the order-sensitive `test_engineering_lab_agent_loop` flake). No merge.

Revised queue verdicts, all still human-only:

| PR | verdict |
|---|---|
| #150 | **merge** — canonical cp866 recovery (`a7ef8002`) |
| #143 | **merge after dropping its `AGENTS.md` hunk** (superseded by #150) |
| #147 | **close as superseded** — Cyrillic 188, never healed |
| #152 | test-only fingerprint guard; independent |
| #151 | this branch — adjudication instrument + evidence |

