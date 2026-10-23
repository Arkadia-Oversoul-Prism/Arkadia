"""Read-aloud contract — the console's voice surface against the live TTS backend.

`POST /api/tts`, `GET /api/tts/status` and `GET /api/tts/voices` are served by
`api/main.py` and were reachable anonymously in production before this change
(measured: `200`, `X-TTS-Engine: edge_tts`, 20448 bytes). The archived Prism
reached them from three components (`ScrollListenButton.tsx`,
`OracleVoicePlayer.tsx`, `SonataBar.tsx`); the console reached them from none, so
the capability was UNSURFACED rather than absent.

This guard pins the four properties that make the new surface *truthful*, not
merely present. Each has a negative control that feeds the pre-repair shape to
the same detector the live assertion uses, so a detector that matched nothing
cannot pass by accident:

1. The registry entries resolve to handlers the canonical app actually serves,
   and the client reads them through the registry rather than an inline literal.
2. A synthesis failure — including an empty audio body — is reported as a
   failure. A player that renders for a zero-byte response claims success it
   did not have.
3. A voice the active engine cannot deliver is locked with its reason, not
   offered and then silently substituted. `kernel/tts.py` marks `aetheria`
   `requires_elevenlabs`; without a key the backend substitutes the Edge voice.
4. The backend's declared shape is what the client's interfaces declare, read
   from the live app rather than restated from the source.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
VOICE_CLIENT = SRC / "lib" / "voice.ts"
READ_ALOUD = SRC / "components" / "ReadAloud.tsx"
ARKANA_PAGE = SRC / "pages" / "ArkanaPage.tsx"
ENDPOINTS = SRC / "lib" / "endpoints.ts"


# ---------------------------------------------------------------------------
# Detectors (module level, so the negative controls exercise the same code).
# ---------------------------------------------------------------------------


def _strip_js_comments(text: str) -> str:
    """Remove block and line comments so prose cannot masquerade as a path.

    The contract is documented in comments that legitimately name `/api/tts`;
    scanning the raw text would report the documentation as an inlined path.
    """
    text = re.sub(r"/\*[\s\S]*?\*/", " ", text)
    return re.sub(r"(?m)^\s*//.*$", " ", text)


def _inline_backend_literals(text: str, prefix: str = "/api/tts") -> list[str]:
    """Backend paths written as literal text instead of read from the registry.

    The pre-repair shape is ``fetch(`${API_BASE}/api/tts`)`` — the literal is
    *inside* a template substitution, so it is not preceded by a quote and a
    quote-anchored pattern misses exactly the case that matters. The decidable
    property is simpler: a registry read carries no path text at all
    (``endpoints.tts``), so any occurrence of the path in code is a second,
    unreviewed contract. Comments are stripped first.
    """
    code = _strip_js_comments(text)
    return sorted(set(re.findall(re.escape(prefix) + r"[A-Za-z0-9_/\-{}]*", code)))


def _rejects_empty_audio(text: str) -> bool:
    """True when a zero-length synthesis response is treated as a failure."""
    return bool(re.search(r"blob\.size\s*===\s*0", text)) and bool(
        re.search(r"blob\.size\s*===\s*0[\s\S]{0,400}?throw\s", text)
    )


def _balanced(text: str, start: int) -> str:
    """Text from the ``{`` at *start* through its matching ``}``."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return ""


def _function_body(text: str, name: str) -> str:
    """The brace-balanced body of an exported ``function <name>``."""
    match = re.search(rf"export\s+function\s+{re.escape(name)}\s*\([^)]*\)[^{{]*\{{", text)
    if not match:
        return ""
    return _balanced(text, match.end() - 1)


