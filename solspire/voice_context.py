"""Arkadia Voice — context resolution against the existing substrate (Phase 6).

Turns a parsed intent into a *resolved* context with an explicit status:

    KNOWN        exactly one referent, owned by the subject
    AMBIGUOUS    multiple candidates — the operator must choose (CLARIFY)
    UNKNOWN      no candidate — the operator must name it
    UNAUTHORIZED the referent exists but belongs to another subject

Uncertainty is never converted into confidence. Resolution reads canonical
substrate state only:

  * projects        → solspire.project_manager (all projects, ownership checked)
  * people          → knowledge.search.people_search (owner-scoped)
  * documents/notes → knowledge.search.fulltext_search (owner-scoped)
  * knowledge query → knowledge.search.fulltext_search (owner-scoped)

``disambiguations`` lets the operator answer a CLARIFY with an explicit value
for a bounded field (name / target / query / path / recipient); re-resolution
then yields KNOWN or a truthful UNKNOWN.
"""
from __future__ import annotations

import logging
from typing import Any

from solspire.voice_contracts import Context, ResolutionStatus, VoiceAction, new_id

logger = logging.getLogger("solspire.voice_context")

_DISAMBIGUATION_FIELDS = ("name", "target", "query", "path", "recipient")


def _ambiguity(field: str, reason: str, candidates: list[dict[str, Any]] | None = None,
               detail: str = "") -> dict[str, Any]:
    return {
        "field": field,
        "reason": reason,
        "detail": detail,
        "candidates": candidates or [],
    }


def _worst(statuses: list[str]) -> str:
    precedence = [
        ResolutionStatus.UNAUTHORIZED.value,
        ResolutionStatus.UNKNOWN.value,
        ResolutionStatus.AMBIGUOUS.value,
        ResolutionStatus.KNOWN.value,
    ]
    for status in precedence:
        if status in statuses:
            return status
    return ResolutionStatus.UNKNOWN.value


def _project_candidates(target: str, subject: str) -> tuple[list[dict[str, Any]], str | None]:
    """Match a project by name across ALL projects; return candidates + owner error.

    Returns (candidates, unauthorized_id). Ownership is checked here so a
    foreign project yields UNAUTHORIZED instead of a silent miss.
    """
    from solspire.project_manager import get_project_manager

    needle = (target or "").strip().lower()
    if not needle:
        return [], None
    candidates: list[dict[str, Any]] = []
    unauthorized: str | None = None
    try:
        projects = get_project_manager().list_projects()
    except Exception as exc:  # pragma: no cover - store unavailable
        logger.warning("[voice-context] project store unavailable: %s", exc)
        return [], None
    exact: list[Any] = []
    partial: list[Any] = []
    for project in projects:
        name = (project.name or "").strip().lower()
        if name == needle:
            exact.append(project)
        elif needle and needle in name:
            partial.append(project)
    for project in (exact or partial):
        owner = (project.owner_uid or "").strip()
        if owner and owner != subject:
            unauthorized = project.id
        candidates.append({
            "id": project.id,
            "label": project.name,
            "type": "PROJECT",
            "owner_uid": owner or None,
            "status": project.status,
        })
    return candidates, unauthorized


def _knowledge_documents(query: str, subject: str, limit: int = 8) -> list[dict[str, Any]]:
    from knowledge.search import fulltext_search

    rows = fulltext_search(query, limit=limit, user_id=subject)
    return [
        {
            "id": row.get("uuid") or row.get("id"),
            "label": row.get("title") or "(untitled)",
            "type": row.get("note_type") or "document",
        }
        for row in rows
    ]


def _knowledge_people(query: str, subject: str, limit: int = 8) -> list[dict[str, Any]]:
    from knowledge.search import people_search

    rows = people_search(query, limit=limit, user_id=subject)
    return [
        {"id": row.get("uuid") or row.get("id"), "label": row.get("title") or "(unnamed)",
         "type": "person"}
        for row in rows
    ]


