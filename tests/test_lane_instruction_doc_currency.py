"""Lane instruction-doc currency (Prism UI parallel lanes) — fitness test.

Guards the drift repaired in branch ``feat/prism-l1-lane-doc-currency-01``
(evidence: ``docs/control-plane/evidence/prism-l1-lane-doc-currency-01/``):
the four lane instruction documents under
``docs/control-plane/parallel-ui/AGENT-0N-*.md`` carried active-branch/PR
pointers to a **merged** wave (PRs #429/#430/#431/#428), so a successor agent
reading a lane doc would resume a closed thread.

The oracle is the machine-readable snapshot
``docs/control-plane/parallel-ui/lane-state.json``: the doc must agree with it,
and a lane may only be *deferred* while another open PR is repairing that doc.

Every check here reads the **real** snapshot and the **real** documents. Each
carries a negative control that proves the detector reports the shape it claims
to detect -- a guard that is silent on a planted defect is not a guard.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LANE_DIR = REPO / "docs" / "control-plane" / "parallel-ui"
LANE_STATE = LANE_DIR / "lane-state.json"


def _load_guard():
    spec = importlib.util.spec_from_file_location(
        "lane_state", REPO / "scripts" / "lane_state.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


# The guard resolves LANE_DIR/LANE_STATE from its own file location, so a
# hermetic freshness control needs the scratch repo to mirror that layout and
# the guard's module constants to be pointed at it for the duration of the test.
_DOC = "docs/control-plane/parallel-ui/AGENT-01-SHELL.md"
_SNAP = "docs/control-plane/parallel-ui/lane-state.json"


def _scratch_repo(tmp_path):
    """A throwaway git repo carrying the guarded lane-doc layout."""
    import subprocess

    repo = tmp_path / "scratch"
    (repo / "docs/control-plane/parallel-ui").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "config", key, value], cwd=repo, check=True)
    (repo / _DOC).write_text("original\n", encoding="utf-8")
    (repo / _SNAP).write_text("{}\n", encoding="utf-8")
    return repo


def _commit(repo, message):
    import subprocess

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=repo, check=True)
    return _head(repo)


def _head(repo):
    import subprocess

    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()


def _scratch_state(repo, monkeypatch):
    """Rebind the guard's lane paths onto a scratch repo and return a snapshot.

    ``_freshness_findings`` takes ``repo`` as a parameter, but the guarded *path
    list* is derived from the module-level ``LANE_DIR``/``LANE_STATE``, so those
    are rebound to the scratch tree for the duration of the test (monkeypatch
    restores them). Without this the control would compute paths in the real
    repository and pass for the wrong reason.
    """
    monkeypatch.setattr(guard, "REPO", repo)
    monkeypatch.setattr(guard, "LANE_DIR", repo / "docs/control-plane/parallel-ui")
    monkeypatch.setattr(
        guard, "LANE_STATE", repo / "docs/control-plane/parallel-ui/lane-state.json"
    )
    return {
        "schema": "arkadia.lane-state/1.2",
        "base_main": _head(repo),
        "lanes": {
            "1": {"doc": "AGENT-01-SHELL.md", "open_prs": [], "merged_prs": []},
        },
    }


def live_state() -> dict:
    return json.loads(LANE_STATE.read_text(encoding="utf-8"))


# ------------------------------------------------- authoritative PR-state oracle


def test_pr_status_classifies_the_four_states():
    assert guard.pr_status({"state": "open", "merged": False}) == "OPEN"
    assert guard.pr_status({"state": "closed", "merged": True}) == "MERGED"
    assert guard.pr_status({"state": "closed", "merged": False}) == "CLOSED_UNMERGED"


def test_pr_status_is_unknown_rather_than_guessed():
    """A record the oracle cannot classify must not be read as any of the three.

    ``closed`` is returned by GitHub for both merge outcomes, so a record
    missing ``merged`` is genuinely undecidable. Defaulting it to either answer
    would manufacture a verdict from an absent field.
    """
    assert guard.pr_status({"state": "closed"}) == "UNKNOWN"
    assert guard.pr_status({"state": "weird", "merged": True}) == "UNKNOWN"
    assert guard.pr_status({}) == "UNKNOWN"


def test_closed_unmerged_pr_cannot_stay_classified_as_open():
    """The continuity failure: a closed PR must not be treated as an open thread.

    Local git ancestry cannot decide this -- a closed PR that never merged has
    no merge commit to find, and a merged one has a commit but no way to
    distinguish "merged" from "still open" without asking. The oracle asks.
    """
    record = {"state": "closed", "merged": False}
    assert guard.pr_status(record) == "CLOSED_UNMERGED"
    assert guard.pr_status(record) != "OPEN"


def test_declared_pointer_finding_bites_for_every_lane(tmp_path):
    """A dead pointer is reported even when the lane is deferred.

    This is the hole: ``check_lane_docs`` skips a deferred lane, so its pointer
    was judged by nobody. Measured on the live repository, open PR #548 installs
    a closed PR number into AGENT-03 and open PR #555 does the same into
    AGENT-04 -- and both lanes were deferred, so no guard complained.
    """
    state = live_state()
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        "**Active PR:** #430\n", encoding="utf-8"
    )
    records = {430: {"state": "closed", "merged": True}}
    findings = guard._declared_pointer_findings(
        state, records, lane_dir=tmp_path, lanes=["1"]
    )
    assert findings and "MERGED" in findings[0]


def test_declared_pointer_control_is_silent_for_an_open_pr(tmp_path):
    """Negative control: the same detector must not fire on a live pointer."""
    state = live_state()
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        "**Active PR:** #562\n", encoding="utf-8"
    )
    records = {562: {"state": "open", "merged": False}}
    assert guard._declared_pointer_findings(
        state, records, lane_dir=tmp_path, lanes=["1"]
    ) == []


def test_declared_pointer_fails_closed_when_state_is_unavailable(tmp_path):
    """No GitHub access is UNKNOWN, not a pass.

    The guard is run without a token in many environments. Reporting "no dead
    pointers" from a read that never happened is the same defect as reading a
    truncated deployment window as an absence.
    """
    state = live_state()
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        "**Active PR:** #562\n", encoding="utf-8"
    )
    findings = guard._declared_pointer_findings(
        state, {}, failure="HTTP 401", lane_dir=tmp_path, lanes=["1"]
    )
    assert findings and "UNKNOWN, not a pass" in findings[0]


def test_declared_pointer_is_unknown_when_the_pr_is_absent_from_the_response(tmp_path):
    state = live_state()
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        "**Active PR:** #999999\n", encoding="utf-8"
    )
    findings = guard._declared_pointer_findings(
        state, {}, lane_dir=tmp_path, lanes=["1"]
    )
    assert findings and "UNKNOWN, not a pass" in findings[0]


def test_declared_pointer_reports_lanes_outside_the_blocking_scope(tmp_path):
    """Reporting scope is total even when blocking scope is narrow.

    The guard blocks only on the lanes whose docs it owns, but it must still
    *report* the others: a finding nobody prints is the hole being repaired.
    """
    state = live_state()
    (tmp_path / "AGENT-02-NOVANET-OPPORTUNITY.md").write_text(
        "**Active PR:** #430\n", encoding="utf-8"
    )
    records = {430: {"state": "closed", "merged": True}}
    reported = guard._declared_pointer_findings(state, records, lane_dir=tmp_path)
    blocking = guard._declared_pointer_findings(
        state, records, lane_dir=tmp_path, lanes=["1"]
    )
    assert reported, "lane 2's dead pointer must still be reported"
    assert blocking == [], "lane 2 is not owned by this guard, so it must not block"


def test_live_pointer_check_agrees_with_the_committed_docs():
    """The committed lane-1 doc must name a live PR.

    Offline form: the snapshot records lane 1's open PRs, and the doc's declared
    pointer must be among them. This is the local half of the oracle; the live
    half (``--verify-live``) is what proves the snapshot's own claim.
    """
    state = live_state()
    declared = guard.declared_pr(
        (LANE_STATE.parent / state["lanes"]["1"]["doc"]).read_text(encoding="utf-8")
    )
    open_numbers = {p["number"] for p in state["lanes"]["1"]["open_prs"]}
    assert declared in open_numbers, (
        f"AGENT-01 declares #{declared}, which the snapshot does not list as an "
        f"open lane-1 PR ({sorted(open_numbers)})"
    )


# ---------------------------------------------------------------- real corpus


def test_snapshot_exists_and_is_well_formed():
    state = live_state()
    assert state["schema"] == "arkadia.lane-state/1.2"
    assert len(state["base_main"]) == 40, "base_main must be a full 40-char SHA"
    assert sorted(state["lanes"]) == ["1", "2", "3", "4"]
    assert "closed_unmerged" in state, (
        "the snapshot must record PRs that closed without merging, so a refresh "
        "cannot re-list them as open"
    )


def test_every_merged_pr_carries_its_merge_commit():
    # The liveness oracle decides "is this PR merged?" from ``merged_prs``. A
    # bare PR number makes that undecidable, so the guard would silently lose
    # the ability to catch a merged PR left under ``open_prs``. Each entry must
    # therefore be a {number, merge_commit_sha} object with a full-length SHA.
    state = live_state()
    for lane_no, lane in state["lanes"].items():
        for entry in lane["merged_prs"]:
            assert isinstance(entry, dict), (
                f"lane {lane_no}: merged_prs entry {entry!r} is a bare PR number"
            )
            assert len(entry["merge_commit_sha"]) == 40, (
                f"lane {lane_no} merged PR #{entry['number']} merge_commit_sha "
                f"is not full length"
            )


def test_every_recorded_head_sha_is_full_length():
    # This repo has a recorded defect class: an abbreviated SHA makes an API
    # query silently return "no results". A snapshot is only re-verifiable if
    # its SHAs are full.
    state = live_state()
    for lane_no, lane in state["lanes"].items():
        for pr in lane["open_prs"]:
            assert len(pr["head_sha"]) == 40, (
                f"lane {lane_no} PR #{pr['number']} head_sha is not full length"
            )


def test_live_guarded_docs_agree_with_the_snapshot():
    state = live_state()
    findings = guard._disposition_findings(state)
    findings += guard.check_lane_docs(state, lanes=guard.current_lanes(state))
    assert findings == [], findings


def test_lane_one_shell_doc_is_guarded_current():
    # Lane 1 owns the shell instruction (SHARED-CONTRACTS.md row 1). Its doc is
    # the one this workstream repairs, so it must not be deferred away.
    state = live_state()
    assert state["lanes"]["1"]["doc_guard"] == "current"


def test_lane_one_shell_doc_does_not_name_a_merged_pr():
    state = live_state()
    lane = state["lanes"]["1"]
    text = (LANE_DIR / lane["doc"]).read_text(encoding="utf-8")
    declared = guard.declared_pr(text)
    assert declared in guard._pr_index(state), (
        f"AGENT-01-SHELL.md declares PR #{declared}, not an open lane PR"
    )
    assert declared not in guard.merged_pr_numbers(state), (
        f"AGENT-01-SHELL.md declares merged PR #{declared}"
    )


def test_idle_lane_has_no_open_pr_and_is_not_guarded_as_active_work():
    state = live_state()
    for lane_no, lane in state["lanes"].items():
        if lane["doc_guard"] == "idle":
            assert lane["open_prs"] == [], f"lane {lane_no}: idle lane has open PRs"
            assert lane_no not in guard.current_lanes(state)


def test_every_deferral_is_owned_by_an_open_pr():
    state = live_state()
    open_prs = guard._pr_index(state)
    for lane_no, lane in state["lanes"].items():
        if lane["doc_guard"] == "deferred":
            owner = lane["deferred_to_pr"]
            assert owner in open_prs, (
                f"lane {lane_no} defers to PR #{owner}, which is not open"
            )


def test_snapshot_freshness_is_asserted_not_merely_printed():
    """A snapshot measured against a superseded main must fail the check.

    The first cut of this guard printed ``base main: X (current: Y)`` and exited
    0 regardless -- a stale snapshot (the thing that makes every currency claim
    unsound) could not redden it. Fed a base_main that is not current main, the
    check must now report drift.
    """
    state = live_state()
    findings = guard._freshness_findings(state, "0" * 40)
    assert findings, "stale snapshot base_main was not reported"
    assert "re-measure" in findings[0]


def test_freshness_fails_closed_when_main_is_unresolvable():
    """An unprovable freshness is not a pass.

    The pre-repair guard returned no finding here and the caller printed
    "unknown". That is the wrong direction for this check: a clone that cannot
    resolve ``main`` also cannot prove the snapshot is current, and reporting
    "no drift" from an unproved state is exactly how a superseded snapshot
    survives. The contract is now fail-closed -- a finding, and the caller still
    prints that the current revision is unknown rather than inventing one.
    """
    state = live_state()
    findings = guard._freshness_findings(state, None)
    assert findings, "unresolvable main must fail closed, not abstain"
    assert "UNKNOWN, not a pass" in findings[0]
    assert "unknown" in guard.freshness_text(state, None)


def test_live_snapshot_is_fresh_against_current_main():
    """End-to-end: the committed snapshot must not read as stale.

    This is the property the freshness rule exists to protect, asserted on the
    real corpus rather than a fixture. It holds both before this work is
    committed (the doc edits are not yet in history) and after (the doc edit and
    the snapshot update land in the same commit, which the rule treats as a
    re-measurement) -- so it does not depend on when it runs.
    """
    state = live_state()
    main = guard.resolve_main()
    assert main is not None, "this environment must resolve main"
    assert guard._freshness_findings(state, main) == []


def test_freshness_reports_staleness_when_a_guarded_doc_moved(tmp_path, monkeypatch):
    """The property the freshness rule exists for must still bite.

    The negative control for the check above, built hermetically because the
    reference point is *derived* from git history: on the real repository the
    newest snapshot commit is treated as a re-measurement, so a doc change that
    predates it is correctly not stale and cannot be used to exercise this
    branch. A throwaway repo lets the exact shape be constructed -- a guarded
    lane doc edited with no snapshot refresh -- and the same code path is
    exercised, since ``_freshness_findings`` takes ``repo`` as a parameter.
    """
    repo = _scratch_repo(tmp_path)
    _commit(repo, "base")
    state = _scratch_state(repo, monkeypatch)  # base_main = the base commit
    (repo / _DOC).write_text("changed\n", encoding="utf-8")
    _commit(repo, "doc edit with no snapshot refresh")

    findings = guard._freshness_findings(state, _head(repo), repo=repo)
    assert findings, "a guarded doc changed after the snapshot was recorded"
    assert "stale" in findings[0]


def test_freshness_accepts_a_snapshot_that_records_its_own_doc_change(tmp_path, monkeypatch):
    """A refresh must not invalidate itself.

    The complementary control: when the doc edit and a *real* snapshot update
    land in the same commit -- which is what a refresh does -- the snapshot is
    fresh. Without this, every refresh would immediately re-redden the gate and
    the only way to pass would be to never refresh. Also covers the squash/merge
    ambiguity: the commit is the reference, so its own topology is irrelevant.

    The snapshot is written with *different* content on purpose. A refresh that
    leaves the snapshot byte-identical is not a refresh -- git records no change
    to it, so it cannot serve as the reference point -- and the test must not
    accidentally rely on that being treated as one.
    """
    repo = _scratch_repo(tmp_path)
    _commit(repo, "base")
    state = _scratch_state(repo, monkeypatch)
    (repo / _DOC).write_text("changed\n", encoding="utf-8")
    (repo / _SNAP).write_text('{"refreshed": true}\n', encoding="utf-8")
    _commit(repo, "refresh: doc + snapshot together")

    assert guard._freshness_findings(state, _head(repo), repo=repo) == []


def test_freshness_ignores_a_commit_that_touches_no_guarded_doc(tmp_path, monkeypatch):
    """Unrelated repository movement is not staleness."""
    repo = _scratch_repo(tmp_path)
    state = _scratch_state(repo, monkeypatch)
    _commit(repo, "base")
    (repo / "unrelated.txt").write_text("x\n", encoding="utf-8")
    _commit(repo, "unrelated change")

    assert guard._freshness_findings(state, _head(repo), repo=repo) == []


def test_freshness_fails_closed_when_the_base_is_not_an_ancestor(tmp_path, monkeypatch):
    """A rewritten main voids the recorded provenance, so freshness is UNKNOWN.

    Reported rather than passed: a window that cannot be established is not
    evidence that nothing changed, and reading it as a pass would let a
    superseded snapshot through on exactly the repositories where history was
    rewritten.
    """
    repo = _scratch_repo(tmp_path)
    state = _scratch_state(repo, monkeypatch)
    _commit(repo, "base")
    state["base_main"] = "b" * 40  # well-formed, but absent from this clone

    findings = guard._freshness_findings(state, _head(repo), repo=repo)
    assert findings and "UNKNOWN, not a pass" in findings[0]


def test_detector_flags_a_merged_pr_left_recorded_as_open():
    """Feed the liveness oracle the stale-snapshot shape and require a finding.

    Uses a real merge commit from the snapshot, so the control exercises the
    same git ancestry path the live check uses -- not a mock of it.
    """
    state = copy.deepcopy(live_state())
    merged_entry = state["lanes"]["1"]["merged_prs"][0]
    state["lanes"]["1"]["open_prs"].append(
        {
            "number": merged_entry["number"],
            "branch": "feat/prism-next2-01-shell-contract-map",
            "head_sha": "0" * 40,
        }
    )
    findings = guard._liveness_findings(state)
    assert any("already an ancestor of HEAD" in f for f in findings), findings


def test_liveness_reports_undecidable_when_the_clone_lacks_the_commit():
    # A shallow clone cannot see the merge commit. Scoring that as "not merged"
    # is a silent pass in the dangerous direction, so it must be reported as
    # UNKNOWN instead. Proven with a well-formed but absent object name.
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["open_prs"].append(
        {"number": 429, "branch": "x", "head_sha": "0" * 40}
    )
    for entry in state["lanes"]["1"]["merged_prs"]:
        if entry["number"] == 429:
            entry["merge_commit_sha"] = "a" * 40
    findings = guard._liveness_findings(state)
    assert any("UNKNOWN, not a pass" in f for f in findings), findings


def test_merge_commit_check_flags_a_bare_pr_number():
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["merged_prs"] = [429]
    findings = guard._merge_commit_findings(state)
    assert any("bare PR number" in f for f in findings), findings


def test_merge_commit_check_flags_a_missing_sha():
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["merged_prs"][0]["merge_commit_sha"] = ""
    findings = guard._merge_commit_findings(state)
    assert any("liveness cannot be decided" in f for f in findings), findings


def test_merged_pr_numbers_is_not_vacuous_against_dict_entries():
    # The pre-repair test asserted ``declared not in lane["merged_prs"]``. With
    # dict entries that compares an int against dicts and is *always* true --
    # a silently vacuous guard. The helper must extract numbers.
    state = live_state()
    numbers = guard.merged_pr_numbers(state)
    assert numbers, "merged_pr_numbers returned nothing"
    assert all(isinstance(n, int) for n in numbers)
    assert numbers == guard.merged_pr_commits(state).keys()


# ------------------------------------------------------------ negative controls


def test_detector_flags_a_doc_pointing_at_a_merged_pr(tmp_path):
    """Feed the detector the exact pre-repair shape and require it to report it."""
    state = live_state()
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        "**Active branch:** `feat/prism-next2-01-shell-contract-map`\n"
        "**Active PR:** [#429](https://example/429)\n",
        encoding="utf-8",
    )
    findings = guard.check_lane_docs(state, lane_dir=tmp_path, lanes=["1"])
    assert findings, "detector was silent on a doc naming a merged PR"
    assert any("#429" in f for f in findings)


def test_detector_flags_a_branch_that_does_not_match_its_pr(tmp_path):
    state = live_state()
    live = guard._pr_index(state)
    open_number = sorted(live)[0]
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        f"**Active branch:** `feat/wrong-branch`\n**Active PR:** #{open_number}\n",
        encoding="utf-8",
    )
    findings = guard.check_lane_docs(state, lane_dir=tmp_path, lanes=["1"])
    assert any("heads" in f for f in findings), findings


def test_disposition_check_flags_a_deferral_to_a_closed_pr():
    state = copy.deepcopy(live_state())
    state["lanes"]["2"]["doc_guard"] = "deferred"
    state["lanes"]["2"]["deferred_to_pr"] = 99999999  # not in the snapshot
    findings = guard._disposition_findings(state)
    assert any("#99999999" in f for f in findings), findings


def test_disposition_check_flags_an_unknown_disposition():
    state = copy.deepcopy(live_state())
    state["lanes"]["1"]["doc_guard"] = "ignored"
    findings = guard._disposition_findings(state)
    assert any("must be 'current', 'deferred', or 'idle'" in f for f in findings), findings


@pytest.mark.parametrize("lane_no", ["1", "2", "3", "4"])
def test_last_declaration_wins_over_the_wave_header(lane_no):
    """A dated status block must supersede the earlier wave header.

    Lanes update by *appending* a status block; a first-wins scanner would
    read the stale wave header forever. This pins the last-wins convention.
    """
    text = (
        "**Active branch:** `feat/old-wave`\n"
        "**Active PR:** #429\n"
        "... later ...\n"
        "**Active branch:** `feat/new-wave`\n"
        "**Active PR:** #507\n"
    )
    assert guard.declared_branch(text) == "feat/new-wave"
    assert guard.declared_pr(text) == 507


# ------------------------------------------------------------------- wiring


def test_a_workflow_executes_the_lane_doc_guard():
    """The guard must have a continuous execution surface, and its trigger
    filter must name every input the guard reads.

    The guard reads the lane docs + snapshot, the policy script, and this test
    file. A filter that omits any of them lets a change to that input land
    without executing the guard -- the "guard no workflow runs is decoration"
    class recorded elsewhere in this repo.
    """
    workflow = (REPO / ".github/workflows/lane-doc-currency.yml").read_text(
        encoding="utf-8"
    )
    for needed in (
        "docs/control-plane/parallel-ui/**",
        "scripts/lane_state.py",
        "tests/test_lane_instruction_doc_currency.py",
        ".github/workflows/lane-doc-currency.yml",
    ):
        assert needed in workflow, f"lane-doc-currency.yml filter omits {needed}"
    # It must actually invoke pytest on the guard, not merely mention it.
    assert "pytest -q tests/test_lane_instruction_doc_currency.py" in workflow
    # The liveness oracle reads git ancestry, so the checkout must carry full
    # history. A depth-1 checkout makes the oracle undecidable (or, read
    # naively, silently permissive) -- pin the requirement to the workflow.
    assert "fetch-depth: 0" in workflow, (
        "lane-doc-currency.yml must check out full history (fetch-depth: 0) for "
        "the merge-ancestry liveness oracle"
    )
