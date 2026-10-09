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
    KNOWN_FRONTENDS,
    MARKER_APP,
    MARKERS,
    classify_deployment_identity,
    classify_marker_oracle,
    classify_sg04,
    classify_source_lineage,
    frontend_of,
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
    """Source closure is verified, but the verdict must not claim a marker
    observation it did not make. Closure says every candidate *would* compile the
    same literals; it says nothing about any served artifact."""
    assert classify_source_lineage(_closure(True, True), [], [_dep(OTHER)]) == (
        "VERIFIED (source closed; marker set NOT observed)"
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


# ── the marker oracle must observe, and must know which app it saw ───────────
#
# Measured on the live run of 2026-10-09. The alias served the *Console* app
# (root ``vercel.json`` was repointed to ``web/console`` at 404452e0) while the
# harness scored it against *Prism* markers. Every Prism marker read 0, and the
# harness still printed "VERIFIED (marker set matches, source closed)": an
# entirely-absent marker set was reported as agreement. Source closure was
# genuine; the marker claim was not observed at all, and the two were fused into
# one verdict so the unobserved half could not fail on its own.


def test_all_markers_absent_is_contradicted_not_verified():
    """The defect, at the predicate: for the app the markers describe, a marker
    list that reads 0 everywhere is the strongest possible evidence that the
    artifact diverges. It must never be summarised as agreement."""
    assert classify_marker_oracle(MARKER_APP, {m: 0 for m in MARKERS}, []) == (
        "CONTRADICTED (markers absent from served artifact: "
        + ", ".join(sorted(MARKERS)) + ")"
    )


def test_markers_present_is_the_only_verified_marker_verdict():
    """Positive control: the verdict the harness was claiming without evidence is
    reachable, but only from a positive reading of the app the markers describe."""
    assert classify_marker_oracle(MARKER_APP, {m: 1 for m in MARKERS}, []) == (
        "VERIFIED (marker set observed in served artifact)"
    )


def test_a_different_app_cannot_be_scored_against_this_marker_set():
    """App identity is read from the deployment label, not inferred from markers.
    The alias currently serves Console while the marker literals are Prism, so a
    Console artifact reads 0 on every marker. That is 'not this application' --
    a category error -- and must not be reported as CONTRADICTED, which would
    assert the artifact was scored and disagreed."""
    assert classify_marker_oracle("console", {m: 0 for m in MARKERS}, []) == (
        f"NOT OBSERVED (artifact is 'console'; markers describe '{MARKER_APP}')"
    )
    assert classify_marker_oracle("console", {m: 1 for m in MARKERS}, []) == (
        f"NOT OBSERVED (artifact is 'console'; markers describe '{MARKER_APP}')"
    )


def test_an_undetermined_app_is_not_observed():
    """The marker list describes one application. With no app identity there is
    nothing to score against, so the verdict must not fall through to the
    fetched-artifact branches."""
    assert classify_marker_oracle(None, {m: 1 for m in MARKERS}, []) == (
        f"NOT OBSERVED (served app undetermined; markers describe '{MARKER_APP}')"
    )


def test_unfetched_artifact_is_unknown_not_verified():
    """No artifact means no observation. ``None`` and ``{}`` are different states:
    one is 'nothing was read', the other 'nothing was found'."""
    assert classify_marker_oracle(MARKER_APP, None, []) == "UNKNOWN (no artifact fetched)"
    assert classify_marker_oracle(MARKER_APP, {}, []) == "UNKNOWN (no markers read)"


def test_stale_marker_list_still_blocks_the_marker_verdict():
    assert classify_marker_oracle(MARKER_APP, {m: 1 for m in MARKERS}, ["opportunity-radar"]) == (
        "UNKNOWN (marker list stale: literals absent from source)"
    )


def test_a_partial_reading_names_the_absent_markers():
    """A marker set that is partly present must name what is missing rather than
    degrade to a boolean."""
    observed = {m: 1 for m in MARKERS}
    observed["opportunity-radar"] = 0
    verdict = classify_marker_oracle(MARKER_APP, observed, [])
    assert verdict.startswith("CONTRADICTED")
    assert "opportunity-radar" in verdict
    assert "solspire-object-summary" not in verdict


def test_the_pre_repair_verdict_is_unreachable_from_the_classifier():
    """Negative control: the exact string the harness used to print without ever
    reading a marker. It must not be producible by the classifier, so the defect
    cannot return by restoring an older classifier."""
    for app in ("console", MARKER_APP):
        for observed in (None, {}, {m: 0 for m in MARKERS}, {m: 1 for m in MARKERS}):
            assert "marker set matches" not in classify_marker_oracle(app, observed, [])
    assert "marker set matches" not in classify_source_lineage(_closure(True, True), [], [_dep(OTHER)])


def test_app_identity_is_read_from_the_deployment_label():
    """The only app identity the deployment API exposes is the environment
    suffix, so that is what the harness must parse. App identity is orthogonal to
    the environment class: a Preview deployment of ``console`` is still the
    ``console`` app."""
    assert frontend_of("Production \u2013 console") == "console"
    assert frontend_of("Production \u2013 arkadia-prism") == "arkadia-prism"
    assert frontend_of("Preview \u2013 console") == "console"
    assert frontend_of("Production - console") == "console"
    assert frontend_of("Production") is None
    assert frontend_of("Production \u2013 some-other-project") is None


def test_build_input_scope_is_per_app_not_shared():
    """The two frontends have disjoint build inputs. Scoring Console ancestry
    against a Prism build input is the category error the harness made."""
    assert KNOWN_FRONTENDS["console"] != KNOWN_FRONTENDS["arkadia-prism"]
    assert "web/console/" in KNOWN_FRONTENDS["console"]
    assert "web/public_prism/" in KNOWN_FRONTENDS["arkadia-prism"]
    src = _SCRIPT.read_text(encoding="utf-8")
    assert "last_build_input_commit(app_for_closure)" in src


# ── the classifier is the only copy ──────────────────────────────────────────


def test_classifier_is_a_single_source_of_truth():
    """The boundary must be produced by the tested predicate, not by a second
    inline copy that can drift from it (the defect this pass repairs)."""
    src = _SCRIPT.read_text(encoding="utf-8")
    assert 'report["boundaries"]["build <-> source lineage"] = classify_source_lineage(' in src
    assert 'report["boundaries"]["marker-set oracle"] = classify_marker_oracle(' in src
    assert 'report["boundaries"]["main -> deployment identity"] = classify_deployment_identity(' in src


def test_undetermined_app_does_not_reach_the_marker_call_site_as_this_app():
    """Negative control for the residual defect: the report path must hand the
    classifier the *undetermined* identity, never a coerced ``MARKER_APP``.

    When no Production deployment was observable, the marker link scored an
    artifact it never fetched and printed ``CONTRADICTED (markers absent ...)``.
    The tested classifier already returns NOT OBSERVED for ``None``; the defect
    was a coercing ``or MARKER_APP`` at the call site that made that branch
    unreachable. Pin the call site to the tested predicate and assert the
    coercion is gone, so a re-introduced fallback reddens this test rather than
    silently restoring the false verdict."""
    src = _SCRIPT.read_text(encoding="utf-8")
    assert 'report["boundaries"]["marker-set oracle"] = classify_marker_oracle(' in src
    assert 'report.get("deployed_app") or MARKER_APP' not in src
    assert 'report["boundaries"]["marker-set oracle"] = classify_marker_oracle(\n        report.get("deployed_app"),' in src


def test_an_undetermined_app_is_not_scored_for_sg04():
    """The SG-04 verdict must be NOT EVALUABLE (regression ``None``) when the
    artifact does not belong to the app the SG-04 literals describe -- other
    app, or undetermined. A ``regression: true`` there is a phantom: every
    literal reads 0 because the surface is not in that build."""
    assert classify_sg04(None, MARKER_APP, True, 0)["regression"] is None
    assert classify_sg04(None, MARKER_APP, True, 0)["evaluable"] is False
    assert classify_sg04("console", MARKER_APP, True, 0)["regression"] is None

    # Positive control: the app the literals describe is scored, and the
    # regression is still reachable from a real absence.
    assert classify_sg04(MARKER_APP, MARKER_APP, True, 0)["regression"] is True
    assert classify_sg04(MARKER_APP, MARKER_APP, True, 3)["regression"] is False
    assert classify_sg04(MARKER_APP, MARKER_APP, False, 0)["regression"] is False


def test_sg04_is_produced_by_the_tested_predicate():
    src = _SCRIPT.read_text(encoding="utf-8")
    assert 'report["sg04"] = classify_sg04(' in src


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
