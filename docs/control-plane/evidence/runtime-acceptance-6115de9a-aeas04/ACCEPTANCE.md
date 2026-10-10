# AEAS-04 — Runtime reconciliation & acceptance pass at revision `6115de9a4731b9a6e05696864b904c3b0050769a`

Read-only acceptance pass on the canonical deployment, performed after PR #409 merged.
Every claim is either **observed** from live runtime / GitHub API / a dispatched workflow, or
explicitly marked `NOT TESTED`, `UNKNOWN`, `BLOCKED`, or `NOT CLAIMED`. No secret value is
reproduced. Governing rule: *where evidence stops, claim stops.*

This record **supersedes** the revision scope of
`docs/control-plane/evidence/runtime-acceptance-b58408ef-01/ACCEPTANCE.md`: that pass measured
`b58408ef`; `main` has since advanced to `6115de9a` and the live runtime moved with it. The
prior record is retained as history, not deleted.

## 0. What changed since the inherited baseline

| Inherited claim | Current measured state | Evidence |
| --- | --- | --- |
| PR #409 is a **draft**, head `2ecee949`, acceptance pending | PR #409 is **MERGED**; merge commit `6115de9a` = current `main`; head `fad8b8f0`; merged 2026-10-10T20:23:29Z | `GET /repos/.../pulls/409` |
| "main" SHA `17b931b4…` (older snapshot) | `main` = `6115de9a4731b9a6e05696864b904c3b0050769a` | `GET /commits/main`, `git rev-parse HEAD` |
| Zero open PRs (snapshot) | Zero open PRs (re-measured) | `GET /pulls?state=open` → `[]` |
| Live revision `b58408ef` | Live revision `6115de9a…` (== `main`), `revision_source=RENDER_GIT_COMMIT`, `revision_conflict=false` | `GET /api/version` |

The inherited "PR #409 pending" baseline is **stale**; the PR merged before this pass.

## 1. Repository identity and revision

| Item | Value | State |
| --- | --- | --- |
| Repository | `https://github.com/Arkadia-Oversoul-Prism/Arkadia` | VERIFIED |
| Branch | `main` | VERIFIED |
| HEAD (full) | `6115de9a4731b9a6e05696864b904c3b0050769a` | VERIFIED |
| Working tree | clean (`git status --porcelain` empty at start) | VERIFIED |
| Open PRs | 0 | VERIFIED |

## 2. Canonical deployment

Render is the canonical production backend (ADR-016, one reconciled deployment). The Vercel
retirement is implemented in the repository: root `vercel.json` was removed at `5a292e11`
(2026-10-10) and legacy configs are archived under `archive/deployment/vercel/`. No active
root Vercel config remains.

| Item | Value | State |
| --- | --- | --- |
| Canonical origin | `https://arkadia-qzu4.onrender.com` | VERIFIED |
| Render service id | `srv-db49jbh42hec73aj84qg` | VERIFIED (reconciliation-02 record) |
| Live `source_revision` | `6115de9a4731b9a6e05696864b904c3b0050769a` | OBSERVED (`GET /api/version`) |
| Source↔runtime consistency | `main` == live revision, `revision_conflict=false` | VERIFIED |
| SPA serving | root returns `200 text/html`, title `ARKADIA OVERSOUL PRISM`, bundle `assets/index-BzLymmg4.js` | OBSERVED |
| `/health` | `200 {"status":"radiant","path":"/health"}` | OBSERVED |
| `/api/health` | `404 {"detail":"Route not found"}` — never a backend route | OBSERVED |

Revision identity is necessary but **not sufficient** evidence of correct behaviour; the
endpoint states this itself in `verification_note`.

## 3. Fresh route inventory and authorization probes at `6115de9a`

Source: dispatched workflow `canonical-render-runtime-probe.yml`, run **`38085968670`**
(head `6115de9a`, success), artifact `11681892457`,
`production-route-inventory.json`, captured `2026-10-10T21:00:46Z`.

| Metric | Value | State |
| --- | --- | --- |
| Deployed OpenAPI paths / operations | 288 / 331 | OBSERVED |
| Source↔runtime exact method+path matches | 331 / 331 | OBSERVED |
| Runtime operations without a source match | 0 | OBSERVED |
| Source declarations without a runtime match | 0 | OBSERVED |
| `securitySchemes` / per-operation `security` declared | none | OBSERVED |

Authorization (live probes, same artifact):

| Probe | Result | State |
| --- | --- | --- |
| Anonymous → `/api/operator/security-verification` | `401` | OBSERVED |
| Malformed bearer → same route | `401` | OBSERVED |
| Anonymous → `/api/lab/engineering/overview` (direct probe, this pass) | `401 Authentication required` | OBSERVED |
| Valid low-privilege identity (401 vs 403) | `not_tested` (`ARKADIA_PROBE_LOW_PRIVILEGE_BEARER` unset) | NOT TESTED |

