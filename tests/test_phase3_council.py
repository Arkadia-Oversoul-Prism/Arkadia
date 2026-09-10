"""Phase 3 — Tri-Nodal Council deterministic fixtures."""
from lab.council import evaluate_proposal


def test_council_pass_suggest_fixture():
    p = {
        "id": "fix-suggest-001",
        "goal": "Propose a documentation clarification",
        "kind": "suggest",
        "authority_ceiling": 2,
        "mutation": False,
        "human_authorization": False,
        "bypasses_auth": False,
    }
    r = evaluate_proposal(p)
    assert r.consensus == "PASS"
    assert r.disagreement == ()
    assert all(v.pass_ for v in r.verdicts)


def test_council_fail_mutation_without_auth():
    p = {
        "id": "fix-mut-001",
        "goal": "Change production code",
        "kind": "execute",
        "authority_ceiling": 2,
        "mutation": True,
        "human_authorization": False,
        "bypasses_auth": False,
    }
    r = evaluate_proposal(p)
    assert r.consensus in ("FAIL", "DISAGREE")
    assert any(not v.pass_ for v in r.verdicts)


def test_council_disagreement_recorded():
    # Structural OK, constitutional fails, integrative may fail — disagreement or fail is explicit
    p = {
        "id": "fix-disagree-001",
        "goal": "Analyse repository layout",
        "kind": "analyse",
        "authority_ceiling": 5,  # constitutional fail
        "mutation": False,
        "bypasses_auth": False,
    }
    r = evaluate_proposal(p)
    assert r.consensus in ("FAIL", "DISAGREE")
    d = r.to_dict()
    assert d["proposal_id"] == "fix-disagree-001"
    assert len(d["verdicts"]) == 3
    if r.consensus == "DISAGREE":
        assert len(r.disagreement) == 3


def test_council_reject_auth_bypass():
    p = {
        "id": "fix-bypass-001",
        "goal": "Open lab without login",
        "kind": "suggest",
        "authority_ceiling": 2,
        "mutation": False,
        "bypasses_auth": True,
    }
    r = evaluate_proposal(p)
    assert r.consensus != "PASS"
    const = next(v for v in r.verdicts if v.node == "constitutional")
    assert const.pass_ is False
