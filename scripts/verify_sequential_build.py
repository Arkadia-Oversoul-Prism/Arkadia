#!/usr/bin/env python3
"""Canonical verifier for ARKADIA-SEQUENTIAL-BUILD envelopes.

The verifier proves protocol progression, not production authority.
It intentionally uses a small stdlib-only semantic gate and optionally
uses jsonschema when installed for full Draft 2020-12 validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "schemas" / "sequential_build_envelope.schema.json"

FORBIDDEN_AUTHORITY_KEYS = {
    "authority",
    "authorization_id",
    "authorization_scope",
    "human_authority",
    "approval",
    "production_acceptance",
    "work_event",
    "governing_identity",
}

REQUIRED_FIELDS = {
    "protocol",
    "protocol_version",
    "build_id",
    "parent_build",
    "base_commit",
    "objective",
    "scope",
    "transition",
    "invariants",
    "proof",
    "status",
    "failures",
    "unknowns",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _walk_forbidden(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in FORBIDDEN_AUTHORITY_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(_walk_forbidden(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_walk_forbidden(child, f"{path}[{index}]"))
    return hits


def _schema_validate(envelope: Mapping[str, Any]) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return []

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in sorted(validator.iter_errors(envelope), key=str)]


def _manual_validate(envelope: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(envelope))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
        return errors

    if envelope.get("protocol") != "ARKADIA-SEQUENTIAL-BUILD":
        errors.append("protocol must be ARKADIA-SEQUENTIAL-BUILD")
    if envelope.get("protocol_version") != "1.0":
        errors.append("protocol_version must be 1.0")
    if not isinstance(envelope.get("build_id"), str) or not envelope["build_id"]:
        errors.append("build_id must be a non-empty string")
    if not isinstance(envelope.get("base_commit"), str) or len(envelope["base_commit"]) < 7:
        errors.append("base_commit must contain a commit identifier")
    if not isinstance(envelope.get("objective"), str) or not envelope["objective"].strip():
        errors.append("objective must be non-empty")

    scope = envelope.get("scope")
    if not isinstance(scope, Mapping):
        errors.append("scope must be an object")
    else:
        if scope.get("kind") not in {"project", "repository"}:
            errors.append("scope.kind must be project or repository")
        if not scope.get("scope_ref"):
            errors.append("scope.scope_ref is required")
        if not scope.get("repository_ref"):
            errors.append("scope.repository_ref is required")
        if scope.get("kind") == "project" and not scope.get("project_ref"):
            errors.append("project scope requires project_ref")

    transition = envelope.get("transition")
    if not isinstance(transition, Mapping):
        errors.append("transition must be an object")
    else:
        for field in ("input_state_root", "output_state_root", "delta_ref", "changed_paths"):
            if field not in transition:
                errors.append(f"transition.{field} is required")
        if transition.get("external_side_effects") is not False:
            errors.append("transition.external_side_effects must be false")
        for field in ("input_state_root", "output_state_root"):
            value = transition.get(field)
            if not isinstance(value, str) or len(value) != 64:
                errors.append(f"transition.{field} must be a 64-character SHA-256 root")

    invariants = envelope.get("invariants")
    proof = envelope.get("proof")
    if not isinstance(invariants, list) or not invariants:
        errors.append("invariants must be a non-empty list")
    if not isinstance(proof, list):
        errors.append("proof must be a list")

    if isinstance(invariants, list) and isinstance(proof, list):
        proof_names = {item.get("invariant") for item in proof if isinstance(item, Mapping)}
        for invariant in invariants:
            if invariant not in proof_names:
                errors.append(f"missing proof for invariant: {invariant}")

    return errors


def verify_envelope(
    envelope: Mapping[str, Any],
    parent: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    errors = _manual_validate(envelope)
    errors.extend(_schema_validate(envelope))
    forbidden = _walk_forbidden(envelope)
    errors.extend(f"forbidden authority field: {path}" for path in forbidden)

    proof = envelope.get("proof") if isinstance(envelope.get("proof"), list) else []
    evidence_refs: list[str] = []
    unknown_gates: list[str] = []
    failed_gates: list[str] = []

    for item in proof:
        if not isinstance(item, Mapping):
            errors.append("proof entries must be objects")
            continue
        name = str(item.get("invariant", "UNKNOWN"))
        result = item.get("result")
        refs = item.get("evidence_refs")
        if result == "PASS":
            if not isinstance(refs, list) or not refs:
                errors.append(f"PASS gate {name} has no evidence_refs")
            else:
                evidence_refs.extend(str(ref) for ref in refs)
        elif result == "FAIL":
            failed_gates.append(name)
        elif result == "UNKNOWN":
            unknown_gates.append(name)
        else:
            errors.append(f"gate {name} has invalid result")

    failures = envelope.get("failures")
    if isinstance(failures, list) and failures:
        failed_gates.extend(str(item) for item in failures)

    transition = envelope.get("transition") if isinstance(envelope.get("transition"), Mapping) else {}
    input_root = transition.get("input_state_root")
    output_root = transition.get("output_state_root")

    parent_errors: list[str] = []
    if parent is not None:
        if parent.get("status") != "VERIFIED":
            parent_errors.append("parent build is not VERIFIED")
        if parent.get("build_id") != envelope.get("parent_build"):
            parent_errors.append("parent build_id does not match parent_build")
        parent_transition = parent.get("transition")
        if isinstance(parent_transition, Mapping) and input_root != parent_transition.get("output_state_root"):
            parent_errors.append("child input_state_root does not equal parent output_state_root")
        parent_scope = parent.get("scope")
        if isinstance(parent_scope, Mapping) and isinstance(envelope.get("scope"), Mapping):
            if parent_scope.get("repository_ref") != envelope["scope"].get("repository_ref"):
                parent_errors.append("child scope changes repository without a new governance boundary")
            if parent_scope.get("kind") == "project" and envelope["scope"].get("kind") != "project":
                parent_errors.append("project-scoped parent cannot silently widen to repository scope")
            if parent_scope.get("kind") == "project" and parent_scope.get("project_ref") != envelope["scope"].get("project_ref"):
                parent_errors.append("child project scope differs from parent project scope")

    errors.extend(parent_errors)

    all_pass = (
        not errors
        and not failed_gates
        and not unknown_gates
        and isinstance(envelope.get("status"), str)
        and envelope.get("status") == "VERIFIED"
        and isinstance(input_root, str)
        and isinstance(output_root, str)
        and bool(envelope.get("transition", {}).get("delta_ref"))
    )

    certificate_payload = {
        "protocol": envelope.get("protocol"),
        "protocol_version": envelope.get("protocol_version"),
        "build_id": envelope.get("build_id"),
        "base_commit": envelope.get("base_commit"),
        "input_state_root": input_root,
        "output_state_root": output_root,
        "scope": envelope.get("scope"),
        "evidence_refs": sorted(set(evidence_refs)),
        "can_proceed": all_pass,
    }

    return {
        "valid": all_pass,
        "can_proceed": all_pass,
        "build_id": envelope.get("build_id"),
        "status": "VERIFIED" if all_pass else "BLOCKED",
        "output_state_root": output_root,
        "next_input_root": output_root if all_pass else None,
        "failed_gates": sorted(set(failed_gates)),
        "unknown_gates": sorted(set(unknown_gates)),
        "errors": errors,
        "evidence_refs": sorted(set(evidence_refs)),
        "certificate_root": digest(certificate_payload),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an Arkadia sequential build envelope.")
    parser.add_argument("envelope", type=Path)
    parser.add_argument("--parent", type=Path)
    args = parser.parse_args()

    envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
    parent = json.loads(args.parent.read_text(encoding="utf-8")) if args.parent else None
    result = verify_envelope(envelope, parent)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
