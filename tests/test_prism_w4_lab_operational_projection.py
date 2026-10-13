"""PRISM Workstream 4 — Lab operational projections (handler oracle + execution).

`GET /api/lab/engineering/overview` (`api.lab_routes.engineering_overview`) folds
four truthful sub-reports into its response:

  * ``integrations``      <- ``lab.engineering_lab.adapters.describe_integrations()``
  * ``android``           <- ``lab.engineering_lab.android.android_capability_report()``
  * ``voice``             <- ``lab.engineering_lab.voice.voice_boundary_report()``
  * ``automation_grammar``<- ``lab.engineering_lab.automations.grammar_view()``

The page rendered these as one ``Object.entries(...).slice(0, 12)`` JSON string
(``EngineeringLabPage.tsx``), so the distinctions the reports exist to state were
an opaque blob — or dropped entirely once the overview grew past twelve keys.

This guard binds the replacement surface (`LabOperationalSurfaces.tsx` +
`labOperational.ts`) to the two things that make its claim real:

1. **The shape is the handlers' own.** Each handler is invoked directly and its
   output is what the projection is given, so the fields read are the handlers'
   keys — not inferred from an interface.

2. **The projection behaves as claimed.** `labOperational.ts` is pure and
   dependency-free, so it is *executed* (not read) under Node and given the real
   handler output. "No credential present" reading as an availability, or an
   authorization-required capability reading as available, is therefore an
   observed output.

Non-collapses under test are the Lab's own doctrine: UNAVAILABLE is not
AVAILABLE, AVAILABLE is not AUTHORIZATION_REQUIRED, a transcript is not an
authorization, and an automation may prepare but never authorize a consequential
action. Node executes the module directly; if Node is unavailable the projection
tests skip with a stated reason rather than silently passing. Each detector has a
negative control.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LAB_SRC = REPO_ROOT / "web" / "arkadia_console" / "src" / "components" / "lab"
PROJECTION = LAB_SRC / "labOperational.ts"
SURFACE = LAB_SRC / "LabOperationalSurfaces.tsx"
PAGE = REPO_ROOT / "web" / "arkadia_console" / "src" / "pages" / "EngineeringLabPage.tsx"


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_operational(overview: dict) -> dict:
    """Execute the real ``labOperational.ts`` over *overview* and return the ledger."""
    node = _node()
    program = (
        f"const m = await import({json.dumps(PROJECTION.as_uri())});\n"
        "const overview = JSON.parse(process.argv[1]);\n"
        "const r = m.readOperationalReadings(overview);\n"
        "process.stdout.write(JSON.stringify({\n"
        "  integrations: r.integrations, android: r.android, voice: r.voice,\n"
        "  scalars: m.scalarOverview(overview),\n"
        "}));\n"
    )
    completed = subprocess.run(
        [node, "--input-type=module", "-e", program, json.dumps(overview)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        pytest.fail(f"projection execution failed: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


# ---------------------------------------------------------------------------
# The shape is the handlers' own
# ---------------------------------------------------------------------------


def test_handlers_emit_the_keys_the_projection_reads():
    """Every field the projection reads must be a key the handlers emit.

    A rename on either side would make the surface report an unconfigured-but-
    healthy reading rather than fail, so the keys are measured, not assumed.
    """
    from lab.engineering_lab.adapters import describe_integrations
    from lab.engineering_lab.android import android_capability_report
    from lab.engineering_lab.voice import voice_boundary_report

    integrations = describe_integrations()
    assert set(integrations) >= {"adapters", "generated_at", "note"}
    assert integrations["adapters"], "control premise: the handler must describe adapters"
    for entry in integrations["adapters"].values():
        assert {"provider", "state", "detail", "credential_source"} <= set(entry)

    android = android_capability_report()
    assert set(android) >= {"surface", "execution_location", "capabilities", "authority"}
    assert {"android_is_not_an_authority_layer", "merge_exposed", "deploy_exposed"} <= set(android["authority"])
    for cap in android["capabilities"]:
        assert {"capability", "state", "human_only_never_exposed"} <= set(cap)

    voice = voice_boundary_report()
    assert {"surface", "recognizer_state", "recognizer_configured", "intents", "human_only_intents"} <= set(voice)


def test_projection_reads_the_real_handler_output():
    from lab.engineering_lab.adapters import describe_integrations
    from lab.engineering_lab.android import android_capability_report
    from lab.engineering_lab.voice import voice_boundary_report

    overview = {
        "integrations": describe_integrations(),
        "android": android_capability_report(),
        "voice": voice_boundary_report(),
        # A couple of the overview's own scalars to confirm they survive as facts.
        "sessions": 3,
    }
    result = run_operational(overview)

    assert result["integrations"]["counts"]["adapters"] == len(describe_integrations()["adapters"])
    assert len(result["android"]["capabilities"]) == len(android_capability_report()["capabilities"])
    assert result["voice"]["recognizer_state"] == voice_boundary_report()["recognizer_state"]
    # The sub-reports are removed from the scalar facts; the counter survives.
    labels = {row["label"] for row in result["scalars"]}
    assert labels == {"sessions"}


# ---------------------------------------------------------------------------
# The non-collapses
# ---------------------------------------------------------------------------


def test_an_unconfigured_adapter_is_not_rendered_available():
    """No credential -> detail says so and the state is not AVAILABLE."""
    from lab.engineering_lab.adapters import describe_integrations

    if any(v["state"] == "AVAILABLE" for v in describe_integrations()["adapters"].values()):
        pytest.skip("an integration credential is present in this environment")
    ledger = run_operational({"integrations": describe_integrations()})["integrations"]
    assert ledger["counts"]["available"] == 0
    for row in ledger["adapters"]:
        assert row["state"] != "AVAILABLE"
        assert "credential" in row["detail"] or "token" in row["detail"]


def test_authorization_required_capabilities_are_not_available():
    """An android capability needing authorization must not read AVAILABLE."""
    from lab.engineering_lab.android import android_capability_report

    ledger = run_operational({"android": android_capability_report()})["android"]
    states = {c["capability"]: c["state"] for c in ledger["capabilities"]}
    assert states.get("initiate_authorized_run") == "AUTHORIZATION_REQUIRED"
    assert ledger["counts"]["authorization_required"] == sum(
        1 for c in android_capability_report()["capabilities"] if c["state"] == "AUTHORIZATION_REQUIRED"
    )


def test_the_control_plane_does_not_expose_merge_or_deploy():
    """The report's own authority block must survive: merge/deploy not exposed."""
    from lab.engineering_lab.android import android_capability_report

    ledger = run_operational({"android": android_capability_report()})["android"]
    assert ledger["authority"]["android_is_not_an_authority_layer"] == "yes"
    assert ledger["authority"]["merge_exposed"] == "no"
    assert ledger["authority"]["deploy_exposed"] == "no"


