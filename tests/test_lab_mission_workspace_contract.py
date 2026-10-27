"""The mission workspace contract (ARKADIA Unified Engineering Lab MVP).

The mission workspace is the first surface that *writes* through the Lab API:
it creates a session, records an authorization, and executes a bounded run.
Every shape it depends on is therefore a load-bearing contract, and each one
below was measured against the running backend rather than inferred.

These are source-level assertions, matching the convention used by the other
console-contract guards in this repository. They pin the properties that would
be silently wrong rather than loudly broken:

* the execute endpoint must not be reachable without an authorization step;
* the session view is a WRAPPER, so reading `state` off the response is a bug;
* the surface must not claim acceptance for a run that stops at review.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONSOLE = REPO / "web" / "arkadia_console" / "src"
CONTRACT = CONSOLE / "components" / "lab" / "missionContract.ts"
WORKSPACE = CONSOLE / "components" / "lab" / "MissionWorkspace.tsx"
PAGE = CONSOLE / "pages" / "EngineeringLabPage.tsx"
LAB_ROUTES = REPO / "api" / "lab_routes.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing {path.relative_to(REPO)}"
    return path.read_text(encoding="utf-8")


# -- the served contract the UI depends on ------------------------------------


def test_session_view_is_a_wrapper_not_a_bare_session():
    """`GET /sessions/{id}` returns a wrapper; the UI must unwrap it.

    Measured: the handler returns `runtime.session_view(...)`, whose payload is
    `{session, agent, runs, events, evidence, artifacts, loop, ...}`. A caller
    that reads `.state` off that object gets `undefined` -- a silent wrong
    answer rather than an error. This asserts both sides: the served shape and
    the client's unwrapping of it.
    """
    routes = _read(LAB_ROUTES)
    assert "def session_view" in _read(REPO / "lab" / "engineering_lab" / "runtime.py")
    assert '"session": session,' in _read(REPO / "lab" / "engineering_lab" / "runtime.py")

    contract = _read(CONTRACT)
    assert "interface LabSessionView" in contract
    assert "session: LabSession;" in contract, "the wrapper must expose `session` as its own field"

    workspace = _read(WORKSPACE)
    assert "view.session" in workspace, (
        "the workspace must read the session off the view wrapper; reading it off "
        "the response directly yields undefined"
    )
    assert "getSessionView(" in workspace
    # The bare-session accessor must not exist: it encoded the wrong shape.
    assert not _detects_bare_session_read(contract), (
        "a bare `getSession` would hide the wrapper and reintroduce the undefined-state bug"
    )


def test_execute_is_gated_by_a_separate_authorization_call():
    """SESSION != AUTHORIZATION: the UI must not collapse the two steps.

    The backend refuses a PROPOSED session with 400. The surface therefore needs
    a distinct authorize call, and the execute call must not be reachable
    without it.
    """
    contract = _read(CONTRACT)
    assert "authorizeSession" in contract
    assert "executeBounded" in contract

    workspace = _read(WORKSPACE)
    # The execute button is enabled only when an authorization is present.
    # "Present" means the SUBSTRATE reports one (`session.authorization_ref`),
    # not that this component recorded one locally: a resumed session carries
    # the reference while the local object is empty, and gating on the local
    # object would let step 3 succeed and raise a false BOUNDARY NOT ENFORCED.
    assert re.search(r"const canExecute = Boolean\(session\) && sessionAuthorized", workspace), (
        "execution must require a recorded authorization"
    )
    assert "sessionAuthorized" in workspace
    assert "session?.authorization_ref" in workspace
    # And an explicit pre-approval attempt exists, so the gate is observable.
    assert "onExecuteUnauthorized" in workspace
    assert "Attempt before approval" in workspace

    routes = _read(LAB_ROUTES)
    assert "session must be AUTHORIZED or QUEUED to execute" in _read(
        REPO / "lab" / "engineering_lab" / "runtime.py"
    )
    assert "record_authorization" in routes


def test_run_is_presented_as_a_proposal_not_an_acceptance():
    """A run stops at the review boundary. The surface must not claim success."""
    workspace = _read(WORKSPACE)
    assert "awaiting human review" in workspace
    assert "not an acceptance" in workspace
    assert "cannot merge, deploy, or self-authorize" in workspace
    # The prohibited words must not appear as a completion claim.
    assert "Run succeeded" not in workspace
    assert "deployment complete" not in workspace.lower()


def test_workspace_is_read_only_by_construction():
    """The MVP surface must not be able to request a write."""
    contract = _read(CONTRACT)
    assert "requires_write: false" in contract, (
        "the mission workspace is read-only; a write request must not be expressible"
    )
    # Only read operations are constructed.
    assert 'kind: "read"' in contract
    assert not re.search(r'kind:\s*"write"', contract)


def test_authorization_is_surfaced_as_human_originated():
    """The recorded authorization must be shown as human-originated and bounded."""
    workspace = _read(WORKSPACE)
    assert "originated_by" in workspace
    assert "merge_prohibited" in _read(CONTRACT) or "merge" in _read(CONTRACT)


def test_workspace_is_mounted_on_the_engineering_lab_surface():
    page = _read(PAGE)
    assert "MissionWorkspace" in page
    assert "<MissionWorkspace />" in page, "the workspace must actually render, not merely be imported"


def test_substrate_event_stream_is_rendered_not_narrated():
    """The timeline must read the backend's own events.

    A client-side narration of what the operator clicked is not evidence. The
    surface renders the session's recorded events and says whose sequence it is.
    """
    workspace = _read(WORKSPACE)
    assert "mission-event-stream" in workspace
    assert "backendEvents" in workspace
    assert "recorded by the substrate, not narrated by this surface" in workspace
    assert "view.events" in workspace


def test_mission_paths_come_from_the_one_endpoint_registry():
    """The mission contract must not inline endpoint paths.

    Measured defect: the first cut passed five raw literals to `apiRequest`
    (`"/api/lab/engineering/agents"`, the session collection, and the
    authorize/execute sub-resources), which
    `tests/test_console_endpoint_registry_contract.py` rejects — a literal is a
    second, unreviewed endpoint contract. The paths now derive from
    `endpoints.labAgents` / `endpoints.labSessions`, so a registry rename is a
    single edit.
    """
    contract = _read(CONTRACT)
    assert 'from "../../lib/endpoints"' in contract
    assert "endpoints.labAgents" in contract
    assert "endpoints.labSessions" in contract
    # The declared builder is used for the session view rather than re-derived.
    assert "labSession(sessionId)" in contract
    # No raw Lab path literal may remain.
    literals = re.findall(r'apiRequest<[^>]*>\(\s*(["`])/api/', contract)
    assert literals == [], f"apiRequest is given a raw path literal: {literals}"


def test_negative_control_detector_flags_the_bare_session_read():
    """Negative control: the guard must detect the exact defect it claims to.

    The defect is a client that types the session endpoint as a bare
    `LabSession` and reads `.state` off the wrapper, yielding `undefined`.
    This feeds the detector that pre-repair shape and asserts it is reported,
    then feeds it the repaired shape and asserts it is not. A guard that is
    silent on both is not a guard.
    """
    detector = _detects_bare_session_read

    broken = (
        "export function getSession(sessionId: string): Promise<LabSession> {\n"
        "  return apiRequest<LabSession>(`/api/lab/engineering/sessions/${sessionId}`);\n"
        "}\n"
    )
    assert detector(broken) is True, "the detector must flag the bare-session accessor"

    # The mutation that actually reintroduces the bug: the *view* accessor with
    # the wrong return type. The first cut of this detector matched the name
    # `getSession` only, so it passed this exact mutation -- measured, the live
    # file stayed green with `Promise<LabSession>` planted on `getSessionView`.
    mistyped_view = (
        "export function getSessionView(sessionId: string): Promise<LabSession> {\n"
        "  return apiRequest<LabSession>(labSession(sessionId));\n"
        "}\n"
    )
    assert detector(mistyped_view) is True, (
        "the detector must flag the view accessor mistyped as a bare session"
    )

    # A bare-session return is legitimate when it reads the *collection*: POST
    # /sessions really does respond with a session, not a view.
    legitimate_create = (
        "export function createSession(): Promise<LabSession> {\n"
        "  return apiRequest<LabSession>(endpoints.labSessions, { method: \"POST\" });\n"
        "}\n"
    )
    assert detector(legitimate_create) is False, (
        "the detector must not flag the collection create, which returns a real bare session"
    )

    repaired = (
        "export function getSessionView(sessionId: string): Promise<LabSessionView> {\n"
        "  return apiRequest<LabSessionView>(labSession(sessionId));\n"
        "}\n"
    )
    assert detector(repaired) is False, "the detector must accept the unwrapping accessor"

    # And the live file must be in the accepted state.
    assert detector(_read(CONTRACT)) is False


def _detects_bare_session_read(source: str) -> bool:
    """True when a function reads the session *view* endpoint as a bare session.

    The defect is a shape, not a name: any function whose body reads
    `GET /sessions/{id}` (the wrapper) while declaring its return type as the
    bare `LabSession` will hand callers an object with no `.session`, so
    `view.state` is `undefined` — a silent wrong answer.

    Matching on the name `getSession` alone was the first cut's defect: it
    accepted the live file for the wrong reason and stayed silent when the
    wrong return type was planted on `getSessionView`, which is the mutation
    that actually reintroduces the bug. The detector now judges the shape.
    """
    for match in re.finditer(
        r"function\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*:\s*Promise<\s*([A-Za-z_$][\w$]*)\s*>",
        source,
    ):
        name, returned = match.group(1), match.group(2)
        if returned != "LabSession":
            continue
        # `createSession` legitimately returns a bare session: POST /sessions
        # really does respond with one. Only a *view* read is the defect.
        brace = source.find("{", match.end())
        if brace == -1:
            continue
        body = _function_body(source, brace)
        if body is None:
            continue
        reads_view = "labSession(" in body or re.search(r"sessions/\$\{", body) is not None
        if reads_view:
            return True
    return False


def _function_body(source: str, brace_at: int) -> str | None:
    """The brace-balanced body starting at *brace_at*, or ``None``."""
    depth = 0
    for i in range(brace_at, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[brace_at : i + 1]
    return None


# -- resume across a reload ---------------------------------------------------


def test_resume_never_reconstructs_an_authorization():
    """A resumed session must not fabricate an authorization record.

    Measured against the running backend: no served route reads an
    authorization back. `GET /sessions/{id}/authorize` is `405`, there is no
    `/authorizations` collection (`404`), and the session view carries only
    `authorization_ref` — not the record. The original `originated_by`,
    `operations_allowed`, and duration are therefore unknowable client-side.

    A surface that rebuilt an `LabAuthorization` from the stored id would be
    asserting `originated_by: "human"` on evidence it does not have — inventing
    the very claim the substrate exists to keep. Resume must read the session
    and its state from the server and leave the authorization absent.
    """
    workspace = _read(WORKSPACE)
    contract = _read(CONTRACT)

    # The resume handler must not set an authorization.
    body = _resume_handler_body(workspace)
    assert body is not None, "the resume handler must exist"
    assert "setAuthorization" not in body, (
        "resume must not reconstruct an authorization; no route can read one back"
    )
    assert "setSession" in body and "getSessionView" in body, (
        "resume must re-read the session from the server"
    )

    # And the client must not offer an authorization accessor at all.
    assert "getAuthorization" not in contract, (
        "there is no served authorization read; a client accessor would be a fabrication"
    )
    # The session view is the only source of authorization *identity*.
    assert "authorization_ref" in contract


def test_resume_does_not_treat_a_stored_id_as_authority():
    """A stored id is a hint. It must be confirmed by a real read.

    The id lives in localStorage, which any script on the origin can write. If
    the surface adopted it without a read, a forged id would present as a live
    mission. The mount effect must confirm it and discard it on failure.
    """
    workspace = _read(WORKSPACE)
    effect = _resume_effect_body(workspace)
    assert effect is not None, "the mount effect must exist"
    assert "getSessionView" in effect, "the retained id must be confirmed by a real read"
    assert "forgetMissionSession" in effect, (
        "an unconfirmable id must be discarded, not left to offer a mission that is not there"
    )
    # The offer is held separately from the live session.
    assert "resumable" in workspace
    assert re.search(r"setResumable\(view\.session\.session_id\)", workspace), (
        "the offer must be set from the server's own session, not from storage"
    )


def test_authorized_state_is_read_from_the_substrate_not_local_state():
    """The gates must ask the substrate whether an authorization exists.

    Measured defect in this slice's own first cut: `canAttempt`/`canAuthorize`
    were keyed off the local `authorization` object. A resumed session carries
    `authorization_ref` while that object is empty, so step 3 would have
    *succeeded* and the surface would have reported "BOUNDARY NOT ENFORCED" —
    a false alarm about a gate that held, which is worse than a missed check
    because it destroys the operator's trust in the one signal that matters.
    """
    workspace = _read(WORKSPACE)
    assert "sessionAuthorized" in workspace
    assert "session?.authorization_ref" in workspace, (
        "the authorization test must consult the server-reported reference"
    )
    assert re.search(r"const canAttempt = Boolean\(session\) && !sessionAuthorized", workspace)
    assert re.search(r"const canAuthorize = Boolean\(session\) && !sessionAuthorized", workspace)
    assert re.search(r"const canExecute = Boolean\(session\) && sessionAuthorized", workspace)
    # The bare-object form must be gone.
    assert not re.search(r"const canExecute = Boolean\(session && authorization\)", workspace), (
        "gating on the local object reintroduces the false BOUNDARY NOT ENFORCED alarm"
    )


def test_resume_is_scoped_per_operator():
    """One operator's stored session id must not be offered to another."""
    contract = _read(CONTRACT)
    assert "resumeKey(uid)" in contract or "`${RESUME_KEY}:${uid}`" in contract, (
        "the stored id must be namespaced by uid"
    )
    workspace = _read(WORKSPACE)
    assert "uid" in workspace
    assert "recallMissionSession(uid)" in workspace
    assert "rememberMissionSession(uid" in workspace


