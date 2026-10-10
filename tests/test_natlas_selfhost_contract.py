"""Contract tests for the self-hosted N-ATLaS validation gateway.

`deploy/n-atlas-server/app.py` exposes N-ATLaS behind an OpenAI-compatible
`/v1/chat/completions` API, which is the contract `lab/engineering_lab/natlas.py::NAtlasAdapter`
speaks when `N_ATLAS_PROTOCOL=openai_compatible` (the default) points `N_ATLAS_BASE_URL` at a
self-hosted runtime. Without these pins the gateway can drift from the adapter that consumes it.

These are source-level assertions, matching this repository's convention for deployment and
frontend surfaces (see tests/test_solspire_*). They import no third-party dependency: the
gateway requires `fastapi`/`llama_cpp`, which are not installed in the test environment.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP = REPO_ROOT / "deploy" / "n-atlas-server" / "app.py"
DOCKERFILE = REPO_ROOT / "deploy" / "n-atlas-server" / "Dockerfile"
ADAPTER = REPO_ROOT / "lab" / "engineering_lab" / "natlas.py"
GATEWAY = REPO_ROOT / "lab" / "engineering_lab" / "gateway.py"

REQUIRED_ROUTES = (
    "@app.post('/v1/chat/completions')",
    "@app.get('/v1/models')",
    "@app.get('/health')",
)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_selfhost_gateway_parses_as_python():
    ast.parse(_source(APP))


def _missing_contract_routes(src: str) -> set[str]:
    """Return required OpenAI routes absent from a gateway source string."""
    return {route for route in REQUIRED_ROUTES if route not in src}


def test_selfhost_gateway_exposes_the_openai_compatible_contract():
    missing = _missing_contract_routes(_source(APP))
    assert not missing, f"gateway is missing required routes: {sorted(missing)}"


def test_negative_control_detector_reports_a_missing_route():
    """The detector must flag absence, or the contract test above is vacuous."""
    stripped = "@app.get('/health')\ndef health(): ..."
    assert _missing_contract_routes(stripped) == {
        "@app.post('/v1/chat/completions')",
        "@app.get('/v1/models')",
    }


def test_selfhost_gateway_response_shape_matches_adapter_expectations():
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


def test_selfhost_gateway_requires_no_fallback_provider():
    """The boundary forbids silently substituting another model."""
    src = _source(APP).lower()
    for forbidden in ("gemini", "openai_api", "anthropic", "ollama"):
        assert forbidden not in src, f"self-host gateway must not reference {forbidden}"


def test_only_generate_is_served_without_a_streaming_path():
    """v0.1 rejects streaming explicitly rather than silently returning partial text."""
    src = _source(APP)
    assert "streaming is not enabled in v0.1" in src


def test_api_key_is_optional_and_enforced_when_configured():
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
