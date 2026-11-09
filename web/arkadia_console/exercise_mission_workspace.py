#!/usr/bin/env python3
"""Exercise the real Engineering Lab mission path in an authenticated browser.

This uses the repository's existing disposable dev-mode test identity. It is
not Firebase authentication and cannot authenticate against production.
The browser drives the existing console controls and reads the canonical Lab
session view; it does not call private UI helpers or create a parallel store.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "render_evidence"
OBJECTIVE = "DEA-01 mission lifecycle browser acceptance"
TARGET = "README.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Existing authenticated-test Vite server.")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    subject = f"ao005-layout-mission-flow-{os.environ.get('GITHUB_RUN_ID', 'local')}"
    OUT.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    api_responses: list[dict[str, object]] = []
    page_errors: list[str] = []
    evidence: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "route": "/engineering-lab",
        "identity": "DISPOSABLE TEST IDENTITY (dev-mode, not Firebase)",
        "subject": subject,
        "objective": OBJECTIVE,
        "target": TARGET,
        "api_responses": api_responses,
        "page_errors": page_errors,
        "screenshots": [],
    }

    browser = None
    context = None
    page = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            page.on("pageerror", lambda error: page_errors.append(str(error)[:300]))

            def record_response(response) -> None:
                path = urlparse(response.url).path
                if not path.startswith("/api/lab/engineering/"):
                    return
                try:
                    body = response.text()[:700] if response.status >= 400 else ""
                except Exception:
                    body = ""
                api_responses.append(
                    {
                        "method": response.request.method,
                        "path": path,
                        "status": response.status,
                        "error_body": body,
                    }
                )

            page.on("response", record_response)
            page.add_init_script(
                f"window.__ARKADIA_TEST_IDENTITY_SUBJECT__ = {json.dumps(subject)};"
            )
            page.goto(f"{base_url}/engineering-lab", wait_until="networkidle", timeout=60_000)
            page.wait_for_function(
                """() => Boolean(document.querySelector('[data-testid="test-identity-banner"]'))
                    && !document.querySelector('[data-testid="auth-threshold-signin"]')""",
                timeout=20_000,
            )
            page.wait_for_selector('[data-testid="mission-workspace"]', timeout=20_000)

            if not page.locator('[data-testid="test-identity-banner"]').count():
                failures.append("disposable test-identity banner was not rendered")
            if page.locator('[data-testid="auth-threshold-signin"]').count():
                failures.append("protected Engineering Lab route remained at the sign-in threshold")

            scope = page.locator('[data-testid="mission-scope-preview"]').inner_text()
            if "LOCAL DRAFT" not in scope or "Operation ceiling" not in scope:
                failures.append("plain-language intent and scoped plan preview did not render")

            page.locator('[data-testid="mission-objective"]').fill(OBJECTIVE)
            page.locator('[data-testid="mission-targets"]').fill(TARGET)

            # 1. Register a bounded agent, then create a PROPOSED mission.
            page.locator('[data-testid="mission-deploy-agent"]').click()
            page.locator('[data-testid="mission-steps"]').get_by_text(
                "Agent deployed", exact=False
            ).wait_for(timeout=20_000)
            page.locator('[data-testid="mission-create"]').click()
            page.wait_for_function(
                """() => (document.querySelector('[data-testid="mission-session-meta"]')?.innerText || '')
                    .includes('PROPOSED')""",
                timeout=20_000,
            )
            session_meta = page.locator('[data-testid="mission-session-meta"]').inner_text()
            session_match = re.search(r"SES-[A-Za-z0-9-]+", session_meta)
            session_id = session_match.group(0) if session_match else None
            if not session_id:
                failures.append("created mission did not expose its canonical session id")
            evidence["session_id"] = session_id
            evidence["session_state_after_create"] = "PROPOSED" if "PROPOSED" in session_meta else "UNKNOWN"

            # 2. Prove the backend refuses execution before human authorization.
            page.locator('[data-testid="mission-attempt"]').click()
            page.locator('[data-testid="mission-steps"]').get_by_text(
                "Execution refused (expected)", exact=False
            ).wait_for(timeout=20_000)
            preauth_meta = page.locator('[data-testid="mission-session-meta"]').inner_text()
            if "PROPOSED" not in preauth_meta:
                failures.append("pre-authorization attempt changed the session out of PROPOSED")
            if "BOUNDARY NOT ENFORCED" in page.locator('[data-testid="mission-steps"]').inner_text():
                failures.append("pre-authorization execution unexpectedly succeeded")

            # 3. Record a separate human-originated authorization.
            page.locator('[data-testid="mission-authorize"]').click()
            page.wait_for_function(
                """() => (document.querySelector('[data-testid="mission-session-meta"]')?.innerText || '')
                    .includes('AUTHORIZED')""",
                timeout=20_000,
            )
            authorization_timeline = page.locator('[data-testid="mission-steps"]').inner_text()
            if "originated_by human" not in authorization_timeline:
                failures.append("authorization record did not report human origin")

            # 4. Execute one read-only operation and inspect the server-returned evidence.
            page.locator('[data-testid="mission-execute"]').click()
            page.wait_for_function(
                """() => {
                    const meta = document.querySelector('[data-testid="mission-session-meta"]')?.innerText || '';
                    const run = document.querySelector('[data-testid="mission-run-id"]')?.textContent?.trim() || '';
                    const trace = document.querySelector('[data-testid="lab-trace-runs"]');
                    const evidence = document.querySelector('[data-testid="mission-evidence-ref"]')?.textContent?.trim() || '';
                    const records = document.querySelector('[data-testid="mission-recorded-evidence"]')?.innerText || '';
                    return meta.includes('READY_FOR_REVIEW') && Boolean(run) && Boolean(trace)
                        && Boolean(evidence) && records.includes('Evidence records');
                }""",
                timeout=45_000,
            )

            run_id = page.locator('[data-testid="mission-run-id"]').inner_text().strip()
            evidence_id = page.locator('[data-testid="mission-evidence-ref"]').inner_text().strip()
            session_meta = page.locator('[data-testid="mission-session-meta"]').inner_text()
            trace_text = page.locator('[data-testid="mission-trace-review"]').inner_text()
            evidence_text = page.locator('[data-testid="mission-recorded-evidence"]').inner_text()
            events_text = page.locator('[data-testid="mission-backend-events"]').inner_text()

            if "READY_FOR_REVIEW" not in session_meta:
                failures.append("the session did not reach READY_FOR_REVIEW")
            if "VERIFYING" not in trace_text:
                failures.append("the run was not presented at the VERIFYING review boundary")
            if "acceptance: not recorded" not in trace_text:
                failures.append("the trace did not preserve the human-acceptance boundary")
            if evidence_id == "—" or evidence_id not in evidence_text:
                failures.append("the run evidence reference did not resolve to a server-returned evidence record")

            required_events = (
                "SESSION_CREATED",
                "PLAN_PRODUCED",
                "SANDBOX_OPERATION",
                "EVIDENCE_RECORDED",
                "PROPOSAL_PREPARED",
                "AUTHORIZATION_REQUIRED",
                "RUN_FINISHED",
            )
            observed_events = [event for event in required_events if event in events_text]
            missing_events = [event for event in required_events if event not in events_text]
            if missing_events:
                failures.append(f"canonical substrate events missing from the session view: {missing_events}")

            execute_responses = [
                item for item in api_responses
                if item["method"] == "POST" and str(item["path"]).endswith("/execute")
            ]
            if [item["status"] for item in execute_responses] != [400, 200]:
                failures.append(
                    "expected exactly one pre-authorization HTTP 400 followed by one authorized HTTP 200 "
                    f"for execute; observed {[item['status'] for item in execute_responses]}"
                )
            elif "SESSION != AUTHORIZATION" not in str(execute_responses[0]["error_body"]):
                failures.append("pre-authorization refusal did not report the canonical SESSION != AUTHORIZATION boundary")

            agent_posts = [
                item for item in api_responses
                if item["method"] == "POST" and item["path"] == "/api/lab/engineering/agents"
            ]
            session_posts = [
                item for item in api_responses
                if item["method"] == "POST" and item["path"] == "/api/lab/engineering/sessions"
            ]
            authorization_posts = [
                item for item in api_responses
                if item["method"] == "POST" and str(item["path"]).endswith("/authorize")
            ]
            if len(agent_posts) != 1 or agent_posts[0]["status"] != 200:
                failures.append(f"agent registration response was not one HTTP 200: {agent_posts}")
            if len(session_posts) != 1 or session_posts[0]["status"] != 200:
                failures.append(f"mission creation response was not one HTTP 200: {session_posts}")
            if len(authorization_posts) != 1 or authorization_posts[0]["status"] != 200:
                failures.append(f"human authorization response was not one HTTP 200: {authorization_posts}")

            evidence["run_id"] = run_id
            evidence["evidence_id"] = evidence_id
            evidence["session_state_after_execution"] = "READY_FOR_REVIEW"
            evidence["run_state"] = "VERIFYING"
            evidence["observed_events"] = observed_events
            evidence["trace_acceptance"] = "not recorded"
            evidence["api_execute_statuses"] = [item["status"] for item in execute_responses]

            flow_shot = OUT / "mission_flow.png"
            page.screenshot(path=str(flow_shot), full_page=True)
            evidence["screenshots"].append(str(flow_shot.relative_to(HERE)))

            # 5. Reload and re-enter: local hint + canonical server read must
            # restore the same mission, run and evidence without reconstructing
            # an authorization record.
            page.reload(wait_until="networkidle", timeout=60_000)
            page.wait_for_selector('[data-testid="mission-resume-offer"]', timeout=20_000)
            resume_offer = page.locator('[data-testid="mission-resume-offer"]').inner_text()
            if session_id and session_id not in resume_offer:
                failures.append("resume offer did not name the server-confirmed mission id")
            page.locator('[data-testid="mission-resume"]').click()
            page.wait_for_function(
                """(expectedRun) => {
                    const meta = document.querySelector('[data-testid="mission-session-meta"]')?.innerText || '';
                    const run = document.querySelector('[data-testid="mission-run-id"]')?.textContent?.trim() || '';
                    const evidence = document.querySelector('[data-testid="mission-evidence-ref"]')?.textContent?.trim() || '';
                    return meta.includes('READY_FOR_REVIEW') && run === expectedRun && Boolean(evidence);
                }""",
                arg=run_id,
                timeout=30_000,
            )
            if page.locator('[data-testid="mission-objective"]').input_value() != OBJECTIVE:
                failures.append("objective did not survive reload and resume")
            if page.locator('[data-testid="mission-targets"]').input_value() != TARGET:
                failures.append("user-scoped read-target hint did not survive reload and resume")
            resumed_evidence = page.locator('[data-testid="mission-recorded-evidence"]').inner_text()
            if evidence_id not in resumed_evidence:
                failures.append("server-recorded evidence did not survive reload and resume")
            if page.locator('[data-testid="mission-resume-offer"]').count():
                failures.append("resume offer remained after the mission was resumed")

            resumed_shot = OUT / "mission_flow_resumed.png"
            page.screenshot(path=str(resumed_shot), full_page=True)
            evidence["screenshots"].append(str(resumed_shot.relative_to(HERE)))
            evidence["resume_session_id"] = session_id
            evidence["resume_run_id"] = page.locator('[data-testid="mission-run-id"]').inner_text().strip()
            evidence["resume_session_state"] = "READY_FOR_REVIEW"

            if page_errors:
                failures.append(f"browser page errors: {page_errors}")
    except Exception as exc:
        failures.append(f"{type(exc).__name__}: {exc}")
        if page is not None:
            try:
                failure_shot = OUT / "mission_flow_failure.png"
                page.screenshot(path=str(failure_shot), full_page=True)
                evidence["screenshots"].append(str(failure_shot.relative_to(HERE)))
            except Exception:
                pass
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass

    evidence["page_errors"] = page_errors
    evidence["failures"] = failures
    evidence["verdict"] = "PASS" if not failures else "FAIL"
    evidence_path = OUT / "mission_flow.json"
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
