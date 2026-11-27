"""Guards for the hourly portfolio ledger and its fairness rule.

`docs/control-plane/openhands/hourly-weaver/2026-11-21-weekly-closure-directive.md`
makes the Hourly Weaver a three-repository portfolio worker and requires a
durable ledger plus a deterministic "oldest verified ``last_progress_at``"
selection. Before this file nothing held either: every pulse re-derived state
from scratch and no record survived the sandbox, so a stalled repository could
be starved indefinitely and no one could show it.

The assertions fall in three groups:

1. the committed artefacts are structurally complete and the recorded
   selection is the arithmetic result (not a typed value);
2. the fairness rule behaves as specified -- a blocked repository does not
   consume the slot, a no-op pulse does not reset the clock, and a tie breaks
   in the directive's fixed order;
3. the refresh measures what it claims -- it reads each repository's declared
   ``default_branch`` instead of assuming ``main``, and a failed observation is
   recorded rather than omitted.

Each rule is proven with a negative control that feeds the detector the shape
it is meant to catch, so a rewrite of the module cannot silently disarm the
guard.
"""

from __future__ import annotations

import copy
import json
import sys
import urllib.parse
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import portfolio_state  # noqa: E402
import portfolio_state_refresh  # noqa: E402

STATE = ROOT / "docs/control-plane/openhands/hourly-weaver/portfolio-state.json"
CURSOR = ROOT / "docs/control-plane/openhands/hourly-weaver/portfolio-cursor.json"
WORKFLOW = ROOT / ".github/workflows/portfolio-state.yml"

SONATA = "Arkadia-Oversoul-Prism/sonata"
FSN = "Arkadia-Oversoul-Prism/family-safety-network"
ARKADIA = "Arkadia-Oversoul-Prism/Arkadia"


@pytest.fixture()
def state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8"))


@pytest.fixture()
def cursor() -> dict:
    return json.loads(CURSOR.read_text(encoding="utf-8"))


def _row(state: dict, name: str) -> dict:
    return next(r for r in state["repositories"] if r["repository"] == name)


def _cursor_row(cursor: dict, name: str) -> dict:
    return next(r for r in cursor["repositories"] if r["repository"] == name)


# --- 1. the committed artefacts -------------------------------------------------


def test_committed_artefacts_support_their_own_selection(state, cursor):
    assert portfolio_state.findings(state, cursor) == []


def test_every_canonical_repository_is_present_exactly_once(state, cursor):
    names = [row["repository"] for row in state["repositories"]]
    assert names == list(portfolio_state.CANONICAL_REPOS)
    authored = [row["repository"] for row in cursor["repositories"]]
    assert sorted(authored) == sorted(portfolio_state.CANONICAL_REPOS)


def test_a_missing_repository_is_reported_not_silently_dropped(state, cursor):
    """Negative control: the pre-repair failure was a repository disappearing."""
    broken = copy.deepcopy(state)
    broken["repositories"] = [
        row for row in broken["repositories"] if row["repository"] != SONATA
    ]
    broken["selection"] = portfolio_state.select_next(broken, cursor)
    problems = portfolio_state.findings(broken, cursor)
    assert any(SONATA in problem and "missing" in problem for problem in problems)


def test_an_abbreviated_sha_is_rejected(state, cursor):
    """Negative control: an abbreviated SHA is not an identity."""
    broken = copy.deepcopy(state)
    _row(broken, ARKADIA)["head_sha"] = _row(broken, ARKADIA)["head_sha"][:12]
    problems = portfolio_state.findings(broken, cursor)
    assert any("full 40-character sha" in problem for problem in problems)


def test_last_progress_at_must_be_the_measured_maximum(state, cursor):
    """Negative control: the fairness input cannot be typed by hand."""
    broken = copy.deepcopy(state)
    _row(broken, FSN)["last_progress_at"] = "2030-01-01T00:00:00Z"
    problems = portfolio_state.findings(broken, cursor)
    assert any("maximum observed activity" in problem for problem in problems)


