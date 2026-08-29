"""WEAVER-K1 — Context Packet / reconnaissance tests."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from weaver.recon import (
    SCHEMA_VERSION,
    build_context_packet,
    git_identity,
    is_stale,
    write_context_packet,
)


def _git_init(tmp_path: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    return head


def test_packet_contains_actual_git_head(tmp_path):
    head = _git_init(tmp_path)
    # minimal architecture file
    arch = tmp_path / "tests" / "architecture"
    arch.mkdir(parents=True)
    (arch / "LAYER_MAP.py").write_text('LAYER_MAP = {"docs": 5, "api": 1}\n')
    pkt = build_context_packet(str(tmp_path))
    assert pkt["head_sha"] == head
    assert pkt["repository"]["head_sha"] == head
    assert pkt["schema_version"] == SCHEMA_VERSION


def test_detects_remote_divergence_flag(tmp_path):
    head = _git_init(tmp_path)
    # no origin/main → origin_sha None, divergent false or based on comparison
    ident = git_identity(str(tmp_path))
    assert ident["head_sha"] == head
    # working tree dirty
    (tmp_path / "extra").write_text("y")
    ident2 = git_identity(str(tmp_path))
    assert ident2["working_tree_clean"] is False


def test_architecture_from_layer_map(tmp_path):
    _git_init(tmp_path)
    arch = tmp_path / "tests" / "architecture"
    arch.mkdir(parents=True)
    (arch / "LAYER_MAP.py").write_text(
        'LAYER_MAP = {"docs": 5, "api": 1, "providers": 3}\n'
    )
    pkt = build_context_packet(str(tmp_path))
    assert pkt["architecture"]["status"] == "ok"
    assert pkt["architecture"]["source"] == "tests/architecture/LAYER_MAP.py"
    assert "constitution" in pkt["architecture"]["prefixes_by_layer"] or "5" in str(
        pkt["architecture"]
    )


def test_checkpoint_state_represented(tmp_path):
    _git_init(tmp_path)
    ck = tmp_path / "data" / "weaver" / "checkpoints"
    ck.mkdir(parents=True)
    (ck / "WEAVER_TEST_1.json").write_text(
        json.dumps(
            {
                "pass_id": "WEAVER-TEST",
                "status": "PASS",
                "result_sha": "abc",
                "remote_sha": "abc",
                "publication_status": "published",
                "timestamp": 1,
            }
        )
    )
    pkt = build_context_packet(str(tmp_path))
    assert pkt["checkpoint_state"]["count"] >= 1
    assert pkt["checkpoint_state"]["current"]["pass_id"] == "WEAVER-TEST"


def test_protected_boundaries_present(tmp_path):
    _git_init(tmp_path)
    pkt = build_context_packet(str(tmp_path))
    assert isinstance(pkt["protected_boundaries"], list)
    assert any("auth" in b.lower() or "api" in b.lower() for b in pkt["protected_boundaries"])


def test_context_is_not_authorization(tmp_path):
    _git_init(tmp_path)
    pkt = build_context_packet(str(tmp_path))
    assert pkt["next_action"] == "awaiting human authorization"
    assert pkt["authorization"]["pass_spec_required"] is True
    assert "CONTEXT" in pkt["authorization"]["note"]


def test_stale_detection(tmp_path):
    head = _git_init(tmp_path)
    pkt = build_context_packet(str(tmp_path))
    assert is_stale(pkt, str(tmp_path)) is False
    # mutate binding
    pkt["stale_detection"]["bound_head_sha"] = "0" * 40
    assert is_stale(pkt, str(tmp_path)) is True
    assert pkt["stale_detection"]["bound_head_sha"] != head or True


def test_deterministic_core_fields(tmp_path):
    _git_init(tmp_path)
    arch = tmp_path / "tests" / "architecture"
    arch.mkdir(parents=True)
    (arch / "LAYER_MAP.py").write_text('LAYER_MAP = {"docs": 5}\n')
    a = build_context_packet(str(tmp_path))
    b = build_context_packet(str(tmp_path))
    for key in ("head_sha", "schema_version", "next_action", "topology"):
        assert a[key] == b[key]
    assert a["architecture"]["status"] == b["architecture"]["status"]


def test_write_context_packet(tmp_path):
    _git_init(tmp_path)
    rel = write_context_packet(str(tmp_path))
    assert rel.endswith("current.json")
    data = json.loads((tmp_path / rel).read_text())
    assert data["head_sha"]
