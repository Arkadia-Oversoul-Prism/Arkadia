# N-ATLaS access differential — GitHub CI succeeds while Render and the sandbox fail (2026-10-10)

Follow-up investigation appended to the AEAS-04 pass, after the operator re-ran the
N-ATLAS external-beta workflow. Governing rule: *where evidence stops, claim stops.*

## 1. The observation that changes the diagnosis

For a period of ~6 minutes the **same** `/generate` request, against the **same** Space, produced
**opposite outcomes depending on who sent it**:

| Client (egress) | Time (UTC) | Result |
| --- | --- | --- |
| GitHub Actions runner | 21:43:22 → 21:44:25 | **SUCCESS** — 4/4 jobs; English + Hausa + native golden all real responses |
| Agent sandbox (`curl`) | 21:43:28 | `event: error` / `data: null` |
| Canonical **Render** deployment | 21:45:10 | **503** — `provider emitted error event with null/empty data (event_id=f2e30f8a…)` |
| GitHub Actions runner (prior) | 21:38:36 → 21:39:25 | **SUCCESS** — fresh artifacts, real hashes |

The request **contract** was identical (the beta workflow sends `{"data":[messages_json, 0.0, 128,
False]}` at line 91 — the same four parameters our adapter sends), the Space was `RUNNING`, and
there is **no retry logic** in the workflow. The only variable that separates the outcomes is the
**client**.

## 2. Consequence for the earlier incident record

`PROVIDER-INCIDENT-01.md` (in the `runtime-acceptance-6115de9a-aeas04` directory) concludes the
fault is a ZeroGPU availability outage affecting "every queued invocation". That conclusion is now
**superseded in scope, not retracted**:

- It is still true that *from the sandbox and from Render* every invocation fails, and that both
  endpoints and all parameters fail that way.
- It is **not** true that the provider is down for everyone: the GitHub runner succeeded twice in
  the same window.

The refined characterisation is a **per-client admission differential** on a **shared ZeroGPU
pool** (`zero-a10g`), where admission (or a per-identity quota) is granted to some request sources
and refused to others. An authenticated or differently-attributed client is admitted; ours is not.

**Weak, untested hypothesis (do not state as fact):** admission correlates with the request's
`Authorization`/identity. The beta workflow runs **without** `HF_TOKEN` and succeeds, so a token is
not obviously required — but a token (or a differently-attributed egress) may change quota
attribution. This needs an HF credential to test and is **NOT TESTED**. No credential is available
here.

## 3. Why this matters for acceptance (the load-bearing point)

**The canonical governed route — the only one users actually reach — currently returns 503.**

A green CI job therefore **disagrees with the product's own runtime**:

- `n-atlas-external-beta.yml` run `38088403003` (head `4f09b558`) — 4/4 jobs, `status PASS`,
  `response_sha256 f82de127…`;
- `n-atlas-external-beta.yml` run `38088702840` (dispatched 21:43Z) — 4/4 jobs success;
- yet `https://arkadia-qzu4.onrender.com`'s `/api/lab/engineering/n-atlas/run` returns **503**.

**"Green CI" is not "usable product."** The beta workflow exercises the inference from GitHub's
network position; it does not exercise the deployment's network position. Recording a CI PASS as
product acceptance would be exactly the overstatement the governing rule forbids.

## 4. Observed evidence (fresh, this pass)

Run `38088403003` artifact `11683331221` (`native-golden.json`):

```json
{"status": "PASS", "run_id": "RUN-a3e5b49396e2",
 "response_sha256": "f82de127ca5268a5368dca2d8c431ba038618afbb51943fdda23998323f743b3",
 "evidence": {"evidence_id": "EVD-bc03c79801ca", "run_ref": "RUN-a3e5b49396e2",
              "state": "IMPLEMENTED",
              "detail": {"provider": "n_atlas", "model": "N-ATLaS",
                         "prompt_sha256": "cbde4c54bf982a947662faa5130f9f9a0199ccddb34c805365980ff6180f2f7e",
                         "evaluation": {"name": "non_empty_response", "passed": true},
                         "usage": {"protocol": "gradio", "endpoint": "/gradio_api/call/generate",
                                   "event_id": "27d1b9fa10784a55a4a310628869600a",
                                   "sse_events": ["complete"], "terminal_event": "complete"}},
              "timestamp_utc": "2026-10-10T21:39:25.910145+00:00"}}
```

Run `38088403003` artifact `11683395478` (`beta-01-english.json`) — same `response_sha256`
`f82de127…`, `provider "external-space"`, `events [RUN_STARTED … MODEL_TURN …]`.

Hausa (`11683765190`, `beta-02-hausa`) — a **fresh, distinct** model output:
`response_sha256 905bb3a31f50c41552ba2cf279414f57611cdd2c85516908cf4fa62c53159730` (234 chars,
non-empty Hausa text), i.e. the provider really ran the model, not a cached replay.

**Cross-client hash agreement:** `f82de127…` is now confirmed by **four** independent executions
(CI runs `38080315731`, this run's external + native paths, and the canonical run
`RUN-766769015520`), all byte-identical for the same prompt.

## 5. Acceptance states

| Item | State |
| --- | --- |
| GitHub-runner access to N-ATLaS `/generate` | VERIFIED (runs `38088403003`, `38088702840`) |
| Canonical Render deployment access to `/generate` | **BLOCKED** (503 at 21:45:10Z) |
| Agent-sandbox access to `/generate` | BLOCKED (`event: error` / `data: null`) |
| Provider running the real model (not a replay) | VERIFIED (distinct Hausa hash) |
| Per-client admission differential | OBSERVED |
| Cause of the differential | **NOT TESTED** (needs an HF credential / provider-side access) |
| Product-level N-ATLAS usability right now | **BLOCKED** |

## 6. Recommended next action (provider/operator, not repository)

The blocker is on the provider boundary; no repository change removes it. In priority order:

1. **Establish provider-side observability.** Add `HF_TOKEN` (or an equivalent Hugging Face
   credential) to the Render service and to the forensics workflow so authenticated runtime
   logs/events can be retrieved for a failing event id, and so quota attribution can be tested.
   *This is a secret-management action — operator-authorized only.*
2. **Move the runtime off the shared ZeroGPU pool** (a dedicated GPU / a paid Space tier), which
   removes the shared-admission differential as a class.
3. **Or point `N_ATLAS_BASE_URL` at a self-hosted N-ATLAS runtime**, keeping the same
   `protocol=gradio` (or `openai`) contract.

## 7. What is *not* claimed

- Not claimed that ZeroGPU quota exhaustion is the proven cause; it is the leading hypothesis
  consistent with the shared-pool hardware, and it is **NOT TESTED**.
- Not claimed that the CI PASS is invalid as CI evidence; it is valid **about the GitHub network
  position**, and invalid **as product acceptance**.
- The canonical route still degrades honestly (`503`, run `BLOCKED`, no evidence written).
- No credential was used, printed, or committed.
