# ARK-OPS-CONTINUOUS-001 — cycle 39: Arkadia is the fair selection, the queue is 64 unique drafts, and production carries the revision it claims

**Directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Contract:** `docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`
**Pulse (UTC):** 2026-11-28T14:06 – 14:40
**Authority:** human-governed, evidence-bounded, fail-closed. `MERGE_AUTHORITY = NONE`, `DEPLOY_AUTHORITY = NONE`.
**Outcome:** one bounded unit — live reconstruction of all three repositories, a re-derived
fairness selection, a queue reconciliation measurement, and a Gate-2 revision-parity
observation. **No implementation was available that no open draft owns; that is stated as
the finding, not offered as a substitute for work.** No merge, no deployment, no acceptance.

## 1. Fresh-sandbox reconstruction

Identity was re-verified, not assumed. `gh auth status` reported account
`Arkadia-Oversoul-Prism` with token prefix `ghu_`; every read below used
`export GH_TOKEN="$GITHUB_TOKEN"`.

| repository | default branch | head | open PRs | open issues | `pushed_at` = last verified progress |
|---|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 5 | 1 | 2026-11-28T12:12:23Z |
| `family-safety-network` | `main` | `18c729735fd4` | 14 | 9 | 2026-11-28T13:11:41Z |
| `Arkadia` | `main` | `8f746f9eab6d` | 64 | 10 | 2026-11-28T11:14:08Z |

All three reachable. **No repository was omitted.** `family-safety-network` is private and
does not appear in `GET /users/Arkadia-Oversoul-Prism/repos`; it was confirmed by an
explicit `GET /repos/Arkadia-Oversoul-Prism/family-safety-network` (private `true`,
archived `false`, default `main`). A discovery path that only lists public repositories
would have silently dropped R3.

Since cycle 37 every repository advanced: sonata +1 PR (`#13`), FSN +2 PRs and +2 issues
(`#30`/`#31`), and FSN's head is unchanged at `18c72973` because its new work is on
branches, not `main`.

## 2. The selection (re-derived by the ledger's own selector)

```
$ PYTHONPATH=scripts python scripts/portfolio_state_refresh.py
sonata: VERIFIED branch=feature/sonata-tts-app head=7c4e6a64e39e pulls=5 issues=1 progress=2026-11-28T12:12:23Z
family-safety-network: VERIFIED branch=main head=18c729735fd4 pulls=14 issues=9 progress=2026-11-28T13:11:41Z
Arkadia: VERIFIED branch=main head=8f746f9eab6d pulls=64 issues=10 progress=2026-11-28T11:14:08Z
next: Arkadia-Oversoul-Prism/Arkadia -- oldest verified last_progress_at among unblocked
  repositories (2026-11-28T11:14:08Z); tie-break order Sonata -> FSN -> Arkadia
```

**Selected: Arkadia.** The previous pulse (13:11Z) worked FSN — it opened `#31`, a
migration-graph guard that proves two sibling Alembic revisions off one parent produce two
heads (`alembic heads` on `main` + `#12` + `#27` → `0003_audit_immu`,
`0003_erasure_identity`), with a negative control that must report 2 heads and a positive
control at 1. Its own CI log reads `65 passed` and `alembic upgrade head` succeeded. That
is FSN's clock, not Arkadia's, and the arithmetic is re-derived rather than remembered.

## 3. Arkadia queue reconciliation — measured, and it does not reduce

The directive's objective is to reduce open-PR accumulation through verified
consolidation, completion, or justified closure. Three closure tests were run against live
objects; the count is reported because the answer is negative.

| test | command | result |
|---|---|---|
| fully merged (commits landed) | `git merge-base --is-ancestor <head> origin/main` per PR | **0 of 64** |
| no net tree delta | `git diff --quiet origin/main..<head>` | **0 of 64** |
| no own delta vs merge base | `git diff --quiet origin/main...<head>` | **0 of 64** |

So **no open Arkadia PR is demonstrably obsolete**, and the contract's one closure
permission (`close an OpenHands-owned PR only when it is demonstrably obsolete`) is
therefore not satisfied by any PR. Nothing was closed.

GraphQL over all 64 open PRs:

| property | measured |
|---|---|
| total open | 64 |
| drafts | **64** |
| `reviewDecision` set | **0** |
| reviews of any kind | **0** |
| head CI `SUCCESS` | 40 |
| head CI `FAILURE` | 24 |
| oldest open PR created | 2026-11-21T12:10:58Z (7 days) |

Two facts follow, and both are human-blocked rather than agent-blocked:

