"""
Approval gate for sensitive tool calls.
Extracted from api/main.py (Phase 2 decomposition) — paths unchanged.

Pending approvals live in memory (good enough for single-instance use).
Both the /api/approvals endpoints and CEO chat (api/main.py) share this
module-level state.

Verified boundary (reconciliation/verified-boundary-01):

  * **authentication** — every route requires ``require_auth``; an approval is
    always attributable to a subject.
  * **authorization**  — deciding an approval is a governance act: only a
    principal holding the ``Govern`` permission (``Flamekeeper``, or the
    sovereign ``access_level >= 3`` tier) may approve or reject.
  * **separation**     — ``approve`` records a *decision*; it does **not**
    execute the tool. Execution is a distinct act at
    ``POST /api/tools/{tool_name}/run``, which independently re-checks the
    approval. Recording an authorization and performing the action are not the
    same event.
  * **subject scoping**— an approval is spendable only by the subject that
    requested it, and a decision is never self-approved.
"""
import logging
import threading
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import require_auth

logger = logging.getLogger("arkadia")

PENDING_APPROVALS: dict = {}
APPROVAL_LOCK = threading.Lock()

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


#: Arkadia's governance layer (governance/roles.json) grants the `Govern`
#: permission — "grants high-level governance and approvals" — to the
#: Flamekeeper role only; the Weaver is explicitly "non-authoritative for
#: governance". An approval is a governance decision, so only a principal
#: holding that authority may make one. This is not an invented role: it is the
#: model Arkadia already declares, enforced here rather than assumed.
GOVERN_ROLE = "Flamekeeper"
SOVEREIGN_ACCESS_LEVEL = 3


def _has_govern_authority(user: dict) -> bool:
    """True iff *user* may decide approvals.

    Authority comes from the governance model, not from being authenticated:
    authentication establishes *who* is calling; it does not establish
    entitlement to approve a consequential operation. Two encodings are
    accepted — the canonical ``Flamekeeper`` role, and ``access_level >= 3``,
    the identity system's sovereign tier (see api.auth.require_sovereign).
    """
    if (user.get("role") or "").strip() == GOVERN_ROLE:
        return True
    try:
        return int(user.get("access_level", 0)) >= SOVEREIGN_ACCESS_LEVEL
    except (TypeError, ValueError):
        return False


def _require_govern_authority(user: dict) -> None:
    if not _has_govern_authority(user):
        raise HTTPException(
            status_code=403,
            detail=(
                "Approval authority required: the `Govern` permission is held by "
                "the Flamekeeper role. Authentication alone does not entitle a "
                "principal to approve a consequential operation."
            ),
        )


def queue_approval(
    tool_name: str, payload: dict, description: str, subject_ref: str | None = None
) -> str:
    """Create a pending approval entry; returns the approval_id.

    ``subject_ref`` records the identity on whose behalf the approval was
    requested. The tool-run boundary requires this to match the executing
    caller, so an approval can never be spent by a different subject.
    """
    approval_id = str(uuid.uuid4())[:12]
    with APPROVAL_LOCK:
        PENDING_APPROVALS[approval_id] = {
            "id": approval_id,
            "tool_name": tool_name,
            "payload": payload,
            "description": description,
            "status": "pending",
            "created_at": _now_iso(),
            "decided_at": None,
            "subject_ref": subject_ref,
            "decided_by": None,
            "consumed_at": None,
            "consumed_by": None,
        }
    return approval_id


@router.post("/api/approvals/request")
async def api_request_approval(request: Request, user: dict = Depends(require_auth)):
    """Queue a tool call for approval. Returns approval_id.

    Requires authentication so every approval is attributable to a subject.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    tool_name = body.get("tool_name", "")
    payload = body.get("payload", {})
    description = body.get("description", f"Run {tool_name}")
    approval_id = queue_approval(tool_name, payload, description, subject_ref=user["uid"])
    logger.info(
        "[APPROVAL] created %s for tool=%s subject=%s", approval_id, tool_name, user["uid"]
    )
    return {"approval_id": approval_id, "status": "pending"}


@router.get("/api/approvals")
async def api_list_approvals(status: str | None = None, user: dict = Depends(require_auth)):
    """List approvals visible to the caller.

    Ordinary callers see only the approvals they originated. A principal with
    `Govern` authority (Flamekeeper) sees every pending approval — a reviewer
    must be able to see what it is entitled to decide.
    """
    with APPROVAL_LOCK:
        if _has_govern_authority(user):
            items = list(PENDING_APPROVALS.values())
        else:
            items = [a for a in PENDING_APPROVALS.values() if a.get("subject_ref") == user["uid"]]
    if status:
        items = [a for a in items if a["status"] == status]
    return {"approvals": sorted(items, key=lambda a: a["created_at"], reverse=True)}


@router.post("/api/approvals/{approval_id}/approve")
async def api_approve(approval_id: str, user: dict = Depends(require_auth)):
    """Record an approval decision. Does NOT execute the tool.

    Execution is the caller's act, performed at POST /api/tools/{tool_name}/run
    with this approval_id. Separating the decision from the execution keeps the
    recorded authorization distinct from the permitted action.

    Requires `Govern` authority: deciding an approval is a governance act, and
    being authenticated is not the same as being entitled to approve. A
    principal may not approve its own request — a decision must come from a
    different authority than the requester.
    """
    _require_govern_authority(user)
    with APPROVAL_LOCK:
        approval = PENDING_APPROVALS.get(approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        if approval.get("subject_ref") is not None and approval["subject_ref"] == user["uid"]:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Self-approval is prohibited: the principal requesting an "
                    "approval cannot also decide it. A distinct authority must "
                    "render the decision."
                ),
            )
        approval["status"] = "approved"
        approval["decided_at"] = _now_iso()
        approval["decided_by"] = user["uid"]
    logger.info(
        "[APPROVAL] %s approved by %s for tool=%s",
        approval_id, user["uid"], approval["tool_name"],
    )
    return {"approval_id": approval_id, "status": "approved"}


@router.post("/api/approvals/{approval_id}/reject")
async def api_reject(approval_id: str, user: dict = Depends(require_auth)):
    """Record a rejection. Requires `Govern` authority, as with approval.

    Self-rejection is permitted: withdrawing one's own request is not a
    governance decision over another's consequential operation.
    """
    _require_govern_authority(user)
    with APPROVAL_LOCK:
        approval = PENDING_APPROVALS.get(approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        approval["status"] = "rejected"
        approval["decided_at"] = _now_iso()
        approval["decided_by"] = user["uid"]
    return {"approval_id": approval_id, "status": "rejected"}
