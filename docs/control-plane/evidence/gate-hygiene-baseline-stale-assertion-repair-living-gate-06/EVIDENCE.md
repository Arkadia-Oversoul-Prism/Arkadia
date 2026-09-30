# EVIDENCE — `gate-hygiene` / SH-02 batch 6 (Living Gate / W2 handoff)

Bounded objective: repair the five `STALE_ASSERTION` failures in
`tests/test_ais_w2_living_gate_grove_handoff.py` (W2 — Living Gate A.I.S diagnostic →
Spiral Grove handoff) **without** editing any `web/public_prism/**` path, and record the one
node that is not a hygiene repair.

- **BASE_MAIN** (source of the runtime claim): `df7a99a067382401c00de5e7bbaaac0125ba2088`
- **Branch**: `gate-w2/living-gate-grove-handoff`
- **Scope**: test-only. No production surface, no frontend path, no `api/**` change.
- **Authority boundary**: root-cause diagnosis + test repair. No merge. No product decision
  taken. `main` untouched.

## 1. Precondition — the base moved under this pass

Reconstructed live, per contract step 01. The prior pass's base was stale:

| fact | prior pass assumed | measured this pass |
| --- | --- | --- |
| `origin/main` | `4164573` | **`df7a99a`** (PR #131 merged) |
| open PRs | PRs #130/#132 assumed open | **zero** — #130, #131, #132 all **merged** |

The first branch baselined in this pass was checked out at `4164573`, which **predates** the
merges of #130/#132/#131. Diffing that branch against the *new* main therefore reported seven
sibling gate-hygiene nodes as "newly failing" — an artifact of the stale base, not a
regression. Re-basing onto `df7a99a` removed all seven. **A node diff is only meaningful when
both sides share a base.**

## 2. Baseline fingerprint at `df7a99a` (measured, clean worktree)

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors
```

```
main df7a99a : 32 failed / 1025 passed / 13 skipped / 2 errors   (34 nodes)
architecture : 11/11 passed
py_compile api/main.py : pass    (api/main.py = 2519 / 2600)
vite build   : environment-blocked (no npm registry access)
```

The automation contract's `main := 6038989`, `804 passed`, `architecture 9/10` figures are
**stale**; so is the `39 failed / 1018 passed` figure carried in the batch-5 ledger. Both are
re-measured here. Counts move whenever tests are added — compare **node ids**, never counts.

## 3. What was repaired

Five nodes, all `STALE_ASSERTION` per
`…/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
(Appendix A rows 3–8), re-pinned to the live expressions:

| node | was | now asserts |
| --- | --- | --- |
| `test_living_gate_defaults_to_diagnostic_not_reset` | legacy `FlowStep` / `initialMode` shape | `STEPS` declaration + `useState(0)` opening on step 0 |
| `test_pulse_analyze_endpoint_preserved` | literal string in the component | route (`api/pulse.py`) → caller (`ArkadianPulse.tsx`) → transport (`apiClient`) |
| `test_spiral_grove_handoff_prop_and_cta` | bare prop name | prop declaration + CTA + `onGrove={onEnterSpiralGrove}` wiring |
| `test_app_wires_grove_navigation` | prop-drilled call site | `App.tsx` own-route (`view === 'grove'`) + import + `<SpiralGrovePage />` |
| `test_ims_lineage_preserved` | invitation copy inside the gate | lineage at its present location (`OfferingsPage.tsx`) |

Each keeps the property the test exists to protect; the copy is what was re-pinned, not the
governance claim.

## 4. Two defects found in the repair itself, and fixed here

1. **Over-broad guard.** The re-pin asserted `"reset" not in src.lower()`. The gate no longer
   contains the token at all, so the assertion is green *today* — but any incidental
   `type="reset"` button would red it without reopening the deleted reset entry. A false-red
   generator. Replaced with the constructs that actually encode the removed flow:
   `FlowStep` absent, `initialMode` absent, no `'reset'`/`"reset"` entry value.
2. **Dangling evidence reference.** The docstring cited
   `…/gate-hygiene-baseline-stale-assertion-repair-living-gate-06/` (did not exist) and
   `…-sci-nexus-01/WORKSTREAM_STATE.md` for F-01. The first is created by this pass; the
   second is corrected to point at this document.

## 5. F-01 — left failing, deliberately

`test_no_firebase_persistence_in_gate` is **not** stale-assertion drift and is **not**
repaired here. It asserts `"sessionStorage" not in src`; `LivingGate.tsx` uses
`sessionStorage` for a tab-scoped diagnostic handoff. `sessionStorage` is a browser
persistence facility, so the guard's *proxy* no longer measures its stated intent (no cloud
persistence, no silent identity creation) — the gate does carry zero `firebase`/`firestore`
references. Re-pinning the assertion would **loosen a persistence boundary**, which is a
governance decision, not test hygiene. Preserved exactly as `main` carries it.

