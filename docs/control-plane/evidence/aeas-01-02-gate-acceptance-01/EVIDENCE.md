# AEAS-01 / AEAS-02 Gate 2 + Gate 3 acceptance — browser evidence

Observation date: 2026-10-07
Instrument: `tools/aeas-browser-runner/gate-acceptance.mjs` (real Chromium via Playwright)
Isolated Render environment: `https://arkadia-pr-337.onrender.com`
Isolated SPA origin: `http://localhost:5000` (development CORS allowlist)
Backend under test: PR #337 head `7f39639d7b37e688549f18106df4ea385e11627b`
Work branch: `aeas-02-sse-transport-correctness` @ `0f53b2bbc62727ca9dac64156bacb8f5a16f6d4d` (tracks `origin/aeas-browser-runner-01`)

No production changes, no `main` changes, no merge, no deletion. No fabricated JWT,
no localStorage auth injection, no auth bypass. Authentication is the real Firebase
client flow through the deployed Login UI, using a disposable identity provisioned
through the repository's own harness.

## Verdict

| Gate | Result | Basis |
| --- | --- | --- |
| Gate 2 — isolated browser environment + authenticated Lab API against Render #337 | **PASS** | 4/4 browser steps, 200s on authorized Lab routes |
| Gate 3 — authenticated `/solspire/engineering-lab`, native session, SSE ● LIVE, native event in Events pane | **FAIL on the deployed revision** | 1/5 steps; SSE transport non-conformant on the wire |
| Gate 3 — same instrument, same SPA, local backend carrying the AEAS-02 fix (positive control) | **PASS** | 9/9 steps, event `AEV-412bf8741afc` seq 2 |

The Gate 3 failure is a property of the **deployed revision**, not of the acceptance
environment. The positive control isolates it: identical instrument, identical SPA
bundle, identical identity — only the backend revision differs.

## Gate 2 — PASS

Steps (`deployed-render-pr337.json` → `gate2.steps`), all PASS:

1. `spa-serves-login-route` — SPA serves `/login`.
2. `authenticate-via-real-login-ui` — `tab-signin` → email/password → `button-signin`.
   Result: `id_token_present: true`, `id_token_is_jwt: true`, `fabricated: false`.
   The token is minted by Firebase Identity Toolkit and stored by the app's own
   `AuthContext`, not by the harness.
3. `authenticated-lab-api-operation` — browser `fetch` with the app's own token:
   - `GET /api/lab/overview` → **200**
   - `GET /api/lab/engineering/sessions` → **200**
   Network capture confirms `authorized: true` on both.
4. `engineering-lab-surface-renders` — `/solspire/engineering-lab` renders
   `[data-testid=aeas-01-engineering-lab]` with the "Engineering Lab" marker.

Authentication result: disposable Firebase identity, uid prefix `OKd9BxVX`,
domain `gmail.com`, provisioned via `tests/production/firebase_harness.py`
(`accounts:signUp` through the public Identity Toolkit with the same web API key the
frontend uses). Subject binding returned by the API is
`"subject_binding": "authenticated_firebase_uid"` — the workspace is bound to that
Firebase uid.

Screenshots: `gate2-01-authenticated-login.png`, `gate2-02-lab-api-authorized.png`,
`gate2-03-engineering-lab-surface.png`.

## Gate 3 — FAIL on the deployed revision

Steps (`deployed-render-pr337.json` → `gate3.steps`):

| Step | Result |
| --- | --- |
| `select-or-create-native-session` | PASS |
| `sse-eventstream-live` | **FAIL** — `page.waitForFunction` timed out waiting for `data-transport="LIVE"` |
| `trigger-native-lab-event` | not reached |
| `native-event-reaches-events-pane` | not reached |
| `capture-raw-sse-frames-from-browser` | not reached |

Network evidence: the SSE request itself succeeds —
`GET /api/lab/engineering/sessions/SES-…/events` → **200**,
`content-type: text/event-stream; charset=utf-8`,
`cache-control: no-cache, no-transform`. The transport is reachable; its **framing**
is not conformant.

### Root cause — byte-level proof

Independent wire capture (`/tmp/aeas-wire-bytes.py`) of the deployed endpoint's first
400 bytes:

```
b': connected\\n\\nevent: agent\\ndata: {"event_id": "AEV-af3d23bf7f14", … }\\n\\n:'
```

Byte census on the deployed stream:

- real LF bytes (`0x0A`): **0**
- literal backslash-n (`5C 6E`): **5**
- double backslash-n (`5C 5C 6E`): 0

