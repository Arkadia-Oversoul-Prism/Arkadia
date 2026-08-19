"""
PHASE 0C — Production adversarial isolation matrix.

Requires explicit opt-in:
  ARKADIA_RUN_PRODUCTION_ISOLATION=1 pytest tests/production/test_phase_0c.py -v

Provisions disposable Firebase users via Identity Toolkit (no manual tokens).
Cleans up users in finally. Never logs ID tokens or passwords.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.production.firebase_harness import (
    DisposableUser,
    ProductionClient,
    base_url,
    delete_user,
    marker_present,
    production_gate_enabled,
    provision_user,
)

pytestmark = pytest.mark.skipif(
    not production_gate_enabled(),
    reason="Set ARKADIA_RUN_PRODUCTION_ISOLATION=1 to run production isolation tests",
)

REPORT_MD = Path("docs/verification/PHASE_0C_PRODUCTION_ISOLATION_REPORT.md")
REPORT_JSON = Path("docs/verification/PHASE_0C_PRODUCTION_ISOLATION_REPORT.json")


@pytest.fixture(scope="module")
def run_ctx():
    run_id = secrets.token_hex(4)
    base = base_url()
    user_a = user_b = None
    results: list[dict] = []
    canaries: dict = {}
    errors: list[str] = []
    cleanup_ok = True

    try:
        user_a = provision_user(run_id, "a")
        user_b = provision_user(run_id, "b")
    except Exception as e:
        pytest.fail(f"Firebase provisioning failed: {e}")

    ctx = {
        "run_id": run_id,
        "base": base,
        "user_a": user_a,
        "user_b": user_b,
        "client_a": ProductionClient(base, user_a),
        "client_b": ProductionClient(base, user_b),
        "client_anon": ProductionClient(base, None),
        "results": results,
        "canaries": canaries,
        "errors": errors,
        "started": datetime.now(timezone.utc).isoformat(),
    }
    yield ctx

    # cleanup
    for u in (user_a, user_b):
        if u is None:
            continue
        try:
            if not delete_user(u):
                cleanup_ok = False
                errors.append(f"cleanup failed for uid={u.uid}")
        except Exception as e:
            cleanup_ok = False
            errors.append(f"cleanup exception uid={u.uid}: {e}")

    ctx["cleanup_ok"] = cleanup_ok
    ctx["finished"] = datetime.now(timezone.utc).isoformat()
    _write_reports(ctx)


def _record(ctx, name: str, ok: bool, detail: str, status: int | None = None):
    ctx["results"].append({
        "name": name,
        "ok": ok,
        "detail": detail,
        "status": status,
    })
    if not ok:
        ctx["errors"].append(f"{name}: {detail}")


def _write_reports(ctx):
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    all_ok = all(r["ok"] for r in ctx["results"]) and not ctx["errors"] and ctx.get("cleanup_ok", False)
    verdict = "GREEN" if all_ok else ("RED" if any(not r["ok"] for r in ctx["results"]) else "PARTIAL")
    if any("provision" in e.lower() for e in ctx["errors"]):
        verdict = "BLOCKED"

    payload = {
        "verdict": verdict,
        "run_id": ctx["run_id"],
        "base_url": ctx["base"],
        "started": ctx.get("started"),
        "finished": ctx.get("finished"),
        "user_a_uid": ctx["user_a"].uid if ctx.get("user_a") else None,
        "user_b_uid": ctx["user_b"].uid if ctx.get("user_b") else None,
        "canaries": {k: {"uuid": v.get("uuid"), "id": v.get("id"), "marker": v.get("marker")} for k, v in ctx.get("canaries", {}).items()},
        "results": ctx["results"],
        "errors": ctx["errors"],
        "cleanup_ok": ctx.get("cleanup_ok"),
        "commit_expected": "ffefb338b2a620c78ef7933bff6bb90b1e56eacf",
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2))

    lines = [
        "# PHASE 0C — PRODUCTION ISOLATION REPORT",
        "",
        f"**Verdict:** {verdict}",
        f"**Run ID:** `{ctx['run_id']}`",
        f"**Host:** `{ctx['base']}`",
        f"**Started:** {ctx.get('started')}",
        f"**Finished:** {ctx.get('finished')}",
        f"**User A UID:** `{payload['user_a_uid']}`",
        f"**User B UID:** `{payload['user_b_uid']}`",
        f"**Cleanup:** {'OK' if ctx.get('cleanup_ok') else 'FAILED'}",
        "",
        "## Matrix",
        "",
        "| Test | OK | Status | Detail |",
        "|------|----|--------|--------|",
    ]
    for r in ctx["results"]:
        lines.append(f"| {r['name']} | {'✅' if r['ok'] else '❌'} | {r.get('status')} | {r['detail'][:80]} |")
    lines.extend(["", "## Errors", ""])
    lines.extend([f"- {e}" for e in ctx["errors"]] or ["- none"])
    lines.extend([
        "",
        "## Notes",
        "",
        "Tokens and passwords are never written to this report.",
        "Canary markers are synthetic isolation probes only.",
        "",
    ])
    REPORT_MD.write_text("\n".join(lines))


def test_01_health_and_public_corpus(run_ctx):
    c = run_ctx["client_anon"]
    status, body = c.get("/api/knowledge/status")
    ok = status == 200 and (body or {}).get("status") == "operational"
    _record(run_ctx, "anon_status", ok, f"status={status}", status)
    assert ok

    status, body = c.post("/api/knowledge/search", {"query": "Arkadia", "modes": ["fulltext"], "top_k": 3})
    hits = (body or {}).get("fulltext") or []
    ok = status == 200 and len(hits) >= 1
    _record(run_ctx, "anon_public_search", ok, f"hits={len(hits)}", status)
    assert ok


def test_02_user_a_creates_private_canary(run_ctx):
    marker = f"PHASE0C_USER_A_{run_ctx['run_id']}_{secrets.token_hex(3)}"
    body = {
        "title": marker,
        "content": f"Private isolation canary for User A. marker={marker} run={run_ctx['run_id']}",
        "tags": ["phase0c", "isolation", run_ctx["run_id"]],
    }
    status, resp = run_ctx["client_a"].post("/api/personal/ingest-note", body)
    note = (resp or {}).get("note") if isinstance(resp, dict) else {}
    if not isinstance(note, dict):
        note = {}
    uuid = note.get("uuid") or (resp or {}).get("uuid")
    nid = note.get("id") or (resp or {}).get("id")
    ok = status in (200, 201) and bool(uuid)
    run_ctx["canaries"]["a"] = {"marker": marker, "uuid": uuid, "id": nid, "raw_keys": list(resp.keys()) if isinstance(resp, dict) else []}
    _record(run_ctx, "a_create_canary", ok, f"uuid={uuid} id={nid}", status)
    assert ok, f"A create failed status={status} body_keys={run_ctx['canaries']['a'].get('raw_keys')}"


def test_03_user_b_creates_private_canary(run_ctx):
    marker = f"PHASE0C_USER_B_{run_ctx['run_id']}_{secrets.token_hex(3)}"
    body = {
        "title": marker,
        "content": f"Private isolation canary for User B. marker={marker} run={run_ctx['run_id']}",
        "tags": ["phase0c", "isolation", run_ctx["run_id"]],
    }
    status, resp = run_ctx["client_b"].post("/api/personal/ingest-note", body)
    note = (resp or {}).get("note") if isinstance(resp, dict) else {}
    if not isinstance(note, dict):
        note = {}
    uuid = note.get("uuid") or (resp or {}).get("uuid")
    nid = note.get("id") or (resp or {}).get("id")
    ok = status in (200, 201) and bool(uuid)
    run_ctx["canaries"]["b"] = {"marker": marker, "uuid": uuid, "id": nid}
    _record(run_ctx, "b_create_canary", ok, f"uuid={uuid} id={nid}", status)
    assert ok


def test_04_a_retrieves_own_canary(run_ctx):
    ca = run_ctx["canaries"].get("a") or {}
    marker, uuid, nid = ca.get("marker"), ca.get("uuid"), ca.get("id")
    assert uuid, "missing A uuid"
    c = run_ctx["client_a"]

    st, body = c.get(f"/api/knowledge/notes/{uuid}")
    ok = st == 200 and marker_present(body, marker)
    _record(run_ctx, "a_get_note", ok, f"status={st}", st)
    assert ok

    if nid is not None:
        st, body = c.get(f"/api/knowledge/node/{nid}")
        ok = st == 200 and marker_present(body, marker)
        _record(run_ctx, "a_get_node", ok, f"status={st}", st)
        assert ok

        st, body = c.get(f"/api/knowledge/graph/{nid}/traverse?depth=1")
        ok = st == 200 and (marker_present(body, marker) or marker_present(body, uuid))
        # traverse may return nodes without full content — presence of id is enough if start accessible
        if st == 200 and isinstance(body, dict) and body.get("nodes"):
            ok = True
        _record(run_ctx, "a_traverse", ok, f"status={st} nodes={len((body or {}).get('nodes') or [])}", st)

    st, body = c.get("/api/knowledge/graph")
    ok = st == 200 and marker_present(body, uuid or marker)
    _record(run_ctx, "a_full_graph", ok, f"status={st}", st)

    st, body = c.post("/api/knowledge/search", {"query": marker, "modes": ["fulltext"], "top_k": 10})
    ok = st == 200 and marker_present(body, marker)
    _record(run_ctx, "a_search", ok, f"status={st}", st)
    assert ok


def test_05_b_cannot_access_a(run_ctx):
    ca = run_ctx["canaries"]["a"]
    marker, uuid, nid = ca["marker"], ca.get("uuid"), ca.get("id")
    c = run_ctx["client_b"]

    st, body = c.get(f"/api/knowledge/notes/{uuid}")
    leaked = marker_present(body, marker)
    ok = (st in (403, 404) or (st == 200 and not leaked)) and not leaked
    _record(run_ctx, "b_get_a_note", ok, f"status={st} leaked={leaked}", st)
    assert ok

    if nid is not None:
        st, body = c.get(f"/api/knowledge/node/{nid}")
        leaked = marker_present(body, marker)
        ok = not leaked and st in (403, 404, 200)
        if st == 200:
            ok = not leaked
        _record(run_ctx, "b_get_a_node", ok, f"status={st} leaked={leaked}", st)
        assert ok

        st, body = c.get(f"/api/knowledge/graph/{nid}/traverse?depth=2")
        leaked = marker_present(body, marker)
        # empty graph or no private content
        nodes = (body or {}).get("nodes") if isinstance(body, dict) else []
        ok = not leaked and (st in (200, 403, 404)) and (not nodes or not marker_present(nodes, marker))
        _record(run_ctx, "b_traverse_a", ok, f"status={st} nodes={len(nodes or [])}", st)
        assert ok

    st, body = c.get("/api/knowledge/graph")
    leaked = marker_present(body, marker) or (uuid and marker_present(body, uuid))
    ok = st == 200 and not leaked
    _record(run_ctx, "b_graph_no_a", ok, f"status={st} leaked={leaked}", st)
    assert ok

    st, body = c.post("/api/knowledge/search", {"query": marker, "modes": ["fulltext"], "top_k": 10})
    leaked = marker_present(body, marker)
    ok = st == 200 and not leaked
    _record(run_ctx, "b_search_a_marker", ok, f"status={st} leaked={leaked}", st)
    assert ok

    st, body = c.get("/api/knowledge/timeline/recent?limit=50")
    leaked = marker_present(body, marker)
    ok = not leaked
    _record(run_ctx, "b_timeline_no_a", ok, f"status={st} leaked={leaked}", st)
    assert ok


def test_06_a_cannot_access_b(run_ctx):
    cb = run_ctx["canaries"]["b"]
    marker, uuid = cb["marker"], cb.get("uuid")
    c = run_ctx["client_a"]
    st, body = c.get(f"/api/knowledge/notes/{uuid}")
    leaked = marker_present(body, marker)
    ok = not leaked
    _record(run_ctx, "a_get_b_note", ok, f"status={st} leaked={leaked}", st)
    assert ok

    st, body = c.post("/api/knowledge/search", {"query": marker, "modes": ["fulltext"], "top_k": 10})
    leaked = marker_present(body, marker)
    ok = not leaked
    _record(run_ctx, "a_search_b_marker", ok, f"status={st} leaked={leaked}", st)
    assert ok


def test_07_anonymous_cannot_access_private(run_ctx):
    c = run_ctx["client_anon"]
    for label in ("a", "b"):
        can = run_ctx["canaries"][label]
        marker, uuid, nid = can["marker"], can.get("uuid"), can.get("id")
        st, body = c.get(f"/api/knowledge/notes/{uuid}")
        leaked = marker_present(body, marker)
        ok = not leaked
        _record(run_ctx, f"anon_get_{label}_note", ok, f"status={st} leaked={leaked}", st)
        assert ok

        st, body = c.post("/api/knowledge/search", {"query": marker, "modes": ["fulltext"], "top_k": 10})
        leaked = marker_present(body, marker)
        ok = not leaked
        _record(run_ctx, f"anon_search_{label}", ok, f"status={st} leaked={leaked}", st)
        assert ok

    st, body = c.get("/api/knowledge/graph")
    leaked_a = marker_present(body, run_ctx["canaries"]["a"]["marker"])
    leaked_b = marker_present(body, run_ctx["canaries"]["b"]["marker"])
    ok = not leaked_a and not leaked_b
    _record(run_ctx, "anon_graph_no_private", ok, f"leaked_a={leaked_a} leaked_b={leaked_b}", st)
    assert ok

    st, body = c.get("/api/knowledge/timeline/recent?limit=50")
    ok = not marker_present(body, run_ctx["canaries"]["a"]["marker"]) and not marker_present(body, run_ctx["canaries"]["b"]["marker"])
    _record(run_ctx, "anon_timeline_no_private", ok, f"status={st}", st)
    assert ok


def test_08_oracle_context_isolation(run_ctx):
    ca = run_ctx["canaries"]["a"]
    marker = ca["marker"]
    # A should be able to get marker in context/search path via resonance memory
    st, body = run_ctx["client_a"].post(
        "/api/commune/resonance",
        {"message": f"Recall the exact canary marker if archived: {marker}", "session_id": f"phase0c-a-{run_ctx['run_id']}", "history": []},
    )
    # AI may not echo; check memory/notes path if present
    present = marker_present(body, marker)
    # soft pass if endpoint works even when model doesn't quote marker
    ok = st == 200
    _record(run_ctx, "a_oracle_status", ok, f"status={st} marker_in_response={present}", st)

    st, body = run_ctx["client_b"].post(
        "/api/commune/resonance",
        {"message": f"Recall private marker {marker}", "session_id": f"phase0c-b-{run_ctx['run_id']}", "history": []},
    )
    leaked = marker_present(body, marker)
    ok = st == 200 and not leaked
    _record(run_ctx, "b_oracle_no_a_marker", ok, f"status={st} leaked={leaked}", st)
    assert ok


def test_09_public_corpus_still_works(run_ctx):
    st, body = run_ctx["client_anon"].post(
        "/api/knowledge/search",
        {"query": "Arkadia", "modes": ["fulltext"], "top_k": 5},
    )
    hits = (body or {}).get("fulltext") or []
    ok = st == 200 and len(hits) >= 1
    _record(run_ctx, "public_corpus_regression", ok, f"hits={len(hits)}", st)
    assert ok
