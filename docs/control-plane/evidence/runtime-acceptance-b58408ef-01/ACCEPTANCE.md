# Evidence-driven acceptance pass — revision `b58408ef043cabbdbd7e20884b2404298ea7477b`

Read-only acceptance pass on the current canonical deployment. Every claim below is either
**observed** from the live runtime / GitHub API or explicitly marked `NOT TESTED`,
`UNKNOWN`, `BLOCKED`, or `NOT CLAIMED`. No secret value is reproduced; only mask-derived,
allowlisted metadata is recorded.

- Canonical origin: `https://arkadia-qzu4.onrender.com`
- Canonical deployment revision (live `GET /api/version`): `b58408ef043cabbdbd7e20884b2404298ea7477b`
- `origin/main` at measurement: `b58408ef043cabbdbd7e20884b2404298ea7477b`
- PR #408 (`acceptance/route-composition-01`) is **merged**; merge commit `b58408ef`.
  The guard correction in this pass is a follow-on on the same guard file.

## 1. Revision truth and deployment

| Item | Value | State |
| --- | --- | --- |
| `origin/main` | `b58408ef043cabbdbd7e20884b2404298ea7477b` | VERIFIED |
| Live `/api/version` `source_revision` | `b58408ef043cabbdbd7e20884b2404298ea7477b` | VERIFIED |
| `revision_source` | `RENDER_GIT_COMMIT` | VERIFIED |
| `revision_conflict` | `false` | VERIFIED |
| `ARKADIA_SOURCE_REVISION` | `absent` | VERIFIED (single source, no disagreement) |

Revision metadata is necessary evidence of source-to-runtime consistency. It is **not**
proof of correct application behaviour and is **not** deployment acceptance (the endpoint
states this itself in `verification_note`). Deployment metadata and the live response are
kept as separate evidence sources.

## 2. Fresh route inventory at the current revision

Re-measured **at `b58408ef`**, not inherited from the earlier `c8abb28e` pass. Source: workflow
`canonical-render-runtime-probe.yml`, run `38079749751` (head `b58408ef`, success), artifact
`11679946596`, file `production-route-inventory.json`, sha256
`c5365ee14ff24ea06eab7ad59ff6931a75d3189bf99929a72828830a6643002b`.

| Metric | Value | State |
| --- | --- | --- |
| Deployed OpenAPI paths / operations | 288 / 331 | OBSERVED |
| Source-to-runtime exact method+path matches | 331 / 331 | OBSERVED |
| Runtime operations without a source match | 0 | OBSERVED |
| Source declarations without a runtime match | 0 | OBSERVED |
| EDEN-OPS-02 composed routes present | yes (`console_router` subset) | OBSERVED |
| `securitySchemes` / `security` declared | none across all 331 operations | OBSERVED |

The deployed OpenAPI declares **no** authorization metadata, so it cannot serve as an
authorization oracle. Authorization behaviour is established only by live probes (Section 6).

## 3. Effective provider configuration — allowlisted, secret-free

Obtained from runtime descriptors, never from repository defaults or the mere existence of
environment-variable names.

| Source | Field | Value | State |
| --- | --- | --- | --- |
| `GET /api/lab/engineering/n-atlas/catalog` | `descriptor.status` | `UNCONFIGURED` | OBSERVED |
| same | `descriptor.configured` | `false` | OBSERVED |
| same | `descriptor.detail` | `N_ATLAS_BASE_URL is not configured` | OBSERVED |
| same | `descriptor.model` | `N-ATLaS` | OBSERVED |
| `GET /api/tts/status` | `engine` / `preferred_engine` | `edge_tts` | OBSERVED |
| `GET /api/keys/pool` | Gemini pool size / available | `1` / `1` | OBSERVED |

