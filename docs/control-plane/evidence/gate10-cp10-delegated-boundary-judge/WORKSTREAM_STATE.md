# GATE-10 / CP10 — Workstream State (heartbeat continuity)

> Persisted in-repo so the next heartbeat reconstructs from evidence, not memory.

## Live state at this pass

| field | value |
|---|---|
| BASE_MAIN | `02fe88c812b573313553bd32c6037484fa97c17f` |
| active gate | **GATE-10 — Governed Execution** (CP10 mutation boundary / M02A CI gate integrity) |
| active PR | **#120** `gate10/cp10-delegated-boundary-judge` (this PR) |
| related, not overlapping | **#118** `gate10/cp10-allowlist-opportunity-radar` — separate workstream; no shared file |
| last recorded baseline | `main` @ `6038989`: 804 passed / 54 failed / 12 skipped / 2 collection errors |
| re-measured baseline | `main` @ `02fe88c`: **959 / 54 / 12** (two known collection-error modules excluded) |
| failure fingerprint (both trees) | `sha256:10619a7231ee50653ad33235b0c405fb38023d192bc23f999f15b494ad3753df` |
| architecture fitness | passing (11/11 historically; 60 passed when run alongside the M02A gate test) |
| `api/main.py` | 2519 lines, budget 2600 — untouched |
| frontend build | environment-blocked (no npm registry access) |
| K5 · Static Ingestion | **CLOSED** — merged as PR #109 |
| bootstrap docs (`01_STATE`, `03_SCOPE`) | **STALE** — still describe K5 as pending. Not authoritative; do not act on them over live repo state. |

## Next bounded task (do not start inside this PR)

Triage the 54 baseline failures as a **standalone test-hygiene workstream** (the pattern
already established in `gate-hygiene-baseline-test-debt-classification-01`, PR #106). Two
candidate bounded repairs, each independently scoped:

1. `test_weaver_sci_boundary_01` / `test_weaver_sci_contract_01` — `test_nexus_novanet_alias_intact`
   and `test_solspire_is_workspace_not_second_sci` assert an alias the NovaNet/Nexus hub
   unification moved; likely a stale assertion, but must be classified before repair.
2. `test_prism_pass_c_surface_ownership` (6 nodes) — surface-ownership assertions against
   `.tsx` sources; classify as stale assertion vs real defect.

Classification first. Repair only in its own branch/PR, never folded into GATE-10.

## Do not

- Do not re-open the CP10 allowlist inventory in #120.
- Do not merge; the sovereign merges.
- Do not treat `.bootstrap/01_STATE.md` as current — it is stale.
