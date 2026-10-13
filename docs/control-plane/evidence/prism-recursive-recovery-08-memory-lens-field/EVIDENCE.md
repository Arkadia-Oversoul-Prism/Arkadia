# EVIDENCE — PRR-08 · Solariun `memory` lens reads the personal Echofeild model

**Work item:** PRR-08 (prism-recursive-recovery-01 ledger)
**Target behavior:** The Solariun `memory` lens reads the served, verified
contract `GET /api/me/field` (`api/echofeild.py::get_my_field`, `require_auth`)
— the archived Prism's Personal Echofeild capability — rendering counts with
the contract's **per-source provenance**: an unavailable source shows
"unavailable · not counted", never a confident zero.
**Base (dependency):** stacks on draft PR #510
(`feat/prism-rec-01-solariun-routed-lenses` @ `b67b8f7`), which owns
`SolariunPage.tsx`.
**Implementation commit:** `f7f9c7d836c207df4d655a176245d0f89de93aed`
(candidate head when every verification below was executed; the PR head also
carries this record — base + PR head identify the candidate).

## 1. Correction of a prior claim (evidence before claims)

PRR-01 (PR #510) rendered the `memory` lens as an honest not-wired state with
the claim "no verified read contract exists in the console endpoint registry".
**That claim was too strong.** `endpoints.field` (`/api/me/field`) is in the
registry and served (`test_console_endpoint_registry_contract` proves every
declared endpoint is served), and the archived route table maps
`/personal-echofeild` → solariun observatory, making this the lens's natural
canonical contract. This work item wires it and **supersedes** the PRR-01
memory state; `tests/test_solariun_lens_contract.py`'s memory test was updated
in the same commit (documented here — the pinned state was improved with
evidence, not weakened to make a build pass).

## 2. Changed paths

- `web/arkadia_console/src/components/solariun/PersonalFieldPanel.tsx` (new)
  — one read of `endpoints.field` (registry member, satisfies the one-registry
  guard); counts only (notes, timeline, knowledge projects, SolSpire projects,
  conversations, messages, executions); graph nodes/edges counts; provenance
  chips straight from `meta.sources` with the contract's own `detail`;
  loading/auth-required/unavailable/error delegated to the shared
  `ContractState`; `generated_at` shown.
- `web/arkadia_console/src/pages/SolariunPage.tsx` — memory lens mounts the
  panel; the superseded not-wired block and its claim removed; header comment
  corrected.
- `tests/test_solariun_lens_contract.py` — memory test superseded (asserts the
  panel and the absence of the stale claim).
- `tests/test_prism_solariun_memory_lens.py` (new, 7 tests).

Read-only: no control in the slice mutates anything; no record content is
rendered (counts and provenance only).

## 3. Verification

| Command | Baseline @ `b67b8f7` (measured in a detached worktree) | After candidate |
|---|---|---|
| `cd web/arkadia_console && pnpm run build` | PASS | **PASS** (exit 0) |
| shared set (solariun-lens, echofeild aggregator, canonical routing, rebuild-01, aeas05, endpoint registry, authority chain, shell nav, pass-C, solariun consolidation/knowledge/x01-x12, CP10 integrity, `tests/architecture`) | **226 passed** | **226 passed** (unchanged) |
| same set + `tests/test_prism_solariun_memory_lens.py` | — | **233 passed** |

The backend contract this lens consumes is regression-covered by the executed
suite `tests/test_echofeild_aggregator.py` (auth refusal, cross-user
isolation, composition) — run in every verification above and passing
unchanged. Frontend contracts (negative controls included): panel mounts on
the memory lens; reads the registry member (no inline path); renders
provenance verbatim with `detail`; degraded sources gated on the included set;
a confident-zero panel shape is flagged; record-item maps are flagged; the
hydration state passes straight to the shared `ContractState` (a hand-rolled
state machine is flagged).

## 4. Review findings

- Scope: 1 new component, one lens block swapped, one test updated, one test
  added (+evidence). No backend change; no new dependency.
- Honest states: partial compositions degrade visibly (chip + "unavailable ·
  not counted"), matching what the contract actually reported.
- No duplicate authority: the panel reads the one canonical field contract;
  Knowledge OS surface reads its own `/api/knowledge/*` contracts — different
  contracts, no second implementation.

## 5. Limitations / risks (explicitly not claimed)

- **NOT TESTED (browser)** — no browser harness in this sandbox.
- The unavailable-source branch of the panel is pinned by source contracts,
  not by a seeded fault injection (the backend suite covers the handler's
  graceful-degradation paths).
- Stack: merges only after PR #510; overlaps PR #513's `SolariunPage` edits
  only in distant hunks (projects lens vs memory lens).

## 6. Next dependency / recommended action

Draft PR with base = `feat/prism-rec-01-solariun-routed-lenses`; retargets to
`main` after #510 merges.
