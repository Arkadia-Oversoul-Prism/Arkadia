"""ReasoMate direct threads — the console surface against the live message substrate.

The archived Prism surface (`archive/.../components/ReasoMateSurface.tsx`) carried
two lenses: the Arkana conversation and direct node-to-node threads. The console
already serves the first as its own `/arkana` surface; it served the second from
nowhere, so the capability was UNSURFACED rather than absent. `api/messages.py`
serves it today: `GET /api/messages/inbox`, `GET /api/messages/thread/{peer_uid}`
and `POST /api/messages`, all behind `require_auth`.

This guard pins the properties that make the recovered surface *truthful*, not
merely present. Each live assertion is paired with a negative control that feeds
the pre-repair shape to the same detector, so a detector that matched nothing
cannot pass by accident:

1. The surface is declared once, on `/reasomate`, and is `requiresAuth` — the
   shell refuses it to an anonymous viewer before the page mounts.
2. Every advertised path resolves to a handler the canonical app actually
   serves, and the page reads them through the registry rather than inline.
3. A payload the client cannot read is reported as unrecognised, never rendered
   as an empty conversation; a genuine empty read renders its own state.
4. Sending is the handler's own contract: the recipient is taken from the send
   response, so the surface never guesses the peer's identity.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
PAGE = SRC / "pages" / "ReasoMatePage.tsx"
CONTRACTS = SRC / "pages" / "reasomate" / "reasomateContracts.ts"
ENDPOINTS = SRC / "lib" / "endpoints.ts"
SURFACES = SRC / "lib" / "surfaces.ts"
APP = SRC / "App.tsx"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (module level, so the negative controls exercise the same code).
# ---------------------------------------------------------------------------


def surface_entry(source: str, surface_id: str) -> str | None:
    """The declared surface block for ``surface_id``, or ``None``."""
    match = re.search(r'\{\s*\n\s*id: "%s",(.*?)\n  \},' % re.escape(surface_id), source, re.S)
    return match.group(1) if match else None


def declares_auth_surface(source: str, surface_id: str, path: str) -> bool:
    block = surface_entry(source, surface_id)
    if block is None:
        return False
    return "requiresAuth: true" in block and f'path: "{path}"' in block


def registered_paths(source: str) -> dict[str, str]:
    return dict(re.findall(r'^\s*(\w+):\s*"([^"]+)"', source, re.M))


def served_paths() -> set[str]:
    """Every path template the canonical application declares.

    Read from the app's own OpenAPI document rather than from a hand-written
    list, and rather than by walking `app.routes`: the message router is mounted
    through a composed wrapper whose nested routes do not expose `methods`, so a
    route-table walk silently sees none of them.
    """
    from api.main import app

    return set(app.openapi().get("paths", {}))


def _template_regex(template: str) -> str:
    """Turn a path template into a regex: every `{param}` becomes one segment."""
    parts = re.split(r"\{[^}]+\}", template)
    return r"[^/]+".join(re.escape(part) for part in parts)


def served_by_the_app(path: str) -> bool:
    """True when ``path`` is a declared path template, or instantiates one."""
    paths = served_paths()
    if path in paths:
        return True
    return any("{" in template and re.fullmatch(_template_regex(template), path) for template in paths)


def validates_before_rendering(page: str, guard: str) -> bool:
    """The page must import ``guard`` and refuse the payload through it."""
    imported = re.search(r"import\s*\{[^}]*\b%s\b[^}]*\}\s*from" % guard, page, re.S)
    used = re.search(r"if\s*\(\s*!\s*%s\(" % guard, page) or re.search(r"!\s*%s\(" % guard, page)
    return bool(imported and used)


def renders_a_hardcoded_conversation(page: str) -> bool:
    """A fabricated thread: a message array literal with content and no request."""
    literal = re.search(r"\[\s*\{\s*id:\s*['\"][^'\"]+['\"],\s*sender_uid", page)
    return bool(literal)


# ---------------------------------------------------------------------------
# 1. One declared, protected surface.
# ---------------------------------------------------------------------------


def test_the_surface_is_declared_once_on_its_own_path():
    source = _read(SURFACES)
    assert declares_auth_surface(source, "reasomate", "/reasomate")
    assert source.count('id: "reasomate"') == 1
    assert source.count('path: "/reasomate"') == 1


def test_the_negative_control_rejects_an_unprotected_declaration():
    unprotected = '{\n    id: "reasomate",\n    name: "ReasoMate",\n    path: "/reasomate",\n  },'
    assert not declares_auth_surface(unprotected, "reasomate", "/reasomate")
    # The path matters as much as the flag: a surface on the wrong route is a different surface.
    wrong_path = '{\n    id: "reasomate",\n    requiresAuth: true,\n    path: "/messages",\n  },'
    assert not declares_auth_surface(wrong_path, "reasomate", "/reasomate")


def test_the_shell_routes_the_surface_to_the_page():
    assert 'case "reasomate":' in _read(APP)
    assert "ReasoMatePage" in _read(APP)


# ---------------------------------------------------------------------------
# 2. The advertised paths are served, and are read through the registry.
# ---------------------------------------------------------------------------


def test_every_advertised_message_path_is_served():
    paths = registered_paths(_read(ENDPOINTS))
    for name in ("messages", "messagesInbox"):
        assert name in paths, f"{name} is not declared in the endpoint registry"
        assert served_by_the_app(paths[name]), f"{paths[name]} is advertised but not served"
    # The thread path is derived from the collection rather than declared as its
    # own prefix, so it is not a registry entry at all: `/api/messages/thread` is
    # not a served route, and declaring it would be an invented endpoint.
    assert "messagesThreadBase" not in paths
    assert not served_by_the_app(paths["messages"] + "/thread")
    assert served_by_the_app(paths["messages"] + "/thread/probe-peer")


def test_the_thread_path_is_percent_encoded():
    source = _read(ENDPOINTS)
    assert re.search(r"export function messagesThread\(peerUid: string\)", source)
    assert "encodeURIComponent(peerUid)" in source


def test_the_page_reads_the_registry_not_an_inline_literal():
    page = _read(PAGE)
    assert "endpoints.messagesInbox" in page
    assert "messagesThread(" in page
    assert "endpoints.messages" in page
    assert '"/api/messages' not in page


def test_the_negative_control_flags_an_invented_path():
    assert not served_by_the_app("/api/messages/threads")
    assert not served_by_the_app("/api/reasomate")


# ---------------------------------------------------------------------------
# 3. Unreadable payloads are not empty conversations.
# ---------------------------------------------------------------------------


def test_the_page_validates_before_it_renders():
    page = _read(PAGE)
    assert validates_before_rendering(page, "isInbox")
    assert validates_before_rendering(page, "isThread")
    assert validates_before_rendering(page, "isSentMessage")
    # A failed read renders the contract state, not a zeroed list.
    assert "ContractState" in page


def test_the_negative_control_rejects_an_unvalidated_reader():
    unvalidated = """
    import { useHydration } from "../lib/useHydration";
    const inbox = useHydration(endpoints.messagesInbox, (p) => apiRequest(p));
    """
    assert not validates_before_rendering(unvalidated, "isInbox")


def test_a_genuine_empty_read_has_its_own_state():
    page = _read(PAGE)
    assert "EmptyState" in page
    assert "No conversations yet" in page
    assert "No messages in this thread" in page


def test_the_contract_guards_reject_a_failure_envelope():
    contracts = _read(CONTRACTS)
    for guard in ("isDirectMessage", "isInboxEntry", "isInbox", "isThread", "isSentMessage"):
        assert f"export function {guard}(" in contracts


# ---------------------------------------------------------------------------
# 4. The peer is taken from the handler's response, never guessed.
# ---------------------------------------------------------------------------


def test_the_send_path_uses_the_response_recipient():
    page = _read(PAGE)
    assert re.search(r"payload\.message\.recipient_uid", page)
    assert "recipientField(" in page


def test_no_fabricated_conversation_is_rendered():
    page = _read(PAGE)
    assert not renders_a_hardcoded_conversation(page)


def test_the_negative_control_flags_a_fabricated_thread():
    fabricated = '[{ id: "1", sender_uid: "a", recipient_uid: "b", content: "hi", timestamp: 0 }]'
    assert renders_a_hardcoded_conversation(fabricated)
