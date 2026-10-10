import json
import os
import pytest

from lab.engineering_lab import gateway as gateway_mod
from lab.engineering_lab.gateway import ModelGateway, ModelResponse
from lab.engineering_lab.natlas import NAtlasAdapter, NAtlasGradioAdapter


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


@pytest.mark.asyncio
async def test_native_natlas_route_live_external_gradio(monkeypatch):
    if os.environ.get("N_ATLAS_LIVE_TEST") != "1":
        pytest.skip("live external N-ATLaS validation is opt-in")

    import api.lab_routes as lab_routes

    class FakeRuntime:
        def get_session(self, session_id, subject_uid):
            return {
                "session_id": session_id,
                "subject_ref": subject_uid,
                "workspace_ref": "WS-live-natlas",
                "agent_id": "AGT-live-natlas",
                "state": "AUTHORIZED",
                "authorization_ref": "AUTH-live-natlas",
            }

    class FakeStore:
        def __init__(self):
            self.runs = []
            self.evidence = []
        def create_run(self, run):
            self.runs.append(run)
        def update_run(self, *args, **kwargs):
            return None
        def save_evidence(self, evidence):
            self.evidence.append(evidence)

    class FakeStream:
        def __init__(self):
            self.events = []
        def emit(self, **kwargs):
            self.events.append(kwargs)

    store = FakeStore()
    stream = FakeStream()
    monkeypatch.setattr(lab_routes, "get_runtime", lambda: FakeRuntime())
    monkeypatch.setattr(lab_routes, "get_store", lambda: store)
    monkeypatch.setattr(lab_routes, "get_event_stream", lambda: stream)

    result = await lab_routes.n_atlas_run(
        lab_routes.NAtlasRunBody(
            session_id="SES-live-natlas",
            prompt="Respond briefly: What is the purpose of evidence in a governed AI workflow?",
            model="N-ATLaS",
        ),
        user={"uid": "subject-live-natlas"},
    )

    assert result["provider"] == "n_atlas"
    assert result["model"] == "N-ATLaS"
    assert result["evaluation"]["passed"] is True
    assert result["response"].strip()
    assert len(store.evidence) == 1
    assert store.evidence[0].detail["integration"] == "gradio N-ATLaS runtime adapter"
    event_types = [event["event_type"] for event in stream.events]
    evidence_dir = os.environ.get("N_ATLAS_LIVE_EVIDENCE_DIR")
    if evidence_dir:
        os.makedirs(evidence_dir, exist_ok=True)
        evidence_payload = result["evidence"]
        assert isinstance(evidence_payload, dict)
        assert evidence_payload["detail"]["integration"] == "gradio N-ATLaS runtime adapter"
        artifact = {
            "status": "PASS",
            "run_id": result["run_id"],
            "response_sha256": evidence_payload["detail"]["response_sha256"],
            "evidence": evidence_payload,
        }
        with open(os.path.join(evidence_dir, "native-golden.json"), "w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2, ensure_ascii=False)
        with open(os.path.join(evidence_dir, "native-golden.json"), "r", encoding="utf-8") as fh:
            persisted_artifact = json.load(fh)
        assert persisted_artifact["status"] == "PASS"
        assert persisted_artifact["evidence"]["detail"]["response_sha256"] == evidence_payload["detail"]["response_sha256"]

    assert event_types == [
        "RUN_STARTED",
        "MODEL_TURN",
        "EVIDENCE_RECORDED",
        "RUN_FINISHED",
    ]


def test_natlas_tester_onboarding_records_human_authorization(monkeypatch):
    import api.lab_routes as lab_routes

    class FakeWorkspace:
        id = "WS-tester"

    class FakeWorkspaceManager:
        def get_or_create(self, uid, display_name):
            assert uid.startswith("natlas-tester-")
            assert display_name == "N-ATLaS External Test Workspace"
            return FakeWorkspace()

    class FakeStore:
        def __init__(self):
            self.auth = []
            self.agents = []
            self.attached = []

        def list_agents(self, uid):
            return self.agents

        def attach_authorization(self, session_id, uid, auth_id):
            self.attached.append((session_id, uid, auth_id))

    class FakeRuntime:
        def __init__(self):
            self.authorizations = []
            self.transitions = []

        def register_agent(self, **kwargs):
            return {"agent_id": "AGT-tester"}

        def open_session(self, **kwargs):
            return {
                "session_id": "SES-tester",
                "state": "PROPOSED",
                "workspace_ref": kwargs["workspace_ref"],
                "agent_id": kwargs["agent_id"],
            }

        def record_authorization(self, **kwargs):
            self.authorizations.append(kwargs)
            return {"authorization_id": "AUTH-tester"}

        def transition(self, session_id, uid, target):
            self.transitions.append((session_id, uid, target))
            return {
                "session_id": session_id,
                "state": target,
                "workspace_ref": "WS-tester",
                "agent_id": "AGT-tester",
            }

    class FakeGateway:
        class Descriptor:
            status = "AVAILABLE"
            model = "N-ATLaS"
            detail = "available"

        def describe(self, provider):
            assert provider == "n_atlas"
            return self.Descriptor()

    store = FakeStore()
    runtime = FakeRuntime()
    monkeypatch.setattr(
        lab_routes, "get_store", lambda: store
    )
    monkeypatch.setattr(
        lab_routes, "get_runtime", lambda: runtime
    )
    monkeypatch.setattr(
        lab_routes, "get_gateway", lambda: FakeGateway()
    )
    monkeypatch.setattr(
        "solspire.workspace_manager.get_workspace_manager",
        lambda: FakeWorkspaceManager(),
    )

    monkeypatch.setattr(lab_routes, "mint_natlas_tester_token", lambda **kwargs: "natlas-tester.test.signature")

    result = __import__("asyncio").run(
        lab_routes.n_atlas_test_session()
    )

    assert result["session_id"] == "SES-tester"
    assert result["state"] == "AUTHORIZED"
    assert result["tester_token"] == "natlas-tester.test.signature"
    assert result["scope"] == ["n_atlas:run"]
    assert runtime.authorizations[0]["scope_ref"] == "SES-tester"
    assert runtime.authorizations[0]["operations_allowed"] == ("read", "test")
    assert len(store.attached) == 1
    assert store.attached[0][0] == "SES-tester"
    assert store.attached[0][1].startswith("natlas-tester-")
    assert store.attached[0][2] == "AUTH-tester"
    assert len(runtime.transitions) == 1
    assert runtime.transitions[0][0] == "SES-tester"
    assert runtime.transitions[0][1].startswith("natlas-tester-")
    assert runtime.transitions[0][2] == "AUTHORIZED"


def test_natlas_tester_token_is_scoped_and_signed(monkeypatch):
    from api import auth

    monkeypatch.setenv("SOVEREIGN_KEY", "test-secret")
    token = auth.mint_natlas_tester_token(session_id="SES-123", subject_ref="natlas-tester-123")
    claims = auth.verify_natlas_tester_token(token)
    assert claims is not None
    assert claims["sid"] == "SES-123"
    assert claims["sub"] == "natlas-tester-123"
    assert claims["scope"] == ["n_atlas:run"]

    tampered = token[:-1] + ("0" if token[-1] != "0" else "1")
    assert auth.verify_natlas_tester_token(tampered) is None


def test_natlas_tester_token_not_accepted_as_general_auth(monkeypatch):
    from api import auth
    from starlette.requests import Request

    monkeypatch.setenv("SOVEREIGN_KEY", "test-secret")
    token = auth.mint_natlas_tester_token(session_id="SES-123", subject_ref="natlas-tester-123")
    scope = {"type": "http", "method": "GET", "path": "/api/me", "headers": [(b"authorization", f"Bearer {token}".encode())]}
    request = Request(scope)

    import asyncio
    try:
        asyncio.run(auth.require_auth(request))
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 401
    else:
        raise AssertionError("N-ATLaS tester capability must not authenticate general routes")


def test_natlas_gradio_adapter_waits_for_complete_and_parses_sse_error(monkeypatch):
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
        FakeResponse(json.dumps({"event_id": "evt-stream"})),
        FakeResponse(
            'event: generating\n'
            'data: ["first chunk"]\n\n'
            'event: generating\n'
            'data: ["complete chunk"]\n\n'
            'event: complete\n'
            'data: ["final response"]\n\n'
        ),
    ]

    def fake_urlopen(request, timeout=0):
        calls.append((request.full_url, timeout))
        return responses.pop(0)

    monkeypatch.setattr(gateway_mod.urllib.request, "urlopen", fake_urlopen)
    result = NAtlasGradioAdapter(base_url="https://natlas.test").generate(
        model="N-ATLaS",
        messages=[{"role": "user", "content": "Hello"}],
    )

    assert result.text == "final response"
    assert result.usage["sse_events"] == ["generating", "generating", "complete"]
    assert result.usage["terminal_event"] == "complete"
    assert calls[0][1] == 300.0
    assert calls[1][1] == 300.0


