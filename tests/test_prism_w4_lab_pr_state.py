"""PRISM Workstream 4 — Lab PR-state surface contract (handler oracle + execution).

`GET /api/lab/engineering/pr/{number}` (`api.lab_routes.pr_state`, EL-10) reads a
pull request from GitHub under the Lab's read-only boundary. It answers with
exactly two states and never fabricates:

  * ``AVAILABLE``   -> ``pr`` is the record read from GitHub
  * ``UNAVAILABLE`` -> ``pr`` is ``None`` and ``detail`` says why

Before this surface the console had **no** reference to that handler: the Lab's
own PR-state read was reachable only by hand. This guard binds the replacement
surface (`LabPrState.tsx` + `labPrState.ts`) to the two things that make its
claim real:

1. **The shape is the handler's own.** The handler is invoked directly and the
   keys it returns are asserted, so the fields the projection reads are measured
   rather than inferred from an interface.

2. **The projection behaves as claimed.** `labPrState.ts` is pure and
   dependency-free, so it is *executed* (not read) under Node against the real
   handler output. "Unavailable" reading as a mergeability claim, or a `closed`
   state reading as an outcome, is therefore an observed output.

Non-collapses under test are the Lab's own doctrine: UNAVAILABLE is not
AVAILABLE, reachability is not mergeability, `closed` is not `merged`, and a
declared AVAILABLE with no record is a malformed answer rather than a PR. Node
executes the module directly; if Node is unavailable the projection tests skip
with a stated reason rather than silently passing. Each detector has a negative
control.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LAB_SRC = REPO_ROOT / "web" / "arkadia_console" / "src" / "components" / "lab"
PROJECTION = LAB_SRC / "labPrState.ts"
SURFACE = LAB_SRC / "LabPrState.tsx"
PAGE = REPO_ROOT / "web" / "arkadia_console" / "src" / "pages" / "EngineeringLabPage.tsx"


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_projection(payload) -> dict:
    """Execute the real ``labPrState.ts`` over *payload* and return its readings."""
    node = _node()
    program = (
        f"const m = await import({json.dumps(PROJECTION.as_uri())});\n"
        "const payload = JSON.parse(process.argv[1]);\n"
        "const TEMPLATE = '/api/lab/engineering/pr';\n"
        "const r = m.readPrState(payload);\n"
        "process.stdout.write(JSON.stringify({\n"
        "  reading: r,\n"
        "  availability: m.readAvailability(payload),\n"
        "  lifecycle: m.lifecyclePhrase(r),\n"
        "  mergeable: m.reported(r.mergeableState),\n"
        "  head: m.reported(r.head),\n"
        "  path623: m.prStatePath(TEMPLATE, '623'),\n"
        "  pathBlank: m.prStatePath(TEMPLATE, '  '),\n"
        "  pathZero: m.prStatePath(TEMPLATE, '0'),\n"
        "  pathNeg: m.prStatePath(TEMPLATE, '-1'),\n"
        "  pathWord: m.prStatePath(TEMPLATE, 'abc'),\n"
        "  pathTrail: m.prStatePath(TEMPLATE, ' 12 '),\n"
        "  pathSlash: m.prStatePath(TEMPLATE + '/', '7'),\n"
        "  pathPrefix: m.prStatePath('/api/lab/engineering/pr', '7'),\n"
        "}));\n"
    )
    completed = subprocess.run(
        [node, "--input-type=module", "-e", program, json.dumps(payload)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        pytest.fail(f"projection execution failed: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


# ---------------------------------------------------------------------------
# The shape is the handler's own
# ---------------------------------------------------------------------------


def test_handler_emits_the_keys_the_projection_reads():
    """Every field the projection reads must be a key the handler emits.

    A rename on either side would make the surface report an unreported value
    rather than fail, so the keys are measured, not assumed.
    """
    from api import lab_routes

    # No token in the environment -> the handler must report UNAVAILABLE with a
    # reason and a null record. That is the shape the surface renders.
    absent = asyncio.run(lab_routes.pr_state(623))
    assert set(absent) >= {"state", "detail", "pr"}
    assert absent["state"] == "UNAVAILABLE"
    assert absent["pr"] is None
    assert absent["detail"], "control premise: an unavailable read must state a reason"

    # The AVAILABLE branch's record is built from GitHub's response. Its key set
    # is the contract the projection reads; measure it from the source of truth
    # rather than from a live network call.
    source = (REPO_ROOT / "api" / "lab_routes.py").read_text(encoding="utf-8")
    start = source.index('@router.get("/engineering/pr/{number}")')
    body = source[start : source.index("def _require_session_scoped_project_authorization", start)]
    for key in (
        "number",
        "title",
        "state",
        "draft",
        "mergeable_state",
        "html_url",
        "head",
        "base",
    ):
        assert f'"{key}":' in body, f"the handler no longer emits {key!r}"
    assert '"state": "AVAILABLE"' in body


def test_projection_reads_the_handler_output():
    """The projection is executed against the handler's own unavailability."""
    from api import lab_routes

    payload = asyncio.run(lab_routes.pr_state(623))
    result = run_projection(payload)
    assert result["availability"] == "UNAVAILABLE"
    assert result["reading"]["availability"] == "UNAVAILABLE"
    assert result["reading"]["hasRecord"] is False
    # The handler's reason survives into the ledger verbatim.
    assert result["reading"]["detail"] == payload["detail"]
    # No field is invented from the absence.
    assert result["reading"]["mergeableState"] is None
    assert result["reading"]["state"] is None


