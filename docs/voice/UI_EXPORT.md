# Arkadia Voice — Operator UI Export

**Status:** IMPLEMENTED. Route `/solspire/voice` in `web/public_prism`
(canonical frontend), page `src/pages/SolspireVoice.tsx`.

---

## 1. Route & shell

- `App.tsx` `resolvePath('/solspire/voice') → {view:'voice'}`; direct URL
  load and in-app navigation both work (`pushState`/`replaceState` pattern
  preserved).
- Rendered inside `ExperienceConsolidationFrame surface="SolSpire"`.
- Authenticated: `PrismInteriorShell` renders the identity bar + surface rail
  (`activeSurfaceFor('voice') = 'solspire'`), with "Voice Console" in the
  rail's secondary tray and a "Voice" entry in the signed-out drawer nav.
- Signed out: the `.solspire-auth-threshold` card routes into the existing
  sign-in flow.

## 2. Transport

All calls go through the existing `src/lib/apiClient.ts`:

- `apiFetch` for every pipeline call (the page parses `detail` objects
  itself so `VoiceError {state, detail, recovery}` renders truthfully
  instead of `[object Object]`).
- Multipart `FormData` to `POST /solspire/voice/events` (browser sets the
  multipart boundary; `apiClient` skips JSON content-type for FormData).
- Bearer token: `AuthContext` writes `arkadia_token`; the page also mirrors
  the `useLayoutEffect(setApiAuthToken)` pattern used by the other consoles.
- Binary audio uses `apiFetch` → Blob → object URL for in-page playback.

## 3. Panels (in order)

| # | Panel | Contents |
|---|---|---|
| — | Status board | subject role/access, event status, proposal/authorization/work-event/evidence/verification chips, the 14 chain stages highlighted when recorded |
| A0 | Providers (toggle) | per-provider `state`, `model`, `config_source`, `recognized`, reason; default priority; pinned env name — config names only, no secrets |
| A1 | Recent events (toggle) | subject-scoped list; click loads a historical event with full panel reconstruction |
| 02 | Voice control | mic start/stop/cancel with live `MM:SS` timer, provider selector, max-audio-size chip, typed test-provider fallback (generates a silent WAV locally + `transcript_hint`), `MIC_DENIED`/capture errors with recovery copy |
| 03 | Transcript & provenance | exact transcript, provider name, recognized flag, confidence, `sha256` of stored audio, mime/size/duration, **Play audio** (replay from `/events/{id}/audio`) |
| 04 | Understanding | intent action + canonical type + confidence, entities, resolved entities, authority status, human-only refusal chip; clarification inputs per ambiguity (select from candidates when provided) → re-`understand` with `disambiguations` |
| 05 | ARKADIA PROPOSES | objective, requested action, risk, executor, `NO_CANONICAL_EXECUTOR` warning, alternatives, proposal status; **Approve / Reject / Edit** (edit = withdraw & re-propose via `/revise`); reminder "a human decision is not authorization"; observation-only note instead of a proposal for ASK/SEARCH |
| 06 | Authorization & execution | **Authorize (govern authority)** and **Execute** buttons gated on stored status (`APPROVED → authorize`, `AUTHORIZED → execute`, observation executes after understanding); authorization id/channel/tools; execution status/result |
| 07 | Evidence & verification | evidence + verdict chips, chain digest, claim input, **Verify / Insufficient / Contradicted** — separated from execution by design |
| F  | Evidence chain drawer | right-side drawer: every stage with seq, stage, record type, record id, payload digest, timestamp; click expands the full payload JSON |

## 4. State handling rules

- **No client-side guessing.** Panels render stored event fields
  (`intent`, `context`, `proposal_id`, `authorization_ref`, …) and chain
  stage payloads; after every action the page re-reads
  `GET /solspire/voice/events/{id}` (canonical server state) instead of
  trusting the response of the clicked call.
- **Errors are first-class**: `VoiceError.state`, `detail` and `recovery`
  render in a visible error card (including `MIC_DENIED`,
  `ASR_UNAVAILABLE` 503, `TRANSCRIPT_EMPTY`/`INTENT_UNKNOWN` 422,
  `AUTHORIZATION_DENIED` 403). Errors that persist an event (e.g. empty
  transcript) automatically load that event so the ERROR stage is visible in
  the chain drawer — evidence survives negatives.
- Buttons are disabled against the stored status machine, so
  `execute` cannot appear before authorization for consequential actions and
  approval cannot precede a proposal.

## 5. Visual language

Existing SolSpire tokens only: `.solspire-kicker`, `.solspire-mono`,
Georgia serif headings, `#0B0E17` console background, teal `#00D4AA` /
gold `#C9A84C` / blue `#6A9FD8` accents, 13px-radius glass panels, framer-motion
for the drawer. Responsive: single-column stack under 1180px, flex-wrap action
rows, no invented utility classes.

## 6. Build evidence

- `pnpm install --frozen-lockfile` — OK (pnpm 10.26.1).
- `pnpm run build` (`vite build`) — ✓ 3447 modules transformed, bundle
  emitted (no tsconfig exists in `web/public_prism`; the project verifies
  via `vite build`, per its own evidence records).
- Targeted `tsc --noEmit --strict` over `SolspireVoice.tsx` + `App.tsx`:
  **zero errors in `SolspireVoice.tsx`**; remaining diagnostics are
  pre-existing variance patterns in untouched files (the repo has never
  type-checked this frontend) — one genuine pre-existing bug was fixed:
  `App.tsx` `setSolSpireSection` → `setSolspireSection` typo that broke
  URL pushState on every navigation.
