"""Weaver — approval ledger projection (Workstream 4, Lane 4).

Guards the read-only Weaver approval surface added for the Lane-4 reconciliation:

  * the projection is executed for real (node imports the `.ts` and runs it), so
    its behaviour — not a source substring — is what is judged;
  * the record shape and status vocabulary are pinned to the serving handler
    (`api/approval_routes.py`), so a handler rename reddens the guard rather
    than letting the surface silently mis-label a record;
  * the load-bearing boundary is proven with a **negative control**: a recorded
    decision (`approved`) without a real `consumed_at` must read as DECIDED, never
    as CONSUMED. If someone conflates "approved" with "executed", that control
    fails.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONSOLE = REPO_ROOT / "web" / "arkadia_console"
WEAVER_TREE = CONSOLE / "src" / "components" / "weaver"
PROJECTION = WEAVER_TREE / "approvalLedger.ts"
SURFACE = WEAVER_TREE / "ApprovalLedger.tsx"
WEAVER_PAGE = CONSOLE / "src" / "pages" / "WeaverPage.tsx"
HANDLER = REPO_ROOT / "api" / "approval_routes.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_projection(payload: dict) -> dict:
    """Execute the real ``approvalLedger.ts`` over *payload* and return the ledger."""
    node = _node()
    program = (
        f"const m = await import({json.dumps(PROJECTION.as_uri())});\n"
        "const view = JSON.parse(process.argv[1]);\n"
        "process.stdout.write(JSON.stringify(m.buildApprovalLedger(view)));\n"
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


def test_handler_returns_the_key_the_projection_reads():
    """`api_list_approvals` must return `{approvals: [...]}` — the key the
    projection reads. A rename would make the surface report an empty ledger
    (an absence) instead of failing loudly."""
    source = _read(HANDLER)
    assert '"approvals": sorted(' in source or "'approvals': sorted(" in source, (
        "api_list_approvals no longer returns an `approvals` collection"
    )


def test_status_vocabulary_is_the_handler_s_own():
    """The projection's `DECISION_STATUSES` must be the statuses the handler writes."""
    source = _read(HANDLER)
    handler_statuses = set(re.findall(r'"status":\s*"([a-z]+)"', source))
    # The approve/reject handlers set these literal statuses.
    handler_statuses |= set(re.findall(r'status="?([a-z]+)"?', source)) & {
        "approved",
        "rejected",
    }
    assert {"pending", "approved", "rejected"} <= handler_statuses, handler_statuses

    projection = _read(PROJECTION)
    for status in ("pending", "approved", "rejected"):
        assert f'"{status}"' in projection


def test_record_fields_the_projection_reads_are_the_handler_s_keys():
    """The projection reads `subject_ref`, `decided_by`, `consumed_at`,
    `tool_name` — the keys `queue_approval` writes. Read them from the handler,
    not from memory, so a field rename is caught here."""
    source = _read(HANDLER)
    for field in ("subject_ref", "decided_by", "consumed_at", "tool_name", "decided_at"):
        assert f'"{field}"' in source, f"handler no longer writes {field!r}"


# ---------------------------------------------------------------------------
# Behaviour — the projection is executed, not read
# ---------------------------------------------------------------------------


def test_a_decision_is_not_an_execution():
    """The load-bearing property: an `approved` record with no real consumption
    reads as DECIDED, and is explicitly not consumed."""
    ledger = run_projection(
        {
            "approvals": [
                {
                    "id": "a1",
                    "tool_name": "deploy",
                    "status": "approved",
                    "subject_ref": "u-requester",
                    "decided_by": "u-governor",
                    "consumed_at": None,
                }
            ]
        }
    )
    reading = ledger["readings"][0]
    assert reading["phase"] == "DECIDED"
    assert reading["consumed"] is False


def test_negative_control_approved_without_consumption_is_not_consumed():
    """A negative control for the executed behaviour above.

    If the projection inferred consumption from the `status` string (treating
    `approved` as "executed"), this assertion fails. Two records are compared so
    the control cannot pass by accident: one with a real `consumed_at`, one
    without, and only the first may read CONSUMED.
    """
    ledger = run_projection(
        {
            "approvals": [
                {"id": "decided", "status": "approved", "consumed_at": None},
                {"id": "consumed", "status": "approved", "consumed_at": "2026-10-13T00:00:00Z"},
            ]
        }
    )
    by_id = {r["id"]: r for r in ledger["readings"]}
    assert by_id["decided"]["phase"] == "DECIDED"
    assert by_id["decided"]["consumed"] is False
    assert by_id["consumed"]["phase"] == "CONSUMED"
    assert by_id["consumed"]["consumed"] is True


def test_pending_request_is_not_an_authorization():
    ledger = run_projection({"approvals": [{"id": "p", "status": "pending"}]})
    reading = ledger["readings"][0]
    assert reading["phase"] == "REQUESTED"
    assert reading["consumed"] is False


def test_self_decision_is_a_boundary_violation():
    """The backend refuses self-approval (403). A record naming the same identity
    as requester and decider is reported as a violation, not shown as ordinary."""
    ledger = run_projection(
        {
            "approvals": [
                {
                    "id": "self",
                    "status": "approved",
                    "subject_ref": "u-1",
                    "decided_by": "u-1",
                    "consumed_at": None,
                }
            ]
        }
    )
    reading = ledger["readings"][0]
    assert reading["self_decided"] is True
    assert reading["boundary_violation"] is True
    assert ledger["violations"] and ledger["violations"][0]["id"] == "self"


