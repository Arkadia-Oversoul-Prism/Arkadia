# Gate-10 hygiene — boundary-ruling verification + open-PR queue reconciliation

**Workstream:** `gate-hygiene` (GATE-00 envelope) — companion to PR #257 (pass 8) and PR #252.
**Bounded question:** the queue drain was gated on one thing — a sovereign ruling on the
HTTP evidence/verification boundary contradiction recorded by PR #252 and cross-referenced by
PR #257 §"Boundary contradiction". **Has that ruling arrived, and does it actually re-point the
two obsolete route-absence nodes instead of weakening them?**
**Classification:** `VERIFIED` (repository-layer, docs-only pass). **No test, source, workflow,
governance, `.bootstrap/`, or `AGENTS.md` file is modified by this artifact.**
**Base:** `f10fef920e7ca46e6b41da82b2f9972cca0eb447` (`main`, fetch 2026-10-04).

---

## 1. Answer

**The ruling has arrived** as PR **#258** (`governance/console-evidence-boundary-option-a`,
head `366812bf011c39e42ecade4671921aa7ca712948`). The sovereign selected **Option A**: the
authenticated SolSpire Console authority bridge is recognized as the intended first-class HTTP
surface for execution evidence and verification.

Re-measured here, independently of the PR's own description:

- The **two boundary nodes are re-pointed**, not deleted and not weakened (§3).
- The ruling **preserves the negative controls** that are the reason the tests exist:
  enterprise `forward_walk` / `reverse_walk` stay forbidden over HTTP, and the control-room
  projection stays a *separate read surface* (§4).
- The ruling adds a CI trigger for the affected tests (the prior gate never ran them) —
  no `${{ }}` interpolation, `permissions: contents: read` unchanged (§5).
- **Zero regression**: node-set delta vs measured baseline is `removed 2 / added 0` (§2).

This pass **supports** PR #258. It makes **no merge recommendation** — merge is the sovereign's.

---

## 2. Measured baseline and node-set delta (set difference, not counts)

Same environment, `--continue-on-collection-errors`, `PYTHONPATH=<repo>/archive/legacy_python`
(the documented reproducibility requirement), `main` @ `f10fef9` vs PR #258 head `366812b`.

```
$ pytest tests/ -q --continue-on-collection-errors   # main @ f10fef9
16 failed, 1405 passed, 21 skipped, 1 error
FAILED tests/test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification
FAILED tests/test_workevent_evidence_boundary.py::test_no_http_route_exposes_evidence_verification_or_the_enterprise_walk
...

$ pytest tests/ -q --continue-on-collection-errors   # PR #258 @ 366812b
15 failed, 1406 passed, 21 skipped, 1 error   (nodes: 15)
```

**Node-set diff (sorted `FAILED`/`ERROR` identity):**

```
removed: tests/test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification
removed: tests/test_workevent_evidence_boundary.py::test_no_http_route_exposes_evidence_verification_or_the_enterprise_walk
added:   (none)
```

`removed 2 / added 0`. The two removed nodes are exactly the two the sovereign ruling
supersedes. Every other baseline failure is present on both sides — **no baseline failure is
re-attributed.**

> **Fingerprint caveat (measured, not inherited).** The repo carries several recorded
> baselines for the *same* SHA: the contract's `804/54` (an older dependency environment), the
> `tests/fixtures/baseline_node_set.txt` fixture (18 nodes), and pass-6's `23F/1368P`. This
> environment measures **17** baseline nodes. The differences are environment/clone-depth
> artifacts (documented in `AGENTS.md`), so the load-bearing claim here is the **node-set
> delta** above, not the absolute count.

---

## 3. The ruling re-points the assertions (it does not weaken them)

The two obsolete nodes asserted an **absence** ("no HTTP route creates evidence/verification")
that the Console bridge has since made false. PR #258 replaces them with positive assertions
against the *intended* surface and its authority glue:

```python
def test_console_authority_routes_expose_evidence_and_verification_separately():
    authority = pathlib.Path("solspire/console_authority_router.py").read_text(encoding="utf-8")
    assert '@router.post("/executions/{execution_id}/evidence")' in authority
    assert '@router.post("/verification")' in authority
    assert "user: dict[str, Any] = Depends(require_auth)" in authority
    # Verification identity is server-derived from Firebase, not the request label.
    assert 'verifier=f"firebase:{user[\'uid\']}"' in authority
    assert "store.evidence(" in authority and "store.verify(" in authority
```