The classification ledger (rows 251–252) flags exactly this coupling — durable/local
persistence — as the item needing a decision.

## 6. Additional finding — one handoff is incomplete, not stale

`test_node_entry_declares_the_ais_signup_boundary` (added by this pass) pins the surface that
`App.tsx` actually mounts. Verified: `LivingGate.tsx` is imported by **nothing** except a
string in `sciCommandRegistry.ts`; `App.tsx` routes `gate`/`aic`/`login` to `NodeEntry`.

The committed in-code note reports "NOT AUTO-REPAIRED — escalated as a product decision" but
its docstring and F-01's both cite
`…/gate-hygiene-baseline-stale-assertion-repair-sci-nexus-01/WORKSTREAM_STATE.md`, which does
**not contain** the escalation (its scope is `sci-nexus`). The `DECISION_CACHE.md` section on
Living Gate reads: **"DEFERRED — action required."** The escalation is real in substance but
has no in-repo record. That is a **continuity gap**, not a live product ask: the decision was
already made and is still pending, and this pass could not source it server-side (zero open
PRs implied, and the referenced PRs are merged). It is recorded here and in
`WORKSTREAM_STATE.md` §Next so the next heartbeat reconstructs it from evidence.

**No new product decision is requested by this pass.**

## 7. Verification

```
W2 file, standalone          : 9 passed / 1 failed (F-01, by design)  — 10 nodes, no count drift
full suite, branch            : 27 failed / 1031 passed / 13 skipped / 2 errors
  vs main df7a99a             : 32F → 27F  (−5, exactly the five repairs)
nodes ADDED vs main           : none
nodes REMOVED vs main         : the five repaired W2 nodes only
architecture                  : 11/11 (unchanged)
py_compile api/main.py        : pass
CP10 mutation boundary (this diff): tests/ + docs/ only — outside the
                                `sg-02-fe-2-v.yml` path filter, so no CP10 run is expected
```

Reproduce the diff (compare by **name**, both sides on the same base):

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

## 8. Regression boundary

- Touched: `tests/test_ais_w2_living_gate_grove_handoff.py`, and new documentation under
  `docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-living-gate-06/`.
- Not touched: `web/public_prism/**` (CP10-fenced), `api/**`, `knowledge/**`, `weaver/**`,
  authority/identity/governance code, `.gitleaks.toml`, the CP10 policy module.
- The six sibling `SH-08` / product-decision nodes classified in the ledger are **not**
  repaired here — they are out of this workstream's scope.

## 9. Remaining uncertainty

- `vite build` remains environment-blocked; the repairs are inspection-verified against the
  live sources, which is the convention this repository already uses for frontend contracts.
- The clone is **shallow** (`.git/shallow`), so ancestry beyond the fetched depth is not
  inspectable locally. All claims above rest on `df7a99a` and the fetched window.
- `test_agent_loop_does_not_mutate_repository` (`tests/test_weaver_provider_non_mutation.py`)
  is a K2-namespace WIP file from the prior branch's working tree, not part of this PR; it
  fails on `data/*.db-wal` / `-shm` sidecar files. Recorded, not carried.
