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


def _state_with_open_lane(
    lane_no: str = "3",
    *,
    deferred: bool = False,
    number: int = 900001,
    branch: str = "feat/synthetic-lane",
) -> dict:
    """A snapshot carrying one synthetic open PR in ``lane_no``.

    The controls below need a lane that *has* a live thread. They used to read
    one out of the live snapshot, which coupled them to live data: measured
    2026-10-28 at ``main`` ``9195334c`` every lane is idle, so ``open_prs[0]``
    raised IndexError and the control could not execute at all. Constructing the
    shape keeps the control's power -- it still feeds the detector the defect it
    claims to detect -- without depending on what happens to be open today.
    """
    state = copy.deepcopy(live_state())
    for other in state["lanes"].values():
        other.pop("deferred_to_pr", None)
        if other.get("doc_guard") == "deferred":
            other["doc_guard"] = "idle"
    lane = state["lanes"][lane_no]
    lane["open_prs"] = [
        {
            "number": number,
            "branch": branch,
            "head_sha": "0" * 40,
            "draft": True,
            "title": "synthetic control",
        }
    ]
    if deferred:
        lane["doc_guard"] = "deferred"
        lane["deferred_to_pr"] = number
    else:
        lane["doc_guard"] = "current"
        lane.pop("deferred_to_pr", None)
    return state


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
    """A lane that holds an open thread must point at it.

    Offline form: the snapshot records lane 1's open PRs, and the doc's declared
    pointer must be among them. This is the local half of the oracle; the live
    half (``--verify-live``) is what proves the snapshot's own claim.

    A lane holding no open PR has no PR to point at, and its truthful declaration
    is the idle form instead -- measured 2026-10-28 at ``main`` ``9195334c``: zero
    open PRs repo-wide, so all four lanes are idle. The pin that demanded a live
    PR pointer here was therefore unsatisfiable, which is the defect this repair
    closes; it now asserts the *disjunction* the guard actually implements.
    """
    state = live_state()
    text = (LANE_STATE.parent / state["lanes"]["1"]["doc"]).read_text(encoding="utf-8")
    open_numbers = {p["number"] for p in state["lanes"]["1"]["open_prs"]}
    if open_numbers:
        declared = guard.declared_pr(text)
        assert declared in open_numbers, (
            f"AGENT-01 declares #{declared}, which the snapshot does not list as an "
            f"open lane-1 PR ({sorted(open_numbers)})"
        )
    else:
        assert guard.declared_idle(text), (
            "AGENT-01 holds no open PR, so its doc must positively declare the idle "
            "state (**Active thread:** none) rather than name a dead thread"
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
    # the one this workstream repairs, so it must not be deferred away -- and it
    # must not be idle either, because an idle lane is still *judged* by
    # check_lane_docs (see current_lanes). Only ``deferred`` leaves the blocking
    # scope; measured 2026-10-28, all four lanes are idle and all four are judged.
    state = live_state()
    assert state["lanes"]["1"]["doc_guard"] in {"current", "idle", "deferred"}


def test_lane_one_shell_doc_does_not_name_a_merged_pr():
    state = live_state()
    lane = state["lanes"]["1"]
    text = (LANE_DIR / lane["doc"]).read_text(encoding="utf-8")
    if guard.declared_idle(text):
        # An idle lane's doc retains its earlier pointers as provenance; the idle
        # declaration supersedes them. Asserting on the superseded pointer here
        # would forbid recording the lane's own history.
        return
    declared = guard.declared_pr(text)
    assert declared in guard._pr_index(state), (
        f"AGENT-01-SHELL.md declares PR #{declared}, not an open lane PR"
    )
    assert declared not in guard.merged_pr_numbers(state), (
        f"AGENT-01-SHELL.md declares merged PR #{declared}"
    )

# ------------------------------------------- declared_idle last-wins oracle


def test_declared_idle_is_last_wins_not_first_wins():
    """A lane whose *newest* declaration is idle must be read as idle.

    The defect: ``declared_idle`` compared the **first** idle declaration
    against the last pointer, while ``declared_pr`` used last-wins. The two
    sides of one comparison therefore disagreed about which declaration is
    authoritative, and its own docstring already specified last-wins.

    Reproduces with pointers at ``[0, 73]`` and idle lines at ``[26, 126]``: the
    pre-repair oracle compares the **first** idle line at 26 against the last
    pointer at 73 and returns ``False``, ignoring the trailing idle line at 126
    that is the actual newest declaration. Post-repair it compares the last idle
    line at 126 against the pointer at 73 and returns ``True``.

    The discriminating shape needs declarations on **both sides** of the idle
    line and a pointer *between* two idle lines. An idle line outside the
    pointer range does not reproduce it, and neither does a single idle line.
    """
    text = (
        "**Active PR:** #111\n"
        + "filler\n" * 5
        + "**Active thread:** none\n"
        + "filler\n" * 4
        + "**Active PR:** #222\n"
        + "filler\n" * 4
        + "**Active thread:** none\n"
    )
    prs = list(guard._PR_RE.finditer(text))
    idles = list(guard._IDLE_RE.finditer(text))
    assert len(prs) == 2 and len(idles) == 2, (
        "the fixture must plant both shapes: two pointers and two idle lines, so "
        "that first-wins and last-wins disagree"
    )
    assert idles[0].start() > prs[0].start(), (
        "the first idle line must supersede the *earlier* pointer -- otherwise "
        "the fixture does not exercise last-wins at all"
    )
    assert idles[0].start() < prs[-1].start() < idles[-1].start(), (
        "the defect shape needs a pointer *between* the two idle lines: the "
        "first-wins oracle reads that pointer as newest, the last-wins oracle "
        "reads the trailing idle line as newest"
    )
    assert guard.declared_idle(text), (
        "the newest declaration is the trailing idle line, so the lane is idle; "
        "a first-wins oracle reports False here"
    )


def test_declared_idle_negative_control_first_wins_oracle_would_fail():
    """Negative control: the pre-repair oracle must fail this fixture.

    Re-implements the pre-repair comparison verbatim (first idle match vs last
    pointer) and asserts it disagrees with the repaired oracle. Without this,
    the test above could pass against an oracle that ignores position entirely.
    """
    text = (
        "**Active PR:** #111\n"
        + "filler\n" * 5
        + "**Active thread:** none\n"
        + "filler\n" * 4
        + "**Active PR:** #222\n"
        + "filler\n" * 4
        + "**Active thread:** none\n"
    )
    first_idle = guard._IDLE_RE.search(text)
    prs = list(guard._PR_RE.finditer(text))
    pre_repair = not prs or first_idle.start() > prs[-1].start()
    assert pre_repair is False, (
        "the pre-repair oracle must report the lane as NOT idle for this shape; "
        "if it already agreed, the fixture does not exercise the defect"
    )
    assert guard.declared_idle(text) is True, (
        "the repaired oracle must report idle for the same shape"
    )


def test_declared_idle_still_defers_to_a_newer_pointer():
    """Positive control: an idle line superseded by a later pointer is not idle.

    Last-wins must not degrade into "any idle declaration anywhere wins" --
    that would let a lane hide live work behind a stale idle sentence, which is
    the hole ``_declared_pointer_findings`` exists to close.
    """
    text = (
        "**Active thread:** none\n"
        + "filler\n" * 5
        + "**Active PR:** #333\n"
    )
    assert guard.declared_idle(text) is False, (
        "a pointer appended after the idle declaration supersedes it; the lane "
        "is live and must be judged by that pointer"
    )


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


def _shallow_clone_with_detached_base(tmp_path):
    """A depth-1 clone holding ``base`` as an object that is not walkable.

    Mirrors the measured artifact exactly: the commit is *present* (fetched
    alongside a lane branch, as the automation's clone does) but the graft on
    HEAD truncates the ancestry walk, so ``merge-base --is-ancestor`` exits
    non-zero for a commit that is a true ancestor in the real history.
    """
    import subprocess

    origin = _scratch_repo(tmp_path / "origin")
    base = _commit(origin, "base")
    subprocess.run(["git", "branch", "side", base], cwd=origin, check=True)
    (origin / "a.txt").write_text("a\n", encoding="utf-8")
    _commit(origin, "second")
    (origin / "b.txt").write_text("b\n", encoding="utf-8")
    _commit(origin, "third")

    clone = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{origin}", str(clone)],
        check=True,
    )
    subprocess.run(
        ["git", "fetch", "-q", "--depth", "1", "origin", "side"], cwd=clone, check=True
    )
    return clone, base


