# WORKSTREAM STATE — `gate01/relational-lineage-canonical-provenance`

## Status

IMPLEMENTED · push complete · **PR not yet opened** (see blocker)

## Live inventory at observation time

- `main` = `3e1cd007c93fcfe5a73fb3dc81fd65644b06306f`
- Open PRs: **1** — #174 `gate02/capability-chamber-union-repair-02` @ `4c1bc70d`,
  `mergeable_state=clean`, checks: secret scan success, Vercel preview success, `validate` success
- The stacked chain described by the previous pass (#169–#173) is **already merged**; it is no
  longer an open queue. #166 is closed/merged as `47e4128`.

## Blocker — notification path, not write path

`gh` CLI rejects the ambient `GH_TOKEN` (`The token in GH_TOKEN is invalid.`). The token
embedded in `origin` **is** valid — `GET /repos/.../Arkadia` → HTTP 200, and `git push` to the
branch succeeded.

Per the contract this is **not** a hard stop: the credential blocking PR creation is
recoverable from the ambient remote, so the work is preserved on a pushed branch. Opening the
PR is the only step gated. Escalated rather than worked around silently.

## Files

- `knowledge/graph.py` — `_attach_provenance` reads through `capture.provenance_for_note`;
  `traverse()` wraps nodes.
- `tests/test_relational_lineage.py` — assertions rebound to the nested canonical shape.
- `docs/control-plane/evidence/gate01-relational-lineage-canonical-provenance-01/` — this evidence.

## Baseline fingerprint (re-measured this pass, by node identity)

| Tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| `main` `3e1cd00` | 22 | 1123 | 17 | 1 |
| branch | 20 | 1125 | 17 | 1 |
| branch + #174 | 17 | 1128 | 17 | 1 |

`main`'s 22 includes **2** `test_relational_lineage` failures that are a **known debt**, not
green-on-main. Zero new failures in any composition.

## Proposed (NOT authorized, NOT executed)

1. **`knowledge/` has no CI gate.** No workflow references `knowledge/` or
   `test_relational_lineage`. Proposed: add a path-filtered pytest workflow covering
   `knowledge/**`. Bounded, small, but a workflow change — needs sovereign authorization.
2. **`test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` is a test-side
   defect** (asserts a literal where the component renders a template). Proposed: its own
   bounded workstream. Not fixed here — scope expansion.
3. **Squash-merge duplicate workstreams.** #170 and #173 both rewrote `knowledge/graph.py`;
   #173's landing silently deleted a green test. Proposed: require a "files changed" review
   before batch-merging same-workstream PRs.

## Deterministic next-action block

- **Current state:** fix implemented, tested, pushed; evidence committed on the branch.
- **Evidence:** the fingerprint table above, reproducible with
  `PYTHONPATH=archive/legacy_python pytest tests/ -q --continue-on-collection-errors -p no:randomly`.
- **Blockers:** PR creation gated on a valid `GH_TOKEN` for `gh`; no code blocker.
- **Authorized action:** none pending — no merge, no push to `main`.
- **Forbidden:** merge, force-push, push to `main`, scope expansion into items 1–3 above.
- **Completion condition:** PR opened against `main` with this evidence attached, marked
  READY_FOR_SOVEREIGN_MERGE. A human merges. Do not merge.