The running service's **effective N-ATLAS provider is unconfigured**. The configured model
identifier for other Lab providers is recorded from source
(`lab/engineering_lab/gateway.py`, `_MODEL_REFS`: gemini `gemini-2.0-flash`, openai
`gpt-4o-mini`, claude `claude-3-5-sonnet-20241022`, deepseek `deepseek-chat`, n_atlas
`N-ATLaS`) and is a **source-level** fact, not a runtime observation of an active call.

### 3.1 The live N-ATLAS endpoint exists and is public; only the Render env var is missing

The intended endpoint is documented in-repo (`.github/workflows/n-atlas-external-beta.yml`):
`https://koladeodunope-ednai-natlas-runtime.hf.space`, called via the Gradio SSE contract
`/gradio_api/call/generate`. Read-only probes:

| Probe | Result | State |
| --- | --- | --- |
| `GET https://koladeodunope-ednai-natlas-runtime.hf.space/openapi.json` | `200` | OBSERVED |
| `GET .../gradio_api/info` | `200` | OBSERVED |

The Space is reachable and public (no `Authorization` required), so the gap between the
`UNCONFIGURED` live descriptor and the working CI job is a **Render environment-variable
omission**, not a missing capability, adapter, or credential.

`get_gateway().describe("n_atlas")` (`lab/engineering_lab/gateway.py`) returns
`UNCONFIGURED` exactly when `N_ATLAS_BASE_URL` is unset, and `AVAILABLE` when the URL is set
and the 1s reachability probe succeeds, with `N_ATLAS_PROTOCOL=gradio` selecting
`NAtlasGradioAdapter`. Therefore the minimal live configuration is:

| Variable | Intended value | Secret? |
| --- | --- | --- |
| `N_ATLAS_BASE_URL` | `https://koladeodunope-ednai-natlas-runtime.hf.space` | no |
| `N_ATLAS_PROTOCOL` | `gradio` | no |
| `N_ATLAS_MODEL` | `N-ATLaS` (code default; optional) | no |

**`HF_TOKEN` is not required** for this Space: the CI evidence below executed the full
inference with no `HF_TOKEN` set, and the read-only probes returned `200` without a
credential. The Gradio adapter *would* attach `Authorization: Bearer $HF_TOKEN` if the
variable were present, so it remains optional hardening (only if the Space becomes private),
never a committed value.

## 4. N-ATLAS genuine inference — BLOCKED on the canonical runtime, VERIFIED in CI

The golden workflow is `RUN → INSPECT → EVALUATE → EVIDENCE → VERIFY`. A genuine
current-revision inference requires a real provider response — not a fixture, mock, cached
output, or source assertion.

### 4.1 Canonical runtime `/api/lab` path — BLOCKED

| Workflow step | This pass | State |
| --- | --- | --- |
| INSPECT (provider availability) | `descriptor.status = UNCONFIGURED` | OBSERVED |
| RUN | not performed — the gateway `describe("n_atlas")` is not `AVAILABLE`, so the route refuses with `503` before any model call | BLOCKED |
| EVALUATE / EVIDENCE / VERIFY | not reached | BLOCKED |

The canonical runtime cannot complete the chain while `N_ATLAS_BASE_URL` is unset
(Section 3.1). This is the correct governed refusal; it is not a fabricated success.

### 4.2 The same governed chain — VERIFIED via CI against the live Space

The `n-atlas-external-beta.yml` workflow **does** set `N_ATLAS_BASE_URL`,
`N_ATLAS_PROTOCOL=gradio`, `N_ATLAS_MODEL=N-ATLaS` and executes the genuine inference with no
`HF_TOKEN`. Run `38080315731` (head `2ecee949`, **success**), artifacts:

| Artifact | Content | State |
| --- | --- | --- |
| `beta-01-english-evidence` | `status PASS`, `endpoint /gradio_api/call/generate`, `response_sha256 f82de127…`, 240 chars, real English answer | OBSERVED |
| `beta-02-hausa-evidence` | `status PASS`, `response_sha256 905bb3a…`, real Hausa answer | OBSERVED |
| `natlas-native-golden-evidence` | `RUN-80252ac3d7fd` → `EVD-c39db84ef035`, `state IMPLEMENTED`, `provider_status AVAILABLE` | OBSERVED |

