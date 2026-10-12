"""An artifact glob must not be able to count a sibling job's artifact.

`n-atlas-external-beta.yml`'s `bundle-beta-evidence` job downloaded every artifact
matching `pattern: "*-evidence"` and then asserted `len(files) != 2`. That pattern
also selects `natlas-native-golden-evidence`, uploaded by the `native-arkadia-golden-workflow`
job. Both jobs become runnable at the same instant (`bundle` is `needs: beta` with
`if: always()`; `native` is `needs.beta.result == 'success'`), so whether the third
artifact was present when the bundle listed the directory was a race, not a shape.

Measured at `main` `6109c72a` on the branch head `a3c630a2`:

| run | bundle start->end | golden start->end | bundle |
|---|---|---|---|
| `38088702840` | 21:43:43->21:43:49 | 21:43:43->21:44:24 | success (2 files) |
| `38232115080` | 09:47:26->09:47:30 | 09:47:26->09:48:12 | success (2 files) |
| `38233402572` | 10:06:20->10:06:27 | 10:03:48->10:04:30 | failure (3 files) |

The repair narrows the download to `beta-*-evidence` and asserts the invariant the
guard actually means: the two beta evidence files are present and each is `PASS`.

The detector is a pure-source read of the workflow. It has a negative control
(the exact pre-repair shape, which must be flagged) and a positive control (the
repaired shape, which must be silent), so it cannot be disarmed by rewriting the
workflow without reddening a control.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "n-atlas-external-beta.yml"
BUNDLE_JOB = "bundle"

# The pre-repair bundle job, preserved verbatim so the defect stays reconstructable
# and the negative control feeds the detector the shape it must catch.
PRE_REPAIR_BUNDLE = """
  bundle:
    name: bundle-beta-evidence
    needs: beta
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          path: evidence
          pattern: "*-evidence"
          merge-multiple: true
      - name: Verify bundle shape
        run: |
          python - <<'PY'
          import glob, json, sys
          files = glob.glob("evidence/*.json")
          statuses=[]
          for p in files:
              d=json.load(open(p))
              statuses.append(d.get("status"))
          if len(files) != 2 or any(s != "PASS" for s in statuses):
              sys.exit(1)
          PY
"""


def _bundle_job(workflow: dict) -> dict:
    assert BUNDLE_JOB in workflow["jobs"], f"workflow has no `{BUNDLE_JOB}` job"
    return workflow["jobs"][BUNDLE_JOB]


def _download_patterns(job: dict) -> list[str]:
    """Every `pattern:` passed to an `actions/download-artifact` step in `job`."""
    patterns: list[str] = []
    for step in job.get("steps", []):
        if "download-artifact" not in str(step.get("uses", "")):
            continue
        pattern = (step.get("with") or {}).get("pattern")
        if pattern:
            patterns.append(pattern)
    return patterns


def _matrix_ids(workflow: dict) -> list[str]:
    """The `id` of every entry in the beta job's matrix `include` list."""
    strategy = workflow["jobs"]["beta"].get("strategy") or {}
    include = (strategy.get("matrix") or {}).get("include") or []
    return [entry["id"] for entry in include if "id" in entry]


def _expand_matrix(name: str, workflow: dict) -> set[str]:
    """Expand a `beta-${{ matrix.id }}-evidence` upload name over the matrix.

    The beta artifacts are named from the matrix, so a detector that skips
    `${{ }}` names would see no beta artifact at all and could assert nothing.
    """
    marker = "${{ matrix.id }}"
    if marker not in name:
        return {name}
    return {name.replace(marker, beta_id) for beta_id in _matrix_ids(workflow)}


def _artifacts_uploaded_by(workflow: dict, job_id: str) -> set[str]:
    """Every artifact name uploaded by `job_id`, matrix names expanded."""
    names: set[str] = set()
    for step in workflow["jobs"][job_id].get("steps", []):
        if "upload-artifact" not in str(step.get("uses", "")):
            continue
        name = (step.get("with") or {}).get("name")
        if name:
            names |= _expand_matrix(name, workflow)
    return names


def _beta_artifacts(workflow: dict) -> set[str]:
    """The artifacts the bundle job is supposed to bundle: the beta job's own."""
    return _artifacts_uploaded_by(workflow, "beta")


def _foreign_artifacts(workflow: dict) -> set[str]:
    """Artifacts uploaded by any job other than the producer and the bundler.

    These are the names the bundle job must never select. Selecting one makes its
    shape check a race against that job's upload timing.
    """
    names: set[str] = set()
    for job_id in workflow["jobs"]:
        if job_id in {"beta", BUNDLE_JOB}:
            continue
        names |= _artifacts_uploaded_by(workflow, job_id)
    return names


def _inflatable_patterns(workflow: dict) -> list[str]:
    """Download patterns in the bundle job that also select a foreign artifact."""
    foreign = _foreign_artifacts(workflow)
    return [
        pattern
        for pattern in _download_patterns(_bundle_job(workflow))
        if any(fnmatch.fnmatch(name, pattern) for name in foreign)
    ]


def _verify_step_script(job: dict) -> str:
    for step in job.get("steps", []):
        if step.get("name") == "Verify bundle shape":
            return str(step.get("run", ""))
    raise AssertionError("bundle job has no `Verify bundle shape` step")