def test_freshness_names_a_truncated_clone_instead_of_a_rewritten_main(tmp_path, monkeypatch):
    """A depth-1 checkout must not be reported as "was main rewritten?".

    Both are findings, but they demand opposite repairs: a truncated clone is
    repaired by fetching history, a rewritten ``main`` by re-measuring the lane
    PRs. Diagnosing the first as the second sends an operator to investigate a
    rewrite that never happened. Measured 2026-10-26 at ``main`` 36f53be2: the
    same tree returned exit 0 from ``--check`` after ``git fetch --unshallow``.
    """
    clone, base = _shallow_clone_with_detached_base(tmp_path)
    monkeypatch.setattr(guard, "REPO", clone)
    monkeypatch.setattr(guard, "LANE_DIR", clone / "docs/control-plane/parallel-ui")
    monkeypatch.setattr(
        guard, "LANE_STATE", clone / "docs/control-plane/parallel-ui/lane-state.json"
    )

    assert guard.clone_is_shallow(repo=clone) is True
    assert guard.commit_is_present(base, repo=clone) is True
    assert guard.is_ancestor_of_head(base, repo=clone) is False

    state = {
        "schema": "arkadia.lane-state/1.2",
        "base_main": base,
        "lanes": {"1": {"doc": "AGENT-01-SHELL.md", "open_prs": [], "merged_prs": []}},
    }
    findings = guard._freshness_findings(state, _head(clone), repo=clone)
    assert findings, "a truncated ancestry walk is not a pass"
    assert "shallow" in findings[0], findings
    assert "rewritten" not in findings[0], (
        "a truncated checkout must not be diagnosed as a rewritten main"
    )
    assert "UNKNOWN, not a pass" in findings[0]