def _lock_rule_is_derived(text: str) -> bool:
    """True when the deliverability rule *decides* from the contract.

    Both flags must be consulted **inside the rule's own body**. Testing for the
    strings anywhere in the file is not enough: the interface declares
    `requires_elevenlabs` and the doc comment names `elevenlabs_active`, so a
    rule that ignores both and hardcodes a voice-name list still satisfied the
    first draft — the live control that hardcoded ``["aetheria"]`` passed it.
    """
    body = _function_body(text, "voiceIsDeliverable")
    if not body:
        return False
    return "requires_elevenlabs" in body and "elevenlabs_active" in body


def _component_uses_the_shared_rule(text: str) -> bool:
    """True when the component consumes the one rule instead of re-deriving it.

    Duplicating the rule in the component would be a second source of truth for
    the same product decision.
    """
    return bool(re.search(r"voiceIsDeliverable\s*\(", text))


def _synthesis_is_user_initiated(text: str) -> bool:
    """True when playback begins from an explicit control, not on mount.

    `autoPlay` or a `play()` reachable from an effect would start a real backend
    synthesis without the user asking for it.
    """
    if re.search(r"autoPlay", text):
        return False
    return bool(re.search(r"onClick=\{[^}]*play\(\)", text) or re.search(r"onClick=\{[^}]*void play\(\)", text))


def _renders_read_aloud_for_assistant_turns(text: str) -> bool:
    """True when the assistant branch itself renders ``ReadAloud``.

    The mount must be *inside* the assistant conditional, not merely near it. A
    proximity window is satisfied by any nearby ``turn.role === "assistant"``
    text — the page's own ``className`` ternary provides one — so the live
    control that neutralised the condition to ``{false && (`` still passed the
    first draft. The branch's balanced block is extracted instead.
    """
    match = re.search(r'turn\.role\s*===\s*"assistant"\s*&&\s*\(', text)
    if not match:
        return False
    block = _balanced(text, text.index("(", match.end() - 1))
    return "<ReadAloud" in block


def _declared_endpoints(text: str) -> dict[str, str]:
    body = re.search(r"export const endpoints\s*=\s*\{(.*?)\}\s*as const;", text, re.DOTALL)
    assert body, "endpoints.ts declares no `endpoints` object literal"
    return dict(re.findall(r'(\w+):\s*"([^"]+)"', body.group(1)))


def _served_paths() -> set[str]:
    from api.main import app

    return set(app.openapi()["paths"].keys())


# ---------------------------------------------------------------------------
# 1. Registry binding — one API surface map, bound to served handlers
# ---------------------------------------------------------------------------


def test_voice_registry_entries_are_served_by_the_canonical_app():
    declared = _declared_endpoints(ENDPOINTS.read_text(encoding="utf-8"))
    served = _served_paths()
    for name in ("tts", "ttsStatus", "ttsVoices"):
        assert name in declared, f"endpoints.ts declares no {name!r} entry"
        assert declared[name] in served, f"{declared[name]!r} is not served by api.main:app"


def test_voice_client_reads_paths_through_the_registry():
    """The client must not carry its own copy of the backend paths."""
    text = VOICE_CLIENT.read_text(encoding="utf-8")
    assert _inline_backend_literals(text) == [], (
        "voice.ts inlines a backend path instead of reading the registry: "
        + ", ".join(_inline_backend_literals(text))
    )
    assert "endpoints.tts" in text, "voice.ts does not reference the registry"


def test_detector_flags_an_inlined_backend_path():
    """Negative control: the pre-repair shape (a literal path) must be reported.

    The shape that matters is a literal *inside* a template substitution, which
    a quote-anchored pattern does not see — the first draft of this detector
    missed it and this control caught the miss.
    """
    pre_repair = 'fetch(`${API_BASE}/api/tts`, { method: "POST" })'
    assert _inline_backend_literals(pre_repair) == ["/api/tts"]
    quoted = 'const p = "/api/tts";'
    assert _inline_backend_literals(quoted) == ["/api/tts"]
    legit = 'fetch(`${API_BASE}${endpoints.tts}`, { method: "POST" })'
    assert _inline_backend_literals(legit) == []
    # Prose naming the route must not be reported as an inlined contract.
    documented = "/** Reaches /api/tts through the registry. */\n// see /api/tts/status\n"
    assert _inline_backend_literals(documented) == []


