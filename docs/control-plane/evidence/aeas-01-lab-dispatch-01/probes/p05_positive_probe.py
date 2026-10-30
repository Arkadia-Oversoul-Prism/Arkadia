"""P0.5 positive-path served probe: real HTTP adapter call -> tool -> DONE.

Runs against the local stub completion endpoint (artifacts/ollama_stub.py), which is
NOT a model. This proves the adapter contract, tool execution, event attribution and
terminal-state reporting work end to end. It does not make any provider available and
is not evidence for a LIVE worker.
"""
import base64
import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8126/api/lab/engineering"  # uvicorn with OLLAMA_BASE_URL set


def b64(d):
    return base64.urlsafe_b64encode(json.dumps(d, separators=(",", ":")).encode()).decode().rstrip("=")


TOKEN = f"{b64({'alg': 'none', 'typ': 'JWT'})}." \
        f"{b64({'sub': 'p05-operator', 'email': 'p05@example.test', 'exp': int(time.time()) + 600})}." \
        f"local-dev"


def call(method, path, body=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, {"raw": raw[:400]}
    except Exception as exc:
        return -1, {"error": str(exc)}


print("=== A. availability with a configured local endpoint ===")
_, gw = call("GET", "/gateway")
for p in gw.get("catalog", []):
    if p["provider"] in ("ollama", "n_atlas", "openai_compatible"):
        print(f"  {p['provider']:<18} status={p['status']:<14} adapter_bound={p['adapter_bound']}"
              f" dispatchable={p['dispatchable']} detail={p.get('detail')}")

print("\n=== B. fresh authorized session ===")
_, ag = call("POST", "/agents", {"role": "BUILDER", "display_name": "P05 positive-path probe"})
aid = ag.get("agent_id") or ag.get("id")
_, s = call("POST", "/sessions", {
    "workspace_ref": "/workspace/chats/f6a4fd1dd162a73f0b053afb",
    "agent_id": aid,
    "objective": "List the workspace and report what is present",
})
sid = s.get("session_id") or s.get("id")
_, a = call("POST", f"/sessions/{sid}/authorize",
            {"operations_allowed": ["read", "test"], "duration_minutes": 60})
print(f"  session={sid} state={(a.get('session') or {}).get('state')} "
      f"origin={(a.get('authorization') or {}).get('originated_by')} "
      f"ops={(a.get('authorization') or {}).get('operations_allowed')} "
      f"merge={(a.get('authorization') or {}).get('merge')}")

print("\n=== C. dispatch run-agent against the configured local endpoint ===")
st, disp = call("POST", f"/sessions/{sid}/run-agent",
                {"objective": "List the workspace root and summarise the entries you observe.",
                 "provider": "ollama", "max_turns": 4})
print(f"HTTP {st}")
print(json.dumps({k: disp.get(k) for k in (
    "state", "result_state", "loop_state", "loop_reason", "provider", "model",
    "effective_tools", "summary", "human_decision_required", "merge", "deploy",
    "self_authorized", "evidence_refs", "run_id") if k in disp}, indent=2))
print("  -- turns --")
for t in disp.get("turns") or []:
    obs = t.get("observation") or {}
    print(f"   turn {t.get('turn_index')}: decision={t.get('decision')} tool={t.get('tool_name')} "
          f"args={t.get('tool_arguments')}")
    print(f"     text: {str(t.get('text'))[:160]}")
    print(f"     observation ok={obs.get('ok')} keys={sorted(obs.keys())} "
          f"entries={str(obs.get('entries'))[:200]}")

print("\n=== D. events attributable to this run ===")
_, view = call("GET", f"/sessions/{sid}")
for e in view.get("events", []):
    print(f"  seq={e.get('sequence')} {str(e.get('event_type')):<32} run={e.get('run_id')} "
          f"payload={json.dumps(e.get('payload'), default=str)[:170]}")
print(f"  session_state={(view.get('session') or {}).get('state')} "
      f"reached_review_boundary={view.get('reached_review_boundary')} "
      f"runs={len(view.get('runs') or [])} evidence={len(view.get('evidence') or [])}")

print("\n=== E. boundary re-check: no test tool in the envelope ===")
tools = disp.get("effective_tools") or []
print(f"  effective_tools={tools} -> test present: "
      f"{any('test' in str(t).lower() for t in tools)}")