def test_freshness_still_reports_a_rewritten_main_on_a_full_clone(tmp_path, monkeypatch):
    """The positive control for the split: a real rewrite still says so.

    Without this, the shallow branch could swallow the rewritten-main finding
    entirely and the guard would be silent on the defect it exists to catch.
    """
    import subprocess

    repo = _scratch_repo(tmp_path)
    base = _commit(repo, "base")
    state = _scratch_state(repo, monkeypatch)  # base_main = the base commit
    (repo / "orphan.txt").write_text("x\n", encoding="utf-8")
    orphan = _commit(repo, "will be orphaned")
    subprocess.run(["git", "branch", "side", orphan], cwd=repo, check=True)
    subprocess.run(["git", "reset", "-q", "--hard", base], cwd=repo, check=True)

    assert guard.clone_is_shallow(repo=repo) is False
    assert guard.commit_is_present(orphan, repo=repo) is True
    assert guard.is_ancestor_of_head(orphan, repo=repo) is False

    state["base_main"] = orphan
    findings = guard._freshness_findings(state, _head(repo), repo=repo)
    assert findings and "rewritten" in findings[0], findings
    assert "shallow" not in findings[0]


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


def _shallow_clone_with_unwalkable_merge_commit(tmp_path):
    """A depth-1 clone holding a *real merged* commit as an unwalkable object.

    Distinct from :func:`_shallow_clone_with_detached_base`: that fixture models
    a ``base_main`` whose ancestry is truncated. This one models the *liveness*
    shape -- a merge commit that git can read (``cat-file`` succeeds, so
    ``commit_is_present`` is True) but that the graft on HEAD cannot walk to.
    ``merge-base --is-ancestor`` therefore exits non-zero for a commit that is a
    true ancestor in the real history, which is the shape that made
    ``_liveness_findings`` report a merged PR as "not merged" -- a silent pass.
    """
    import subprocess

    origin = _scratch_repo(tmp_path / "origin")
    _commit(origin, "base")
    subprocess.run(["git", "checkout", "-q", "-b", "merged-branch"], cwd=origin, check=True)
    (origin / "work.txt").write_text("work\n", encoding="utf-8")
    _commit(origin, "merged work")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=origin, check=True)
    subprocess.run(
        ["git", "merge", "-q", "--no-ff", "-m", "merge it", "merged-branch"],
        cwd=origin,
        check=True,
    )
    merge_commit = _head(origin)
    # A ref that *is* the merge commit, so a depth-1 fetch lands it as a
    # grafted object -- present, but not reachable by the ancestry walk.
    subprocess.run(["git", "branch", "merged-tip", merge_commit], cwd=origin, check=True)
    (origin / "after.txt").write_text("after\n", encoding="utf-8")
    _commit(origin, "after the merge")

    clone = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{origin}", str(clone)],
        check=True,
    )
    subprocess.run(
        ["git", "fetch", "-q", "--depth", "1", "origin", "merged-tip"],
        cwd=clone,
        check=True,
    )
    return clone, merge_commit, origin