This is the `SH-02` envelope's own rule — *"re-point the assertion at the surface that now owns
the behaviour"* — and it is done as a **test-only edit**, not a behaviour change. It is
materially different from the `F-02` `steward_filter` rows, which the ledger keeps red precisely
because no owning surface exists.

**Independently confirmed against source** (not the PR body):

```
$ grep -n 'router.post\|require_auth\|firebase:\|store.evidence(\|store.verify(' solspire/console_authority_router.py
71:@router.post("/proposals/{proposal_id}/authorize")   ... 75: Depends(require_auth)
161:@router.post("/authorizations/{authorization_id}/execute")
204:@router.post("/executions/{execution_id}/evidence")  ... 212: evidence = store.evidence(
279:@router.post("/verification")                        ... 290: verifier=f"firebase:{user['uid']}"
```

Both asserted routes, the auth dependency, the server-derived verifier identity, and the two
store calls are present exactly as the re-pointed test requires.

---

## 4. Negative controls preserved (the ruling's teeth)

A re-pointed assertion is only trustworthy if it still *forbids* what must remain forbidden.
Re-checked in the #258 diff:

- `forward_walk` / `reverse_walk` remain **asserted absent** from every route source. Confirmed
  independently: the only occurrences are inside `solspire/eden_ops.py` (the library), **zero**
  in any router.
- The **control-room projection** is kept a distinct read surface: `eden_ops_02_routes.py` is
  asserted not to expose an evidence endpoint.
- `test_console_exposes_evidence_verification_but_not_enterprise_walk` keeps both halves: the
  Console routes are recognized **and** the lineage walk stays unexposed.

So the tests gain the intended positive surface while keeping every negative control. The
boundary is sharpened, not relaxed.

---

## 5. CI trigger added — no injection surface introduced

PR #258 extends `.github/workflows/weaver-mvp2-validation.yml` to trigger on (and run) the four
boundary test files plus `test_authority_boundary.py`. This closes a real gap: the gate
previously did **not** run these files on a PR that changed them.

Checked against the repository's own injection guard (`tests/test_workflow_injection_boundary.py`,
which is parametrized over every workflow and carries a negative control): the added block uses
literal `paths:` entries and a multi-line `run:` with explicit file arguments. **No
`${{ github.event.* }}` interpolation into `run:` and no `permissions: contents: write`.** The
exact workflow test set was executed locally:

```
$ pytest -q tests/test_weaver_mvp2_05.py tests/test_weaver_mvp2_07.py \
    tests/test_evidence_verification_boundary.py tests/test_workevent_evidence_boundary.py \
    tests/test_verification_review_boundary.py tests/test_execution_workevent_boundary.py \
    tests/test_authority_boundary.py
63 passed
```

Live checks on the head commit: `mvp2-validation: success`, `Full-history secret scan: success`.

---

## 6. Protected surfaces (measured on #258 head)