The native golden record ties the full chain with agreeing identifiers:

- `run_id = RUN-80252ac3d7fd` == `evidence.run_ref`;
- `prompt_sha256 cbde4c54…` identical across the external-beta and native-golden runs for the
  same prompt;
- `response_sha256 f82de127…` identical across both — the external-beta harness and Arkadia's
  native adapter received byte-identical model output;
- `evaluation {name: non_empty_response, passed: true}`;
- `usage.protocol = gradio`, `event_id`, `sse_events ["complete"]`.

So a genuine N-ATLAS inference **with execution → evaluation → evidence correlation** is
demonstrated for the current deployment lineage. What is *not* yet demonstrated is that same
chain through the **canonical runtime's** `/api/lab` route, which stays BLOCKED pending the
env var. Prior `NATLAS-LAB-001` results are historical and are not substituted.

## 5. Evidence-chain correlation (revision → request → … → evidence)

| Link | Status |
| --- | --- |
| exact revision → request | VERIFIED for the read-only descriptors in Section 3 |
| request → provider/model selection | VERIFIED (Section 3) |
| provider selection → inference result | VERIFIED via CI (Section 4.2); BLOCKED on the canonical runtime (4.1) |
| inference → evaluation | VERIFIED via CI (`passed: true`) |
| evaluation → persisted evidence (`RUN-*` → `EVD-*`) | VERIFIED via CI (`RUN-80252ac3d7fd` → `EVD-c39db84ef035`) |
| same chain through the canonical `/api/lab` route | BLOCKED (provider UNCONFIGURED) |

## 6. Security boundary checks (driven by the Section 2 inventory)

Fresh `authorization_matrix` from the same artifact (`b58408ef`):

| Probe | Result | State |
| --- | --- | --- |
| anonymous, no `Authorization` header | 98 routes → `401`/`403` (`protected`) | OBSERVED |
| malformed bearer (`/api/operator/security-verification`) | `401` | PASSED |
| anonymous reachable GET routes | 40 → non-error response | OBSERVED |
| valid low-privilege identity | `not_tested` (`ARKADIA_PROBE_LOW_PRIVILEGE_BEARER` unset) | NOT TESTED |

The 40 anonymously reachable routes need endpoint-by-endpoint classification: a 2xx is
neither proof of safety nor proof of a defect. A `200` from the root SPA rewrite does not
establish that a route exists.

### 6.1 The four credential-related anonymous endpoints (explicitly adjudicated)

Direct live fetch of the exact endpoints named by the review, no credentials sent:

| Endpoint | HTTP | Disclosed content | Verdict |
| --- | --- | --- | --- |
| `GET /api/keys` | 200 | `id` `b3e82bd3`, `label` "Default (env)", `added_at`, `active`, `quota_hit`, `masked` `AQ.A****FRAA` | metadata + masked prefix/suffix only |
| `GET /api/provider-keys` | 200 | per-provider `source`/`quota_hit`; gemini `label` "Environment variable", `masked` `****env****`; others null | presence metadata only |
| `GET /api/tts/keys` | 200 | `{"keys": []}` | empty |
| `GET /api/keys/pool` | 200 | `size`/`available`/`cooled` | aggregate count only |

Masking is `key[:4] + "****" + key[-4:]` for keys longer than 8 characters, else `****`
(`api/key_manager.py`, `api/provider_key_store.py`, `api/tts_key_manager.py`). The full secret
value is never returned.

