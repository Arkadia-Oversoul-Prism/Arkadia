"""Gate 2 production-observation harness -- classifier fitness tests.

Source-level and pure-function tests, following the convention of
``tests/test_gate2_backend_observation.py``. The live probe is exercised by
running the script; what is proven here is that the harness cannot report a
stronger boundary than its evidence supports.

Defects this pins, all measured on the live run of 2026-10-02:

1. ``environment=Production`` filters out every record, because the query
   parameter is case-insensitive while the record field is capitalized. The
   filter admitted nothing, so the deployment link could never be more than a
   guess.
2. A newest deployment older than main was reported as ``UNKNOWN`` (link
   unproven) rather than ``STALE`` (deploy exists, does not name main). Those
   are different states and only one of them is true.
3. The ``build <-> source lineage`` boundary was computed from a second copy of
   the closure predicate, so it could disagree with the printed closure.

A fourth defect, measured on the live run of 2026-10-04: the record label gained
a project suffix (``Production – arkadia-prism``) and neither the equality
filter nor the server-side ``?environment=Production`` query predicate matches
it. The harness saw *no* production deployments and reported the link as
``UNKNOWN`` -- the absent state -- while a newer production deployment existed.
The label is now matched on an anchored production prefix, and the fetch is
unfiltered so the query predicate cannot reintroduce the omission.
"""

from pathlib import Path

from scripts.gate2_production_observation import (
    classify_deployment_identity,
    classify_source_lineage,
    lineage_closed,
    production_deployments,
)

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "gate2_production_observation.py"

MAIN = "2b167e4f41ca87699db33a28c76f03550db66847"
# Deliberately synthetic: these tests are pure functions and never resolve a
# SHA against git, so a real deployment id would imply provenance it lacks.
OTHER = "f" * 40


def _dep(sha: str, environment: str = "Production") -> dict:
    return {"id": 1, "sha": sha, "ref": sha, "environment": environment, "created_at": "2026-10-02T06:06:28Z"}


# ── deployment filtering ─────────────────────────────────────────────────────


def test_capitalized_environment_is_admitted():
    """The record field is ``Production``; the query parameter is ``production``.
    A case-sensitive filter on the lowercase form admits nothing."""
    assert len(production_deployments([_dep(MAIN)], 12)) == 1


def test_other_environments_are_excluded():
    payload = [_dep(MAIN, "Production"), _dep(OTHER, "Preview"), _dep(OTHER, "staging")]
    assert [d["sha"] for d in production_deployments(payload, 12)] == [MAIN]


def test_project_suffixed_production_labels_are_admitted():
    """Vercel suffixes the project name: ``Production – arkadia-prism``. An
    equality test on the bare form drops these, so once the suffix appeared the
    harness matched no production deployments at all -- a stale-deploy reading
    for a repository that was in fact deployed."""
    labels = ["Production – arkadia-prism", "Production – console"]
    payload = [_dep(MAIN, lab) for lab in labels]
    assert [d["sha"] for d in production_deployments(payload, 12)] == [MAIN, MAIN]


def test_suffixed_preview_label_is_not_admitted():
    """The prefix match must stay anchored: ``Preview – arkadia-prism`` is a
    preview, not a production deployment. This is the negative control for the
    suffix fix -- it fails if the regex is loosened to a substring search."""
    payload = [_dep(OTHER, "Preview – arkadia-prism"), _dep(MAIN, "Production – arkadia-prism")]
    assert [d["sha"] for d in production_deployments(payload, 12)] == [MAIN]


def test_record_without_a_full_sha_is_excluded():
    """A truncated or absent SHA must not be compared as if it were identity."""
    payload = [_dep("57e67c534ff6"), {"id": 2, "environment": "Production"}, _dep(MAIN)]
    assert [d["sha"] for d in production_deployments(payload, 12)] == [MAIN]


def test_non_list_payload_is_not_a_deployment_set():
    """An API error payload must not be iterated as if it were records."""
    assert production_deployments({"__error__": "HTTP 403"}, 12) == []


