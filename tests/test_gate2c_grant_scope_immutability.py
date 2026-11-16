"""Gate 2c — grant scope and operation naming at the tool boundary.

Gate 2b bound the native agent loop to the executive-delegation contract, but
deliberately left the grant's *scope* and *operation naming* to the envelope
derived once at start. This file answers the assurance question that left open:
are those fields immutable after creation, and if not, are they still enforced
at each dispatch?

The answer, established here rather than assumed:

* ``scope_ref`` is effectively immutable for a live run. ``attach_authorization``
  refuses to rebind a session unless it is still ``PROPOSED``, so the
  authorization reference cannot be swapped once the session is AUTHORIZED.
* ``operations_allowed`` is **not** immutable. ``el_authorizations`` stores the
  whole record as a mutable JSON blob, and every mutator rewrites that blob
  wholesale. A narrowing therefore *can* land after the envelope was computed.

That second fact was a real gap, reproduced before the fix: narrowing the grant
mid-run still let ``filesystem.read`` execute and return file content, because
the guard re-read the grant but never re-checked that the tool's operation was
still named by it. The fix re-checks operation naming per call. It only ever
narrows — a tool outside the envelope is already refused by ``granted`` — so
existing human-authorized execution semantics are preserved, not loosened.

Every test asserts a refusal or a preserved permission; none weakens an
existing test. The agent is never commissioned: each delegation is created in a
temporary database and torn down with it.
"""
from __future__ import annotations

import json
import sqlite3
import time

import pytest

import executive_office.registry as registry_module
import lab.engineering_lab.gateway as gateway_mod
import lab.engineering_lab.store as lab_store_module
import weaver.authorization_revocation as revocation_module
import weaver.enterprise_orchestration as ew
from executive_office.control import FounderDelegationControl
from executive_office.registry import DelegationRegistry
from lab.engineering_lab.events import EventStream
from lab.engineering_lab.gateway import ModelAdapter, ModelGateway, ModelResponse
from lab.engineering_lab.runtime import EngineeringLabRuntime
from lab.engineering_lab.sandbox import SandboxPolicy
from lab.engineering_lab.store import EngineeringLabStore

