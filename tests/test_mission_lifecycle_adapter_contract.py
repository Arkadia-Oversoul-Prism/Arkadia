"""Mission lifecycle adapter — the inspector's stage state is driven by the real
governed chain, not by a hardcoded strip.

The product owner's requirement: the seven-stage lifecycle
(Understand → Propose → Authorize → Execute → Verify → Accept → Release) must be
driven by live backend state, and the display must never overstate — proposed vs
authorized, running vs completed, completed vs independently verified, verified
vs human-accepted, accepted vs released must remain visibly distinct, and a stage
with no evidence must render as unknown rather than as complete.

The adapter under test is ``web/arkadia_console/src/lib/missionLifecycle.ts``.
Its ``projectLifecycle`` is a pure function over the canonical chain shape served
by ``GET /solspire/voice/events/{id}/chain`` (``solspire/voice_contracts.py``
``ChainStage`` / ``solspire/voice_pipeline.py`` ``chain()``). Because it is pure
and dependency-free, it is *executed* in Node against real payloads rather than
pinned by source text — a source pin could only restate the implementation.

The adapter is transpiled with the repository's own TypeScript compiler (the
same one ``tsc --noEmit`` uses), so the executed code is the real module, not a
hand-stripped approximation.

The payloads below are the exact stage/record shapes the backend emits (verified
against ``scripts/voice_smoke.py``, which runs the full chain green). This is
unauthenticated-session evidence: it proves the adapter maps real backend state
correctly, not that a signed-in browser session was exercised.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
ADAPTER_PATH = SRC / "lib" / "missionLifecycle.ts"
TSC = ROOT / "web" / "arkadia_console" / "node_modules" / "typescript" / "lib" / "typescript.js"

ADAPTER = ADAPTER_PATH.read_text(encoding="utf-8")


def _transpile(ts_source: str) -> str:
    """Transpile the real adapter with the repo's TypeScript compiler."""
    node = shutil.which("node")
    assert node, "node is required to evaluate the mission lifecycle adapter"
    assert TSC.exists(), f"the repository TypeScript compiler is missing at {TSC}"

    script = (
        f"const ts = require({json.dumps(str(TSC))});\n"
        f"const src = {json.dumps(ts_source)};\n"
        "const out = ts.transpileModule(src, {\n"
        "  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },\n"
        "});\n"
        "process.stdout.write(out.outputText);\n"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"transpile failed: {result.stderr.strip()}"
    return result.stdout


def _run_adapter(payload: dict) -> list[dict]:
    """Execute the real adapter's projectLifecycle over one chain payload."""
    node = shutil.which("node")
    assert node, "node is required to evaluate the mission lifecycle adapter"

    emitted = _transpile(ADAPTER)

    # The adapter's async readers import the API client and the endpoint
    # registry. `projectLifecycle` is pure and touches neither, so the harness
    # supplies inert stubs and asserts the adapter requires nothing else — a new
    # runtime dependency would fail here rather than silently execute something
    # other than the real module.
    script = (
        "const __stubs = {\n"
        '  "./apiClient": { apiRequest: async () => { throw new Error("network is not used by projectLifecycle"); } },\n'
        '  "./endpoints": { endpoints: {}, voiceEvent: (id) => id, voiceEventChain: (id) => id },\n'
        "};\n"
        "const __seen = [];\n"
        "const __require = (m) => {\n"
        "  __seen.push(m);\n"
        "  if (__stubs[m]) return __stubs[m];\n"
        '  throw new Error("unexpected runtime import: " + m);\n'
        "};\n"
        "const __mod = { exports: {} };\n"
        "(function (require, exports, module) {\n"
        + emitted
        + "\n})(__require, __mod.exports, __mod);\n"
        + f"const read = {json.dumps(payload)};\n"
        + "console.log(JSON.stringify(__mod.exports.projectLifecycle(read)));\n"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"adapter evaluation failed: {result.stderr.strip()}"
    return json.loads(result.stdout)


def _stage(seq: int, stage: str, record_id: str, payload: dict | None = None) -> dict:
    return {
        "stage": stage,
        "seq": seq,
        "record_type": stage.title(),
        "record_id": record_id,
        "payload": payload or {},
        "created_at": 1_700_000_000 + seq,
        "prev_record_id": None if seq == 0 else f"rec-{seq - 1}",
        "payload_digest": f"digest-{seq}",
    }


def _by_stage(lifecycle: list[dict]) -> dict[str, dict]:
    return {entry["stage"]: entry for entry in lifecycle}


# ---------------------------------------------------------------------------
# The seven stages are always present, in order.
# ---------------------------------------------------------------------------

def test_the_seven_stages_are_always_present_in_order():
    lifecycle = _run_adapter({"state": "empty"})
    assert [entry["stage"] for entry in lifecycle] == [
        "understand",
        "propose",
        "authorize",
        "execute",
        "verify",
        "accept",
        "release",
    ]


# ---------------------------------------------------------------------------
# No chain recorded: every stage is unknown, never complete.
# ---------------------------------------------------------------------------

def test_no_recorded_chain_renders_every_stage_unknown_not_complete():
    lifecycle = _by_stage(_run_adapter({"state": "empty"}))
    for stage in ("understand", "propose", "authorize", "execute", "verify"):
        assert lifecycle[stage]["state"] == "unknown", stage
    # Accept and Release are unavailable by construction — no backend record
    # exists for either, so they can never read as complete.
    assert lifecycle["accept"]["state"] == "unavailable"
    assert lifecycle["release"]["state"] == "unavailable"


# ---------------------------------------------------------------------------
# A real recorded chain drives the stages that exist.
# ---------------------------------------------------------------------------

def test_a_recorded_chain_marks_reached_stages_done():
    payload = {
        "state": "ready",
        "chain": {
            "event_id": "VE-abc",
            "chain_digest": "deadbeefcafe",
            "stages": [
                _stage(0, "VOICE_EVENT", "rec-0"),
                _stage(1, "TRANSCRIPT", "rec-1"),
                _stage(2, "INTENT", "rec-2"),
                _stage(3, "CONTEXT", "rec-3"),
                _stage(4, "AUTHORITY", "rec-4"),
                _stage(5, "PROPOSAL", "rec-5", {"proposal_status": "PRESENTED"}),
            ],
        },
    }
    lifecycle = _by_stage(_run_adapter(payload))
    assert lifecycle["understand"]["state"] == "done"
    assert lifecycle["propose"]["state"] == "done"
    # The chain is in progress but authorization has not been recorded.
    assert lifecycle["authorize"]["state"] == "pending"
    assert lifecycle["execute"]["state"] == "pending"
    assert lifecycle["verify"]["state"] == "pending"


# ---------------------------------------------------------------------------
# proposed ≠ authorized: an ACCEPTED proposal without a grant is NOT authorized.
# ---------------------------------------------------------------------------

def test_accepted_proposal_without_grant_is_not_authorized():
    payload = {
        "state": "ready",
        "chain": {
            "event_id": "VE-abc",
            "chain_digest": "deadbeefcafe",
            "stages": [
                _stage(0, "VOICE_EVENT", "rec-0"),
                _stage(5, "PROPOSAL", "rec-5", {"proposal_status": "PRESENTED"}),
                _stage(6, "APPROVAL", "rec-6", {"proposal_status": "ACCEPTED"}),
            ],
        },
    }
    lifecycle = _by_stage(_run_adapter(payload))
    assert lifecycle["authorize"]["state"] == "pending", (
        "an accepted proposal is a human decision, not an authorization grant"
    )
    assert "no authorization grant" in lifecycle["authorize"]["evidence"].lower()


def test_a_recorded_authorization_marks_authorize_done():
    payload = {
        "state": "ready",
        "chain": {
            "event_id": "VE-abc",
            "chain_digest": "deadbeefcafe",
            "stages": [
                _stage(0, "VOICE_EVENT", "rec-0"),
                _stage(6, "APPROVAL", "rec-6", {"proposal_status": "ACCEPTED"}),
                _stage(7, "AUTHORIZATION", "rec-7", {"authorization_id": "AUTH-1"}),
            ],
        },
    }
    lifecycle = _by_stage(_run_adapter(payload))
    assert lifecycle["authorize"]["state"] == "done"


# ---------------------------------------------------------------------------
# completed ≠ verified: execution done does not make verification done.
# ---------------------------------------------------------------------------

def test_execution_done_does_not_mark_verification_done():
    payload = {
        "state": "ready",
        "chain": {
            "event_id": "VE-abc",
            "chain_digest": "deadbeefcafe",
            "stages": [
                _stage(0, "VOICE_EVENT", "rec-0"),
                _stage(7, "AUTHORIZATION", "rec-7", {"authorization_id": "AUTH-1"}),
                _stage(8, "EXECUTION", "rec-8", {"status": "completed"}),
                _stage(9, "RESULT", "rec-9"),
                _stage(10, "WORK_EVENT", "rec-10"),
                _stage(11, "EVIDENCE", "rec-11"),
            ],
        },
    }
    lifecycle = _by_stage(_run_adapter(payload))
    assert lifecycle["execute"]["state"] == "done"
    assert lifecycle["verify"]["state"] == "pending", (
        "execution is not verification — a successful executor response is not "
        "verified real-world completion"
    )


def test_a_verification_verdict_marks_verify_done():
    payload = {
        "state": "ready",
        "chain": {
            "event_id": "VE-abc",
            "chain_digest": "deadbeefcafe",
            "stages": [
                _stage(0, "VOICE_EVENT", "rec-0"),
                _stage(8, "EXECUTION", "rec-8", {"status": "completed"}),
                _stage(12, "VERIFICATION", "rec-12", {"verification": {"verdict": "VERIFIED"}}),
            ],
        },
    }
    lifecycle = _by_stage(_run_adapter(payload))
    assert lifecycle["verify"]["state"] == "done"
    assert "VERIFIED" in lifecycle["verify"]["evidence"]


# ---------------------------------------------------------------------------
# verified ≠ accepted, accepted ≠ released: the last two stages have no record.
# ---------------------------------------------------------------------------

def test_accept_and_release_are_unavailable_even_after_verification():
    payload = {
        "state": "ready",
        "chain": {
            "event_id": "VE-abc",
            "chain_digest": "deadbeefcafe",
            "stages": [
                _stage(0, "VOICE_EVENT", "rec-0"),
                _stage(12, "VERIFICATION", "rec-12", {"verification": {"verdict": "VERIFIED"}}),
            ],
        },
    }
    lifecycle = _by_stage(_run_adapter(payload))
    assert lifecycle["accept"]["state"] == "unavailable"
    assert lifecycle["release"]["state"] == "unavailable"
    assert "never self-sets COMPLETED" in lifecycle["accept"]["evidence"]
    assert "RELEASE" in lifecycle["release"]["evidence"]


# ---------------------------------------------------------------------------
# An unreachable contract renders unavailable, never complete.
# ---------------------------------------------------------------------------

def test_an_unreachable_contract_renders_unavailable_not_complete():
    lifecycle = _by_stage(
        _run_adapter({"state": "unavailable", "error": "401 AUTH_REQUIRED"})
    )
    for stage in ("understand", "propose", "authorize", "execute", "verify"):
        assert lifecycle[stage]["state"] == "unavailable", stage
    assert "401 AUTH_REQUIRED" in lifecycle["understand"]["evidence"]


# ---------------------------------------------------------------------------
# Negative control: the adapter is not a constant strip.
# ---------------------------------------------------------------------------

def test_negative_control_the_adapter_is_not_a_constant_strip():
    empty = _by_stage(_run_adapter({"state": "empty"}))
    full = _by_stage(
        _run_adapter(
            {
                "state": "ready",
                "chain": {
                    "event_id": "VE-abc",
                    "chain_digest": "deadbeefcafe",
                    "stages": [
                        _stage(0, "VOICE_EVENT", "rec-0"),
                        _stage(5, "PROPOSAL", "rec-5", {"proposal_status": "PRESENTED"}),
                        _stage(7, "AUTHORIZATION", "rec-7", {"authorization_id": "AUTH-1"}),
                        _stage(8, "EXECUTION", "rec-8", {"status": "completed"}),
                        _stage(12, "VERIFICATION", "rec-12", {"verification": {"verdict": "VERIFIED"}}),
                    ],
                },
            }
        )
    )
    assert empty["understand"]["state"] != full["understand"]["state"]
    assert empty["execute"]["state"] != full["execute"]["state"]
