#!/usr/bin/env python3
"""Gate 2 production observation harness (gate-hygiene).

Observes the live production surface and classifies each link of the chain:

    main SHA -> deployment SHA -> deployment observation -> alias binding -> UI

Read-only. Holds no Vercel credential, performs no mutation, and never prints a
token. Uses only the standard library so it runs in any sandbox.

Two oracles are used, and their limits are stated rather than glossed:

  * marker-set lineage -- discriminating source literals that survive minification.
    Asset hashes are NOT used: the build output is environment-dependent, so a hash
    match proves nothing and a mismatch proves nothing.
  * source-lineage closure -- if every candidate deployment SHA is a descendant of
    the last commit that touched the *same* frontend build input, then every
    candidate compiles byte-identical frontend source, and the artifact cannot
    discriminate between them. The alias->SHA question becomes immaterial to
    *source* lineage even though it remains unobservable.

Neither oracle may be applied to a deployment of a different application. The
root ``vercel.json`` was repointed to ``web/console`` (commit 404452e0), so the
repository now produces two frontends with disjoint build inputs and disjoint
marker sets. Comparing the marker set of one against the artifact of the other
is meaningless, and a "no markers found" result must never be reported as
agreement. The harness therefore reads which app the deployment's build input
names before it reads any marker, and refuses to claim marker agreement it did
not observe.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "Arkadia-Oversoul-Prism/Arkadia"
ALIAS = "https://arkadia-prism.vercel.app/"

# The harness observes the Prism surface. Its closure argument is valid only over
# deployments built from the Prism build input: a Console deployment shares no
# build input with Prism, so its ancestry says nothing about the Prism artifact.
BUILD_INPUTS = ["web/public_prism/", ":!web/public_prism/dist"]

# Every frontend the root ``vercel.json`` can be repointed at. A Production
# deployment whose environment names a project with no build input here cannot
# be placed on a build<->source lineage and must be classified, not assumed.
KNOWN_FRONTENDS: dict[str, list[str]] = {
    "arkadia-prism": ["web/public_prism/", ":!web/public_prism/dist"],
    "console": ["web/console/", ":!web/console/dist"],
}

# The application the MARKERS literals below were drawn from. This is a property
# of the marker list, NOT of any deployment: the harness must never assume the
# artifact it fetched is the app its markers describe.
#
# The alias resolves to whichever project Vercel last assigned it to, and the
# root project was repointed from ``web/public_prism`` to ``web/console`` at
# 404452e0 (2026-10-02). From that commit the alias serves Console while these
# markers remain Prism literals, so every marker reads 0 -- which is "this is a
# different application", not "the artifact disagrees with the source".
MARKER_APP = "arkadia-prism"

# A Production record is labelled `Production`, `Production – arkadia-prism`, or
# `Production – console`. An exact-equality test admitted only the bare form, so
# once Vercel began suffixing the project name the harness matched *no*
# production deployments and reported the link as stale while a current
# deployment existed. Match the production prefix exactly -- anchored, so a
# `Preview – ...` record cannot be admitted -- and never by equality.
PRODUCTION_ENVIRONMENT_RE = re.compile(r"^Production\b")

# literal -> (provenance, expected_in_source, discriminates)
MARKERS: dict[str, tuple[str, bool, str]] = {
    "separate explicit downstream stages": (
        "CapabilityChamber.tsx (SG-03 boundary)",
        True,
        "SG-03 chamber rewrite",
    ),
    "separate downstream stages": (
        "control: pre-SG-03 wording",
        False,
        "control -- must be absent",
    ),
    "activity-draft.v1:": (
        "CapabilityChamber.tsx (SG-03 draft key)",
        True,
        "SG-03",
    ),
    "learning-activity-work-surface": (
        "CapabilityChamber.tsx (SG-03 testid)",
        True,
        "SG-03",
    ),
    "sg03-contract-boundary": (
        "CapabilityChamber.tsx (SG-03 testid)",
        True,
        "SG-03",
    ),
    "solspire-object-summary": (
        "OpportunityRadarPage",
        True,
        "Solariun radar",
    ),
    "opportunity-radar": (
        "SolSpire lens registry",
        True,
        "Solariun radar route",
    ),
    "activity-runtime-draft.v1:": (
        "ActivityRuntime.tsx (SG-04 draft key)",
        True,
        "SG-04 -- RED on main, see classification",
    ),
}


def sh(args: list[str]) -> str:
    return subprocess.run(
        args, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ).stdout.strip()


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_main() -> str:
    return sh(["git", "rev-parse", "origin/main"])


def frontend_of(environment: str) -> str | None:
    """Which frontend does a ``Production – <project>`` record name?

    The project suffix is the only app identity the deployment API exposes, so it
    is read from the label rather than inferred from the marker set. A record with
    no known project suffix returns ``None``: its app is undetermined, and an
    undetermined app cannot be scored against any marker set.
    """
    # Split on the label separator (en/em dash, or a spaced hyphen) -- never on a
    # bare hyphen, which is part of project names like ``arkadia-prism``.
    parts = re.split(r"\s+[\u2013\u2014]\s+|\s+-\s+", environment.strip())
    if len(parts) < 2:
        return None
    project = parts[-1].strip().lower()
    return project if project in KNOWN_FRONTENDS else None


def last_build_input_commit(app: str = MARKER_APP) -> tuple[str, str, str]:
    """Last commit that touched the build input of ``app``.

    Scoped to one app: the two frontends have disjoint inputs, so a commit that
    rebuilt Console is not evidence about Prism source and vice versa.
    """
    out = sh(["git", "log", "-1", "--format=%H|%ci|%s", "--", *KNOWN_FRONTENDS[app]])
    sha, date, subject = out.split("|", 2)
    return sha, date, subject


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            capture_output=True,
            cwd=repo_root(),
        ).returncode
        == 0
    )


def production_deployments(payload, limit: int) -> list[dict]:
    """Filter a ``/deployments`` response to Production records.

    ``environment`` in a record is capitalized and may carry a project suffix
    (``Production – arkadia-prism``), so it is matched on the production prefix
    rather than by equality: an equality test admits only the bare form and
    silently drops the rest. A record is accepted only when it names a full
    40-char source SHA, so a truncated or absent ``sha`` cannot be compared as
    if it were identity.
    """
    if not isinstance(payload, list):
        return []
    out = []
    for d in payload:
        if not isinstance(d, dict) or not isinstance(d.get("environment"), str):
            continue
        if not PRODUCTION_ENVIRONMENT_RE.match(d["environment"]):
            continue
        sha = d.get("sha") or ""
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            continue
        out.append(d)
    return out[:limit]


def classify_deployment_identity(main_sha: str, prod: list[dict]) -> str:
    """Is the newest Production deployment's source SHA the current main?

    The question is *whether the deploy names main*, not *whether a deploy
    exists*. Deployments on record are older than main whenever main has moved
    since the last successful production build, so a false answer is the normal
    state and must read as a stale deploy -- not as a missing link.
    """
    if not prod:
        return "UNKNOWN"
    return "VERIFIED" if prod[0].get("sha") == main_sha else "STALE"


def lineage_closed(closure: list[dict]) -> bool:
    """True only when every candidate was checked *and* is a descendant."""
    return bool(closure) and all(c.get("descendant_of_last_build_input") for c in closure)


def classify_source_lineage(closure: list[dict], stale: list[str], prod: list[dict]) -> str:
    """Do all candidate deployments compile identical frontend source?

    "Closed" means every candidate is a descendant of the last commit that
    touched a frontend build input -- so the artifact cannot discriminate
    between them, and the alias->SHA question is immaterial to *source*
    lineage. A candidate that does not exist locally cannot be checked and
    therefore cannot close the argument.

    Source closure is *not* a marker observation. It says every candidate would
    compile the same literals; it does not say any of those literals was read
    from a served artifact. Claiming "marker set matches" from closure alone is
    the defect this repairs: the verdict must name only what was observed.
    """
    if not prod or not closure or any(c.get("descendant_of_last_build_input") is None for c in closure):
        return "UNKNOWN"
    if lineage_closed(closure) and not stale:
        return "VERIFIED (source closed; marker set NOT observed)"
    return "UNKNOWN"


def classify_marker_oracle(app: str | None, observed: dict[str, int] | None, stale: list[str]) -> str:
    """Did the harness actually read a marker set off a served artifact?

    ``app`` is the application the served artifact belongs to (from the
    deployment label), or ``None`` when it could not be determined. ``observed``
    is the per-marker occurrence count taken from the fetched document, or
    ``None`` when nothing was fetched.

    The marker list describes ``MARKER_APP``. An artifact belonging to any other
    application cannot be scored against it at all: every literal reads 0 because
    the surface is not in that build, which is a category error, not a
    regression. Agreement additionally requires a positive reading -- an entirely
    absent marker set is evidence that the artifact is not this app, never
    evidence that it agrees. Without these distinctions an absent app and a
    correct app produced the same verdict, which is exactly how a false
    ``VERIFIED`` was reachable.
    """
    if app is None:
        return f"NOT OBSERVED (served app undetermined; markers describe '{MARKER_APP}')"
    if app != MARKER_APP:
        return f"NOT OBSERVED (artifact is '{app}'; markers describe '{MARKER_APP}')"
    if observed is None:
        return "UNKNOWN (no artifact fetched)"
    if stale:
        return "UNKNOWN (marker list stale: literals absent from source)"
    if not observed:
        return "UNKNOWN (no markers read)"
    if all(count > 0 for count in observed.values()):
        return "VERIFIED (marker set observed in served artifact)"
    absent = sorted(k for k, v in observed.items() if v == 0)
    return f"CONTRADICTED (markers absent from served artifact: {', '.join(absent)})"


def api(path: str, token: str | None):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "arkadia-gate2-observation",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"__error__": f"HTTP {e.code}"}
    except Exception as e:  # network boundary
        return {"__error__": type(e).__name__}


def head(url: str) -> dict:
    """Observe a URL without following redirects."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "arkadia-gate2-observation"})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=30) as r:
            return {"status": r.status, "headers": {k.lower(): v for k, v in r.headers.items()}, "body": r.read()}
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "headers": {k.lower(): v for k, v in (e.headers or {}).items()},
            "body": b"",
            "location": (e.headers or {}).get("Location"),
        }
    except Exception as e:
        return {"status": None, "error": type(e).__name__, "body": b""}