# ---------------------------------------------------------------------------
# The projection behaves as claimed
# ---------------------------------------------------------------------------


def test_unavailable_is_not_a_mergeability_reading():
    """UNAVAILABLE must not read as a state, a draft flag, or mergeability."""
    result = run_projection({"state": "UNAVAILABLE", "detail": "http 404", "pr": None})
    reading = result["reading"]
    assert reading["availability"] == "UNAVAILABLE"
    assert reading["hasRecord"] is False
    assert reading["state"] is None
    assert reading["draft"] is None
    assert reading["mergeableState"] is None
    assert reading["head"] is None
    assert result["lifecycle"] == "not reported"
    assert result["mergeable"] == "not reported"


def test_available_record_is_reported_as_measured():
    result = run_projection(
        {
            "state": "AVAILABLE",
            "pr": {
                "number": 623,
                "title": "Lane 1: bind the recorded contracts",
                "state": "open",
                "draft": True,
                "mergeable_state": "dirty",
                "html_url": "https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/623",
                "head": "abc123",
                "base": "main",
            },
        }
    )
    reading = result["reading"]
    assert reading["availability"] == "AVAILABLE"
    assert reading["hasRecord"] is True
    assert reading["state"] == "open"
    assert reading["draft"] is True
    assert reading["mergeableState"] == "dirty"
    assert reading["head"] == "abc123"
    assert reading["base"] == "main"
    # `draft` is a separate fact from `state` and both are stated.
    assert "open" in result["lifecycle"]
    assert "draft" in result["lifecycle"]


def test_closed_does_not_read_as_an_outcome():
    """GitHub returns `closed` for a merged *and* an abandoned PR.

    The handler does not read GitHub's `merged` field, so the projection must not
    claim an outcome. This is the non-collapse the surface exists to preserve.
    """
    result = run_projection(
        {"state": "AVAILABLE", "pr": {"number": 1, "state": "closed", "draft": False, "head": "h", "base": "main"}}
    )
    assert result["reading"]["state"] == "closed"
    assert "outcome not reported" in result["lifecycle"]
    # The phrase names both candidate outcomes only to disclaim them; the
    # projection must not *assert* either one.
    assert result["reading"]["state"] != "merged"
    assert "closed · " in result["lifecycle"]


def test_available_without_a_record_is_not_a_pr():
    """A declared AVAILABLE with a null record is malformed, not a PR."""
    result = run_projection({"state": "AVAILABLE", "pr": None})
    assert result["reading"]["availability"] == "AVAILABLE"
    assert result["reading"]["hasRecord"] is False
    assert result["lifecycle"] == "not reported"


def test_null_payload_is_unknown_not_absent():
    """No answer at all must not render as "there is no pull request"."""
    result = run_projection(None)
    assert result["availability"] == "UNKNOWN"
    assert result["reading"]["hasRecord"] is False
    assert result["lifecycle"] == "not reported"


