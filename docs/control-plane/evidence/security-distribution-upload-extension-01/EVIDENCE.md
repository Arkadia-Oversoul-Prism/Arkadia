# Distribution upload — the stored extension must not be client-chosen

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. This record performs no
  merge, no push to `main`, no deployment, and claims no acceptance. Merge execution is human-only
  (GOV-03/GOV-04).
- **Branch:** `security/distribution-upload-extension-01`
- **Observed:** 2026-11-26T01:0xZ onward

---

## 1. Reconstructed state (live, before any change)

| fact | measured value | how |
|---|---|---|
| canonical `main` | `cb2841956bcc0397007b9efffbaa8cc6d0801836` | `git rev-parse origin/main`; `GET /commits/main` agrees |
| `main` head commit | `docs(weaver): multi-repository hourly portfolio directive (#675)` | `git log -1` |
| production `source_revision` | `cb284195…`, `revision_conflict: false` | `GET /api/version` |
| production `/health` | `200 {"status":"radiant"}` | `GET /health` |
| open PRs | **60**, all `draft`, all `base: main` | `GET /pulls?state=open` |
| branch protection | **UNKNOWN** — `GET /branches/main/protection` returns `403 Resource not accessible by integration` | REST |
| rulesets | **0** | `GET /rulesets` |
| `main` check-runs at `cb284195` | `Full-history secret scan: success` only | `GET /commits/<sha>/check-runs` |

Source↔runtime revision is **VERIFIED** at this revision. That is consistency evidence; it is not
application correctness and not deployment acceptance. Branch protection is recorded as
**UNKNOWN** because the credential cannot read it — not as "absent".

### 1.1 Baseline — one full-suite pass on `main`

```
$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
22 failed, 4251 passed, 22 skipped, 6 warnings, 1 error in 318.59s
```

23 failing/error nodes, every one classified and **none unowned**:

| node(s) | owner |
|---|---|
| `ERROR tests/test_autonomy.py` | sovereign-reserved (CE-01 `weaver.autonomy` collision) |
| `tests/test_ais_w2_living_gate_grove_handoff.py::…` | sovereign-reserved (FINDING F-01) |
| `tests/test_gov04_bounded_merge_delegation.py::…` | open #725 |
| `tests/test_identity_spine_w1.py::…`, `tests/test_m02_reasomate_truth.py::…` | open #700 |
| `tests/test_m01_persistence.py::…`, `tests/test_m05_files.py::…` | open #690 |
| `tests/test_solspire_r1_governance_convergence.py::…` (2) | open #693 |
| `tests/test_solspire_r3_execution_runtime.py::…` | open #691 |
| `tests/test_static_ingestion_idempotency.py::…` | open #698 |
| `tests/test_prism_w4_lab_pr_state.py::…` (2) | open #683 |
| `tests/test_mission_lifecycle_adapter_contract.py::…` (10) | environment-only (`web/arkadia_console/node_modules/typescript` absent) |

This cycle therefore did not open a competing repair for any failing node. It looked for a defect
that no test currently reports.

## 2. The defect — measured against the real handler

`api/distribution.py` writes uploads into `static/releases`, and `api.main` mounts `/static` from
that tree (`app.mount("/static", StaticFiles(directory="static"))`). The extension of a stored file
therefore decides the `Content-Type` the canonical origin serves those bytes with. The handler
validated the client's `content_type` against an allowlist but took the **stored extension from the
client's filename**:

```python
audio_ext = audio.filename.rsplit(".", 1)[-1] if audio.filename and "." in audio.filename else "mp3"
audio_fn  = f"{release_id}_audio.{audio_ext}"
```

Measured in-process at `main` `cb284195`, with `/static` mounted the way `api.main` mounts it:

```
POST /api/distribution/upload   filename="track.html", content_type="audio/mpeg"
  -> 200
  -> stored: <uuid>_audio.html
GET /static/releases/<uuid>_audio.html
  -> 200, content-type: text/html; charset=utf-8
  -> body: <script>alert(document.domain)</script>
```

Production facts measured read-only at `cb284195`:

| probe | result |
|---|---|
| `GET /openapi.json` contains `/api/distribution/upload` | `true` |
| its declared `security` | `[]` (no authentication declared) |
| `GET /static/index.html` | `200` — the tree that receives the upload is served |

So the defect is an **anonymous stored content-injection primitive on the production origin**: the
uploader chooses the extension, and the origin serves the uploaded bytes under it. The artwork
field carried the same defect (`art_ext` from `artwork.filename`).

### 2.1 Negative result, recorded rather than claimed

Path traversal was **tested and is not exploitable**: the extension is always appended to the fixed
prefix `<uuid>_audio.`, so a filename such as `song.mp3/../../../../tmp/x` resolves to
`static/releases/<uuid>_audio.mp3/../../../../tmp/x`, and the intermediate `<uuid>_audio.mp3`
segment does not exist. The measured result was `FileNotFoundError`, not an escaped write. The
repair removes the question entirely, but the traversal claim would have been false.

## 3. The repair

One map per field is now both the accepted set and the extension source, so they cannot drift:

