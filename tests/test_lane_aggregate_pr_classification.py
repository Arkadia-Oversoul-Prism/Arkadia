"""Aggregate-PR classification repair — regression tests.

The defect this repairs, measured on live data 2026-11-18 at integration head
``0fdf4ca8``: PR #668 (the EWOR evidence baseline) composes #663-#667, so its
diff touches paths owned by all four lanes. The classifier assigned it to every
lane by path ownership, and because it carried the newest ``updated_at`` it was
then selected as ``active_pr`` in all four -- superseding the genuine lane PRs
#665/#666/#667/#664. An aggregate evidence PR is not the working owner of the
lanes it composes.

The repair is an explicit, version-controlled declaration
(``docs/control-plane/parallel-ui/aggregate-prs.json``) that the classifier
reads. It is deliberately *not* a title substring or a branch prefix: either
would classify a genuine multi-lane implementation PR as aggregate and silently
strip it from lane ownership.

Every test here runs the real classifier against the real config. The PR records
come from ``tests/fixtures/lane_aggregate_pr_records.json``, captured from live
GitHub (see its ``_provenance``), so the record shape is the API's, not a
convenient invention.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LANE_DIR = REPO / "docs" / "control-plane" / "parallel-ui"
FIXTURE = REPO / "tests" / "fixtures" / "lane_aggregate_pr_records.json"
CONFIG = LANE_DIR / "aggregate-prs.json"


def _load_refresh():
    spec = importlib.util.spec_from_file_location(
        "lane_state_refresh", REPO / "scripts" / "lane_state_refresh.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


refresh = _load_refresh()


def _records() -> dict[str, dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["records"]


def _open_prs() -> list[dict]:
    return [dict(r) for r in _records().values()]


# Changed-path sets, taken from the real PRs' diffs. Each lane PR touches only
# its own lane's owned paths; #668 touches all four because it composes them.
LANE_PATHS = {
    664: ["web/arkadia_console/src/components/lab/renderClip.ts"],
    665: ["tests/test_console_document_title_contract.py"],
    666: ["web/arkadia_console/src/components/opportunities/opportunityRadarContract.ts"],
    667: ["web/arkadia_console/src/pages/knowledge/KnowledgeContracts.ts"],
}
AGGREGATE_PATHS = sorted({p for paths in LANE_PATHS.values() for p in paths})


def _files() -> dict[int, list[str]]:
    files = {n: list(p) for n, p in LANE_PATHS.items()}
    files[668] = list(AGGREGATE_PATHS)
    return files


def _build(aggregate=None):
    return refresh.build(
        _open_prs(),
        _files(),
        "f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a",
        "Arkadia-Oversoul-Prism/Arkadia",
        aggregate=aggregate if aggregate is not None else refresh.load_aggregate_config(),
    )


# ------------------------------------------------------- A. aggregate exclusion


def test_aggregate_pr_is_not_an_active_or_ordinary_lane_pr_in_any_lane():
    """A. #668 must not appear as active or ordinary owner in any of the four."""
    state = _build()
    for lane_no, lane in state["lanes"].items():
        numbers = [p["number"] for p in lane["open_prs"]]
        assert 668 not in numbers, (
            f"lane {lane_no} lists aggregate PR #668 as an ordinary lane PR: {numbers}"
        )
        assert lane["active_pr"] != 668, (
            f"lane {lane_no} selected aggregate PR #668 as its active thread"
        )


def test_aggregate_pr_does_not_supersede_the_genuine_lane_pr():
    """F. The newer aggregate PR must not win active-thread selection."""
    state = _build()
    expected = {"1": 665, "2": 666, "3": 667, "4": 664}
    for lane_no, want in expected.items():
        assert state["lanes"][lane_no]["active_pr"] == want, (
            f"lane {lane_no} active_pr is {state['lanes'][lane_no]['active_pr']}, "
            f"expected the genuine lane PR #{want}"
        )


# ------------------------------------------------- B. aggregate evidence retained


def test_aggregate_pr_remains_discoverable_in_an_auditable_collection():
    """B. Exclusion must not mean deletion: #668 stays visible and explained."""
    state = _build()
    aggregate = {p["number"]: p for p in state["aggregate_prs"]}
    assert 668 in aggregate, "aggregate PR #668 vanished from the evidence record"
    entry = aggregate[668]
    assert entry["classification"] == "aggregate"
    assert entry["lanes_touched"] == ["1", "2", "3", "4"], (
        "the record must still show which lanes the aggregate diff spans"
    )
    assert entry["reason"], "an aggregate entry must carry its stated reason"
    assert entry["head_sha"] and entry["branch"]


def test_aggregate_config_status_is_recorded_in_the_snapshot():
    state = _build()
    assert state["aggregate_config"]["status"] == "present"
    assert 668 in state["aggregate_config"]["declared"]


# ------------------------------------------------------- C. genuine multi-lane


