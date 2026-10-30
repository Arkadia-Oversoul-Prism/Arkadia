"""P0.5 served-path probe: real HTTP against the running Arkadia API.

Proves the dispatch wiring end to end (route -> runtime -> gateway -> loop -> events)
and that the outcome is reported honestly. NOT a proof of a live model: no inference
provider is configured in this environment, so the expected terminal state is BLOCKED.
"""
import base64
import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8124/api/lab/engineering"


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
    except Exception as exc:  # network/timeout
        return -1, {"error": str(exc)}


print("=== 1. availability (configuration truth vs dispatch truth) ===")
_, gw = call("GET", "/gateway")
for p in gw.get("catalog", []):
    print(f"  {p['provider']:<24} status={p['status']:<14} bound={p['adapter_bound']}"
          f" dispatchable={p['dispatchable']}")

print("\n=== 2. negative control: dispatch on an unauthorized session ===")
_, agent = call("POST", "/agents", {"role": "BUILDER", "display_name": "P05 probe worker"})
agent_id = agent.get("agent_id") or agent.get("id")
print(f"  agent_id={agent_id}")
_, anon = call("POST", "/sessions", {"workspace_ref": "/workspace", "agent_id": agent_id,
                                     "objective": "unauthorized probe"})
anon_id = anon.get("session_id") or anon.get("id")
st, resp = call("POST", f"/sessions/{anon_id}/run-agent",
                {"objective": "should be refused", "provider": "ollama", "max_turns": 2})
print(f"  dispatch without authorization -> HTTP {st}: {json.dumps(resp)[:300]}")

print("\n=== 3. authorized session ===")
_, sess = call("POST", "/sessions", {"workspace_ref": "/workspace/chats/f6a4fd1dd162a73f0b053afb",
                                     "agent_id": agent_id,
                                     "objective": "Inspect the bounded test execution module"})
sid = sess.get("session_id") or sess.get("id")
print(f"  session_id={sid} state={sess.get('state')}")
_, authz = call("POST", f"/sessions/{sid}/authorize",
                {"operations_allowed": ["read", "test"], "duration_minutes": 60})
print(f"  authorize(read,test) -> state={authz.get('state')} "
      f"operations={authz.get('operations_allowed')} origin={authz.get('origin')}")

print("\n=== 4. dispatch run-agent (no provider configured -> expect BLOCKED) ===")
st, disp = call("POST", f"/sessions/{sid}/run-agent",
                {"objective": "Read the bounded test execution module and summarise its allowlist",
                 "provider": "ollama", "max_turns": 3})
print(f"HTTP {st}")
print(json.dumps({k: disp.get(k) for k in (
    "state", "loop_state", "loop_reason", "provider", "model", "effective_tools",
    "turn_count", "error") if k in disp}, indent=2))
print("  turns:", json.dumps(disp.get("turns"), default=str)[:400])

print("\n=== 5. observation: session events attributable to the mission ===")
st, view = call("GET", f"/sessions/{sid}")
events = view.get("events", []) if isinstance(view, dict) else []
for e in events[-12:]:
    print(f"  {str(e.get('created_at', ''))[:19]} {str(e.get('kind')):<28} "
          f"{str(e.get('summary') or e.get('detail') or e.get('message'))[:110]}")
print(f"  total events={len(events)} session_state={view.get('state')}")

print("\n=== 6. boundary: is 'test' inside the dispatched tool envelope? ===")
tools = disp.get("effective_tools") or []
test_tools = [t for t in tools if "test" in str(t).lower()]
print(f"  effective_tools={tools}")
print(f"  test-shaped tools in dispatch envelope = {test_tools}  "
      f"({'BOUNDARY HELD' if not test_tools else 'BOUNDARY BREACHED'})")

print("\n=== 7. second provider: bound-but-not-dispatchable (n_atlas) ===")
st2, disp2 = call("POST", f"/sessions/{sid}/run-agent",
                  {"objective": "probe n_atlas availability", "provider": "n_atlas", "max_turns": 2})
print(f"HTTP {st2} state={disp2.get('state')} loop_state={disp2.get('loop_state')} "
      f"reason={disp2.get('loop_reason')}")