1. **GOV-04 offers nothing.** Gate 1 requires a non-draft PR targeting `main`; all 64 are
   drafts, and GOV-04 forbids silent draft conversion. `reviewDecision` set on 0 PRs and
   0 reviews means gate 2's required reviews are unsatisfied on all 64 as well.
2. **24 of 64 could not merge even if made ready.** A failing head check is a real
   blocker independent of draft status. That split was not in any prior cycle record,
   which counted the queue (62, then 64) without recording how much of it is red.

## 4. Gate-2 revision parity — VERIFIED at the revision, NOT an acceptance

The standing boundary is `main → canonical deployment → production verification →
UI/runtime evidence`. Two links were observed read-only at the canonical origin:

```
$ curl -s https://arkadia-qzu4.onrender.com/api/version
HTTP 200 bytes=643
{"schema":"arkadia.version/v1","read_only":true,
 "canonical_deployment":"one_reconciled_deployment",
 "source_revision":"8f746f9eab6df51733f6d43c8bab26af63eb6471",
 "revision_source":"RENDER_GIT_COMMIT","revision_conflict":false, ...}

$ curl -s https://arkadia-qzu4.onrender.com/health
{"status":"radiant","path":"/health"}
```

`source_revision` equals current `main` exactly, and `revision_conflict` is `false`. So
**source↔runtime revision consistency is VERIFIED** — the deployed process is running this
revision's code.

What that does **not** establish, and is not claimed: the served frontend artifact, the
rendered UI, or any route behaviour. A matching revision is necessary evidence and not
sufficient proof, and no browser observation was taken this pulse. `/api/version` is the
only route cited; `/api/health` is not a backend route (`/health` is) and its 404 was not
re-measured here.

## 5. Why no implementation unit

The contract says a cycle "must not substitute a report for an available safe
implementation". No safe unowned implementation was available, and the search is recorded
so the next pulse does not repeat it:

- **Exception text in 5xx responses** — 59 matching sites remain across `api/`,
  `solspire/`, `kernel/`, `knowledge/`, `lab/`. The class is **owned**: `#718` repairs the
  Knowledge OS 5xx contract (`api/knowledge_routes.py` carries the densest concentration)
  and `#729` covers eight `api/` handlers. §8 forbids a parallel PR for a task an open
  draft owns.
- **Console endpoint-registry oracle** — repaired and merged as `#588`; re-ran this pulse
  at the live tree, `92 passed` across the six console-contract files.
- **Governance guards** — `tests/architecture`, `test_m02a_ci_gate_integrity.py` and
  `test_lane_instruction_doc_currency.py` re-ran: `153 passed`.
- **Consolidation tooling** — owned by `#736` (wave dry-run), `#733` (batch packet) and
  `#750` (already-landed oracle). This pulse *applied* those tests by hand (§3) rather
  than duplicating the detector.

Residual recovery named by the directive revalidated against live `main` in the same
pass: `tests/test_history_depth_ci_wiring.py` is present (R482), `scripts/lane_state.py`
carries `clone_is_shallow()` with the split verdict (R572), and `merged_acceptance_pending`
is exercised by four test modules (R499). None of the three is missing from `main`; no
recovery PR is warranted.

## 6. An environment finding worth keeping

A naive `python -m pytest tests/` in a fresh sandbox reported **146 failed, 145 errors**.
That number is not a repository signal: the errors are missing dependencies, and the
failure cluster is downstream of them (`ModuleNotFoundError: No module named 'httpx'`
raised from `api/main.py:10` inside `test_console_endpoint_registry_contract.py`). After
`pip install -r requirements.txt`, the same files report `92 passed`.

**Therefore: a failure count measured before `requirements.txt` is installed must not be
attributed to the tree.** Only after installation does a local failure mean anything.

## 7. Next-action block

- **Current state:** Arkadia `main` `8f746f9e`; 64 open PRs, all drafts, 0 reviews, 40
  green / 24 red heads; production running `8f746f9e` (`revision_conflict: false`).
- **Evidence:** this file; §2 selector output; §3 closure tests and GraphQL counts; §4
  `/api/version`; §5 guard runs; §6 dependency attribution.
- **Blockers:** every merge path needs an owner action (mark ready) and human review;
  24 PRs additionally need their head checks fixed before they can be considered.
- **Authorized action:** maintain existing OpenHands-owned drafts; repair an evidence-backed
  defect that no draft owns; close a PR only when demonstrably obsolete (none is).
- **Forbidden:** merge, push to `main`, force-push, draft conversion, deployment, ruleset
  or protection change, closing a PR that is not demonstrably obsolete.
- **Completion condition:** a bounded change with targeted tests and this cycle's record
  appended to the ledger PR — no merge claimed.
