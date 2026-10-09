# WORKSTREAM STATE — gate-hygiene / current-tip integration verification 01

Owner: OpenHands (Engineering Runtime) · Authority: Human Sovereign
Base: `a47ea92817436675c15d472ca80f39d7295e880a`
Branch: `gate-hygiene/current-tip-integration-verification-01`

## State

- **Baseline reproduced** at `a47ea928`: 16 failing/error nodes —
  outcomes `bfcfe592…`, ids `ed5e4714…` (identical to PR #375's record).
- **Composed tree reproduced** (#354 + #356 + #357 + #363 + #365 + #347):
  **2** remaining nodes, both sovereign-reserved — outcomes `f607dffd…`,
  ids `48e2b758…` (`-14`, 0 new). Architecture **11 passed**; CP10 judge **PASS**.
- **Merge-order conflict inventory (net-new):** every `CONFLICTING` cluster PR
  (#354/#356/#357/#363) conflicts on **`AGENTS.md` only**; #365/#347/#366/#368 are
  clean. **No two cluster PRs share a non-`AGENTS.md` path.** Merge order is
  unconstrained by code conflict; the only ordering obligation is the
  insertion-only `AGENTS.md` resolution.
- **Gate-2:** main→deployment resolves; deployment build **BLOCKED** (SSO);
  marker-oracle soundness defect owned by open **#366** yet unmerged on `main`.
  #366's `frontend_of()` reads the app identity from the deployment **label**
  (fail-closed); root `vercel.json` at `a47ea928` builds `web/console`, so the
  oracle correctly reports `NOT OBSERVED (artifact is 'console')`.

## Next bounded task (derived from live evidence)

1. Sovereign review/merge of the product-repair cluster — `#354`, `#356`
   (authority surface), `#357`, `#363`, `#365`, `#347`. This record independently
   reproduces the composed-green evidence and adds the conflict inventory the
   merge order needs.
2. `#366` merge to make the Gate-2 marker oracle sound (separate PR; stacked
   `#368`/`#370` are its same-instrument companions).
3. `#361` (fixture reconciliation, disjoint) carries the correct 16-node fixture;
   sovereign review independent of the product cluster.
4. CE-01 (`weaver.autonomy` module/package collision) and F-01 (living-gate
   proxy) remain **sovereign-reserved**; do not repair inside an unrelated
   workstream.

## Forbidden this pass

- No merge, no push to `main`, no force-push.
- No change to `api/lab_routes.py`, workflows, boundary policy, or identity.
- No fixing of CE-01 / F-01.
- No rewrite of an existing `AGENTS.md` oracle line (append corrections only).
