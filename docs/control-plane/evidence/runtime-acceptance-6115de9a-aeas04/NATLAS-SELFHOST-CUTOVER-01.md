# N-ATLAS self-host cutover — executable vs human-gated (2026-10-10)

Requested: *point `N_ATLAS_BASE_URL` at a self-hosted `deploy/n-atlas-server` instance.*

Governing rule: **where evidence stops, claim stops.** This pass separates what the agent can
execute from what requires deployment authority, and records two defects found while doing so.

## 1. Why the agent cannot perform this cutover

`N_ATLAS_BASE_URL` is read from the **canonical Render service's environment**
(`lab/engineering_lab/natlas.py:22`, `gateway.py:69,184`). Changing it is a production
configuration mutation.

| Requirement | Status here |
| --- | --- |
| Render API credential / dashboard access | **ABSENT** (no `RENDER*` env var) |
| Cloud credential of any kind | **ABSENT** |
| Docker daemon | **UNAVAILABLE** (`dockerd`: "needs to be started with root privileges") |
| Ability to build/run the container locally | **NO** |

No repository change can point the canonical service at a self-hosted runtime. Editing a repo file
would not move the deployed configuration. **This step is human-gated.**

## 2. Two defects found while establishing the cutover surface

### 2.1 `deploy/n-atlas-server/` is not a self-contained build — nothing builds it

`e074a63b` ("use official llama.cpp server runtime for inference") **replaced** the Dockerfile with
a llama.cpp server image and, as the diff shows, only that file changed:

```dockerfile
FROM ghcr.io/ggml-org/llama.cpp:server
ENV N_ATLAS_MODEL_REPO=QuantFactory/N-ATLaS-GGUF:Q4_K_M
CMD /app/llama-server -hf ${N_ATLAS_MODEL_REPO} --host 0.0.0.0 --port ${PORT} -c 4096 -n 256
```

Consequences, each verified:

- The image **never `COPY`s `app.py` or `requirements.txt`** (`grep -c "COPY"` → 0). Those files
  are now **dead code** — the earlier FastAPI gateway they describe is no longer the deployed
  runtime.
- `grep -rn "deploy/n-atlas-server" .github/` → **0 matches**: **no CI job builds this directory.**
  Its image is not built, tested, or exercised anywhere.
- The base image sets **`ENTRYPOINT ["/app/llama-server"]`** (exec form; confirmed from the ghcr
  config blob `sha256:763fd800…`) while the child's `CMD` is **shell form**. Docker therefore
  appends the CMD as argv, giving the final command
  `/app/llama-server /bin/sh -c "/app/llama-server -hf …"`. **This was a real defect, now PROVEN
  and repaired** — see §2.3.

### 2.3 The image could not start — proven by building and running it (2026-10-10)

The earlier revision of this document flagged the `ENTRYPOINT`/`CMD` interaction as "NOT TESTED"
because no Docker daemon was available. Docker **is** available here via `sudo dockerd`, so the
flag was converted into a measurement instead of being left as a suspicion.

**Built this directory's image as shipped and ran it:**

```
Entrypoint=["/app/llama-server"]
Cmd=["/bin/sh","-c","/app/llama-server -hf ${N_ATLAS_MODEL_REPO} --host 0.0.0.0 --port ${PORT} -c 4096 -n 256"]

$ docker run --rm -e PORT=8080 natlas-selfhost:probe
error: invalid argument: /bin/sh
```

The image **exited immediately and could never serve a request.** Docker itself emits the
diagnosis on build: `JSONArgsRecommended: JSON arguments recommended for CMD to prevent unintended
behavior related to OS signals (line 5)`.

**Repair applied** (`deploy/n-atlas-server/Dockerfile`) — clear the inherited exec-form entrypoint
so the shell-form CMD is the whole command and `${PORT}`/`${N_ATLAS_MODEL_REPO}` keep expanding:

```dockerfile
ENTRYPOINT []
```

**Re-built the repository Dockerfile and ran it — verified end to end:**

| Probe | Result |
| --- | --- |
| Container start | model loaded, `listening on http://0.0.0.0:8080` |
| `GET /health` | `{"status":"ok"}` |
| `GET /v1/models` | `QuantFactory/N-ATLaS-GGUF:Q4_K_M` |
| **Real `NAtlasAdapter.generate`** | text `'OK'`, `finish_reason stop`, usage `{prompt 40, completion 2}` |

That last row is the load-bearing one: it drives the **shipped adapter** from
`lab/engineering_lab/natlas.py`, not a hand-rolled request, so the OpenAI-compatible contract the
product actually speaks is satisfied by this image.