## 4. Product surfaces

Two independent browser observations, both at the current revision.

### 4.1 Canonical browser smoke — VERIFIED at `6115de9a`

Dispatched `canonical-render-browser-smoke.yml` at `ref=main`; run **`38085325263`**
(head `6115de9a`, `completed/success`), artifact `11681776743`. The harness launches headless
Chromium, visits each route, and **fails the job** on any non-2xx, empty body, console error,
page error, or navigation error.

| Route | Status | Body chars | Console err | Page err |
| --- | --- | --- | --- | --- |
| `/` | 200 | 1897 | 0 | 0 |
| `/solariun` | 200 | 115 | 0 | 0 |
| `/oracle` | 200 | 180 | 0 | 0 |
| `/solariun/engineering-lab` | 200 | 115 | 0 | 0 |
| `/operator` | 200 | 4012 | 0 | 0 |
| `/n-atlas-lab` | 200 | 443 | 0 | 0 |
| `/n-atlas-tester` | 200 | 443 | 0 | 0 |

Result: **PASS**. This closes the previously-observed browser-acceptance gap: the last browser
smoke before this pass ran at `07834232` (2026-10-10T15:16Z), i.e. **no browser observation
existed at `6115de9a`** until this dispatch (the merge touched no path-filtered trigger, so no
run fired automatically).

### 4.2 Independent agent-browser observation — PARTIAL

An independent browser session (Playwright-backed agent tool) loaded the canonical origin:
`/` rendered the ARKADIA front page with the same hidden-chrome nav model found in the
earlier pass (`*` menu + `Enter Arkadia`), **no login wall**, and `/oracle` rendered the Arkana
chat surface (input present, "Guest session").

| Check | Result | State |
| --- | --- | --- |
| `/` renders, no login wall | OBSERVED | VERIFIED |
| `/oracle` renders chat surface | OBSERVED | VERIFIED |
| Oracle backend reply path | `POST /api/commune/resonance` → `200`, full markdown reply, `rag_hits 3`, `resonance 0.86` | VERIFIED |
| Interactive UI send via agent browser | **NOT TESTED** — the agent browser could not reliably drive the React controlled textarea (typing staged text; no submission registered). This is a **tooling limitation**, not a product defect. | NOT TESTED |

No freeze was reproduced on `/oracle`: the page loaded, the input accepted text, and the
backend reply path returns within ~7 s. The previously-reported Arkana/Oracle freeze was **not**
reproduced in this session (surface loads clean). A full interactive-send walkthrough remains
for the human/browser-smoke harness, which does not exercise form submission either.

`RUNTIME_BROWSER_VERIFICATION = AVAILABLE` (route render + backend); interactive form
submission via the agent tool = **UNAVAILABLE**.

## 5. N-ATLAS provider acceptance

### 5.1 Effective configuration (secret-free)

`GET /api/lab/engineering/n-atlas/catalog` →
`status: AVAILABLE`, `configured: true`, `detail: "protocol=gradio; reachable via /models"`,
`model: N-ATLaS`. State: **VERIFIED**. `HF_TOKEN` is **not required** for this public Space
(verified in the prior pass); it remains optional hardening only.

### 5.2 Genuine governed inference at the current revision — VERIFIED

One governed inference was executed in this pass through the canonical deployed route
(`POST …/n-atlas/test-session` → `POST …/n-atlas/run`), 2026-10-10T20:49:48Z, using the
canonical English beta prompt:

> "Respond briefly: What is the purpose of evidence in a governed AI workflow?"

| Field | Value |
| --- | --- |
| session | `SES-537520ff65f0` (state `AUTHORIZED`) |
| authorization | `AUTH-d491e4be0837` (scope `n_atlas:run`, 30 min) |
| run | `RUN-766769015520` |
| provider / model | `n_atlas` / `N-ATLaS` |
| response | real text (211 chars), `response_sha256 f82de127ca5268a5368dca2d8c431ba038618afbb51943fdda23998323f743b3` |
| prompt_sha256 | `cbde4c54bf982a947662faa5130f9f9a0199ccddb34c805365980ff6180f2f7e` |
| evaluation | `{non_empty_response, passed: true}` |
| evidence | `EVD-e2203f62d506`, state `IMPLEMENTED`, `run_ref = RUN-766769015520` |
| usage | `protocol gradio`, `endpoint /gradio_api/call/generate`, `event_id 3b33b2123deb4d4f9a7f8ed0e1f04d50`, `sse_events ["complete"]` |

