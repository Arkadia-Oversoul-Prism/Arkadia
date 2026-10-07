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


def test_natlas_gradio_adapter_uses_real_event_contract(monkeypatch):
    class FakeResponse:
        def __init__(self, body):
            self.body = body.encode()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
        def read(self):
            return self.body
        def readline(self):
            if not hasattr(self, "_lines"):
                self._lines = iter(self.body.splitlines(True))
            try:
                return next(self._lines)
            except StopIteration:
                return b""

    calls = []
    responses = [
        FakeResponse(json.dumps({"event_id": "evt-123"})),
        FakeResponse('data: ["{\\"text\\": \\"N-ATLaS through Gradio.\\"}"]\n\n'),
    ]

    def fake_urlopen(request, timeout=0):
        calls.append((request.full_url, request.data))
        return responses.pop(0)

    monkeypatch.setattr(gateway_mod.urllib.request, "urlopen", fake_urlopen)
    result = NAtlasGradioAdapter(base_url="https://natlas.test").generate(
        model="N-ATLaS",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.0,
        max_tokens=128,
    )
    assert result.text == "N-ATLaS through Gradio."
    assert calls[0][0].endswith("/gradio_api/call/generate")
    assert calls[1][0].endswith("/gradio_api/call/generate/evt-123")
    payload = json.loads(calls[0][1].decode())
    assert payload["data"][0] == json.dumps([{"role": "user", "content": "Hello"}], ensure_ascii=False)
