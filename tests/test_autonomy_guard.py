"""
Tests for Autonomy Guard — Cycle 9

Ensures autonomy is disabled by default and properly constrained.
"""

import pytest
from weaver.autonomy.guard import AutonomyGuard
from weaver.autonomy.proposal_engine import ProposalEngine


def test_autonomy_disabled_by_default():
    """Autonomy must be disabled by default."""
    guard = AutonomyGuard({"status": "disabled"})
    assert guard.allowed() is False


def test_kill_switch_enabled_by_default():
    """Kill-switch must be enabled by default."""
    guard = AutonomyGuard({"kill_switch": {"default": True}})
    assert guard.allowed() is False


def test_autonomy_requires_explicit_enable():
    """Autonomy requires status='enabled' AND kill_switch default=False."""
    guard = AutonomyGuard({
        "status": "enabled",
        "kill_switch": {"default": False}
    })
    assert guard.allowed() is True


def test_forbidden_paths_blocked():
    """Forbidden paths cannot be modified."""
    guard = AutonomyGuard({
        "forbidden_paths": ["governance/", "sanctum/", ".git/", ".github/"]
    })
    assert guard.path_allowed("governance/autonomy.json") is False
    assert guard.path_allowed("sanctum/status.json") is False
    assert guard.path_allowed(".git/config") is False
    assert guard.path_allowed("weaver/autonomy/guard.py") is True


def test_change_volume_limits():
    """Changes must respect file and line limits."""
    guard = AutonomyGuard({
        "conditions": {
            "max_files_changed": 5,
            "max_lines_changed": 300
        }
    })
    assert guard.can_write_files(3, 200) is True
    assert guard.can_write_files(5, 300) is True
    assert guard.can_write_files(6, 300) is False
    assert guard.can_write_files(5, 301) is False


def test_proposal_engine_never_writes():
    """Proposal engine must never write files."""
    engine = ProposalEngine()
    proposal = engine.propose("test task")
    assert proposal["requires_human"] is True
    assert proposal["changes"] == []


def test_proposal_engine_deterministic():
    """Proposal engine is deterministic."""
    engine = ProposalEngine()
    p1 = engine.propose("test")
    p2 = engine.propose("test")
    assert p1["task"] == p2["task"]
    assert p1["requires_human"] == p2["requires_human"]


def test_check_conditions_returns_all():
    """Check conditions returns all configured constraints."""
    config = {
        "conditions": {
            "tests_must_pass": True,
            "proposal_reviewed": True,
            "human_present": True,
            "max_files_changed": 5,
            "max_lines_changed": 300,
        }
    }
    guard = AutonomyGuard(config)
    conditions = guard.check_conditions()
    assert "tests_must_pass" in conditions
    assert "proposal_reviewed" in conditions
    assert "human_present" in conditions
    assert "max_files_changed" in conditions
    assert "max_lines_changed" in conditions
