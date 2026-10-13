# Workstream 4 — Engineering Lab operational authority reading

**Workstream:** 4 (Arkana/Oracle, Weaver, Engineering Lab)
**Branch:** `feat/prism-l4-lab-governance-readings-01`
**PR:** (draft, opened from this branch)
**Base (`origin/main` at read time):** `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`
**Authority:** read-only slice. No merge, deployment, or acceptance is claimed or performed.
The canonical origin remains `https://arkadia-qzu4.onrender.com` under ADR-016.

---

## 1. Objective

Add one bounded, user-visible, read-only slice to the Engineering Lab surface: an
**operational authority reading** that presents what the Lab declares about its own
ceiling and the mutations it forbids, sourced from data the surface already fetches.

This is a recovery of a capability present in the archived Prism UI
(`archive/frontend/arkadia-prism/web/public_prism/src/components/solspire/EngineeringLabLens.tsx`
renders an "Authority ceiling / The Lab does not change the system" panel), reconciled onto
the live `GET /api/lab/engineering/overview` contract rather than restored blindly.

## 2. Verified backend contract (source evidence, not archive usage)

| Method | Path | Auth | Handler |
|---|---|---|---|
| GET | `/api/lab/engineering/overview` | bearer — `require_lab_auth` (whole-router dependency, `api/lab_routes.py:61`) | `api/lab_routes.py::engineering_overview` |

`engineering_overview` spreads `runtime.overview(uid)` and adds operational sections. The
`authority` and `counts` blocks this slice reads are declared in
`lab/engineering_lab/runtime.py::EngineeringLabRuntime.overview` (lines ~631–654):

```
"counts":    { "sessions", "active", "awaiting_human" }
"authority": { "lab_authority_ceiling": 2, "autonomous_merge": False,
               "autonomous_deploy": False, "human_authorization_required": True }
```

These keys are pinned by the guard, so a handler rename reddens the guard instead of letting
the surface read a healthy-looking `unknown`.

## 3. Files changed

| File | Change |
|---|---|
| `web/arkadia_console/src/components/lab/labGovernance.ts` | New. Pure projection of the `authority`/`counts` blocks. No network, no React. |
| `web/arkadia_console/src/components/lab/LabAuthorityReadings.tsx` | New. Renders the reading. Issues no request of its own. |
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | Import + mount the reading, fed the overview the page already holds. |
| `tests/test_prism_w4_lab_governance_readings.py` | New guard (8 nodes): executed projection + handler-shape pins + negative controls. |

No shared file is touched: routing, navigation, tokens, `endpoints.ts`, `types.ts`, and
`surfaces.ts` are untouched (Workstream 1's seam).

## 4. State-boundary properties preserved (the non-collapses)

- **A ceiling is not a grant.** `lab_authority_ceiling` is reported as the maximum the Lab may
  hold, and the reading's note says so explicitly ("not a granted authority").
- **A declared prohibition is not consent.** `autonomous_merge`/`autonomous_deploy` are shown
  as declarations about the substrate, not permissions.
- **A run at the review boundary is not acceptance.** `awaiting_human` is surfaced as its own
  count, distinct from `active`.
- **Absence is unknown, not a closed door.** An unreported boolean reads `unknown`, never
  `false` — the dangerous direction (a missing flag reading as "merges are closed").

## 5. Negative controls (executed)

The projection is **executed** by node (the test imports the `.ts` and runs it), not
substring-matched. The load-bearing controls:

- `test_negative_control_absent_flag_is_unknown_not_false` — an omitted `autonomous_merge`
  reads `null`, and the mutation path is **not** called closed when only one of the two flags
  is declared.
- `test_negative_control_missing_block_reads_unknown` — an absent `authority` block reads
  unknown, never a healthy ceiling.

## 6. Verification run

- `python -m pytest tests/test_prism_w4_lab_governance_readings.py -q -rEf` → **8 passed**.
- `python -m pytest tests/architecture -q` → **11 passed**.
- `python -m pytest tests/test_prism_console_ci_wiring.py -q -rEf` → **30 passed** (the new
  test is inside the derived console-contract domain — `python scripts/console_contract_domain.py`).
- `cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build`
  → `tsc --noEmit` clean, `vite build` succeeded.
- `git diff --name-only HEAD | python scripts/cp10_mutation_boundary_policy.py --judge` →
  all paths admitted.

## 7. Remaining uncertainty / next bounded move

- The reading depends on the `authority`/`counts` block continuing to be served by
  `runtime.overview`; the guard names that dependency, but a **runtime** observation of the
  served payload requires an authenticated Lab session and was not performed here. This is a
  repository-source claim, not a production observation.
- Next Lane-4 move: continue the read-only Weaver/Arkana surfaces per
  `docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md`, one verified slice at a time.