**Verdict: no full secret value is disclosed by the three endpoints, and no payload
sensitive beyond masked metadata and configuration state was observed.** Residually
disclosed: (a) a masked Gemini key prefix/suffix (`AQ.A` + `FRAA`), (b) the presence and
labels of a Gemini env key and no other provider key. This is a **configuration-metadata
disclosure** on endpoints intentionally unauthenticated by design (they fall back to the
process-global env key when no user is authenticated). Severity is low; the `AQ.` prefix is
the well-known Google API-key prefix an attacker already knows. Recorded OBSERVED; no secret
exposure verdict beyond this.

### 6.2 Unauthenticated mutation surface (source-level, credential-related)

`api/key_routes.py` guards only via `_get_current_user` and falls back to the
**process-global** store when no user resolves. For an anonymous caller (source observation;
**no mutation was issued** in this pass):

- `POST /api/keys`, `DELETE /api/keys/{key_id}`, `PATCH /api/keys/{key_id}/activate`,
  `PATCH /api/keys/{key_id}/reset-quota` mutate the shared legacy/global key store;
- `POST /api/provider-keys`, `DELETE /api/provider-keys/{provider}`,
  `PATCH /api/provider-keys/{provider}/reset-quota` mutate the shared provider key store.

`GET`-only probing cannot demonstrate an anonymous write; the code path is
**OBSERVED (source)** and the runtime effect is **NOT TESTED**. If confirmed, an
unauthenticated `POST /api/keys` could override the shared env key and force a
denial-of-service — a larger finding than the masked reads. Recorded as a proposed bounded
follow-up (Section 11), not repaired here.

## 7. CI-guard correction (the review's named false positive)

The prior guard decided "this workflow runs the contract" by locating a `pytest` word
anywhere in the tokenised command, so `echo pytest tests/test_solspire_route_composition.py`
was **detected** as an execution. Corrected: `pytest` counts only when it is the invoked
command word (`pytest …` directly, or `python -m pytest …`), and the contract must be an
argument to it.

Measured live on the **real** workflow file (mutated in the working tree, then restored
byte-identically):

| Mutation of `.github/workflows/solspire-route-composition.yml` | Guard result |
| --- | --- |
| executing step's `run` → `echo pytest tests/test_solspire_route_composition.py` | **2 failed** |
| job-level `continue-on-error: true` added | **2 failed** |

The guard is now **24 tests** (was 14): negative controls cover mention-without-execution
(`echo`/`printf`/comment), `pytest`-as-an-argument, a non-pytest command naming the path,
pytest on a different file, missing `workflow_dispatch`, an incomplete `paths` filter,
`continue-on-error` (step and job), and `if: false` (step and job). Positive controls cover
`pytest x`, `python -m pytest x`, `python3 -m pytest x`, `ENV=1 python -m pytest x`,
`env python -m pytest x`, a `file::test` selector, and a directory invocation (`pytest tests/ -q`).

## 8. Regression state (same environment, true baseline)

Measured against clean `main` `b58408ef` in a detached worktree, same environment:

| Tree | Result | Failing/error node set |
| --- | --- | --- |
| `main` `b58408ef` | 79 failed, 1840 passed, 34 skipped, 19 errors | 98 nodes, sha256 `12051eef7c33…` |
| this branch | 79 failed, 1850 passed, 34 skipped, 19 errors | 98 nodes, sha256 `12051eef7c33…` |

The failing/error node sets are **identical**; the `+10 passed` is exactly the guard's new
controls. The `79 failed / 19 errors` are pre-existing repository debt (including the
`weaver.autonomy` module-vs-package collection error) and are **not repaired here**.

Environment note: a few order/network-dependent nodes (e.g.
`test_natlas_developer_lab::test_native_natlas_route_live_external_gradio`) are occasionally
flaky under the full suite but pass in isolation; both trees were measured identically in
this environment, so the comparison is apples-to-apples.

## 9. Acceptance states (summary)

