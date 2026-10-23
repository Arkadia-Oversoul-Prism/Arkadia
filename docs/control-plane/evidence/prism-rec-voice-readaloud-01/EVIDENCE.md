# Prism reconciliation — voice / read-aloud surface (PRISM-REC-VOICE-READALOUD-01)

Bound to base `main` `68403b9ea8e2ba16ade0d1b08418453a79b9dcb7` (2026-10-23).

## 1. The defect, measured

The mission brief warns that the console "has previously been characterized as a
thin scaffold." That characterization was re-measured rather than assumed, by
comparing three sets derived from source:

| Set | Meaning | Size |
|---|---|---|
| legacy | `/(api\|solspire)/…` paths referenced by `archive/frontend/arkadia-prism/web/public_prism/src/**` | 160 |
| served | paths in `api.main:app.openapi()["paths"]` | 288 |
| console | `/(api\|solspire)/…` referenced by `web/arkadia_console/src/**` | 32 |

**130 legacy-used, backend-served endpoints are referenced by no console file.**
The console reaches 32. This is the scaffold gap in one number, and it is why the
reconciliation is a recovery mission rather than a polish pass.

`/api/tts` is one of those 130, and it is the one this slice recovers.

### Why read-aloud specifically

- **The capability is live, not merely declared.** Measured on production
  (`https://arkadia-qzu4.onrender.com`, `source_revision` == `68403b9e`):
  `GET /api/tts/status` → `200 {"engine":"edge_tts","elevenlabs_active":false,…}`;
  `GET /api/tts/voices` → 7 voices. Local synthesis with `edge_tts` installed:
  `POST /api/tts` → `200`, `X-TTS-Engine: edge_tts`, `audio/mpeg`, 29664 bytes.
- **The archive proves the intent.** Three archived components reach it —
  `ScrollListenButton.tsx`, `OracleVoicePlayer.tsx`, `SonataBar.tsx` — so the
  legacy product treated read-aloud as a first-class interaction, not an extra.
- **It was UNSURFACED, not ABSENT_BACKEND.** The console's `endpoints.ts` held no
  `tts` entry at all.
- **It is unowned.** No open PR among the 18 touches `tts`/`voice`/`readaloud`.

Classification before this change: **UNSURFACED**. After: **CONNECTED**
(verified in a browser against the production backend — §5).

## 2. Changed files

| Path | Change |
|---|---|
| `web/arkadia_console/src/lib/endpoints.ts` | +3 registry entries (`tts`, `ttsStatus`, `ttsVoices`), appended after `approvals` |
| `web/arkadia_console/src/lib/voice.ts` | new — the audio fetch, the deliverability rule, markdown stripping |
| `web/arkadia_console/src/components/ReadAloud.tsx` | new — the control |
| `web/arkadia_console/src/pages/ArkanaPage.tsx` | +1 import, +1 mount on assistant turns |
| `tests/test_console_read_aloud_contract.py` | new — 14 tests, 5 live negative controls |

`api/main.py` is untouched. No backend capability was created — the backend
already served this contract.

## 3. Truthfulness rules the slice enforces

These are the properties the tests pin, each with a control that fails when the
property is absent (§4).

1. **One registry (§3.1).** `voice.ts` reads `endpoints.tts*`; it carries no path
   literal. A literal is a second, unreviewed contract.
2. **No fabricated success.** A non-2xx response surfaces the backend's own
   `detail`. A zero-byte audio body throws rather than rendering a player that
   produces no sound and implies it worked.
3. **No silent voice substitution.** `kernel/tts.py` marks `aetheria`
   `requires_elevenlabs`; with no ElevenLabs key the backend serves the Edge
   voice instead. The console locks the option (🔒) and states the reason rather
   than presenting a voice the deployment cannot deliver.
4. **No autoplay.** Synthesis is a real backend call and happens only on an
   explicit user action.
5. **The client's declared shape is the served shape.** `TtsStatus`'s fields are
   asserted against the live `/api/tts/status` payload, read from the app rather
   than restated, so a backend rename reddens the guard instead of rendering
   `undefined`.

