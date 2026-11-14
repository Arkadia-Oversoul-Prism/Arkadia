"""Arkadia Executive Office — ARKADIA-CHIEF-001 runtime module.

This package holds the Gate 1 identity and governance enforcement layer for the
Chief Executive Operating Agent. It is a feature module inside the canonical
Arkadia application: it owns no intelligence spine, no model client, no
approval engine and no execution runtime. It coordinates the existing ones.

Nothing in this package commissions the agent. A delegation must be granted by
the Founder through an authenticated control action before any token can be
issued, and the agent remains `PROPOSED_NOT_COMMISSIONED` until that happens.
"""

from __future__ import annotations

PRINCIPAL_ID = "ARKADIA-CHIEF-001"
PRINCIPAL_SUBJECT = "service:ARKADIA-CHIEF-001"
PRINCIPAL_TYPE = "machine_service"
TOKEN_AUDIENCE = "arkadia-executive-api"
MAX_TOKEN_TTL_SECONDS = 300

__all__ = [
    "PRINCIPAL_ID",
    "PRINCIPAL_SUBJECT",
    "PRINCIPAL_TYPE",
    "TOKEN_AUDIENCE",
    "MAX_TOKEN_TTL_SECONDS",
]
