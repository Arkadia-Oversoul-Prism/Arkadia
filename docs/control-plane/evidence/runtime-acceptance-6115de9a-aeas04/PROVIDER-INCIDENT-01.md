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