FOUNDER_UID = "founder-uid-gate2c"
WORKSPACE_ID = "ws-gate2c"
SUBJECT = "subject-gate2c"


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def stores(tmp_path, monkeypatch):
    db = str(tmp_path / "gate2c.db")
    monkeypatch.setattr(registry_module, "_DB_PATH", db)
    monkeypatch.setattr(revocation_module, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    monkeypatch.setattr(lab_store_module, "_DB_PATH", db)
    return {"db": db, "registry": DelegationRegistry(db_path=db)}


@pytest.fixture()
def founder():
    return {"uid": FOUNDER_UID, "access_level": 3, "role": "Flamekeeper"}


@pytest.fixture()
def workspace(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "README.md").write_text("# workspace\n", encoding="utf-8")
    return root


class ScriptedAdapter(ModelAdapter):
    """Deterministic stub: one tool call, then stop."""

    def __init__(self, provider: str, script: list[dict], on_first=None) -> None:
        self.provider = provider
        self._script = script
        self._index = 0
        self._on_first = on_first

    def generate(self, *, model, messages, tools=None, **options) -> ModelResponse:
        if self._index >= len(self._script):
            return ModelResponse(self.provider, model, text="done", tool_calls=[])
        step = self._script[self._index]
        self._index += 1
        if self._index == 1 and self._on_first is not None:
            # Mutate the grant *during* the run, after the envelope was derived.
            self._on_first()
        return ModelResponse(
            self.provider, model, text=step.get("text", ""),
            tool_calls=step.get("tool_calls", []),
        )


READ_SCRIPT = [
    {"tool_calls": [{"name": "filesystem.read", "arguments": {"path": "README.md"}}]},
    {"text": "done", "tool_calls": []},
]


def _grant(stores, founder, *, ttl=3600):
    return FounderDelegationControl(registry=stores["registry"]).grant(
        founder=founder,
        owner_uid=FOUNDER_UID,
        workspace_id=WORKSPACE_ID,
        capabilities=["read_project_metadata"],
        resources=["project-1"],
        expires_at=time.time() + ttl,
    )


def _runtime(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", str(tmp_path / "data"))
    stream = EventStream(log_path=str(tmp_path / "events.jsonl"))
    return EngineeringLabRuntime(store=EngineeringLabStore(), stream=stream)


def _session(runtime, *, delegation_id, delegation_epoch, operations=("read",)):
    agent = runtime.register_agent(
        subject_ref=SUBJECT, role="BUILDER", display_name="gate2c-agent"
    )
    session = runtime.open_session(
        subject_ref=SUBJECT,
        agent_id=agent["agent_id"],
        workspace_ref=WORKSPACE_ID,
        objective="gate2c",
    )
    auth = runtime.record_authorization(
        subject_ref=SUBJECT,
        scope_ref=session["session_id"],
        operations_allowed=operations,
        delegation_id=delegation_id,
        delegation_epoch=delegation_epoch,
    )
    runtime._store.attach_authorization(
        session["session_id"], SUBJECT, auth["authorization_id"]
    )
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    return runtime.get_session(session["session_id"], SUBJECT), auth


def _rewrite_payload(db: str, authorization_id: str, mutate) -> None:
    """Rewrite the stored JSON blob directly — the real mutability surface.

    This is not a contrivance: every store mutator (revoke, consume,
    revoke_for_delegation) rewrites this same blob wholesale, so a field that
    is not re-read at dispatch is a field that can change under a live run.
    """
    conn = sqlite3.connect(db)
    try:
        row = conn.execute(
            "SELECT payload FROM el_authorizations WHERE authorization_id = ?",
            (authorization_id,),
        ).fetchone()
        record = json.loads(row[0])
        mutate(record)
        conn.execute(
            "UPDATE el_authorizations SET payload = ? WHERE authorization_id = ?",
            (json.dumps(record), authorization_id),
        )
        conn.commit()
    finally:
        conn.close()


def _run(runtime, session, workspace, monkeypatch, *, script=None, on_first=None):
    gateway = ModelGateway()
    gateway.register_adapter(
        "ollama", ScriptedAdapter("ollama", script or READ_SCRIPT, on_first=on_first)
    )
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)
    return runtime.execute_agent_loop(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        objective="read the readme",
        provider="ollama",
        model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("git",)),
    )


def _executed(out) -> bool:
    return any(
        t["tool_name"] and (t["observation"] or {}).get("ok") for t in out["turns"]
    )


# ── 1. scope_ref is immutable for a live run ─────────────────────────────────

def test_scope_ref_cannot_be_rebound_once_authorized(tmp_path, stores, founder):
    """The authorization reference cannot be swapped after AUTHORIZED.

    ``attach_authorization`` is the only way to bind a grant to a session, and
    it refuses any session that has left PROPOSED. So a broader grant cannot be
    substituted for the one the envelope was derived from.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, pytest.MonkeyPatch())
    session, _ = _session(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    # A second, broader grant scoped to the same session.
    broader = runtime.record_authorization(
        subject_ref=SUBJECT,
        scope_ref=session["session_id"],
        operations_allowed=("read", "write", "run"),
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    with pytest.raises(ValueError, match="PROPOSED"):
        runtime._store.attach_authorization(
            session["session_id"], SUBJECT, broader["authorization_id"]
        )

    # The session still points at the original grant.
    current = runtime.get_session(session["session_id"], SUBJECT)
    assert current["authorization_ref"] == session["authorization_ref"]


def test_scope_mismatch_is_refused_at_the_dispatch_gate(tmp_path, stores, founder):
    """A grant scoped to another session is refused, not silently accepted."""
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, pytest.MonkeyPatch())
    session, _ = _session(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    # Point the stored grant at a different scope.
    _rewrite_payload(
        stores["db"],
        session["authorization_ref"],
        lambda r: r.__setitem__("scope_ref", "some-other-session"),
    )

    from lab.engineering_lab.contracts import BoundaryViolation

    with pytest.raises(BoundaryViolation, match="not scoped to this session"):
        runtime.assert_session_dispatchable(session, SUBJECT, "read")


# ── 2. operations_allowed is mutable — and now enforced per call ─────────────

def test_narrowing_operations_mid_run_blocks_the_next_tool_call(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """The reproduction, now refused.

    Before the Gate 2c fix this returned ``loop_state=DONE`` with the file's
    content in the observation: the guard re-read the grant but never checked
    that the tool's operation was still named by it, so a withdrawal made
    during the run only took effect on the next run.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, auth = _session(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    def withdraw_read():
        _rewrite_payload(
            stores["db"], auth["authorization_id"],
            lambda r: r.__setitem__("operations_allowed", []),
        )

    out = _run(runtime, session, workspace, monkeypatch, on_first=withdraw_read)

    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out), "a withdrawn operation must not execute"
    assert "no longer permits 'read'" in out["loop_reason"]
    denied = [t for t in out["turns"] if t["decision"] == "DENIED"]
    assert denied and denied[0]["observation"]["denied"] is True