def test_natlas_gradio_adapter_surfaces_provider_error_event(monkeypatch):
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

    responses = [
        FakeResponse(json.dumps({"event_id": "evt-error"})),
        FakeResponse(
            'event: error\n'
            'data: "generation failed"\n\n'
        ),
    ]

    def fake_urlopen(request, timeout=0):
        return responses.pop(0)

    monkeypatch.setattr(gateway_mod.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(Exception, match="Gradio runtime error: generation failed"):
        NAtlasGradioAdapter(base_url="https://natlas.test").generate(
            model="N-ATLaS",
            messages=[{"role": "user", "content": "Hello"}],
        )


# ---------------------------------------------------------------- provider-failure boundary


def _failure_route_harness(monkeypatch, frames_body, *, descriptor_status="AVAILABLE"):
    """Drive the REAL `/n-atlas/run` route with the provider's failure frame.

    Only the storage/runtime/stream seams are stubbed (the same seams the live test
    stubs); the route and the real `NAtlasGradioAdapter` are exercised unchanged, so
    the assertion below is about product code rather than a reimplementation.

    The injected frame is the one the Space actually emits on a ZeroGPU admission
    rejection, captured from the provider-forensics artifacts:

        event: error
        data: null
    """
    import asyncio

    import api.lab_routes as lab_routes

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

    class FakeRuntime:
        def get_session(self, session_id, subject_uid):
            return {
                "session_id": session_id,
                "subject_ref": subject_uid,
                "workspace_ref": "WS-failure",
                "agent_id": "AGT-failure",
                "state": "AUTHORIZED",
                "authorization_ref": "AUTH-failure",
            }

    class FakeStore:
        def __init__(self):
            self.runs = []
            self.evidence = []
            self.updates = []

        def create_run(self, run):
            self.runs.append(run)

        def update_run(self, run_id, subject_uid, **kwargs):
            self.updates.append(kwargs)

        def save_evidence(self, evidence):
            self.evidence.append(evidence)

    class FakeStream:
        def __init__(self):
            self.events = []

        def emit(self, **kwargs):
            self.events.append(kwargs)

    class FakeDescriptor:
        def __init__(self, status):
            self.status = status
            self.model = "N-ATLaS"
            self.detail = "harness"

        def to_dict(self):
            return {"status": self.status, "model": self.model}

    class FakeGateway:
        def describe(self, provider):
            return FakeDescriptor(descriptor_status)

        def generate(self, **kwargs):
            return NAtlasGradioAdapter(base_url="https://natlas.test").generate(**kwargs)

    responses = [FakeResponse(json.dumps({"event_id": "evt-failure"})), FakeResponse(frames_body)]

    def fake_urlopen(request, timeout=0):
        return responses.pop(0)

    monkeypatch.setattr(gateway_mod.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(lab_routes, "get_runtime", lambda: FakeRuntime())
    monkeypatch.setattr(lab_routes, "get_gateway", lambda: FakeGateway())

    store, stream = FakeStore(), FakeStream()
    monkeypatch.setattr(lab_routes, "get_store", lambda: store)
    monkeypatch.setattr(lab_routes, "get_event_stream", lambda: stream)
    return lab_routes, store, stream, asyncio


def test_provider_error_frame_never_writes_a_false_pass(monkeypatch):
    """A provider failure must not produce an evidence record or a passed evaluation.

    The route already behaves correctly (it raises 503 and writes no `EVD-*`), but
    nothing pinned that. Without this test, a future edit that wrote evidence before
    checking the response would record a fabricated PASS with no failing assertion.
    """
    lab_routes, store, stream, asyncio = _failure_route_harness(
        monkeypatch, 'event: error\ndata: null\n\n'
    )

    with pytest.raises(lab_routes.HTTPException) as excinfo:
        asyncio.run(
            lab_routes.n_atlas_run(
                lab_routes.NAtlasRunBody(
                    session_id="SES-failure", prompt="probe", model="N-ATLaS"
                ),
                user={"uid": "subject-failure"},
            )
        )

    assert excinfo.value.status_code == 503
    assert "error event with null/empty data" in str(excinfo.value.detail)

    # The load-bearing assertion: no acceptance artefact for a failed inference.
    assert store.evidence == [], (
        "a failed provider run wrote an evidence record; a provider failure must never "
        "be recorded as success"
    )

    # The run is still tracked, and tracked as blocked - not as a success.
    assert len(store.runs) == 1
    assert any(u.get("result_state") == "BLOCKED" for u in store.updates), store.updates
    assert not any(u.get("result_state") == "IMPLEMENTED" for u in store.updates), store.updates

    event_types = [event["event_type"] for event in stream.events]
    assert event_types == ["RUN_STARTED", "BLOCKED"]
    assert "EVIDENCE_RECORDED" not in event_types
    assert "MODEL_TURN" not in event_types


def test_provider_success_still_writes_exactly_one_evidence_record(monkeypatch):
    """Positive control for the test above: the same harness must record a real pass.

    A boundary test that passes on both trees proves nothing; this control fails if
    the no-evidence assertion is satisfied by breaking the success path instead.
    """
    lab_routes, store, stream, asyncio = _failure_route_harness(
        monkeypatch,
        'event: complete\n'
        'data: ["{\\"text\\": \\"ok\\", \\"model\\": \\"NCAIR1/N-ATLaS\\"}"]\n\n',
    )

    result = asyncio.run(
        lab_routes.n_atlas_run(
            lab_routes.NAtlasRunBody(session_id="SES-success", prompt="probe", model="N-ATLaS"),
            user={"uid": "subject-success"},
        )
    )

    assert result["evaluation"]["passed"] is True
    assert len(store.evidence) == 1
    assert store.evidence[0].state == "IMPLEMENTED"
    assert [e["event_type"] for e in stream.events] == [
        "RUN_STARTED",
        "MODEL_TURN",
        "EVIDENCE_RECORDED",
        "RUN_FINISHED",
    ]

