"""GitHub push-webhook surface inventory.

Two operations in ``api.main:app`` handle GitHub push events, and they have
different authentication postures:

``POST /api/github/webhook``
    Verifies an HMAC-SHA256 signature (``X-Hub-Signature-256``) when
    ``SOVEREIGN_KEY`` is configured, and busts the in-memory corpus cache.

``POST /api/webhook/github``
    Has no runtime guard at all and forces a full corpus re-ingest
    (``_get_scrolls(force=True)``) for any caller that sends
    ``X-GitHub-Event: push``.

Both postures are *disclosed* — ``api/openapi_security.py`` derives
``x-arkadia-auth-boundary`` from the handler's dependency graph, and the second
route is classified ``anonymous_no_auth_guard`` rather than left unclassified.
Disclosure is not endorsement: changing that route's authorization is a
sovereign decision, so this guard does not change it.

What was missing is binding. ``tests/test_openapi_security_production_contract.py``
pins the HMAC route's ``security`` and nothing else, so the anonymous route could
change posture — or a *third* push webhook could be mounted — with no test to
report it. This file binds the whole surface to a recorded inventory: the set of
webhook operations, each one's auth classification, runtime guard and security
schemes. Any addition, removal or posture change is then a visible, reviewed
edit to this record rather than a silent drift.

The same measurement found the second handler *shadowed* the first at module
level: both were named ``github_webhook`` (``ruff --select F811``). FastAPI had
already captured each function at decoration time, so behaviour was unaffected,
but a maintainer editing ``github_webhook`` would silently edit the wrong
handler. The duplicate is renamed, and the emitted ``operationId`` is pinned
here so the rename stays schema-neutral.

Negative controls feed the detectors the defect shapes they exist to catch, so a
guard that stops detecting cannot pass by agreeing with itself.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "api" / "main.py"

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}

#: The published ``operationId`` of the corpus-resync route. Pinned because the
#: handler was renamed to remove a module-level shadowing; the emitted schema
#: must not move with it.
RECORDED_RESYNC_OPERATION_ID = "github_webhook_api_webhook_github_post"

#: Every webhook operation the application serves, with the posture the OpenAPI
#: metadata reports for it. ``security`` is normalized by
#: :func:`_security_schemes` to a tuple of scheme-name tuples.
RECORDED_WEBHOOK_OPERATIONS: dict[tuple[str, str], dict] = {
    ("post", "/api/github/webhook"): {
        "classification": "github_webhook_hmac",
        "runtime_guard": "X-Hub-Signature-256",
        "security": (("GitHubWebhookHMAC",),),
    },
    ("post", "/api/webhook/github"): {
        "classification": "anonymous_no_auth_guard",
        "runtime_guard": None,
        "security": (),
    },
}


# ---------------------------------------------------------------------------
# Detectors (module level, so the negative controls exercise the same code the
# live assertions use).
# ---------------------------------------------------------------------------


def _security_schemes(operation: dict) -> tuple[tuple[str, ...], ...]:
    """An operation's ``security`` requirement, normalized for comparison."""
    return tuple(
        tuple(sorted(requirement)) for requirement in operation.get("security") or []
    )


def _webhook_inventory(schema: dict) -> dict[tuple[str, str], dict]:
    """Every served operation whose path names a webhook, with its posture."""
    inventory: dict[tuple[str, str], dict] = {}
    for path, operations in (schema.get("paths") or {}).items():
        if "webhook" not in path:
            continue
        for method, operation in operations.items():
            if method not in HTTP_METHODS:
                continue
            boundary = operation.get("x-arkadia-auth-boundary") or {}
            inventory[(method, path)] = {
                "classification": boundary.get("classification"),
                "runtime_guard": boundary.get("runtime_guard"),
                "security": _security_schemes(operation),
            }
    return inventory


def _inventory_drift(
    actual: dict[tuple[str, str], dict],
    recorded: dict[tuple[str, str], dict],
) -> list[str]:
    """Differences between the served surface and the recorded one.

    An empty list means the two agree. A new webhook, a retired one, and a
    changed posture are reported separately: they call for different reviews.
    """
    drift: list[str] = []
    for key in sorted(set(actual) - set(recorded)):
        drift.append(
            f"{key[0].upper()} {key[1]} is a webhook operation absent from the "
            f"recorded inventory"
        )
    for key in sorted(set(recorded) - set(actual)):
        drift.append(
            f"{key[0].upper()} {key[1]} is recorded but is no longer served"
        )
    for key in sorted(set(actual) & set(recorded)):
        if actual[key] != recorded[key]:
            drift.append(
                f"{key[0].upper()} {key[1]} posture drifted: recorded "
                f"{recorded[key]!r}, served {actual[key]!r}"
            )
    return drift