def test_a_verified_row_without_a_head_is_reported(state, cursor):
    """A "verified" row with no head is the shape a hardcoded `main` produces."""
    broken = copy.deepcopy(state)
    row = _row(broken, SONATA)
    row["head_sha"] = None
    row["last_progress_at"] = portfolio_state.last_progress_at(row)
    broken["selection"] = portfolio_state.select_next(broken, cursor)
    problems = portfolio_state.findings(broken, cursor)
    assert any("VERIFIED but head_sha is empty" in problem for problem in problems)


def test_a_recorded_selection_that_disagrees_with_arithmetic_is_reported(state, cursor):
    # The control must disagree with the *recomputation*, not with a remembered
    # winner: pinning SONATA here passed only while the live clock happened to
    # select Arkadia, so a correct ledger refresh reddened it.
    broken = copy.deepcopy(state)
    recomputed = portfolio_state.select_next(broken, cursor)["repository"]
    disagreeing = next(
        name for name in portfolio_state.CANONICAL_REPOS if name != recomputed
    )
    broken["selection"] = {"repository": disagreeing, "reason": "typed"}
    problems = portfolio_state.findings(broken, cursor)
    assert any("not the recomputed selection" in problem for problem in problems)


# --- 2. the fairness rule -------------------------------------------------------


def test_blocked_repository_does_not_consume_the_slot(state, cursor):
    """The directive: a blocked repository rotates out, it does not idle forever.

    The clock is pinned here on purpose. This rule is about *rotation*, and the
    committed snapshot is re-derived from live activity on every refresh, so an
    expectation read off the recorded timestamps drifts the moment two
    repositories swap order. It did: the first cut asserted the next-oldest was
    Sonata, which held until a refresh left Arkadia 8 seconds older. Live-data
    consistency is `test_committed_artefacts_support_their_own_selection`'s job;
    this one decides the rule.
    """
    pinned = copy.deepcopy(state)
    _row(pinned, SONATA)["last_progress_at"] = "2026-11-26T13:00:00Z"
    _row(pinned, FSN)["last_progress_at"] = "2026-11-26T11:00:00Z"
    _row(pinned, ARKADIA)["last_progress_at"] = "2026-11-26T12:00:00Z"

    # FSN is the oldest, so it is selected while unblocked.
    assert portfolio_state.select_next(pinned, cursor)["repository"] == FSN

    blocked = copy.deepcopy(cursor)
    _cursor_row(blocked, FSN)["blocked"] = True
    selection = portfolio_state.select_next(pinned, blocked)
    # The slot rotates to the next-oldest unblocked repository, not to the
    # tie-break order's first entry: Arkadia (12:00) precedes Sonata (13:00).
    assert selection["repository"] == ARKADIA
    assert any(FSN in line and "blocked" in line for line in selection["skipped"])


def test_a_noop_pulse_does_not_reset_fairness(state, cursor):
    """A pulse that produced nothing did not progress, so it cannot reset the clock."""
    baseline = portfolio_state.select_next(state, cursor)["repository"]

    pulsed = copy.deepcopy(cursor)
    _cursor_row(pulsed, FSN)["last_pulse_at"] = "2031-01-01T00:00:00Z"
    assert portfolio_state.select_next(state, pulsed)["repository"] == baseline


def test_a_comment_does_not_reset_the_fairness_clock():
    """Negative control: ``updated_at`` is a comment clock, so it is not progress.

    The shape is the measured one -- PR #741 carried ``updated_at``
    ``2026-11-26T08:37:43Z`` while its head commit was ``2026-11-25T22:13:53Z``,
    and the timeline's ``commented`` event at ``08:37:43Z`` was the only cause.
    Reading ``updated_at`` as progress lets a conversation starve a repository.
    """
    row = {
        "head_committed_at": "2026-11-25T22:13:53Z",
        "pushed_at": "2026-11-25T22:14:12Z",
        "latest_open_pull": {"number": 741, "updated_at": "2026-11-26T08:37:43Z"},
    }
    assert portfolio_state.last_progress_at(row) == "2026-11-25T22:14:12Z"


def test_a_push_moves_the_fairness_clock():
    """Positive control for the same node: a push *is* progress."""
    row = {
        "head_committed_at": "2026-11-26T08:22:33Z",
        "pushed_at": "2026-11-27T03:14:30Z",
        "latest_open_pull": {"number": 16, "updated_at": "2026-11-26T09:00:00Z"},
    }
    assert portfolio_state.last_progress_at(row) == "2026-11-27T03:14:30Z"