def test_negative_control_resume_detector_flags_a_reconstructed_authorization():
    """Negative control: the detector must bite on the defect it claims to.

    The defect is a resume handler that sets an authorization object it cannot
    have read. Fed that shape the detector must report it; fed the repaired
    shape it must not. A guard silent on both is not a guard.
    """
    broken = (
        "const onResume = useCallback(async () => {\n"
        "  const view = await getSessionView(resumable);\n"
        "  setSession(view.session);\n"
        "  setAuthorization({ authorization_id: view.session.authorization_ref,\n"
        "    originated_by: 'human', operations_allowed: ['read'], duration_minutes: 60 });\n"
        "}, [resumable]);\n"
    )
    assert _resume_reconstructs_authorization(broken) is True, (
        "the detector must flag a reconstructed authorization"
    )

    repaired = (
        "const onResume = useCallback(async () => {\n"
        "  const view = await getSessionView(resumable);\n"
        "  setSession(view.session);\n"
        "  setBackendEvents(view.events ?? []);\n"
        "}, [resumable]);\n"
    )
    assert _resume_reconstructs_authorization(repaired) is False, (
        "the detector must accept a resume that only re-reads"
    )

    # And the live file must be in the accepted state.
    assert _resume_reconstructs_authorization(_read(WORKSPACE)) is False


def _resume_handler_body(source: str) -> str | None:
    """The body of the `onResume` callback, or ``None``."""
    match = re.search(r"const onResume = useCallback\(", source)
    if match is None:
        return None
    brace = source.find("{", match.end())
    if brace == -1:
        return None
    return _function_body(source, brace)


def _resume_effect_body(source: str) -> str | None:
    """The body of the mount effect that confirms a retained session."""
    match = re.search(r"useEffect\(\(\) => \{", source)
    if match is None:
        return None
    brace = source.find("{", match.end() - 1)
    if brace == -1:
        return None
    return _function_body(source, brace)


def _resume_reconstructs_authorization(source: str) -> bool:
    """True when a resume handler sets an authorization it cannot have read.

    The defect is a *shape*: a resume path that writes an authorization object
    while no served route returns one. Matching the handler name alone would
    pass any rename; this judges what the handler does.
    """
    body = _resume_handler_body(source)
    if body is None:
        return False
    return re.search(r"setAuthorization\s*\(", body) is not None