def test_narrowing_to_a_different_operation_blocks_the_original(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """Replacing 'read' with 'write' must not leave 'read' executable."""
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, auth = _session(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    def swap_operation():
        _rewrite_payload(
            stores["db"], auth["authorization_id"],
            lambda r: r.__setitem__("operations_allowed", ["write"]),
        )

    out = _run(runtime, session, workspace, monkeypatch, on_first=swap_operation)

    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "no longer permits 'read'" in out["loop_reason"]


def test_widening_operations_mid_run_cannot_add_a_tool(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """Widening is inert: the envelope is a ceiling the guard cannot raise.

    This is the other half of the assurance question. Because the envelope is
    frozen at ``granted=effective``, a grant widened mid-run cannot introduce a
    tool the run was never given — the registry refuses it before the sandbox.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, auth = _session(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    def widen():
        # ``filesystem.propose_edit`` requires the ``candidate_write``
        # operation, so the grant is widened with that exact name — otherwise
        # the refusal would come from the grant and prove nothing about the
        # envelope.
        _rewrite_payload(
            stores["db"], auth["authorization_id"],
            lambda r: r.__setitem__(
                "operations_allowed", ["read", "candidate_write", "run"]
            ),
        )

    write_script = [
        {"tool_calls": [{"name": "filesystem.propose_edit",
                         "arguments": {"path": "README.md", "content": "x"}}]},
        {"text": "done", "tool_calls": []},
    ]
    out = _run(
        runtime, session, workspace, monkeypatch,
        script=write_script, on_first=widen,
    )

    assert not _executed(out), "a widened grant must not add a tool mid-run"
    # The grant really was widened — the refusal is the envelope, not the grant.
    stored = runtime._store.get_authorization(auth["authorization_id"], SUBJECT)
    assert "candidate_write" in stored["operations_allowed"]
    assert any(
        "not granted to this run" in str((t["observation"] or {}).get("error", ""))
        for t in out["turns"] if t["tool_name"]
    )


def test_unchanged_grant_still_executes(tmp_path, stores, founder, workspace, monkeypatch):
    """The fix must not break the ordinary, fully-authorized path.

    A guard that refuses everything would pass every test above. This one
    proves the permitted operation still runs when nothing was withdrawn.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    out = _run(runtime, session, workspace, monkeypatch)

    assert out["loop_state"] == "DONE"
    assert _executed(out), "an unchanged, permitted grant must still execute"
    assert "# workspace" in str(
        [t for t in out["turns"] if t["tool_name"]][0]["observation"]["content"]
    )


def test_operation_naming_is_rechecked_even_without_a_delegation(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """The check is a grant check, not a delegation check.

    A plain human authorization with no ``delegation_id`` must be narrowed just
    as strictly — otherwise the fix would only protect agent-associated runs.
    """
    runtime = _runtime(tmp_path, monkeypatch)
    session, auth = _session(
        runtime, delegation_id=None, delegation_epoch=None
    )

    def withdraw_read():
        _rewrite_payload(
            stores["db"], auth["authorization_id"],
            lambda r: r.__setitem__("operations_allowed", []),
        )

    out = _run(runtime, session, workspace, monkeypatch, on_first=withdraw_read)

    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "no longer permits 'read'" in out["loop_reason"]
