"""Arkadia Voice — pipeline orchestration across canonical primitives (Phases 4–10).

One voice event walks one chain, and every step reuses an existing substrate
primitive. Voice creates no second executor, no second proposal ledger, no
second authority:

    ingest      VoiceEvent + sha256(audio) → ASRProvider → Transcript
    understand  Transcript → bounded Intent → Context → AUTHORITY assessment
    propose     → proposal_manager.create_proposal   (canonical proposal)
    decide      → proposal_manager.record_decision   (human approval)
    revise      → WITHDRAWN + create_proposal         (EDIT, supersession noted)
    authorize   → console_authority_router.authorize_proposal_sync
                  (govern authority: Flamekeeper / access_level ≥ 3)
    execute     → ExecutionRuntime (canonical executor) + enterprise
                  execution_attempt/evidence + workevent_manager (WorkEvent)
    verify      → enterprise store.verify (separate human act)

Failures raise :class:`VoiceError` with a canonical error state from
``VOICE_ERROR_STATES``; the failure itself is recorded in the chain first, so
evidence survives every negative path.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from solspire.voice_asr import ASRError, get_provider, select_provider
from solspire.voice_contracts import (
    RISK_LEVELS,
    VOICE_ERROR_STATES,
    VoiceEvent,
    VoiceStage,
    canonical_digest,
    chain_digest,
    hash_audio,
    new_id,
    requires_approval,
    utc_now,
)
from solspire.voice_context import resolve_context
from solspire.voice_intent import parse_intent
from solspire.voice_store import get_voice_store

logger = logging.getLogger("solspire.voice_pipeline")

MAX_AUDIO_BYTES = 5 * 1024 * 1024
EXECUTION_WAIT_SECONDS = 15.0


class VoiceError(Exception):
    """A canonical voice error state with operator-facing recovery guidance."""

    def __init__(self, state: str, detail: str = "", **extra: Any) -> None:
        info = VOICE_ERROR_STATES.get(state, {})
        super().__init__(detail or state)
        self.state = state
        self.detail = detail or state
        self.recovery = info.get("recovery", "Inspect the evidence chain for this stage.")
        self.stage = info.get("stage", "ERROR")
        self.extra = extra

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "state": self.state,
            "detail": self.detail,
            "recovery": self.recovery,
            "stage": self.stage,
        }
        payload.update(self.extra)
        return payload


def _require_state(event: dict[str, Any], *states: str) -> None:
    if event.get("status") not in states:
        raise VoiceError(
            "PROPOSAL_REQUIRED",
            f"voice event is in status {event.get('status')}; expected {'/'.join(states)}",
            event_id=event.get("event_id"),
        )


class VoicePipeline:
    """Implements the Arkadia Voice chain over the existing substrate."""

    def __init__(self) -> None:
        self.store = get_voice_store()

    # ── helpers ─────────────────────────────────────────────────────────────

    def _event_or_raise(self, event_id: str, subject: str) -> dict[str, Any]:
        event = self.store.get_event(event_id, subject)
        if event is None:
            raise LookupError(f"voice event not found: {event_id}")
        return event

    def _fail(self, event_id: str, subject: str, state: str, detail: str, **extra: Any) -> VoiceError:
        """Persist the failure in the chain before surfacing it (evidence survives)."""
        recovery = VOICE_ERROR_STATES.get(state, {}).get("recovery", "")
        extra.setdefault("event_id", event_id)
        try:
            self.store.update_event(event_id, status="FAILED", error_state=state,
                                    error_detail=detail)
            self.store.append_stage(
                event_id,
                stage=VoiceStage.ERROR.value,
                record_type="VoiceError",
                record_id=new_id("ER"),
                payload={"state": state, "detail": detail, "recovery": recovery,
                         "event_id": event_id},
            )
        except Exception:  # pragma: no cover - persistence must not mask the error
            logger.exception("[voice] failed to persist error state %s", state)
        return VoiceError(state, detail, **extra)

    def _authority_payload(self, user: dict[str, Any], action: str,
                           context: dict[str, Any], human_only: bool) -> dict[str, Any]:
        if human_only:
            status = "HUMAN_ONLY_REFUSED"
        elif context.get("resolution_status") == "UNAUTHORIZED":
            status = "SUBJECT_NOT_AUTHORIZED"
        elif not requires_approval(action):
            status = "OBSERVATION_ONLY"
        else:
            status = "GOVERN_AUTHORITY_REQUIRED"
        return {
            "authority_status": status,
            "risk_level": RISK_LEVELS.get(action, "UNKNOWN"),
            "required_approval": requires_approval(action),
            "authorization_required": requires_approval(action),
            "subject": {
                "uid": user.get("uid"),
                "role": user.get("role"),
                "access_level": user.get("access_level"),
            },
            "policy": (
                "Speech is an input modality, not authorization. "
                "Observation-only requests follow the Engineering Lab voice "
                "boundary (READ disposition); consequential requests must pass "
                "proposal → human decision → authorization (govern authority) → "
                "execution."
            ),
        }

    def _executor_for(self, intent: dict[str, Any],
                      context: dict[str, Any]) -> dict[str, Any] | None:
        """Map a resolved intent onto the canonical ExecutionRuntime tool envelope."""
        action = intent.get("action")
        entities = intent.get("entities") or {}
        resolved = (context.get("resolved_entities") or {})

        if action == "CREATE" and entities.get("entity") == "PROJECT" and resolved.get("name"):
            name = str(resolved["name"])
            return {
                "channel": "execution_runtime",
                "label": f"Create project '{name}'",
                "tools": ["project_create"],
                "steps": [{"tool": "project_create", "payload": {"name": name},
                           "description": f"Create project {name}"}],
                "read_only": False,
            }
        if action == "MODIFY":
            project = resolved.get("project")
            field = str(entities.get("field") or "name")
            new_value = entities.get("new_value")
            if project and new_value and field in {"name", "status", "description"}:
                label = f"Update project '{project.get('label')}' {field} → {new_value}"
                return {
                    "channel": "execution_runtime",
                    "label": label,
                    "tools": ["project_update"],
                    "steps": [{"tool": "project_update",
                               "payload": {"project_id": project.get("id"),
                                           field: new_value},
                               "description": label}],
                    "read_only": False,
                }
            return None
        if action == "EXECUTE":
            operation = entities.get("operation")
            if operation == "fs_list":
                path = str(resolved.get("path") or ".").strip() or "."
                return {
                    "channel": "execution_runtime",
                    "label": f"List directory '{path}' (read-only)",
                    "tools": ["fs_list"],
                    "steps": [{"tool": "fs_list", "payload": {"path": path},
                               "description": f"List {path}"}],
                    "read_only": True,
                }
            return None  # transfer and friends have no canonical executor
        return None

    # ── Phase 4: audio → VoiceEvent → Transcript ────────────────────────────

    def ingest(
        self,
        user: dict[str, Any],
        *,
        audio: bytes,
        mime: str = "",
        language: str = "en",
        provider: str | None = None,
        transcript_hint: str | None = None,
        session_id: str | None = None,
        duration_ms: int | None = None,
    ) -> dict[str, Any]:
        subject = str(user["uid"])
        if not audio:
            raise VoiceError("AUDIO_EMPTY", "captured audio is empty")
        if len(audio) > MAX_AUDIO_BYTES:
            raise VoiceError(
                "AUDIO_CAPTURE_FAILED",
                f"audio is {len(audio)} bytes; limit is {MAX_AUDIO_BYTES}",
            )

        from solspire.workspace_manager import get_workspace_manager
        workspace = get_workspace_manager().get_or_create(subject)

        audio_hash = hash_audio(audio)
        event = VoiceEvent.create(
            subject=subject,
            workspace_ref=workspace.id,
            audio_hash=audio_hash,
            audio_reference="",  # bound to the event id below
            language=language,
            session_id=session_id,
            audio_mime=mime,
            audio_size=len(audio),
            duration_ms=duration_ms,
        )
        event.audio_reference = f"voice-audio:{event.event_id}"

        self.store.insert_event(
            event_id=event.event_id,
            session_id=event.session_id,
            subject_ref=subject,
            workspace_ref=workspace.id,
            language=language,
            audio_reference=event.audio_reference,
            audio_mime=mime,
            audio_size=len(audio),
            audio_hash=audio_hash,
            audio_bytes=audio,
            duration_ms=duration_ms,
            status="RECEIVED",
        )
        self.store.append_stage(
            event.event_id,
            stage=VoiceStage.VOICE_EVENT.value,
            record_type="VoiceEvent",
            record_id=event.event_id,
            payload={
                "event_id": event.event_id,
                "session_id": event.session_id,
                "subject": subject,
                "workspace_ref": workspace.id,
                "audio_reference": event.audio_reference,
                "audio_hash": audio_hash,
                "audio_mime": mime,
                "audio_size": len(audio),
                "duration_ms": duration_ms,
                "language": language,
                "timestamp": event.timestamp,
            },
        )

        # Provider selection: only AVAILABLE providers may run.
        try:
            asr_provider, info = select_provider(provider)
        except ASRError as err:
            raise self._fail(event.event_id, subject, err.state, err.detail)

        options: dict[str, Any] = {
            "language": language,
            "mime": mime,
            "audio_hash": audio_hash,
        }
        if transcript_hint is not None:
            options["transcript_hint"] = transcript_hint
        try:
            transcript = asr_provider.transcribe(audio, options)
        except ASRError as err:
            raise self._fail(event.event_id, subject, err.state, err.detail)
        except Exception as exc:  # provider bug — surface as a failed state
            logger.exception("[voice] provider %s crashed", asr_provider.name)
            raise self._fail(event.event_id, subject, "ASR_FAILED", str(exc))

        transcript_dict = transcript.to_dict()
        self.store.append_stage(
            event.event_id,
            stage=VoiceStage.TRANSCRIPT.value,
            record_type="Transcript",
            record_id=new_id("TR"),
            payload={"transcript": transcript_dict, "provider": info.to_dict()},
        )

        if not transcript.text:
            raise self._fail(
                event.event_id, subject, "TRANSCRIPT_EMPTY",
                f"provider '{info.name}' produced an empty transcript",
            )

        self.store.update_event(
            event.event_id,
            transcript_json=transcript_dict,
            status="TRANSCRIBED",
            error_state=None,
            error_detail=None,
        )
        return {
            "event": self.store.get_event(event.event_id, subject),
            "transcript": transcript_dict,
            "provider": info.to_dict(),
        }

    # ── Phases 5–7: Intent → Context → Authority ────────────────────────────

    def understand(self, user: dict[str, Any], event_id: str,
                   disambiguations: dict[str, Any] | None = None) -> dict[str, Any]:
        subject = str(user["uid"])
        event = self._event_or_raise(event_id, subject)
        transcript = event.get("transcript") or {}
        text = str(transcript.get("text") or "")
        if not text:
            raise VoiceError("TRANSCRIPT_EMPTY",
                             "no transcript on this event — capture and transcribe first")

        if disambiguations:
            self.store.append_stage(
                event_id,
                stage=VoiceStage.CLARIFICATION.value,
                record_type="Clarification",
                record_id=new_id("CL"),
                payload={"disambiguations": disambiguations, "by": subject},
            )

        intent = parse_intent(text, event_id)
        intent_dict = intent.to_dict()
        self.store.update_event(event_id, intent_json=intent_dict)
        self.store.append_stage(
            event_id,
            stage=VoiceStage.INTENT.value,
            record_type="Intent",
            record_id=intent.intent_id,
            payload=intent_dict,
        )

        context = resolve_context(intent, subject, disambiguations)
        context_dict = context.to_dict()
        self.store.update_event(event_id, context_json=context_dict)
        self.store.append_stage(
            event_id,
            stage=VoiceStage.CONTEXT.value,
            record_type="Context",
            record_id=context.context_id,
            payload=context_dict,
        )

        human_only = bool(intent.entities.get("human_only"))
        authority = self._authority_payload(user, intent.action, context_dict, human_only)
        authority.update({
            "event_id": event_id,
            "intent_id": intent.intent_id,
            "context_id": context.context_id,
        })
        self.store.append_stage(
            event_id,
            stage=VoiceStage.AUTHORITY.value,
            record_type="AuthorityAssessment",
            record_id=new_id("AU"),
            payload=authority,
        )

        status = ("UNDERSTOOD" if context.resolution_status == "KNOWN"
                  else "CLARIFICATION_REQUIRED")
        self.store.update_event(event_id, status=status)

        # Derived, explicit state for the operator surface (never a guess).
        error: dict[str, Any] | None = None
        if human_only:
            error = {"state": "AUTHORITY_MISSING",
                     "detail": "this operation is human-only and is never dispatched by voice",
                     **{"recovery": VOICE_ERROR_STATES["AUTHORITY_MISSING"]["recovery"]}}
        elif intent.action == "UNKNOWN":
            error = {"state": "INTENT_UNKNOWN",
                     "detail": "no canonical intent matched the transcript",
                     **{"recovery": VOICE_ERROR_STATES["INTENT_UNKNOWN"]["recovery"]}}
        elif context.resolution_status == "AMBIGUOUS":
            error = {"state": "CONTEXT_AMBIGUOUS",
                     "detail": "multiple candidates match — clarify before proceeding",
                     **{"recovery": VOICE_ERROR_STATES["CONTEXT_AMBIGUOUS"]["recovery"]}}
        elif context.resolution_status == "UNKNOWN" and not requires_approval(intent.action):
            error = {"state": "CONTEXT_UNKNOWN",
                     "detail": "no referent resolved for this request",
                     **{"recovery": VOICE_ERROR_STATES["CONTEXT_UNKNOWN"]["recovery"]}}
        elif context.resolution_status == "UNAUTHORIZED":
            error = {"state": "AUTHORIZATION_DENIED",
                     "detail": "the resolved target belongs to another subject",
                     **{"recovery": VOICE_ERROR_STATES["AUTHORIZATION_DENIED"]["recovery"]}}

        return {
            "event": self.store.get_event(event_id, subject),
            "transcript": transcript,
            "intent": intent_dict,
            "context": context_dict,
            "authority": authority,
            "error": error,
            "requires_proposal": requires_approval(intent.action),
        }

    # ── Phase 8: explicit proposal ──────────────────────────────────────────

    def propose(self, user: dict[str, Any], event_id: str) -> dict[str, Any]:
        subject = str(user["uid"])
        event = self._event_or_raise(event_id, subject)
        intent = event.get("intent")
        context = event.get("context")
        if not intent or not context:
            raise VoiceError("INTENT_UNKNOWN",
                             "understand this event before proposing",
                             event_id=event_id)

        if intent.get("entities", {}).get("human_only"):
            raise self._fail(event_id, subject, "AUTHORITY_MISSING",
                             "human-only operation refused at the voice boundary")
        if intent.get("action") == "UNKNOWN":
            raise self._fail(event_id, subject, "INTENT_UNKNOWN",
                             "no canonical intent matched the transcript")

        resolution = context.get("resolution_status")
        if resolution == "UNAUTHORIZED":
            raise self._fail(event_id, subject, "AUTHORIZATION_DENIED",
                             "resolved target is not owned by this subject")
        if resolution == "AMBIGUOUS":
            fields = [a.get("field") for a in context.get("ambiguities", [])]
            raise VoiceError(
                "CONTEXT_AMBIGUOUS",
                f"ambiguous context on {', '.join(str(f) for f in fields)} — clarify first",
                event_id=event_id,
                ambiguities=context.get("ambiguities", []),
            )
        if resolution != "KNOWN":
            raise VoiceError(
                "CONTEXT_UNKNOWN",
                "context unresolved — name the target explicitly and re-understand",
                event_id=event_id,
                ambiguities=context.get("ambiguities", []),
            )

        action = intent.get("action")
        if not requires_approval(action):
            return {
                "proposal": None,
                "note": "observation-only request: no proposal and no approval "
                        "required (Engineering Lab voice boundary, READ disposition)",
                "risk_level": RISK_LEVELS.get(action),
                "required_approval": False,
            }

        executor = self._executor_for(intent, context)
        from solspire.workspace_manager import get_workspace_manager
        workspace = get_workspace_manager().get_or_create(subject)

        summary = (
            intent.get("entities", {}).get("name")
            or intent.get("entities", {}).get("target")
            or intent.get("entities", {}).get("query")
            or (event.get("transcript") or {}).get("text", "")
        )
        scope_payload = {
            "source": "arkadia_voice",
            "event_id": event_id,
            "session_id": event.get("session_id"),
            "intent_id": intent.get("intent_id"),
            "context_id": context.get("context_id"),
            "action": action,
            "risk_level": RISK_LEVELS.get(action),
            "entities": intent.get("entities"),
            "resolved_entities": context.get("resolved_entities"),
            "executor": executor,
            "transcript": (event.get("transcript") or {}).get("text", ""),
        }
        proposal = get_proposal_manager_or_raise().create_proposal(
            subject_ref=subject,
            workspace_ref=workspace.id,
            objective=f"[VOICE] {action}: {summary}",
            scope=json.dumps(scope_payload, default=str),
            requested_decision=f"APPROVE_VOICE_{action}",
            assumptions=[f"voice transcript: {scope_payload['transcript']}"],
            alternatives=["EDIT the request", "REJECT the request"],
        )
        self.store.update_event(event_id, proposal_id=proposal.proposal_id,
                                status="PROPOSED")

        voice_proposal = {
            "proposal_id": proposal.proposal_id,
            "intent_id": intent.get("intent_id"),
            "context_id": context.get("context_id"),
            "requested_action": f"{action}: {summary}",
            "risk_level": RISK_LEVELS.get(action),
            "authority_status": "GOVERN_AUTHORITY_REQUIRED",
            "authorization_status": "PENDING_APPROVAL",
            "required_approval": True,
            "status": proposal.proposal_status,
            "executor": executor.get("label") if executor else "UNSUPPORTED",
            "detail": {
                "executor": executor,
                "event_id": event_id,
                "transcript": scope_payload["transcript"],
                "warning": None if executor else "NO_CANONICAL_EXECUTOR",
            },
        }
        self.store.append_stage(
            event_id,
            stage=VoiceStage.PROPOSAL.value,
            record_type="Proposal",
            record_id=proposal.proposal_id,
            payload={"proposal": proposal.to_dict(), "voice_proposal": voice_proposal},
        )
        return {
            "proposal": proposal.to_dict(),
            "voice_proposal": voice_proposal,
            "required_approval": True,
        }

    # ── Phase 8 (human controls): APPROVE / REJECT / EDIT ───────────────────

    def decide(self, user: dict[str, Any], event_id: str, decision: str) -> dict[str, Any]:
        subject = str(user["uid"])
        event = self._event_or_raise(event_id, subject)
        proposal_id = event.get("proposal_id")
        if not proposal_id:
            raise VoiceError("PROPOSAL_REQUIRED", "no proposal exists for this event",
                             event_id=event_id)
        manager = get_proposal_manager_or_raise()
        proposal = manager.get_proposal(proposal_id, subject)
        if proposal is None:
            raise VoiceError("PROPOSAL_REQUIRED", "proposal not found for this subject",
                             event_id=event_id)
        decision_u = (decision or "").strip().upper()
        try:
            updated = manager.record_decision(
                proposal_id=proposal_id, subject_ref=subject, decision=decision_u,
            )
        except ValueError as exc:
            raise VoiceError("APPROVAL_REQUIRED", str(exc), event_id=event_id)

        approval_id = updated.decision_ref
        self.store.update_event(
            event_id,
            approval_ref=approval_id,
            status="APPROVED" if decision_u == "ACCEPTED" else "REJECTED",
        )
        self.store.append_stage(
            event_id,
            stage=VoiceStage.APPROVAL.value,
            record_type="Approval",
            record_id=approval_id or new_id("AP"),
            payload={
                "decision": decision_u,
                "decision_ref": approval_id,
                "proposal_id": proposal_id,
                "proposal_status": updated.proposal_status,
                "decided_by": subject,
                "boundary": "A human decision is not authorization; "
                            "ACCEPTED still requires the authority step.",
            },
        )
        return {"proposal": updated.to_dict(), "decision": decision_u,
                "approval_id": approval_id}

    def revise(self, user: dict[str, Any], event_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        """EDIT: withdraw the pending proposal and present a revised one."""
        subject = str(user["uid"])
        event = self._event_or_raise(event_id, subject)
        proposal_id = event.get("proposal_id")
        if not proposal_id:
            raise VoiceError("PROPOSAL_REQUIRED", "no proposal exists to edit",
                             event_id=event_id)
        manager = get_proposal_manager_or_raise()
        old = manager.get_proposal(proposal_id, subject)
        if old is None:
            raise VoiceError("PROPOSAL_REQUIRED", "proposal not found for this subject",
                             event_id=event_id)
        if old.authorization_ref:
            raise VoiceError("AUTHORIZATION_DENIED",
                             "proposal already authorized — withdrawal is a separate act",
                             event_id=event_id)
        if old.proposal_status not in {"DECLINED", "WITHDRAWN"}:
            old = manager.record_decision(
                proposal_id=proposal_id, subject_ref=subject, decision="WITHDRAWN",
            )

        from solspire.workspace_manager import get_workspace_manager
        workspace = get_workspace_manager().get_or_create(subject)
        reason = str(changes.get("reason") or "operator edit")
        scope = json.loads(old.scope) if old.scope and old.scope.startswith("{") else {}
        scope["supersedes"] = old.proposal_id
        scope["revision_reason"] = reason
        if changes.get("requested_action"):
            scope["requested_action_edit"] = changes["requested_action"]
        new = manager.create_proposal(
            subject_ref=subject,
            workspace_ref=workspace.id,
            objective=str(changes.get("objective") or old.objective),
            scope=json.dumps(scope, default=str),
            requested_decision=str(changes.get("requested_decision") or old.requested_decision),
            assumptions=list(old.assumptions) + [f"revision of {old.proposal_id}: {reason}"],
            alternatives=list(old.alternatives),
        )
        self.store.update_event(event_id, proposal_id=new.proposal_id,
                                approval_ref=None, status="PROPOSED")
        self.store.append_stage(
            event_id,
            stage=VoiceStage.PROPOSAL.value,
            record_type="ProposalRevision",
            record_id=new.proposal_id,
            payload={
                "supersedes": old.proposal_id,
                "reason": reason,
                "proposal": new.to_dict(),
            },
        )
        return {"proposal": new.to_dict(), "supersedes": old.proposal_id}

    # ── authorization (govern authority) ────────────────────────────────────

    def authorize(self, user: dict[str, Any], event_id: str) -> dict[str, Any]:
        subject = str(user["uid"])
        event = self._event_or_raise(event_id, subject)
        proposal_id = event.get("proposal_id")
        if not proposal_id:
            raise VoiceError("PROPOSAL_REQUIRED", "no proposal exists for this event",
                             event_id=event_id)

        intent = event.get("intent") or {}
        context = event.get("context") or {}
        executor = self._executor_for(intent, context)
        tools = list(executor.get("tools", [])) if executor else []
        scope = {
            "tools": tools + ["voice.pipeline"],
            "channel": "voice_execution_runtime",
            "voice_event_id": event_id,
        }
        constraints = {
            "network": False,
            "repository_root": ".",
            "channel": "voice_execution_runtime",
            "read_only": bool(executor.get("read_only")) if executor else False,
        }

        from fastapi import HTTPException
        from solspire.console_authority_router import (
            AuthorizationRequest,
            authorize_proposal_sync,
        )
        try:
            result = authorize_proposal_sync(
                proposal_id,
                AuthorizationRequest(scope=scope, constraints=constraints),
                user,
            )
        except HTTPException as exc:
            if exc.status_code == 403:
                raise self._fail(event_id, subject, "AUTHORIZATION_DENIED",
                                 str(exc.detail))
            if exc.status_code == 409:
                raise VoiceError("APPROVAL_REQUIRED", str(exc.detail), event_id=event_id)
            if exc.status_code == 404:
                raise VoiceError("PROPOSAL_REQUIRED", str(exc.detail), event_id=event_id)
            raise VoiceError("AUTHORIZATION_DENIED", str(exc.detail), event_id=event_id)

        authorization = result.get("authorization") or {}
        self.store.update_event(event_id, authorization_ref=authorization.get("id"),
                                status="AUTHORIZED")
        self.store.append_stage(
            event_id,
            stage=VoiceStage.AUTHORIZATION.value,
            record_type="Authorization",
            record_id=authorization.get("id") or new_id("AZ"),
            payload={
                "authorization": authorization,
                "human_authority_event": result.get("human_authority_event"),
                "scope": scope,
                "constraints": constraints,
                "boundary": result.get("note"),
            },
        )
        return {
            "authorization": authorization,
            "human_authority_event": result.get("human_authority_event"),
            "voice_proposal_authorization_status": "AUTHORIZED",
        }

    # ── Phase 9: execution through the canonical executor ───────────────────

    @staticmethod
    def _wait_for_execution(execution_id: str, owner: str,
                            timeout: float = EXECUTION_WAIT_SECONDS):
        from solspire.execution_runtime import ExecutionStatus, get_runtime
        deadline = time.time() + timeout
        while time.time() < deadline:
            execution = get_runtime().get(execution_id, owner_uid=owner)
            if execution is None:
                return None
            if execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED,
                                    ExecutionStatus.CANCELLED):
                return execution
            time.sleep(0.05)
        return get_runtime().get(execution_id, owner_uid=owner)

    def execute(self, user: dict[str, Any], event_id: str) -> dict[str, Any]:
        from solspire.execution_runtime import Plan, get_runtime
        from solspire.workevent_manager import get_workevent_manager
        from weaver.enterprise_orchestration import EnterpriseOrchestrationStore

        subject = str(user["uid"])
        event = self._event_or_raise(event_id, subject)
        intent = event.get("intent")
        context = event.get("context")
        if not intent or not context:
            raise VoiceError("INTENT_UNKNOWN", "understand this event before executing",
                             event_id=event_id)
        if intent.get("entities", {}).get("human_only"):
            raise self._fail(event_id, subject, "AUTHORITY_MISSING",
                             "human-only operation refused at the voice boundary")
        if intent.get("action") == "UNKNOWN":
            raise self._fail(event_id, subject, "INTENT_UNKNOWN",
                             "no canonical intent matched the transcript")
        if context.get("resolution_status") == "UNAUTHORIZED":
            raise self._fail(event_id, subject, "AUTHORIZATION_DENIED",
                             "resolved target is not owned by this subject")
        if context.get("resolution_status") in {"AMBIGUOUS", "UNKNOWN"}:
            raise VoiceError("CONTEXT_AMBIGUOUS",
                             "context is not resolved — clarify before executing",
                             event_id=event_id)

        action = intent.get("action")
        required = requires_approval(action)
        store = EnterpriseOrchestrationStore()

        if not required:
            return self._execute_observation(subject, event_id, event, intent, context)

        proposal = None
        authorization = None
        attempt = None

        if required:
            proposal_id = event.get("proposal_id")
            if not proposal_id:
                raise VoiceError("PROPOSAL_REQUIRED",
                                 "consequential requests require an explicit proposal",
                                 event_id=event_id)
            from solspire.proposal_manager import get_proposal_manager
            proposal = get_proposal_manager().get_proposal(proposal_id, subject)
            if proposal is None:
                raise VoiceError("PROPOSAL_REQUIRED", "proposal not found",
                                 event_id=event_id)
            if proposal.proposal_status != "ACCEPTED":
                raise VoiceError(
                    "APPROVAL_REQUIRED",
                    f"proposal status is {proposal.proposal_status} — a human "
                    "decision (APPROVE) is required before execution",
                    event_id=event_id, proposal_id=proposal_id,
                )
            if not proposal.authorization_ref:
                raise VoiceError(
                    "AUTHORIZATION_REQUIRED",
                    "proposal is ACCEPTED but not authorized — authorize first",
                    event_id=event_id, proposal_id=proposal_id,
                )
            authorization = store.authorization(
                subject=subject, authorization_id=proposal.authorization_ref,
            )

        executor = self._executor_for(intent, context)

        def _blocked(reason: str) -> None:
            """Record a BLOCKED execution attempt + evidence, then raise."""
            attempt_ref = None
            if authorization is not None:
                attempt = store.execution_attempt(
                    subject=subject, authorization_id=authorization.id,
                    tool_channel="voice.execution_runtime",
                    request_payload={"event_id": event_id, "reason": reason},
                    result_status="ATTEMPTED",
                )
                attempt_ref = attempt.id
            evidence = store.evidence(
                subject=subject,
                evidence_type="voice_execution_blocked",
                content_or_ref={"event_id": event_id, "reason": reason,
                                "intent": intent, "context": context},
                execution_attempt_id=attempt_ref,
                source_ref=None if attempt_ref else f"voice-event:{event_id}",
            )
            if attempt_ref:
                store.complete_execution_attempt(
                    subject=subject, execution_attempt_id=attempt_ref,
                    result_status="BLOCKED",
                )
            self.store.update_event(event_id, evidence_ref=evidence.id, status="FAILED")
            self.store.append_stage(
                event_id,
                stage=VoiceStage.EVIDENCE.value,
                record_type="Evidence",
                record_id=evidence.id,
                payload={"evidence_id": evidence.id, "kind": "blocked",
                         "reason": reason},
            )

        if executor is None:
            reason = ("NO_CANONICAL_EXECUTOR: no canonical executor exists for this "
                      "action/entity combination")
            _blocked(reason)
            raise self._fail(event_id, subject, "EXECUTION_FAILED", reason)

        # Scope validation: the executed tool must be inside the authorization.
        if authorization is not None:
            scope = authorization.scope if isinstance(authorization.scope, dict) else {}
            allowed = scope.get("tools") or []
            for tool in executor["tools"]:
                if tool not in allowed:
                    reason = f"tool '{tool}' is outside the authorization scope {allowed}"
                    _blocked(reason)
                    raise self._fail(event_id, subject, "AUTHORIZATION_DENIED", reason)

        if authorization is not None:
            attempt = store.execution_attempt(
                subject=subject, authorization_id=authorization.id,
                tool_channel="voice.execution_runtime",
                request_payload={"event_id": event_id, "steps": executor["steps"]},
                result_status="ATTEMPTED",
            )

        plan = Plan(
            id=new_id("PLAN"),
            request=str((event.get("transcript") or {}).get("text") or ""),
            intent=str(action),
            steps=executor["steps"],
        )
        try:
            started = get_runtime().execute(plan, owner_uid=subject)
        except PermissionError as exc:
            reason = str(exc)
            _blocked(reason)
            raise self._fail(event_id, subject, "EXECUTION_FAILED", reason)

        execution = self._wait_for_execution(started.id, subject)
        if execution is None:
            ok = False
            results: list[dict[str, Any]] = []
            exec_error = "execution record disappeared before completion"
            exec_status = "missing"
            exec_id = started.id
        else:
            results = list(execution.results)
            failing = next((r for r in results if not r.get("ok", True)), None)
            # The canonical runtime can end COMPLETED after a retryable step
            # failure; voice success requires the terminal status AND every
            # step to have reported ok.
            ok = execution.status.value == "completed" and failing is None
            exec_error = execution.error or (
                failing.get("error") if failing else None
            )
            exec_status = execution.status.value
            exec_id = execution.id
        result = {
            "execution_id": exec_id,
            "status": exec_status,
            "steps": results,
            "error": exec_error,
            "executor_channel": executor["channel"],
            "executor_label": executor["label"],
        }

        # Canonical evidence record (enterprise store) — always.
        if attempt is not None:
            evidence = store.evidence(
                subject=subject,
                execution_attempt_id=attempt.id,
                evidence_type="voice_execution",
                content_or_ref={
                    "event_id": event_id,
                    "proposal_id": event.get("proposal_id"),
                    "authorization_id": getattr(authorization, "id", None),
                    "result": result,
                },
            )
            store.complete_execution_attempt(
                subject=subject, execution_attempt_id=attempt.id,
                result_status="SUCCEEDED" if ok else "FAILED",
            )
        else:
            evidence = store.evidence(
                subject=subject,
                evidence_type="voice_observation",
                content_or_ref={"event_id": event_id, "result": result},
                source_ref=f"voice-event:{event_id}",
            )

        # Canonical WorkEvent. For authorized executions the enterprise store
        # already captures one 1:1 with the execution attempt
        # (weaver/execution_workevent_bridge via complete_execution_attempt);
        # we REFERENCE it instead of creating a second one. Observation-only
        # executions have no attempt, so the voice chain records the WorkEvent.
        from solspire.workspace_manager import get_workspace_manager
        workspace = get_workspace_manager().get_or_create(subject)
        work_event = None
        if attempt is not None:
            work_event = get_workevent_manager().get_by_execution_attempt(
                attempt.id, subject,
            )
        if work_event is None:
            artifact_refs = [f"voice-event:{event_id}", f"voice-evidence:{evidence.id}"]
            if event.get("proposal_id"):
                artifact_refs.append(f"proposal:{event['proposal_id']}")
            work_event = get_workevent_manager().create(
                subject_ref=subject,
                workspace_ref=workspace.id,
                event_type="VOICE_EXECUTION" if required else "VOICE_OBSERVATION",
                occurred_at=time.time(),
                execution_attempt_ref=None,
                actor_ref=subject,
                artifact_refs=artifact_refs,
                decision_ref=event.get("approval_ref"),
                scope_ref=f"voice-action:{action}",
                state_after_ref=f"sha256:{canonical_digest(result)}",
                status="RECORDED",
            )

        stages_before = self.store.list_stages(event_id)
        self.store.append_stage(
            event_id,
            stage=VoiceStage.EXECUTION.value,
            record_type="Execution",
            record_id=result["execution_id"],
            payload={
                "execution": result,
                "proposal_id": event.get("proposal_id"),
                "approval_id": event.get("approval_ref"),
                "authorization_id": getattr(authorization, "id", None),
                "execution_attempt_id": getattr(attempt, "id", None),
                "executor": executor,
            },
        )
        self.store.append_stage(
            event_id,
            stage=VoiceStage.RESULT.value,
            record_type="Result",
            record_id=new_id("RS"),
            payload={"ok": ok, "result": result},
        )
        self.store.append_stage(
            event_id,
            stage=VoiceStage.WORK_EVENT.value,
            record_type="WorkEvent",
            record_id=work_event.work_event_id,
            payload=work_event.to_dict(),
        )
        stages = self.store.list_stages(event_id)
        digest = chain_digest(stages)
        self.store.append_stage(
            event_id,
            stage=VoiceStage.EVIDENCE.value,
            record_type="Evidence",
            record_id=evidence.id,
            payload={
                "evidence_id": evidence.id,
                "evidence_type": getattr(evidence, "evidence_type", ""),
                "chain_digest": digest,
                "stages_before": len(stages_before) + 1,
                "verification_state": "PENDING",
                "boundary": "Execution is not verification: a successful executor "
                            "response is not verified real-world completion.",
            },
        )
        self.store.update_event(
            event_id,
            execution_id=result["execution_id"],
            work_event_id=work_event.work_event_id,
            evidence_ref=evidence.id,
            status="EXECUTED" if ok else "FAILED",
        )

        if not ok:
            detail = result.get("error") or f"execution ended in status {result['status']}"
            raise self._fail(event_id, subject, "EXECUTION_FAILED", detail)

        return {
            "execution": result,
            "work_event": work_event.to_dict(),
            "evidence_id": evidence.id,
            "chain_digest": digest,
            "verification_state": "PENDING",
        }

    # ── observation-only execution (ASK / SEARCH) ─────────────────────────────

    def _execute_observation(
        self,
        subject: str,
        event_id: str,
        event: dict[str, Any],
        intent: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an informational request as an observation.

        No proposal, approval or authorization is required for observation-only
        actions (Engineering Lab voice boundary, READ disposition). The result is
        still recorded as canonical evidence + a canonical WorkEvent so the
        chain stays complete for every request.
        """
        from solspire.workevent_manager import get_workevent_manager
        from solspire.workspace_manager import get_workspace_manager
        from weaver.enterprise_orchestration import EnterpriseOrchestrationStore

        resolved = (context.get("resolved_entities") or {})
        query = str(resolved.get("query") or
                    (intent.get("entities") or {}).get("query") or
                    (event.get("transcript") or {}).get("text") or "")
        matches: list[dict[str, Any]] = []
        search_error: str | None = None
        try:
            from knowledge.search import fulltext_search
            matches = fulltext_search(query, limit=10, user_id=subject)
        except Exception as exc:  # observation must still record its failure
            logger.warning("[voice] observation search failed: %s", exc)
            search_error = str(exc)

        ok = search_error is None
        observation = {
            "query": query,
            "count": len(matches),
            "matches": [
                {"title": m.get("title"), "type": m.get("note_type")}
                for m in matches
            ],
            "error": search_error,
        }
        execution_id = new_id("OBS")
        executor = {
            "channel": "knowledge_search",
            "label": "Knowledge observation (read-only)",
            "tools": ["knowledge.search"],
            "steps": [],
            "read_only": True,
        }
        result = {
            "execution_id": execution_id,
            "status": "completed" if ok else "failed",
            "steps": [],
            "error": search_error,
            "executor_channel": executor["channel"],
            "executor_label": executor["label"],
            "observation": observation,
        }

        store = EnterpriseOrchestrationStore()
        evidence = store.evidence(
            subject=subject,
            evidence_type="voice_observation",
            content_or_ref={"event_id": event_id, "result": result},
            source_ref=f"voice-event:{event_id}",
        )
        workspace = get_workspace_manager().get_or_create(subject)
        work_event = get_workevent_manager().create(
            subject_ref=subject,
            workspace_ref=workspace.id,
            event_type="VOICE_OBSERVATION",
            occurred_at=time.time(),
            execution_attempt_ref=None,
            actor_ref=subject,
            artifact_refs=[f"voice-event:{event_id}", f"voice-evidence:{evidence.id}"],
            scope_ref=f"voice-action:{intent.get('action')}",
            state_after_ref=f"sha256:{canonical_digest(result)}",
            status="RECORDED",
        )
        self.store.append_stage(
            event_id,
            stage=VoiceStage.EXECUTION.value,
            record_type="Execution",
            record_id=execution_id,
            payload={
                "execution": result,
                "proposal_id": None,
                "approval_id": None,
                "authorization_id": None,
                "executor": executor,
                "policy": "observation-only: no proposal, approval or "
                          "authorization required",
            },
        )
        self.store.append_stage(
            event_id,
            stage=VoiceStage.RESULT.value,
            record_type="Result",
            record_id=new_id("RS"),
            payload={"ok": ok, "result": result},
        )
        self.store.append_stage(
            event_id,
            stage=VoiceStage.WORK_EVENT.value,
            record_type="WorkEvent",
            record_id=work_event.work_event_id,
            payload=work_event.to_dict(),
        )
        digest = chain_digest(self.store.list_stages(event_id))
        self.store.append_stage(
            event_id,
            stage=VoiceStage.EVIDENCE.value,
            record_type="Evidence",
            record_id=evidence.id,
            payload={
                "evidence_id": evidence.id,
                "evidence_type": "voice_observation",
                "chain_digest": digest,
                "verification_state": "PENDING",
                "boundary": "Execution is not verification.",
            },
        )
        self.store.update_event(
            event_id,
            execution_id=execution_id,
            work_event_id=work_event.work_event_id,
            evidence_ref=evidence.id,
            status="EXECUTED" if ok else "FAILED",
        )
        if not ok:
            raise self._fail(event_id, subject, "EXECUTION_FAILED",
                             search_error or "observation failed")
        return {
            "execution": result,
            "work_event": work_event.to_dict(),
            "evidence_id": evidence.id,
            "chain_digest": digest,
            "verification_state": "PENDING",
        }

    # ── Phase 10: verification (separate human act) ─────────────────────────

    def verify(self, user: dict[str, Any], event_id: str, verdict: str,
               claim: str = "") -> dict[str, Any]:
        from weaver.enterprise_orchestration import (
            VERIFICATION_VERDICTS,
            EnterpriseOrchestrationStore,
        )

        subject = str(user["uid"])
        event = self._event_or_raise(event_id, subject)
        evidence_ref = event.get("evidence_ref")
        if not evidence_ref:
            raise VoiceError("VERIFICATION_PENDING",
                             "no evidence exists yet — execute first", event_id=event_id)
        verdict_u = (verdict or "").strip().upper()
        if verdict_u not in VERIFICATION_VERDICTS:
            raise VoiceError("VERIFICATION_FAILED",
                             f"unsupported verdict '{verdict}' — "
                             f"expected one of {sorted(VERIFICATION_VERDICTS)}",
                             event_id=event_id)

        store = EnterpriseOrchestrationStore()
        verification = store.verify(
            subject=subject,
            claim=claim or f"Voice execution for {event_id} produced the recorded result.",
            evidence_refs=[evidence_ref],
            verifier=f"voice-console:{subject}",
            verdict=verdict_u,
        )
        self.store.update_event(
            event_id,
            verification_ref=verification.id,
            error_state=None if verdict_u == "VERIFIED" else "VERIFICATION_FAILED",
            error_detail=None if verdict_u == "VERIFIED"
            else f"verification verdict {verdict_u}",
        )
        self.store.append_stage(
            event_id,
            stage=VoiceStage.VERIFICATION.value,
            record_type="Verification",
            record_id=verification.id,
            payload={
                "verification": verification.to_dict(),
                "boundary": "Verification is a separate human act from execution "
                            "and from evidence.",
            },
        )
        return {"verification": verification.to_dict(), "verdict": verdict_u}

    # ── reads ───────────────────────────────────────────────────────────────

    def get(self, user: dict[str, Any], event_id: str) -> dict[str, Any]:
        subject = str(user["uid"])
        event = self._event_or_raise(event_id, subject)
        stages = self.store.list_stages(event_id)
        return {
            "event": _event_payload(event),
            "chain": [stage.to_dict() for stage in stages],
            "chain_digest": chain_digest(stages),
            "stage_order": [stage.value for stage in VoiceStage],
        }

    def list(self, user: dict[str, Any], session_id: str | None = None,
             limit: int = 50) -> dict[str, Any]:
        subject = str(user["uid"])
        events = self.store.list_events(subject, session_id=session_id, limit=limit)
        return {"events": [_event_payload(e) for e in events], "count": len(events)}

    def chain(self, user: dict[str, Any], event_id: str) -> dict[str, Any]:
        subject = str(user["uid"])
        self._event_or_raise(event_id, subject)
        stages = self.store.list_stages(event_id)
        return {
            "event_id": event_id,
            "stages": [stage.to_dict() for stage in stages],
            "chain_digest": chain_digest(stages),
        }

    def audio(self, user: dict[str, Any], event_id: str):
        subject = str(user["uid"])
        self._event_or_raise(event_id, subject)
        return self.store.get_audio(event_id, subject)


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Compose the VoiceEvent contract shape (asr_provenance from the transcript)."""
    payload = dict(event)
    transcript = payload.get("transcript")
    if transcript:
        payload["asr_provenance"] = {
            "provider": transcript.get("provider"),
            "model": transcript.get("model"),
            **(transcript.get("provenance") or {}),
        }
    else:
        payload["asr_provenance"] = {"state": "PENDING"}
    return payload


def get_proposal_manager_or_raise():
    from solspire.proposal_manager import get_proposal_manager
    return get_proposal_manager()


_PIPELINE = VoicePipeline()


def get_voice_pipeline() -> VoicePipeline:
    return _PIPELINE


__all__ = ["VoiceError", "VoicePipeline", "get_voice_pipeline", "VoiceEvent",
           "MAX_AUDIO_BYTES"]
