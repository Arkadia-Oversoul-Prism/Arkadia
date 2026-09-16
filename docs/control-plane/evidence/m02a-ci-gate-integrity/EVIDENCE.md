# M02A — CI Gate Integrity — Evidence

**Move:** M02A  
**Authorization:** Architect explicit (pause M03; CI integrity intervening move)  
**Starting SHA:** 36d971459c47b1b1dafe6f14af27bc7bf3c084bc  
**Branch:** weaver/arkadia-truthfulness/m02a-ci-gate-integrity  

## Baseline

- Workflow: SG-02-FE.2-V (`.github/workflows/sg-02-fe-2-v.yml`)
- Failing runs on main/product: e.g. 35032418455 (M02 merge), multiple solariun nav commits
- Failing step: `CP10 mutation boundary`
- Failure: `Unexpected non-harness paths in tip commit`
- Last known Lab green: phase10 era (~34449093636) when tip commits were harness-only

## Root cause

**Expected policy:** Distinguish legitimate repository mutation from forbidden architectural mutation.  
**Actual policy:** Tip commit allow-list limited to Lab harness paths (`lab/*`, `tests/test_phase*`, limited docs/verification, workflow file only).  
**Determination:** Outdated Lab-phase allow-list applied to all pushes — **workflow policy defect**, not intentional rejection of product architecture.

## Repair

- Replace harness-only allow-list with **legitimate surface** regex (web/api/solspire/kernel/weaver/lab/tests/docs/scripts/…).
- Add **constitutional denylist** for V3 dual shell and active V2 implementation reintroduction.
- Preserve workflow diff scan against `git push/commit` and `gh pr/workflow` merge automation.
- Testable policy module: `scripts/cp10_mutation_boundary_policy.py`.

## Tests

- `tests/test_m02a_ci_gate_integrity.py` — positive product/control-plane/lab; negative unknown path / V3 / active V2; trajectory next = M02A

## Next legal move after acceptance

M03 — NovaNet Public Field (not executed in this move)
