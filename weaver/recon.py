"""WEAVER-K1 — deterministic repository reconnaissance (no LLM, no authorization)."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"

# Product/architecture boundaries (summary only; enforcement remains PassSpec/K0.1)
DEFAULT_PROTECTED = [
    "api/auth.py",
    "api/ (ownership / isolation)",
    "providers/",
    "api/key_pool.py",
    "solspire/",
    "ReasoMate / api/messages.py",
    "Oracle",
    "Firebase auth",
    "arkadia-android/",
    "sonata-android/",
    "tests/architecture/",
    "deployment (vercel/render)",
]


def _run(cmd: list[str], cwd: str = ".") -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def git_identity(repo_root: str = ".") -> dict[str, Any]:
    _, head, _ = _run(["git", "rev-parse", "HEAD"], repo_root)
    _, branch, _ = _run(["git", "branch", "--show-current"], repo_root)
    rc, origin, _ = _run(["git", "rev-parse", "origin/main"], repo_root)
    origin_sha = origin if rc == 0 else None
    _, status, _ = _run(["git", "status", "--short"], repo_root)
    clean = status == ""
    ahead, behind = 0, 0
    if origin_sha:
        rc2, ab, _ = _run(["git", "rev-list", "--left-right", "--count", "HEAD...origin/main"], repo_root)
        if rc2 == 0 and ab:
            parts = ab.split()
            if len(parts) >= 2:
                ahead, behind = int(parts[0]), int(parts[1])
    _, remote_url, _ = _run(["git", "remote", "get-url", "origin"], repo_root)
    return {
        "remote": remote_url or None,
        "branch": branch or None,
        "head_sha": head or None,
        "origin_sha": origin_sha,
        "ahead": ahead,
        "behind": behind,
        "working_tree_clean": clean,
        "divergent": bool(ahead or behind) or (origin_sha is not None and head != origin_sha),
    }


def recent_lineage(repo_root: str = ".", n: int = 8) -> list[dict[str, str]]:
    rc, out, _ = _run(["git", "log", f"-n{n}", "--pretty=%H\t%s"], repo_root)
    if rc != 0 or not out:
        return []
    rows = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        sha, msg = line.split("\t", 1)
        rows.append({"sha": sha, "message": msg})
    return rows


def architecture_summary(repo_root: str = ".") -> dict[str, Any]:
    layer_map_path = Path(repo_root) / "tests" / "architecture" / "LAYER_MAP.py"
    if not layer_map_path.is_file():
        return {"status": "unknown", "source": None, "layers": {}}
    # Parse LAYER_MAP dict without importing (avoids side effects)
    text = layer_map_path.read_text(encoding="utf-8", errors="replace")
    layers: dict[str, list[str]] = {}
    # crude extraction of "path": number pairs
    import re

    for m in re.finditer(r'["\']([^"\']+)["\']\s*:\s*(\d+)', text):
        path, num = m.group(1), int(m.group(2))
        layers.setdefault(str(num), []).append(path)
    names = {
        "0": "presentation",
        "1": "api",
        "2": "runtime_core",
        "3": "knowledge_identity_provider",
        "4": "storage",
        "5": "constitution",
    }
    return {
        "status": "ok",
        "source": "tests/architecture/LAYER_MAP.py",
        "layer_names": names,
        "prefixes_by_layer": {names.get(k, k): v[:20] for k, v in sorted(layers.items())},
    }


def weaver_capabilities(repo_root: str = ".") -> list[dict[str, str]]:
    root = Path(repo_root) / "weaver"
    catalog = [
        ("pass_spec", "weaver/pass_spec.py", "authorization object"),
        ("session_kernel", "weaver/session_kernel.py", "lifecycle gates + publication"),
        ("agent", "weaver/agent.py", "authorized modification path"),
        ("autonomy_guard", "weaver/autonomy/guard.py", "scope / kill-switch"),
        ("recursive_engine", "weaver/recursive.py", "bounded recursive steps"),
        ("git_operations", "weaver/git_ops.py", "commit/push primitives"),
        ("provider_dispatch", "weaver/llm.py", "LLM provider dispatch"),
        ("checkpoint_system", "weaver/session_kernel.py", "durable checkpoints"),
        ("recon", "weaver/recon.py", "deterministic reconnaissance"),
    ]
    out = []
    for key, path, role in catalog:
        status = "present" if (Path(repo_root) / path).is_file() else "missing"
        out.append({"id": key, "path": path, "status": status, "role": role})
    return out


def list_checkpoints(repo_root: str = ".") -> dict[str, Any]:
    ck_dir = Path(repo_root) / "data" / "weaver" / "checkpoints"
    items = []
    if ck_dir.is_dir():
        for p in sorted(ck_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.name.startswith("."):
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                data = {"status": "unreadable"}
            items.append(
                {
                    "path": str(p.relative_to(repo_root)).replace("\\", "/"),
                    "pass_id": data.get("pass_id"),
                    "status": data.get("status"),
                    "result_sha": data.get("result_sha"),
                    "remote_sha": data.get("remote_sha"),
                    "publication_status": data.get("publication_status"),
                    "timestamp": data.get("timestamp"),
                }
            )
    current = items[0] if items else None
    return {"count": len(items), "current": current, "recent": items[:5]}


def last_verified_pass(lineage: list[dict[str, str]], checkpoints: dict[str, Any]) -> dict[str, Any]:
    # Prefer latest checkpoint bound to a SHA; fall back to first lineage entry
    cur = checkpoints.get("current")
    if cur and cur.get("result_sha"):
        return {
            "source": "checkpoint",
            "pass_id": cur.get("pass_id"),
            "sha": cur.get("result_sha"),
            "status": cur.get("status"),
            "publication_status": cur.get("publication_status"),
        }
    if lineage:
        return {
            "source": "git_log",
            "pass_id": None,
            "sha": lineage[0]["sha"],
            "message": lineage[0]["message"],
            "status": None,
            "publication_status": None,
        }
    return {"source": "unknown", "sha": None}


def test_inventory(repo_root: str = ".") -> list[str]:
    tests = Path(repo_root) / "tests"
    paths = []
    if not tests.is_dir():
        return paths
    preferred = [
        "tests/architecture",
        "tests/test_weaver_k0.py",
        "tests/test_weaver_context.py",
        "tests/test_recursive_init.py",
        "tests/test_git_ops.py",
        "tests/test_autonomy_guard.py",
        "tests/test_key_pool.py",
    ]
    for pref in preferred:
        p = Path(repo_root) / pref
        if p.is_file():
            paths.append(pref)
        elif p.is_dir():
            for f in sorted(p.rglob("test_*.py")):
                paths.append(str(f.relative_to(repo_root)).replace("\\", "/"))
    # any other test_weaver_*
    for f in sorted(tests.glob("test_weaver_*.py")):
        rel = str(f.relative_to(repo_root)).replace("\\", "/")
        if rel not in paths:
            paths.append(rel)
    return paths


def build_inventory(repo_root: str = ".") -> list[dict[str, Any]]:
    out = []
    pkg = Path(repo_root) / "web" / "public_prism" / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        pm = data.get("packageManager") or (
            "pnpm" if (pkg.parent / "pnpm-lock.yaml").is_file() else "npm"
        )
        scripts = data.get("scripts") or {}
        out.append(
            {
                "surface": "web/public_prism",
                "package_manager": pm,
                "build_command": scripts.get("build"),
                "availability": "declared",
            }
        )
    if (Path(repo_root) / "vercel.json").is_file():
        out.append({"surface": "vercel.json", "package_manager": None, "build_command": None, "availability": "config_present"})
    return out


def topology(repo_root: str = ".") -> list[str]:
    interesting = [
        "api",
        "kernel",
        "providers",
        "solspire",
        "web/public_prism",
        "data",
        "vault",
        "weaver",
        "tests",
        "arkadia-android",
        "sonata-android",
        "docs",
    ]
    present = []
    root = Path(repo_root)
    for name in interesting:
        if (root / name).exists():
            present.append(name)
    return present


def build_context_packet(repo_root: str = ".") -> dict[str, Any]:
    """Deterministic Context Packet — facts and references only."""
    repo = git_identity(repo_root)
    lineage = recent_lineage(repo_root)
    checkpoints = list_checkpoints(repo_root)
    arch = architecture_summary(repo_root)
    packet = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": repo,
        "branch": repo.get("branch"),
        "head_sha": repo.get("head_sha"),
        "origin_sha": repo.get("origin_sha"),
        "ahead": repo.get("ahead"),
        "behind": repo.get("behind"),
        "working_tree_clean": repo.get("working_tree_clean"),
        "architecture": arch,
        "topology": topology(repo_root),
        "weaver": weaver_capabilities(repo_root),
        "last_verified_pass": last_verified_pass(lineage, checkpoints),
        "checkpoint_state": checkpoints,
        "protected_boundaries": list(DEFAULT_PROTECTED),
        "available_tests": test_inventory(repo_root),
        "available_builds": build_inventory(repo_root),
        "recent_lineage": lineage,
        "available_providers": _provider_inventory(),
        "next_action": "awaiting human authorization",
        "authorization": {
            "note": "CONTEXT ≠ AUTHORIZATION. This packet never grants a PassSpec.",
            "pass_spec_required": True,
        },
        "stale_detection": {
            "bound_head_sha": repo.get("head_sha"),
            "bound_origin_sha": repo.get("origin_sha"),
            "instruction": "If HEAD or origin/main differs from bound_* fields, this packet is stale.",
        },
    }
    return packet


def is_stale(packet: dict[str, Any], repo_root: str = ".") -> bool:
    current = git_identity(repo_root)
    bound = packet.get("stale_detection") or {}
    return (
        bound.get("bound_head_sha") != current.get("head_sha")
        or bound.get("bound_origin_sha") != current.get("origin_sha")
    )


def write_context_packet(repo_root: str = ".", path: str | None = None) -> str:
    packet = build_context_packet(repo_root)
    rel = path or os.path.join("data", "weaver", "context", "current.json")
    full = Path(repo_root) / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(rel).replace("\\", "/")


def _provider_inventory() -> dict:
    """Names and capabilities only — never keys or secrets."""
    try:
        from weaver.provider import list_available_providers

        names = list_available_providers()
    except Exception:
        names = ["gemini"]
    return {
        "providers": names,
        "gemini_key_pool": "api.key_pool (acquire_key / report_failure)",
        "note": "No credentials included. CONTEXT ≠ AUTHORIZATION.",
    }