```diff
+AUDIO_EXTENSION_BY_TYPE = {"audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/wav": "wav",
+                           "audio/x-wav": "wav", "audio/flac": "flac", "audio/x-flac": "flac"}
+ARTWORK_EXTENSION_BY_TYPE = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png"}
...
-    allowed_audio    = {"audio/mpeg", "audio/wav", ...}
-    if audio_ct not in allowed_audio:
+    if audio_ct not in AUDIO_EXTENSION_BY_TYPE:
...
-    audio_ext = audio.filename.rsplit(".", 1)[-1] if ...
-    audio_fn  = f"{release_id}_audio.{audio_ext}"
+    audio_fn  = f"{release_id}_audio.{AUDIO_EXTENSION_BY_TYPE[audio_ct]}"
```

Behaviour is preserved for legitimate clients (an `audio/mpeg` upload is still stored as
`_audio.mp3`, an `image/png` artwork as `_artwork.png`), the accepted-type error messages are
unchanged, and no authorization, route, or record shape changed. `api/main.py` is untouched.

## 4. The guard and its executable surface

`tests/test_distribution_upload_extension_contract.py` — **13 nodes**, hermetic: the working
directory moves to `tmp_path`, so `static/releases` and `data/` resolve inside the test and nothing
is written into the repository.

| assertion | shape |
|---|---|
| allowlist values ⊆ `{mp3,wav,flac}` / `{jpg,png}` | a future accepted type cannot arrive with a browser-interpretable extension |
| each accepted audio/artwork type is stored with its canonical extension | 9 parametrized nodes |
| an HTML filename over an accepted audio type stores `.mp3` **and** the served `Content-Type` is `audio/`, not `text/html` | negative control for the defect, with a detector premise (`_extension_from_filename("track.html") == "html"`) |
| a filename carrying path segments writes nothing outside `UPLOAD_DIR` | negative control |
| an unsupported `content_type` is still `400` and writes nothing | positive control for the allowlist |

Live negative control on the real file (repair reverted in the working tree, then restored
byte-identically):

```
pre-repair : 11 failed, 2 passed   (the traversal control and the allowlist control already held)
repaired   : 13 passed
```

`.github/workflows/distribution-upload-contract.yml` is the executable surface: path-filtered to
`api/distribution.py`, the guard, and itself; `pull_request` and `push` filters identical;
`workflow_dispatch`; `permissions: contents: read`; a file-targeted pytest run (so an unrelated
collection error cannot suppress it). No existing workflow selects this guard — CP10 is filtered to
`web/arkadia_console/**`, `spiral_grove/**`, `lab/**`, `api/lab_routes.py`, and
`provider-routing.yml` to `weaver/**`/`providers/**`.

## 5. Verification actually run

| command | result |
|---|---|
| `python -m py_compile api/distribution.py` | exit 0 |
| `pytest tests/test_distribution_upload_extension_contract.py` | **13 passed** |
| `pytest tests/test_ci_gate_trigger_coverage.py tests/test_workflow_injection_boundary.py tests/test_ci_suite_collection_continuation.py tests/test_m02a_ci_gate_integrity.py` | **332 passed** |
| `pytest tests/architecture` | **11 passed** |
| `printf '<paths>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS` |
| targeted re-run of the 12 files that failed on `main` + the new guard + `test_console_legacy_route_coverage.py` | `21 failed, 103 passed, 1 error` |

Failing-node comparison by **identity**, not count: the branch's targeted set contains **zero**
nodes that `main`'s full run does not contain. One node appears only on `main`'s side
(`tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip`),
which is the recorded order-dependent node that passes in isolation on both trees and is owned by
open #698. The `+13 passed` is exactly the new guard's node count.

## 6. Limitations and findings recorded, not repaired

- **No production mutation was performed.** Confirming the defect on the live origin would create a
  release record and write two files, so runtime reachability of the *upload* is **NOT TESTED**;
  the defect is established from the handler plus the deployed `/openapi.json` and the served
  `/static` tree. Labelling: `OBSERVED` in-process, `NOT CLAIMED` in production.
- **The route family is anonymous mutating surface.** `POST /api/distribution/{upload,covenant/sign,submit}`
  require no identity. Repairing that is an authorization change and is **sovereign-gated**; it is
  recorded, not executed.
- **`submit_release` echoes the caught exception text** in its `500` (`f"Aggregator submission failed: {e}"`).
  That is the class #729/#735 repair elsewhere; it is recorded here as separate proposed work.
- **`static/releases` is not gitignored**, so a local upload leaves untracked files in a tracked
  tree. Separate hygiene item.
- **Branch protection is UNKNOWN** at this revision (the credential cannot read it); `main` carries
  no rulesets. Neither fact is treated as a merge precondition here — merge execution is human-only.

## 7. Next action block

- **State:** `main` `cb284195`; production sha-identical; 60 open draft PRs, all human-merge-gated.
- **Evidence:** this record; guard 13/13; 332 workflow+CP10 guards; architecture 11/11; zero
  branch-only failing nodes.
- **Blocker:** none for this change. Merge authority is `NONE`; the PR is a draft.
- **Authorized next action:** human review of the draft PR; on merge, the gate
  `Distribution Upload Contract` becomes the surface that keeps the extension boundary pinned.
- **Forbidden:** merging, deploying, changing the distribution authorization model, or probing the
  production upload route with a real write.
- **Completion condition:** the PR is reviewed and merged by a human, and the gate reports success
  on `main`; production verification remains a separate, credential-gated step.
