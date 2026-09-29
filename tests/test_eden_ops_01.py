"""EDEN-OPS-01 — living-cell and binding contract tests."""
from __future__ import annotations

from solspire.eden_ops import EDEN_DESKS, EdenOps
from weaver.enterprise_orchestration import EnterpriseOrchestrationStore


def _ops(tmp_path, monkeypatch):
    import solspire.eden_ops as eden_mod
    import weaver.enterprise_orchestration as ew_mod

    db = str(tmp_path / "eden_ops.db")
    monkeypatch.setattr(eden_mod, "_DB_PATH", db)
    monkeypatch.setattr(ew_mod, "_DB_PATH", db)
    store = EnterpriseOrchestrationStore()
    return EdenOps(store=store)


def test_bind_two_humans_to_all_desks(tmp_path, monkeypatch):
    ops = _ops(tmp_path, monkeypatch)
    bindings = ops.bind_default_two_humans(enterprise_id="eden-01")
    assert len(bindings) == len(EDEN_DESKS) * 2
    listed = ops.list_bindings(enterprise_id="eden-01")
    assert len(listed) == len(EDEN_DESKS) * 2
    desks = {b.desk for b in listed}
    assert desks == set(EDEN_DESKS)
    humans = {b.human_name for b in listed}
    assert humans == {"Divine Favour Yusuf", "Jessica"}


def test_unknown_desk_rejected(tmp_path, monkeypatch):
    ops = _ops(tmp_path, monkeypatch)
    try:
        ops.bind_desk(
            enterprise_id="eden-01",
            subject="architect",
            human_name="Divine Favour Yusuf",
            desk="Fiction Department",
        )
    except ValueError as exc:
        assert "unknown desk" in str(exc)
    else:
        raise AssertionError("unknown desk must be rejected")


def test_living_cell_preserves_unknown_until_evidence(tmp_path, monkeypatch):
    ops = _ops(tmp_path, monkeypatch)
    result = ops.living_cell_supplier_path(
        subject="architect",
        enterprise_id="eden-01",
        verified_price_ngn_per_kg=1200,
    )

    # Interpretation left price UNKNOWN
    assert result["interpretation"].interpretation["price"] == "UNKNOWN"

    # Proposal required because price was unknown
    assert result["proposal"] is not None
    assert result["authorization"] is not None

    # Evidence introduced the price
    assert result["evidence"].content_or_ref["price_ngn_per_kg"] == 1200
    assert result["verification"].verdict == "VERIFIED"

    # Field: only evidence-backed commercial fields updated
    field = result["field"]
    assert field.commercial["buy_price"] == "₦1200/kg"
    assert field.commercial["supplier"] == "A"
    assert field.commercial["commodity"] == "potatoes"
    # Unsupported commercial facts stay UNKNOWN
    assert field.commercial["buyer"] == "UNKNOWN"
    assert field.commercial["sell_price"] == "UNKNOWN"
    assert field.commercial["route"] == "UNKNOWN"
    # Capital: budget is context; committed/spent/recovered stay UNKNOWN
    assert field.capital["committed"] == "UNKNOWN"
    assert field.capital["spent"] == "UNKNOWN"
    assert field.capital["recovered"] == "UNKNOWN"

    # Reverse-walk complete
    assert result["reverse_walk"]["complete"] is True


def test_reject_proposal_does_not_authorize(tmp_path, monkeypatch):
    ops = _ops(tmp_path, monkeypatch)
    ingest = ops.ingest_supplier_signal(
        subject="jessica",
        enterprise_id="eden-01",
        message="Supplier B available; price unknown",
        price="UNKNOWN",
    )
    decision = ops.decide_proposal(
        subject="jessica",
        proposal_id=ingest["proposal"].id,
        action="REJECT",
        actor="jessica",
    )
    assert decision["status"] == "REJECTED"
    assert decision["authorization"] is None


def test_execution_requires_authorization(tmp_path, monkeypatch):
    ops = _ops(tmp_path, monkeypatch)
    try:
        ops.execute_and_evidence(
            subject="architect",
            authorization_id="missing",
            tool_channel="x",
            request_payload={},
            evidence_content={"ok": True},
            claim="should fail",
        )
    except ValueError as exc:
        assert "authorization" in str(exc).lower()
    else:
        raise AssertionError("execution without authorization must fail")


def test_today_summary_surfaces_bindings_and_unknowns(tmp_path, monkeypatch):
    ops = _ops(tmp_path, monkeypatch)
    ops.bind_default_two_humans(enterprise_id="eden-01")
    summary = ops.today_summary(subject="architect", enterprise_id="eden-01")
    assert len(summary["bindings"]) == len(EDEN_DESKS) * 2
    assert summary["unknowns"] >= 1
    assert "critical_objectives" in summary
