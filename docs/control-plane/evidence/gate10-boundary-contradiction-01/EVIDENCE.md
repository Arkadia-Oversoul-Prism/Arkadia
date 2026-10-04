# GATE-10 · Boundary contradiction — HTTP evidence/verification creation vs. the Gate-03/04 boundary tests

**Status:** CONTRADICTED — evidence record only, no repair in this artifact
**Date:** 2026-10-04
**Measured at:** `357fbd83001924e909979fbaebdedbd991a2aadb` (main, `Merge pull request #244`)
**Branch:** `gate10/boundary-contradiction-01`
**Gate:** GATE-10 (Governed Execution) — the execution/authority boundary
**Authority required:** human sovereign (boundary adjudication; see §6)

## 1. Objective

Resolve the Phase 1 classification of
`tests/test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification`,
recorded in
`docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md` §4.2 as a
**"regex false positive, not a new HTTP mutation path."**

This artifact measures that classification against the live tree. It repairs
nothing: the boundary decision it surfaces is the sovereign's (§6).

## 2. Measurement

Three boundary nodes fail on `main` @ `357fbd8`. They are **not** the same class.

| node | measured cause | class |
|---|---|---|
| `test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification` | `solspire/console_authority_router.py` contains `store.evidence(` / `store.verify(` and declares `@router.post("/executions/{execution_id}/evidence")` + `@router.post("/verification")` | **REAL boundary breach** |
| `test_workevent_evidence_boundary.py::test_no_http_route_exposes_evidence_verification_or_the_enterprise_walk` | same router — its `"evidence"` / `"verif"` route-path assertion is hit by the two routes above | **REAL boundary breach** |
| `test_verification_review_boundary.py::test_no_http_surface_exposes_review_as_a_first_class_record` | substring `review` inside `/projects/{project_id}/patches/preview` | **false positive** (PR #249) |

### 2.1 The failing assertion text (verbatim)

```
>           assert ".evidence(" not in text, f"{src} creates evidence over HTTP"
E           AssertionError: solspire/console_authority_router.py creates evidence over HTTP
tests/test_evidence_verification_boundary.py:213: AssertionError
```

```
>       assert not review_routes, f"review route exists: {review_routes}"
E       AssertionError: review route exists:
  ['solspire/console_router.py: @router.post("/projects/{project_id}/patches/preview")']
tests/test_verification_review_boundary.py:225: AssertionError
```

### 2.2 The source that breaches the boundary

`solspire/console_authority_router.py` (introduced by `c052cee`, mounted by
`69a1c37`, both ancestors of the #234 merge `049abef`):

```
 71: @router.post("/proposals/{proposal_id}/authorize")
161: @router.post("/authorizations/{authorization_id}/execute")
204: @router.post("/executions/{execution_id}/evidence")   <- creates evidence over HTTP
212:     evidence = store.evidence(
228: @router.post("/captures")
269: @router.post("/verification")                          <- creates verification over HTTP
276:     verification = store.verify(
```

Both handlers are `Depends(require_auth)`-gated and actor-bound to the Firebase
uid, so this is **not** an anonymous mutation path. But `require_auth` is an
**authentication** gate, not the **authority** gate: nothing in the handler
requires the `Govern` authority that `POST /proposals/{proposal_id}/authorize`
enforces. An authenticated subject can call `/verification` directly with
`verifier` defaulted to `"human-console"`, fabricating a verification record.

The route is genuinely reachable: `api/main.py:333-334` mounts
`solspire.console_router`, which composes `console_authority_router` at
`solspire/console_router.py:65`.

## 3. The contradiction

`RECONCILED-BOUNDARY-MAP-01.md` (recovered by `ae847dd`, PR #180) is the
governing record of the boundary. It states, as the **measured finding** of the
Boundary Expansion Gate 04 (§5, §6 item 10):

> **Unexposed:** no route creates or lists evidence or verification; both are
> readable only through the control-room projection.

and of Gate 03 (§6 item 9):

> **Unexposed:** no dedicated route exposes evidence or verification as
> first-class records; the enterprise chain is read only as a control-room
> projection.

The `console_authority_router.py` routes are **exactly** the surface those
records assert is absent. The tests are therefore measuring the property they
name; they are not matching an incidental substring.

Two distinct dispositions are available, and **both are sovereign decisions**:

- **(A) The routes are authorized.** PR #234's own body discloses "exposes
  explicit execution-attempt, evidence, and verification endpoints" and a human
  merged it. If the Console's human-edge authority bridge is the intended
  governed surface, then `RECONCILED-BOUNDARY-MAP-01.md` §5/§6 and the two
  boundary tests must be **amended to reflect the new authorized surface** — a
  governance/boundary change, not a test repair.
- **(B) The routes exceed the boundary.** If the Gate-03/04 records remain
  canonical, then `console_authority_router.py`'s `/evidence` and `/verification`
  endpoints are an un-reconciled boundary expansion and must be removed or
  reduced to the projection-only read surface.

**This artifact does not choose.** Either choice changes a governance boundary
the contract reserves to the sovereign, and no evidence record in the repository
currently amends Gate-03/04 to admit these routes (searched: `docs/`, root
markdown, `RECONCILED-*`).

## 4. Regression point (established)

At `049abef^1` (`fbe9b83`, the #233 merge, before #234):

- `solspire/console_authority_router.py` — **absent**;
- `git grep -E '@router\.(post|get)\("/[^"]*(evidence|verif)'` over
  `solspire/*router*.py` and `api/*route*.py` — **none**.

So no HTTP route created evidence or verification before `049abef`, and the
Gate-03/04 assertions held. The breach is introduced by `c052cee`/`69a1c37` in
PR #234. The Phase 1 evidence record's classification of these two nodes as
"false positive" is **contradicted** by this measurement.

The third node (review/preview) **is** a genuine false positive and is repaired
separately by PR #249. The two classes must not be conflated: PR #249's
non-goals already exclude the two evidence/verification nodes, and PR #249's
§2 "the boundary itself is intact" claim holds only for the review boundary —
not for the evidence/verification boundary.

## 5. Baseline fingerprint (recorded, for the next heartbeat)

`main` @ `357fbd8`, `PYTHONPATH=<repo>/archive/legacy_python`,
`pytest tests/ -q --continue-on-collection-errors`:

- result: **28 failed / ~1368 passed / 1 error** (passed count is order-dependent
  via `test_agent_loop_does_not_mutate_repository`; use the node set)
- failing/error node set: **29 nodes**
- outcomes fingerprint: `5745314330ce11df9ee8c06986c506ac71a5883e4c2ff1f0a4902400e971bef6`
- ids fingerprint: `0d2ff1b182cf0146007ee231fb427fb5dea60be20810f7877ac182215701683b`
- `tests/architecture` — **11 passed**
- `python -m py_compile api/main.py` — OK (2582 lines, budget 2600)

PR #250's `provider-routing` failure is the pre-existing `tests/test_autonomy.py`
collection `ImportError` (`weaver.autonomy` module-vs-package collision,
sovereign-reserved) reached by that workflow's "Broader test suite" step
(`python -m pytest tests/ -q`). It is baseline debt, not a regression from #250.

## 6. Authority boundary and next action

- **This artifact records a contradiction. It does not repair it.** Amending a
  boundary test or removing an authority route both require the sovereign's
  adjudication (§3).
- **PR #249 must not merge on the strength of the Phase 1 classification** while
  §3 is open: its EVIDENCE.md §2 leans on the same "boundary is intact"
  reasoning that is false for the sibling nodes.
- Required sovereign decision: **(A) amend the boundary records and tests to admit
  the authorized Console authority surface**, or **(B) treat the routes as an
  un-reconciled expansion and remove/reduce them**. Re-entry condition: a recorded
  sovereign ruling in this directory naming the chosen disposition.

Read-only measurement plus this classification record. No test repaired, no route
changed, no merge, no push to `main`.