**Cross-validation.** `response_sha256 f82de127…` is **byte-identical** to (a) the CI
external-beta evidence for the same prompt (`n-atlas-external-beta.yml`, run `38080315731`) and
(b) the prior canonical-runtime run `RUN-78944dd8c3dd` / `EVD-a46a79ffb52f`. Three independent
executions — CI harness, prior canonical run, and this run — received the same model output for
the same prompt. The governed chain `RUN → INSPECT → EVALUATE → EVIDENCE → VERIFY` completes on
the canonical runtime at `6115de9a`.

**Temporal validity (superseding observation).** Later in the same pass (~21:10–21:22Z) the
provider began emitting `event: error` / `data: null` for every invocation and the canonical
route returned **503 BLOCKED** with no evidence written. The inference above is a *true
observation at 20:49Z*, but its **current validity is STALE** while the provider errors persist.
The provider runs on `zero-a10g` (ZeroGPU, shared/time-sliced); see
`PROVIDER-INCIDENT-01.md` in this directory for the full timeline, the (unbroken) request
contract, the provider runtime state, and the honest-degradation confirmation. **The canonical
route does not fabricate success during the outage.**

### 5.3 N-ATLAS acceptance requirements

The documented external acceptance contract (`docs/submission/NAIC-2026-PS1-BETA-VALIDATION.md`)
requires **two independent human testers** (records A and B), each run by a different real
person, kept **OPEN** until both are independently reviewed.

| Requirement | State |
| --- | --- |
| Truthful catalog / effective configuration | VERIFIED |
| Genuine inference + execution→evaluation→evidence correlation | VERIFIED (canonical route + CI) |
| Single-user tester flow usable | VERIFIED (route renders; governed run succeeds) |
| Human tester A | **MISSING** — BLOCKED (human) |
| Human tester B | **MISSING** — BLOCKED (human) |
| PS1 external human-beta criterion | **NOT PROVEN** — BLOCKED (human) |

A successful inference establishes one genuine execution; it does **not** satisfy the
two-independent-human-tester criterion. That boundary is human-gated and remains open.

## 6. Security boundary — key-management mutation surface

`api/key_routes.py` guards its write endpoints only via `_get_current_user`. `api/auth.py`
`get_current_user` is an *optional* dependency that **returns `None`** (never raises) for an
anonymous caller, so the `if not user_id:` fallbacks that mutate the process-global key stores
are reachable without authentication.

**Runtime-observed in this pass** (anonymous, invalid input so **no write occurred**):

| Request (no `Authorization` header) | Response | Interpretation |
| --- | --- | --- |
| `POST /api/provider-keys` `{"provider":"__aeas04_probe__","key":"x"}` | `400 {"detail":"Unknown provider: __aeas04_probe__"}` | handler executed; provider validated → **no write** |
| `POST /api/keys` `{"key":""}` | `400 {"detail":"'key' is required"}` | handler executed; empty key rejected → **no write** |
| `POST /api/tts/keys` `{"key":""}` | `400 {"detail":"'key' is required"}` | handler executed; empty key rejected → **no write** |
| (control) `GET /api/lab/engineering/overview` | `401 Authentication required` | protected route rejects anonymous |

A `400` (input validation) rather than `401` (unauthenticated) proves the request reached the
handler body **without authentication**. With a *valid* provider name and a non-empty key, the
same anonymous path would call `provider_key_store.set_key` / `key_manager.add_key`. This is now
**runtime-OBSERVED that anonymous callers reach the mutation handlers**; the write effect itself
is **NOT TESTED** (no production credential was mutated).

The three hand-written guards that *do* protect routes here are `require_auth`,
`require_sovereign` (`api/auth.py`) and `require_lab_auth` (`api/lab_routes.py`); `key_routes.py`
uses none of them on its write paths.

**Classification:** a genuine authorization gap on an authority surface. Repairing it edits
authentication/authorization behaviour → **sovereign-gated** (mission §16.2/§16.6). Recorded as
a proposed bounded follow-up; **not repaired here**.

## 7. Engineering Lab / Weaver / AEAS

| Stage | Capability | State |
| --- | --- | --- |
| Identity / workspace / session | `runtime.open_session`, `register_agent` | EXISTS (exercised in §5.2) |
| Authorization | `record_authorization` (scope + duration) | EXISTS (`AUTH-d491e4be0837`) |
| Proposal / Run | `AgentRun`, event stream `RUN_STARTED … RUN_FINISHED` | EXISTS (`RUN-766769015520`) |
| Execution | provider gateway (`n_atlas` gradio adapter) | EXISTS (genuine response) |
| Work-event → Evidence | `EvidenceRecord`, `run_ref` correlation | EXISTS (`EVD-e2203f62d506`) |
| Evaluation / Verification | `non_empty_response` evaluation, `VERIFYING` state | EXISTS (`passed: true`) |
| Fixed test debt | `tests/test_engineering_lab_api.py` pins the pre-`n-atlas` mutating set and `require_auth` on the router | PRE_EXISTING drift (2 failures, §8) |