def test_limit_is_applied_after_filtering():
    payload = [_dep(MAIN), _dep(OTHER), _dep(MAIN)]
    assert len(production_deployments(payload, 2)) == 2


# ── deployment identity: STALE is not UNKNOWN ────────────────────────────────


def test_identity_is_verified_when_deploy_names_main():
    assert classify_deployment_identity(MAIN, [_dep(MAIN)]) == "VERIFIED"


def test_older_deploy_is_stale_not_unknown():
    """The deploy exists and is observable; it simply does not name main. That
    is a stale deploy, and reporting it as UNKNOWN would hide a real fact."""
    assert classify_deployment_identity(MAIN, [_dep(OTHER)]) == "STALE"


def test_identity_is_unknown_only_when_no_deploy_is_observable():
    assert classify_deployment_identity(MAIN, []) == "UNKNOWN"


def test_newest_deploy_decides_identity():
    """Order is the API's (newest first); an older matching deploy must not
    rescue a stale newest one."""
    assert classify_deployment_identity(MAIN, [_dep(OTHER), _dep(MAIN)]) == "STALE"


# ── source lineage: an unchecked candidate cannot close the argument ─────────


def _closure(*checked: bool | None) -> list[dict]:
    return [{"sha": OTHER, "descendant_of_last_build_input": c} for c in checked]


def test_lineage_verified_when_every_candidate_is_a_descendant():
    assert classify_source_lineage(_closure(True, True), [], [_dep(OTHER)]) == (
        "VERIFIED (marker set matches, source closed)"
    )


def test_lineage_unknown_when_a_candidate_diverged():
    assert classify_source_lineage(_closure(True, False), [], [_dep(OTHER)]) == "UNKNOWN"


def test_unchecked_candidate_does_not_close_the_argument():
    """A SHA absent from the local object store is unproven. Treating it as
    checked would let a missing object masquerade as closure."""
    assert classify_source_lineage(_closure(True, None), [], [_dep(OTHER)]) == "UNKNOWN"
    assert lineage_closed(_closure(True, None)) is False


def test_stale_marker_list_blocks_the_verified_verdict():
    """If a marker literal is gone from source, a 0 count is a stale list, not a
    regression -- and the lineage claim cannot be called verified."""
    assert classify_source_lineage(_closure(True), ["opportunity-radar"], [_dep(OTHER)]) == "UNKNOWN"


def test_lineage_unknown_without_candidates_or_prod():
    assert classify_source_lineage([], [], [_dep(OTHER)]) == "UNKNOWN"
    assert classify_source_lineage(_closure(True), [], []) == "UNKNOWN"


def test_lineage_closed_is_a_conjunction_not_an_existence_check():
    assert lineage_closed([]) is False
    assert lineage_closed(_closure(True, True)) is True
    assert lineage_closed(_closure(True, False)) is False


# ── the classifier is the only copy ──────────────────────────────────────────


def test_classifier_is_a_single_source_of_truth():
    """The boundary must be produced by the tested predicate, not by a second
    inline copy that can drift from it (the defect this pass repairs)."""
    src = _SCRIPT.read_text(encoding="utf-8")
    assert 'report["boundaries"]["build <-> source lineage"] = classify_source_lineage(' in src
    assert 'report["boundaries"]["main -> deployment identity"] = classify_deployment_identity(' in src


def test_deployments_are_fetched_unfiltered():
    """The server-side ``?environment=Production`` predicate drops the
    project-suffixed labels and returns an older cohort, so it cannot see the
    newest Production deployment. The fetch is therefore unfiltered and the
    filtering is done client-side by the tested predicate. Pinned because a
    reintroduced query filter is invisible -- it reads as 'no production
    deployments', i.e. the very stale/absent ambiguity this harness exists to
    separate."""
    src = _SCRIPT.read_text(encoding="utf-8")
    assert "/deployments?environment=" not in src
    assert "/deployments?per_page=" in src