**And it settles the identity question empirically.** Asked for `model="N-ATLaS"`, the adapter
reported back:

```
model returned: QuantFactory/N-ATLaS-GGUF:Q4_K_M
```

The runtime echoes the **quantization's own id**, not the official `N-ATLaS`. A cutover to this
instance would keep writing `EVD-*` records under `provider=n_atlas` while the returned model
identity names a community GGUF. That is visible here only because the stack happens to echo it —
do not rely on that echo as the safety mechanism; the boundary is what forbids the substitution.

## 3. The self-hosted model is a *derived quantization*, not the official N-ATLaS

This is the finding that governs the decision, and it is an **acceptance-boundary** issue, not a
technical one:

| | Official (what the Space serves) | Self-host (`deploy/n-atlas-server`) |
| --- | --- | --- |
| Repo | `NCAIR1/N-ATLaS` | `QuantFactory/N-ATLaS-GGUF` (Q4_K_M) |
| GGUF | **none** (safetensors only) | community quantization |
| Gated | **`gated: auto`** | public |
| Model id echoed at runtime | `N-ATLaS` | `QuantFactory/N-ATLaS-GGUF:Q4_K_M` (measured, §2.3) |

The directory's own README states the boundary explicitly:

> *It uses a public GGUF quantization derived from NCAIR1/N-ATLaS. It is validation infrastructure,
> **not a substitute for the official hosted N-ATLAS endpoint**.*

And `docs/architecture/NATLAS_DEVELOPER_LAB_V0.1.md`:

> *A local/self-hosted N-ATLAS execution proves the N-ATLAS integration path. It does **not** prove
> hosted endpoint behavior, hosted authentication, latency, or production quota behavior.*

**Therefore: pointing the canonical route at this instance would change what `N-ATLAS` means for
the product.** A run would still be labelled `provider: n_atlas`, `model: N-ATLas`, and would still
write an `EVD-*` record — but the bytes would come from a 4-bit community quantization rather than
the official model. The acceptance evidence would look identical while measuring a different
object. That is precisely the substitution the established boundary forbids.

It is also **not an equivalent swap for the incident**: the official repo is `gated: auto` and ships
**no GGUF**, so a llama.cpp build cannot serve the official weights without conversion, and the
gated access needs authorization the agent does not hold.

## 4. Correction to this pass's own earlier work