## 4. Verification

### Contract guard

`python3 -m pytest tests/test_console_read_aloud_contract.py -q` → **14 passed**.

### Live negative controls (real source, not fixtures)

Each control mutates the **actual** file, asserts the guard reddens, then
restores it byte-identically (verified by `md5sum`).

| # | Mutation | Result |
|---|---|---|
| A | `fetch(\`${API_BASE}${endpoints.tts}\`)` → `fetch(\`${API_BASE}/api/tts\`)` | 1 failed |
| B | `if (blob.size === 0)` → `if (false)` | 1 failed |
| C | derived rule → `return !["aetheria"].includes(voice.name)` | 1 failed |
| D | component stops calling `voiceIsDeliverable(…)` | 1 failed |
| E | assistant mount neutralised to `{false && (` | 1 failed |

Controls A, C and E **failed to bite on the first draft** and the detectors were
strengthened as a result. Recorded because the weakness is the lesson:

- **A** — the first detector anchored on a preceding quote, but the pre-repair
  shape puts the literal *inside* a template substitution, so it was missed.
  The decidable property is that a registry read carries no path text at all.
- **C** — the first detector searched the whole file for
  `requires_elevenlabs`/`elevenlabs_active`, and the file's own interface and doc
  comment supply both, so a rule that ignored them and hardcoded a voice-name
  list passed. The rule's **own body** is now extracted and judged.
- **E** — the first detector used a 300-character proximity window, which the
  page's own `className={turn.role === "assistant" ? …}` ternary satisfies, so a
  dead branch near assistant prose read as a mount. The branch's **balanced
  block** is now extracted and must contain the component.

A detector that passes the defect it exists to catch is worse than no detector.

### Browser journey (real UI, production backend)

Served by the console's own Vite dev server with `/api` proxied to
`https://arkadia-qzu4.onrender.com`. No application source was modified for the
verification; the temporary Vite config used to point the proxy was deleted
afterwards and never staged.

1. `http://localhost:5174/arkana` → Arkana surface renders.
2. Ask *"In one sentence, what is the Arkadia Oracle spine?"* → real reply,
   `resonance 0.98`.
3. The reply carries **Listen** and the voice toggle (**Aria**) — the control is
   mounted only on assistant turns.
4. Click **Listen** → button becomes **Stop**, and `engine · edge_tts` appears.
   Audio is playing from the production backend.
5. Open the voice list → **Aetheria 🔒** plus six available voices.
6. Click **Aetheria** → selection is refused; the toggle still reads **Aria**.

Step 4 is the end-to-end proof: the button only reads `Stop` while an
`HTMLAudioElement` created from the backend's real response is playing, and
`engine · edge_tts` is the backend's own `X-TTS-Engine` header echoed to the UI.

### Honest-failure path

With `edge_tts` absent the local backend returns `502` with a JSON detail. The
client surfaces that as an error rather than a player. This path was observed
directly (`502`, 122-byte JSON body) before `edge_tts` was installed.

### Regression

Full suite, `-rEf --continue-on-collection-errors`, `PYTHONPATH=archive/legacy_python`,
base and branch measured in the same environment. Compared by failing/error node
**identity**, never by count (counts move with how many tests are present).

- base `main` `68403b9e`: 24 failed, 3328 passed, 30 skipped, 1 error — 25 nodes,
  `sha256 7bd1ed3a78b4a24de2c9cc73339d9c7a1c2fa78a50f785b17cd71db526400deb`
- branch: 24 failed, 3342 passed, 30 skipped, 1 error — 25 nodes,
  `sha256 7bd1ed3a78b4a24de2c9cc73339d9c7a1c2fa78a50f785b17cd71db526400deb`
- `comm -3` on the sorted node sets is **empty**: zero new failures, zero fixed.
  The `+14 passed` is exactly this file's 14 nodes.

