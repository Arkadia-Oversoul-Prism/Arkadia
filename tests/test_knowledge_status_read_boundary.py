"""Lane 3 — Knowledge OS status reader: a 200 can carry a failed read.

Binds the *declared* ``GET /api/knowledge/status`` contract to its real handler,
then binds the feature-local reader to that contract.

Contract under test (read from the handler, not invented):

  * ``GET /api/knowledge/status`` -> ``api.knowledge_routes.knowledge_os_status``
  * the success body carries ``status: "operational"`` plus the ``vault``,
    ``graph`` and ``timeline`` blocks
  * the handler's ``except`` branch **returns** rather than raises:
    ``{"status": "error", "detail": str(e)}`` — with HTTP **200**, and with no
    ``vault``/``graph``/``timeline`` block at all

That last point is the whole boundary. The transport cannot carry the
distinction: a failed read and a healthy read are both ``200``. A reader that
trusts the status code therefore dereferences ``vault.notes`` on the failure
envelope — the vault status panel crashes, and a dead vault is indistinguishable
from an unread one.

The reader under test is ``web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts``,
executed through Node (the module is TypeScript, and the repository's convention
for frontend contracts is to *execute* them rather than string-match their
source — see ``tests/test_prism_opportunity_entry_flow.py``).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.knowledge_routes import router as knowledge_router

REPO_ROOT = Path(__file__).resolve().parents[1]
CONSOLE = REPO_ROOT / "web" / "arkadia_console"
CONTRACT_TS = CONSOLE / "src" / "pages" / "knowledge" / "knowledgeContracts.ts"

# The handler's own failure envelope, measured live (see the module docstring).
ERROR_BODY = {"status": "error", "detail": "simulated vault failure"}


def _healthy_app() -> FastAPI:
    application = FastAPI()
    application.include_router(knowledge_router)
    return application


def _healthy_body() -> dict:
    """The handler's own success body — read from the handler, never restated."""
    response = TestClient(_healthy_app()).get("/api/knowledge/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "operational", "the success path must be reachable for this guard to mean anything"
    return body


# ---------------------------------------------------------------------------
# Backend: the handler answers 200 for a failed read
# ---------------------------------------------------------------------------


@pytest.fixture()
def app(monkeypatch):
    """The knowledge router, with the vault read forced to raise.

    The failure is injected at the DB helper the handler actually calls, so the
    handler's own ``except`` branch runs — this measures the handler, not a
    restatement of it.
    """
    import knowledge.db as kdb

    def boom(*args, **kwargs):
        raise RuntimeError("simulated vault failure")

    monkeypatch.setattr(kdb, "execute_one", boom)
    application = FastAPI()
    application.include_router(knowledge_router)
    return application


def test_a_failed_read_is_served_with_http_200(app):
    """The defect's precondition: the transport does not carry the failure."""
    response = TestClient(app).get("/api/knowledge/status")
    assert response.status_code == 200, "the handler is expected to answer 200 on its error path"


def test_the_failure_envelope_omits_the_reading_blocks(app):
    """It is a *recognised* failure, not a zeroed reading — so it must not look like one."""
    body = TestClient(app).get("/api/knowledge/status").json()
    assert body["status"] == "error"
    assert "detail" in body
    for block in ("vault", "graph", "timeline"):
        assert block not in body, (
            f"the failure envelope must not carry `{block}`; if it does, the "
            "reader's distinction has moved and this guard needs re-deriving"
        )


def test_the_success_status_value_is_not_the_error_value():
    """The reader branches on `status`; the two values must not be conflated.

    Measured against the handler's own success path, so the success value is read
    from the handler rather than restated.
    """
    healthy = _healthy_body()
    assert healthy["status"] != ERROR_BODY["status"]
    for block in ("vault", "graph", "timeline"):
        assert block in healthy


# ---------------------------------------------------------------------------
# Frontend contract — executed through Node, not string-matched
# ---------------------------------------------------------------------------

_NODE_PROBE = r"""
const m = await import(process.argv[1]);
const healthy = JSON.parse(process.argv[2]);
const errorEnvelope = JSON.parse(process.argv[3]);
const out = {};

// The validator.
out.healthy_validates = m.isKnowledgeStatusReading(healthy);
out.error_envelope_validates = m.isKnowledgeStatusReading(errorEnvelope);
out.empty_object_validates = m.isKnowledgeStatusReading({});
out.null_body_validates = m.isKnowledgeStatusReading(null);
out.vault_missing_validates = m.isKnowledgeStatusReading({ status: "operational", graph: {}, timeline: {} });

// The reader the surface must use — it either yields a reading or throws.
out.reader_returns_healthy = m.requireKnowledgeStatusReading(healthy).vault.notes;
try {
  m.requireKnowledgeStatusReading(errorEnvelope);
  out.reader_error_envelope = "RETURNED (defect)";
} catch (err) {
  out.reader_error_envelope = err.message;
}
try {
  m.requireKnowledgeStatusReading({ status: "operational", graph: {}, timeline: {} });
  out.reader_vault_missing = "RETURNED (defect)";
} catch (err) {
  out.reader_vault_missing = err.message;
}

// A body-shape-blind reader — the defect this guard exists for — is reproduced
// here so the oracle is shown to be able to fail: it dereferences vault on the
// error envelope exactly as the pre-fix page did.
try {
  out.naive_reader_on_error_envelope = errorEnvelope.vault.notes;
} catch (err) {
  out.naive_reader_on_error_envelope = "threw: " + err.constructor.name;
}

console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def contract_probe() -> dict:
    """Execute the contract module through Node and return its measured behaviour.

    The healthy body is the handler's own success response, so the probe is bound
    to the live contract rather than to a hand-written shape.
    """
    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            _NODE_PROBE,
            str(CONTRACT_TS),
            json.dumps(_healthy_body()),
            json.dumps(ERROR_BODY),
        ],
        cwd=str(CONSOLE),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"the contract module could not be executed:\n{result.stderr}"
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_the_contract_module_is_executable(contract_probe):
    assert contract_probe, "the probe must return measurements"


def test_a_healthy_reading_validates(contract_probe):
    assert contract_probe["healthy_validates"] is True


def test_the_200_error_envelope_does_not_validate_as_a_reading(contract_probe):
    """The load-bearing assertion: a failed read must not be accepted as a reading."""
    assert contract_probe["error_envelope_validates"] is False, (
        "the handler's 200 `status: error` envelope was accepted as a status reading; "
        "a dead vault would render as a zeroed one"
    )


def test_a_body_missing_a_reading_block_does_not_validate(contract_probe):
    assert contract_probe["vault_missing_validates"] is False


def test_non_object_bodies_do_not_validate(contract_probe):
    assert contract_probe["empty_object_validates"] is False
    assert contract_probe["null_body_validates"] is False


def test_the_reader_returns_the_reading_on_a_healthy_body(contract_probe):
    """The reader is not a blanket refusal: it yields the real reading."""
    assert contract_probe["reader_returns_healthy"] == _healthy_body()["vault"]["notes"]


def test_the_reader_refuses_the_error_envelope_with_its_own_detail(contract_probe):
    """It throws, and it surfaces the handler's failure detail rather than a generic one."""
    assert contract_probe["reader_error_envelope"] == ERROR_BODY["detail"], (
        "the reader must refuse the failure envelope and carry the handler's own detail"
    )


def test_the_reader_refuses_a_body_missing_a_reading_block(contract_probe):
    assert "unrecognised" in contract_probe["reader_vault_missing"]


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------


def test_negative_control_the_naive_reader_dereferences_the_error_envelope(contract_probe):
    """Proves the oracle can bite: the pre-fix reader crashes on this very body.

    The pre-fix page read ``status.data.vault.notes`` after only a status-code
    check, which is what ``errorEnvelope.vault.notes`` reproduces. If this control
    ever stops throwing, the defect's shape has moved and the guard is stale.
    """
    assert contract_probe["naive_reader_on_error_envelope"] == "threw: TypeError", (
        "a body-shape-blind reader must crash on the failure envelope; "
        "the guard's oracle is otherwise unfalsifiable"
    )


def test_negative_control_the_status_surface_routes_through_the_shared_reader():
    """The page's fetch wrapper must call the validated reader, not read blindly.

    Asserted structurally rather than by an exact literal, so a cosmetic rewrite
    of the line cannot silently drop the guard: the seam is that ``readStatus``
    validates its payload through the shared contract reader before returning it.
    """
    page = (CONSOLE / "src" / "pages" / "KnowledgePage.tsx").read_text(encoding="utf-8")
    body = page[page.index("async function readStatus"): page.index("export function KnowledgePage")]
    assert "requireKnowledgeStatusReading(" in body, (
        "readStatus must validate the status body through the shared contract reader; "
        "without it the page dereferences the handler's failure envelope"
    )
    assert "apiRequest<KnowledgeStatus>" not in body, (
        "an unvalidated typed read is the defect this guard exists for"
    )


def test_negative_control_the_reader_is_not_a_blanket_refusal():
    """A reader that rejected everything would pass the defect assertion vacuously."""
    source = CONTRACT_TS.read_text(encoding="utf-8")
    assert "return payload;" in source, (
        "the reader must return a validated reading, or the guard could be satisfied "
        "by a reader that refuses all bodies"
    )