def markers_in(text: str) -> dict[str, int]:
    return {m: text.count(m) for m in MARKERS}


def source_markers_present() -> dict[str, bool]:
    """Confirm each literal still exists in the working tree, so a stale list is
    detected rather than silently trusted."""
    root = repo_root()
    present = {}
    for literal, (prov, expected, _) in MARKERS.items():
        hit = False
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, "web", "public_prism", "src")):
            for fn in filenames:
                if not fn.endswith((".ts", ".tsx")):
                    continue
                try:
                    with open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore") as fh:
                        if literal in fh.read():
                            hit = True
                            break
                except OSError:
                    continue
            if hit:
                break
        present[literal] = hit
    return present


def local_bundle_markers() -> dict[str, int] | None:
    """Marker set from a local build, if one exists. Optional corroboration only."""
    dist = os.path.join(repo_root(), "web", "public_prism", "dist", "assets")
    if not os.path.isdir(dist):
        return None
    chunks = []
    for fn in os.listdir(dist):
        if fn.endswith(".js"):
            with open(os.path.join(dist, fn), encoding="utf-8", errors="ignore") as fh:
                chunks.append(fh.read())
    if not chunks:
        return None
    return markers_in("".join(chunks))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit machine-readable output")
    ap.add_argument("--limit", type=int, default=12, help="production deployments to inspect")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("github_token")
    report: dict = {"boundaries": {}, "markers": {}}

    # ---- link 1: current main ------------------------------------------------
    main_sha = resolve_main()
    report["main_sha"] = main_sha
    report["boundaries"]["current main resolved"] = "VERIFIED" if re.fullmatch(r"[0-9a-f]{40}", main_sha) else "UNKNOWN"

    # ---- link 2: deployment identity ----------------------------------------
    # Fetch UNFILTERED. The server-side `?environment=Production` predicate
    # matches the bare label only and returns a different (older) cohort than the
    # project-suffixed `Production – arkadia-prism` records, so a filtered query
    # can never see the newest Production deployment. Filter client-side.
    deps = api(f"/deployments?per_page={max(args.limit * 5, 50)}", token)
    if isinstance(deps, dict) and "__error__" in deps:
        report["boundaries"]["main -> deployment identity"] = "BLOCKED"
        report["deployments_error"] = deps["__error__"]
        prod = []
    else:
        prod = production_deployments(deps, args.limit)
        report["boundaries"]["main -> deployment identity"] = classify_deployment_identity(main_sha, prod)
    report["production_deployments"] = [
        {"id": d["id"], "sha": d["sha"], "created_at": d["created_at"], "ref": d.get("ref")} for d in prod
    ]
    report["newest_production_sha"] = prod[0]["sha"] if prod else None
    report["newest_production_created_at"] = prod[0]["created_at"] if prod else None

    # ---- link 3: deployment-specific observation ----------------------------
    # The deployment-specific host is published on the deployment *status*, not on
    # the deployment record itself, and its hostname is a provider hash -- it is
    # not derivable from the deployment id. Read it; never guess it.
    dep_url = None
    if prod:
        statuses = api(f"/deployments/{prod[0]['id']}/statuses", token)
        if isinstance(statuses, list):
            for st in statuses:
                if st.get("environment_url"):
                    dep_url = st["environment_url"]
                    break
    report["deployment_url"] = dep_url
    if dep_url:
        obs = head(dep_url)
        report["deployment_url_status"] = obs.get("status")
        loc = obs.get("location") or ""
        report["deployment_url_location"] = loc[:120]
        report["boundaries"]["deployment build output observed"] = (
            "VERIFIED" if obs.get("status") == 200 else "BLOCKED"
        )
        if obs.get("status") in (301, 302, 303, 307, 308):
            report["deployment_url_ssologin"] = "vercel.com/sso" in loc or "/sso-api" in loc
    else:
        report["boundaries"]["deployment build output observed"] = "UNKNOWN"

    # ---- link 4: alias observation ------------------------------------------
    alias = head(ALIAS)
    report["alias_status"] = alias.get("status")
    report["boundaries"]["alias reachable"] = "VERIFIED" if alias.get("status") == 200 else "FAILED"
    html = alias.get("body", b"").decode("utf-8", "ignore")
    assets = sorted(set(re.findall(r"assets/index-[A-Za-z0-9_-]+\.(?:js|css)", html)))
    report["alias_assets"] = assets
    report["alias_headers"] = {
        k: alias.get("headers", {}).get(k)
        for k in ("age", "last-modified", "x-vercel-cache", "x-vercel-id", "etag")
        if alias.get("headers", {}).get(k)
    }

    # ---- link 5: marker-set lineage -----------------------------------------
    js = next((a for a in assets if a.endswith(".js")), None)
    if js:
        bundle = head(ALIAS + js)
        text = bundle.get("body", b"").decode("utf-8", "ignore")
        report["alias_bundle"] = js
        report["alias_bundle_bytes"] = len(bundle.get("body", b""))
        report["markers"]["deployed"] = markers_in(text)
        report["markers"]["deployed_total"] = sum(report["markers"]["deployed"].values())

    present = source_markers_present()
    report["markers"]["source_literal_present"] = present
    stale = [m for m, (_, expected, _) in MARKERS.items() if expected and not present[m]]
    report["markers"]["stale_list"] = stale

    lb = local_bundle_markers()
    if lb is not None:
        report["markers"]["local_build"] = lb

    # SG-04 regression: expected in source, absent from artifact.
    dep_m = report["markers"].get("deployed", {})
    sg04_src = present.get("activity-runtime-draft.v1:", False)
    sg04_dep = dep_m.get("activity-runtime-draft.v1:", 0)
    report["sg04"] = {
        "in_source": sg04_src,
        "in_deployed_artifact": sg04_dep,
        "regression": bool(sg04_src and sg04_dep == 0),
    }

    # ---- link 6: source-lineage closure -------------------------------------
    # The observed Production deployment names its app in the environment label;
    # the closure argument is only meaningful over that app's build input.
    deployed_app = frontend_of(prod[0]["environment"]) if prod else None
    report["deployed_app"] = deployed_app
    app_for_closure = deployed_app or MARKER_APP
    if deployed_app is None and prod:
        report["deployed_app_error"] = (
            f"environment '{prod[0]['environment']}' names no known frontend; "
            "build<->source lineage cannot be scoped"
        )
    last_sha, last_date, last_subject = last_build_input_commit(app_for_closure)
    report["last_build_input_commit"] = {
        "app": app_for_closure, "sha": last_sha, "date": last_date, "subject": last_subject
    }
    closure = []
    for d in prod:
        sha = d["sha"]
        # A candidate that is not in the local object store cannot be tested;
        # record that as unproven (None) rather than False, so a missing object
        # is not silently read as "diverged" or as "closed".
        checked = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True, cwd=repo_root()
        ).returncode == 0
        closure.append({
            "sha": sha,
            "descendant_of_last_build_input": is_ancestor(last_sha, sha) if checked else None,
        })
    report["source_lineage_closure"] = closure
    all_closure = lineage_closed(closure)
    report["source_lineage_closed"] = all_closure

    # If every candidate compiles identical frontend source, the artifact cannot
    # discriminate between them -- so alias->SHA is immaterial to source lineage.
    report["boundaries"]["alias -> deployment SHA binding"] = (
        "UNKNOWN (immaterial: all candidates share frontend source)" if all_closure else "UNKNOWN"
    )
    report["boundaries"]["build <-> source lineage"] = classify_source_lineage(closure, stale, prod)
    report["boundaries"]["marker-set oracle"] = classify_marker_oracle(
        report.get("deployed_app") or MARKER_APP,
        report["markers"].get("deployed"),
        stale,
    )
    report["boundaries"]["browser-rendered UI correctness"] = "UNKNOWN"
    report["boundaries"]["production acceptance"] = "NOT CLAIMED (human authority)"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=False))
        return 0

    # ---- human-readable glance ----------------------------------------------
    print("ARKADIA ENGINEERING -- GATE-02 PRODUCTION OBSERVATION")
    print("=" * 62)
    print(f"main SHA                : {main_sha}")
    if prod:
        print(f"newest Production deploy: {prod[0]['sha'][:12]}  id={prod[0]['id']}  {prod[0]['created_at']}")
        print(f"  deploy SHA == main    : {prod[0].get('sha') == main_sha}"
              + ("" if prod[0].get("sha") == main_sha else "  (deploy predates main -> STALE)"))
    else:
        print(f"newest Production deploy: UNAVAILABLE {report.get('deployments_error', '')}")
    print()
    print("ALIAS OBSERVATION")
    print(f"  {ALIAS} -> HTTP {report['alias_status']}")
    for k, v in report["alias_headers"].items():
        print(f"    {k}: {v}")
    print(f"  manifest: {', '.join(assets) or 'none'}")
    if "alias_bundle" in report:
        print(f"  bundle  : {report['alias_bundle']} ({report['alias_bundle_bytes']} bytes)")
    if dep_url:
        print(f"  deployment-specific URL -> HTTP {report.get('deployment_url_status')}"
              + (" (SSO redirect)" if report.get("deployment_url_status") != 200 else ""))
    print()
    print("MARKER-SET LINEAGE (literal : deployed / expected)")
    print(f"  artifact app: {report.get('deployed_app') or 'UNDETERMINED'}"
          f"   harness markers describe: {MARKER_APP}")
    if report.get("deployed_app") != MARKER_APP:
        print("  !! the served artifact is a DIFFERENT application than the marker list;")
        print("     a zero count below is 'not this app', not a regression and not agreement.")
    for literal, (prov, expected, note) in MARKERS.items():
        d = dep_m.get(literal, 0)
        flag = ""
        if expected and d == 0:
            flag = "  <-- ABSENT"
        if not expected and d:
            flag = "  <-- UNEXPECTED"
        print(f"  {literal:<38} {d}  ({'expect>0' if expected else 'expect 0'}){flag}")
    if lb is not None:
        match = all(lb.get(k, 0) == dep_m.get(k, 0) for k in MARKERS)
        if report.get("deployed_app") == MARKER_APP:
            print(f"  local build marker set matches deployed: {match}")
        else:
            print("  local build marker set matches deployed: NOT COMPARABLE"
                  f" (deployed app is '{report.get('deployed_app')}')")
    if stale:
        print(f"  !! STALE marker list -- literals gone from source: {stale}")
    print()
    print("SOURCE-LINEAGE CLOSURE")
    print(f"  last commit touching a frontend build input: {last_sha[:12]}  {last_date}")
    print(f"    {last_subject}")
    print(f"  all {len(closure)} candidate Production SHAs are its descendants: {all_closure}")
    unchecked = [c["sha"][:12] for c in closure if c.get("descendant_of_last_build_input") is None]
    if unchecked:
        print(f"  !! {len(unchecked)} candidate SHA(s) not in local object store, unproven: {unchecked}")
    if all_closure:
        print("  => every candidate compiles byte-identical frontend source;")
        print("     the artifact cannot discriminate between them, so alias->SHA")
        print("     is immaterial to source lineage even though it is unobservable.")
    print()
    print("SG-04 REGRESSION")
    if report.get("deployed_app") != MARKER_APP:
        print(f"  in source: {sg04_src}   NOT EVALUABLE against artifact: the served")
        print(f"  document is the '{report.get('deployed_app')}' app, which has no SG-04 surface.")
    else:
        print(f"  in source: {sg04_src}   in deployed artifact: {sg04_dep}"
              f"   => REGRESSION: {report['sg04']['regression']}")
    print()
    print("BOUNDARY CLASSIFICATION")
    for k, v in report["boundaries"].items():
        print(f"  {k:<42} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