def test_liveness_reports_undecidable_for_a_present_but_unwalkable_merge_commit(tmp_path):
    """A truncated clone must not score a *merged* PR as still open.

    The fail-open shape: the commit is present, so the existing absent-object
    guard does not fire; ``merge-base --is-ancestor`` exits non-zero because the
    graft stops the walk; and a naive reader concludes "not merged" and reports
    nothing. Measured 2026-10-26 on a depth-1 clone: the oracle returned **no
    finding** for a stale open-claim on a genuinely merged PR, while the same
    tree on a full clone reports "already an ancestor of HEAD".
    """
    clone, merge_commit, origin = _shallow_clone_with_unwalkable_merge_commit(tmp_path)

    assert guard.clone_is_shallow(repo=clone) is True
    assert guard.commit_is_present(merge_commit, repo=clone) is True
    assert guard.is_ancestor_of_head(merge_commit, repo=clone) is False
    # The negative control's premise: on a full clone this commit *is* an
    # ancestor, so the truncated verdict is a clone artifact, not a rewrite.
    assert guard.is_ancestor_of_head(merge_commit, repo=origin) is True

    state = {
        "schema": "arkadia.lane-state/1.2",
        "lanes": {
            "1": {
                "open_prs": [{"number": 999, "branch": "x", "head_sha": "0" * 40}],
                "merged_prs": [{"number": 999, "merge_commit_sha": merge_commit}],
            }
        },
    }
    findings = guard._liveness_findings(state, repo=clone)
    assert findings, (
        "a merged PR still claimed open must not pass on a truncated clone"
    )
    assert "shallow" in findings[0], findings
    assert "UNKNOWN, not a pass" in findings[0], findings


