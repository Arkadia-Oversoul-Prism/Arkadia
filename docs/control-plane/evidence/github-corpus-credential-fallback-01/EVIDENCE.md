# A refused GitHub credential breaks a public corpus read — and is reported as "authenticated"

Contract: ARK-OPS-CONTINUOUS-001 (revision 2026-11-22).
Cycle: 2026-11-23, observation window 06:06–06:45 UTC.
Authority: read-only production probes, repository change on an isolated branch.
No merge, no deployment, no acceptance is claimed.

## 1. Starting state (measured, not inherited)

| Fact | Value |
|---|---|
| `main` at cycle start | `bb19aabda34d59594615b0279a45e9cbd3d8204d` |
| `origin/main` | identical (no drift) |
| Clone | full (`--is-shallow-repository` → `false`) |
| Open PRs | 24, all drafts; all `MERGEABLE`; 5 `UNSTABLE` |
| CI on `bb19aabd` | `Full-history secret scan`, `boot-syntax`, `console-contract`, `engineering-scheduler`, `posture-currency`, `test` → success; `weaver_evolution` → skipped |
| Canonical runtime | `GET /api/version` → `source_revision = bb19aabd…`, `revision_conflict: false`, `revision_source: RENDER_GIT_COMMIT` |

Production `/api/version` matching `main` is necessary evidence of source↔runtime
consistency. It is **not** proof of correct application behaviour and is not acceptance.

The 5 `UNSTABLE` PRs fail only on the external N-ATLAS provider
(`beta-beta-01/02`, `bundle-beta-evidence`, `native-arkadia-golden-workflow`), for
example `RUN_FAILED … "external runtime did not return usable inference"`. Those are
provider/environment outcomes, not evidence about the tree, and are not attributable
to those PRs.

## 2. Defect (observed)

A read-only sweep of every parameterless `GET` route in the deployed
`/openapi.json` (101 probeable routes: 37×200, 56×401, 3×403, 4×422, **1×502**)
found one server error:

```
GET https://arkadia-qzu4.onrender.com/api/codex/github-tree      → 502
{"error":"Client error '401 Unauthorized' for url
 'https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/git/trees/main?recursive=1'"}
```

The same deployment reported:

```
GET /api/codex    → {"status":"radiant","total_docs":719,"live_docs":719,
                     "scrolls":{"…":{"source":"local", …}}}
GET /api/sources  → {"name":"github","configured":true,"authenticated":true,"live":false, …}
```

So the public Spiral Codex was serving its **local snapshot**, `live: false`, while
the API described the credential as `authenticated: true`. `authenticated` was
computed as `bool(GITHUB_TOKEN)` — the credential's **presence**, not its acceptance.

## 3. Root cause (isolated by control)

| Probe | Result |
|---|---|
| `GET api.github.com/.../git/trees/main` with `Authorization: Bearer not-a-real-token` | **401** |
| same URL with no `Authorization` header | **200** |
| `GET raw.githubusercontent.com/.../README.md` with the bogus token | **404** |
| same raw URL with no header | **200** |

The deployment's `GITHUB_PERSONAL_ACCESS_TOKEN` is refused (401 on the API host,
404 on the raw host), and both helpers sent it unconditionally:

* `_fetch_github_tree` → `raise_for_status()` → the route returned 502;
* `_fetch_raw` → caught per file, so every corpus document failed and the cache fell
  back to `_build_local_scrolls()`.

The corpus is **public data**: anonymous reads of this repository succeed (verified
above). The credential is a rate-limit optimisation, not an authorization
requirement, so a refused credential must degrade instead of failing.

## 4. Repair (bounded)

* New `api/github_corpus.py` — the single GitHub read client:
  - treats `401/403/404` **with a credential attached** as "refused, retry
    anonymously" (404 is included because `raw.githubusercontent.com` answers 404,
    not 401, for a refused token — measured above);
  - remembers a refusal for the process lifetime, so the corpus's ~700 reads do not
    each repeat a doomed request;
  - never logs or raises the token value;
  - exposes `credential_state()` → `absent | unknown | accepted | rejected`.
* `api/main.py` (2597 → **2593** lines, budget 2600): `GH_HEADERS`,
  `_fetch_github_tree` and `_fetch_raw` delegate to the shared client, and
  `/api/sources` reports `authenticated: credential == "accepted"` plus
  `credential_state`. The write path (`_push_image_to_github`) still presents the
  configured token: a forge push genuinely requires it.
* `web/arkadia_console/src/pages/SettingsPage.tsx` renders the observed state
  (`not configured` / `credential rejected` / `authenticated` / `configured`)
  instead of inferring "authenticated" from the presence of a key.

## 5. Verification

