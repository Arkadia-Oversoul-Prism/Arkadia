"""Operational documents must not present a retired deployment host as production.

ADR-016 establishes **one** canonical deployment. `architecture/runtime_manifest.yaml`
is the machine-readable record of which host that is: it carries
`canonical_deployment.canonical_deployment_identity.service_url` and it marks every
other observed host with a status (`legacy_noncanonical`, `archived_noncanonical`).

Measured on `main` @ `bb19aabd` (2026-11-24), that record and the operational
documents disagreed. The manifest marks `arkadia-kw64.onrender.com` as
`legacy_noncanonical`, and `api/main.py`'s production CORS default is the canonical
`arkadia-qzu4.onrender.com` — yet:

* `MISSION.md` said `Backend | **LIVE** — https://arkadia-kw64.onrender.com`, told the
  next session to set `VITE_API_URL` to it, and claimed "All production references
  point to" it (measurably false: `git grep -l arkadia-qzu4.onrender.com | wc -l`
  reported **85** tracked files naming the canonical host);
* `NEXT_AGENT.md` recorded "Production proof (Gate A) | **PASSING**" on that host;
* `UPTIMEROBOT_SETUP.md` instructed an operator to point an uptime monitor at it;
* `.bootstrap/01_STATE.md` reported "Production: LIVE at" it;
* `.agents/memory/phase0-security.md` stated as a **rule** that the only allowed
  production CORS origin is that host, which contradicts `api/main.py`;
* the two Android READMEs offered it as the backend endpoint.

These are not stylistic: an agent or operator following them targets a host the
canonical record does not own. The unit of judgement is a paragraph, or a single
markdown table row: a paragraph that names a retired host must also name the canonical
origin (or mark the host historical), so a document cannot say "LIVE" on a retired host
in one paragraph and name the canonical origin in another. A table row is its own
unit, because a row *is* the claim.

Scope, stated rather than implied: the operational surface is every tracked `*.md`
outside the two record trees (`archive/`, `docs/`), which are dated records by
construction and legitimately quote the host that was canonical when they were
written (`docs/ARKADIA_CANONICAL_RUNTIME_CONTRACT.md` is a frozen Phase-4B proof).
A new *operational* guide placed under `docs/` would therefore not be judged — a
known limitation, recorded rather than hidden.

The oracle is read from the manifest, never restated here: if the canonical host
moves, this guard follows it, and a stale list cannot make the check vacuous.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "architecture" / "runtime_manifest.yaml"

#: Trees that hold dated records rather than operational instruction.
RECORD_TREES = ("archive/", "docs/")

#: Manifest statuses that mean "observed, but not canonical".
RETIREMENT_STATUSES = frozenset({"legacy_noncanonical", "archived_noncanonical"})

#: Words that place a retired-host mention in its historical context. A mention
#: carrying one of these is telling the reader the host is *not* the target.
RETIREMENT_MARKERS = (
    "historical",
    "retired",
    "legacy",
    "superseded",
    "non-canonical",
    "not canonical",
    "archived",
    "no longer",
    "old ",
    "stale",
)

HOST_RE = re.compile(r"\barkadia-[a-z0-9-]+\.onrender\.com\b")


def _manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def _canonical() -> dict:
    return _manifest()["canonical_deployment"]


def canonical_host() -> str:
    url = _canonical()["canonical_deployment_identity"]["service_url"]
    host = urlparse(url).hostname
    assert host, f"the manifest's canonical service_url is not a URL: {url!r}"
    return host


def retired_hosts() -> set[str]:
    """Every host the manifest records as observed-but-not-canonical."""
    record = _canonical()
    observed = record.get("runtime_verification", {}).get("observed") or []
    hosts = {
        entry["host"]
        for entry in observed
        if entry.get("status") in RETIREMENT_STATUSES
    }
    hosts |= set(record.get("historical_targets") or [])
    return hosts


def operational_documents() -> list[str]:
    """The tracked markdown an operator or agent reads for current guidance."""
    result = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"git ls-files failed: {result.stderr.strip()}"
    return sorted(
        path
        for path in result.stdout.split()
        if not path.startswith(RECORD_TREES)
    )


def _blocks(text: str):
    """Yield ``(first_line_number, block_text)`` for a markdown body.

    The unit is a paragraph, or a single table row. Prose wraps, so a per-line
    unit would force every wrapped line that mentions a retired host to repeat the
    canonical origin — the guard would dictate formatting rather than judge claims.
    A table row is its own block because a row *is* the claim; otherwise one correct
    row would vouch for a wrong one in the same table.
    """
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.lstrip().startswith("|"):
            yield index + 1, line
            index += 1
            continue
        start = index
        block = []
        while (
            index < len(lines)
            and lines[index].strip()
            and not lines[index].lstrip().startswith("|")
        ):
            block.append(lines[index])
            index += 1
        yield start + 1, "\n".join(block)


def offences(text: str, canonical: str, retired: set[str]) -> list[str]:
    """Blocks that present a retired host without naming the canonical origin.

    A block is an offence when it names a retired host and neither names the
    canonical host nor marks the retired host as historical. Both escapes are
    visible to the reader, which is the property being protected.
    """
    found = []
    for start, block in _blocks(text):
        hosts = set(HOST_RE.findall(block))
        if not hosts & retired:
            continue
        if canonical in hosts:
            continue
        if any(marker in block.lower() for marker in RETIREMENT_MARKERS):
            continue
        found.append(f"{start}: {' '.join(block.split())}")
    return found


# ─────────────────────────────────────────────────────────────────────────────
# The oracle
# ─────────────────────────────────────────────────────────────────────────────


def test_the_manifest_names_a_canonical_origin_and_its_retired_hosts():
    canonical = canonical_host()
    retired = retired_hosts()
    assert canonical.endswith(".onrender.com"), canonical
    assert retired, (
        "the manifest records no retired host, so this guard would be vacuous"
    )


def test_the_canonical_origin_is_not_also_recorded_as_retired():
    assert canonical_host() not in retired_hosts(), (
        "the manifest marks its own canonical origin as retired"
    )


def test_the_domain_covers_the_operational_surface():
    documents = operational_documents()
    assert documents, "git ls-files returned no markdown outside the record trees"
    assert not any(path.startswith(RECORD_TREES) for path in documents)
    # The domain must reach the trees that actually carry current guidance, or a
    # filter defect would leave the check below vacuous rather than red.
    for tree in ("", ".bootstrap/", ".agents/memory/"):
        assert _covers(documents, tree), f"the domain reaches nothing under {tree!r}"


def _covers(documents: list[str], prefix: str) -> bool:
    if not prefix:
        return any("/" not in path for path in documents)
    return any(path.startswith(prefix) for path in documents)


# ─────────────────────────────────────────────────────────────────────────────
# The invariant
# ─────────────────────────────────────────────────────────────────────────────


def test_no_operational_document_presents_a_retired_host_without_the_canonical_origin():
    canonical = canonical_host()
    retired = retired_hosts()
    report = []
    for path in operational_documents():
        text = (ROOT / path).read_text(encoding="utf-8")
        for line in offences(text, canonical, retired):
            report.append(f"{path}:{line}")
    assert not report, (
        "operational documents present a retired deployment host without naming the "
        f"canonical origin ({canonical}):\n  " + "\n  ".join(report)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Negative and silence controls — the detector must bite, and only where it should
# ─────────────────────────────────────────────────────────────────────────────

#: The exact pre-repair line from `MISSION.md` @ `bb19aabd`. It is preserved
#: verbatim so the control cannot be softened by editing the document it came from.
PRE_REPAIR_LINE = "| Backend | **LIVE** — https://arkadia-kw64.onrender.com |"


def test_control_the_pre_repair_claim_is_reported():
    found = offences(PRE_REPAIR_LINE, "arkadia-qzu4.onrender.com", {"arkadia-kw64.onrender.com"})
    assert found, "the detector does not flag the defect it exists to catch"


def test_control_naming_the_canonical_origin_is_not_reported():
    line = "| Backend | **LIVE** — https://arkadia-qzu4.onrender.com |"
    assert offences(line, "arkadia-qzu4.onrender.com", {"arkadia-kw64.onrender.com"}) == []


def test_control_marking_the_host_as_historical_is_not_reported():
    line = (
        "The legacy host https://arkadia-kw64.onrender.com is retained only as a "
        "historical record."
    )
    assert offences(line, "arkadia-qzu4.onrender.com", {"arkadia-kw64.onrender.com"}) == []


def test_control_an_unrelated_host_is_not_reported():
    line = "| Backend | **LIVE** — https://example.onrender.com |"
    assert offences(line, "arkadia-qzu4.onrender.com", {"arkadia-kw64.onrender.com"}) == []


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