def test_a_transcript_boundary_preserves_human_authority():
    from lab.engineering_lab.voice import voice_boundary_report

    ledger = run_operational({"voice": voice_boundary_report()})["voice"]
    assert ledger["human_authority_preserved"] == "yes"
    assert ledger["assistant_is_hidden_authority"] == "no"
    assert "AUTHORIZATION" in ledger["non_collapse"]


# ---------------------------------------------------------------------------
# Missing / off-vocabulary readings, with negative controls
# ---------------------------------------------------------------------------


def test_negative_control_an_off_vocabulary_state_is_stated_not_dropped():
    """A state the projection does not know must render as itself, not vanish."""
    overview = {
        "integrations": {
            "adapters": {"google_tasks": {"provider": "google_tasks", "state": "DEGRADED",
                                          "detail": "half-open", "credential_source": None}},
            "generated_at": "t",
            "note": "external services remain authoritative",
        }
    }
    ledger = run_operational(overview)["integrations"]
    (row,) = ledger["adapters"]
    assert row["state"] == "DEGRADED"
    assert row["credential_source"] == "UNKNOWN"  # None is stated, not blank
    assert ledger["counts"]["available"] == 0


def test_negative_control_an_absent_sub_report_is_null_not_a_healthy_default():
    """A sub-report the overview did not carry must read null, not an empty shell."""
    result = run_operational({"sessions": 1})
    assert result["android"] is None
    assert result["voice"] is None
    assert result["integrations"]["adapters"] == []


def test_negative_control_a_missing_field_reads_unknown_not_blank():
    """An undeclared value must be the UNKNOWN sentinel, never an empty string."""
    overview = {"voice": {"surface": "voice_adapter"}}  # every other field absent
    ledger = run_operational(overview)["voice"]
    assert ledger["surface"] == "voice_adapter"
    assert ledger["recognizer_state"] == "UNKNOWN"
    assert ledger["non_collapse"] == "UNKNOWN"
    assert ledger["human_authority_preserved"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# The surface reads the projection, and is read-only
# ---------------------------------------------------------------------------


def test_surface_renders_each_report_and_carries_no_control():
    """The surface must consume the projection and issue no mutating act."""
    source = SURFACE.read_text(encoding="utf-8")
    assert "readOperationalReadings" in source
    assert "buildIntegrationLedger" in source and "buildAndroidLedger" in source and "buildVoiceLedger" in source
    # Read-only: no request of its own, no mutating method.
    assert "apiRequest" not in source
    assert not re.search(r"\b(POST|PUT|PATCH|DELETE)\b", source)
    assert "useHydration" not in source


def test_surface_stays_out_of_the_sibling_grammar_territory():
    """The automation-grammar render is owned by PR #493; this slice must not take it.

    Two open Lane-4 PRs share `EngineeringLabPage.tsx`. Rendering the grammar here
    would duplicate a file another PR owns, so this slice must not surface it.
    """
    surface = SURFACE.read_text(encoding="utf-8")
    assert "AutomationPanel" not in surface
    assert "LabAutomationGrammar" not in surface
    assert "grammar_view" not in surface


def test_page_uses_the_projection_and_drops_the_raw_slice_dump():
    """The page must not fold the overview back into a `slice(0, 12)` JSON blob."""
    source = PAGE.read_text(encoding="utf-8")
    assert "LabOperationalSurfaces" in source
    assert "scalarOverview" in source
    assert ".slice(0, 12)" not in source