def test_a_comment_time_recorded_as_progress_is_a_finding(state, cursor):
    """The guard rejects a row whose clock is a pull's ``updated_at``."""
    broken = copy.deepcopy(state)
    row = _row(broken, FSN)
    row["last_progress_at"] = row["latest_open_pull"]["updated_at"]
    if row["last_progress_at"] == portfolio_state.last_progress_at(row):
        row["last_progress_at"] = "2030-01-01T00:00:00Z"
    problems = portfolio_state.findings(broken, cursor)
    assert any("maximum observed activity" in problem for problem in problems)


def test_a_verified_row_without_a_push_time_is_reported(state, cursor):
    """``pushed_at`` is the clock, so a VERIFIED row without it fails closed."""
    broken = copy.deepcopy(state)
    row = _row(broken, SONATA)
    row["pushed_at"] = None
    row["last_progress_at"] = portfolio_state.last_progress_at(row)
    broken["selection"] = portfolio_state.select_next(broken, cursor)
    problems = portfolio_state.findings(broken, cursor)
    assert any("VERIFIED but pushed_at is empty" in problem for problem in problems)


def test_an_unverified_observation_is_not_selected(state, cursor):
    """Fail closed: a repository that could not be observed is not a candidate."""
    unobserved = copy.deepcopy(state)
    _row(unobserved, FSN)["observation"] = "UNKNOWN"
    unobserved["selection"] = portfolio_state.select_next(unobserved, cursor)
    assert unobserved["selection"]["repository"] != FSN
    assert any(FSN in line for line in unobserved["selection"]["skipped"])


def test_a_tie_breaks_in_the_directives_fixed_order(state, cursor):
    """Sonata -> FSN -> Arkadia, taken from the order of CANONICAL_REPOS."""
    tied = copy.deepcopy(state)
    for row in tied["repositories"]:
        row["last_progress_at"] = "2026-11-20T00:00:00Z"
    tied["selection"] = portfolio_state.select_next(tied, cursor)
    assert tied["selection"]["repository"] == SONATA


def test_no_eligible_repository_refuses_instead_of_guessing(state, cursor):
    nothing = copy.deepcopy(state)
    for row in nothing["repositories"]:
        row["observation"] = "BLOCKED"
    selection = portfolio_state.select_next(nothing, cursor)
    assert selection["repository"] is None
    assert "no eligible repository" in selection["reason"]


# --- 3. the refresh measures what it claims -------------------------------------


def _routes(repository: str, *, branch="main", sha="a" * 40,
            committed="2026-11-20T00:00:00Z", pushed="2026-11-20T00:00:00Z",
            pulls=(), issues=()) -> list[tuple[str, object]]:
    quoted = urllib.parse.quote(branch)
    return [
        (f"/repos/{repository}", {"default_branch": branch, "pushed_at": pushed}),
        (f"/repos/{repository}/commits/{quoted}",
         {"sha": sha, "commit": {"committer": {"date": committed}}}),
        (f"/repos/{repository}/pulls?state=open&per_page=100", list(pulls)),
        (f"/repos/{repository}/issues?state=open&per_page=100", list(issues)),
    ]


class _Transport:
    """A recorded stand-in for the HTTP layer, so the real ``observe`` runs."""

    def __init__(self, routes, failures: dict[str, Exception] | None = None):
        self.routes = list(routes)
        self.failures = failures or {}
        self.requested: list[str] = []

    def __call__(self, url: str, token: str | None, timeout: float = 30.0):
        self.requested.append(url)
        for fragment, error in self.failures.items():
            if fragment in url:
                raise error
        for suffix, payload in self.routes:
            if url.endswith(suffix):
                return payload
        raise AssertionError(f"unexpected request: {url}")