def test_self_rejection_is_a_permitted_withdrawal_not_a_violation():
    """The backend *permits* self-rejection (`api_reject`: "withdrawing one's own
    request is not a governance decision over another's consequential operation"),
    while it refuses self-approval (`api_approve` -> 403). A self-rejection is
    therefore a legitimate record and must not be accused of the self-approval
    boundary.

    This is a **negative control** for the split: both records name the same
    identity as requester and decider, so a projection that flags every
    self-decision reddens the withdrawal assertion, and one that flags no
    self-decision reddens the approval assertion. Neither can pass by accident.
    """
    ledger = run_projection(
        {
            "approvals": [
                {
                    "id": "withdrawn",
                    "status": "rejected",
                    "subject_ref": "u-1",
                    "decided_by": "u-1",
                    "consumed_at": None,
                },
                {
                    "id": "self-approved",
                    "status": "approved",
                    "subject_ref": "u-1",
                    "decided_by": "u-1",
                    "consumed_at": None,
                },
            ]
        }
    )
    by_id = {r["id"]: r for r in ledger["readings"]}

    withdrawn = by_id["withdrawn"]
    assert withdrawn["self_decided"] is True
    assert withdrawn["self_rejected"] is True
    assert withdrawn["self_approved"] is False
    assert withdrawn["boundary_violation"] is False, (
        "a permitted self-rejection was reported as a boundary violation"
    )
    assert withdrawn["phase"] == "DECIDED"
    assert "withdraw" in withdrawn["note"].lower()

    approved = by_id["self-approved"]
    assert approved["self_approved"] is True
    assert approved["self_rejected"] is False
    assert approved["boundary_violation"] is True

    ids = [v["id"] for v in ledger["violations"]]
    assert "self-approved" in ids and "withdrawn" not in ids


def test_a_distinct_decider_is_never_a_self_decision():
    """The guard must not widen: a decision rendered by a *different* principal is
    ordinary, for both an approval and a rejection."""
    ledger = run_projection(
        {
            "approvals": [
                {"id": "ok-a", "status": "approved", "subject_ref": "u-1", "decided_by": "u-2"},
                {"id": "ok-r", "status": "rejected", "subject_ref": "u-1", "decided_by": "u-2"},
            ]
        }
    )
    for reading in ledger["readings"]:
        assert reading["self_decided"] is False
        assert reading["boundary_violation"] is False
    assert ledger["violations"] == []


def test_contradictory_record_is_flagged_not_advanced():
    """A consumed record that is still `pending` cannot have been produced by the
    handler; it is flagged rather than rendered as a normal pending request."""
    ledger = run_projection(
        {"approvals": [{"id": "x", "status": "pending", "consumed_at": "2026-10-13T00:00:00Z"}]}
    )
    reading = ledger["readings"][0]
    assert reading["contradictory"] is True
    assert reading["boundary_violation"] is True


def test_unknown_status_is_reported_not_coerced():
    ledger = run_projection({"approvals": [{"id": "u", "status": "escalated"}]})
    reading = ledger["readings"][0]
    assert reading["status_known"] is False
    assert reading["phase"] == "UNKNOWN"
    assert ledger["counts"]["unknown"] == 1


def test_empty_payload_is_an_empty_ledger_not_a_failure():
    ledger = run_projection({})
    assert ledger["readings"] == []
    assert ledger["counts"]["total"] == 0


# ---------------------------------------------------------------------------
# The surface reads the served contract and stays read-only
# ---------------------------------------------------------------------------


def test_weaver_page_renders_the_approval_ledger():
    page = _read(WEAVER_PAGE)
    assert 'import { ApprovalLedger }' in page
    assert "<ApprovalLedger />" in page


def test_surface_reads_only_a_served_contract():
    """The advertised blocked `contract=` string must be a served path, so the
    page cannot advertise execution it does not perform."""
    advertised = re.findall(r'contract="([^"]+)"', _read(WEAVER_PAGE))
    assert advertised, "the Weaver page advertises no blocked state -- the check would be vacuous"

    from api.main import app

    served = {re.sub(r"\{[^}]*\}", "{}", p) for p in app.openapi()["paths"].keys()}
    for value in advertised:
        normalized = re.sub(r"\{[^}]*\}", "{}", value)
        assert normalized in served, f"advertised contract {value!r} is not a served path"


def test_surface_issues_no_mutating_request():
    """The ledger is read-only: it must not issue a write, nor reference the
    approve/reject/request routes, which are `Govern`-authority acts."""
    surface = _read(SURFACE)
    assert "apiRequest" in surface, "the surface should read the contract"
    # apiRequest defaults to GET; an explicit method is how a write would appear.
    assert "method:" not in surface, "the read-only ledger issues a non-GET request"
    for fragment in ('"POST"', "'POST'", '"PUT"', '"DELETE"'):
        assert fragment not in surface, f"the read-only ledger uses {fragment}"
    for path in ("/approvals/request", "/approve", "/reject"):
        assert path not in surface, f"the read-only ledger references the mutating `{path}` route"