# ---------------------------------------------------------------------------
# 2. No fabricated success
# ---------------------------------------------------------------------------


def test_empty_audio_body_is_a_failure_not_a_silent_success():
    text = VOICE_CLIENT.read_text(encoding="utf-8")
    assert _rejects_empty_audio(text), (
        "voice.ts does not reject a zero-byte synthesis response; a player would "
        "render for an empty body and imply success"
    )


def test_detector_flags_a_client_that_accepts_an_empty_body():
    """Negative control: without the size check the detector must report."""
    pre_repair = "const blob = await response.blob();\nreturn { blob, engine };\n"
    assert not _rejects_empty_audio(pre_repair)
    repaired = (
        "const blob = await response.blob();\n"
        "if (blob.size === 0) {\n  throw new ApiError('empty audio body', {});\n}\n"
    )
    assert _rejects_empty_audio(repaired)


# ---------------------------------------------------------------------------
# 3. Voice honesty — an undeliverable voice is locked, not substituted
# ---------------------------------------------------------------------------


def test_voice_deliverability_rule_has_one_source_of_truth():
    """The rule lives in the client and the component consumes it."""
    client = VOICE_CLIENT.read_text(encoding="utf-8")
    component = READ_ALOUD.read_text(encoding="utf-8")
    assert _lock_rule_is_derived(client), (
        "the deliverability rule must consult requires_elevenlabs and the reported "
        "engine state, not a hardcoded list of voice names"
    )
    assert _component_uses_the_shared_rule(component), (
        "ReadAloud must consume voiceIsDeliverable() rather than re-deriving the rule"
    )
    # The lock must be visible to the user, not merely internal state.
    assert "🔒" in component, "a locked voice must be marked in the UI"


def test_detector_flags_a_hardcoded_lock_list():
    """Negative control: a hardcoded locked-voice list must not satisfy the rule.

    The first draft of this detector tested for the flag names *anywhere in the
    file*, so a rule that ignored both and hardcoded ``["aetheria"]`` passed it —
    the file's interface and doc comment mention the flags. The rule's own body
    is now what is judged, and this control pins that.
    """
    hardcoded = 'const LOCKED = ["aetheria"];\nconst usable = !LOCKED.includes(key);\n'
    assert not _lock_rule_is_derived(hardcoded)
    # A file whose interface and comment name both flags, but whose rule ignores
    # them, must still be reported.
    file_with_flags_but_hardcoded_rule = (
        "export interface VoiceDef { requires_elevenlabs?: boolean }\n"
        "/** elevenlabs_active is reported by /api/tts/status */\n"
        "export function voiceIsDeliverable(v, s) {\n"
        '  return !["aetheria"].includes(v.name);\n'
        "}\n"
    )
    assert not _lock_rule_is_derived(file_with_flags_but_hardcoded_rule), (
        "a hardcoded rule must not pass merely because the flags appear elsewhere"
    )
    derived = (
        "export function voiceIsDeliverable(voice, status) {\n"
        "  if (!voice.requires_elevenlabs) return true;\n"
        "  return Boolean(status?.elevenlabs_active);\n"
        "}\n"
    )
    assert _lock_rule_is_derived(derived)
    assert not _component_uses_the_shared_rule("const usable = !LOCKED.includes(key);")
    assert _component_uses_the_shared_rule("const usable = voiceIsDeliverable(def, status);")


def test_synthesis_is_not_started_without_a_user_action():
    text = READ_ALOUD.read_text(encoding="utf-8")
    assert _synthesis_is_user_initiated(text), (
        "ReadAloud must synthesise only from an explicit control, never on mount"
    )


