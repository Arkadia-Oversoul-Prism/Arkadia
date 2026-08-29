"""WEAVER-K10 — Deep repository evidence + traceability (read-only).

EVIDENCE ≠ AUTHORIZATION. Capability without authority.
"""
from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from .pass_spec import current_head, current_origin_main
from .recon import architecture_summary, topology


class EvidenceKind(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


class ContinuityLike(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    MISSING = "MISSING"
    INVALID = "INVALID"


class TestMapKind(str, Enum):
    DIRECT_TEST_REFERENCE = "DIRECT_TEST_REFERENCE"
    LIKELY_TEST_COVERAGE = "LIKELY_TEST_COVERAGE"
    NO_DISCOVERABLE_TEST = "NO_DISCOVERABLE_TEST"
    UNKNOWN = "UNKNOWN"


@dataclass
class EvidenceRecord:
    id: str
    kind: str
    subject: str
    claim: str
    source: str
    bound_sha: str
    confidence: str = "high"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceRelation:
    source: str
    relation: str
    target: str
    source_kind: str = "module"
    target_kind: str = "module"
    evidence_source: str = "static"
    bound_sha: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceIndex:
    bound_head_sha: str
    bound_origin_sha: str | None
    records: list[EvidenceRecord] = field(default_factory=list)
    relations: list[EvidenceRelation] = field(default_factory=list)
    files: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bound_head_sha": self.bound_head_sha,
            "bound_origin_sha": self.bound_origin_sha,
            "records": [r.to_dict() for r in self.records],
            "relations": [r.to_dict() for r in self.relations],
            "files": self.files,
        }


def _eid(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]
    return f"ev-{h}"


def _is_python(path: Path) -> bool:
    return path.suffix == ".py"


def _iter_python_files(repo_root: Path, roots: Iterable[str]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        base = repo_root / root
        if not base.exists():
            continue
        if base.is_file() and _is_python(base):
            out.append(base)
            continue
        for p in base.rglob("*.py"):
            # skip venv-like
            if any(x in p.parts for x in (".git", "node_modules", "venv", ".venv", "__pycache__")):
                continue
            out.append(p)
    return sorted(out)


def _module_name(repo_root: Path, path: Path) -> str:
    rel = path.relative_to(repo_root).with_suffix("")
    return str(rel).replace("\\", "/").replace("/", ".")


def collect_evidence(
    repo_root: str = ".",
    *,
    roots: list[str] | None = None,
    max_files: int = 200,
) -> EvidenceIndex:
    """Bounded deterministic collection. Read-only."""
    root = Path(repo_root)
    head = current_head(repo_root)
    origin = current_origin_main(repo_root)
    roots = roots or ["weaver", "tests"]
    idx = EvidenceIndex(bound_head_sha=head, bound_origin_sha=origin)

    # Repository facts
    idx.records.append(
        EvidenceRecord(
            id=_eid("repo", head),
            kind=EvidenceKind.FACT.value,
            subject="repository",
            claim=f"HEAD is {head}",
            source="git",
            bound_sha=head,
        )
    )
    idx.records.append(
        EvidenceRecord(
            id=_eid("origin", origin or "none"),
            kind=EvidenceKind.FACT.value,
            subject="repository",
            claim=f"origin/main is {origin}",
            source="git",
            bound_sha=head,
        )
    )

    arch = architecture_summary(repo_root)
    idx.records.append(
        EvidenceRecord(
            id=_eid("arch", str(arch.get("status"))),
            kind=EvidenceKind.FACT.value,
            subject="architecture",
            claim=f"architecture status={arch.get('status')} source={arch.get('source')}",
            source="architecture_map",
            bound_sha=head,
            metadata={"layer_names": arch.get("layer_names") or {}},
        )
    )

    files = _iter_python_files(root, roots)[:max_files]
    import_map: dict[str, set[str]] = {}  # module -> imports
    defines: dict[str, list[str]] = {}

    for path in files:
        rel = str(path.relative_to(root)).replace("\\", "/")
        mod = _module_name(root, path)
        text = path.read_text(encoding="utf-8", errors="replace")
        idx.files[rel] = {
            "path": rel,
            "language": "python",
            "size": len(text),
            "module": mod,
        }
        idx.records.append(
            EvidenceRecord(
                id=_eid("file", rel),
                kind=EvidenceKind.FACT.value,
                subject=rel,
                claim=f"file exists: {rel}",
                source="file",
                bound_sha=head,
                metadata={"module": mod},
            )
        )
        try:
            tree = ast.parse(text)
        except SyntaxError:
            idx.records.append(
                EvidenceRecord(
                    id=_eid("parse", rel),
                    kind=EvidenceKind.UNKNOWN.value,
                    subject=rel,
                    claim="AST parse failed; symbols unknown",
                    source="symbol",
                    bound_sha=head,
                    confidence="low",
                )
            )
            continue

        imports: set[str] = set()
        defs: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0] if alias.name else "")
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    imports.add(node.module.split(".")[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defs.append(node.name)
                idx.relations.append(
                    EvidenceRelation(
                        source=mod,
                        relation="DEFINES",
                        target=node.name,
                        source_kind="module",
                        target_kind="symbol",
                        evidence_source="ast",
                        bound_sha=head,
                    )
                )
        imports.discard("")
        import_map[mod] = imports
        defines[mod] = defs
        for imp in sorted(imports):
            idx.relations.append(
                EvidenceRelation(
                    source=mod,
                    relation="IMPORTS",
                    target=imp,
                    evidence_source="ast",
                    bound_sha=head,
                )
            )

    # reverse dependents for weaver.* targets
    for mod, imports in import_map.items():
        for imp in imports:
            if imp.startswith("weaver") or imp in import_map:
                idx.relations.append(
                    EvidenceRelation(
                        source=mod,
                        relation="DEPENDS_ON",
                        target=imp,
                        evidence_source="ast",
                        bound_sha=head,
                    )
                )

    # Architecture BELONGS_TO_LAYER (prefix heuristic from LAYER_MAP names)
    layer_names = (arch.get("layer_names") or {}) if isinstance(arch, dict) else {}
    # map path prefixes
    prefix_layer = {
        "weaver": "weaver_control_plane",
        "tests": "tests",
        "api": "api",
        "providers": "providers",
        "docs": "constitution_or_docs",
    }
    for rel in idx.files:
        top = rel.split("/", 1)[0]
        layer = prefix_layer.get(top, "unknown")
        idx.relations.append(
            EvidenceRelation(
                source=rel,
                relation="BELONGS_TO_LAYER",
                target=layer,
                source_kind="file",
                target_kind="layer",
                evidence_source="architecture_map",
                bound_sha=head,
            )
        )

    # Test mentions
    test_files = [p for p in files if "test_" in p.name or "/tests/" in str(p).replace("\\", "/")]
    for tpath in test_files:
        trel = str(tpath.relative_to(root)).replace("\\", "/")
        ttext = tpath.read_text(encoding="utf-8", errors="replace")
        for rel in idx.files:
            if rel == trel:
                continue
            stem = Path(rel).stem
            mod_dot = rel.replace("/", ".").replace(".py", "")
            if stem in ttext or mod_dot in ttext or rel in ttext:
                idx.relations.append(
                    EvidenceRelation(
                        source=trel,
                        relation="TESTS",
                        target=rel,
                        source_kind="test",
                        target_kind="file",
                        evidence_source="static_text",
                        bound_sha=head,
                    )
                )
                idx.relations.append(
                    EvidenceRelation(
                        source=trel,
                        relation="REFERENCES",
                        target=rel,
                        evidence_source="static_text",
                        bound_sha=head,
                    )
                )

    return idx


def evidence_staleness(index: EvidenceIndex, repo_root: str = ".") -> ContinuityLike:
    try:
        head = current_head(repo_root)
        origin = current_origin_main(repo_root)
    except Exception:
        return ContinuityLike.INVALID
    if index.bound_head_sha != head:
        return ContinuityLike.STALE
    if index.bound_origin_sha is not None and origin is not None and index.bound_origin_sha != origin:
        return ContinuityLike.STALE
    return ContinuityLike.CURRENT


def query_evidence(index: EvidenceIndex, subject: str) -> dict[str, Any]:
    """Read-only query for a path/module subject."""
    subj = subject.replace("\\", "/").lstrip("./")
    records = [r.to_dict() for r in index.records if subj in r.subject or r.subject in subj]
    rels = [
        r.to_dict()
        for r in index.relations
        if subj in r.source or subj in r.target or subj.replace("/", ".") in r.source or subj.replace("/", ".") in r.target
    ]
    imports = [r for r in index.relations if r.relation == "IMPORTS" and (subj in r.source or subj.replace("/", ".") in r.source)]
    dependents = [
        r
        for r in index.relations
        if r.relation in ("IMPORTS", "DEPENDS_ON", "REFERENCES", "TESTS")
        and (subj in r.target or subj.replace("/", ".") in r.target)
    ]
    tests = [r for r in index.relations if r.relation == "TESTS" and (subj in r.target or subj in r.source)]
    layers = [r for r in index.relations if r.relation == "BELONGS_TO_LAYER" and subj in r.source]

    test_kind = TestMapKind.NO_DISCOVERABLE_TEST.value
    if tests:
        test_kind = TestMapKind.DIRECT_TEST_REFERENCE.value

    return {
        "subject": subj,
        "bound_head_sha": index.bound_head_sha,
        "bound_origin_sha": index.bound_origin_sha,
        "records": records,
        "relations": rels,
        "imports": [r.to_dict() for r in imports],
        "dependents": [r.to_dict() for r in dependents],
        "tests": [r.to_dict() for r in tests],
        "architecture": [r.to_dict() for r in layers],
        "test_map_kind": test_kind,
        "authorization": {
            "current_pass_authorized": False,
            "note": "EVIDENCE ≠ AUTHORIZATION",
        },
    }


def evidence_for_analysis(repo_root: str = ".", subject_hints: list[str] | None = None) -> dict[str, Any]:
    """Compact payload for K9 consumption."""
    idx = collect_evidence(repo_root)
    stale = evidence_staleness(idx, repo_root)
    subjects = subject_hints or ["weaver/session.py", "weaver/analysis.py", "weaver/provider.py"]
    queries = {s: query_evidence(idx, s) for s in subjects}
    return {
        "index_summary": {
            "bound_head_sha": idx.bound_head_sha,
            "bound_origin_sha": idx.bound_origin_sha,
            "record_count": len(idx.records),
            "relation_count": len(idx.relations),
            "file_count": len(idx.files),
            "staleness": stale.value,
        },
        "queries": queries,
        "authorization": {"current_pass_authorized": False, "note": "EVIDENCE ≠ AUTHORIZATION"},
    }