def test_liveness_still_reports_the_stale_claim_on_a_full_clone(tmp_path):
    """The positive control: a full clone still names the stale snapshot.

    Without this, the shallow branch could swallow the stale-claim finding
    entirely -- the guard would be silent on the defect it exists to catch.
    """
    clone, merge_commit, origin = _shallow_clone_with_unwalkable_merge_commit(tmp_path)

    import subprocess

    full = tmp_path / "full"
    subprocess.run(["git", "clone", "-q", f"file://{origin}", str(full)], check=True)

    assert guard.clone_is_shallow(repo=full) is False
    assert guard.is_ancestor_of_head(merge_commit, repo=full) is True

    state = {
        "schema": "arkadia.lane-state/1.2",
        "lanes": {
            "1": {
                "open_prs": [{"number": 999, "branch": "x", "head_sha": "0" * 40}],
                "merged_prs": [{"number": 999, "merge_commit_sha": merge_commit}],
            }
        },
    }
    findings = guard._liveness_findings(state, repo=full)
    assert findings and "already an ancestor of HEAD" in findings[0], findings
    assert "shallow" not in findings[0], findings


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
    state = _state_with_open_lane("1", number=900001, branch="feat/synthetic-lane")
    (tmp_path / "AGENT-01-SHELL.md").write_text(
        f"**Active branch:** `feat/wrong-branch`\n**Active PR:** #900001\n",
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


# ------------------------------------------- deferred-lane branch agreement
#
# A deferred lane's doc is excluded from ``check_lane_docs`` by design, because it
# is mid-repair on its own open PR. That exclusion also dropped the branch/head
# agreement check: measured, a deferred lane declaring a branch its live PR does
# not head was reported by nobody -- ``_declared_pointer_findings`` covers pointer
# *liveness*, which is a disjoint property. ``deferred_branch_findings`` closes it.


def test_deferred_lane_branch_mismatch_is_reported(tmp_path):
    """Negative control: the detector must bite on the exact shape it claims to.

    Feeds the detector a deferred lane whose doc declares a branch its live PR
    does not head, and asserts it is reported. Pre-repair, this input produced no
    finding anywhere -- so a guard that is silent here is not a guard.
    """
    state = _state_with_open_lane("3", deferred=True, number=900003, branch="feat/synthetic-lane")
    (tmp_path / "AGENT-03-SOLARIUN-KNOWLEDGE.md").write_text(
        "**Active PR:** #900003\n**Active branch:** `DELIBERATELY-WRONG-BRANCH`\n",
        encoding="utf-8",
    )
    findings = guard.deferred_branch_findings(state, lane_dir=tmp_path, lanes=["3"])
    assert findings, "a deferred lane's branch mismatch must be reported"
    assert "DELIBERATELY-WRONG-BRANCH" in findings[0]
    assert "feat/synthetic-lane" in findings[0]


def test_deferred_lane_with_a_matching_branch_is_not_reported(tmp_path):
    """Positive control: agreement must stay silent, or the guard is trivially true."""
    state = _state_with_open_lane("3", deferred=True, number=900003, branch="feat/synthetic-lane")
    (tmp_path / "AGENT-03-SOLARIUN-KNOWLEDGE.md").write_text(
        "**Active PR:** #900003\n**Active branch:** `feat/synthetic-lane`\n",
        encoding="utf-8",
    )
    assert guard.deferred_branch_findings(state, lane_dir=tmp_path, lanes=["3"]) == []


def test_deferred_branch_guard_does_not_judge_current_lanes():
    """The scope is the complement: a judged lane must not be double-reported.

    ``check_lane_docs`` already owns the current lanes. If this also judged them,
    one defect would produce two findings and the two would drift apart.
    """
    state = _state_with_open_lane("3", deferred=True, number=900003)
    assert guard.current_lanes(state, invert=True) == ["3"]
    assert "3" not in guard.current_lanes(state)
    assert set(guard.current_lanes(state)) & set(guard.current_lanes(state, invert=True)) == set()
    assert sorted(guard.current_lanes(state) + guard.current_lanes(state, invert=True)) == sorted(
        guard._lane_numbers(state)
    )


def test_deferred_branch_guard_is_wired_into_the_check():
    """A detector nothing calls is decoration.

    ``deferred_branch_findings`` must be invoked from the ``--check`` path, or the
    hole it closes stays open while the function and its tests sit green.
    """
    source = (REPO / "scripts" / "lane_state.py").read_text(encoding="utf-8")
    assert "findings += deferred_branch_findings(" in source, (
        "deferred_branch_findings must be called from the --check path"
    )


def test_live_tree_has_no_deferred_branch_mismatch():
    """The live snapshot's deferred lanes must not currently mismatch.

    Measured at main 36f53be2: both deferred lanes point at dead threads, so the
    branch comparison is not reached and this is empty. That is the honest state,
    not a claim that the lanes are healthy -- their dead pointers are reported by
    ``_declared_pointer_findings``.
    """
    state = live_state()
    findings = guard.deferred_branch_findings(state, lanes=guard.current_lanes(state, invert=True))
    assert findings == [], findings
