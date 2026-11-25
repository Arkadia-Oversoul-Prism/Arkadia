# ARK-OPS-CONTINUOUS-001 — Cycle 20

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22` (recorded by this PR)
- **Cycle:** 20 — immediate execution + hourly continuation
- **Observed:** 2026-11-25T11:06Z onward
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. This cycle performed no
  merge, no push to `main`, no deployment, and claims no acceptance.
- **Substantive change:** none to production code. The cycle's product is a **per-pair composition
  measurement of the whole open-PR queue** (the previous ledger recorded file-overlap *clusters*
  and one conflict; it did not run a three-way merge over each overlapping pair), plus a verified
  resolution for one conflict and a precise classification of another. No new PR was opened: every
  measured defect is owned by an open PR or reserved.

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-24T17:30:03Z) | `git rev-parse origin/main` |
| last merge | `#722` — GOV-04 bounded merge delegation | `git log -1` |
| open PRs | **57** — **56** drafts, **1** non-draft (`#724`) | `GET /pulls?state=open` |
| obsolete PRs | **0** | no open head is an ancestor of `main` (`git merge-base --is-ancestor`) |
| `main` check-runs at `fd0a4fdc` | `test`, `posture-currency`, `lane-doc-currency`, `engineering-scheduler`, `console-contract`, `boot-syntax`, `Full-history secret scan` — all `success`; `weaver_evolution` `skipped` ×2 | `GET /commits/<full sha>/check-runs` |
| branch protection | **absent** (`/branches/main/protection` -> `404 Branch not protected`) | REST |
| rulesets | **0** | `GET /rulesets` |
| `api/main.py` | **2597** lines (budget 2600) | `git show main:api/main.py \| wc -l` |

The absence of branch protection and rulesets is recorded, not repaired: enabling them is a
governance decision, and no agent may bypass or manufacture platform controls.

## 2. Production boundary — source revision VERIFIED, acceptance NOT CLAIMED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision       fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source       RENDER_GIT_COMMIT
  revision_conflict     false
  canonical_deployment  one_reconciled_deployment
