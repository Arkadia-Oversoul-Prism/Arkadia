"""AO-006 — the Arkadia One canvas: one unified read over three governed surfaces.

The console renders Engineering Lab, Arkana and Weaver as three product
boundaries over **one** backend. Before this module each surface composed its own
set of reads, so "what is happening right now" had three different answers and
the workspace shell had no single contract to hydrate. This router publishes that
single contract.

Design rules, all of which are load-bearing:

1.  **A projection, never a second store.** Every field is read from the
    substrate that already owns it — the Engineering Lab store/runtime, the
    Knowledge OS thread table, the SolSpire project store, the approval ledger.
    Nothing here writes, caches, or duplicates state. A canvas read that
    disagreed with the surface it summarises would be a second truth.

2.  **Identity is the only scope.** Every read is keyed on the verified Firebase
    uid from ``require_auth``. There is no ``subject``/``owner``/``uid`` request
    parameter anywhere in this module, so a caller cannot ask for another
    subject's canvas. Cross-subject reads are impossible by construction rather
    than by a check that could be forgotten.

3.  **Project scope is a narrowing filter, never a widening one.** ``project_id``
    is an optional filter on the Arkana thread listing only. It is *not* an
    ownership check and this module does not claim one: the filter is applied
    inside ``knowledge.vault.list_threads``, which scopes every query by
    ``user_id = <verified uid>`` first and then adds ``AND project_id = ?``. A
    project id the caller does not own therefore cannot widen the read — it can
    only narrow it to a subset of the caller's own threads, and an unowned id
    yields an empty list rather than another subject's data. No route in this
    module accepts a subject/owner/uid parameter, so there is no scope to
    re-verify: identity is the only scope (rule 2).

4.  **Absence is reported, not invented.** A surface with no data returns an
    explicit empty collection plus the contract that would populate it. The
    canvas never fabricates a session, a thread, a worker or a metric.

5.  **Read-only.** This router exposes GET only. Consequential acts (authorize,
    execute, transition, approve) stay on the routes that own them, where their
    human-authorization boundary is enforced. A canvas is a view, not a verb.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import require_auth

router = APIRouter(prefix="/api/canvas", tags=["Arkadia One Canvas"])

#: The three governed surfaces this canvas unifies, in reading order. Declared
#: here so the response and the console cannot disagree about what "one canvas"
#: contains.
CANVAS_SURFACES: tuple[str, ...] = ("engineering-lab", "arkana", "weaver")

#: The contract each surface section is projected from. Published in the payload
#: so a consumer can trace a field back to the route that owns it instead of
#: treating the canvas as a new source of truth.
SURFACE_CONTRACTS: dict[str, str] = {
    "engineering-lab": "/api/lab/engineering/overview",
    "arkana": "/api/commune/threads",
    "weaver": "/api/lab/engineering/sessions",
}


def _lab_section(uid: str) -> dict[str, Any]:
    """Engineering Lab: what is running, and what needs a human.

    Read from the Lab runtime's own overview, which is already subject-scoped.
    The section is a *narrowing* of that view, not a re-derivation: counts come
    from the runtime so the canvas and the Lab surface cannot drift.
    """
    from lab.engineering_lab.runtime import CANONICAL_LOOP, get_runtime

    overview = get_runtime().overview(uid)
    sessions = overview.get("sessions", [])
    return {
        "surface": "engineering-lab",
        "contract": SURFACE_CONTRACTS["engineering-lab"],
        "loop": list(CANONICAL_LOOP),
        "counts": overview.get("counts", {}),
        "sessions": sessions,
        "agents": overview.get("agents", []),
        "automations": overview.get("automations", []),
        "authority": overview.get("authority", {}),
    }


def _arkana_section(uid: str, project_id: int | None) -> dict[str, Any]:
    """Arkana: the conversation substrate, as threads the caller owns.

    ``knowledge.vault.list_threads`` is already user-scoped; the uid is passed
    explicitly so this read cannot fall back to an unscoped listing.
    """
    from knowledge.vault import list_threads

    threads = list_threads(uid, project_id=project_id)
    return {
        "surface": "arkana",
        "contract": SURFACE_CONTRACTS["arkana"],
        "threads": [
            {
                "id": row.get("id"),
                "uuid": row.get("uuid"),
                "title": row.get("title"),
                "project_id": row.get("project_id"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
            for row in threads
        ],
        "count": len(threads),
    }


def _weaver_section(uid: str) -> dict[str, Any]:
    """Weaver: governed execution, with the orchestration dimensions published.

    This is the section AO-006 exists for. Weaver's surface previously declared
    task dependencies, subtask decomposition, retry conditions and a poll
    contract as *unavailable* because no Lab record carried them. The run record
    now does (``AgentRun.depends_on`` / ``subtasks`` / ``attempt`` /
    ``retryable``), so this section publishes them from the real runs rather
    than restating a gap.

    ``updated_at`` is the newest run/session timestamp the caller owns. It is
    published as the poll contract: a consumer may re-read on that value's
    change, and the payload says so explicitly instead of implying a live
    stream the backend does not serve.
    """
    from lab.engineering_lab.store import get_store

    store = get_store()
    sessions = store.list_sessions(uid)
    runs: list[dict[str, Any]] = []
    for session in sessions:
        runs.extend(store.list_runs(session["session_id"], uid))

    # The dependency graph is the union of the real edges the runs publish.
    edges = [
        {"from": dependency, "to": run["run_id"]}
        for run in runs
        for dependency in run.get("depends_on", [])
    ]
    subtasks = [
        {"run_id": run["run_id"], **subtask}
        for run in runs
        for subtask in run.get("subtasks", [])
    ]
    retryable = [
        {
            "run_id": run["run_id"],
            "attempt": run.get("attempt", 1),
            "retryable": bool(run.get("retryable")),
            "retry_policy": run.get("retry_policy", ""),
        }
        for run in runs
    ]

    timestamps = [
        value
        for value in (
            [s.get("updated_at") for s in sessions] + [r.get("updated_at") for r in runs]
        )
        if value
    ]
    return {
        "surface": "weaver",
        "contract": SURFACE_CONTRACTS["weaver"],
        "sessions": sessions,
        "runs": runs,
        "orchestration": {
            "dependencies": edges,
            "subtasks": subtasks,
            "retries": retryable,
            "poll": {
                "mode": "poll",
                "cursor_field": "updated_at",
                "updated_at": max(timestamps) if timestamps else None,
                "note": (
                    "No SSE/WebSocket orchestration transport is served. Re-read "
                    "this canvas when updated_at changes; the value is the newest "
                    "owned session or run timestamp."
                ),
            },
        },
    }


@router.get("")
async def canvas(
    project_id: int | None = Query(
        default=None,
        description="Narrow the Arkana section to one project's threads.",
    ),
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    """The unified canvas: Engineering Lab, Arkana and Weaver in one read.

    Every section is scoped to the authenticated subject. ``project_id`` only
    narrows the Arkana thread listing; it never widens any section's scope.
    """
    uid = user["uid"]
    return {
        "subject_ref": uid,
        "surfaces": list(CANVAS_SURFACES),
        "sections": {
            "engineering-lab": _lab_section(uid),
            "arkana": _arkana_section(uid, project_id),
            "weaver": _weaver_section(uid),
        },
        "read_only": True,
        "note": (
            "A projection over the canonical substrates. Consequential acts "
            "(authorize, execute, transition, approve) remain on the routes that "
            "own them and are not reachable from this canvas."
        ),
    }


@router.get("/surfaces")
async def canvas_surfaces(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """The declared surface set and the contract each section projects from.

    A consumer uses this to discover the canvas without hardcoding the section
    list, so adding a surface is one edit here rather than a console change.
    """
    return {
        "surfaces": [
            {"id": surface, "contract": SURFACE_CONTRACTS[surface]}
            for surface in CANVAS_SURFACES
        ],
        "read_only": True,
    }


@router.get("/sessions/{session_id}")
async def canvas_session(session_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    """One session's full canvas, including its orchestration dimensions.

    Ownership is enforced by the Lab runtime's own subject-scoped lookup: a
    session belonging to another subject raises ``KeyError`` and is reported as
    404, so existence is never leaked across subjects.
    """
    from lab.engineering_lab.runtime import get_runtime

    try:
        view = get_runtime().session_view(session_id, user["uid"])
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")

    runs = view.get("runs", [])
    view["orchestration"] = {
        "dependencies": [
            {"from": dependency, "to": run["run_id"]}
            for run in runs
            for dependency in run.get("depends_on", [])
        ],
        "subtasks": [
            {"run_id": run["run_id"], **subtask}
            for run in runs
            for subtask in run.get("subtasks", [])
        ],
        "retries": [
            {
                "run_id": run["run_id"],
                "attempt": run.get("attempt", 1),
                "retryable": bool(run.get("retryable")),
                "retry_policy": run.get("retry_policy", ""),
            }
            for run in runs
        ],
    }
    view["read_only"] = True
    return view
