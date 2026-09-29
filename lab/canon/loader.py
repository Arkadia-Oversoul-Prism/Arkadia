from __future__ import annotations

from pathlib import Path
from typing import Any

from ..model import observed_now

PRIORITY = ["AGENTS.md", "README.md", "governance", "docs/architecture", "docs/adr", "docs"]
TYPES = {"constitution":"CONSTITUTIONAL","constitutional":"CONSTITUTIONAL","vision":"VISION","architecture":"ARCHITECTURAL","behavior":"BEHAVIORAL","design":"DESIGN","commercial":"COMMERCIAL","governance":"GOVERNANCE","taste":"TASTE","evidence":"EVIDENCE"}


def _classify(path: str, text: str) -> str:
    low=path.lower()
    for key,value in TYPES.items():
        if key in low: return value
    if path == "AGENTS.md": return "GOVERNANCE"
    if "principle" in text.lower() or "human sovereignty" in text.lower(): return "ARCHITECTURAL"
    return "DERIVED"


def load_canon(repo_root: str = ".") -> dict[str, Any]:
    root=Path(repo_root).resolve(); candidates=[]
    for base in [root/"AGENTS.md",root/"README.md",root/"governance",root/"docs"]:
        if base.is_file(): candidates.append(base)
        elif base.is_dir(): candidates.extend(p for p in base.rglob("*.md") if p.is_file())
    candidates=sorted(set(candidates),key=lambda p:(PRIORITY.index(next((x for x in PRIORITY if str(p.relative_to(root)).startswith(x)),"docs")) if any(str(p.relative_to(root)).startswith(x) for x in PRIORITY) else 99,str(p)))
    sources=[]
    for p in candidates[:250]:
        try:
            text=p.read_text(encoding="utf-8")
            rel=p.relative_to(root).as_posix()
            sources.append({"path":rel,"classification":_classify(rel,text),"bytes":len(text.encode("utf-8")),"provenance":{"source_file":rel}})
        except (OSError,UnicodeError): continue
    return {"loaded":bool(sources),"sources":sources,"canon_version":"lab-0.1","observed_at":observed_now(),"note":"Explicit repository declarations are canonical evidence; patterns inferred from implementation remain DERIVED."}
