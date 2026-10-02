# WORKSTREAM STATE — gate-hygiene · CE-02 stale-claim reconciliation

**Status:** IMPLEMENTED → READY_FOR_SOVEREIGN_MERGE
**Branch:** `gate-hygiene/ce02-stale-claim-reconciliation-01`
**Base:** `main` @ `0c8a9f6276354fc2eb8c9a3da805d0878946abc7`

## Current state

Three stale narrative claims in `AGENTS.md` corrected against live evidence:

1. `vite build` — "environment-blocked" → **runnable** (3441 modules, exit 0).
2. SG-04 `ActivityRuntime` — "absent / not yet fixed" → **repaired in source** (PR #174,
   `adf3df29`; 12 passed; marker present in build).
3. "two collection errors" → **one** (`test_autonomy.py` only; `test_render_codex.py` absent).
4. **Pass 2 (this correction):** four further claims re-derived and corrected — the SG-04
   repair carrier was mis-attributed to PR #185 (test-only) when the source repair is PR #174;
   the reproducibility command omitted `--continue-on-collection-errors` (a bare `pytest tests/`
   interrupts at the collection error and under-reports); `dist/` is **untracked**, not
   "tracked but stale"; and the intermediate SG-04 counts are flagged as reconstructed, not
   re-executed.

## Method (load-bearing)

The corrections are **insertions-only over oracle `6c43218a48a4`** — `oracle_alterations == []`.
The "2 collection errors" sentence sits on an *oracle* line, so it is corrected by an appended
dated insertion, not a rewrite; the other two claims are post-oracle and edited directly.
An in-place rewrite of the oracle line raises `alterations=1` → `decidable=False` → audit exit 2
and moves the fingerprint to `f1c7c0c3…` / 23 nodes. See `EVIDENCE.md` §7a. The invariant is
recorded in `AGENTS.md` so it is not re-derived next pass.

## Evidence

- `EVIDENCE.md` (this directory).
- Fingerprint unchanged: `a59453b8…` / `9a35c812…`, 21 nodes.
- `scripts/agents_md_encoding_audit.py`: `alterations=0`, `oracle_reproduced=True`, exit 1.
- `tests/architecture` 11/11; `py_compile api/main.py` clean; `AGENTS.md` mojibake 0.
- `test_agents_md_repair_fingerprint.py` + `test_m02a_ci_gate_integrity.py` +
  `test_engineering_lab.py` → 59 passed.

## Blockers

None for this pass. Final head `2c38647` (base `main` `0c8a9f6`), 3 changed paths, docs-only.
Live on the pushed head: both check-runs green (`Vercel Preview Comments`,
`Full-history secret scan`); commit status `Vercel – console` **failure**,
`Vercel – arkadia-prism` **success**. The one remaining red context is also red on `main`
`0c8a9f6`, so it is pre-existing `main` debt and not attributable to this docs-only PR —
`mergeable_state: unstable` reflects that, not a conflict (`mergeable: true`). Fingerprint
re-measured on the pushed tree: `a59453b8…`, 21 nodes — unchanged. See `EVIDENCE.md` §9, §11,
§11a.

## Not in scope / not re-litigated

- **CE-01** `weaver/autonomy` module-vs-package collision — sovereign decision, left red.
- **Gate-2** production parity — deployment identity + runtime observation, provider-auth
  blocked; untouched.
- 20 pre-existing `main` failures — baseline debt, fingerprint-unchanged.

## Next bounded task

None promoted. The three corrections close the recorded handoff from PR #149 and the CE-01
disposition. The remaining open item on this boundary is **Gate-2 production observation**,
which is `BLOCKED` on provider auth and cannot be advanced by repository work. Do not
re-litigate CE-01; do not re-assert the corrected claims from stale prose.

## Authority

READY_FOR_SOVEREIGN_MERGE. Human-only merge. No self-merge, no push to `main`.
