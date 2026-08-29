"""WEAVER-W4 — Read-only capability registry (discovery metadata, not authority)."""
from __future__ import annotations

from typing import Any


def list_capabilities() -> list[dict[str, Any]]:
    """Static inventory of mainline capabilities. Not a PassSpec."""
    return [
        {
            "name": "repository_recon",
            "description": "Repository identity, HEAD/origin, clean/dirty, continuation",
            "authority_level": "READ_ONLY",
            "requires": [],
            "scope": "none",
            "outputs": ["head_sha", "origin_sha", "clean", "continuation"],
            "mutation": False,
            "availability": "AVAILABLE",
            "entrypoint": "weaver.workbench_view.repository_state",
        },
        {
            "name": "evidence_index",
            "description": "Bounded AST evidence (files, imports, tests, layers)",
            "authority_level": "READ_ONLY",
            "requires": [],
            "scope": "optional roots",
            "outputs": ["files", "relations", "test_map"],
            "mutation": False,
            "availability": "AVAILABLE",
            "entrypoint": "weaver.evidence.collect_evidence",
            "limitations": "Default roots weaver/ + tests/; product surfaces optional",
        },
        {
            "name": "engineering_analysis",
            "description": "Facts / inferences / unknowns / risks for an objective",
            "authority_level": "READ_ONLY",
            "requires": ["objective"],
            "scope": "optional path hints",
            "outputs": ["facts", "inferences", "unknowns", "risks"],
            "mutation": False,
            "availability": "AVAILABLE",
            "entrypoint": "weaver.analysis.analyze_objective",
        },
        {
            "name": "engineering_plan",
            "description": "Implementation-grade plan from evidence",
            "authority_level": "READ_ONLY",
            "requires": ["objective"],
            "scope": "recommended path hints",
            "outputs": ["plan_id", "affected_paths", "steps", "risks"],
            "mutation": False,
            "availability": "AVAILABLE",
            "limitations": "UNSCOPED without path hints",
            "entrypoint": "weaver.engineering_plan.build_engineering_plan",
        },
        {
            "name": "changeset_and_patch",
            "description": "ProposedChangeSet + ProposedPatch (reviewable, not applied)",
            "authority_level": "READ_ONLY",
            "requires": ["plan"],
            "scope": "required for useful output",
            "outputs": ["files", "symbols", "patch_text", "impact"],
            "mutation": False,
            "availability": "LIMITED",
            "limitations": "K14 patch fidelity often DESIGN-ONLY / HUMAN-COMPLETE",
            "entrypoint": "weaver.patch.synthesize_patch",
        },
        {
            "name": "governed_execution",
            "description": "K15 execute_patch → K3 run_transaction",
            "authority_level": "MUTATION",
            "requires": ["PassSpec", "PatchApproval", "matching hashes"],
            "scope": "PassSpec allowed_paths",
            "outputs": ["ExecutionResult"],
            "mutation": True,
            "availability": "AVAILABLE",
            "limitations": "Not exposed as one-click in cockpit; UI remains LOCKED",
            "entrypoint": "weaver.execution.execute_patch",
        },
        {
            "name": "verification",
            "description": "K12 proof reconciliation matrix",
            "authority_level": "READ_ONLY",
            "requires": ["plan/patch/results"],
            "scope": "n/a",
            "outputs": ["verdict", "proof_matrix"],
            "mutation": False,
            "availability": "LIMITED",
            "limitations": "Often NOT RUN in cockpit until report supplied",
            "entrypoint": "weaver.verification",
        },
        {
            "name": "operator_cockpit",
            "description": "W1–W3 local browser/CLI observatory with path scoping",
            "authority_level": "READ_ONLY",
            "requires": [],
            "scope": "optional affected_paths",
            "outputs": ["observatory", "pipeline"],
            "mutation": False,
            "availability": "AVAILABLE",
            "entrypoint": "python -m weaver.workbench_app web",
        },
    ]


def capability_summary() -> dict[str, Any]:
    caps = list_capabilities()
    return {
        "count": len(caps),
        "mutation_capabilities": [c["name"] for c in caps if c.get("mutation")],
        "read_only_capabilities": [c["name"] for c in caps if not c.get("mutation")],
        "note": "Registry is discovery metadata. Not authorization. Not PassSpec.",
        "capabilities": caps,
    }
