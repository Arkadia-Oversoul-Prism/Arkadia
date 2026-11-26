#!/usr/bin/env python3
"""Decide the canonical browser-smoke verdict from a captured route report.

`canonical-render-browser-smoke.yml` drives a real headless browser against the
canonical production origin and records, per route, the HTTP status, the
rendered body length, uncaught page errors, navigation errors and console
errors. This module turns that capture into a verdict.

Why the decision lives here
---------------------------
The workflow used to decide inline, with `errors.length` in the pass condition.
Every route on the console fires an anonymous identity probe, so the browser
logs `Failed to load resource: the server responded with a status of 401 ()` on
every route, including the public ones. A 401 from an auth-gated endpoint is the
*expected* answer for a visitor with no identity: `lib/useHydration.ts` maps it
to the `auth-required` state and the surface renders its signed-out view. The
blanket rule therefore failed the gate on every push to `main` from 2026-11-06
onward, and a gate that cannot pass carries no signal about production.

The policy below is narrow on purpose. A *resource-load* console entry is judged
by the status code the browser reports in it: 401 is the authentication
boundary and is expected; every other status (and every non-resource console
entry, which is an application `console.error`) still fails. Uncaught page
errors, navigation errors, a non-200 document, and an empty body all fail. So
the gate keeps its teeth and stops reporting a healthy anonymous visit as a
defect.

Read-only: consumes a JSON file, performs no network or repository access.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterable, Mapping

# Statuses that legitimately answer an anonymous identity probe. 401 means "no
# usable identity" and is the state the console renders as signed-out. 403 is
# deliberately absent: it means a *known* identity was refused, which an
# anonymous visit must never produce.
EXPECTED_AUTH_STATUSES = frozenset({401})

# Chrome's own wording for a resource the browser could not load. Anchored, so a
# `console.error()` that merely mentions the phrase is not mistaken for one.
RESOURCE_LOAD_RE = r"^Failed to load resource: the server responded with a status of (\d{3})\b"

_PASS = "PASS"
_FAIL = "FAIL"


def _origin_of(url: str) -> str:
    """Scheme + host + port of an absolute URL, or '' when unparseable."""
    if not isinstance(url, str) or "://" not in url:
        return ""
    scheme, rest = url.split("://", 1)
    authority = rest.split("/", 1)[0]
    return f"{scheme}://{authority}".lower()


def _resource_status(text: str) -> int | None:
    """The status a browser resource-load console entry names, else ``None``.

    ``None`` means "this is not a resource-load entry", which makes it an
    application console error and therefore a failure.
    """
    import re

    match = re.match(RESOURCE_LOAD_RE, text.strip())
    if not match:
        return None
    return int(match.group(1))


def judge_route(record: Mapping[str, Any], origin: str) -> list[str]:
    """Reasons this route fails. Empty list means the route passed."""
    reasons: list[str] = []

    status = record.get("status")
    if not isinstance(status, int) or status >= 400:
        reasons.append(f"document status {status!r} is not a 2xx/3xx response")

    body_characters = record.get("body_characters")
    if not isinstance(body_characters, int) or body_characters == 0:
        reasons.append("rendered body is empty")

    if record.get("navigation_error"):
        reasons.append(f"navigation error: {record['navigation_error']}")

    for message in record.get("page_errors") or []:
        reasons.append(f"uncaught page error: {message}")

    for message in record.get("console_errors") or []:
        code = _resource_status(str(message))
        if code is None:
            reasons.append(f"application console error: {message}")
        elif code not in EXPECTED_AUTH_STATUSES:
            reasons.append(f"resource failed with status {code}: {message}")

    expected_origin = _origin_of(origin)
    for failed in record.get("failed_responses") or []:
        if not isinstance(failed, Mapping):
            reasons.append(f"malformed failed-response record: {failed!r}")
            continue
        code = failed.get("status")
        url = str(failed.get("url") or "")
        if code not in EXPECTED_AUTH_STATUSES:
            reasons.append(f"request failed with status {code}: {url}")
            continue
        if expected_origin and _origin_of(url) != expected_origin:
            reasons.append(f"expected-auth status {code} came from a foreign origin: {url}")

    return reasons


def judge(report: Mapping[str, Any]) -> dict[str, Any]:
    """Verdict for a whole report.

    Returns ``{"result", "routes", "summary"}``; ``result`` is ``PASS`` only
    when every route passed *and* at least one route was captured, so an empty
    capture cannot pass by vacuity.
    """
    origin = str(report.get("origin") or "")
    routes = report.get("routes") or []
    verdicts = []
    for record in routes:
        if not isinstance(record, Mapping):
            verdicts.append({"path": None, "verdict": _FAIL, "reasons": ["malformed route record"]})
            continue
        reasons = judge_route(record, origin)
        verdicts.append(
            {
                "path": record.get("path"),
                "surface": record.get("surface"),
                "verdict": _FAIL if reasons else _PASS,
                "reasons": reasons,
            }
        )

    failed = [v for v in verdicts if v["verdict"] == _FAIL]
    if not verdicts:
        result = _FAIL
    else:
        result = _FAIL if failed else _PASS

    return {
        "result": result,
        "routes": verdicts,
        "summary": {
            "routes": len(verdicts),
            "passed": len(verdicts) - len(failed),
            "failed": len(failed),
            "origin": origin,
            "source_revision": report.get("source_revision"),
            "empty_capture": not verdicts,
        },
    }


def render(verdict: Mapping[str, Any]) -> str:
    lines = ["CANONICAL BROWSER SMOKE VERDICT", "=" * 34]
    summary = verdict["summary"]
    lines.append(
        f"routes {summary['routes']}  passed {summary['passed']}  failed {summary['failed']}"
        f"  origin {summary['origin'] or '(unknown)'}"
    )
    lines.append(f"source revision: {summary['source_revision'] or '(unknown)'}")
    if summary["empty_capture"]:
        lines.append("no route was captured -- an empty capture is not a pass")
    for route in verdict["routes"]:
        lines.append(f"  {route['verdict']:4}  {route.get('path')}")
        for reason in route["reasons"]:
            lines.append(f"        - {reason}")
    lines.append(f"RESULT: {verdict['result']}")
    return "\n".join(lines)


def _load(path: str) -> Mapping[str, Any]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("report root is not an object")
    return payload


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="path to browser-route-report.json")
    parser.add_argument("--json", action="store_true", help="print the verdict as JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        verdict = judge(_load(args.report))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"cannot read browser report: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print(render(verdict))
    return 0 if verdict["result"] == _PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