def _asserts_bare_file_count(job: dict) -> bool:
    """True when the verify step's shape check compares the *total* file count.

    The repaired step names the files it requires and never sizes the directory,
    so any `len(files)` comparison is the racy form. Testing for the bare call
    (rather than `len(files) != 2` and the absence of the word `expected`) keeps
    the detector from being disarmed by an incidental `expected` in a comment.
    """
    return "len(files)" in _verify_step_script(job)


def _live_workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_bundle_download_cannot_select_a_sibling_job_artifact():
    """The bundle's download pattern must not match another job's artifact name."""
    workflow = _live_workflow()
    inflatable = _inflatable_patterns(workflow)
    assert inflatable == [], (
        "bundle job downloads a pattern that also selects a sibling job's artifact, "
        f"so its count is a race: {inflatable}"
    )


def test_bundle_download_selects_exactly_the_beta_evidence_artifacts():
    """The narrowed pattern still selects both beta artifacts — not zero, not one."""
    workflow = _live_workflow()
    beta = _beta_artifacts(workflow)
    assert beta, "workflow uploads no `beta-*` evidence artifacts"

    patterns = _download_patterns(_bundle_job(workflow))
    assert patterns, "bundle job downloads nothing"
    for pattern in patterns:
        matched = {n for n in beta if fnmatch.fnmatch(n, pattern)}
        assert matched == beta, (
            f"pattern {pattern!r} selects {sorted(matched)}, expected {sorted(beta)}"
        )


def test_bundle_verify_does_not_assert_a_total_file_count():
    """The shape check must name the expected files, not count whatever arrived."""
    job = _bundle_job(_live_workflow())
    assert not _asserts_bare_file_count(job), (
        "the verify step asserts a total file count, which a concurrently uploaded "
        "sibling artifact can inflate"
    )


def test_bundle_verify_asserts_both_beta_files_are_pass():
    """The invariant the guard means: both beta files present and each PASS.

    A subset test (`expected - seen`) is required rather than an exact-set match:
    an exact set is a race against the golden job's concurrent `-evidence` upload,
    which lands its own files in the same downloaded directory.
    """
    script = _verify_step_script(_bundle_job(_live_workflow()))
    assert "beta-01-english.json" in script and "beta-02-hausa.json" in script
    assert '"PASS"' in script
    assert "expected - seen" in script, (
        "the verify step must test for the presence of the beta files, not for an "
        "exact directory contents"
    )
    assert "seen != expected" not in script


def test_verify_step_filenames_are_derived_from_the_matrix():
    """The hardcoded filenames must stay bound to the beta matrix.

    `evidence/{beta_id}.json` is written per matrix entry, so a new matrix id
    would otherwise leave the verify step asserting a stale pair and the bundle
    job red for a reason unrelated to the shape it guards.
    """
    workflow = _live_workflow()
    derived = {f"{beta_id}.json" for beta_id in _matrix_ids(workflow)}
    assert derived, "beta matrix declares no ids"

    script = _verify_step_script(_bundle_job(workflow))
    for filename in derived:
        assert filename in script, (
            f"verify step does not assert {filename!r}, which the beta matrix "
            f"writes ({sorted(derived)})"
        )


def test_negative_control_pre_repair_shape_is_flagged():
    """Feed the detector the exact measured pre-repair shape; it must flag it.

    Without this control the guard could be disarmed by restoring `*-evidence`
    and `len(files) != 2` without any test reddening.
    """
    pre = yaml.safe_load(PRE_REPAIR_BUNDLE)["bundle"]

    assert _download_patterns(pre) == ["*-evidence"]
    assert _asserts_bare_file_count(pre)

    # The detector is only meaningful against the real foreign inventory, so build
    # the pre-repair workflow with the real upload names and assert it bites.
    live = _live_workflow()
    live["jobs"][BUNDLE_JOB] = pre
    assert _inflatable_patterns(live) == ["*-evidence"], (
        "the pre-repair `*-evidence` glob must be reported as selecting the golden "
        "job's artifact"
    )


def test_positive_control_repaired_shape_is_silent():
    """The live (repaired) workflow must not be flagged by either detector."""
    live = _live_workflow()
    assert _inflatable_patterns(live) == []
    assert not _asserts_bare_file_count(_bundle_job(live))


def test_detector_bites_on_a_reintroduced_count():
    """A sibling artifact added under a `beta-` prefix must redden the guard.

    Proves the detector reads the real inventory rather than a hardcoded pattern:
    the repair is correct only while no sibling uploads a name the pattern selects.
    """
    live = _live_workflow()
    live["jobs"]["native-golden"]["steps"].append(
        {"uses": "actions/upload-artifact@v4", "with": {"name": "beta-golden-evidence"}}
    )
    assert _inflatable_patterns(live) == ["beta-*-evidence"], (
        "a sibling uploading `beta-golden-evidence` must be reported, or the guard "
        "is a hardcoded pattern rather than a real inventory check"
    )


def test_count_detector_is_not_disarmed_by_an_incidental_expected():
    """`len(files)` plus an unrelated `expected` must still be flagged as a count.

    The count form is the racy one regardless of what else the script mentions, so
    a rewrite that re-adds `len(files)` beside the repaired naming must redden.
    """
    live = _live_workflow()
    job = _bundle_job(live)
    script = _verify_step_script(job)
    for step in job["steps"]:
        if step.get("name") == "Verify bundle shape":
            step["run"] = script.replace(
                "if expected - seen",
                "if len(files) != 2 or expected - seen",
            )
    assert _asserts_bare_file_count(job), (
        "a reintroduced `len(files)` count must be flagged even when the script "
        "also names an `expected` set"
    )
