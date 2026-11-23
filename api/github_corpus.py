"""Reads of the public Arkadia corpus from GitHub.

The corpus is public data, so a configured token is a rate-limit optimisation,
not an authorization requirement. A credential GitHub refuses must therefore
degrade to an anonymous read rather than fail the corpus.

Measured 2026-11-23 on the canonical deployment (``bb19aabd``): a stale
``GITHUB_PERSONAL_ACCESS_TOKEN`` made ``/api/codex/github-tree`` answer 502 with
the upstream 401 and left ``/api/codex`` serving its local snapshot, while
``/api/sources`` still reported ``authenticated: true`` — the credential's
presence, not its acceptance.

``raw.githubusercontent.com`` answers **404**, not 401, for a refused token, so
both status families mean "the credential was refused; try anonymously".
"""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

TOKEN_ENV = "GITHUB_PERSONAL_ACCESS_TOKEN"
_REFUSAL_STATUSES = frozenset({401, 403, 404})

# Process-local observation of the configured credential. Once GitHub has
# refused it, later reads skip it: the value cannot change without a restart,
# and re-sending it would turn each of the corpus's ~700 reads into a doomed
# request.
_state: dict[str, str] = {"credential": "unknown"}


def token() -> str:
    return os.environ.get(TOKEN_ENV, "")


def credential_state() -> str:
    """One of ``absent`` | ``unknown`` | ``accepted`` | ``rejected``."""
    if not token():
        return "absent"
    return _state["credential"]


def reset_credential_state() -> None:
    _state["credential"] = "unknown"


def headers(token_value: str | None = None) -> dict[str, str]:
    """Request headers; a configured token is always presented.

    Write paths (``api/main.py`` forge push) require the credential, so the
    anonymous degradation belongs to the read helpers below, not here.
    """
    h = {"Accept": "application/vnd.github.v3+json"}
    t = token() if token_value is None else token_value
    if t:
        h["Authorization"] = f"Bearer {t}"
    return h


def _refused(response: httpx.Response, sent_token: str) -> bool:
    return bool(sent_token) and response.status_code in _REFUSAL_STATUSES


async def _get(
    url: str,
    *,
    timeout: float,
    anonymous_retry: bool,
    transport: httpx.AsyncBaseTransport | None = None,
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
        skip_token = anonymous_retry and credential_state() == "rejected"
        sent = "" if skip_token else token()
        response = await client.get(url, headers=headers(sent))
        if anonymous_retry and _refused(response, sent):
            logger.warning(
                "GitHub refused the configured credential (%s); reading %s anonymously",
                response.status_code,
                url,
            )
            _state["credential"] = "rejected"
            response = await client.get(url, headers=headers(""))
        elif sent and response.status_code < 400:
            _state["credential"] = "accepted"
        response.raise_for_status()
        return response


async def get_json(
    url: str,
    *,
    timeout: float = 15,
    anonymous_retry: bool = True,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict:
    response = await _get(
        url, timeout=timeout, anonymous_retry=anonymous_retry, transport=transport
    )
    return response.json()


async def get_text(
    url: str,
    *,
    timeout: float = 12,
    anonymous_retry: bool = True,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    response = await _get(
        url, timeout=timeout, anonymous_retry=anonymous_retry, transport=transport
    )
    return response.text