def test_detector_flags_autoplay():
    assert not _synthesis_is_user_initiated("<audio autoPlay src={url} />")
    assert _synthesis_is_user_initiated('<button onClick={() => void play()}>Listen</button>')


# ---------------------------------------------------------------------------
# 4. The surface is actually mounted
# ---------------------------------------------------------------------------


def test_arkana_replies_expose_read_aloud():
    text = ARKANA_PAGE.read_text(encoding="utf-8")
    assert "ReadAloud" in text, "ArkanaPage does not import ReadAloud"
    assert _renders_read_aloud_for_assistant_turns(text), (
        "ReadAloud must render for assistant turns, not for the user's own message"
    )


def test_detector_flags_a_page_without_the_mount():
    """Negative control: an unmounted or neutralised branch must be reported.

    The first draft used a proximity window, which the page's own
    ``className={turn.role === "assistant" ? … }`` ternary satisfies — so
    neutralising the real condition to ``{false && (`` still passed it. The
    control pins the strengthened detector.
    """
    pre_slice = '<p className="text-sm">{turn.content}</p>\n'
    assert not _renders_read_aloud_for_assistant_turns(pre_slice)
    # The proximity shape the first draft accepted, with the condition dead.
    neutralised = (
        'className={turn.role === "assistant" ? "text-emerald" : "text-white"}\n'
        '<p>{turn.content}</p>\n'
        '{false && (\n  <ReadAloud text={turn.content} />\n)}\n'
    )
    assert not _renders_read_aloud_for_assistant_turns(neutralised), (
        "a dead branch near assistant prose must not read as a mount"
    )
    mounted = (
        '{turn.role === "assistant" && (\n'
        '  <ReadAloud text={turn.content} />\n'
        ")}\n"
    )
    assert _renders_read_aloud_for_assistant_turns(mounted)


# ---------------------------------------------------------------------------
# 5. The client's declared shape is the served shape
# ---------------------------------------------------------------------------


def test_status_contract_declares_the_fields_the_client_reads():
    """The TS `TtsStatus` interface must describe what the endpoint returns.

    Read from the live app rather than restated, so a backend rename reddens
    this instead of silently rendering `undefined`.
    """
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        status = client.get("/api/tts/status")
    assert status.status_code == 200, status.text
    payload = status.json()
    client_src = VOICE_CLIENT.read_text(encoding="utf-8")
    for field in ("engine", "elevenlabs_active", "edge_tts_active", "ready", "default"):
        assert field in payload, f"/api/tts/status no longer reports {field!r}"
        assert re.search(rf"^\s*{field}[?]?:", client_src, re.MULTILINE), (
            f"the client interface does not declare {field!r}"
        )


def test_voice_catalogue_shape_matches_the_client_interface():
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        catalog = client.get("/api/tts/voices")
    assert catalog.status_code == 200, catalog.text
    payload = catalog.json()
    assert isinstance(payload.get("voices"), dict) and payload["voices"], (
        "/api/tts/voices no longer returns a non-empty voice map"
    )
    assert payload.get("default") in payload["voices"], (
        "the declared default voice is not present in the catalogue"
    )
    # Every voice must carry the fields the UI renders; a voice without a name
    # would render as a blank option.
    for key, voice in payload["voices"].items():
        assert voice.get("name"), f"voice {key!r} declares no name"


def test_aetheria_is_declared_elevenlabs_only():
    """The one voice the console locks must still be marked as restricted.

    If `kernel/tts.py` ever makes `aetheria` Edge-deliverable, this fails so the
    lock is re-derived rather than left over-restrictive.
    """
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        payload = client.get("/api/tts/voices").json()
    assert payload["voices"]["aetheria"].get("requires_elevenlabs") is True, (
        "aetheria is no longer flagged requires_elevenlabs; the console's lock must "
        "be re-derived from the contract rather than kept"
    )
