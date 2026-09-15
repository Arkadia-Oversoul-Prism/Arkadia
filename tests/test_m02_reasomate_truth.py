"""M02 — ReasoMate truth: route and surface resolution.

ReasoMate must resolve to itself. `/reasomate` must not silently become Oracle,
and the messenger must mount on the existing Social Field component rather than a
second conversational system.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web" / "public_prism" / "src" / "App.tsx"
REASOMATE = ROOT / "web" / "public_prism" / "src" / "pages" / "ReasoMatePage.tsx"
FIELD = ROOT / "web" / "public_prism" / "src" / "pages" / "SocialFieldVerified.tsx"
NOVA = ROOT / "web" / "public_prism" / "src" / "pages" / "NovaNetPage.tsx"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_reasomate_route_does_not_redirect_to_oracle():
    """The alias that silently retargeted ReasoMate at Oracle must be gone."""
    app = _read(APP)
    assert "'/reasomate': {view:'commune'}" not in app
    assert "if (requested === 'reasomate') next = {view:'commune',path:'/oracle'}" not in app


def test_reasomate_resolves_to_its_own_view_directly():
    """Deep-linking /reasomate lands on the reasomate view, not home or oracle."""
    app = _read(APP)
    assert "'/reasomate': 'reasomate'" in app


def test_reasomate_view_routes_to_its_own_path():
    app = _read(APP)
    assert "reasomate: '/reasomate'" in app


def test_reasomate_view_still_mounts_reasomate_page():
    app = _read(APP)
    assert "view === 'reasomate'" in app
    assert "ReasoMatePage" in app


def test_reasomate_reuses_the_single_social_field_component():
    """One component, two windows — no second messenger or chat component."""
    page = _read(REASOMATE)
    assert "SocialFieldVerified" in page
    assert 'initialMode="reasomate"' in page


def test_social_field_accepts_initial_mode():
    field = _read(FIELD)
    assert "initialMode" in field
    assert "useState<'field' | 'reasomate'>(initialMode)" in field


def test_novanet_defaults_to_the_public_field():
    novanet = _read(NOVA)
    assert "SocialFieldVerified" in novanet
    assert 'initialMode="reasomate"' not in novanet


def test_reasomate_uses_the_existing_messaging_runtime():
    """Backend truth: ReasoMate reads api/messages, not a parallel store."""
    messenger = ROOT / "web" / "public_prism" / "src" / "pages" / "SocialMessenger.tsx"
    text = _read(messenger)
    assert "/api/messages" in text
    assert "/api/relationships/" in text
    assert "apiRequest" in text or "apiFetch" in text


def test_no_second_identity_or_memory_store_introduced():
    """M02 is a routing/lens correction — it must not add persistence layers."""
    page = _read(REASOMATE)
    for forbidden in ("indexedDB", "localStorage", "createStore", "new Map(", "firestore"):
        assert forbidden not in page


def test_reasomate_view_is_not_removed_from_union():
    app = _read(APP)
    m = re.search(r"type View\s*=\s*((?:.|\n)*?);", app)
    assert m
    assert "reasomate" in m.group(1)