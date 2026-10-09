# EVIDENCE — gate2-canonical-alias-app-binding-01

Gate: GATE-02 (production parity) / gate-hygiene
Branch: `gate-hygiene/gate2-canonical-alias-app-binding-01`
PR: #369
Base main at time of pass: `24a00f856a0286cbb464a4b585117dd57a2646fa`
Head: `d6a12b2a` (+ evidence commit)

## 1. Defect

`scripts/gate2_production_observation.py` scores its `MARKERS` table — every entry
drawn from `web/public_prism/src` — against the bundle the canonical alias serves.
The repository-root `vercel.json` declares

```json
{"installCommand": "cd web/console && pnpm install --frozen-lockfile",
 "buildCommand": "cd web/console && pnpm run build",
 "outputDirectory": "web/console/dist",
 "rewrites": [{"source": "/(.*)", "destination": "/index.html"}]}
```

Vercel assigns the canonical alias to the **root** project, so
`https://arkadia-prism.vercel.app/` serves the **console**, not `web/public_prism`.
Against a Console artifact every Prism marker reads `0`.

`0` here means *“this artifact is not Prism”*. It does **not** mean *“Prism disagrees
with its source”*. Reporting the second when only the first is observed is the defect.

## 2. Change (bounded)

New standalone module `scripts/gate2_alias_app_binding.py` (read-only, stdlib only,
no network/credential/subprocess):

- resolves the root `vercel.json` `outputDirectory` → known application via
  longest-prefix match (`web/public_prism` → `arkadia-prism`, `web/console` → `console`);
- `marker_comparison_applicable` is true **only** when the root builds the marker app;
- **fail-closed**: an undetermined (missing/unparseable) or unlisted output directory
  yields no app and therefore no applicability.

New tests `tests/test_gate2_alias_app_binding.py` (12) include negative controls:

- `test_zero_markers_on_a_different_app_is_not_reported_as_agreement` — the would-be
  false positive is prevented;
- `test_unknown_output_is_undetermined_not_assumed` — a repoint to an unenumerated
  frontend cannot silently read as "still Prism".

`scripts/gate2_production_observation.py` is **intentionally not modified**: PRs #366
(per-deployment project labelling) and #368 (deploy enumeration) are concurrently
repairing it, and #368 records the composition finding and states "do not open a third
PR on this file". A new module composes with either without conflict.

## 3. Measurements

Environment: depth-1 clone, `main` = `24a00f85`, `PYTHONPATH=<repo>/archive/legacy_python`.

| Check | Result |
|---|---|
| `pytest tests/test_gate2_alias_app_binding.py -q` | 12 passed |
| `pytest tests/architecture -q` | 11 passed |
| `python -m py_compile api/main.py` | OK (boot code untouched) |
| `wc -l api/main.py` | 2462 (< 2600 budget; unchanged) |
| Full suite on `24a00f85` (baseline worktree) | 20F / 1767P / 23S / 1E — node ids_sha `7563e0de8f8ce5f4e714740774f33adb78c32d4505075bb28b96ad18976b9957` (21 nodes) |
| Full suite on branch | 20F / 1779P / 23S / 1E — node ids_sha `7563e0de8f8ce5f4e714740774f33adb78c32d4505075bb28b96ad18976b9957` (21 nodes) |

**Regression: none.** Failing/error node *set* is byte-identical on both sides; the
`+12 passed` is exactly the new test file. Attribution was done on node identity, not
on counts, per the AGENTS.md rule that the full-suite fingerprint is unstable.

## 4. Live verification

- `python scripts/gate2_alias_app_binding.py` (live tree) →
  `root output directory: web/console/dist`, `root project app: console`,
  `marker comparison: NOT APPLICABLE`.
- `GET https://arkadia-prism.vercel.app/solariun/opportunity-radar` → HTTP 200, 789
  bytes, serves **Console** (the `rewrites` rule sends every path to the console
  `index.html`). The Prism Solariun route is not reachable from the canonical alias.

## 5. Remaining uncertainty / not claimed

- The classifier is not yet *called* by the shared observer; the marker table is still
  scored unconditionally there. This pass makes the fact inspectable and guarded, it
  does not rewire the observer. Wiring is left to whoever lands the #366→#368 sequence.
- The console's own production surface remains observation-blocked behind Vercel
  Deployment Protection (302 → `vercel.com/sso`). Unchanged by this pass.
- No production-parity or acceptance claim is made.