def _duplicate_function_names(source: str) -> list[str]:
    """Module-level function names defined more than once in ``source``.

    The ``ruff`` F811 class. Only module-level definitions are considered: a
    second definition of the same name silently replaces the first binding, so
    the name a reader edits is not necessarily the object the decorator captured.
    """
    lines: dict[str, list[int]] = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines.setdefault(node.name, []).append(node.lineno)
    return sorted(name for name, seen in lines.items() if len(seen) > 1)


# ---------------------------------------------------------------------------
# Live assertions.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schema() -> dict:
    from api.main import app

    return app.openapi()


def test_live_webhook_surface_matches_the_recorded_inventory(schema: dict) -> None:
    drift = _inventory_drift(_webhook_inventory(schema), RECORDED_WEBHOOK_OPERATIONS)
    assert drift == [], "\n".join(drift)


def test_recorded_inventory_is_exactly_the_two_github_push_webhooks() -> None:
    """The record is content, not a wildcard: removing an entry is an edit.

    Without this, deleting the anonymous entry would make the inventory check
    vacuous for it — the recorded set would simply no longer contain the route.
    """
    assert set(RECORDED_WEBHOOK_OPERATIONS) == {
        ("post", "/api/github/webhook"),
        ("post", "/api/webhook/github"),
    }
    assert (
        RECORDED_WEBHOOK_OPERATIONS[("post", "/api/webhook/github")]["runtime_guard"]
        is None
    ), "the anonymous resync route is recorded as unguarded; a guard is a posture change"


def test_resync_route_keeps_its_published_operation_id(schema: dict) -> None:
    operation = schema["paths"]["/api/webhook/github"]["post"]
    assert operation["operationId"] == RECORDED_RESYNC_OPERATION_ID


def test_main_module_defines_no_duplicate_function_name() -> None:
    duplicates = _duplicate_function_names(MAIN_PATH.read_text(encoding="utf-8"))
    assert duplicates == [], (
        "api/main.py defines these function names more than once, so a second "
        f"definition shadows the first: {duplicates}"
    )


# ---------------------------------------------------------------------------
# Controls. These prove the detectors report the defects they exist to catch.
# ---------------------------------------------------------------------------


def _synthetic_schema(
    *operations: tuple[str, str, str, str | None, tuple[str, ...]],
) -> dict:
    schema: dict = {"paths": {}}
    for method, path, classification, guard, security in operations:
        schema["paths"].setdefault(path, {})[method] = {
            "x-arkadia-auth-boundary": {
                "classification": classification,
                "runtime_guard": guard,
            },
            "security": [{scheme: []} for scheme in security],
        }
    return schema


def test_negative_control_reports_a_third_webhook() -> None:
    schema = _synthetic_schema(
        (
            "post",
            "/api/github/webhook",
            "github_webhook_hmac",
            "X-Hub-Signature-256",
            ("GitHubWebhookHMAC",),
        ),
        ("post", "/api/webhook/github", "anonymous_no_auth_guard", None, ()),
        ("post", "/api/webhook/github/extra", "anonymous_no_auth_guard", None, ()),
    )
    drift = _inventory_drift(_webhook_inventory(schema), RECORDED_WEBHOOK_OPERATIONS)
    assert any("/api/webhook/github/extra" in finding for finding in drift), drift


def test_negative_control_reports_a_posture_change() -> None:
    schema = _synthetic_schema(
        (
            "post",
            "/api/github/webhook",
            "github_webhook_hmac",
            "X-Hub-Signature-256",
            ("GitHubWebhookHMAC",),
        ),
        # The anonymous route gained a guard: a real posture change.
        (
            "post",
            "/api/webhook/github",
            "github_webhook_hmac",
            "X-Hub-Signature-256",
            ("GitHubWebhookHMAC",),
        ),
    )
    drift = _inventory_drift(_webhook_inventory(schema), RECORDED_WEBHOOK_OPERATIONS)
    assert any("posture drifted" in finding for finding in drift), drift


def test_positive_control_accepts_the_recorded_inventory() -> None:
    """The same detector is silent when the surface matches: not trivially noisy."""
    schema = _synthetic_schema(
        (
            "post",
            "/api/github/webhook",
            "github_webhook_hmac",
            "X-Hub-Signature-256",
            ("GitHubWebhookHMAC",),
        ),
        ("post", "/api/webhook/github", "anonymous_no_auth_guard", None, ()),
    )
    assert _inventory_drift(_webhook_inventory(schema), RECORDED_WEBHOOK_OPERATIONS) == []


def test_negative_control_reports_a_duplicate_function_name() -> None:
    source = "async def github_webhook(request):\n    pass\n\n\nasync def github_webhook(request):\n    pass\n"
    assert _duplicate_function_names(source) == ["github_webhook"]
