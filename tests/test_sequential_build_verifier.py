import copy

from scripts.verify_sequential_build import verify_envelope


def envelope():
    return {
        "protocol": "ARKADIA-SEQUENTIAL-BUILD",
        "protocol_version": "1.0",
        "build_id": "PRISM-01",
        "parent_build": None,
        "base_commit": "dc6d1563cd53e15f1c3ceb80b434fd37b62f3f11",
        "objective": "bounded conformance build",
        "scope": {
            "kind": "repository",
            "scope_ref": "Arkadia-Oversoul-Prism/Arkadia",
            "repository_ref": "Arkadia-Oversoul-Prism/Arkadia",
            "project_ref": None,
        },
        "transition": {
            "input_state_root": "a" * 64,
            "output_state_root": "b" * 64,
            "delta_ref": "evidence/build-01/delta.json",
            "changed_paths": ["research/oversoul_prism_144/substrate.py"],
            "external_side_effects": False,
        },
        "invariants": ["root-continuity", "authority-boundary"],
        "proof": [
            {
                "invariant": "root-continuity",
                "result": "PASS",
                "evidence_refs": ["E-ROOT-001"],
                "observation": "Delta base root equals the declared input root.",
            },
            {
                "invariant": "authority-boundary",
                "result": "PASS",
                "evidence_refs": ["E-AUTH-001"],
                "observation": "No governing authority was created by the build.",
            },
        ],
        "status": "VERIFIED",
        "failures": [],
        "unknowns": [],
    }


def test_verified_envelope_can_proceed():
    result = verify_envelope(envelope())
    assert result["valid"] is True
    assert result["can_proceed"] is True
    assert result["status"] == "VERIFIED"
    assert result["next_input_root"] == "b" * 64
    assert result["certificate_root"]


def test_unknown_gate_blocks_progression():
    data = envelope()
    data["proof"][1]["result"] = "UNKNOWN"
    result = verify_envelope(data)
    assert result["valid"] is False
    assert result["can_proceed"] is False
    assert "authority-boundary" in result["unknown_gates"]


def test_failure_blocks_progression_even_if_status_claims_verified():
    data = envelope()
    data["failures"] = ["F2 PROVENANCE FAILURE"]
    result = verify_envelope(data)
    assert result["can_proceed"] is False
    assert "F2 PROVENANCE FAILURE" in result["failed_gates"]


def test_authority_injection_is_rejected():
    data = envelope()
    data["metadata"] = {"authorization_id": "forged"}
    result = verify_envelope(data)
    assert result["can_proceed"] is False
    assert any("authorization_id" in item for item in result["errors"])


def test_child_must_start_at_verified_parent_output():
    parent = envelope()
    child = copy.deepcopy(envelope())
    parent["build_id"] = "PRISM-00"
    child["build_id"] = "PRISM-01"
    child["parent_build"] = "PRISM-00"
    child["transition"]["input_state_root"] = "c" * 64

    result = verify_envelope(child, parent)
    assert result["can_proceed"] is False
    assert any("parent output_state_root" in item for item in result["errors"])


def test_project_scope_cannot_silently_widen():
    parent = envelope()
    parent["build_id"] = "PRISM-00"
    parent["scope"] = {
        "kind": "project",
        "scope_ref": "project-123",
        "repository_ref": "Arkadia-Oversoul-Prism/Arkadia",
        "project_ref": "project-123",
    }
    child = copy.deepcopy(envelope())
    child["build_id"] = "PRISM-01"
    child["parent_build"] = "PRISM-00"
    child["transition"]["input_state_root"] = parent["transition"]["output_state_root"]
    child["scope"]["kind"] = "repository"
    child["scope"]["scope_ref"] = "Arkadia-Oversoul-Prism/Arkadia"
    child["scope"]["project_ref"] = None

    result = verify_envelope(child, parent)
    assert result["can_proceed"] is False
    assert any("silently widen" in item for item in result["errors"])
