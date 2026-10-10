#!/usr/bin/env python3
"""Gate 2 browser-rendered UI observation (gate-hygiene).

The companion harness `gate2_production_observation.py` observes the *served*
surface: HTTP status, asset marker lineage, alias binding. It explicitly records
its own blind spot:

    browser-rendered UI correctness = UNKNOWN

A 200 with a matching asset hash proves the bundle was served. It does NOT prove
the app mounted, the router resolved, or the data-bound surfaces rendered. This
script closes exactly that gap by driving a real headless browser against the
live alias and asserting source-verified text anchors per route.

Read-only. Performs no mutation, holds no credential, never prints a token.

Anchor policy
-------------
Every anchor is a lowercase ASCII substring of a literal that exists in
`web/public_prism/src`, and the script re-verifies each one against the working
tree before trusting it (a stale anchor list is detected, not silently believed).
Lowercase ASCII substrings are used deliberately:

  * deployed text is uppercased by CSS, so case-sensitive matching would produce
    false failures;
  * CSS `text-transform` and unicode dashes (em/en) do not survive a naive
    substring match, so anchors avoid non-ASCII punctuation.

Known benign console noise
--------------------------
`/api/codex/categories` returns 404 in production: the route is not implemented
in this repository at all (no handler exists under `api/`). The caller degrades
gracefully -- `SpiralCodexFeed.tsx` falls back to `{ categories: [] }` when the
response is not ok -- so this is recorded as EXPECTED_BENIGN rather than a
runtime defect. Any *other* console error is a failure.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ALIAS = "https://arkadia-qzu4.onrender.com"

# route -> (anchors, provenance). Anchors are lowercase ASCII substrings.
ROUTES: dict[str, tuple[list[str], str]] = {
    "/": (
        ["become one continuous field"],
        "ArkadiaLandingPage.tsx",
    ),
    "/oracle": (
        ["pattern intelligence", "guest session"],
        "ArkanaCommune.tsx:757",
    ),
    "/nexus": (
        ["private reasomate remains separate"],
        "SocialFieldVerified.tsx:325",
    ),
    "/solariun": (
        ["enter solariun"],
        "SolariunConsole.tsx",
    ),
    "/solspire": (
        ["enter the enterprise layer"],
        "EnterpriseConsole.tsx:70",
    ),
    "/spiral-codex": (
        ["living archive of arkadia"],
        "SpiralCodexFeed.tsx:248",
    ),
}

# Console errors that are understood and benign. Matched as substrings.
EXPECTED_BENIGN: dict[str, str] = {
    "/api/codex/categories": (
        "route not implemented in this repository (no handler under api/); "
        "SpiralCodexFeed.tsx degrades to { categories: [] }"
    ),
}

NODE_PROBE = r"""
const {chromium}=require('playwright');
const routes=JSON.parse(process.argv[2]);
const base=process.argv[3];
(async()=>{
  const b=await chromium.launch({headless:true});
  const out=[];
  for(const route of routes){
    const p=await b.newPage();
    const ce=[],pe=[],fr=[];
    p.on('console',m=>{ if(m.type()==='error'){ const l=m.location()||{}; ce.push({text:m.text(),url:l.url||''}); } });
    p.on('pageerror',e=>pe.push(e.message));
    p.on('requestfailed',r=>fr.push(r.url()+' :: '+(r.failure()&&r.failure().errorText)));
    let status=null,err=null,body='';
    try{
      const r=await p.goto(base+route,{waitUntil:'networkidle',timeout:60000});
      status=r.status();
      await p.waitForTimeout(1500);
      body=await p.locator('body').innerText();
    }catch(e){ err=e.message; }
    out.push({route,status,err,bodyLen:body.length,
              bodyLower:body.toLowerCase(),
              consoleErrors:ce,pageErrors:pe,failedRequests:fr});
    await p.close();
  }
  await b.close();
  process.stdout.write(JSON.stringify(out));
})().catch(e=>{process.stdout.write(JSON.stringify({__probe_error__:e.message}));process.exit(1);});
"""


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def source_anchors_present() -> dict[str, bool]:
    """Confirm each anchor still exists in the frontend source tree, so a stale
    anchor list is detected rather than silently trusted."""
    src = os.path.join(repo_root(), "web", "public_prism", "src")
    corpus: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(src):
        for fn in filenames:
            if fn.endswith((".ts", ".tsx")):
                try:
                    with open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore") as fh:
                        corpus.append(fh.read().lower())
                except OSError:
                    continue
    joined = "\n".join(corpus)
    return {a: (a in joined) for anchors, _ in ROUTES.values() for a in anchors}


def playwright_available(node_path: str | None) -> tuple[bool, str]:
    if not shutil.which("node"):
        return False, "node not on PATH"
    env = dict(os.environ)
    if node_path:
        env["NODE_PATH"] = node_path
    r = subprocess.run(
        ["node", "-e", "require('playwright')"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    if r.returncode != 0:
        return False, (r.stderr.strip().splitlines() or ["require('playwright') failed"])[-1]
    return True, "ok"


def run_probe(node_path: str | None) -> list[dict]:
    env = dict(os.environ)
    if node_path:
        env["NODE_PATH"] = node_path
    with tempfile.TemporaryDirectory() as td:
        js = os.path.join(td, "probe.js")
        with open(js, "w", encoding="utf-8") as fh:
            fh.write(NODE_PROBE)
        r = subprocess.run(
            ["node", js, json.dumps(list(ROUTES)), ALIAS],
            capture_output=True,
            text=True,
            env=env,
            timeout=900,
        )
    if not r.stdout.strip():
        raise RuntimeError(f"probe produced no output: {r.stderr.strip()[:400]}")
    data = json.loads(r.stdout)
    if isinstance(data, dict):
        raise RuntimeError(f"probe error: {data.get('__probe_error__')}")
    return data


def classify(obs: dict) -> tuple[str, list[str], list[str]]:
    """Return (verdict, failures, informational)."""
    failures: list[str] = []
    info: list[str] = []
    anchors, _prov = ROUTES[obs["route"]]
    if obs["status"] != 200:
        return "FAILED", [f"HTTP {obs['status']} err={obs['err']}"], info
    missing = [a for a in anchors if a not in obs["bodyLower"]]
    if missing:
        failures.append(f"missing anchors: {missing}")
    if obs["pageErrors"]:
        failures.append(f"pageErrors: {obs['pageErrors'][:2]}")
    if obs["failedRequests"]:
        failures.append(f"failedRequests: {obs['failedRequests'][:2]}")
    unexpected = []
    benign_hits = []
    for err in obs["consoleErrors"]:
        blob = f"{err.get('text', '')} {err.get('url', '')}"
        match = next((b for b in EXPECTED_BENIGN if b in blob), None)
        if match:
            benign_hits.append(match)
            continue
        unexpected.append(err.get("text", str(err)))
    if unexpected:
        failures.append(f"unexpected console errors: {unexpected[:2]}")
    if benign_hits:
        info.append(f"expected-benign console noise: {sorted(set(benign_hits))}")
    return ("OBSERVED" if not failures else "FAILED"), failures, info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit machine-readable output")
    ap.add_argument(
        "--node-path",
        default=os.environ.get("PLAYWRIGHT_NODE_PATH"),
        help="NODE_PATH containing the playwright module",
    )
    args = ap.parse_args()

    result: dict = {
        "alias": ALIAS,
        "routes": {},
        "stale_anchors": [],
        "expected_benign": EXPECTED_BENIGN,
        "browser_rendered_ui": "UNKNOWN",
    }

    stale = [a for a, ok in source_anchors_present().items() if not ok]
    result["stale_anchors"] = stale

    ok, why = playwright_available(args.node_path)
    if not ok:
        result["browser_rendered_ui"] = "BLOCKED"
        result["blocked_reason"] = f"playwright unavailable: {why}"
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"browser-rendered UI: BLOCKED -- {result['blocked_reason']}")
        return 2

    try:
        observations = run_probe(args.node_path)
    except Exception as e:
        result["browser_rendered_ui"] = "BLOCKED"
        result["blocked_reason"] = f"{type(e).__name__}: {e}"
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"browser-rendered UI: BLOCKED -- {result['blocked_reason']}")
        return 2

    verdicts = []
    for obs in observations:
        verdict, failures, info = classify(obs)
        verdicts.append(verdict)
        result["routes"][obs["route"]] = {
            "verdict": verdict,
            "status": obs["status"],
            "bodyLen": obs["bodyLen"],
            "anchors_required": ROUTES[obs["route"]][0],
            "failures": failures,
            "informational": info,
        }

    if "FAILED" in verdicts:
        result["browser_rendered_ui"] = "FAILED"
    elif all(v == "OBSERVED" for v in verdicts):
        result["browser_rendered_ui"] = "OBSERVED"
    else:
        result["browser_rendered_ui"] = "PARTIAL"

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"alias: {ALIAS}")
        for route, info in result["routes"].items():
            print(f"  {route:<16} {info['verdict']:<9} status={info['status']} bodyLen={info['bodyLen']}")
            for n in info["failures"]:
                print(f"      ! {n}")
            for n in info["informational"]:
                print(f"      - {n}")
        if stale:
            print(f"  STALE ANCHORS: {stale}")
        print(f"browser-rendered UI: {result['browser_rendered_ui']}")

    return 0 if result["browser_rendered_ui"] == "OBSERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
