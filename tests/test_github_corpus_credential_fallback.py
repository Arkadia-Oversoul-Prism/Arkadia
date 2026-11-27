"""A refused GitHub credential must not break the public corpus read.

Measured 2026-11-23 on the canonical deployment (``bb19aabd``): a stale
``GITHUB_PERSONAL_ACCESS_TOKEN`` made ``/api/codex/github-tree`` answer 502 with
the upstream 401 and left ``/api/codex`` on its local snapshot, while
``/api/sources`` reported ``authenticated: true``. The corpus is public data, so
the credential is an optimisation and its refusal must degrade to an anonymous
read.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from api import github_corpus

TREE_URL = "https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/git/trees/main"
RAW_URL = "https://raw.githubusercontent.com/Arkadia-Oversoul-Prism/Arkadia/main/README.md"
TOKEN = "stale-token"


@pytest.fixture(autouse=True)
def fresh_credential(monkeypatch):
    monkeypatch.setenv(github_corpus.TOKEN_ENV, TOKEN)
    github_corpus.reset_credential_state()
    yield
    github_corpus.reset_credential_state()


def _refusing_transport(status: int, body, *, seen: list):
    """Refuse any request carrying a credential; answer anonymously."""

    def handler(request: httpx.Request) -> httpx.Response:
        auth = request.headers.get("authorization")
        seen.append(auth)
        if auth:
            return httpx.Response(status, json={"message": "Bad credentials"})
        if isinstance(body, str):
            return httpx.Response(200, text=body)
        return httpx.Response(200, json=body)

    return httpx.MockTransport(handler)


def test_refused_credential_degrades_to_an_anonymous_read():
    seen: list = []
    tree = {"tree": [{"path": "docs/a.md", "type": "blob"}]}

    payload = asyncio.run(
        github_corpus.get_json(
            TREE_URL, transport=_refusing_transport(401, tree, seen=seen)
        )
    )

    assert payload["tree"][0]["path"] == "docs/a.md"
    assert seen == [f"Bearer {TOKEN}", None], "the retry must be anonymous"
    assert github_corpus.credential_state() == "rejected"


def test_negative_control_without_the_retry_the_same_refusal_fails():
    """Disable the degradation and the measured production failure returns."""

    seen: list = []

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        asyncio.run(
            github_corpus.get_json(
                TREE_URL,
                anonymous_retry=False,
                transport=_refusing_transport(401, {"tree": []}, seen=seen),
            )
        )

    assert excinfo.value.response.status_code == 401
    assert seen == [f"Bearer {TOKEN}"], "no anonymous retry was attempted"


def test_raw_host_refusal_is_a_404_not_a_401():
    """raw.githubusercontent.com answers 404 for a refused token (measured)."""

    seen: list = []
    text = asyncio.run(
        github_corpus.get_text(
            RAW_URL, transport=_refusing_transport(404, "# Arkadia\n", seen=seen)
        )
    )

    assert text == "# Arkadia\n"
    assert seen == [f"Bearer {TOKEN}", None]
    assert github_corpus.credential_state() == "rejected"


def test_absent_credential_sends_no_authorization_header(monkeypatch):
    monkeypatch.delenv(github_corpus.TOKEN_ENV, raising=False)
    seen: list = []

    payload = asyncio.run(
        github_corpus.get_json(
            TREE_URL,
            transport=_refusing_transport(401, {"tree": []}, seen=seen),
        )
    )

    assert payload == {"tree": []}
    assert seen == [None]
    assert github_corpus.credential_state() == "absent"


def test_a_remembered_refusal_is_not_re_sent():
    """The corpus issues ~700 reads; a known-bad token must not be retried each time."""

    seen: list = []
    transport = _refusing_transport(401, {"tree": []}, seen=seen)

    asyncio.run(github_corpus.get_json(TREE_URL, transport=transport))
    asyncio.run(github_corpus.get_json(TREE_URL, transport=transport))

    assert seen == [f"Bearer {TOKEN}", None, None]


def test_a_failed_anonymous_read_never_echoes_the_token():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        asyncio.run(
            github_corpus.get_json(TREE_URL, transport=httpx.MockTransport(handler))
        )

    assert TOKEN not in str(excinfo.value)


def test_accepted_credential_is_reported_accepted():
    seen: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("authorization"))
        return httpx.Response(200, json={"tree": []})

    asyncio.run(github_corpus.get_json(TREE_URL, transport=httpx.MockTransport(handler)))

    assert seen == [f"Bearer {TOKEN}"]
    assert github_corpus.credential_state() == "accepted"


def test_api_sources_reports_the_observed_credential_not_its_presence():
    import api.main as main

    github_corpus._state["credential"] = "rejected"
    github = asyncio.run(main.sources())["sources"][0]

    assert github["configured"] is True
    assert github["credential_state"] == "rejected"
    assert github["authenticated"] is False, (
        "a configured but refused credential must not read as authenticated"
    )


def test_main_delegates_its_corpus_reads_to_the_shared_client():
    """Wiring guard: the fallback only helps if main.py uses it."""

    src = Path("api/main.py").read_text(encoding="utf-8")
    assert "github_corpus.get_json" in src
    assert "github_corpus.get_text" in src
