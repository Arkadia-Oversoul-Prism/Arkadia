import json

from lab.engineering_lab import gateway as gateway_mod
from lab.engineering_lab.gateway import ModelGateway, ModelResponse
from lab.engineering_lab.natlas import NAtlasAdapter


def test_natlas_is_truthfully_unconfigured_without_endpoint(monkeypatch):
    monkeypatch.delenv("N_ATLAS_BASE_URL", raising=False)
    gateway = ModelGateway()
    descriptor = gateway.describe("n_atlas")
    assert descriptor.status == "UNCONFIGURED"
    assert descriptor.configured is False


def test_natlas_adapter_maps_openai_compatible_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
        def read(self):
            return json.dumps({
                "model": "N-ATLaS",
                "choices": [{
                    "message": {"content": "Nigeria has many languages."},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 3, "completion_tokens": 5},
            }).encode()

    monkeypatch.setattr(gateway_mod.urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse())
    result = NAtlasAdapter(base_url="http://n-atlas.test/v1").generate(
        model="N-ATLaS",
        messages=[{"role": "user", "content": "Hello"}],
    )
    assert isinstance(result, ModelResponse)
    assert result.provider == "n_atlas"
    assert result.text == "Nigeria has many languages."
    assert result.usage["completion_tokens"] == 5