def resolve_context(
    intent: Any,
    subject: str,
    disambiguations: dict[str, Any] | None = None,
) -> Context:
    """Resolve a parsed intent against canonical substrate state."""
    entities: dict[str, Any] = dict(getattr(intent, "entities", {}) or {})
    for key, value in (disambiguations or {}).items():
        if key in _DISAMBIGUATION_FIELDS:
            entities[key] = value

    action = str(getattr(intent, "action", VoiceAction.UNKNOWN.value))
    resolved: dict[str, Any] = {}
    candidates: dict[str, list[dict[str, Any]]] = {}
    ambiguities: list[dict[str, Any]] = []
    statuses: list[str] = []

    # ── Informational queries: nothing to point at, results are candidates ──
    if action in (VoiceAction.ASK.value, VoiceAction.SEARCH.value):
        query = str(entities.get("query") or "").strip()
        resolved["query"] = query
        if not query:
            statuses.append(ResolutionStatus.UNKNOWN.value)
            ambiguities.append(_ambiguity("query", "MISSING", detail="no query in transcript"))
        else:
            try:
                matches = _knowledge_documents(query, subject)
                candidates["matches"] = matches
                resolved["matches"] = len(matches)
                statuses.append(ResolutionStatus.KNOWN.value)
            except Exception as exc:
                logger.warning("[voice-context] knowledge search failed: %s", exc)
                statuses.append(ResolutionStatus.UNKNOWN.value)
                ambiguities.append(_ambiguity(
                    "query", "SEARCH_UNAVAILABLE",
                    detail=f"knowledge search unavailable: {exc}",
                ))

    # ── CREATE: a name that must not collide ────────────────────────────────
    elif action == VoiceAction.CREATE.value:
        name = str(entities.get("name") or "").strip()
        entity = str(entities.get("entity") or "PROJECT")
        resolved["entity"] = entity
        if not name:
            statuses.append(ResolutionStatus.UNKNOWN.value)
            ambiguities.append(_ambiguity(
                "name", "MISSING",
                detail="the request does not name what to create",
            ))
        else:
            resolved["name"] = name
            if entity == "PROJECT":
                existing, _ = _project_candidates(name, subject)
                exact = [c for c in existing if c["label"].lower() == name.lower()]
                if exact:
                    candidates["existing_projects"] = exact
                    statuses.append(ResolutionStatus.AMBIGUOUS.value)
                    ambiguities.append(_ambiguity(
                        "name", "NAME_COLLISION", exact,
                        detail=f"a project named '{name}' already exists",
                    ))
                else:
                    statuses.append(ResolutionStatus.KNOWN.value)
            else:
                # Bounded executor vocabulary supports PROJECT today.
                statuses.append(ResolutionStatus.KNOWN.value)

    # ── MODIFY: resolve the target project (ownership enforced) ─────────────
    elif action == VoiceAction.MODIFY.value:
        target = str(entities.get("target") or "").strip()
        if not target:
            statuses.append(ResolutionStatus.UNKNOWN.value)
            ambiguities.append(_ambiguity(
                "target", "MISSING", detail="the request does not name what to modify",
            ))
        else:
            resolved["target"] = target
            found, unauthorized = _project_candidates(target, subject)
            candidates["projects"] = found
            if unauthorized:
                statuses.append(ResolutionStatus.UNAUTHORIZED.value)
                ambiguities.append(_ambiguity(
                    "target", "NOT_OWNED_BY_SUBJECT", found,
                    detail="the target exists but is owned by another subject",
                ))
            elif not found:
                statuses.append(ResolutionStatus.UNKNOWN.value)
                ambiguities.append(_ambiguity(
                    "target", "NO_MATCH", detail=f"no project matches '{target}'",
                ))
            elif len(found) > 1:
                statuses.append(ResolutionStatus.AMBIGUOUS.value)
                ambiguities.append(_ambiguity(
                    "target", "MULTIPLE_MATCHES", found,
                    detail=f"{len(found)} projects match '{target}'",
                ))
            else:
                statuses.append(ResolutionStatus.KNOWN.value)
                resolved["project"] = found[0]

    # ── EXECUTE ─────────────────────────────────────────────────────────────
    elif action == VoiceAction.EXECUTE.value:
        operation = str(entities.get("operation") or "fs_list")
        resolved["operation"] = operation
        if operation == "fs_list":
            path = str(entities.get("path") or ".").strip() or "."
            resolved["path"] = path
            statuses.append(ResolutionStatus.KNOWN.value)
        elif operation == "transfer":
            target = str(entities.get("target") or "").strip()
            recipient = str(entities.get("recipient") or "").strip()
            resolved["target"] = target
            resolved["recipient"] = recipient
            if not target:
                statuses.append(ResolutionStatus.UNKNOWN.value)
                ambiguities.append(_ambiguity(
                    "target", "MISSING", detail="no document named in the request",
                ))
            else:
                try:
                    docs = _knowledge_documents(target, subject)
                    candidates["documents"] = docs
                    if not docs:
                        statuses.append(ResolutionStatus.UNKNOWN.value)
                        ambiguities.append(_ambiguity(
                            "target", "NO_MATCH",
                            detail=f"no document matches '{target}'",
                        ))
                    elif len(docs) > 1:
                        statuses.append(ResolutionStatus.AMBIGUOUS.value)
                        ambiguities.append(_ambiguity(
                            "target", "MULTIPLE_MATCHES", docs,
                            detail=f"{len(docs)} documents match '{target}'",
                        ))
                    else:
                        statuses.append(ResolutionStatus.KNOWN.value)
                        resolved["document"] = docs[0]
                except Exception as exc:
                    logger.warning("[voice-context] knowledge search failed: %s", exc)
                    statuses.append(ResolutionStatus.UNKNOWN.value)
                    ambiguities.append(_ambiguity(
                        "target", "SEARCH_UNAVAILABLE",
                        detail=f"knowledge search unavailable: {exc}",
                    ))
            if not recipient:
                statuses.append(ResolutionStatus.UNKNOWN.value)
                ambiguities.append(_ambiguity(
                    "recipient", "MISSING", detail="no recipient named in the request",
                ))
            else:
                try:
                    people = _knowledge_people(recipient, subject)
                    candidates["recipients"] = people
                    if not people:
                        statuses.append(ResolutionStatus.UNKNOWN.value)
                        ambiguities.append(_ambiguity(
                            "recipient", "NO_MATCH",
                            detail=f"no contact matches '{recipient}'",
                        ))
                    elif len(people) > 1:
                        statuses.append(ResolutionStatus.AMBIGUOUS.value)
                        ambiguities.append(_ambiguity(
                            "recipient", "MULTIPLE_MATCHES", people,
                            detail=f"{len(people)} contacts match '{recipient}'",
                        ))
                    else:
                        statuses.append(ResolutionStatus.KNOWN.value)
                        resolved["person"] = people[0]
                except Exception as exc:
                    logger.warning("[voice-context] people search failed: %s", exc)
                    statuses.append(ResolutionStatus.UNKNOWN.value)
                    ambiguities.append(_ambiguity(
                        "recipient", "SEARCH_UNAVAILABLE",
                        detail=f"people search unavailable: {exc}",
                    ))
        else:
            statuses.append(ResolutionStatus.UNKNOWN.value)
            ambiguities.append(_ambiguity(
                "operation", "UNSUPPORTED",
                detail=f"no context resolver for operation '{operation}'",
            ))

    else:
        statuses.append(ResolutionStatus.UNKNOWN.value)
        ambiguities.append(_ambiguity(
            "action", "UNKNOWN_INTENT",
            detail="intent is unresolved; context cannot be inferred",
        ))

    return Context(
        context_id=new_id("CX"),
        resolved_entities=resolved,
        candidate_entities=candidates,
        ambiguities=ambiguities,
        resolution_status=_worst(statuses),
        source_event_id=str(getattr(intent, "source_event_id", "")),
    )


__all__ = ["resolve_context"]
