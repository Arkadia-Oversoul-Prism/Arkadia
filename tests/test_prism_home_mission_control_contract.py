"""Home surface — Mission Control primary workspace (ARE-HOME-001).

Flagship Home elevates `MissionWorkspace` as the primary operational workspace
for an authenticated node, without altering the identity-aware entry contract
(PRR-10 / test_prism_home_entry_contract.py).

What is asserted:

  * HomePage imports and renders `MissionWorkspace`
  * a Mission Control section (`data-testid="home-mission-control"`) exists
  * that section is gated on `isAuthenticated`
  * MissionWorkspace appears inside the Mission Control section
  * Mission Control precedes the capability groups in source order
  * the existing entry primary/secondary testids remain present
  * a negative control per load-bearing detector

Domain: the Arkadia Console (`web/arkadia_console`). This is a presentation-
order and wiring contract, not a runtime behaviour test of the Lab substrate.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
HOME_PATH = SRC / "pages" / "HomePage.tsx"

HOME = HOME_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (module-level so negative controls exercise the same code).
# ---------------------------------------------------------------------------


def _has_mission_workspace_import(text: str) -> bool:
    return bool(
        re.search(
            r'import\s*\{\s*MissionWorkspace\s*\}\s*from\s*["\']\.\./components/lab/MissionWorkspace["\']',
            text,
        )
    )


def _has_mission_control_section(text: str) -> bool:
    return 'data-testid="home-mission-control"' in text


def _mission_control_is_auth_gated(text: str) -> bool:
    """Mission Control must only render when the viewer is authenticated."""
    return bool(
        re.search(
            r"\{isAuthenticated\s*&&\s*\(\s*<section[^>]*data-testid=\"home-mission-control\"",
            text,
            re.DOTALL,
        )
    )


def _mission_workspace_inside_mission_control(text: str) -> bool:
    """`<MissionWorkspace />` must appear inside the home-mission-control section."""
    match = re.search(
        r'data-testid="home-mission-control".*?</section>',
        text,
        re.DOTALL,
    )
    if not match:
        return False
    return "<MissionWorkspace" in match.group(0)


def _mission_control_precedes_capabilities(text: str) -> bool:
    """Mission Control must appear before the capability groups in source order."""
    mc = text.find('data-testid="home-mission-control"')
    caps = text.find('id="capabilities-heading"')
    if mc < 0 or caps < 0:
        return False
    return mc < caps


def _entry_contract_still_present(text: str) -> bool:
    """The PRR-10 entry primary/secondary testids must remain."""
    return (
        'data-testid="home-entry-primary"' in text
        and 'data-testid="home-entry-secondary"' in text
    )


# ---------------------------------------------------------------------------
# 1. MissionWorkspace is wired into Home.
# ---------------------------------------------------------------------------


def test_home_imports_mission_workspace():
    assert _has_mission_workspace_import(HOME), (
        "HomePage must import MissionWorkspace from the lab components — "
        "Mission Control is the primary operational workspace on the authenticated Home"
    )


def test_negative_control_import_detector():
    synthetic = HOME.replace(
        'import { MissionWorkspace } from "../components/lab/MissionWorkspace";',
        'import { SomethingElse } from "../components/lab/SomethingElse";',
    )
    assert not _has_mission_workspace_import(synthetic)
    assert _has_mission_workspace_import(HOME)


# ---------------------------------------------------------------------------
# 2. Mission Control section exists and is auth-gated.
# ---------------------------------------------------------------------------


def test_home_renders_mission_control_section():
    assert _has_mission_control_section(HOME), (
        "HomePage must render a Mission Control section with "
        'data-testid="home-mission-control"'
    )


def test_mission_control_is_gated_on_authentication():
    assert _mission_control_is_auth_gated(HOME), (
        "Mission Control must only mount when isAuthenticated is true — "
        "anonymous visitors must not see the operational workspace"
    )


def test_negative_control_ungated_mission_control():
    """A Mission Control section without the isAuthenticated gate must fail."""
    synthetic = HOME.replace(
        "{isAuthenticated && (",
        "{(",
        1,
    )
    # Only assert the gate detector; other content may still match.
    assert not _mission_control_is_auth_gated(synthetic)
    assert _mission_control_is_auth_gated(HOME)


# ---------------------------------------------------------------------------
# 3. MissionWorkspace lives inside Mission Control.
# ---------------------------------------------------------------------------


def test_mission_workspace_is_inside_mission_control():
    assert _mission_workspace_inside_mission_control(HOME), (
        "<MissionWorkspace /> must be rendered inside the home-mission-control section"
    )


def test_negative_control_workspace_outside_section():
    synthetic = HOME.replace(
        "<MissionWorkspace />",
        "",
        1,
    )
    assert not _mission_workspace_inside_mission_control(synthetic)
    assert _mission_workspace_inside_mission_control(HOME)


# ---------------------------------------------------------------------------
# 4. Hierarchy: Mission Control precedes capability groups.
# ---------------------------------------------------------------------------


def test_mission_control_precedes_capability_groups():
    assert _mission_control_precedes_capabilities(HOME), (
        "Mission Control must appear before the capability groups in source order — "
        "it is the primary operational workspace, not a secondary panel"
    )


def test_negative_control_reversed_order():
    """If Mission Control were moved after capabilities, the detector must fire."""
    mc_marker = 'data-testid="home-mission-control"'
    caps_marker = 'id="capabilities-heading"'
    mc_pos = HOME.find(mc_marker)
    caps_pos = HOME.find(caps_marker)
    assert mc_pos >= 0 and caps_pos >= 0 and mc_pos < caps_pos
    # Swap the two markers only — enough to invert order detection.
    synthetic = HOME.replace(mc_marker, "__MC_TMP__", 1).replace(
        caps_marker, mc_marker, 1
    ).replace("__MC_TMP__", caps_marker, 1)
    assert not _mission_control_precedes_capabilities(synthetic)
    assert _mission_control_precedes_capabilities(HOME)


# ---------------------------------------------------------------------------
# 5. Existing entry contract remains intact.
# ---------------------------------------------------------------------------


def test_entry_contract_still_present_alongside_mission_control():
    assert _entry_contract_still_present(HOME), (
        "Elevating Mission Control must not remove the identity-aware entry "
        "primary/secondary actions required by test_prism_home_entry_contract"
    )