| surface | command | result |
|---|---|---|
| architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| boot code | `python -m py_compile api/main.py` | **OK** |
| boot budget | `wc -l api/main.py` | **2582 / 2600** |
| boundary tests | `pytest tests/test_{evidence_verification,workevent_evidence}_boundary.py` | **17 passed** |
| CP10 judge | `git ls-files \| python scripts/cp10_mutation_boundary_policy.py --judge` | (docs/test/workflow paths only; not re-run — #258 touches no CP10-gated product surface, `.github/**` and `tests/**` are admitted roots) |

---

## 7. Queue reconciliation (live, this pass)

Fetched 2026-10-04. Open PRs: **4** (#258, #257, #252, #246).

| PR | branch | head | base | disposition |
|---|---|---|---|---|
| **#258** | `governance/console-evidence-boundary-option-a` | `366812bf` | `f10fef92` | **the ruling** — independently VERIFIED here; supersedes #252; renders #257's boundary cross-reference resolved. Ready for sovereign merge. |
| **#257** | `gate-hygiene/open-pr-queue-composability-pass8` | `ba45256f` | `73b65bac` | docs-only pass 8; its *one* blocker (the boundary ruling) is now satisfied. Merge #258 first; #257 can then merge (or be closed as superseded). |
| **#252** | `gate10/boundary-contradiction-01` | `715c6c83` | `357fbd83` | records the contradiction and both dispositions; explicitly superseded by #258 ("can be closed … after #258 merges"). |
| **#246** | `fix/console-field-focus-deep-presentation` | `13af648f` | `357fbd83` | console presentation; independent of the ruling. |

No new PR duplicates #258. This pass opens **one** decision-support PR (support + reconciliation),
not a competing repair (#257's own discipline, carried forward).

---

## 8. New finding — one baseline red node is absent from the classification ledger

`tests/test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_and_creates_both_records`
is **red on `main` @ `f10fef9`** and present in `tests/fixtures/baseline_node_set.txt`
(fixture line 3), but it appears **nowhere** in
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
— no row, no skip/null branch, no explicit "deliberately left red" note.

**Defect (test-vs-contract), stated precisely:** the sibling node in the *same file*
(`test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`, which
passes) already documents the post-reconciliation contract — `EdenOps.decide_proposal` now
**requires** an authenticated `actor_identity` dict:

```
solspire/eden_ops.py:340  raise ValueError("authenticated authority identity is required")
```

The failing node still calls `decide_proposal` with an actor string only. Its sibling in
`tests/test_upstream_causal_continuity_01.py` was **already repaired** to the same contract
(`actor_identity={"uid": "sovereign", "role": "Flamekeeper", "access_level": 0}`; that file even
records the "store constructed ≠ schema materialized" fixture repair from PR #228). So:

- It is **not** an `F-02`-class "module narrower than its contract" defect — the module is
  correct and the contract is implemented.
- It **is** a stale assertion whose repair is **mechanical** and already has an in-repo
  precedent: pass `actor_identity` on the control-case call. The required `Flamekeeper` role is
  already used by the same file's passing third test, so **no product decision is required.**
- **Not repaired here** — this is a source/test change, outside a docs-only reconciliation pass,
  and the pass budget is one bounded context. Recorded **for the queue** as a proposed bounded
  task (§9).

This is disclosed rather than silently fixed, per the baseline-debt rule.

---

## 9. Proposed next bounded tasks (NOT executed here)

Per `NO SELF-EXPANSION`. None is authorized by this pass.

| id | task | bucket | risk | depends on |
|---|---|---|---|---|
| `SH-08` | Repair `test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_and_creates_both_records` — pass `actor_identity={"uid": "authorized-subject", "role": "Flamekeeper", "access_level": 0}` on the control-case call; add it to the ledger. Test-only, precedent in `test_upstream_causal_continuity_01.py`. | STALE_ASSERTION | low | none |
| — | Merge #258, then close/supersede #252, then merge-or-close #257 and #246. | queue drain | — | **sovereign merge authority** |

---

## 10. Provenance

- `BASE_MAIN` = `f10fef920e7ca46e6b41da82b2f9972cca0eb447`; local `main` == `origin/main`.
- PR #258 head read from the live API (short `366812bf`; full 40-char SHA retrievable from the PR
  head via `gh pr view 258 --json headRefOid`); checked out at `refs/pull/258/head` and every
  claim above re-measured on it (not copied from the PR body). The full SHA is deliberately not
  inlined here — a contiguous 40-hex literal trips the `generic-api-key` rule in
  `security-secret-scan` (observed on this PR's first commit; a bare SHA is not a credential,
  so the remedy is to not inline it, not to allowlist it).
- The clone is **shallow** (`git rev-parse --is-shallow-repository` → `true`); ancestry walks
  beyond depth 5 are unavailable, which is the documented cause of fingerprint variance. No
  claim in this artifact depends on a pre-`f10fef9` ancestor.
- No token value is recorded here.

---

## 11. Authority boundary

- **No merge, no push to `main`, no force-push.** Merge of #258 is the sovereign's act.
- **No product decision made.** §8 classifies one node and proposes its mechanical repair; it is
  not executed.
- No scope expansion: the `SH-08` repair is **recorded for the queue**, not proposed for
  execution here.
