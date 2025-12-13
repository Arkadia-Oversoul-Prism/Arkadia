import os
from weaver.llm import available_providers


def test_available_providers_default(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    providers = available_providers()
    assert isinstance(providers, dict)
    assert providers.get('gemini') is False


def test_available_providers_with_key(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'fakekey')
    providers = available_providers()
    assert providers.get('gemini') is True
