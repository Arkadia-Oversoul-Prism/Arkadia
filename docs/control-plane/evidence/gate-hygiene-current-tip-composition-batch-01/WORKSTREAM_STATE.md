# WORKSTREAM STATE — gate-hygiene / current-tip composition batch 01

Owner: OpenHands (Engineering Runtime) · Authority: Human Sovereign
Base: `a47ea92817436675c15d472ca80f39d7295e880a`
Branch: `gate-hygiene/current-tip-composition-batch-01`

## State

- **Measured:** the uncovered-debt PR cluster (#354 + #356 + #357 + #363 +
  #365 + #347) composes on the *current* tip to **2** remaining nodes, both
  sovereign-reserved. Baseline **16** → composed **2** (`-14`, 0 new).
- **Gate-2:** main→deployment **VERIFIED** (`a47ea928`), deployment build
  **BLOCKED** (SSO), marker oracle soundness defect owned by open **#366**.
- **Hazard recorded:** chained `git apply --3way` on PRs sharing `AGENTS.md`
  raises `UU` and silently drops the remaining files; exclude `AGENTS.md` and
  verify each PR's files before attributing a result.

## Next bounded task (derived from live evidence)

1. Sovereign review/merge of the debt cluster — `#354`, `#356` (authority
   surface), `#357`, `#363`, `#365`, `#347`. This record supplies the composed
   green evidence the merge order needs.
2. `#366` merge to make the Gate-2 marker oracle sound (separate PR).
3. CE-01 (`weaver.autonomy` module/package collision) and F-01 (living-gate
   `sessionStorage` proxy) remain **sovereign-reserved**; do not repair inside
   an unrelated workstream.

## Forbidden this pass

- No merge, no push to `main`, no force-push.
- No change to `api/lab_routes.py`, workflows, boundary policy, or identity.
- No fixing of CE-01 / F-01.
