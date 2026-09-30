# WORKSTREAM STATE — gate-hygiene / SH-02

**Pass:** 2026-09-29 (hourly bounded execution)
**Base main (BASE_MAIN):** `df7a99a` — `Merge pull request #131 from …/gate-hygiene/baseline-stale-assertion-repair-spiral-grove-05`
**Branch:** `gate-hygiene/sg04-canonical-header-merge-regression-audit`
**Authority:** evidence/docs only. No merge, no `main` push, test-only envelope **not** exercised
(the selected candidate turned out to require source changes).

> NOTE: the previous pass recorded base `4164573586860b9c7e04e1815bca4957559046a2`. That is an
> **ancestor**, not current `main`. Current `main` has advanced by PRs #130, #131, #132.
> Reconstruct from `git log -1 origin/main` every pass — never reuse a stored SHA.

---

## 1. Reconstructed state

| item | live value |
|---|---|
| `origin/main` | `df7a99a` |
| architecture suite | 11/11 passing |
| `api/main.py` | under the 2600-line budget (untouched this pass) |
| full suite | 32 failed / 1025 passed / 13 skipped (ignoring 2 documented collection errors) |
| frontend build | `vite build` environment-blocked (no npm registry access) |

### Open PRs (derived, not assumed)

| PR | branch | state |
|---|---|---|
| #133 | `gate-hygiene/baseline-stale-assertion-repair-living-gate-06` | OPEN, draft=false |
| #135 | `gate-hygiene/sh02d-prism-interior-shell-rebase-01` | OPEN, draft=false |
| #136 | `gate-hygiene/sh02e-agent-run-capability-onboarding-repair` | OPEN, draft=false |
| #137 | `gate-hygiene/sh02f-solspire-p1-experience-01-repair` | OPEN, draft=false |
| #129, #130, #131, #132 | — | MERGED |

No open PR claims the SG-04 canonical-header cluster. No duplicate work created.

## 2. Classification result — CONTRADICTED

The selected candidate
`tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header`
was pre-classified `STALE_ASSERTION`. **That premise is falsified.**

- The node **passed** at `73b8868` (`fix(sg04): establish canonical Spiral Grove header`).
- The node **failed** immediately after merge `ff80b8c`
  (`Merge branch 'main' into sg-04-learning-activity-runtime`), which **restored** the page-local
  `<h1>` that `73b8868` had deliberately removed.
- So: **merge regression, not drift.** The governance property went enforced → violated.

Three sibling nodes fail from the same merge (`:79`, `:85`, `:110`) — a cluster-level loss.
`CapabilityChamber.tsx:4` imports `ActivityRuntime` with no mount: independent corroboration.

Root cause is a **two-mount render surface** (`App.tsx:134` `view==='grove'` vs
`NexusPage.tsx:909` `activeTab==='university'`) where only the Nexus mount supplies an `<h1>`.
Both the delete-header and restore-header variants are wrong on one route. The remedy is
**source + product decision**, outside the `gate-hygiene` test-only envelope.

Detail: `./EVIDENCE.md` §3–§6.

## 3. Next bounded task (queued, not started)

`tests/test_steward_filter.py` — 3 failing nodes, candidates inside the SH-02 envelope:

- `test_allows_mythic_with_action`
- `test_blocks_identity_claims`
- `test_compress_to_choices`

Adjudicate **retain / reword / build-to-reality** against `steward/` source before editing. This
cluster asserts compression + identity-claim blocking; treat it as **possibly a recovered
governance failure**, and check the fail-closed direction before weakening anything.

## 4. Aggregate baseline debt (unchanged, recorded not fixed)

- Full suite: 32 failed / 1025 passed / 13 skipped.
- Documented collection errors (pre-existing): `tests/test_weaver_k0.py`,
  `tests/test_render_codex.py` (missing module `arkadia_drive_sync`).
- `tests/architecture`: 11/11 — unchanged.
- Four `recon/solspire-r0` forked-recon file copies fail locally but are **inert for `main` CI**
  (their workflows trigger only on `push` to `recon/solspire-r0`). Recorded, not repaired.
- `tests/test_steward_filter.py` ×3 and `test_spiral_grove_activity_runtime.py` ×4 are inside
  these counts; the SG-04 four are now attributed to the `ff80b8c` merge regression.

## 5. Blockers / authority required

| item | type | required authority |
|---|---|---|
| SG-04 canonicalization re-land (source) | product/UI architecture | sovereign decision + SG-04-owned source PR |
| Two-mount header ownership (`App.tsx` vs `NexusPage.tsx`) | product decision | sovereign |
| Merge of this evidence PR | merge | human sovereign |

## 6. Provenance / persistence

- Evidence: `docs/control-plane/evidence/gate-hygiene-sg04-canonical-header-merge-regression-01/EVIDENCE.md`
- This file is the persisted workstream state for the next heartbeat (§13 PERSIST).
- No runtime/deployment claim made. Repository layer `VERIFIED`; deployment layer `UNKNOWN`.
  Parity is **not** claimed (`BASE_MAIN` `df7a99a` is not tied to a deployment identity here).
