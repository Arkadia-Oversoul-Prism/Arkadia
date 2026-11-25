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
Every anchor is a lowercase ASCII substring of a literal that exists in the
application the canonical origin actually serves -- `ANCHOR_APP`, which is
`web/arkadia_console`. The script re-reads that app's source and re-verifies
each anchor before trusting it, and a list that no longer matches the app is
reported as `STALE` (exit 2) rather than scored: an anchor table describing a
different frontend would otherwise report a healthy application as failing.

That is not hypothetical. This harness was written when the canonical origin
served the archived Prism frontend, and its anchors came from
`archive/frontend/arkadia-prism/web/public_prism/src`. Prism was archived
(`c081d200`, 2026-10-11) and the origin now serves the console, so every anchor
and four of the six probed routes described a retired application.

Lowercase ASCII substrings are used deliberately:

  * deployed text is uppercased by CSS, so case-sensitive matching would produce
    false failures;
  * CSS `text-transform` and unicode dashes (em/en) do not survive a naive
    substring match, so anchors avoid non-ASCII punctuation.

Two render states are expected, and they are declared per route rather than
inferred:

  * `public` -- the surface renders its own copy to an anonymous visitor;
  * `auth_threshold` -- the surface is protected (`requiresAuth` in
    `src/lib/surfaces.ts`), so `App.tsx` renders the shared sign-in threshold
    instead of the surface's own copy. Scoring a protected route against its
    own subtitle would fail on a correct application.

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

# The application the canonical origin serves. The anchor table is scoped to it:
# a table describing any other frontend is stale by construction, not a finding
# about production.
ANCHOR_APP = os.path.join("web", "arkadia_console")

# route -> (anchors, provenance, expected render state). Anchors are lowercase
# ASCII substrings. `public` routes render their own copy to an anonymous
# visitor; `auth_threshold` routes are protected, so the shared sign-in
# threshold renders instead (see `App.tsx::AuthThreshold`).
ROUTES: dict[str, tuple[list[str], str, str]] = {
    "/": (
        ["one coherent application over the canonical backend"],
        "pages/HomePage.tsx:148",
        "public",
    ),
    "/about": (
        ["one human-governed intelligence architecture"],
        "pages/AboutPage.tsx:6",
        "public",
    ),
    "/novanet": (
        ["the public field"],
        "pages/NovaNetPage.tsx:110",
        "public",
    ),
    "/operator": (
        ["boundary posture, evidence, and authority"],
        "pages/OperatorPage.tsx:109",
        "public",
    ),
    "/login": (
        ["authenticate against the canonical arkadia backend"],
        "pages/SignInPage.tsx:42",
        "public",
    ),
    "/knowledge": (
        ["this surface requires an authenticated arkadia identity"],
        "App.tsx::AuthThreshold (protected surface)",
        "auth_threshold",
    ),
}

# Console errors that are understood and benign. Matched as substrings.
EXPECTED_BENIGN: dict[str, str] = {
    "/api/codex/categories": (
        "route not implemented in this repository (absent from app.openapi()); "
        "components/novaNet/spiralCodexContract.ts records that it is not served"
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


def anchor_app_root() -> str:
    return os.path.join(repo_root(), ANCHOR_APP)


def source_anchors_present() -> dict[str, bool]:
    """Confirm each anchor still exists in the *served* application's source
    tree, so a stale anchor list is detected rather than silently trusted.

    Scoped to ``ANCHOR_APP`` on purpose. The previous revision read the archived
    Prism tree, which certified a list that could not match what the canonical
    origin serves.
    """
    src = os.path.join(anchor_app_root(), "src")
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
    return {a: (a in joined) for anchors, _prov, _state in ROUTES.values() for a in anchors}


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
        # Node's banner ("Node.js v24.22.2") is the last stderr line and says
        # nothing about the cause; report the line that names it.
        lines = [ln.strip() for ln in r.stderr.strip().splitlines() if ln.strip()]
        cause = next(
            (ln for ln in lines if "Cannot find module" in ln or "MODULE_NOT_FOUND" in ln),
            lines[-1] if lines else "require('playwright') failed",
        )
        return False, cause
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
    anchors, _prov, _state = ROUTES[obs["route"]]
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit machine-readable output")
    ap.add_argument(
        "--node-path",
        default=os.environ.get("PLAYWRIGHT_NODE_PATH"),
        help="NODE_PATH containing the playwright module",
    )
    args = ap.parse_args(argv)

    result: dict = {
        "alias": ALIAS,
        "anchor_app": ANCHOR_APP,
        "routes": {},
        "stale_anchors": [],
        "expected_benign": EXPECTED_BENIGN,
        "browser_rendered_ui": "UNKNOWN",
    }

    stale = [a for a, ok in source_anchors_present().items() if not ok]
    result["stale_anchors"] = stale

    # Fail closed. A stale anchor table is a harness defect, and scoring live
    # routes against it would report a healthy application as failing. It is
    # reported as STALE (undecided) rather than FAILED, and the probe is not run.
    if stale or not os.path.isdir(anchor_app_root()):
        result["browser_rendered_ui"] = "STALE"
        result["blocked_reason"] = (
            f"anchor list does not match {ANCHOR_APP}: "
            + (f"literals gone from source: {stale}" if stale else "app source tree missing")
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"browser-rendered UI: STALE -- {result['blocked_reason']}")
        return 2

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
            "expected_state": ROUTES[obs["route"]][2],
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
        print(f"alias: {ALIAS}  (anchor app: {ANCHOR_APP})")
        for route, info in result["routes"].items():
            print(
                f"  {route:<16} {info['verdict']:<9} status={info['status']} "
                f"bodyLen={info['bodyLen']} state={info['expected_state']}"
            )
            for n in info["failures"]:
                print(f"      ! {n}")
            for n in info["informational"]:
                print(f"      - {n}")
        print(f"browser-rendered UI: {result['browser_rendered_ui']}")

    return 0 if result["browser_rendered_ui"] == "OBSERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