### 5.1 Live, against the real GitHub API with a rejected token

```
GITHUB_PERSONAL_ACCESS_TOKEN=not-a-real-token python - <<'PY' …
GitHub refused the configured credential (401); reading … anonymously
entries: 3209
credential_state: rejected
raw_chars: 5874 | starts: # ARKADIA OVERSOUL PRISM
PY
```

The tree and a raw document both succeed anonymously. The warning names the status
and URL; the token does not appear in it.

### 5.2 Regression suite — `tests/test_github_corpus_credential_fallback.py` (9 tests)

| Node | Property |
|---|---|
| `test_refused_credential_degrades_to_an_anonymous_read` | 401 + credential → anonymous retry → payload returned, state `rejected` |
| `test_negative_control_without_the_retry_the_same_refusal_fails` | with `anonymous_retry=False` the same transport raises 401 — the degradation is what makes the first test pass |
| `test_raw_host_refusal_is_a_404_not_a_401` | the raw host's 404 refusal is also recovered |
| `test_absent_credential_sends_no_authorization_header` | no token → no header, state `absent` |
| `test_a_remembered_refusal_is_not_re_sent` | second read sends no credential (3 requests total, not 4) |
| `test_a_failed_anonymous_read_never_echoes_the_token` | both attempts refused → the error text contains no token |
| `test_accepted_credential_is_reported_accepted` | a working credential reports `accepted` |
| `test_api_sources_reports_the_observed_credential_not_its_presence` | `/api/sources` says `authenticated: false`, `credential_state: "rejected"` |
| `test_main_delegates_its_corpus_reads_to_the_shared_client` | wiring guard: `main.py` must call the shared client |

Live negative control (disable the degradation at its definition —
`_refused()` → `return False`): **3 failed, 6 passed**; restore byte-identically
(`diff -q` clean) → **9 passed**.

### 5.3 Adjacent suites

| Command | Result |
|---|---|
| `python -m py_compile api/main.py api/github_corpus.py` | OK |
| `pytest tests/test_corpus_cache_coordination.py tests/architecture -q` | 15 passed (includes the 2600-line budget) |
| `python scripts/console_contract_domain.py` → `pytest … -q` | 2 failed, 1282 passed, 4 skipped |
| `pnpm exec tsc --noEmit` (console) | exit 0 |
| `pnpm exec vite build` (console) | exit 0, `dist/assets/index-g2hEachE.js` 425.20 kB |
| `python scripts/cp10_mutation_boundary_policy.py --judge` on the 4 new paths | PASS |

The 2 console-domain failures are `tests/test_prism_w4_lab_pr_state.py` and are an
**environment** artifact: they fail only when a `GH_TOKEN` is exported in the shell
(measured: 19 passed with `env -u GH_TOKEN`, 2 failed with `GH_TOKEN=x`). Open PR #683
enforces that no-token premise. They are not caused by this change and are not
repaired here.

## 6. Baseline attribution

Full suite, same environment, `-rEf --continue-on-collection-errors`:

| Tree | Result |
|---|---|
| `main` `bb19aabd` (before the change) | 19 failed, 4250 passed, 22 skipped, 1 error |
| this branch | recorded below |

Of those 19 nodes, **10** (`tests/test_mission_lifecycle_adapter_contract.py`) were
environment-only: they require the repository TypeScript compiler at
`web/arkadia_console/node_modules/typescript/lib/typescript.js`. After
`pnpm install --frozen-lockfile`, that module is **10 passed**. The remaining 9 are
each owned by an open PR (`#690` ×2, `#691`, `#693` ×2, `#698`, `#700` ×2) or are the
deliberate, sovereign-reserved proxy invalidation
`tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate`.
The 1 error is the sovereign-reserved CE-01 `weaver.autonomy` module/package collision.

No failing node is introduced by this change; the branch's failing set is the
`main` set minus the 10 environment nodes.

## 7. Limitations (explicitly not claimed)

* The deployment's credential is still refused. This change makes the public read
  survive that refusal; it does not repair the operator-owned secret. Rotating or
  removing `GITHUB_PERSONAL_ACCESS_TOKEN` in Render remains a sovereign/provider action.
* Production still serves `bb19aabd`-era code: the repair reaches production only
  after a human merges this PR **and** Render deploys. No parity is claimed.
* `credential_state` is process-local and resets on restart, which is correct: the
  env value cannot change without one.
* No merge, deployment, ruleset, or acceptance is claimed by this document.

## 8. Next authorized action

Human review of this PR. If merged, the next cycle should re-probe
`/api/codex/github-tree` and `/api/sources` on the deployed revision and record the
observed `credential_state`, then continue the boundary pulse from the first
unresolved item.
