# Pulse 5 — bounded governance conflict + `/nexus/*` alias measurement

Bounded objective for this pulse: **reconstruct live state and measure the
governance conflict** between the active draft PR #418 and the accepted
parallel-work contract on `main`. No source edit was made: the file-level
conflict below is a **hard stop** for workstream-1-owned files, not a task to
patch around (contract §1, §4; directive §03/§09).

Authority: human retains merge, production deployment, and acceptance. Nothing
in this record claims any of the three.

## Revision binding

| Ref | SHA | Note |
|---|---|---|
| `origin/main` at pass start | `8dcb78d2` | merge of PR #419 (`a29a9b8f`), `d2670ce8` → `8dcb78d2` |
| PR #418 base | `d2670ce8` | unchanged; `main` has advanced past it |
| PR #418 head | `34c9a58b` | "docs(ui): point Hourly Weaver to shell implementation PR" |
| Local clone | `34c9a58b` | fast-forwarded from `75bbd859`; tree clean |

Local/remote divergence was masked by a narrow fetch refspec
(`+refs/heads/main:refs/remotes/origin/main`). Branch refs must be fetched
explicitly: `git fetch origin '+refs/heads/*:refs/remotes/origin/*'`.

## Finding 1 — `main` accepted a contract that re-homes PR #418's files

`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` is present on `main` and
self-describes as **ACCEPTED — merged via PR #419 at `a29a9b8f`** (verified: PR
#419 is `closed` / `merged=True`, `merge_commit_sha == a29a9b8f`, ancestor of
`origin/main`).

It defines four parallel workstreams with **exclusive file ownership**, and §2
assigns PR #418's own paths to workstream 1:

> `web/arkadia_console/src/App.tsx` | Route composition seam; workstream 1 owns.
> … `src/lib/router.ts` | Canonical router and alias resolution; workstream 1 owns.
> … `src/components/SurfaceLenses.tsx` | Shared navigation control; workstream 1 owns.

§6 explicitly supersedes the single-PR rule for the four named workstreams, and
§2 states plainly: *"Do not cherry-pick, split, close, or rewrite #418
automatically."* — that disposition is reserved to the human/coordinator.

**All four workstream PRs are open:**

| PR | Branch | Draft |
|---|---|---|
| #423 | `feat/prism-parallel-01-shell-implementation` | yes |
| #420 | `feat/prism-parallel-02-novanet-opportunity` | yes |
| #421 | `feat/prism-parallel-03-solariun-knowledge` | yes |
| #422 | `feat/prism-parallel-04-arkana-weaver-lab` | yes |
| #418 | `feat/prism-ui-reconciliation-overnight-01` | yes |

PR #423 (workstream 1 — the owner of the shell/router/surfaces/lenses) states in
its own body:

> PR #418 already changes the shell/router/surface registry/lenses/endpoint/type/
> shared test files. Until #418 is merged or the human explicitly chooses a
> split, do not edit those overlapping paths.

and its measured diff touches only `Shell.tsx` + its own instruction file.

**Consequence.** Editing `router.ts` (or any workstream-1-owned path) in PR #418
would create a **second mutation path** onto files `main`'s accepted contract
assigns to another live workstream — the contract's own §1/§4 prohibition and the
workstream-1 agent's recorded decision. This is a hard-stop class, not a patchable
defect.

Note the governance asymmetry to preserve: the `parallel-ui/` contract is
**on `main` (accepted)**, while the directive it would amend
(`docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md`) is **absent on
`main`** and lives only on PR #418's branch. The directive's §7 one-branch rule is
therefore still live for this branch while the accepted contract re-homes its
files.

## Finding 2 — `/nexus/*` deep links fall through to `home` (measured)

`PATH_ALIASES` in `src/lib/router.ts` maps only the exact path `/nexus`. Alias
resolution runs **before** path parsing, and `/nexus/ims` matches no alias, so it
parses as an unknown surface and `App.tsx` renders `home`.

Executed, not inferred — `router.ts`/`surfaces.ts` copied verbatim and run under
Node 24 with a stubbed `react`:

```
/nexus                   -> surface=novanet  section=-
/nexus/ims               -> surface=home     section=-
/nexus/grove             -> surface=home     section=-
/nexus/larder            -> surface=home     section=-
/nexus/distribution      -> surface=home     section=-
/novanet                 -> surface=novanet  section=-
/novanet/ims             -> surface=novanet  section=ims
/novanet/hub             -> surface=novanet  section=hub
routeForSurface(novanet,ims) = /novanet/ims
```

This **corrects a claim in pulse-4** (`56ca23b8`), which recorded the four
sub-views as rendering "an explicit `NotYetWired` state inside the surface". That
is true of `/novanet/<lens>` but **not** of the legacy `/nexus/<sub>` URLs, which
render `home`.

Legacy binding confirmed from the archive, not memory —
`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx:71-72` binds
`/nexus/ims`, `/nexus/grove`, `/nexus/larder`, `/nexus/distribution`.

**The defect is owner-scoped.** Its one-line fix belongs to workstream 1
(`router.ts`), per the accepted contract — the same seam as Finding 1. It is
recorded as a measured, reproducible handoff, not implemented here.

## Evidence-chain honesty

`/api/ims/inquiries` is sovereign-key gated while the console `apiClient` sends a
Bearer token only. Aliasing `/nexus/ims` → a lens would therefore route an
unauthenticated user into a contract that can only fail. Restoring alias
resolution and rendering an honest blocked state are **separable**; the alias
restoration is safe and owner-scoped, and does not by itself claim the IMS
contract is serviceable.

## Checks run this pass

| Check | Result |
|---|---|
| `python -m pytest tests/test_console_shell_nav_contract.py -q -rEf` | **20 passed** |
| CP10 mutation boundary (`--judge`, this record's path) | **PASS** (exit 0) |
| `main` delta `d2670ce8..8dcb78d2` | 2 docs files, +107 — no console source change |
| No source edit made | confirmed; tree clean apart from this record |

## Explicit non-claims

- No merge, no deployment, no production acceptance. PR #418 remains a **draft**.
- No claim that `https://arkadia-qzu4.onrender.com` serves this change; the
  console has not been deployed with it.
- No Vercel path used, promoted, or treated as evidence (directive §8).
- Finding 2 is a **source-level router measurement**, not a runtime/device
  observation.
