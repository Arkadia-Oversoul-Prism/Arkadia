# Lane 2 — echo display completeness (evidence)

**Lane:** 2 (NovaNet / Opportunity Radar)
**Branch:** `feat/prism-l2-echo-display-completeness-01`
**Base:** freshly fetched `main` `19697a6a358ec114265e665fcc22eea8d5018ac2`
**Opened under:** `11 — LANE NEW-PR AUTHORIZATION` (N1–N8). Draft; merge is human-only.

## The defect

`GET /api/echoes` (`api/main.py::echoes_feed`) derives five display fields for every
public echo — `title`, `category`, `preview` (the scroll `body` truncated to 200
characters), `source`, and `resonance` — and `EchoEntry` in `src/lib/types.ts` declares
all five. The echoes panel in `NovaNetPage.tsx` rendered only `title`, `source` and
`resonance`, so an echo's **substance** — the handler's own preview of its body — and
its **category** were never shown. A reader saw a headline and no content.

Measured at `main` `19697a6a`:

| Fact | Command | Result |
|---|---|---|
| Handler derives `preview` | `sed -n '1672,1735p' api/main.py` | `"preview": (s.get("preview") or (s.get("body") or "")[:200])` |
| Handler derives `category` | same | `"category": s.get("category") or … or "NEURAL_SPINE"` |
| Type declares both | `lib/types.ts` `EchoEntry` | `category: string; preview: string;` |
| Panel rendered neither | `grep -n 'e\.' …/NovaNetPage.tsx` (echoes block) | only `e.title`, `e.source`, `e.resonance` |

This is the same "dead data" class this lane repaired twice before
(`prism-opportunity-evidence-coverage-01`, and the radar's operator `notes`): a value
the backend returns, the type declares, and the surface silently drops.

## The repair

`NovaNetPage.tsx` — the echo's metadata line now carries `category` beside `source`,
and the handler's `preview` renders beneath the title when present. Display-only: both
are the handler's own values, shown as returned. No new request, route, or control.

`tests/test_prism_novanet_echoes_completeness.py` — extends the file the console gate
already executes (no new workflow, no wiring change). Adds a pure source detector
(`find_unrendered_echo_fields`), its live assertion, and a negative control.

## Proof — live negative control on the real file

| Step | Result |
|---|---|
| Revert the real `NovaNetPage.tsx` to the pre-repair render (drop `category` + `preview`) | `test_every_handler_supplied_echo_field_is_rendered` → **FAILED**; `1 failed, 4 passed` |
| Restore byte-identically (`md5 9e813b5edcab254cfd50f1bb12af44b9` before and after) | `5 passed` |

The control also asserts the silent-cap detector still **passes** the reverted shape, so
the two detectors measure different properties rather than one re-stating the other.

## Attribution

`--collect-only` on the file: `3` on `main` → `5` on the branch. `+2` = exactly the new
guard and its control. The console-contract domain the CI gate executes
(`python -m pytest -q $(python scripts/console_contract_domain.py)`) is **1163 passed,
0 failed**. `tests/architecture` **11 passed**. `tsc --noEmit` exit 0; `vite build`
succeeds.

## Environment note

Ten `tests/test_mission_lifecycle_adapter_contract.py` nodes failed on first run
(`the repository TypeScript compiler is missing at …/node_modules/typescript`). They
reproduce identically on a clean `origin/main` worktree, so they are **not** branch
caused — the sandbox starts without `web/arkadia_console/node_modules`. After
`corepack pnpm install --frozen-lockfile` all ten pass, and the domain is fully green.
Recorded rather than attributed.

## Boundaries

Lane-2 owned paths only: `web/arkadia_console/src/pages/NovaNetPage.tsx` and
`tests/test_prism_novanet_echoes_completeness.py`. No Lane 1 registry/type edit; no
other lane's file; no backend change. No authority, identity, governance, or deployment
surface touched. Merge, production deployment and acceptance remain human-only.