def test_genuine_multi_lane_pr_is_still_classified_into_every_lane_it_touches():
    """C. The repair must not blind the classifier to real multi-lane work."""
    prs = _open_prs()
    files = _files()
    # A non-aggregate PR touching lane 1 and lane 3 owned paths.
    prs.append(
        {
            "number": 900001,
            "state": "open",
            "draft": True,
            "title": "feat: genuine cross-lane implementation",
            "merged": False,
            "updated_at": "2026-11-18T23:59:59Z",
            "labels": [],
            "head": {"ref": "feat/genuine-multi-lane", "sha": "a" * 40},
            "base": {"ref": "main", "sha": "f" * 40},
        }
    )
    files[900001] = [
        "tests/test_console_document_title_contract.py",  # lane 1
        "web/arkadia_console/src/pages/knowledge/KnowledgeContracts.ts",  # lane 3
    ]
    state = refresh.build(
        prs, files, "f" * 40, "x/y", aggregate=refresh.load_aggregate_config()
    )
    assert 900001 in [p["number"] for p in state["lanes"]["1"]["open_prs"]]
    assert 900001 in [p["number"] for p in state["lanes"]["3"]["open_prs"]]
    assert 900001 not in [p["number"] for p in state["lanes"]["2"]["open_prs"]]
    assert 900001 not in [p["number"] for p in state["lanes"]["4"]["open_prs"]]
    assert 900001 not in [p["number"] for p in state["aggregate_prs"]]


# ------------------------------------------------------------ D. single-lane


def test_single_lane_pr_keeps_its_existing_classification():
    """D. Ordinary single-lane ownership is unchanged by the repair."""
    state = _build()
    assert [p["number"] for p in state["lanes"]["1"]["open_prs"]] == [665]
    assert [p["number"] for p in state["lanes"]["2"]["open_prs"]] == [666]
    assert [p["number"] for p in state["lanes"]["3"]["open_prs"]] == [667]
    assert [p["number"] for p in state["lanes"]["4"]["open_prs"]] == [664]


# --------------------------------------------------------- E. metadata failure


def test_missing_config_is_reported_not_silently_treated_as_ordinary(tmp_path):
    """E. Absent metadata is a *reported* state, and no PR is assumed aggregate."""
    missing = tmp_path / "does-not-exist.json"
    cfg = refresh.load_aggregate_config(missing)
    assert cfg["status"] == "absent"
    assert cfg["numbers"] == set()
    state = _build(aggregate=cfg)
    assert state["aggregate_config"]["status"] == "absent"
    # With no declaration, #668 is classified by path ownership -- which is the
    # pre-repair behaviour, and the snapshot says so rather than pretending.
    assert 668 in [p["number"] for p in state["lanes"]["1"]["open_prs"]]


def test_malformed_config_aborts_rather_than_falling_back(tmp_path):
    """E. Unreadable metadata must fail closed, never degrade to 'none aggregate'."""
    bad = tmp_path / "aggregate-prs.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(refresh.AggregateConfigError):
        refresh.load_aggregate_config(bad)


def test_config_without_the_required_list_aborts(tmp_path):
    bad = tmp_path / "aggregate-prs.json"
    bad.write_text(json.dumps({"aggregate_prs": "668"}), encoding="utf-8")
    with pytest.raises(refresh.AggregateConfigError):
        refresh.load_aggregate_config(bad)


def test_config_entry_without_an_integer_number_aborts(tmp_path):
    bad = tmp_path / "aggregate-prs.json"
    bad.write_text(json.dumps({"aggregate_prs": [{"number": "668"}]}), encoding="utf-8")
    with pytest.raises(refresh.AggregateConfigError):
        refresh.load_aggregate_config(bad)


def test_refresh_main_exits_2_when_config_is_malformed(tmp_path, monkeypatch):
    """E. The CLI must refuse to write a snapshot it cannot classify safely."""
    bad = tmp_path / "aggregate-prs.json"
    bad.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(refresh, "AGGREGATE_CONFIG", bad)
    monkeypatch.setenv("GH_TOKEN", "dummy-not-used")
    # base_main is supplied so the function reaches the config load without git.
    rc = refresh.main(["--base-main", "f" * 40])
    assert rc == 2


# ------------------------------------------------- G. live record-shape compat


def test_classifier_works_on_the_real_github_record_shape():
    """G. The fixture is a real API record, not a synthetic convenience shape."""
    records = _records()
    assert set(records) == {"664", "665", "666", "667", "668"}
    for number, rec in records.items():
        # Fields the classifier actually reads, present in the real payload.
        assert isinstance(rec["number"], int)
        assert rec["state"] == "open"
        assert isinstance(rec["draft"], bool)
        assert isinstance(rec["title"], str)
        assert rec["head"]["ref"] and rec["head"]["sha"]
        assert rec["updated_at"]
        assert isinstance(rec["labels"], list)
    # The aggregate PR really is the newest, which is why it used to win.
    newest = max(records.values(), key=lambda r: r["updated_at"])
    assert newest["number"] == 668


def test_fixture_declares_its_provenance():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert "api.github.com" in payload["_provenance"]
    assert "not invented" in payload["_provenance"]


# ------------------------------------------------------- config sanity (live)


def test_live_config_declares_668_and_is_well_formed():
    cfg = refresh.load_aggregate_config()
    assert cfg["status"] == "present"
    assert 668 in cfg["numbers"]
    entry = next(e for e in cfg["entries"] if e["number"] == 668)
    assert entry["reason"]
    assert entry["composes"] == [663, 664, 665, 666, 667]


def test_live_snapshot_records_the_aggregate_classification():
    """The committed snapshot must carry the classification, not just the code."""
    state = json.loads((LANE_DIR / "lane-state.json").read_text(encoding="utf-8"))
    assert "aggregate_prs" in state, "snapshot predates the classification repair"
    assert "aggregate_config" in state
    numbers = [p["number"] for p in state["aggregate_prs"]]
    assert 668 in numbers, "the committed snapshot does not record #668 as aggregate"
    for lane_no, lane in state["lanes"].items():
        assert 668 not in [p["number"] for p in lane["open_prs"]], (
            f"committed snapshot still lists #668 as an ordinary lane {lane_no} PR"
        )
        assert lane["active_pr"] != 668
