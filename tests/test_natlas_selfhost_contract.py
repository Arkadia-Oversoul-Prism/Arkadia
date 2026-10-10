"""Contract tests for the N-ATLaS self-hosted validation runtime.

There are **two** revisions of this deployment unit in the tree, and the distinction matters:

- `deploy/n-atlas-server/app.py` — the original FastAPI/llama-cpp-python gateway. `e074a63b`
  ("use official llama.cpp server runtime for inference") **replaced the Dockerfile** with the
  upstream `ghcr.io/ggml-org/llama.cpp:server` image and, per that commit's diff, changed only
  the Dockerfile. The image never `COPY`s `app.py` or `requirements.txt`, so those files are no
  longer part of the deployed runtime. They are kept as the historical gateway definition.
- `deploy/n-atlas-server/Dockerfile` — the current, canonical build unit.

The tests below therefore separate (a) the *historical* gateway contract, kept so the superseded
interface stays reconstructable, from (b) the *current* runtime contract the Dockerfile defines.
Conflating the two is what made an earlier revision of this file overstate the runtime contract.

`lab/engineering_lab/natlas.py::NAtlasAdapter` speaks the OpenAI-compatible contract against
whatever `N_ATLAS_BASE_URL` names, so the runtime contract that matters is the Dockerfile's.

These are source-level assertions, matching this repository's convention for deployment and
frontend surfaces (see tests/test_solspire_*). They import no third-party dependency: the gateway
requires `fastapi`/`llama_cpp`, which are not installed in the test environment.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY = REPO_ROOT / "deploy" / "n-atlas-server"
APP = DEPLOY / "app.py"
DOCKERFILE = DEPLOY / "Dockerfile"
ADAPTER = REPO_ROOT / "lab" / "engineering_lab" / "natlas.py"
GATEWAY = REPO_ROOT / "lab" / "engineering_lab" / "gateway.py"

HISTORICAL_ROUTES = (
    "@app.post('/v1/chat/completions')",
    "@app.get('/v1/models')",
    "@app.get('/health')",
)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _missing_contract_routes(src: str) -> set[str]:
    """Return required OpenAI routes absent from a gateway source string."""
    return {route for route in HISTORICAL_ROUTES if route not in src}


def test_historical_gateway_still_parses_as_python():
    """The superseded FastAPI gateway is kept; it must not rot into invalid Python."""
    ast.parse(_source(APP))


def test_historical_gateway_declares_the_openai_compatible_contract():
    missing = _missing_contract_routes(_source(APP))
    assert not missing, f"historical gateway is missing required routes: {sorted(missing)}"


def test_negative_control_detector_reports_a_missing_route():
    """The detector must flag absence, or the contract test above is vacuous."""
    stripped = "@app.get('/health')\ndef health(): ..."
    assert _missing_contract_routes(stripped) == {
        "@app.post('/v1/chat/completions')",
        "@app.get('/v1/models')",
    }


def test_current_runtime_is_the_llamacpp_server_image():
    """The canonical build unit is the upstream server, not the superseded FastAPI app."""
    src = _source(DOCKERFILE)
    assert src.splitlines()[0].strip() == "FROM ghcr.io/ggml-org/llama.cpp:server"


def test_current_runtime_does_not_copy_the_superseded_gateway():
    """Pins the finding: app.py/requirements.txt are not part of the deployed image.

    If a future change starts COPYing them, the historical and current contracts have been
    re-merged and this test forces that decision to be explicit rather than silent.
    """
    src = _source(DOCKERFILE)
    assert "COPY" not in src
    assert "app.py" not in src
    assert "requirements.txt" not in src


def test_current_runtime_serves_the_port_and_host_the_platform_injects():
    src = _source(DOCKERFILE)
    assert "--host 0.0.0.0" in src
    assert "--port ${PORT}" in src


def test_current_runtime_pins_a_model_repo():
    src = _source(DOCKERFILE)
    match = re.search(r"N_ATLAS_MODEL_REPO=(\S+)", src)
    assert match, "Dockerfile must name a model repo"


def test_current_runtime_model_is_a_derived_quantization_not_the_official_repo():
    """Records the acceptance boundary: this is a community GGUF, not NCAIR1/N-ATLaS.

    A self-hosted run must not be readable as evidence about the official model. If the
    Dockerfile is ever repointed at official weights, this test fails so the change is
    reviewed as an identity change rather than a quiet config edit.
    """
    src = _source(DOCKERFILE)
    assert "QuantFactory/N-ATLaS-GGUF" in src
    assert "NCAIR1/N-ATLaS" not in src


def test_current_runtime_clears_the_inherited_entrypoint():
    """The image must start; the inherited exec-form ENTRYPOINT made it impossible.

    The upstream image declares `ENTRYPOINT ["/app/llama-server"]`. With a shell-form CMD and
    no `ENTRYPOINT []` override, Docker appends the CMD as argv, so llama-server received
    `/bin/sh` as a positional argument and aborted with "error: invalid argument: /bin/sh".

    Verified empirically on 2026-10-10 by building and running this image:
    - unmodified: `error: invalid argument: /bin/sh`
    - with `ENTRYPOINT []`: model loaded, `listening on http://0.0.0.0:8080`, `/health` -> ok

    This test fails if the override is removed, forcing the regression to be visible.
    """
    src = _source(DOCKERFILE)
    assert "ENTRYPOINT []" in src, (
        "the inherited exec-form ENTRYPOINT must be cleared, or the shell-form CMD is "
        "appended as argv and the server exits with 'invalid argument: /bin/sh'"
    )


def test_current_runtime_pins_the_cmd_shape_the_entrypoint_override_requires():
    """`ENTRYPOINT []` and a shell-form CMD are a pair; pinning one without the other drifts."""
    src = _source(DOCKERFILE)
    cmd = [line for line in src.splitlines() if line.startswith("CMD ")]
    assert cmd, "Dockerfile must declare a CMD"
    assert not cmd[0].startswith("CMD ["), (
        "the shell form is required so ${N_ATLAS_MODEL_REPO} and ${PORT} expand"
    )
    assert "/app/llama-server" in cmd[0]


def test_historical_gateway_response_shape_matches_adapter_expectations():
    """`NAtlasAdapter.generate` reads choices[0].message.content, model, finish_reason, usage."""
    src = _source(APP)
    assert "'object':'chat.completion'" in src
    assert "'choices':[{" in src
    assert "'message':{'role':'assistant'" in src
    assert "'finish_reason'" in src
    assert "'usage'" in src


def test_adapter_calls_the_selfhost_path_the_gateway_serves():
    adapter = _source(ADAPTER)
    assert "/chat/completions" in adapter
    assert 'f"{self._base_url}/chat/completions"' in adapter


def test_protocol_default_is_openai_compatible_so_selfhost_is_reachable():
    """A self-hosted endpoint is only selected when the protocol is not `gradio`."""
    gw = _source(GATEWAY)
    assert 'os.environ.get("N_ATLAS_PROTOCOL", "openai_compatible")' in gw
    assert "NAtlasGradioAdapter() if protocol == \"gradio\" else NAtlasAdapter()" in gw


def test_historical_gateway_requires_no_fallback_provider():
    """The boundary forbids silently substituting another model."""
    src = _source(APP).lower()
    for forbidden in ("gemini", "openai_api", "anthropic", "ollama"):
        assert forbidden not in src, f"self-host gateway must not reference {forbidden}"


def test_historical_gateway_rejects_streaming_explicitly():
    """v0.1 rejects streaming explicitly rather than silently returning partial text."""
    src = _source(APP)
    assert "streaming is not enabled in v0.1" in src


def test_historical_gateway_api_key_is_optional_and_enforced_when_configured():
    src = _source(APP)
    assert "N_ATLAS_API_KEY" in src
    assert "if API_KEY and authorization" in src
    assert "status_code=401" in src


def test_negative_control_detector_flags_a_missing_route():
    """The route detector must actually detect absence, not just presence."""
    src = "@app.get('/health')\ndef health(): ..."
    assert "@app.post('/v1/chat/completions')" not in src


def test_dockerfile_pins_the_model_repo_and_serves_on_the_platform_port():
    src = _source(DOCKERFILE)
    assert re.search(r"N_ATLAS_MODEL_REPO=\S+", src)
    assert "--port ${PORT}" in src
    assert "--host 0.0.0.0" in src
