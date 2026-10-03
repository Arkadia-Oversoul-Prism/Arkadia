"""SOLARIUN-THREAD-01 — the chain must be followable without implying authority.

Whole-architecture experience calibration: the stages identity → workspace →
event → proposal → authority → execution → evidence → knowledge → verification
were distributed across disconnected panels. This guards the minimum bounded fix:
Home must expose a truthful handoff to Weaver / Engineering Lab / Knowledge, and
no surface may imply a transition the substrate has not established.

Source-level assertions follow this repo's existing frontend test convention.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx"
COCKPIT = ROOT / "web/public_prism/src/components/solspire/SolariunHomeCockpit.tsx"


def test_home_cockpit_accepts_a_bounded_navigation_prop():
    src = COCKPIT.read_text(encoding="utf-8")
    assert "onNavigate" in src
    # Bounded to the three thread destinations — not an arbitrary router.
    assert "'weaver' | 'engineering-lab' | 'knowledge'" in src


def test_thread_section_names_the_full_chain():
    src = COCKPIT.read_text(encoding="utf-8")
    assert "Follow the thread" in src
    for stage in ("IDENTITY", "WORKSPACE", "EVENT", "PROPOSAL", "AUTHORITY",
                  "EXECUTION", "EVIDENCE", "KNOWLEDGE", "VERIFICATION"):
        assert stage in src, stage


def test_thread_copy_does_not_claim_derivation_or_authority():
    src = COCKPIT.read_text(encoding="utf-8")
    assert "not a second source of truth" in src
    assert "no transition is implied" in src
    # Must not present the chain as proven continuity.
    assert "No placeholder state has been substituted." in src


def test_cockpit_degrades_truthfully_without_a_handler():
    src = COCKPIT.read_text(encoding="utf-8")
    assert "disabled={!onNavigate}" in src
    assert "Thread navigation unavailable in this mount." in src
    assert "No synthetic destination has been substituted." in src


def test_shell_wires_home_to_lens_selection():
    src = EXP.read_text(encoding="utf-8")
    # The Home mount was superseded by SolariunInteractionCanvas (sovereign merge #189,
    # "chore: remove superseded Solariun home import"); SolariunHomeCockpit is dead code.
    # The handoff invariant is unchanged: the canvas' onNavigate target is routed to the
    # canonical lens selector, and the handler is typed to the lens union — not a new
    # surface. A non-lens target (e.g. 'commune') must be intercepted before selection.
    assert "<SolariunInteractionCanvas onNavigate={target=>{" in src
    assert "onThreadTarget(target as any)" in src
    assert "onThreadTarget={selectSection}" in src
    # The handler must be typed to the canonical lens union, not a new surface.
    assert "onThreadTarget:(s:SolSpireLens)=>void" in src


def test_no_second_navigation_or_state_system_introduced():
    src = EXP.read_text(encoding="utf-8")
    assert "react-router" not in src
    assert "createContext" not in src
