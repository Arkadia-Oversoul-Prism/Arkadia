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
  config blob `sha256:763fd800…`). The child's `CMD` is written in **shell form**, so Docker
  appends it as `["/bin/sh","-c","/app/llama-server -hf …"]`, giving the final argv
  `/app/llama-server /bin/sh -c "/app/llama-server -hf …"`. This is **very likely wrong** — the
  server would receive `/bin/sh` as a positional argument rather than its flags. **NOT TESTED
  end-to-end** (no Docker daemon here); flagged as a probable defect, not asserted as proven.

### 2.2 The self-hosted model is a *derived quantization*, not the official N-ATLaS

This is the finding that governs the decision, and it is an **acceptance-boundary** issue, not a
technical one:

| | Official (what the Space serves) | Self-host (`deploy/n-atlas-server`) |
| --- | --- | --- |
| Repo | `NCAIR1/N-ATLaS` | `QuantFactory/N-ATLaS-GGUF` (Q4_K_M) |
| GGUF | **none** (safetensors only) | community quantization |
| Gated | **`gated: auto`** | public |

The directory's own README states the boundary explicitly:

> *It uses a public GGUF quantization derived from NCAIR1/N-ATLaS. It is validation infrastructure,
> **not a substitute for the official hosted N-ATLAS endpoint**.*

And `docs/architecture/NATLAS_DEVELOPER_LAB_V0.1.md`:

> *A local/self-hosted N-ATLAS execution proves the N-ATLAS integration path. It does **not** prove
> hosted endpoint behavior, hosted authentication, latency, or production quota behavior.*

**Therefore: pointing the canonical route at this instance would change what `N-ATLAS` means for
the product.** A run would still be labelled `provider: n_atlas`, `model: N-ATLaS`, and would still
write an `EVD-*` record — but the bytes would come from a 4-bit community quantization rather than
the official model. The acceptance evidence would look identical while measuring a different
object. That is precisely the substitution the established boundary forbids.

It is also **not an equivalent swap for the incident**: the official repo is `gated: auto` and ships
**no GGUF**, so a llama.cpp build cannot serve the official weights without conversion, and the
gated access needs authorization the agent does not hold.

## 3. Correction to this pass's own earlier work

`tests/test_natlas_selfhost_contract.py` (added in the previous commit, PR #411) pins
`deploy/n-atlas-server/app.py` — **a file the deployed image no longer contains.** The tests are
green and the file is real, so they are not wrong as file assertions, but they **overstate the
runtime contract**: they describe the superseded FastAPI gateway, not the llama.cpp server that
`e074a63b` made canonical. That test needs to be re-pointed (see §5).

## 4. What *is* executable, and was executed

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

## 5. Recommended path (requires the operator)

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

## 6. Not claimed

- The Dockerfile `CMD`/`ENTRYPOINT` interaction is **NOT TESTED** end-to-end (no Docker daemon).
- No claim that a self-hosted instance works; it has never been built in CI.
- No production configuration was changed; no credential was used, printed, or committed.
- **Production acceptance remains NOT CLAIMED.**
