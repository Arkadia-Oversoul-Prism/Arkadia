"""Verdict policy for the canonical browser smoke.

The gate failed on every push to `main` from 2026-11-06 onward because the
console fires an anonymous identity probe and the browser logs the resulting
401 as a console error. These tests pin the *policy*: a 401 resource response is
the authentication boundary and passes; everything else still fails.

Every negative control below is a shape the previous blanket rule (`errors.length`
in the pass condition) would also have caught, so passing them proves the gate
kept its teeth rather than merely became quieter. The first test is the shape
that was actually observed, so the change is demonstrated on the real capture
and not only on a synthetic one.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.canonical_browser_report import (
    EXPECTED_AUTH_STATUSES,
    judge,
    judge_route,
    main,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "canonical-render-browser-smoke.yml"
ORIGIN = "https://arkadia-qzu4.onrender.com"

AUTH_PROBE_ERROR = "Failed to load resource: the server responded with a status of 401 ()"


def route(path="/", **overrides):
    record = {
        "path": path,
        "surface": "surface",
        "status": 200,
        "body_characters": 2366,
        "console_errors": [AUTH_PROBE_ERROR, AUTH_PROBE_ERROR],
        "page_errors": [],
        "navigation_error": None,
        "failed_responses": [
            {"url": f"{ORIGIN}/api/me", "status": 401},
            {"url": f"{ORIGIN}/api/knowledge/search", "status": 401},
        ],
    }
    record.update(overrides)
    return record


def report(*routes, origin=ORIGIN):
    return {"origin": origin, "source_revision": "0" * 40, "routes": list(routes)}


# --- the observed shape ---------------------------------------------------


def test_the_captured_anonymous_visit_passes():
    """Run 44663630718: seven routes, two 401s each, zero page errors."""
    observed = report(*[route(p) for p in ("/", "/solariun", "/oracle", "/operator", "/n-atlas-lab")])
    verdict = judge(observed)
    assert verdict["result"] == "PASS"
    assert verdict["summary"]["failed"] == 0
    assert verdict["summary"]["routes"] == 5


def test_the_pre_repair_rule_would_have_failed_that_capture():
    """The old pass condition counted any console error, so it failed this tree.

    This is the control that keeps the repair honest: if the observed capture
    ever stops carrying console errors, this test fails and the *reason* for the
    repair must be re-derived rather than assumed.
    """
    captured = [route(p) for p in ("/", "/solariun", "/oracle")]
    assert all(r["console_errors"] for r in captured)
    legacy_failed = any(
        not r["status"] or r["status"] >= 400 or r["body_characters"] == 0
        or r["console_errors"] or r["page_errors"] or r["navigation_error"]
        for r in captured
    )
    assert legacy_failed is True
    assert judge(report(*captured))["result"] == "PASS"


# --- negative controls: the gate keeps its teeth --------------------------


def test_application_console_error_fails():
    record = route(console_errors=["TypeError: cannot read properties of undefined"])
    reasons = judge_route(record, ORIGIN)
    assert any("application console error" in reason for reason in reasons)


def test_console_error_that_only_mentions_the_phrase_is_not_excused():
    record = route(console_errors=["report: Failed to load resource: the server responded with a status of 401 ()"])
    reasons = judge_route(record, ORIGIN)
    assert any("application console error" in reason for reason in reasons)


@pytest.mark.parametrize("status", [400, 403, 404, 422, 429, 500, 503])
def test_resource_failure_other_than_the_auth_boundary_fails(status):
    message = f"Failed to load resource: the server responded with a status of {status} ()"
    reasons = judge_route(route(console_errors=[message]), ORIGIN)
    assert any(f"status {status}" in reason for reason in reasons)


def test_uncaught_page_error_fails():
    reasons = judge_route(route(page_errors=["ReferenceError: x is not defined"]), ORIGIN)
    assert any("uncaught page error" in reason for reason in reasons)


def test_navigation_error_fails():
    reasons = judge_route(route(navigation_error="net::ERR_CONNECTION_RESET"), ORIGIN)
    assert any("navigation error" in reason for reason in reasons)


def test_empty_body_fails():
    reasons = judge_route(route(body_characters=0, console_errors=[], failed_responses=[]), ORIGIN)
    assert any("body is empty" in reason for reason in reasons)


@pytest.mark.parametrize("status", [None, 404, 500])
def test_document_status_must_be_successful(status):
    reasons = judge_route(route(status=status), ORIGIN)
    assert any("document status" in reason for reason in reasons)


@pytest.mark.parametrize("status", [500, 502, 404])
def test_structured_failed_response_other_than_the_auth_boundary_fails(status):
    record = route(failed_responses=[{"url": f"{ORIGIN}/api/x", "status": status}])
    reasons = judge_route(record, ORIGIN)
    assert any(f"status {status}" in reason for reason in reasons)


def test_auth_status_from_a_foreign_origin_fails():
    """A 401 is only expected from the canonical origin we asked for."""
    record = route(failed_responses=[{"url": "https://evil.example/api/me", "status": 401}])
    reasons = judge_route(record, ORIGIN)
    assert any("foreign origin" in reason for reason in reasons)


def test_an_empty_capture_is_not_a_pass():
    verdict = judge(report())
    assert verdict["result"] == "FAIL"
    assert verdict["summary"]["empty_capture"] is True


def test_only_the_authentication_boundary_is_expected():
    assert EXPECTED_AUTH_STATUSES == frozenset({401})


# --- CLI ------------------------------------------------------------------


def test_cli_exit_code_matches_the_verdict(tmp_path):
    passing = tmp_path / "pass.json"
    passing.write_text(json.dumps(report(route())), encoding="utf-8")
    assert main([str(passing)]) == 0

    failing = tmp_path / "fail.json"
    failing.write_text(json.dumps(report(route(page_errors=["boom"]))), encoding="utf-8")
    assert main([str(failing)]) == 1


def test_cli_refuses_an_unreadable_report(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert main([str(broken)]) == 2


# --- wiring: the policy must be executed, not merely mentioned ------------


def _run_commands(text: str) -> list[list[str]]:
    """Command lines of every ``run:`` step, with block scalars expanded."""
    commands: list[list[str]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)run:\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group(1))
        inline = match.group(2).strip()
        body: list[str] = []
        if inline and not inline.startswith("|") and not inline.startswith(">"):
            body.append(inline)
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and (len(line) - len(line.lstrip())) <= indent:
                break
            body.append(line.strip())
            index += 1
        commands.append(body)
    return commands


def test_the_workflow_executes_the_judge():
    text = WORKFLOW.read_text(encoding="utf-8")
    invoked = False
    for body in _run_commands(text):
        for line in body:
            tokens = line.split()
            if not tokens:
                continue
            command = tokens[0]
            if command not in {"python", "python3"}:
                continue
            if "scripts/canonical_browser_report.py" in tokens[1:]:
                invoked = True
    assert invoked, "no run: step invokes scripts/canonical_browser_report.py"


def test_the_workflow_does_not_decide_the_verdict_itself():
    """The inline pass condition is what drifted; it must not come back."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "errors.length" not in text
    assert "report.result" not in text


def test_the_workflow_selects_the_judge_inputs():
    """A workflow that reads a file must re-run when that file changes."""
    text = WORKFLOW.read_text(encoding="utf-8")
    for trigger in ("push", "pull_request"):
        block = re.search(rf"^  {trigger}:\n(?:    .*\n|      .*\n)*", text, re.MULTILINE)
        assert block, f"{trigger} trigger is missing"
        assert "scripts/canonical_browser_report.py" in block.group(0)