A conformant SSE parser delimiters frames on a blank line (two real LF bytes). The
deployed emitter writes the two-character sequence `\` `n` instead, so **no frame
boundary ever exists**. `drainSse` (and any conformant parser) yields zero frames,
`lastEventAt` is never set, and `● LIVE` can never be reached. The UI correctly
reports the stream as `CONNECTED` and never claims `LIVE` — the state machine is
honest; the transport is broken.

This matches the source at the PR #337 head exactly
(`git show 7f39639d:api/lab_routes.py`, `body()`): both the comment frame and the
event frame are terminated with a literal `\n\n` rather than a real newline.

A second, independent defect on the same revision: `web/public_prism/src/pages/EngineeringLabPage.tsx`
at `7f39639d` **does not build** (unbalanced JSX, `</div></aside>` at line 58). The
SPA used for the Gate 2 proof therefore comes from the corrected runner branch
`0f53b2bb`, which repairs the JSX and points at the same backend.

## Gate 3 positive control — PASS

Same instrument, same SPA bundle, same disposable identity; backend is the local
backend built from the work branch carrying the AEAS-02 emitter fix.

All 9 steps PASS (`positive-control-local-fixed.json`):

- `sse-eventstream-live` — transport state `{"text": "● LIVE", "transport": "LIVE"}`
- `trigger-native-lab-event` — human `AUTHORIZE` action
- `native-event-reaches-events-pane` — 4 `[data-event-id]` nodes (2 in the operator
  conversation, 2 in the right-hand Events pane)
- `capture-raw-sse-frames-from-browser` — 3 conformant frames

Native event ID and sequence:

- `AEV-457e4498766b` — `SESSION_CREATED` — sequence 1
- **`AEV-412bf8741afc` — `SESSION_TRANSITION` (`state: AUTHORIZED`) — sequence 2**
- session `SES-e329423f95e1`

Raw frames captured in the browser:

```
: connected\n\n
event: agent\ndata: {"event_id": "AEV-457e4498766b", "event_type": "SESSION_CREATED", … "sequence": 1, "session_id": "SES-e329423f95e1", …}\n\n
event: agent\ndata: {"event_id": "AEV-412bf8741afc", "event_type": "SESSION_TRANSITION", "payload": {"state": "AUTHORIZED"}, … "sequence": 2, …}\n\n
```

Screenshots: `gate3-01-session-selected.png`, `gate3-02-transport-live.png`,
`gate3-03-event-triggered.png`, `gate3-04-event-in-pane.png`.

## AEAS-02 emitter regression test (byte boundary)

`tests/test_aeas02_sse_transport.py` — 7 tests, **7 passed**.

The endpoint's own async generator is driven directly in one event loop so the
assertions are on the bytes the route yields, not on a re-implementation:

- frames terminate with real LF, not the literal two-character sequence
- the captured AEAS-01 payload is retained as a negative-control fixture and parses
  to **zero** frames
- conformant framing parses to the expected frames with event id / type / sequence intact
- collection is bounded (max 4 chunks) so a malformed emitter fails the assertion
  instead of spinning on keepalives

Negative control: reverting the emitter to the literal-`\n` form fails exactly the 4
byte-boundary tests while the 3 fixture-integrity tests still pass. Restoring the fix
returns 7 passed.

## Adjacent failure observed, not repaired (cross-lane discipline)

`tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set`
fails at the runner-branch head `0f53b2bb` and at the AEAS-02 commit. The
browser-instrument commit added `POST /api/lab/engineering/browser/probe` without
adding it to `ALLOWED_MUTATION_ENDPOINTS`, so the boundary guard flags it as an
unreviewed mutating endpoint.

Measured: `git checkout 0f53b2bb && pytest <that node>` → **1 failed**. It is
pre-existing on the branch that this work branch tracks, not introduced by the SSE
fix. Per the execution contract it is recorded here as adjacent work rather than
repaired inside the AEAS-02 workstream — the browser-instrument lane owns the
decision of whether `browser/probe` belongs in the reviewed set.

Regression scope run at `99d55e2c`: `test_engineering_lab*.py`, `test_m07_aeas_freeze.py`,
`test_nodes_composition_seam.py`, `test_aeas02_sse_transport.py`, `tests/architecture`
→ **74 passed, 1 failed** (the pre-existing node above).

## Remaining blockers

1. **Gate 3 cannot pass against PR #337 as currently deployed.** The emitter defect is
   in the deployed revision. Gate 3 closure requires either a deployment carrying the
   AEAS-02 emitter fix, or merging the fix into the branch PR #337 serves.
2. **PR #337's head is the non-buildable branch** (`7f39639d`); the buildable runner
   branch is `0f53b2bb`. The Gate 2 SPA proof necessarily used the buildable branch's
   bundle while targeting the PR #337 backend.
3. **Render #337 runs in dev-mode auth** (`FIREBASE_SERVICE_ACCOUNT_JSON` unset →
   JWT signatures not verified). The identity flow is real, but token *verification*
   is not exercised in this environment.
4. `AEV-*` native event IDs on the deployed revision are reachable over the
   authenticated REST read path (`GET …/sessions/{id}`) but are not observable over
   SSE until blocker 1 is resolved.

## Reproduction

```bash
# identity (deleted on cleanup; never committed)
VITE_FIREBASE_API_KEY=<public web key> python3 tools/aeas-browser-runner/provision-identity.py provision /tmp/aeas-fb-user.json

# SPA host on the development CORS-allowed origin
DIST_DIR=web/public_prism/dist PORT=5000 node tools/aeas-browser-runner/spa-host.mjs

# acceptance
SPA_ORIGIN=http://localhost:5000 API_ORIGIN=https://arkadia-pr-337.onrender.com \
EVIDENCE_DIR=./evidence/gate-acceptance AEAS_IDENTITY_FILE=/tmp/aeas-fb-user.json \
node tools/aeas-browser-runner/gate-acceptance.mjs
```
