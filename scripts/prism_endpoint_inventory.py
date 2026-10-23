#!/usr/bin/env python3
"""Prism reconciliation inventory — the enduring acceptance instrument.

Counts the endpoint gap between what the archived Prism used and what the
current console references, so a completed slice reduces a *measured* number
rather than improving a headline.

Three sets, all derived at run time from live sources:

  legacy   paths referenced by ``archive/frontend/arkadia-prism/web/public_prism/src``
  served   paths in the real FastAPI route table (``app.openapi()``)
  console  paths referenced by ``web/arkadia_console/src``

The reconciliation gap is reported on two bases, because they answer different
questions and differ by more than 3x:

  legacy & served - console   capabilities the archived product actually used
                              that the console does not reach. This is the
                              mission-relevant number and the stable one: it
                              moves by at most 1 across the normalization
                              variants in ``--matrix``.
  served - console            every served path the console does not reach.
                              Includes capability the archive never used, so it
                              is a coverage figure, not a reconciliation target.

Normalization is a parameter, not a hidden assumption: ``--normalize id``
collapses path parameters to ``{id}`` so ``/api/x/{post_id}`` and
``/api/x/{id}`` are one endpoint; ``raw`` compares literal text. The chosen
variant is always printed with the result, because the same repository yields
70 and 248 depending on the definition — a count quoted without its variant is
not reproducible.

A path appearing in a registry is NOT reconciliation. This instrument measures
*reachability*; ``docs/control-plane/evidence/prism-rec-voice-readaloud-01``
records what it takes to count an endpoint as reconciled.

Read-only. No network. Exits non-zero only on a usage error.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

LEGACY_ROOT = "archive/frontend/arkadia-prism/web/public_prism/src"
CONSOLE_ROOT = "web/arkadia_console/src"

# Only these prefixes are in scope: the reconciliation is about the product's
# own API surface, not framework or static-asset paths.
PATH_PREFIXES = ("/api", "/solspire")

# Trailing characters a path can pick up from surrounding source punctuation.
_TRAILING = ".,;:)\"'`\\"

PATH_RE = re.compile(r"(/(?:api|solspire)/[A-Za-z0-9_\-{}/.]*)")

# The console does not surface the Engineering Lab through this inventory's
# question; the Lab is a first-class console surface with its own contract.
EXCLUDED_PREFIXES = ("/api/lab",)


def _tracked(root: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", root],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [str(REPO_ROOT / p) for p in out]


def _normalize(path: str, mode: str) -> str:
    path = path.rstrip(_TRAILING)
    if mode == "id":
        path = re.sub(r"\{[^}]*\}", "{id}", path)
    return path


def paths_referenced_by(files: list[str], mode: str) -> set[str]:
    found: set[str] = set()
    for name in files:
        try:
            text = Path(name).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in PATH_RE.findall(text):
            found.add(_normalize(match, mode))
    return found


def served_paths(mode: str) -> set[str]:
    """The real route table, not a source grep.

    A literal search under-reports prefix-composed routers (``/api/lab/*`` is
    mounted from ``APIRouter(prefix="/api/lab")``), so the app's own OpenAPI
    document is the oracle. Importing the app needs the application
    dependencies (see ``requirements.txt``).
    """
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from api.main import app  # noqa: PLC0415 — deliberate: heavy import, only when needed

    out: set[str] = set()
    for path in app.openapi()["paths"]:
        if not path.startswith(PATH_PREFIXES):
            continue
        if path.startswith(EXCLUDED_PREFIXES):
            continue
        out.add(_normalize(path, mode))
    return out


def compute(mode: str) -> dict:
    legacy = paths_referenced_by(_tracked(LEGACY_ROOT), mode)
    console = paths_referenced_by(_tracked(CONSOLE_ROOT), mode)
    served = served_paths(mode)

    used = served & legacy
    return {
        "normalize": mode,
        "sizes": {
            "legacy": len(legacy),
            "served": len(served),
            "console": len(console),
        },
        # The mission-relevant figure.
        "gap_legacy_served": sorted(used - console),
        # Coverage figure; includes capability the archive never used.
        "gap_served_only": sorted(served - console),
        "clusters": dict(
            sorted(
                collections.Counter(
                    "/".join(p.split("/")[:3]) for p in (used - console)
                ).most_common()
            )
        ),
    }


def _revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--normalize", choices=("id", "raw"), default="id")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--matrix",
        action="store_true",
        help="show every normalization variant, so the quoted count carries its definition",
    )
    ap.add_argument("--list", action="store_true", help="list the gap paths")
    args = ap.parse_args(argv)

    if args.matrix:
        rows = [compute(m) for m in ("id", "raw")]
        if args.json:
            print(json.dumps({"revision": _revision(), "variants": rows}, indent=2))
            return 0
        print(f"revision {_revision()}")
        print(f"{'normalize':<12}{'legacy':>8}{'served':>8}{'console':>9}{'gap(l&s)':>10}{'gap(s)':>9}")
        for r in rows:
            s = r["sizes"]
            print(
                f"{r['normalize']:<12}{s['legacy']:>8}{s['served']:>8}{s['console']:>9}"
                f"{len(r['gap_legacy_served']):>10}{len(r['gap_served_only']):>9}"
            )
        print()
        print("gap(l&s) is the reconciliation target and is stable across variants.")
        print("gap(s) is coverage and varies with the definition — always name the variant.")
        return 0

    result = compute(args.normalize)
    result["revision"] = _revision()

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    s = result["sizes"]
    print(f"revision  {result['revision']}")
    print(f"normalize {result['normalize']}")
    print(f"legacy {s['legacy']}   served {s['served']}   console {s['console']}")
    print()
    print(f"gap (legacy & served, not in console): {len(result['gap_legacy_served'])}")
    print(f"gap (served only, not in console):    {len(result['gap_served_only'])}")
    print()
    print("top clusters:")
    for k, v in list(result["clusters"].items())[:20]:
        print(f"  {v:3}  {k}")
    if args.list:
        print()
        for p in result["gap_legacy_served"]:
            print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