The first branch measurement showed `+2 failed` and was **not** a regression: a
`git add` executed while the suite was running changed the console-contract
domain under it, so `test_prism_console_ci_wiring.py`'s two nodes observed a
moving inventory. Re-measured on a stable tree the wiring guard is **30 passed**
and the node-set delta is empty. Recorded because a mid-run mutation of the tree
under test is exactly the kind of artifact that reads as a real failure — the
node-set hash, not the count, is what settled it.

### CI gate

`python3 -m pytest -q $(python3 scripts/console_contract_domain.py)` → **746 passed**,
reproducing the `prism-console-contract.yml` step locally. The domain is derived
from tracked files, so the new guard joins it automatically — no workflow edit.
Both files are admitted by `scripts/cp10_mutation_boundary_policy.py --judge`.

## 5. Limitations — what is NOT claimed

- **No production deployment.** Production runs `68403b9e`, which does not
  contain this change. This is a repository-source and local-runtime
  verification, not a production-parity claim. A merge is a production release
  here (Render auto-deploys `main`), so deployment is the human's decision.
- **The ElevenLabs path is untested.** No ElevenLabs key exists in this
  environment or the deployment, so `aetheria` could not be synthesised. The
  lock is verified as a *refusal*; its release when a key is configured is
  `INFERRED` from the contract's `elevenlabs_active` flag, not observed.
- **One surface only.** The archive exposed read-aloud on many scroll surfaces
  (`ScrollListenButton` was mounted in ReasoMate, Spiral Codex, Personal Codex,
  Echofeild, ChamberView). Here it is mounted on Arkana replies. Extending it to
  the remaining surfaces is the natural next slice — the component is already
  generic and takes arbitrary `text`.
- **No persistent voice preference across reloads beyond `localStorage`.** The
  archive shared a global voice preference through React context (`voiceContext`)
  and a single audio element (`audioManager`) so the `SonataBar` surfaced
  playback everywhere. This slice keeps the preference in `localStorage` and
  does not add a global player bar. Consolidating on one audio authority is a
  separate bounded slice — adding a second audio manager now would create the
  duplicate source of truth §3.1 forbids.
- **`resonance 0.98` is the backend's value**, displayed verbatim; this slice
  neither computes nor interprets it.

## 6. Next slice (highest-value remaining gap)

Of the 130 unreferenced endpoints, the largest coherent unowned cluster is
**NovaNet social**: `/api/transmissions`, `/api/transmissions/{id}/comment`,
`/api/transmissions/{id}/react`, `/api/social/nodes` — all served, all used by
the archived NovaNet feed. `GET /api/transmissions` was measured live
(`200`, one transmission with author, reactions, comments). PR #492 already
touches NovaNet/opportunities, so ownership must be reconciled before claiming
it.

## 7. Rollback

Revert the branch. Four source files (one modified file restored, two new files
deleted, one mount line removed) plus one test file. No backend, schema,
migration, configuration, or deployment change is involved, so rollback is a
pure source revert with no data or runtime consequence.

## 8. Adjacent defect found and NOT repaired (ownership held elsewhere)

`python3 scripts/lane_state.py --check` exits **1** on `main` `68403b9e`:

```
DRIFT snapshot base_main 7580bd8f… != current main 68403b9e…;
re-measure the lane PRs and refresh the snapshot
```

`docs/control-plane/parallel-ui/lane-state.json` is owned by **two** open PRs
(#555 and #553), both of which set `base_main` to `04e1b83b…`. That SHA is a real
ancestor of `main` (merge of #545), but it is **not** current `main`, so the
guard still fails after both merge. The snapshot pins a **moving target**: any
commit to `main` re-stales it by construction.

This is not repaired here. The file is contended by two PRs, and rewriting it
from a third branch would either conflict or silently overwrite their lane
measurements — exactly the concurrent-edit hazard §3.1 and the ownership rule
forbid. Recorded as a finding for the file's owners; the structural fix (derive
the comparison from live `main`, or record the snapshot against a revision the
guard treats as a floor rather than an equality) is a bounded change for whoever
owns the snapshot next.