`tests/test_natlas_selfhost_contract.py` (added in the previous commit, PR #411) pinned
`deploy/n-atlas-server/app.py` — **a file the deployed image no longer contains.** The tests were
green and the file is real, so they were not wrong as file assertions, but they **overstated the
runtime contract**: they described the superseded FastAPI gateway, not the llama.cpp server that
`e074a63b` made canonical. That test is now re-pointed, and it **also pinned the broken
`CMD`/`ENTRYPOINT` shape as if it were correct** — the sharpest form of the defect, since a test
that freezes a broken shape will red on the repair. Both are corrected in §2.3 and §5.

## 5. What *is* executable, and was executed

The **safe, non-production** half of the request — preparing the self-host target and pinning it —
was verified:

- `ghcr.io/ggml-org/llama.cpp:server` **exists** and publishes `linux/amd64` (manifest `200`;
  digest `sha256:63fecb2a…`), so the image is real and multi-arch.
- The OpenAI-compatible surface the adapter needs (`/v1/chat/completions`, `/v1/models`,
  `/health`) **is** provided by that upstream server, and `_probe_local`
  (`gateway.py:140-153`) already probes `/v1/models` and `/health` — so the reachability check
  would succeed against a correctly-running instance.
- The protocol switch is the default: `N_ATLAS_PROTOCOL` unset or `openai_compatible` selects
  `NAtlasAdapter` (`gateway.py:191,437-439`).

## 6. Recommended path (requires the operator)

Two options, with the trade-off stated plainly:

**Option A — keep the official model (recommended).** Do **not** cut over to
`deploy/n-atlas-server`. The official Space is public and now reachable from Render with the
credential already added; `RUN-a852a91251d7` → `EVD-55a25912d284` proves the path. The shared-ZeroGPU
differential is a reliability risk, not an identity risk, and it does not justify substituting a
different model. If reliability is the goal, host the **official** weights (requires converting
`NCAIR1/N-ATLaS`, which is `gated: auto`) or move the Space to a dedicated GPU.

**Option B — self-host, but re-label it honestly.** If a self-hosted runtime is wanted for
validation, then:
1. fix the Dockerfile `ENTRYPOINT`/`CMD` defect (§2.1) and `COPY` or delete `app.py`;
2. add a CI job that actually **builds and smoke-tests** the image (nothing builds it today);
3. re-point `tests/test_natlas_selfhost_contract.py` at the llama.cpp contract;
4. and record the runs as a **distinct provider identity** (e.g. `n_atlas_selfhost_gguf`) so an
   `EVD-*` from a community quantization can never be read as evidence about official N-ATLAS.

The cutover itself — setting `N_ATLAS_BASE_URL`/`N_ATLAS_PROTOCOL` on Render — is a **single
operator action** once the above is settled.

## 7. Not claimed

- ~~The Dockerfile `CMD`/`ENTRYPOINT` interaction is **NOT TESTED** end-to-end~~ — **superseded**:
  it is now PROVEN (the unmodified image exits `error: invalid argument: /bin/sh`) and REPAIRED
  (`ENTRYPOINT []`), then re-verified end-to-end through the real `NAtlasAdapter` (§2.3).
- No claim that a self-hosted instance serves the **official** N-ATLAS model: it serves the
  community GGUF, and the adapter's returned model id names it. That is the boundary in §3.
- **No CI job builds this image.** The repair was verified locally only; the image is not built,
  tested, or exercised anywhere in CI, so the fix is not protected by any pipeline.
  **Superseded (2026-10-10, second pass):** `n-atlas-developer-lab.yml` now builds the unit and
  asserts the container reaches llama-server's startup path, and its `paths` filter selects
  `deploy/n-atlas-server/**`. The gap is closed in source; see §8.
- No production configuration was changed; no credential was used, printed, or committed.
- **Production acceptance remains NOT CLAIMED.** The official hosted route
  (`RUN-a852a91251d7` → `EVD-55a25912d284`) is unchanged and remains the only accepted path.

## 8. CI coverage gap closed (2026-10-10, second pass)

The previous pass repaired the image **locally** and disclosed that nothing in CI built it. That
disclosure was correct, and this pass closes it.

**Measured coverage before the change** — which workflows actually executed the branch:

| Suite | Executed by |
| --- | --- |
| `tests/test_natlas_selfhost_contract.py` | **nothing** (`grep -rn` in `.github/` → 0) |
| `deploy/n-atlas-server/**` (image) | **nothing** (`grep -rn` in `.github/` → 0) |

Only `provider-forensics`, the three `N-ATLAS external beta validation` jobs, `boot-syntax` and
the secret scan ran on the branch. The N-ATLAS gate (`n-atlas-developer-lab.yml`) did **not**
trigger, because its `paths` filter named `tests/test_natlas_developer_lab.py` but not the
self-host contract or the deployment unit.

**Repair** (`.github/workflows/n-atlas-developer-lab.yml`):

1. `paths` now selects `tests/test_natlas_selfhost_contract.py`,
   `tests/test_natlas_selfhost_ci_wiring.py`, and `deploy/n-atlas-server/**`.
2. The `backend` job runs the self-host contract.
3. **New `selfhost-image` job** builds `deploy/n-atlas-server` **and runs the image**, failing if
   the logs show `invalid argument: /bin/sh` or if llama-server never reaches its startup path.

Item 3 is the load-bearing one: the image on `main` **built cleanly and then died**, so a
build-only job would have passed. "Builds" is not "starts".

**Guard** — `tests/test_natlas_selfhost_ci_wiring.py` (10 tests) states the invariant generically
over every workflow that runs the contract, deriving the deployment unit's domain from
`git ls-files -- deploy/n-atlas-server` at test time rather than restating it. Four mutations of
the **real** workflow were applied and **each was detected**, with the file restored
byte-identically:

| Mutation | Detected by |
| --- | --- |
| `deploy/n-atlas-server/**` dropped from `paths` | `..._selected_by_the_whole_deployment_unit` |
| contract file dropped from `paths` | `..._selected_by_the_whole_deployment_unit` |
| contract step removed | `test_a_workflow_executes_the_selfhost_contract` |
| smoke step removed (build-only) | `test_a_workflow_builds_and_runs_the_deployment_unit` |

The smoke step's own branch logic was exercised against the **real** log capture from §2.3:
broken-image logs → `exit 1`, fixed-image logs → `exit 0`, empty logs (silent death) → `exit 1`.
A gate that cannot fail for the outcome it names is not a gate.

**Verification:** 179 passed / 1 skipped on the affected suites; full-suite failing/error **node
set identical** to `main` (52 nodes, `sha256 95df9d36…`) — zero regression. CP10 mutation boundary
PASS. The new job interpolates no `github.event.*`/`inputs.*` into `run:`.