def test_refresh_reads_the_declared_default_branch_not_main():
    """Regression: sonata's default branch is ``feature/sonata-tts-app``.

    ``GET /repos/.../commits/main`` answers ``422 No commit found for SHA:
    main`` for that repository, so a tool that assumes ``main`` records no head
    for it while reporting success.
    """
    transport = _Transport(
        _routes(
            SONATA,
            branch="feature/sonata-tts-app",
            committed="2026-11-25T21:50:06Z",
            pulls=[{"number": 7, "updated_at": "2026-11-26T00:48:38Z"}],
            issues=[{"number": 1}],
        )
    )
    row = portfolio_state_refresh.observe(SONATA, get=transport, token="x")

    assert row["default_branch"] == "feature/sonata-tts-app"
    assert row["head_sha"] == "a" * 40
    assert row["observation"] == "VERIFIED"
    branch_ref = f"/commits/{urllib.parse.quote('feature/sonata-tts-app')}"
    assert any(url.endswith(branch_ref) for url in transport.requested)
    assert not any(url.endswith("/commits/main") for url in transport.requested)


def test_refresh_derives_the_clock_from_the_push_not_the_comment():
    """``observe`` must not let a pull's ``updated_at`` become the clock.

    ``updated_at`` (``03:14:49``) is *later* than ``pushed_at`` (``03:14:30``)
    here on purpose: the pre-repair derivation recorded the pull's timestamp as
    progress, so this node discriminates the two implementations rather than
    passing on both.
    """
    transport = _Transport(
        _routes(
            FSN,
            committed="2026-11-26T08:22:33Z",
            pushed="2026-11-27T03:14:30Z",
            pulls=[{"number": 16, "updated_at": "2026-11-27T03:14:49Z"}],
        )
    )
    row = portfolio_state_refresh.observe(FSN, get=transport, token="x")

    assert row["pushed_at"] == "2026-11-27T03:14:30Z"
    assert row["last_progress_at"] == "2026-11-27T03:14:30Z"
    assert row["latest_open_pull"]["updated_at"] == "2026-11-27T03:14:49Z"


def test_a_failed_observation_is_recorded_not_omitted():
    """The directive: never silently omit a repository."""
    transport = _Transport([], failures={"/repos/": OSError("network down")})
    row = portfolio_state_refresh.observe(FSN, get=transport, token="x")

    assert row["repository"] == FSN
    assert row["observation"] == "UNKNOWN"
    assert row["detail"], "a failed observation must say why"
    assert row["head_sha"] is None


def test_a_failed_observation_survives_into_the_built_ledger(cursor):
    transport = _Transport([], failures={"/repos/": OSError("network down")})
    rows = [portfolio_state_refresh.observe(name, get=transport, token="x") for name in
            portfolio_state.CANONICAL_REPOS]
    built = portfolio_state_refresh.build(rows, cursor)

    assert [row["repository"] for row in built["repositories"]] == list(
        portfolio_state.CANONICAL_REPOS
    )
    assert built["selection"]["repository"] is None


def test_the_refresh_never_writes_the_token_into_the_ledger(cursor):
    secret = "ghp_THISMUSTNOTAPPEAR"
    transport = _Transport(
        [route for name in portfolio_state.CANONICAL_REPOS for route in _routes(name)]
    )
    rows = [portfolio_state_refresh.observe(name, get=transport, token=secret)
            for name in portfolio_state.CANONICAL_REPOS]
    rendered = json.dumps(portfolio_state_refresh.build(rows, cursor))
    assert secret not in rendered


# --- 4. the gate ----------------------------------------------------------------


def test_the_workflow_executes_this_guard_and_selects_itself():
    """A guard no workflow executes is decoration."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    trigger = workflow.get(True, workflow.get("on"))

    scripts = [
        step["run"]
        for job in (workflow.get("jobs") or {}).values()
        for step in (job.get("steps") or [])
        if isinstance(step.get("run"), str)
    ]
    assert any("tests/test_portfolio_state_ledger.py" in script for script in scripts)
    assert any("portfolio_state.py --check" in script for script in scripts)

    pull = set(trigger["pull_request"]["paths"])
    push = set(trigger["push"]["paths"])
    assert pull == push, "an asymmetric filter lets a surface reach main unjudged"
    for path in (
        "tests/test_portfolio_state_ledger.py",
        "scripts/portfolio_state.py",
        "scripts/portfolio_state_refresh.py",
        ".github/workflows/portfolio-state.yml",
        "docs/control-plane/openhands/hourly-weaver/**",
    ):
        assert path in pull, f"{path} must select the gate that judges it"
    assert "workflow_dispatch" in trigger
