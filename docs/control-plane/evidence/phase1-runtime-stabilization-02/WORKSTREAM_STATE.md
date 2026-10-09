# WORKSTREAM STATE — Phase 1 · Runtime Stabilization (PASS 2)

**Updated:** 2026-10-09 · **Base main:** `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`

## Current state

| field | value |
|---|---|
| Canonical main | `f9ced6b6` |
| Open PRs | 28 |
| Active workstream | Phase 1 · Runtime Stabilization |
| Active PR (this pass) | _new_ `phase1/runtime-stabilization-02-queue-reconciliation` |
| Live baseline node set | **16** (`bfcfe592…` / `ed5e4714…`) |
| Architecture suite | 11 passed |
| `main` required gate | **red** — `validate` job (`CP10 browser route verification`) |

## Evidence

- Baseline fingerprint: §2 of `EVIDENCE.md`
- Node classification: §3 of `EVIDENCE.md`
- Queue reconciliation: §5 of `EVIDENCE.md`
- PR #354 independent verification: §6 of `EVIDENCE.md`

## Blockers

- `main`'s required `validate` gate is red until PR #354 merges (sovereign).
- Two authority-boundary repair nodes (`test_engineering_lab_api.py`) are
  sovereign-only.

## Authorized action (this pass, done)

Read-only measurement + in-repo evidence persistence on a dedicated branch.
Branch pushed → PR opened. **Not merged.**

## Forbidden actions (this pass)

- No merge, no push to `main`, no force-push.
- No repair of unrelated baseline debt.
- No edit to `api/lab_routes.py` or any authority/governance surface.

## Exact completion condition

A human merges PR #354 (closing §3.1 + §3.2). The next heartbeat reconstructs from
`main`, re-derives the node set, and continues from the first unresolved boundary.

## Deterministic next-action block (for the next pass)

- **Current state:** `main` `f9ced6b6`; baseline 16 nodes; `validate` red.
- **Evidence:** this directory.
- **Blockers:** #354 unmerged; authority-boundary nodes sovereign-only.
- **Authorized action:** verify #354 still green at its head; recommend merge; then
  reconcile the composition-conflict PR cluster (#358/#361/#375/#376/#377) into one record.
- **Forbidden:** merge; edit authority surfaces; duplicate repair PRs.

## PASS 2B addendum — measured at `f9ced6b6` (2026-10-09)

The 16-node baseline above **supersedes nothing and is not environment-independent**.
The canonical command reproduces `bfcfe592…` / `ed5e4714…` **only when the full
declared requirements are installed**. `requirements.txt` declares `pytest-asyncio`
(and `jsonschema`) explicitly; disabling the plugin (`-p no:asyncio`) on the same
`main` SHA yields **23** nodes (`f3a01107…`), a fixed 7-node delta of `async def`
tests that fail with pytest's "async def functions are not natively supported"
diagnostic rather than a product assertion. `.github/workflows/baseline-fingerprint.yml:60`
installs `pip install pytest pyyaml`, omitting the declared plugin, so the CI contract
and the repository contract disagree. Reproduce with `-r requirements.txt`, and treat
a fingerprint as valid only together with its requirement set. Full measurement and
negative control: `docs/control-plane/evidence/phase1-runtime-stabilization-02b-baseline-dependency-sensitivity/EVIDENCE.md`.
