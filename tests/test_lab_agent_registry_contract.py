"""Engineering Lab deployed-agent registry -- backend oracle (Workstream 4).

``GET /api/lab/engineering/agents`` -> ``{"agents": [...]}`` returns the
owner-scoped bounded agents an identity has deployed. This file drives the
**real** runtime over an isolated database and pins the shape the console reads,
plus the boundary the contract states: a deployed agent is a *declaration* of
bounded capability, never implicit authority.
"""
from __future__ import annotations

import pytest

OWNER = "subject-owner"
OTHER = "subject-other"


@pytest.fixture()
def runtime(tmp_path, monkeypatch):
    from lab.engineering_lab import store as store_mod
    from lab.engineering_lab.runtime import EngineeringLabRuntime

    monkeypatch.setattr(store_mod, "_DB_PATH", str(tmp_path / "lab.db"))
    monkeypatch.setattr(store_mod, "_GLOBAL_STORE", None)
    return EngineeringLabRuntime(store=store_mod.get_store())


def test_register_agent_returns_the_declared_envelope(runtime):
    agent = runtime.register_agent(subject_ref=OWNER, role="WEAVER", display_name="Weaver")
    assert set(agent) >= {
        "agent_id",
        "role",
        "display_name",
        "capabilities",
        "tool_access",
        "model_ref",
        "created_at",
    }
    assert agent["role"] == "WEAVER"
    assert set(agent["tool_access"]) >= {"tools", "write_allowed", "network_allowed"}


def test_list_agents_returns_owner_scoped_records(runtime):
    runtime.register_agent(subject_ref=OWNER, role="WEAVER", display_name="W")
    runtime.register_agent(subject_ref=OWNER, role="REVIEWER", display_name="R")
    listed = runtime._store.list_agents(OWNER)
    assert len(listed) == 2
    assert {a["role"] for a in listed} == {"WEAVER", "REVIEWER"}
    assert runtime._store.list_agents(OTHER) == []


def test_a_reviewer_agent_cannot_be_granted_edit(runtime):
    """A capability may not exceed the role's ceiling -- a REVIEWER cannot edit."""
    from lab.engineering_lab.contracts import BoundaryViolation

    with pytest.raises(BoundaryViolation):
        runtime.register_agent(subject_ref=OWNER, role="REVIEWER", capabilities=("EDIT",))


def test_unknown_role_is_rejected(runtime):
    with pytest.raises(ValueError):
        runtime.register_agent(subject_ref=OWNER, role="engineer")


def test_deployed_agent_does_not_imply_write_authority(runtime):
    """The contract's core claim: a deployed agent never receives implicit
    authority. A read-only role must not carry write access."""
    agent = runtime.register_agent(subject_ref=OWNER, role="SENTINEL", display_name="S")
    assert agent["tool_access"]["write_allowed"] is False
    for forbidden in ("EXECUTE", "MERGE", "DEPLOY", "AUTHORIZE"):
        assert forbidden not in agent["capabilities"]


def test_agents_route_is_a_declared_get_route():
    from pathlib import Path

    routes = (Path(__file__).resolve().parents[1] / "api" / "lab_routes.py").read_text(encoding="utf-8")
    assert '@router.get("/engineering/agents")' in routes


def test_agents_route_is_served():
    from api.main import app

    assert "/api/lab/engineering/agents" in app.openapi()["paths"]


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------

def test_negative_control_ceiling_check_is_not_vacuous(runtime):
    """The ceiling detector must pass a role that genuinely holds EDIT
    (BUILDER) -- proof the REVIEWER rejection above is about the ceiling, not a
    blanket ban on EDIT."""
    agent = runtime.register_agent(subject_ref=OWNER, role="BUILDER", capabilities=("EDIT",))
    assert "EDIT" in agent["capabilities"]
