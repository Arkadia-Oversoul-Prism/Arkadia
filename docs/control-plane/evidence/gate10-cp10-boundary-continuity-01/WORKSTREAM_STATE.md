# GATE-10 / CP10 — Workstream State (heartbeat continuity)

> Persisted in-repo so the next heartbeat reconstructs from evidence, not memory.
> Reconstruct this file against live `origin/main` before trusting any line of it.

## Live state at this pass

| field | value |
|---|---|
| BASE_MAIN | `8843fd589f62eebea7815367e2e37f2648ca758e` |
| active gate | **GATE-10 — Governed Execution** (CP10 mutation boundary / M02A CI gate integrity) |
| active PR | this PR — `gate10/cp10-boundary-continuity-01` |
| just merged | **#120** `gate10/cp10-delegated-boundary-judge` → `8843fd5` (sovereign merge) |
| also merged this cycle | #117 trigger-parity, #118 allowlist-opportunity-radar, #119 ledger-h1-dedup |
| failure fingerprint | `sha256:10619a7231ee50653ad33235b0c405fb38023d192bc23f999f15b494ad3753df` (carried forward; no executable change since) |
| contract-recorded baseline | `main` @ `6038989`: 804 passed / 54 failed / 12 skipped / 2 collection errors — **anchored behind current main; compare fingerprints, not counts** |
| re-measured baseline (PR #120 pass) | `main` @ `02fe88c`: 959 / 54 / 12 · branch: 962 / 54 / 12; +3 passed = exactly the three new M02A tests |
| architecture + M02A gate tests | **60 passed** |
| `api/main.py` | 2519 lines, budget 2600 — untouched, `py_compile` OK |
| frontend build | environment-blocked (no npm registry access) |
| K5 · Static Ingestion | **CLOSED** — merged as PR #109 |
| bootstrap docs (`01_STATE`, `03_SCOPE`) | **STALE** — still describe K5 as pending. Not authoritative; never act on them over live repo state |

## Boundary state (post-#120) — do not regress

- `scripts/cp10_mutation_boundary_policy.py` holds the **only** copy of the allowlist (`LEGIT`).
- The workflow pipes `git diff --name-only` into `python scripts/cp10_mutation_boundary_policy.py --judge`.
- The inline `legit=` regex is gone and `tests/test_m02a_ci_gate_integrity.py` asserts its absence.
  Do **not** reintroduce a shell-side copy — that was the drift defect.
- The gate's teeth remain the `forbid` stage (`SolSpireExperienceV2/V3.tsx`) and unknown-root
  rejection. Do not tighten the boundary by removing surfaces the repo genuinely tracks.

## Next bounded task (do not start inside this PR)

The CP10 boundary is now internally consistent and the documentation follows it. The remaining
open work is **baseline test debt**, which the contract classifies as its own bounded workstream:

54 failing nodes, 51 already classified by PR #106
(`docs/control-plane/evidence/` test-debt classification record). Two candidate first slices,
classification-before-repair:

1. `test_weaver_sci_boundary_01` / `test_weaver_sci_contract_01` — assert a NovaNet/Nexus alias
   the hub unification moved. Likely stale assertions; classify before repairing.
2. `test_prism_pass_c_surface_ownership` (6 nodes) — surface-ownership assertions over `.tsx`
   sources; classify as stale assertion vs real defect.

Each slice gets its own branch and PR. Never fold repair into a GATE-10 branch.

## Do not

- Do not merge; the sovereign merges.
- Do not re-open the CP10 allowlist inventory.
- Do not repair baseline debt inside a GATE-10 architectural pass.
- Do not treat `.bootstrap/01_STATE.md` as current — it is stale.