| Finding | State |
| --- | --- |
| Source revision → live revision consistency | VERIFIED (`b58408ef` = `b58408ef`) |
| Route composition, current revision | VERIFIED (331/331, 0 unmatched) |
| OpenAPI as authorization oracle | NOT VALID (no `security` declared) |
| Anonymous → protected routes rejected (98 routes) | OBSERVED |
| Malformed bearer rejected | PASSED (401) |
| Low-privilege authenticated rejection | NOT TESTED |
| Secret non-exposure, three key endpoints | OBSERVED (masked metadata only) |
| Unauthenticated mutation of global key store | NOT TESTED (source path OBSERVED) |
| Effective N-ATLAS provider configuration | OBSERVED (UNCONFIGURED on the canonical runtime) |
| N-ATLAS inference + evidence chain (CI, live Space) | VERIFIED |
| N-ATLAS inference + evidence chain (canonical `/api/lab` route) | BLOCKED (env var unset) |
| Application semantics beyond route composition | NOT CLAIMED |
| Production acceptance | NOT CLAIMED |

## 10. Reproduction commands

```bash
# revision truth
curl -s https://arkadia-qzu4.onrender.com/api/version

# fresh route inventory (dispatch, then download artifact 11679946596)
gh workflow run canonical-render-runtime-probe.yml --ref main

# effective provider configuration (secret-free)
curl -s https://arkadia-qzu4.onrender.com/api/lab/engineering/n-atlas/catalog
curl -s https://arkadia-qzu4.onrender.com/api/tts/status

# credential-related anonymous endpoints (no credentials sent)
curl -s https://arkadia-qzu4.onrender.com/api/keys
curl -s https://arkadia-qzu4.onrender.com/api/provider-keys
curl -s https://arkadia-qzu4.onrender.com/api/tts/keys

# guard + contract, and the live controls
python -m pytest tests/test_solspire_route_composition_ci_wiring.py \
  tests/test_solspire_route_composition.py -q

# N-ATLAS live Space (read-only)
curl -s -o /dev/null -w '%{http_code}\n' https://koladeodunope-ednai-natlas-runtime.hf.space/gradio_api/info

# the CI job that runs the genuine inference + evidence chain
gh workflow run n-atlas-external-beta.yml --ref main
```

## 11. Required follow-up: provision the canonical runtime (human/operator action)

**I did not and cannot perform this step.** This environment has no Render API credential
(`curl https://api.render.com/v1/services` → `401`; no `RENDER_API_KEY`), and the canonical
service is not declared by any `render.yaml` blueprint, so the environment variables are set
in the Render dashboard only. Setting them is a production-configuration change and a
`restart`, which requires the operator.

Exact action for the operator, on the canonical Render service for
`https://arkadia-qzu4.onrender.com`:

1. Add environment variable `N_ATLAS_BASE_URL = https://koladeodunope-ednai-natlas-runtime.hf.space`
2. Add environment variable `N_ATLAS_PROTOCOL = gradio`
3. (optional) `N_ATLAS_MODEL = N-ATLaS`
4. `HF_TOKEN` — **not required** for this public Space; add it only as a secret if the Space
   becomes private, never as a plain value and never committed.
5. Save and let the service restart.

Verification after the restart (do not treat a healthy process as acceptance):

```bash
curl -s https://arkadia-qzu4.onrender.com/api/lab/engineering/n-atlas/catalog
# expect descriptor.status == "AVAILABLE" and configured == true
```

Then run one genuine inference through the canonical route and confirm the returned
`run_id` / `evidence` correlation, per the golden-workflow contract.

## 12. Boundaries not claimed

- No merge, deployment, production-configuration change, or restart was performed.
- The N-ATLAS chain through the canonical `/api/lab` route remains BLOCKED until the env var
  is provisioned (Section 11).
- Low-privilege identity testing remains NOT TESTED (no such credential configured).
- **Proposed follow-up (bounded, not done here):** confirm and remediate the unauthenticated
  mutation surface in `api/key_routes.py` (require user context for write endpoints, or bind
  them to a documented operator token). This changes an authority surface and needs sovereign
  authorization.