A full governance chain `IDENTITY → AUTHORITY → AUTHORIZATION → RUN → EVIDENCE →
VERIFICATION` was demonstrated end-to-end on the canonical runtime within this pass (via the
N-ATLAS governed route), with a traceable run/evidence identifier pair.

## 8. Test results (same environment)

Measured at `6115de9a`:

| Command | Result | Classification |
| --- | --- | --- |
| `pytest tests/test_solspire_route_composition.py tests/test_solspire_route_composition_ci_wiring.py tests/test_boot_syntax_boundary.py -q -rEf` | **30 passed** | PASS |
| `pytest tests/test_natlas_developer_lab.py tests/test_engineering_lab_api.py -q -rEf` | **11 passed, 1 skipped, 2 failed** | 2 failures **PRE_EXISTING / NON_BLOCKING** |

The 2 failures are the documented **unowned drift** (AGENTS.md "Baseline-fingerprint guard"
section): `test_lab_router_is_read_only_and_authenticated` and
`test_lab_mutation_endpoints_are_exactly_the_lab_state_set` pin the *pre*-`n-atlas` Lab route
set and `require_auth` on the router, and were broken by the new `/api/lab/engineering/n-atlas/*`
endpoints (`72432353`) and `require_auth` → `require_lab_auth` (`f96d5fd2`, PR #353). Repairing
them edits `api/lab_routes.py`, an authority surface carrying the Lab mutation boundary →
sovereign-gated. Not repaired here.

No new test suite was added; the existing canonical harnesses (`canonical-render-browser-smoke`,
`canonical-render-runtime-probe`, the route-composition contract) were used.

## 9. Acceptance states (summary)

| Finding | State |
| --- | --- |
| Source revision → live revision consistency (`6115de9a` = `6115de9a`) | VERIFIED |
| Route composition at current revision (331/331, 0 unmatched) | VERIFIED |
| Canonical SPA serving (7 routes, 0 console/page errors) | VERIFIED |
| Browser observation at the current revision | VERIFIED (run `38085325263`) |
| Arkana/Oracle freeze reproduction | NOT REPRODUCED (surface loads clean) |
| Oracle backend reply path | VERIFIED (`/api/commune/resonance` 200) |
| Oracle interactive send via agent browser | NOT TESTED (tooling) |
| Effective N-ATLAS provider configuration | VERIFIED (AVAILABLE) |
| N-ATLAS genuine governed inference at current revision | VERIFIED (`RUN-766769015520` → `EVD-e2203f62d506`) |
| N-ATLAS two-human-tester acceptance criterion | BLOCKED (human) |
| Anonymous → protected routes rejected | OBSERVED (401) |
| Low-privilege authenticated rejection (401 vs 403) | NOT TESTED |
| Anonymous reaches key-mutation handlers | OBSERVED (runtime, no write) |
| Anonymous write effect on key stores | NOT TESTED |
| Vercel public alias retired as product default | VERIFIED (config removed `5a292e11`) |
| Production acceptance | NOT CLAIMED |

## 10. Reproduction commands

```bash
# revision truth
curl -s https://arkadia-qzu4.onrender.com/api/version
curl -s https://arkadia-qzu4.onrender.com/health

# browser acceptance at the current revision
gh workflow run canonical-render-browser-smoke.yml --ref main

# fresh route inventory + auth probes
gh workflow run canonical-render-runtime-probe.yml --ref main

# genuine governed N-ATLAS inference (canonical prompt)
SESS=$(curl -s -X POST https://arkadia-qzu4.onrender.com/api/lab/engineering/n-atlas/test-session)
SID=$(echo "$SESS" | python3 -c 'import sys,json;print(json.load(sys.stdin)["session_id"])')
TOK=$(echo "$SESS" | python3 -c 'import sys,json;print(json.load(sys.stdin)["tester_token"])')
curl -s -X POST https://arkadia-qzu4.onrender.com/api/lab/engineering/n-atlas/run \
  -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"prompt\":\"Respond briefly: What is the purpose of evidence in a governed AI workflow?\"}"

# key-mutation boundary (non-mutating inputs; no write)
curl -s -X POST https://arkadia-qzu4.onrender.com/api/provider-keys \
  -H 'Content-Type: application/json' -d '{"provider":"__aeas04_probe__","key":"x"}'
```

## 11. Boundaries not claimed

- No merge, deployment, production-configuration change, credential mutation, or restart was
  performed by the agent in this pass. The N-ATLAS configuration referenced in §5.1 was applied
  by the operator in the prior pass.
- No secret value was printed, returned, copied, or committed; only allowlisted metadata is
  recorded.
- Two-human-tester N-ATLAS acceptance and any authoritative authorization repair are
  human/sovereign-gated and remain open.
- **Production acceptance is NOT CLAIMED.** An accepted N-ATLAS inference does not imply
  acceptance of the Arkadia product.
