# WORKSTREAM STATE — gate-hygiene/solspire-r1-r3-contract-repin-01

| field | value |
|---|---|
| workstream | gate-hygiene — uncovered test-contract re-pins (SolSpire R1/R3) |
| gate | GATE-07 / GATE-10 hygiene (baseline-debt reduction, no authority change) |
| status | **READY FOR SOVEREIGN MERGE** |
| PR | #357 |
| head | `6590df0e1ba866ef616bd2148b511d006940a736` |
| base main | `f96d5fd27d40110196ec22b114808efc0eb9dc05` |
| checks | **5/5 check-runs success** (`Full-history secret scan`, `bundle-beta-evidence`, `native-arkadia-golden-workflow`, `beta-beta-01-english`, `beta-beta-02-hausa`) |
| commit status | `failure` - Vercel `build-rate-limit` (provider quota). **Pre-existing: identical on `main` `f96d5fd2`.** Not attributable to this change. |
| mergeable | `true` / `clean` |
| changed paths | `tests/test_solspire_r1_governance_convergence.py`, `tests/test_solspire_r3_execution_runtime.py`, `AGENTS.md`, this evidence dir |
| production code | **none** |
| baseline delta | `main` 16F/1770P/22S/1E → branch 13F/1773P/22S/1E; node-set `-3/+0` |

## Next action (deterministic)

**Sovereign:** review and merge PR #357. No agent action is required or permitted before that.

After merge, the next heartbeat should:

1. Reconstruct `main` and confirm the new SHA contains the four changed paths.
2. Re-measure the baseline on the merged tree — the three SolSpire nodes must be absent from the
   `FAILED`/`ERROR` set; expect `13F/1773P/22S/1E` modulo the open-PR carriers below.
3. Pick the next uncovered cluster. Candidate residual debt, all currently unclaimed:
   - 3 × `test_m02a_ci_gate_integrity` (CP10 gate integrity)
   - 3 × `test_steward_filter`
   - `test_ci_gate_trigger_coverage[n-atlas-developer-lab.yml]` — carried by open PR #355
   - 2 × `test_engineering_lab_api` — carried by open PR #356
   - `test_autonomy.py` collection error — **CE-01, sovereign-reserved, do not touch**

## Forbidden in this workstream

- Touching `test_autonomy.py` (CE-01 module-vs-package collision is sovereign-reserved).
- Removing the dead per-step branch at `solspire/execution_runtime.py:243` (source-side decision).
- Widening scope to any cluster already carried by an open PR.
- Any change to production code, authority paths, or mutation paths.

## Completion condition

PR #357 merged by the sovereign, and the post-merge `main` re-measurement shows the three SolSpire
nodes absent with zero added nodes.
