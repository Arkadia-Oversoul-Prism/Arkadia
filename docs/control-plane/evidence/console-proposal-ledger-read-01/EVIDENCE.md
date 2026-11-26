# Console proposal ledger — read the served contract instead of advertising it as unwired

**Contract:** ARK-OPS-CONTINUOUS-001 (continuous reconciliation, fail-closed).
**Date:** 2026-11-22
**Base:** `main` @ `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Branch:** `feat/console-proposal-ledger-read-01`
**Authority:** none. No merge, no deployment, no production acceptance. Draft PR only.

## 1. Defect

The SolSpire `proposals` lens rendered a `NotYetWired` panel whose advertised contract was
`/solspire/proposals`:

```
<NotYetWired
  contract="/solspire/proposals"
  note="Proposal reads and the proposal decision endpoint are served, but a decision is a
        human act on the authority chain, so the console does not offer one yet."
/>
```

The panel's shared copy asserts the contract is *absent* ("contract not yet wired"). It is
not. Measured from the canonical app's own document at this revision —
`api.main:app.openapi()["paths"]`, **300** served paths:

```
/solspire/proposals               -> {'get', 'post'}
/solspire/proposals/{proposal_id} -> {'get'}
```

and `solspire/proposal_router.py` declares the collection under
`APIRouter(prefix="/proposals", dependencies=[Depends(require_auth)])`, so the read is
authenticated and owner-scoped through the subject's canonical workspace. The lens therefore
told an operator that a served, authenticated read did not exist, and showed them nothing the
contract could answer. That is the honesty failure `SHARED-CONTRACTS.md` §3.5/§3.6 governs:
the two states — *contract absent* and *interface unbuilt* — were collapsed into one.

The note was also partly self-contradictory: it said the reads are served while the shared
copy said the contract is not wired.

## 2. Change

Read-only, bounded to three source files plus tests. No route, no authority, no mutating act.

| Path | Change |
|---|---|
| `web/arkadia_console/src/lib/endpoints.ts` | adds `solspireProposals: "/solspire/proposals"` |
| `web/arkadia_console/src/components/solspire/ProposalLedger.tsx` | new read-only ledger over the registry entry |
| `web/arkadia_console/src/pages/SolSpirePage.tsx` | mounts `<ProposalLedger />` in the `proposals` lens; the `/solspire/workevents` placeholder stays |

The ledger renders only fields the handler publishes (`proposal_id`, `proposal_status`,
`objective`, `scope`, `requested_decision`, `proposal_version`, `updated_at`) and keeps four
states distinct:

- **ready + records** — the recorded proposals, status shown as the recorded value;
- **ready + empty** — "No proposals are recorded for this workspace. An empty ledger is not an
  approval.";
- **ready + unlistable shape** — refused, not rendered as an empty list;
- **`409` (no canonical workspace)** — a workspace prerequisite, not a failure. The handler
  raises `409 "Canonical workspace not found"`; `CONFLICT` is classified separately, the same
  way `SolSpireControlPlane` treats it.

It offers **no** decision or authorization control. `POST /solspire/proposals/{id}/decision`
and `POST /solspire/authority/proposals/{id}/authorize` remain human acts on the authority
chain and are not reachable from this surface.

## 3. Verification (measured)

### 3.1 The guard

`tests/test_console_proposal_ledger_contract.py` — **9 passed**.

It binds these properties and carries a negative control per detector:

| Property | Live assertion |
|---|---|
| registry entry is the served path, served as `GET` | `api.main:app.openapi()` |
| the serving router requires authentication | `solspire.proposal_router.router.dependencies` contains `require_auth` |
| the component reads through the registry | `useHydration<unknown>(endpoints.solspireProposals` and **no** literal path argument |
| no mutating act is reachable | no `/decision`, `/authorize`, `/execute`, `/transition` route and no `POST` in the rendered code |
| the page mounts the ledger and stops advertising the contract | `SolSpirePage.tsx` |

### 3.2 Live negative controls (real files, then restored)

Each control was applied to the working tree, measured, and reverted:

| Control | Result |
|---|---|
| page re-advertises `contract="/solspire/proposals"` on `NotYetWired` | `1 failed, 8 passed` — `test_page_mounts_the_ledger_and_stops_advertising_the_served_contract` |
| ledger passes `"/solspire/proposals"` inline instead of the registry | `1 failed, 8 passed` — `test_ledger_reads_through_the_registry` |
| `dependencies=[Depends(require_auth)]` removed from `solspire/proposal_router.py` | `1 failed, 8 passed` — `test_serving_router_requires_authentication` |

`solspire/proposal_router.py` is byte-identical after restore (`git status --short` empty).
Each control reddens exactly one intended node — a guard that reddens on all three or on none
would be measuring the wrong thing.

### 3.3 Console-contract domain (same environment, both trees)

The gate executes a **derived** inventory (`scripts/console_contract_domain.py`), so the new
guard enters it without editing the workflow. Measured in a `main` worktree with the same
`node_modules` symlinked, and on this branch:

```
main   @ 034d8879 : 2 failed, 1279 passed, 4 skipped   (74 guards)
branch            : 2 failed, 1288 passed, 4 skipped   (75 guards)
```

The **failing node set is identical** — `tests/test_prism_w4_lab_pr_state.py::
test_handler_emits_the_keys_the_projection_reads` and `::test_projection_reads_the_handler_output`
— and the `+9 passed` is exactly the new guard's node count, not a behavioural delta.

**The two local failures are credential-dependent, not repository debt.** They assert
`"state": "AVAILABLE"` from `api.lab_routes.pr_state`, which needs an authenticated GitHub
client; this sandbox has none, so the handler answers `UNAVAILABLE`. The same guard is red on
`main` for the same reason, and open PR #683 ("enforce the Lab PR-state guard's no-token
premise", touching exactly that test file) owns the repair.

**The CI measurement is stronger and is the authoritative one for this branch:** run
`45043938762`, job `console-contract`, step *Verify the console contract guards* →
`1294 passed in 46.55s`, **0 failed**. The runner has a token, so the two premise nodes pass
there. Local and CI counts differ because the premise differs; neither reading contradicts the
other, and neither is a regression from this change.

### 3.4 Frontend

```
pnpm exec tsc --noEmit            exit 0
pnpm exec vitest run              9 files, 67 tests passed   (was 8 files / 61 — +6 new)
pnpm exec vite build              built; dist/ is untracked
```

`web/arkadia_console/src/components/solspire/ProposalLedger.test.tsx` mounts the real component
with only the transport hook stubbed, and pins the state separation: registry path, records,
empty-is-not-approval, unlistable-shape refusal, `409` as prerequisite, and a transport failure
that must not render as an empty ledger.

### 3.5 Baseline note (recorded so it is not misread as debt)

A full-suite run before the console toolchain was installed measured
`21 failed, 4245 passed, 22 skipped, 1 error`. Ten of those failures are
`tests/test_mission_lifecycle_adapter_contract.py`, which requires the repository TypeScript
compiler at `web/arkadia_console/node_modules/typescript/lib/typescript.js`; with
`pnpm install --frozen-lockfile` present they are **10 passed**. That cluster is a missing
toolchain in the measuring environment, not repository debt.

A test run also materialises `data/engineering_lab/agent_events.jsonl` inside the repository
(the subject of open PR #688). It was removed, not committed.

## 4. Limits — what this does not claim

- **No merge, no deployment, no production observation.** The ledger is verified by typecheck,
  production build, behavioural tests and source-contract guards. It has **not** been observed
  against an authenticated production session.
- The response shape is taken from the handler and `Proposal.to_dict()`, not from an
  authenticated live read. `updated_at` is rendered from the handler's `time.time()` clock
  (epoch seconds) as ISO-8601; an absent or non-numeric value renders `UNKNOWN`.
- The `proposals` lens still renders a `NotYetWired` panel for `/solspire/workevents`, which is
  a *different* served spine (list + single reads) with no console surface yet. That remains
  honest and is unchanged.
- `/solspire/voice/events` (the `voice` lens) is untouched.

## 5. Next single bounded move

The `workevents` panel is the next served read in this section: `GET /solspire/workevents` is
served and auth-gated, and a read-only work-event ledger would close it the same way. It is a
separate change because its event refs must be reconciled with the console's provenance surface
first — the panel's own note states that gap, and this slice did not establish it.