```

Source <-> running revision is sha-identical to `main`. That is consistency evidence; it is not
proof of correct behaviour and not deployment acceptance.

### 2.1 Whole-surface GET sweep — one 5xx, owned

Every `GET` operation in the deployed `openapi.json` was probed read-only, with `{param}` segments
replaced by `1`:

| status | operations |
|---|---|
| 200 | 44 |
| 401 | 102 |
| 404 | 5 |
| 422 | 4 |
| 403 | 3 |
| 400 | 1 |
| **502** | **1** |
| **total** | **160** |

The single 5xx is `GET /api/codex/github-tree`:

```
502 {"error":"Client error '401 Unauthorized' for url
     'https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/git/trees/main?recursive=1'"}
```

This is a real production defect (availability, and it echoes the upstream URL), and it is
**owned**:

- **#701** (`fix/github-corpus-credential-fallback-01`) makes a refused credential degrade to an
  anonymous read instead of failing the corpus. Verified at its own head:
  `tests/test_github_corpus_credential_fallback.py` -> **9 passed**.
- The anonymous fallback it relies on was measured live: an unauthenticated
  `GET /repos/.../git/trees/main?recursive=1` -> **200**, 1,049,842 B, **3212** entries,
  `truncated: false`.
- **#729** (`fix/api-main-5xx-error-contract-01`) replaces the echoed exception text with a
  governed failure detail; its diff covers this exact handler (`github_tree`).

The 404/422/403/400 rows were each inspected and are legitimate: missing required query
parameters (`/api/knowledge/search/*`, `/api/google-workspace/oauth/callback`), unknown ids
(`Release 1`, `Note not found`, `Persona not found`, `Project not found`), and the two sovereign
gates (`/api/dashboard/loops`, `/api/ims/inquiries`). No undeclared route defect.

## 3. Open-PR queue — composition measured per pair, not assumed

The previous cycle recorded composition **clusters** (file overlap) and carried forward one known
conflict. This cycle ran a three-way merge over **every** overlapping pair.

Method: all 57 heads were fetched by exact SHA; changed files were read from
`GET /pulls/<n>/files`; every pair sharing at least one path was composed with
`git merge-tree --write-tree <head-a> <head-b>` in this repository's object store.

```
open PRs                 57
shared files             14
overlapping pairs        16
  CLEAN                  13
  CONFLICT                3
  UNPROVABLE              0
```

| pair | result | conflicted path |
|---|---|---|
| `681 × 687` | CONFLICT | `tests/test_gate2_production_observation.py` |
| `686 × 724` | CONFLICT | `AGENTS.md` |
| `689 × 728` | CONFLICT | `.github/workflows/canonical-render-browser-smoke.yml` |
| `682×684`, `692×704`, `693×716`, `701×711`, `701×717`, `701×729`, `707×728`, `710×713`, `711×717`, `711×729`, `717×721`, `717×729`, `718×734` | CLEAN | — |

**This supersedes the implicit "one conflict" reading.** The queue has **three** textual conflicts.
Two of them (`686 × 724`, `689 × 728`) were listed by the previous cycle only as file-overlap
clusters and had never been composed.

## 4. `686 × 724` — a mechanical union, with the merge order determined

Both PRs touch the **same GOV-04 region** of `AGENTS.md`:

- **#724** rewrites the GOV-04 paragraph to record that `#722` was human-merged and GOV-04 is
  active.
- **#686** appends a new section, `## A tracked artifact turns a read-model leak into a published
  one (secret-hygiene)`, immediately after that paragraph.

Neither is superseded: #686 carries the `weaver/recon.py` remote-userinfo redaction, which is not
on `main`, and #724 carries the activation record.

The conflict resolves as a union, and the resolution was **built and executed** in a detached
worktree (`#724` head `7e32149a` + merge of `#686` head `330f5874`):

| check | result |
|---|---|
| conflict markers remaining | **0** |
| Cyrillic codepoints in `AGENTS.md` | **0** |
| `scripts/agents_md_encoding_audit.py` | `alterations=0`, `oracle_reproduced=True`, insertions-only |
| `tests/test_agents_md_encoding_adjudication.py` | **21 passed, 2 skipped** |
| `tests/test_repository_remote_redaction.py` | **18 passed** |
| `tests/test_gov04_bounded_merge_delegation.py` | **1 failed, 3 passed** |

The one failing node is `test_bounded_merge_is_exact_head_and_protected_fail_closed`. It is
**pre-existing on `main`**, not caused by the composition: the same file at `main` in a clean
worktree reports **1 failed, 3 passed** with the same node. It is repaired by open **#725**.

**Recommended order: #724 first (it is the non-draft), then #686 rebased onto it.** The rebase is a
union of one rewritten paragraph plus one appended section; it is not a design decision.

## 5. `689 × 728` — competing implementations, and they are not field-compatible

Both PRs repair the same defect — the canonical browser smoke failing on the console's accepted
anonymous 401 — but they implement it differently:

| | #689 | #728 |
|---|---|---|
| verdict lives in | `scripts/canonical_browser_report.py` (new, testable) | the workflow heredoc (inline `report.result`) |
| capture fields | `console_errors`, `failed_responses` | `unexpected_console_errors`, `anonymous_401_count`, `ok`, `final_path`, `expected_path`, `fell_back` |
| route set | unchanged | rewritten, bound to `surfaces.ts`, includes legacy aliases |
| revision identity | `ARKADIA_OBSERVED_REVISION` env | `deployed_revision` + `require_revision` outputs |
| `scripts/canonical_browser_report.py` on `main` | **absent** (new in #689) | n/a |

The two are **not trivially composable**: #689's judge reads `console_errors` and
`failed_responses`, which #728's report no longer emits (it emits
`unexpected_console_errors` / `anonymous_401_count` instead). Feeding #728's report to #689's
judge would require adapting the judge or the capture — i.e. a decision about **where the verdict
lives**, not a textual merge.

This is recorded as a **design conflict requiring human adjudication**, not repaired by an agent.
Merging both unreconciled would produce a workflow whose verdict is computed twice under different
rules; merging either alone is coherent.

#707 shares **`prism-console-contract.yml`** with #728 (that pair is CLEAN); it does **not** touch
`canonical-render-browser-smoke.yml`, so it does not force the order between #689 and #728.

## 6. `681 × 687` — unchanged

Identical to the previous cycles' measurement; adjudicated by the open evidence record on **#703**
(`docs/control-plane/evidence/gate-hygiene-gate2-open-pr-composition-01/EVIDENCE.md`). This cycle
re-measured it rather than restating it.

## 7. What was searched for and not found (negative results)

Recorded because a cycle that finds nothing must say what it looked at:

| candidate class | result |
|---|---|
| duplicate FastAPI `(method, path)` registrations | **0** (route table enumerated) |
| router modules never imported elsewhere | **0** of 36 |
| workflow `run:` commands referencing a missing repo path | **0** (4 crude matches were prose in comments) |
| whole-suite gates without `fetch-depth: 0` | **0** (`provider-routing.yml`, `sg-02-fe-2-v.yml` both set it) |
| executed workflow inputs not selected by their own `paths` filters | **0** |
| console `"/api/..."` / `"/solspire/..."` literals absent from the deployed `openapi.json` | **2**, both documented: `/api/codex/categories` is deliberately not served and derived locally; `/solspire/*` is a display pattern in `surfaces.ts` |
| unconditional `pytest.mark.skip` | **0** |
| always-true assertions (`assert True`, `assert … or True`) | **0** remaining on `main`; the seven found are repaired by **#730** |

No measured, unowned defect was found that a new PR could carry.

## 8. Next-action block

**Current state.** `main` = `fd0a4fdc…`; production `source_revision` identical,
`revision_conflict: false`; `main` CI 7 `success` + 1 `skipped`; **57** open PRs (56 drafts, 1
non-draft), **0** obsolete; 16 overlapping pairs, 13 CLEAN, **3 CONFLICT**; one live 5xx
(`/api/codex/github-tree`) owned by #701 + #729.

**Evidence.** §2.1's 160-operation sweep; §3's per-pair `merge-tree` table; §4's built and executed
union; §5's field-level comparison; §7's negative results.

**Blockers.**
(a) **Merge execution is human-only** (GOV-03; GOV-04 delegates only to a designated human
operator). `main` has not advanced past `#722`.
(b) `686 × 724` needs an order: **#724 then #686** (mechanical).
(c) `689 × 728` needs a **design decision**: where the browser-smoke verdict lives. Do not merge
both unreconciled.
(d) Branch protection and rulesets are absent; enabling them is a governance decision.
(e) CE-01, FINDING F-01, the `/api/webhook/github` anonymous surface, and
`scripts/prism_coherence_check.py`'s scope remain reserved.

**Authorized next action.** Human review of the queue, using §4's order and §5's decision. An
agent may keep maintaining its own drafts and recording cycles; it must not merge, push to `main`,
deploy, or open a PR for a defect another open PR already owns.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; resolving `689 × 728` by
picking a side without a stated design decision; weakening a guard to manufacture green; opening a
PR with no measured, unowned defect.

**Completion condition.** This cycle is complete when this record is reviewable, `main` is
unmodified, the three conflicts and their dispositions are stated, and no merge, deployment or
acceptance is claimed.