def test_partial_record_reports_absent_fields_as_unreported():
    """A field GitHub omitted is unreported; it is never inferred."""
    result = run_projection({"state": "AVAILABLE", "pr": {"number": 7, "state": "open", "head": "h"}})
    assert result["reading"]["mergeableState"] is None
    assert result["reading"]["base"] is None
    assert result["mergeable"] == "not reported"
    assert "open" in result["lifecycle"]


# ---------------------------------------------------------------------------
# Path construction
# ---------------------------------------------------------------------------


def test_path_builder_substitutes_an_encoded_segment_in_the_registry_template():
    """The builder substitutes the validated parameter into the exact route template
    declared in the shared registry (SHARED-CONTRACTS §3.1). It refuses a bare
    prefix or trailing path segment instead of guessing.
    """
    result = run_projection(None)
    assert result["path623"] == "/api/lab/engineering/pr/623"
    assert result["pathTrail"] == "/api/lab/engineering/pr/12"
    assert result["pathSlash"] is None
    assert result["pathPrefix"] is None


def test_invalid_numbers_issue_no_request():
    """A malformed number yields no path, so no request is made."""
    result = run_projection(None)
    for key in ("pathBlank", "pathZero", "pathNeg", "pathWord"):
        assert result[key] is None, f"{key} must not build a path"


def test_negative_control_path_builder_can_fail():
    """Negative control: the validator is not trivially true.

    A builder that returned a path for everything would make the invalid-number
    assertions vacuous. This pins the discriminating direction.
    """
    result = run_projection(None)
    assert result["path623"] is not None
    assert result["pathWord"] is None


# ---------------------------------------------------------------------------
# The surface exists, reads only, and is mounted
# ---------------------------------------------------------------------------


def test_surface_reads_only_and_never_mutates():
    text = SURFACE.read_text(encoding="utf-8")
    assert "apiRequest<LabPrStatePayload>" in text
    # A read-only surface must not carry a mutating verb to the Lab boundary.
    for verb in ("POST", "PUT", "PATCH", "DELETE"):
        assert verb not in text, f"the PR-state surface must not issue {verb}"
    assert "prStatePath" in text
    assert "readPrState" in text


def test_surface_preserves_the_non_collapse():
    text = SURFACE.read_text(encoding="utf-8")
    assert "lab-pr-non-collapse" in text
    assert "cannot merge" in text
    assert "GitHub remains the repository authority" in text


def test_surface_is_mounted_on_the_engineering_lab_page():
    page = PAGE.read_text(encoding="utf-8")
    assert "LabPrState" in page
    assert "<LabPrState" in page


def test_neither_owned_file_inlines_the_endpoint_path():
    """One endpoint registry (§3.1): Lane 4 must not declare a second path.

    `src/lib/endpoints.ts` is Lane 1's file. Lane 4 supplies the surface and the
    projection; the prefix is a parameter. A literal here would be a second,
    unreviewed endpoint contract — the defect
    `test_console_endpoint_registry_contract.py` reports as
    "page-local endpoint path(s)".
    """
    for path in (SURFACE, PROJECTION):
        code = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            # Prose about the handler is provenance; a path used as a *value* is
            # the second contract. The authoritative detector is
            # test_console_endpoint_registry_contract.py, which reads the
            # useHydration argument itself; this is the lane-local echo.
            if not line.lstrip().startswith(("*", "/*", "//"))
        ]
        assert "/api/lab/engineering/pr" not in "\n".join(code), (
            f"{path.name} inlines the endpoint path; it must take the registry's "
            "base as a parameter instead"
        )


def test_surface_takes_its_route_template_from_the_shared_registry():
    """The route template's owner is `src/lib/endpoints.ts` (Lane 1), not this lane.

    Asserting the import is what makes the previous test meaningful: a surface
    that inlined nothing *and* read nothing from the registry would be unwired
    by omission rather than by contract.
    """
    text = SURFACE.read_text(encoding="utf-8")
    assert 'from "../../lib/endpoints"' in text
    # The entry name is the contract: an import that is not *read* would leave
    # the surface unwired while looking wired.
    assert "registry.labEngineeringPr" in text


def test_surface_does_not_fire_a_request_per_keystroke():
    """The handler performs a live GitHub read, so the request is on submit."""
    text = SURFACE.read_text(encoding="utf-8")
    assert "<form" in text
    assert "event.preventDefault()" in text
