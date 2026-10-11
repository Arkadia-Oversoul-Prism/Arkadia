# N-ATLaS provider incident — ZeroGPU runtime error frames (2026-10-10)

Observed and recorded during the AEAS-04 acceptance pass. This is a **provider-side**
availability event on the public Hugging Face Space used as the N-ATLaS runtime; it is not a
defect in Arkadia's adapter or canonical route, both of which degrade honestly.

Governing rule: *where evidence stops, claim stops.*

## 1. Symptom

The canonical governed route returns HTTP **503** with the adapter's precise provider error:

```
N-ATLaS Gradio runtime error: provider emitted error event with null/empty data
(event_id=935874afd2084dd1bf192735de9bc5c1, raw_data='null', events=['error'])
```

Provider model ref: `NCAIR1/N-ATLaS` (per the Space's own success payload).

## 2. Reproduction — direct against the Space (no Arkadia code)

```bash
SPACE=https://koladeodunope-ednai-natlas-runtime.hf.space
DATA='{"data":["[{\"role\":\"user\",\"content\":\"Respond briefly: What is the purpose of evidence in a governed AI workflow?\"}]",0.0,128,false]}'
EID=$(curl -s -X POST "$SPACE/gradio_api/call/generate" -H 'Content-Type: application/json' -d "$DATA" \
      | python3 -c 'import sys,json;print(json.load(sys.stdin)["event_id"])')
curl -sN "$SPACE/gradio_api/call/generate/$EID" -H 'Accept: text/event-stream'
```

Observed sequence (`2026-10-10`):

| Time (UTC) | Observation |
| --- | --- |
| ~20:49 | one inference **succeeded** — `event: complete`, real answer, `usage.total_tokens 92`, `provider ednai_zerogpu` (this is the `RUN-766769015520` acceptance run) |
| ~21:10 | first `event: error` / `data: null` |
| ~21:12 | 5/5 probes → `event: error` `data: null` |
| ~21:19–21:21 | 6/6 probes over 120 s → `event: error` `data: null` |
| ~21:22 | 17 consecutive error frames total; no successful frame since ~20:49 |

Failure frame body (verbatim):

```
event: error
data: null
```

## 3. Request contract is unchanged (rules out a client/contract break)

`GET $SPACE/gradio_api/info` → `/generate` parameters are exactly the four the adapter sends:

| Param | Type | Default |
| --- | --- | --- |
| `messages_json` | str | `[{"role":"user","content":"What is N-ATLaS?"}]` |
| `temperature` | float | 0.2 |
| `max_tokens` | float | 512 |
| `json_mode` | bool | False |

The **same** request shape returned `complete` at 20:49 and `error/null` later. The protocol
and payload are correct; only the runtime outcome changed.

## 4. Provider runtime state

`GET https://huggingface.co/api/spaces/KoladeOdunope/ednai-natlas-runtime`:

```json
{"id": "KoladeOdunope/ednai-natlas-runtime", "sdk": "gradio", "private": false,
 "runtime": {"stage": "RUNNING", "hardware": {"current": "zero-a10g", "requested": "zero-a10g"},
             "replicas": {"current": 1, "requested": 1}, "gcTimeout": 172800},
 "sha": "b72ca9cfa9d87781b682aa9710df642a3744f177"}
```

The Space is `RUNNING` on **`zero-a10g` (ZeroGPU)** — a shared, time-sliced GPU whose requests
are admitted per-invocation and can be rejected when the shared pool is exhausted or the
quotas/cooldown are in force. The error arrives as a Gradio `error` event with `null` data,
i.e. the provider's own handler rejected/aborted the invocation and passed no detail.

**Root cause: provider-side ZeroGPU availability.** No Arkadia code, credential, or
configuration change caused it.

## 5. Arkadia behaviour is honest (the important finding)

| Layer | Behaviour under the error | Verdict |
| --- | --- | --- |
| `NAtlasGradioAdapter` (`lab/engineering_lab/natlas.py`) | consumes the event type explicitly; an `error` frame is **never** mistaken for text; raises `ModelUnavailable` with the event_id and raw data | CORRECT |
| `/api/lab/engineering/n-atlas/run` | catches `ModelUnavailable`, sets run `BLOCKED`/`result_state=BLOCKED`, emits a `BLOCKED` event, returns **503** | CORRECT |
| Evidence | **no** `EVD-*` is written for a failed run; no fabricated success | CORRECT |
| Canonical route (live) | `503` with the exact detail — reproduced in this pass | OBSERVED |

A failed inference therefore cannot produce a false acceptance record. This is the intended
boundary: *provider failure must never be recorded as success.*

## 6. Observability gap (recorded, not repaired)

`GET /api/lab/engineering/n-atlas/catalog` reports `status: AVAILABLE` throughout the outage,
because the descriptor probe (`gateway._probe_natlas`) only checks static reachability
(`/models` → 200). Reachability does **not** prove an inference can run — exactly the
mission's "configured provider ≠ successful inference" distinction. As of this incident,
`catalog == AVAILABLE` while **every** governed inference returns `503`.

This is a genuine, bounded follow-up: have the catalog/liveness surface reflect a **recent
inference outcome** (or last-error) rather than static reachability alone. It changes Lab
descriptor semantics on an authority surface, so it is recorded here as a proposal and
**not implemented** in this pass.

## 7. Classification

| Aspect | Classification |
| --- | --- |
| Provider error frames | **ENVIRONMENTAL** (external infrastructure) |
| Canonical route 503 behaviour | CORRECT (not a defect) |
| N-ATLAS inference acceptance right now | **BLOCKED** (provider) |
| ZeroGPU availability | **NOT TESTED** (no HF credential; no authenticated runtime logs) |
| Catalog-still-AVAILABLE observability gap | **OBSERVED** — proposed follow-up |

## 8. What is *not* claimed

- No claim that the Space is permanently down; it was working at ~20:49 and may recover.
- No claim of ZeroGPU quota exhaustion as the definitive cause — that requires authenticated
  Space logs, which were not available.
- The earlier `RUN-766769015520` → `EVD-e2203f62d506` verification remains a **true observation
  at 20:49Z**; it is time-bound, not invalidated. Its current validity is **STALE** while the
  provider errors persist.
- No credential was used, printed, or committed.

## 9. Bounded provider-failure investigation (2026-10-10, second pass)

A bounded follow-up asked for one specific event id and a set of questions. Answering them
required locating evidence rather than retrying, and the first answer is negative.

### 9.1 The requested event id does not exist in any retrievable record

`478453e5ab404d018bd5365d477e96b1` appears in **zero** of the surfaces examined:

| Surface | Result |
| --- | --- |
| Working tree (`grep -rn`) | 0 |
| Every git object, all refs (`git grep` over `rev-list --all`, 21,127 objects) | 0 |
| All 63 `n-atlas-provider-forensics` run artifacts | 0 |
| All 20 `n-atlas-external-beta` run artifacts | 0 |
| Local stores (`data/`) | 0 |

**The search method is validated, not assumed.** The same commands locate a *known* id from
the record (`935874afd2084dd1bf192735de9bc5c1`, §1) and a known artifact id
(`e42719e01f814faaa4d91f89317bd9d0`), so the zero is a real absence rather than a broken
query. Gradio `event_id`s are minted per call and are **not** persisted by Arkadia (they live
only in the adapter's `usage` payload and in CI artifacts), so an id quoted outside those
surfaces cannot be correlated here. **This is recorded as an unresolved identifier, not
reconciled by inventing a match.**

### 9.2 The real failure traces — correlated by time

Every recorded failure is the same shape. The three runs whose artifacts carry error frames:

| Run | event_id | Observed at (UTC) | Frames |
| --- | --- | --- | --- |
| `37956291373` | `731760907d3f4290be9bc58ca2f99eb5` | 2026-10-09T16:03:26Z | `error` |
| `38061092379` | `76cfcc0ca31748ce8271044d0588dc64` | 2026-10-10T14:48:59Z | `error` |
| `38089446122` | `b83a31efd4d94016be4b5d22de8d3b19` | 2026-10-10T21:55:34Z | `error` |

Across all 63 forensics runs the frame sequences are: **55 `complete`**, **3 `error`**,
2 `heartbeat`, 2 empty. Success and failure are each a *single* frame, so immediacy alone
does not separate them — **timing does** (§9.3).

### 9.3 The failure is pre-admission, and the mechanism is identified

The sequence around the failure is a single frame and nothing else — **no** queue, admission,
`process_starts` or `generating` event precedes it:

```
submit       : HTTP 200 {"event_id":"0d83272ce74845bd9b7e879c9125e7fc"}
sse_http     : 200 text/event-stream; charset=utf-8
  event='error' data='null'  (+0.1s)
```

Measured three consecutive times: error at **+0.26s / +0.23s / +0.23s**, i.e. ~0.1 s after the
SSE connection opened and far below any inference latency. Meanwhile the provider's own
admission stream is healthy — `stage: RUNNING`, `zero-gpu-count: 0`, `readyReplicas: 1` of
`targetReplicas: 1`, `hardware zero-a10g`, Space sha `b72ca9cf…` unchanged.

The mechanism is in the Space's own source (captured by the forensics harness):

```python
@spaces.GPU(duration=60)
def generate(messages_json, temperature=0.2, max_tokens=512, json_mode=False): ...
...
demo.queue(default_concurrency_limit=1).launch()
```

A `@spaces.GPU`-decorated handler on a **shared, time-sliced ZeroGPU** is admitted
per-invocation; when the shared pool will not grant a slot the invocation is rejected
**before the handler body runs**, and the provider surfaces that as `event: error` /
`data: null` with no detail. This is consistent with every observation: instant rejection,
healthy `stage`, healthy request contract (the same payload shape returned `complete` 55 times).

**Classification: ENVIRONMENTAL — provider-side ZeroGPU admission, not a Space outage and not
an Arkadia defect.** The definitive cause cannot be named without authenticated Space logs
(`HF_TOKEN` is absent from the GitHub secret store), so quota/cooldown attribution stays
**NOT TESTED**.

### 9.4 Persistence: the failure occurred *during* governed execution, after the run was created

The failure does **not** precede governed execution — the run is created first. Driven through
the **real** route with the real adapter and only the storage/runtime/stream seams stubbed:

```
CASE A (event: error / data: null)
  response         : HTTP 503
  detail           : N-ATLaS Gradio runtime error: provider emitted error event with
                     null/empty data (event_id=..., raw_data='null', events=['error'])
  runs created     : 1
  run updates      : [{'state': 'BLOCKED', 'result_state': 'BLOCKED'}]
  EVIDENCE RECORDS : 0        <-- no false PASS
  events           : ['RUN_STARTED', 'BLOCKED']

CASE B (control, event: complete)
  response         : 200 OK, evaluation passed=True
  EVIDENCE RECORDS : 1        state=IMPLEMENTED
  events           : ['RUN_STARTED','MODEL_TURN','EVIDENCE_RECORDED','RUN_FINISHED']
```

So: a **run** is persisted and correctly marked `BLOCKED`; **no `EVD-*` is written**; the
route returns an explicit `503`.

Scope of this claim, stated precisely: it is the route's **`ModelUnavailable` path** that
writes no evidence, and that is what the test pins. A response that *arrives* but fails
evaluation takes the other branch — it writes an `EVD-*` with `state=BLOCKED` (the
`result_state = "IMPLEMENTED" if evaluation["passed"] else "BLOCKED"` line), which is an
evidence record but **not** a false PASS. So the accurate claim is: **no path records a
passing/`IMPLEMENTED` evidence for a failed inference**, not "no path writes evidence at all."

The `catalog == AVAILABLE` gap (§6) is adjacent and unfixed: reachability still does not
reflect inference outcome.

### 9.5 The tester returns to a usable state

The failure path updates the **run** but never transitions the **session**, so the
`AUTHORIZED`/`QUEUED` guard still admits a retry. Proven end to end — fail then succeed on the
**same** `session_id`:

```
attempt 1: HTTP 503  N-ATLaS Gradio runtime error: provider emitted error event with null/empty data
attempt 2: SUCCESS   run=RUN-71c85edd56cf  eval_passed=True
  runs created : 2
  evidence     : 1   (only the successful attempt)
  events       : ['RUN_STARTED','BLOCKED','RUN_STARTED','MODEL_TURN','EVIDENCE_RECORDED','RUN_FINISHED']
```

Explicit error, no false PASS, and the session is reusable.

### 9.6 Gap closed — the boundary was correct but unprotected

Correct behaviour with no test pinning it is one edit away from a fabricated PASS. No test
asserted the failure path, so `tests/test_natlas_developer_lab.py` gained:

- `test_provider_error_frame_never_writes_a_false_pass` — asserts `503`, `store.evidence == []`,
  run `BLOCKED` and never `IMPLEMENTED`, and events exactly `['RUN_STARTED','BLOCKED']`.
- `test_provider_success_still_writes_exactly_one_evidence_record` — **positive control**: the
  same harness must still record a real pass, so the boundary cannot be satisfied by breaking
  the success path.

**Mutation-proven.** Injecting a fabricated `save_evidence(..., state="IMPLEMENTED")` into the
failure path makes the guard fail on exactly its load-bearing assertion
(`AssertionError: a failed provider run wrote an evidence record; a provider failure must
never be recorded as success`), and the source was restored byte-identically (`git diff` empty).

### 9.7 Controlled retry — outcome unchanged

One bounded retry under identical conditions (same prompt, `prompt_sha256 d173365f…`, no
credential): **4 consecutive `error`/`null` frames, zero successes**. The provider remains
unavailable for inference. Retrying cannot convert this to VERIFIED, so it is not repeated.

### 9.8 Status

| Question | Finding |
| --- | --- |
| Event `478453e5…` located | **NOT FOUND** (validated search, 0/21,127 objects, 0/83 artifacts) |
| Failure timestamp correlated | **VERIFIED** — 3 traces, §9.2 |
| SSE sequence around failure | **VERIFIED** — bare `error`/`null` at ~+0.23 s, no queue/admission/processing frames |
| Backend persisted a failed run | **VERIFIED** — run created, `BLOCKED`; no `EVD-*` |
| Failure before governed execution | **NO** — the run is created first; the failure is *inside* execution |
| Tester usable after failure | **VERIFIED** — explicit 503, retry on the same session succeeds |
| No false PASS | **VERIFIED** + now **guarded by test** |
| Root cause | **INFERRED: ENVIRONMENTAL (ZeroGPU admission)** — mechanism identified from the Space's source; the provider's `error`/`null` frame carries no detail, so quota vs cooldown attribution is **NOT TESTED** (§9.9) |
| Controlled retry | **Still failing** (4/4 error frames) |

### 9.9 Admission attribution — investigated separately (quota vs cooldown still NOT TESTED)

Attribution was pursued as its own question, separately from the failure-path work.

**Authorized diagnostic access is not available — checked, not assumed.**

| Channel | Status |
| --- | --- |
| `HF_TOKEN` in the agent environment | **absent** (presence checked; value never read or printed) |
| `HF_TOKEN` as a GitHub Actions secret | **not configured** — every run logs `authenticated_logs_status: skipped_missing_github_secret` and writes `SKIPPED: HF_TOKEN GitHub Actions secret is not configured.` |
| Space public/gated | `private: false`, `gated: false` — no token needed for the **inference** path, only for the **private runtime logs** |

The credential exists on the Space (its `app.py` would `raise RuntimeError` at import without it), but it is not available to this environment or to CI, and the repository's collection API is not readable by this integration. Per the governing rule, **quota vs cooldown attribution therefore remains NOT TESTED.** No authenticated runtime log was read, so no cause beyond the inference-level finding below is claimed.

**What token-free evidence does establish — the failure is intermittent, not an outage.**

This materially sharpens §3. Reading every recorded run's outcome in time order, failures are *isolated single calls interleaved with successes seconds apart*:

| Time (UTC) | Run | Frames |
| --- | --- | --- |
| 2026-10-09T16:03:26.0 | `37956284383` | `complete` |
| 2026-10-09T16:03:26 | `37956291373` | **`error`** |
| 2026-10-09T16:03:34.7 | `37956308404` | `complete` |
| 2026-10-10T21:55:35.1 | `38089446393` | `complete` |
| … | `38089446122` | **`error`** (same minute) |
| 2026-10-11T00:04:23.7 | `38097150267` | `complete` |
| 2026-10-11T00:10:42–00:11 | this pass's probe | **`error` ×6** |

So the same Space served a `complete` and an `error` **within the same second** on 2026-10-09, and served `complete` at 00:04 before rejecting 6/6 at 00:10. Of 64 recorded runs, only **3** error — and each time a neighbouring run succeeded immediately.

**Consequence, stated precisely:** the Space's *declared* state (`stage: RUNNING`, `zero-gpu-count: 0`, `readyReplicas 1/1`) is necessary but **not sufficient** to predict admission. This generalises §6's "reachability ≠ inference" lesson one level further: **a healthy app-level state ≠ a granted GPU slot.** Admission is decided per-invocation by the shared ZeroGPU scheduler.

That is consistent with a shared, time-sliced pool granting or refusing slots per call, and is the same class as the §3 mechanism — but it does **not** distinguish per-user quota exhaustion from a short cooldown, which requires the authenticated logs and remains **NOT TESTED**.

**Recorded follow-up (unchanged, not implemented):** the `catalog == AVAILABLE` observability gap in §6 is now demonstrably load-bearing — the catalog reported `AVAILABLE` throughout, including periods where every inference was refused.

**Retries were bounded, not repeated.** A finding of this shape cannot be converted to VERIFIED by retrying, so probing stopped after this measurement.

**Merged-worker note:** the underlying investigation shipped in PR #412 (`640fa55f`). The claim-scope correction at §9.4 and this section are recorded so the refined attribution is not left only in a pull request.

## 10. Authenticated diagnostics — configuration is a human-only action (2026-10-11)

The refinement requested here is: configure `HF_TOKEN` as a GitHub Actions secret so
`n-atlas-provider-forensics` can read the Space's private runtime logs and settle quota vs
cooldown. **This could not be executed by an agent, and the reason was measured rather than
assumed.** What follows is the boundary, the readiness of the harness, and one defect that
would make the action silently fail.

### 10.1 The blocker: no credential and no secret-write permission

| Required | Status | Evidence |
| --- | --- | --- |
| An `HF_TOKEN` value | **NOT AVAILABLE** | `HF_TOKEN` and `HUGGINGFACE_TOKEN` both absent from the environment (presence checked; no value read or printed) |
| Permission to write the secret | **DENIED** | `gh secret set` → `403 Resource not accessible by integration` (`.../actions/secrets/public-key`); the same 403 blocks reading `.../actions/secrets` |

So this is not a decision to defer; it is a capability that is absent. The secret must be set
by a human with repository-admin rights. **No secret was set, read, printed, or committed.**

### 10.2 The harness needs no change — its contract is verified

`n-atlas-provider-forensics` already passes the token correctly and already fetches the right
endpoints, so the operator's action alone should be sufficient. Verified arms-length, with no
credential:

| Endpoint (as used by the job) | Without a token | Conclusion |
| --- | --- | --- |
| `/api/spaces/<space>/events?tail=100` | **200** | public — the admission signal needs no credential |
| `/api/spaces/<space>/logs/run?tail=300` | **401** `{"error":"Invalid username or password."}` | **this is exactly what the secret unlocks** |

The token is also wired correctly on two counts that matter: it is delivered through
`env: HF_TOKEN: ${{ secrets.HF_TOKEN }}` and referenced as a *quoted* variable inside the
`run:` block — it is **never** interpolated as `${{ secrets.* }}` into shell text, so the
`ADR-013 §1` / workflow-injection class does not apply here. Job permissions are
`contents: read`, which is the correct least privilege for reading a public Space's logs.
`workflow_dispatch` is present, so an operator can trigger it on the exact revision.

### 10.3 The defect that would make the action silently fail — recorded, not repaired

**`get_text()` never checks the HTTP status**, so a token without read access to that Space
would produce a **green job** whose `runtime-logs.txt` contains a 401 error body instead of
logs. The asymmetry is in the same file:

```python
get_stream_bounded(...)   # calls response.raise_for_status()   <- fails loudly
get_text(...)             # never checks status; writes response.text  <- fails silently
```

`get_text` is used for `runtime-logs.txt` (`/logs/run?tail=300`) *and* for the public
`space-metadata.json` / `app.py` / `README.md` fetches. So a blanket `raise_for_status()`
would be a behaviour change with real blast radius, and that is why this is **recorded as a
proposed follow-up rather than patched in this pass** — it edits a CI surface whose
authenticated path cannot be exercised here (no token), so a patch could not be verified.

**Proposed patch (for authorization, not applied):** give `get_text` a `required: bool = False`
parameter; set `required=True` for the authenticated fetches only, so an auth failure is
reported explicitly while the public fetches keep their current tolerance.

Combined effect if left unpatched: an operator could set a token with insufficient scope, see
a passing job and a populated `runtime-logs.txt`, and conclude "no errors in the logs" — a
false negative of exactly the class this repository already guards against elsewhere.

### 10.4 Status

| Item | State |
| --- | --- |
| `HF_TOKEN` secret configured | **NOT DONE** — human-admin action (403 / no value); no secret touched |
| Harness ready for the token | **VERIFIED** (contract + env wiring + dispatch + least privilege) |
| Authenticated runtime logs read | **NO** — 401 without the secret |
| Quota vs cooldown attribution | **NOT TESTED** — unchanged, and left explicit per instruction |
| Silent-failure defect in `get_text` | **OBSERVED** — proposed follow-up, not repaired |



