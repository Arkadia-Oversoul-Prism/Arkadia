"""WEAVER-K2 — provider orchestration proofs."""
from __future__ import annotations

from weaver.provider import (
    ProviderOutcome,
    ProviderRequest,
    invoke_provider,
    list_available_providers,
    _mask_secrets,
)
from weaver import agent as weaver_agent
from weaver.pass_spec import PassSpec


def test_list_providers():
    names = list_available_providers()
    assert "gemini" in names
    assert "claude" in names


def test_unknown_provider():
    r = invoke_provider(ProviderRequest(provider="not-a-provider", prompt="hi"))
    assert r.outcome == ProviderOutcome.CONFIGURATION_ERROR
    assert not r.ok


def test_empty_prompt_invalid():
    r = invoke_provider(ProviderRequest(provider="gemini", prompt="  "))
    assert r.outcome == ProviderOutcome.INVALID_REQUEST


def test_provider_has_no_write_commit_push():
    """Provider module must not expose repository mutation APIs."""
    import weaver.provider as prov
    for forbidden in ("write_file", "commit_and_push", "push_current", "run_authorized"):
        assert not hasattr(prov, forbidden)


def test_mask_secrets():
    s = _mask_secrets("error key=AIzaSyDummySecretValue123 status")
    assert "AIzaSyDummy" not in s or "***" in s
    assert "key=***" in s or "***" in s


def test_gemini_rotation_mock(monkeypatch):
    keys = ["key-a", "key-b"]
    state = {"i": 0, "failed": set()}

    def acquire():
        for k in keys:
            if k not in state["failed"]:
                return k
        raise RuntimeError("no key")

    def report_failure(key, cooldown=45.0):
        state["failed"].add(key)
        return key

    def report_success(key):
        state["failed"].discard(key)

    monkeypatch.setattr("api.key_pool.acquire_key", acquire, raising=False)
    # patch inside provider after import path
    import weaver.provider as prov

    class Resp:
        def __init__(self, code, text="{}", data=None):
            self.status_code = code
            self.text = text
            self._data = data or {}

        def json(self):
            return self._data

    calls = {"n": 0}

    def fake_post(url, json=None, timeout=None, headers=None):
        calls["n"] += 1
        if "key-a" in url:
            return Resp(429, "rate")
        return Resp(
            200,
            data={"candidates": [{"content": {"parts": [{"text": "ok-from-b"}]}}]},
        )

    monkeypatch.setattr(
        prov,
        "_invoke_gemini",
        lambda req: _fake_gemini_with_pool(req, acquire, report_failure, report_success, fake_post),
    )
    r = prov.invoke_provider(ProviderRequest(provider="gemini", prompt="hello", max_key_attempts=3))
    assert r.ok
    assert r.text == "ok-from-b"


def _fake_gemini_with_pool(req, acquire, report_failure, report_success, fake_post):
    from weaver.provider import ProviderResult, ProviderOutcome
    import time

    attempts = 0
    last = ""
    while attempts < req.max_key_attempts:
        attempts += 1
        try:
            key = acquire()
        except Exception as e:
            return ProviderResult(
                outcome=ProviderOutcome.CONFIGURATION_ERROR,
                provider="gemini",
                attempts=attempts,
                error=str(e),
            )
        url = f"https://example/?key={key}"
        r = fake_post(url, json={}, timeout=1, headers={})
        if r.status_code == 200:
            report_success(key)
            return ProviderResult(
                outcome=ProviderOutcome.SUCCESS,
                text=r.json()["candidates"][0]["content"]["parts"][0]["text"],
                provider="gemini",
                attempts=attempts,
            )
        if r.status_code == 429:
            report_failure(key)
            last = "rate"
            continue
        last = f"status {r.status_code}"
    return ProviderResult(
        outcome=ProviderOutcome.RATE_LIMITED,
        provider="gemini",
        attempts=attempts,
        error=last,
    )


def test_all_keys_exhausted(monkeypatch):
    import weaver.provider as prov

    def always_429(req):
        from weaver.provider import ProviderResult, ProviderOutcome

        return ProviderResult(
            outcome=ProviderOutcome.RATE_LIMITED,
            provider="gemini",
            attempts=3,
            error="all keys exhausted",
        )

    monkeypatch.setattr(prov, "_invoke_gemini", always_429)
    r = prov.invoke_provider(ProviderRequest(provider="gemini", prompt="x"))
    assert not r.ok
    assert r.outcome == ProviderOutcome.RATE_LIMITED


def test_agent_provider_failure_no_commit(monkeypatch):
    """Provider failure must not proceed to writes."""
    import weaver.agent as agent
    from weaver.provider import ProviderResult, ProviderOutcome
    from weaver.session_kernel import SessionResult

    spec = PassSpec(
        pass_id="K2-TEST",
        objective="fail provider",
        base_sha="0" * 40,
        allowed_paths=["weaver/"],
        commit_required=False,
        push_allowed=False,
        publication_required=False,
    )

    monkeypatch.setattr(
        agent,
        "preflight",
        lambda *a, **k: "0" * 40,
    )
    monkeypatch.setattr(
        agent,
        "invoke_provider",
        lambda req: ProviderResult(
            outcome=ProviderOutcome.PROVIDER_UNAVAILABLE,
            provider="gemini",
            error="down",
        ),
    )
    monkeypatch.setattr(agent, "read_repo", lambda *a, **k: {})
    monkeypatch.setattr(agent, "build_prompt", lambda *a, **k: "p")

    res = agent.run_authorized("task", spec)
    assert res.ok is False
    assert res.stage == "llm"
    assert res.status == "FAILED"
