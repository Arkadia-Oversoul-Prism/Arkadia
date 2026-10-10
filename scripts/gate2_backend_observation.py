#!/usr/bin/env python3
"""Gate 2 backend-runtime observation harness (gate-hygiene).

The older sibling harnesses observed the former split frontend. The canonical
production verifier is now scripts/render_production_reconciliation.py, which
captures live OpenAPI and compares every operation against source. The browser
observer is also pointed at the canonical Render origin.

Neither observes the backend. The Render service is the actual application
runtime -- the Oracle spine, the TTS boundary, the API surface -- and it is
reachable without a credential, so the link

    main SHA -> backend deployment -> backend runtime observation

is testable where the Vercel build-output link is not.

Read-only. Holds no credential, performs no mutation, never prints a token.
Standard library only, so it runs in any sandbox.

ORACLE AND ITS LIMITS
---------------------
The oracle is the canonical FastAPI schema: the set of ``METHOD path`` pairs,
compared between the deployed service and a locally-imported revision. This is
a *route-set lineage* oracle, analogous in kind to the frontend marker-set
oracle.

Its discriminating power is measured, not assumed. A route set only changes
when a route is added, removed, or re-pathed, so it cannot separate two
revisions that differ only in handler bodies -- which is the common case for
this repository. ``oracle_power()`` reports whether the candidate revisions
are in fact separated; when they are not, equality is reported as
``VERIFIED (undiscriminating)`` and never as a stronger claim. Repetition
cannot convert that into discrimination.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "Arkadia-Oversoul-Prism/Arkadia"

# The Render service that serves the application runtime. Both the apex host and
# the service host are probed; Render's onrender.com hosts are not SSO-gated the
# way Vercel Deployment Protection gates the frontend preview URLs.
BACKEND_HOSTS = [
    "https://arkadia-qzu4.onrender.com",
]

# Route prefixes that must be present for the backend to be the real Arkadia
# runtime rather than a placeholder/health-only service. Provenance is the
# feature that introduced each prefix.
REQUIRED_PREFIXES: dict[str, str] = {
    "/api/commune": "Oracle/ReasoMate chat spine",
    "/api/stellar-cartography": "Stellar Cartography readout (kernel/stellar.py)",
    "/api/tts": "TTS boundary (kernel/tts.py)",
    "/api/echoes": "Echofeild -> SolSpire/Knowledge OS pipe",
}

# Endpoints expected to answer anonymously with 200. Used as a liveness floor so
# a schema served by a stale or degraded process cannot pass unremarked.
LIVE_PROBES = [
    "/",
    "/api/stellar-cartography",
    "/api/tts/status",
]


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(args: list[str], cwd: str | None = None) -> str:
    return subprocess.run(
        args, capture_output=True, text=True, cwd=cwd or repo_root()
    ).stdout.strip()


def resolve_main() -> str:
    return sh(["git", "rev-parse", "origin/main"])


def fetch(url: str, timeout: int = 45) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "arkadia-gate2-backend-observation"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # noqa: BLE001 -- network shape is part of the evidence
        return 0, str(e).encode()


def operation_signature(spec: dict) -> list[str]:
    """Canonical, order-independent signature of a FastAPI schema.

    Method, path, summary and tags are all deployment-visible in the schema and
    survive serialization, so they discriminate slightly more than the bare
    path set. They are still not handler bodies.
    """
    rows = []
    for path, ops in spec.get("paths", {}).items():
        for method, op in ops.items():
            if method.lower() not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                continue
            rows.append(
                f"{method.upper()} {path} :: {op.get('summary', '')} :: "
                f"{','.join(sorted(op.get('tags') or []))}"
            )
    return sorted(rows)


def digest(rows: list[str]) -> str:
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def local_signature(rev: str, worktree: str | None = None) -> list[str] | None:
    """Import the app at ``rev`` and return its schema signature.

    Imports in a subprocess so a revision that fails to import (for example the
    P1-A SyntaxError) is reported as an observation rather than crashing the
    harness. Imports from a detached worktree so the caller's checkout is never
    disturbed.
    """
    root = worktree or repo_root()
    code = (
        "import sys, json; sys.path.insert(0, '.');"
        "import api.main as m;"
        "print('@@' + json.dumps(m.app.openapi()))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=root,
        timeout=600,
    )
    for line in out.stdout.splitlines():
        if line.startswith("@@"):
            spec = json.loads(line[2:])
            return operation_signature(spec)
    return None


def oracle_power(revs: dict[str, list[str] | None]) -> dict:
    """Measure whether the oracle actually separates the candidate revisions.

    Equality between deployed and local is only *evidence* if some candidate
    would have produced a different signature. Where all candidates agree, the
    oracle is undiscriminating and the result must be labelled as such.
    """
    usable = {r: s for r, s in revs.items() if s is not None}
    hashes = {r: digest(s) for r, s in usable.items()}
    distinct = set(hashes.values())
    return {
        "revisions_compared": sorted(usable),
        "signature_hashes": hashes,
        "distinct_signatures": len(distinct),
        "discriminating": len(distinct) > 1,
    }


def classify(
    deployed: list[str] | None,
    local: list[str] | None,
    power: dict,
    live_ok: bool,
    prefixes_ok: list[str],
) -> tuple[str, list[str]]:
    """Return (state, failures). State is one of the five evidence states."""
    failures: list[str] = []
    if deployed is None:
        return "UNKNOWN", ["backend schema unreachable"]
    if local is None:
        return "UNKNOWN", ["local revision failed to import"]
    if not live_ok:
        failures.append("liveness floor not met")
    if prefixes_ok:
        failures.append(f"required route prefixes absent: {prefixes_ok}")
    if failures:
        return "FAILED", failures
    if deployed != local:
        only_deployed = sorted(set(deployed) - set(local))
        only_local = sorted(set(local) - set(deployed))
        return "CONTRADICTED", [
            f"schema differs; only in deployment: {only_deployed[:5]}",
            f"only in local: {only_local[:5]}",
        ]
    if not power.get("discriminating"):
        return "VERIFIED (undiscriminating)", [
            "all candidate revisions share one signature; equality cannot "
            "separate the deployed commit"
        ]
    return "VERIFIED", []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--host", default=BACKEND_HOSTS[0])
    ap.add_argument(
        "--compare",
        nargs="*",
        default=[],
        metavar="REV",
        help="extra revisions to test the oracle's discriminating power against",
    )
    args = ap.parse_args()

    report: dict = {"host": args.host, "boundaries": {}}
    main_sha = resolve_main()
    report["main_sha"] = main_sha

    # ---- deployed schema ----------------------------------------------------
    status, body = fetch(f"{args.host}/openapi.json")
    deployed = None
    if status == 200:
        try:
            spec = json.loads(body)
            deployed = operation_signature(spec)
            report["deployed_title"] = spec.get("info", {}).get("title")
            report["deployed_operations"] = len(deployed)
            report["deployed_digest"] = digest(deployed)
        except Exception as e:  # noqa: BLE001
            report["schema_error"] = str(e)
    report["schema_status"] = status

    # ---- liveness floor -----------------------------------------------------
    probes = {}
    for path in LIVE_PROBES:
        s, b = fetch(f"{args.host}{path}")
        probes[path] = {"status": s, "bytes": len(b)}
    report["live_probes"] = probes
    live_ok = all(p["status"] == 200 for p in probes.values())

    # ---- required prefixes --------------------------------------------------
    # A signature row is "METHOD path :: summary :: tags"; the path is the
    # second whitespace-delimited token. Splitting on the first space alone
    # would keep the " :: summary" suffix and make every prefix look absent.
    paths = {r.split(" ", 2)[1] for r in (deployed or [])}
    missing = [
        f"{p} ({prov})"
        for p, prov in REQUIRED_PREFIXES.items()
        if not any(x == p or x.startswith(p + "/") for x in paths)
    ]
    report["required_prefixes_missing"] = missing

    # ---- local + candidate signatures --------------------------------------
    revs: dict[str, list[str] | None] = {}
    local = local_signature(main_sha)
    revs[f"main:{main_sha[:12]}"] = local

    worktrees: list[str] = []
    for rev in args.compare:
        wt = f"/tmp/gate2_backend_wt_{rev[:12]}"
        if not os.path.isdir(wt):
            subprocess.run(
                ["git", "worktree", "add", "--detach", wt, rev],
                capture_output=True,
                cwd=repo_root(),
            )
            worktrees.append(wt)
        revs[f"cand:{rev[:12]}"] = local_signature(rev, worktree=wt)

    power = oracle_power(revs)
    report["oracle_power"] = power
    if deployed is not None:
        report["deployed_matches_main"] = deployed == local

    state, failures = classify(deployed, local, power, live_ok, missing)
    report["state"] = state
    report["failures"] = failures

    report["boundaries"]["current main resolved"] = f"VERIFIED -- {main_sha}"
    report["boundaries"]["main -> backend deployment identity"] = (
        "UNKNOWN -- no provider record; Render does not publish a source SHA "
        "and no route exposes the deploy commit"
    )
    report["boundaries"]["backend runtime observation"] = state
    report["boundaries"]["backend <-> source lineage"] = (
        f"{state} -- route-set oracle"
    )
    report["boundaries"]["production acceptance"] = "NOT CLAIMED (human authority)"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        print("ARKADIA ENGINEERING -- GATE-02 BACKEND RUNTIME OBSERVATION")
        print("=" * 64)
        print(f"main SHA          : {main_sha}")
        print(f"backend host      : {args.host}")
        print(f"schema            : HTTP {status}  operations={report.get('deployed_operations')}")
        print(f"deployed digest   : {report.get('deployed_digest', '-')[:20]}")
        print()
        print("LIVENESS FLOOR")
        for p, r in probes.items():
            print(f"  {p:<28} HTTP {r['status']}  {r['bytes']} bytes")
        print()
        print("REQUIRED PREFIXES")
        print(f"  missing: {missing or 'none'}")
        print()
        print("ROUTE-SET ORACLE")
        for rev, h in power["signature_hashes"].items():
            print(f"  {rev:<24} {h[:20]}")
        print(f"  distinct signatures: {power['distinct_signatures']}"
              f"  => discriminating: {power['discriminating']}")
        print()
        print("BOUNDARY CLASSIFICATION")
        for k, v in report["boundaries"].items():
            print(f"  {k:<42} {v}")
        if failures:
            print()
            print("NOTES")
            for f in failures:
                print(f"  - {f}")

    for wt in worktrees:
        subprocess.run(["git", "worktree", "remove", "--force", wt],
                       capture_output=True, cwd=repo_root())
    return 0


if __name__ == "__main__":
    sys.exit(main())
