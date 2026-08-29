"""WEAVER-W2 — Browser cockpit over W1 view model (stdlib HTTP only).

VIEW, NOT BRAIN. No mutation. No PassSpec inference.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .workbench_view import (
    observatory,
    render_verification_matrix,
    repository_state,
    run_read_only_pipeline,
)

# In-process last analysis for the local operator session (not durable memory)
_LAST: dict[str, Any] = {}


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, indent=2, default=str).encode("utf-8")


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Weaver Cockpit W2</title>
<style>
  :root {
    --bg: #0f1218; --panel: #171b24; --border: #2a3140; --text: #e6eaf0;
    --muted: #8b95a8; --accent: #5b9fd4; --ok: #3d9a6a; --warn: #c9a227;
    --bad: #c44; --locked: #a67c52;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.45;
  }
  header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 18px; border-bottom: 1px solid var(--border); background: #12161e;
  }
  header h1 { margin: 0; font-size: 16px; letter-spacing: 0.04em; font-weight: 600; }
  .auth-badge {
    font-size: 12px; padding: 4px 10px; border: 1px solid var(--locked); color: var(--locked);
    border-radius: 4px; font-weight: 600;
  }
  .layout { display: grid; grid-template-columns: 200px 1fr 260px; min-height: calc(100vh - 52px); }
  nav, aside, main { padding: 14px; }
  nav, aside { background: var(--panel); border-right: 1px solid var(--border); }
  aside { border-right: none; border-left: 1px solid var(--border); }
  nav h2, aside h2, main h2 { margin: 0 0 10px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }
  .stage { padding: 6px 8px; margin-bottom: 4px; border-radius: 4px; border: 1px solid transparent; font-size: 12px; }
  .stage .name { font-weight: 600; }
  .stage .st { color: var(--muted); font-size: 11px; }
  .stage.COMPLETE { border-color: #2d5a40; }
  .stage.LOCKED, .stage.NONE { border-color: #4a3a28; }
  .stage.PENDING, .stage.AVAILABLE { border-color: var(--border); }
  .panel {
    background: var(--panel); border: 1px solid var(--border); border-radius: 6px;
    padding: 12px; margin-bottom: 12px;
  }
  .panel h3 { margin: 0 0 8px; font-size: 13px; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  input[type=text] {
    flex: 1; min-width: 200px; background: #0c0f14; border: 1px solid var(--border);
    color: var(--text); padding: 8px 10px; border-radius: 4px;
  }
  button {
    background: #1e3a55; color: var(--text); border: 1px solid var(--accent);
    padding: 8px 14px; border-radius: 4px; cursor: pointer; font-weight: 600;
  }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .label-ro { font-size: 11px; color: var(--accent); margin-left: 8px; }
  .col3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
  .list { max-height: 180px; overflow: auto; font-size: 12px; }
  .list div { padding: 4px 0; border-bottom: 1px solid #222833; }
  pre {
    background: #0c0f14; border: 1px solid var(--border); padding: 8px; overflow: auto;
    max-height: 240px; font-size: 11px; white-space: pre-wrap;
  }
  .pill { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 11px; border: 1px solid var(--border); }
  .pill.warn { color: var(--warn); border-color: var(--warn); }
  .pill.ok { color: var(--ok); border-color: var(--ok); }
  .pill.bad { color: var(--bad); border-color: var(--bad); }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th, td { text-align: left; padding: 4px 6px; border-bottom: 1px solid var(--border); }
  .muted { color: var(--muted); }
  @media (max-width: 960px) {
    .layout { grid-template-columns: 1fr; }
    .col3 { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<header>
  <h1>WEAVER COCKPIT <span class="muted">W2</span></h1>
  <div class="auth-badge" id="authBadge">AUTH: LOCKED</div>
</header>
<div class="layout">
  <nav>
    <h2>Lifecycle</h2>
    <div id="lifecycle"></div>
    <h2 style="margin-top:16px">Repository</h2>
    <div id="repoMini" class="mono muted"></div>
  </nav>
  <main>
    <div class="panel">
      <h3>Objective <span class="label-ro">READ-ONLY ANALYSIS</span></h3>
      <div class="row">
        <input type="text" id="objective" placeholder="What do you want Weaver to investigate?"/>
        <button id="btnAnalyze">ANALYZE</button>
      </div>
      <p class="muted" style="margin:8px 0 0">Does not modify files, commit, push, or authorize execution.</p>
    </div>
    <div class="panel">
      <h3>Analysis</h3>
      <div class="col3">
        <div><strong>FACTS</strong><div class="list" id="facts"></div></div>
        <div><strong>INFERENCES</strong><div class="list" id="inferences"></div></div>
        <div><strong>UNKNOWN</strong><div class="list" id="unknowns"></div></div>
      </div>
    </div>
    <div class="panel">
      <h3>Engineering Plan</h3>
      <div id="planMeta" class="mono muted"></div>
      <div id="planSteps" class="list"></div>
    </div>
    <div class="panel">
      <h3>Changeset</h3>
      <div id="changeset" class="list"></div>
    </div>
    <div class="panel">
      <h3>Proposed Patch <span class="pill" id="execPill">EXECUTED: FALSE</span></h3>
      <div id="patchMeta" class="mono muted"></div>
      <pre id="patchText"></pre>
      <div id="impact" class="muted"></div>
    </div>
    <div class="panel">
      <h3>Verification / Proof</h3>
      <table><thead><tr><th>Claim</th><th>Evidence</th><th>Status</th></tr></thead>
      <tbody id="proofBody"></tbody></table>
    </div>
  </main>
  <aside>
    <h2>Governance</h2>
    <div class="panel">
      <div>PassSpec: <strong id="gPass">NONE</strong></div>
      <div>PatchApproval: <strong id="gAppr">NONE</strong></div>
      <div>Execution: <strong id="gExec">LOCKED</strong></div>
      <div>Mutation: <strong>K3 ONLY</strong></div>
      <p class="muted" style="margin-top:10px;font-size:11px">
        PROPOSED ≠ APPROVAL ≠ EXECUTION ≠ VERIFICATION
      </p>
      <button disabled title="Requires PassSpec + PatchApproval via K15→K3">EXECUTE (LOCKED)</button>
    </div>
    <h2>Observatory</h2>
    <div class="panel mono" id="obsDetail" style="font-size:11px"></div>
  </aside>
</div>
<script>
async function jget(url) {
  const r = await fetch(url);
  return r.json();
}
async function jpost(url, body) {
  const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  return r.json();
}
function esc(s) {
  return String(s??'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function fillList(el, items, pick) {
  el.innerHTML = (items||[]).slice(0,40).map(it => '<div>'+esc(pick(it))+'</div>').join('') || '<div class="muted">—</div>';
}
function renderObs(o) {
  const repo = o.repository||{};
  const auth = o.authority||{};
  document.getElementById('authBadge').textContent = 'AUTH: ' + (auth.Execution||'LOCKED');
  document.getElementById('gPass').textContent = auth.PassSpec||'NONE';
  document.getElementById('gAppr').textContent = auth.PatchApproval||'NONE';
  document.getElementById('gExec').textContent = auth.Execution||'LOCKED';
  document.getElementById('repoMini').innerHTML =
    esc(repo.identity)+'<br/>'+esc(repo.branch)+'<br/>HEAD '+(repo.clean?'● CLEAN':'● DIRTY')+
    '<br/>'+esc((repo.head_sha||'').slice(0,12))+
    (repo.head_sha===repo.origin_sha?' == ORIGIN':' ≠ ORIGIN')+
    (repo.stale_hint?' <span class="pill warn">STALE</span>':'');
  document.getElementById('obsDetail').textContent = JSON.stringify(repo, null, 2);
  const life = document.getElementById('lifecycle');
  life.innerHTML = (o.lifecycle||[]).map(s =>
    '<div class="stage '+(s.status||'')+'"><div class="name">'+esc(s.stage)+'</div><div class="st">'+esc(s.status)+'</div></div>'
  ).join('');
}
function renderPipeline(p) {
  const an = p.analysis||{};
  fillList(document.getElementById('facts'), an.facts, x => (x.kind?('['+x.kind+'] '):'')+(x.statement||x));
  fillList(document.getElementById('inferences'), an.inferences, x => (x.kind?('['+x.kind+'] '):'')+(x.statement||x));
  fillList(document.getElementById('unknowns'), an.unknowns, x => (x.kind?('['+x.kind+'] '):'')+(x.statement||x));
  const plan = p.plan||{};
  document.getElementById('planMeta').textContent =
    'plan_id='+(plan.plan_id||'')+'  scope='+(plan.scope_status||'')+'  paths='+JSON.stringify(plan.affected_paths||[]);
  fillList(document.getElementById('planSteps'), plan.implementation_steps||[], x => x);
  const cs = p.changeset||{};
  fillList(document.getElementById('changeset'), cs.files||[], f =>
    (f.operation||'')+' '+ (f.path||'')+'  symbols='+JSON.stringify(f.symbols_or_regions||[])
  );
  const patch = p.patch||{};
  document.getElementById('patchMeta').textContent =
    'patch_id='+(patch.patch_id||'')+' status='+(patch.status||'')+' base='+(patch.base_head_sha||'');
  document.getElementById('execPill').textContent = 'EXECUTED: ' + (patch.EXECUTED===false||patch.EXECUTED==null?'FALSE':String(patch.EXECUTED));
  const files = patch.files||[];
  document.getElementById('patchText').textContent = files.map(f => f.patch_text||'').join('\n---\n') || '(no patch text)';
  document.getElementById('impact').textContent = 'impact: ' + JSON.stringify(patch.impact||{});
  const gov = p.authorization||{};
  document.getElementById('gPass').textContent = gov.PassSpec||'NONE';
  document.getElementById('gAppr').textContent = gov.PatchApproval||'NONE';
  document.getElementById('gExec').textContent = gov.Execution||'LOCKED';
  document.getElementById('authBadge').textContent = 'AUTH: ' + (gov.Execution||'LOCKED');
  if (p.pipeline) {
    // refresh lifecycle from pipeline after analyze
    jget('/api/observatory?pipeline=1').then(renderObs).catch(()=>{});
  }
}
async function refresh() {
  const o = await jget('/api/observatory');
  renderObs(o);
  const last = await jget('/api/last');
  if (last && last.objective) renderPipeline(last);
  const proof = await jget('/api/proof');
  const body = document.getElementById('proofBody');
  body.innerHTML = (proof.matrix||[]).map(r =>
    '<tr><td>'+esc(r.claim)+'</td><td>'+esc(r.evidence)+'</td><td>'+esc(r.status)+'</td></tr>'
  ).join('') || '<tr><td colspan=3 class="muted">No verification report (NOT RUN)</td></tr>';
}
document.getElementById('btnAnalyze').onclick = async () => {
  const objective = document.getElementById('objective').value.trim();
  if (!objective) return;
  document.getElementById('btnAnalyze').disabled = true;
  try {
    const p = await jpost('/api/analyze', {objective});
    renderPipeline(p);
    const o = await jget('/api/observatory');
    // merge pipeline statuses
    if (p.pipeline) {
      o.lifecycle = Object.keys(p.pipeline).filter(k=>k==k.toUpperCase()).map(k => ({stage:k, status:(p.pipeline[k]&&p.pipeline[k].status)||'PENDING'}));
      // rebuild from known order if present
    }
    renderObs(await jget('/api/observatory'));
    await refresh();
  } finally {
    document.getElementById('btnAnalyze').disabled = false;
  }
};
refresh();
</script>
</body>
</html>
"""


class WorkbenchHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:  # quieter
        pass

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        global _LAST
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/observatory":
            pipe = _LAST.get("pipeline") if _LAST else None
            state = observatory(pipeline=pipe)
            # if pipeline present, overlay lifecycle statuses
            if pipe:
                stages = []
                from .workbench_view import LIFECYCLE

                for name in LIFECYCLE:
                    info = pipe.get(name) or {}
                    stages.append({"stage": name, "status": info.get("status", "PENDING"), "detail": info.get("detail", "")})
                d = state.to_dict()
                d["lifecycle"] = stages
                if pipe.get("pass_spec"):
                    d["authority"]["PassSpec"] = "PRESENT"
                if pipe.get("patch_approval"):
                    d["authority"]["PatchApproval"] = "PRESENT"
                self._send(200, _json_bytes(d), "application/json")
            else:
                self._send(200, _json_bytes(state.to_dict()), "application/json")
            return
        if path == "/api/repo":
            self._send(200, _json_bytes(repository_state()), "application/json")
            return
        if path == "/api/last":
            self._send(200, _json_bytes(_LAST or {}), "application/json")
            return
        if path == "/api/proof":
            matrix = render_verification_matrix((_LAST or {}).get("verification_report"))
            self._send(200, _json_bytes({"matrix": matrix}), "application/json")
            return
        self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:
        global _LAST
        path = urlparse(self.path).path
        if path != "/api/analyze":
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, b'{"error":"invalid json"}', "application/json")
            return
        objective = str(data.get("objective") or "").strip()
        result = run_read_only_pipeline(objective)
        _LAST = result
        self._send(200, _json_bytes(result), "application/json")


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), WorkbenchHandler)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = make_server(host, port)
    print(f"Weaver Cockpit W2: http://{host}:{port}/")
    print("Read-only default. Mutation path: K3 ONLY (not exposed as one-click).")
    httpd.serve_forever()
