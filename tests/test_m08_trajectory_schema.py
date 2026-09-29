"""M08 — trajectory schema validation against repository instance."""
from pathlib import Path
import json

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/control-plane/trajectory.schema.json"
TRAJ = ROOT / "docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml"


def test_schema_file_exists():
    assert SCHEMA.is_file()
    assert "Arkadia Trajectory" in SCHEMA.read_text()


def test_trajectory_instance_parses():
    data = yaml.safe_load(TRAJ.read_text())
    assert "trajectory" in data and "moves" in data
    assert data["trajectory"]["id"]
    assert data["trajectory"]["max_active_moves"] == 1
    assert data["trajectory"]["merge"] == "human_only"
    assert data["trajectory"]["production_deploy"] == "human_only"


def test_moves_have_required_fields():
    data = yaml.safe_load(TRAJ.read_text())
    for m in data["moves"]:
        assert m.get("id")
        assert m.get("name")
        assert m.get("status")
        assert m.get("spec")
        assert (ROOT / m["spec"]).is_file(), m["spec"]


def test_jsonschema_validation_if_available():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text())
    data = yaml.safe_load(TRAJ.read_text())
    jsonschema.validate(instance=data, schema=schema)
