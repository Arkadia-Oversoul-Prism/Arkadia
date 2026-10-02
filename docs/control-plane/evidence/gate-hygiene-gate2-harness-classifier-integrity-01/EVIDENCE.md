# EVIDENCE — Gate-2 observation harness: classifier integrity

Workstream: `gate-hygiene/gate2-harness-classifier-integrity-01`
Gate: GATE-02 (production parity observation)
Base main: `2b167e4f41ca87699db33a28c76f03550db66847`
Branch head: _filled at PR open_

Status: **IMPLEMENTED** (docs + harness + tests; no runtime acceptance claimed)

---

## 1. Objective

Repair three defects in `scripts/gate2_production_observation.py` — the read-only
harness that re-derives the Gate-2 chain
`main SHA → deployment SHA → production response → UI/runtime observation`.

The harness is the instrument every Gate-2 claim rests on. An instrument that
reports the wrong classification makes every downstream claim unreliable, so its
classifier is a legitimate Gate-2 target rather than scope expansion.

Bounded to: one script, one new test file, evidence docs. No product code, no
`api/main.py`, no workflow, no merge.

---

## 2. Defects, each measured

### 2.1 The Production filter admitted nothing

```python
prod = [d for d in deps if d.get("environment") == "Production"]
```

The query parameter is `?environment=Production` but the GitHub deployments API
treats it case-insensitively, while the **record field is capitalized**. A
case-sensitive comparison against the lowercase literal therefore admitted zero
records from a response that did contain them.

Measured negative control on a live-shaped payload:

```
OLD filter admitted: 0 -> identity: UNKNOWN
NEW filter admitted: 1 -> identity: STALE
```

The harness could never prove the deployment link, so it printed `UNKNOWN`
unconditionally and the "link exists and is queryable" fact recorded in
`AGENTS.md` was unverifiable through the harness.

### 2.2 A stale deploy was reported as an unproven link

```python
"VERIFIED" if prod and prod[0].get("sha") == main_sha else "UNKNOWN"
```

A newest deployment that exists, is observable, and names a *different* SHA is
**STALE** — a positive observation that production does not carry main. Folding
that into `UNKNOWN` ("evidence unavailable") discarded a real fact and made the
boundary look less knowable than it is. `STALE` is already a declared evidence
state in the contract; it was simply never produced.

### 2.3 The lineage predicate had two copies

The printed closure used one expression; the `build <-> source lineage` boundary
used a second, re-typed copy of the same conjunction. Two copies of a predicate
can disagree, and here the boundary was the copy that nothing tested. Both are
now produced by `lineage_closed()` / `classify_source_lineage()`.

A fourth, latent hazard was closed with them: a candidate SHA absent from the
local object store was passed to `git merge-base --is-ancestor`, whose non-zero
exit was indistinguishable from "genuinely diverged". Unchecked candidates are
now recorded as `None` (unproven) and cannot close the argument.

---

## 3. What the corrected harness observes (live, 2026-10-02)

```
main SHA                : 2b167e4f41ca87699db33a28c76f03550db66847
newest Production deploy: 57e67c534ff6  id=6802423130  2026-10-02T06:06:28Z
  deploy SHA == main    : False  (deploy predates main -> STALE)

BOUNDARY CLASSIFICATION
  current main resolved                      VERIFIED
  main -> deployment identity                STALE
  deployment build output observed           BLOCKED
  alias reachable                            VERIFIED
  alias -> deployment SHA binding            UNKNOWN
  build <-> source lineage                   UNKNOWN
  browser-rendered UI correctness            UNKNOWN
  production acceptance                      NOT CLAIMED (human authority)
```

Two changes of substance, both honest:

1. `main -> deployment identity` moved `UNKNOWN → STALE`. The link is now
   *proven to be stale* rather than *unproven*.
2. `build <-> source lineage` moved `VERIFIED → UNKNOWN`. This is a **weakening**,
   and it is the important result. The last commit touching a frontend build
   input is `2b167e4f41ca` — current main, today 13:01. The 12 candidate
   Production deployments are therefore **not** its descendants, so they do not
   compile identical frontend source and the artifact *can* discriminate between
   them. The previously recorded closure argument no longer holds at this main.

The harness previously printed the closure verdict from a predicate that could
not express this, so the weakening was invisible. It is now reported.

### SG-04 marker

```
activity-runtime-draft.v1:   in source: True   in deployed artifact: 1
SG-04 REGRESSION: False
```

Corroborates the CE-02 correction (#206): the SG-04 `ActivityRuntime` mount is
present in the deployed artifact, so the `AGENTS.md` claim that it is "absent
from the production bundle" is stale. Recorded here as independent measurement,
not as a claim about #206.

---

## 4. Tests

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_gate2_production_observation.py -q` | **16 passed** (new file) |
| `python -m pytest tests/test_gate2_{production,backend,browser}_observation.py -q` | 48 passed (16 new + 32 existing) |
| `python -m pytest tests/architecture -q` | 11 passed |
| `python -m py_compile scripts/gate2_production_observation.py` | OK |

New file `tests/test_gate2_production_observation.py` pins, per defect: the
capitalized-environment admission and the lowercase-literal rejection; `STALE`
vs `UNKNOWN`; newest-deploy precedence; unchecked-candidate refusal to close;
stale-marker-list refusal to verify; and a source-level assertion that the
boundaries are produced by the tested classifiers rather than a second copy.

Negative control (§2.1) is executed and shown above; it fails against the old
filter and passes against the new one.

---

## 5. Baseline comparison

Architecture fitness unchanged at **11 passed**.

Full-suite fingerprint, measured on this environment, base `2b167e4f41ca` vs.
this branch, same command (`pytest tests/ -q --continue-on-collection-errors
-p no:randomly`):

| | base | branch |
| --- | --- | --- |
| failed | 58 | 58 |
| passed | 792 | 808 |
| skipped | 17 | 17 |
| errors | 44 | 44 |

The sorted `FAILED`/`ERROR` **node set is byte-identical** (102 nodes,
`diff` empty). The +16 passed are exactly the new test file. No baseline failure
fingerprint changed, so no pre-existing failure is attributable to this change.

Note on the error count: 44 collection errors here are a **dependency delta in
this sandbox** (`fastapi`, `requests` absent), not repository state. They are
present identically on both sides, which is what makes the comparison valid; the
contract's `804 passed / 54 failed / 2 collection errors` fingerprint is not
reproducible in this environment and is not claimed.

---

## 6. Authority boundary

- Docs + harness + tests only. No merge, no push to `main`, no force-push.
- `AGENTS.md` is **deliberately untouched**: three open PRs (#143, #147, #150)
  already conflict on it and #206 modifies it. A fifth writer would widen a known
  conflict cluster for no gain; the finding is recorded here instead.
- Production acceptance remains `NOT CLAIMED` — human authority.
- The deployment build output remains `BLOCKED` on Vercel Deployment Protection.
  This pass does **not** close Gate 2 and does not claim to.
