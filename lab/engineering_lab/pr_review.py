"""ARKADIA-CHIEF-PR-REVIEW-001 — the governed PR-review capability.

This is a **capability of the existing canonical Chief identity**
(``ARKADIA-CHIEF-001``, ``executive_office``). It creates no second agent, no
second conversation, no second memory store, no second workspace, no second
authorization engine and no second evidence architecture:

  * identity       -> the caller's verified principal (a Firebase uid resolved by
                      ``api.auth.require_auth``); the Chief principal is named,
                      never minted here.
  * execution      -> the Engineering Lab boundary. Every run is a Lab job with
                      Lab evidence (``el_evidence``) and Lab human authorizations
                      (``el_authorizations``).
  * evidence       -> :class:`lab.engineering_lab.contracts.EvidenceRecord`.
  * authorization  -> the Lab's human-originated grant store. This module can
                      *verify* a grant; it cannot create one.
  * policy         -> injected. The canonical mutation-boundary policy is the
                      API layer's to wire; this module never re-implements it.

Boundary doctrine, extending the Lab's own non-collapses:

    REVIEW      != APPROVAL
    APPROVAL    != MERGE
    GREEN       != MERGE AUTHORIZATION
    SHADOW      != ACTIVATED
    IMPLEMENTED != TESTED

A GREEN review means "evidence-backed, eligible for a separately authorized
next step". It is never an authorization for one.
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Iterable, Sequence

from .contracts import BoundaryViolation, EvidenceRecord, utc_now
from .runtime import authorization_is_usable
from .github_app import (
    GitHubAppWorker,
    GitHubReader,
    GitHubUnavailable,
    PullRequestSnapshot,
    RateLimited,
)

SCHEMA = "arkadia.lab.pr_review/1"

#: The capability id. It is a capability *of* the canonical Chief, not a new one.
CAPABILITY_ID = "chief.pr_review"

#: The existing canonical Chief identity (``executive_office``). Named as a
#: string so this layer does not import the identity package; nothing here
#: creates or renames an identity.
OWNER_PRINCIPAL = "ARKADIA-CHIEF-001"

#: Review outcomes. Deliberately three, and deliberately not a progression.
GREEN = "GREEN"
AMBER = "AMBER"
RED = "RED"
REVIEW_STATUSES: tuple[str, ...] = (GREEN, AMBER, RED)

#: Rollout vocabulary. Reported, never inferred.
ROLLOUT_STATES: tuple[str, ...] = ("DESIGNED", "IMPLEMENTED", "TESTED", "SHADOW", "ACTIVATED")

# -- actions and their separate gates ----------------------------------------

READ = "READ"
GENERATE_FINDINGS = "GENERATE_FINDINGS"
PUBLISH_COMMENT = "PUBLISH_COMMENT"
REQUEST_CHANGES = "REQUEST_CHANGES"
APPROVE = "APPROVE"
MERGE = "MERGE"

REVIEW_ACTIONS: tuple[str, ...] = (
    READ,
    GENERATE_FINDINGS,
    PUBLISH_COMMENT,
    REQUEST_CHANGES,
    APPROVE,
    MERGE,
)


@dataclass(frozen=True)
class ActionGate:
    """One capability's gate. Separate gates are the point of the contract."""

    action: str
    minimum_stage: str
    writes_github: bool
    human_only: bool
    permission: str
    requires_policy_flag: str | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "minimum_stage": self.minimum_stage,
            "writes_github": self.writes_github,
            "human_only": self.human_only,
            "permission": self.permission,
            "requires_policy_flag": self.requires_policy_flag,
            "description": self.description,
        }


ACTION_GATES: dict[str, ActionGate] = {
    READ: ActionGate(
        action=READ,
        minimum_stage="IMPLEMENTED",
        writes_github=False,
        human_only=False,
        permission="read_repository",
        description="Inspect the repository and pull request. No write of any kind.",
    ),
    GENERATE_FINDINGS: ActionGate(
        action=GENERATE_FINDINGS,
        minimum_stage="IMPLEMENTED",
        writes_github=False,
        human_only=False,
        permission="read_pull_request",
        description="Produce structured findings in the Lab. No GitHub write.",
    ),
    PUBLISH_COMMENT: ActionGate(
        action=PUBLISH_COMMENT,
        minimum_stage="ACTIVATED",
        writes_github=True,
        human_only=False,
        permission="publish_review",
        requires_policy_flag="allows_comment",
        description="Post the review as a GitHub comment. Requires an exact-tuple human grant.",
    ),
    REQUEST_CHANGES: ActionGate(
        action=REQUEST_CHANGES,
        minimum_stage="ACTIVATED",
        writes_github=True,
        human_only=False,
        permission="publish_review",
        requires_policy_flag="allows_request_changes",
        description="Submit a REQUEST_CHANGES review. Requires an exact-tuple human grant.",
    ),
    APPROVE: ActionGate(
        action=APPROVE,
        minimum_stage="ACTIVATED",
        writes_github=True,
        human_only=False,
        permission="publish_review",
        requires_policy_flag="allows_approve",
        description=(
            "Submit an APPROVE review. Requires activation, an independent "
            "principal, and an exact-tuple human grant. Never implied by GREEN."
        ),
    ),
    MERGE: ActionGate(
        action=MERGE,
        minimum_stage="ACTIVATED",
        writes_github=True,
        human_only=True,
        permission="merge_protected_branch",
        description=(
            "Merge. Human-only at every stage: this substrate refuses it "
            "unconditionally, including when a review is GREEN."
        ),
    ),
}

#: Actions that may never be performed by this capability, at any stage.
STRUCTURALLY_REFUSED: frozenset[str] = frozenset({MERGE})

#: Findings with this disposition block (RED).
BLOCK = "block"
#: Findings with this disposition require a human decision (AMBER).
HUMAN_DECISION = "human_decision"
#: Findings that are recorded without changing the status.
NOTE = "note"

SEVERITIES: tuple[str, ...] = ("info", "low", "medium", "high", "critical")

#: Check conclusions that are failures for review purposes.
FAILING_CONCLUSIONS: frozenset[str] = frozenset(
    {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}
)

#: Credential *shapes*. A review heuristic that points a human at a diff line —
#: not a second secret scanner and not a merge gate.
SECRET_SHAPES: tuple[re.Pattern[str], ...] = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
)


# -- policy ------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewPolicy:
    """The server-side policy this capability enforces.

    Every default is the most restrictive value. Nothing here can be widened by
    a request; a request supplies *facts* (repository, PR, SHAs), never policy.
    """

    policy_id: str = "ARK-CHIEF-PR-REVIEW-001"
    policy_version: int = 1
    stage: str = "IMPLEMENTED"
    repositories: tuple[str, ...] = ()
    required_checks: tuple[str, ...] = ()
    allows_comment: bool = False
    allows_request_changes: bool = False
    allows_approve: bool = False
    activation_ref: str | None = None
    test_evidence_ref: str | None = None
    stage_conflict: str | None = None

    def fingerprint(self) -> str:
        material = "|".join(
            [
                self.policy_id,
                str(self.policy_version),
                self.stage,
                ",".join(sorted(self.repositories)),
                ",".join(self.required_checks),
                str(self.allows_comment),
                str(self.allows_request_changes),
                str(self.allows_approve),
                self.activation_ref or "",
            ]
        )
        return hashlib.sha256(material.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_fingerprint": self.fingerprint(),
            "stage": self.stage,
            "repositories": list(self.repositories),
            "required_checks": list(self.required_checks),
            "allows_comment": self.allows_comment,
            "allows_request_changes": self.allows_request_changes,
            "allows_approve": self.allows_approve,
            "activation_ref": self.activation_ref,
            "test_evidence_ref": self.test_evidence_ref,
            "stage_conflict": self.stage_conflict,
        }

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "ReviewPolicy":
        env = environ if environ is not None else os.environ
        raw_stage = (env.get("ARKADIA_PR_REVIEW_STAGE") or "SHADOW").strip().upper()
        stage_conflict: str | None = None
        if raw_stage not in ROLLOUT_STATES:
            # An unrecognised stage is a policy conflict, not a default-allow.
            stage_conflict = (
                f"unrecognised ARKADIA_PR_REVIEW_STAGE {raw_stage!r}; "
                "falling back to the most restrictive stage"
            )
            raw_stage = "IMPLEMENTED"
        repositories = tuple(
            item.strip()
            for item in (env.get("ARKADIA_PR_REVIEW_REPOSITORIES") or "").split(",")
            if item.strip()
        )
        required = tuple(
            item.strip()
            for item in (env.get("ARKADIA_PR_REVIEW_REQUIRED_CHECKS") or "").split(",")
            if item.strip()
        )
        return cls(
            stage=raw_stage,
            repositories=repositories,
            required_checks=required,
            allows_comment=(env.get("ARKADIA_PR_REVIEW_ALLOW_COMMENT") or "").lower() == "true",
            allows_request_changes=(
                env.get("ARKADIA_PR_REVIEW_ALLOW_REQUEST_CHANGES") or ""
            ).lower()
            == "true",
            allows_approve=(env.get("ARKADIA_PR_REVIEW_ALLOW_APPROVE") or "").lower() == "true",
            activation_ref=(env.get("ARKADIA_PR_REVIEW_ACTIVATION_REF") or "").strip() or None,
            test_evidence_ref=(env.get("ARKADIA_PR_REVIEW_TEST_EVIDENCE_REF") or "").strip()
            or None,
            stage_conflict=stage_conflict,
        )


_STAGE_ORDER: dict[str, int] = {name: index for index, name in enumerate(ROLLOUT_STATES)}


def stage_reaches(stage: str, minimum: str) -> bool:
    """True when *stage* is at or beyond *minimum* in the declared vocabulary."""
    return _STAGE_ORDER.get(stage, -1) >= _STAGE_ORDER.get(minimum, len(ROLLOUT_STATES))


def assert_action_permitted(action: str, policy: ReviewPolicy) -> ActionGate:
    """The single dispatch gate for every review action.

    Fails closed: an unknown action, a structurally refused action, a stage that
    has not been reached, or a policy flag that is not set all raise.
    """
    if action not in ACTION_GATES:
        raise BoundaryViolation(f"unknown review action '{action}'")
    gate = ACTION_GATES[action]
    if action in STRUCTURALLY_REFUSED:
        raise BoundaryViolation(
            f"'{action}' is human-only; this substrate refuses it unconditionally, "
            "including when a review is GREEN"
        )
    if not stage_reaches(policy.stage, gate.minimum_stage):
        raise BoundaryViolation(
            f"'{action}' requires rollout stage '{gate.minimum_stage}'; the active "
            f"policy stage is '{policy.stage}'"
        )
    if gate.requires_policy_flag and not bool(getattr(policy, gate.requires_policy_flag, False)):
        raise BoundaryViolation(
            f"'{action}' requires policy flag '{gate.requires_policy_flag}', which is "
            "not set in the active policy"
        )
    return gate


def rollout_state(policy: ReviewPolicy, worker: GitHubAppWorker) -> dict[str, Any]:
    """Derive the rollout state from *evidence*, never from intent.

    Precedence is ACTIVATED > SHADOW > TESTED > IMPLEMENTED. Each step requires
    its own evidence; nothing is inferred from the code existing.
    """
    worker_state = worker.status()
    available = worker_state["state"] == "AVAILABLE"
    state = "IMPLEMENTED"
    basis = "the capability module exists and enforces its gates"
    if policy.test_evidence_ref:
        state = "TESTED"
        basis = f"test evidence recorded at {policy.test_evidence_ref}"
    if policy.stage == "SHADOW" and available:
        state = "SHADOW"
        basis = "shadow stage with a configured GitHub App worker; read-only"
    if policy.stage == "ACTIVATED" and available and policy.activation_ref:
        state = "ACTIVATED"
        basis = f"activated by {policy.activation_ref}"
    return {
        "state": state,
        "basis": basis,
        "policy_stage": policy.stage,
        "worker": worker_state["state"],
        "write_actions_enabled": [
            gate.action
            for gate in ACTION_GATES.values()
            if gate.writes_github
            and gate.action not in STRUCTURALLY_REFUSED
            and stage_reaches(policy.stage, gate.minimum_stage)
            and bool(getattr(policy, gate.requires_policy_flag or "", True))
        ],
        "merge_enabled": False,
        "merge_reason": "merge is human-only and structurally refused by this substrate",
        "stage_conflict": policy.stage_conflict,
    }


# -- capability manifest -----------------------------------------------------


#: Map from this capability's actions to the canonical Chief capability names
#: declared in ``executive_office/control.py``. Held as data rather than an
#: import so this layer does not depend on the identity package; the guard test
#: asserts it against the live envelope.
#:
#: ``None`` means the canonical envelope defines no delegated capability for the
#: action, so it cannot be reached through a Chief delegation at all — only
#: through a human grant. The capability introduces **no** new grantable
#: capability: widening that envelope is an authority-model change, which is a
#: reserved human decision.
CHIEF_CAPABILITY_MAP: dict[str, str | None] = {
    READ: "read_repository",
    GENERATE_FINDINGS: "produce_internal_reports",
    PUBLISH_COMMENT: None,
    REQUEST_CHANGES: None,
    APPROVE: "approve_request",
    MERGE: "merge_protected_branch",
}


def capability_manifest() -> dict[str, Any]:
    """The registry entry that makes this capability discoverable.

    Discovery is not authorization: the manifest declares what the capability
    *is*, and the gates decide what a caller may *do*.
    """
    return {
        "schema": SCHEMA,
        "capability_id": CAPABILITY_ID,
        "display_name": "Chief PR Review",
        "owner_principal": OWNER_PRINCIPAL,
        "summary": (
            "Evidence-backed, head-bound pull-request review executed through the "
            "Engineering Lab boundary under a dedicated GitHub App worker."
        ),
        "interfaces": ["arkana", "engineering_lab"],
        "chief_capability_map": dict(CHIEF_CAPABILITY_MAP),
        "requires_envelope_change": False,
        "reuses": {
            "identity": "api.auth.require_auth (verified Firebase uid)",
            "evidence": "lab.engineering_lab.contracts.EvidenceRecord",
            "authorization": "el_authorizations (human-originated Lab grants)",
            "jobs": "el_pr_review_jobs (canonical Lab SQLite store)",
        },
        "inputs": [
            "repository",
            "pr_number",
            "base_sha",
            "head_sha",
            "installation_id",
            "principal",
            "event_id",
            "policy_version",
        ],
        "outputs": [
            "findings (severity, path, line, evidence, disposition)",
            "status (GREEN | AMBER | RED)",
            "evidence_ref",
            "job_id",
        ],
        "actions": [ACTION_GATES[a].to_dict() for a in REVIEW_ACTIONS],
        "rollout_states": list(ROLLOUT_STATES),
        "default_mode": "shadow_read_only",
    }


def capability_registry() -> dict[str, Any]:
    return {"schema": SCHEMA, "capabilities": [capability_manifest()]}


# -- head binding ------------------------------------------------------------


class StaleHead(BoundaryViolation):
    """The live head no longer matches the reviewed head.

    A distinct type because a stale head is *not* a generic refusal: findings
    and approvals produced for the old head remain reconstructable, but they are
    no longer current.
    """


@dataclass(frozen=True)
class HeadBinding:
    """The exact tuple every finding, approval and evidence record binds to."""

    repository: str
    pr_number: int
    base_sha: str
    head_sha: str

    def __post_init__(self) -> None:
        if not self.repository or "/" not in self.repository:
            raise ValueError("binding requires an owner/name repository")
        if int(self.pr_number) <= 0:
            raise ValueError("binding requires a positive pull request number")
        if not self.head_sha or len(self.head_sha) < 7:
            raise ValueError("binding requires an exact head sha")
        if not self.base_sha or len(self.base_sha) < 7:
            raise ValueError("binding requires an exact base sha")

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "pr_number": self.pr_number,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
        }

    def scope_ref(self, action: str) -> str:
        """The grant scope for *action* on this exact tuple.

        Encoding the head into the scope is what makes a head change invalidate
        an approval: the old grant's scope no longer matches, so it is refused
        rather than silently reused.
        """
        return f"pr-review:{self.repository}#{self.pr_number}@{self.head_sha}:{action}"


def assert_head_current(reader: GitHubReader, binding: HeadBinding) -> str:
    """Re-fetch the live head and refuse a write when it moved."""
    live = reader.read_head_sha(binding.repository, binding.pr_number)
    if live != binding.head_sha:
        raise StaleHead(
            f"head moved from {binding.head_sha} to {live}; findings and approvals "
            "for the previous head are invalidated and a fresh review is required"
        )
    return live


# -- findings ----------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One structured finding. Every field is evidence, not opinion."""

    code: str
    severity: str
    title: str
    detail: str
    disposition: str
    path: str | None = None
    line: int | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"unknown severity '{self.severity}'")
        if self.disposition not in (BLOCK, HUMAN_DECISION, NOTE):
            raise ValueError(f"unknown disposition '{self.disposition}'")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "disposition": self.disposition,
            "path": self.path,
            "line": self.line,
            "evidence": dict(self.evidence),
        }

    def sort_key(self) -> tuple[str, str, int]:
        return (self.code, self.path or "", self.line or 0)


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def added_lines(patch: str | None) -> list[tuple[int, str]]:
    """Return ``(new_file_line_number, text)`` for added lines in a unified diff.

    This is what makes a finding trace to a real diff line: the number is the
    line in the post-change file, derived from the hunk header rather than
    counted from the top of the patch.
    """
    if not patch:
        return []
    lines: list[tuple[int, str]] = []
    new_line: int | None = None
    for raw in patch.splitlines():
        header = _HUNK.match(raw)
        if header:
            new_line = int(header.group(1))
            continue
        if new_line is None:
            continue
        if raw.startswith("+"):
            lines.append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-"):
            continue
        elif raw.startswith("\\"):
            continue
        else:
            new_line += 1
    return lines


def _finding_status(findings: Sequence[Finding], *, evidence_complete: bool) -> str:
    if any(f.disposition == BLOCK for f in findings):
        return RED
    if not evidence_complete:
        return AMBER
    if any(f.disposition == HUMAN_DECISION for f in findings):
        return AMBER
    return GREEN


# -- request / result --------------------------------------------------------


@dataclass(frozen=True)
class PrReviewRequest:
    """A review request. Facts only — never policy, never authority."""

    subject_ref: str
    principal: str
    repository: str
    pr_number: int
    base_sha: str
    head_sha: str
    installation_id: int | None
    event_id: str
    requested_action: str = GENERATE_FINDINGS
    job_id: str | None = None
    work_event_ref: str | None = None

    def binding(self) -> HeadBinding:
        return HeadBinding(
            repository=self.repository,
            pr_number=int(self.pr_number),
            base_sha=self.base_sha,
            head_sha=self.head_sha,
        )


@dataclass(frozen=True)
class PrReviewResult:
    """The capability's output. Immutable once produced."""

    job_id: str
    capability: str
    status: str
    binding: HeadBinding
    findings: tuple[Finding, ...]
    evidence_complete: bool
    stale: bool
    principal: str
    subject_ref: str
    policy: dict[str, Any]
    worker: dict[str, Any]
    authorization: dict[str, Any]
    snapshot: PullRequestSnapshot | None
    event_id: str
    work_event_ref: str | None
    evidence_ref: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "job_id": self.job_id,
            "capability": self.capability,
            "status": self.status,
            "binding": self.binding.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "counts": {
                "block": sum(1 for f in self.findings if f.disposition == BLOCK),
                "human_decision": sum(
                    1 for f in self.findings if f.disposition == HUMAN_DECISION
                ),
                "note": sum(1 for f in self.findings if f.disposition == NOTE),
            },
            "evidence_complete": self.evidence_complete,
            "stale": self.stale,
            "principal": self.principal,
            "subject_ref": self.subject_ref,
            "policy": dict(self.policy),
            "worker": dict(self.worker),
            "authorization": dict(self.authorization),
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
            "event_id": self.event_id,
            "work_event_ref": self.work_event_ref,
            "evidence_ref": self.evidence_ref,
            "created_at": self.created_at,
            "non_collapses": [
                "REVIEW != APPROVAL",
                "APPROVAL != MERGE",
                "GREEN != MERGE AUTHORIZATION",
                "SHADOW != ACTIVATED",
            ],
        }

    def to_markdown(self) -> str:
        """The final report, rendered for the canonical conversational surface."""
        lines = [
            f"### Chief PR review — {self.binding.repository}#{self.binding.pr_number}",
            "",
            f"- **Status:** {self.status}",
            f"- **Head:** `{self.binding.head_sha}`",
            f"- **Base:** `{self.binding.base_sha}`",
            f"- **Evidence complete:** {str(self.evidence_complete).lower()}",
            f"- **Stale:** {str(self.stale).lower()}",
            f"- **Job:** `{self.job_id}`",
            f"- **Evidence:** `{self.evidence_ref or 'none recorded'}`",
            f"- **Rollout stage:** {self.policy.get('stage')}",
            "",
            "A GREEN review is evidence-backed and eligible for a separately "
            "authorized next step. It is not merge authorization.",
            "",
            "#### Findings",
        ]
        if not self.findings:
            lines.append("- none")
        for finding in self.findings:
            location = ""
            if finding.path:
                location = f" — `{finding.path}`" + (
                    f":{finding.line}" if finding.line else ""
                )
            lines.append(
                f"- **[{finding.severity.upper()}] {finding.title}**{location} "
                f"({finding.disposition}) — {finding.detail}"
            )
        return "\n".join(lines)


# -- review engine -----------------------------------------------------------


def _diff_findings(
    snapshot: PullRequestSnapshot,
    *,
    path_policy: Callable[[Sequence[str]], tuple[bool, str]] | None,
) -> list[Finding]:
    findings: list[Finding] = []

    if not snapshot.files_observed:
        findings.append(
            Finding(
                code="DIFF_UNOBSERVED",
                severity="medium",
                title="Changed files could not be read",
                detail=(
                    "GitHub did not return the changed-file list, so no diff-level "
                    "finding can be asserted. Missing evidence is not a clean diff."
                ),
                disposition=HUMAN_DECISION,
            )
        )
        return findings

    paths = [f.path for f in snapshot.changed_files]
    if path_policy is None:
        findings.append(
            Finding(
                code="PATH_POLICY_UNOBSERVED",
                severity="medium",
                title="No repository path policy was supplied",
                detail=(
                    "The canonical mutation-boundary policy was not injected, so "
                    "path admissibility was not judged. This is recorded rather "
                    "than assumed admissible."
                ),
                disposition=HUMAN_DECISION,
                evidence={"changed_paths": paths},
            )
        )
    else:
        allowed, reason = path_policy(paths)
        if not allowed:
            findings.append(
                Finding(
                    code="PATH_OUTSIDE_POLICY",
                    severity="high",
                    title="Changed path is outside the repository policy",
                    detail=reason,
                    disposition=BLOCK,
                    evidence={"changed_paths": paths, "policy_reason": reason},
                )
            )

    for changed in snapshot.changed_files:
        for line, text in added_lines(changed.patch):
            if any(pattern.search(text) for pattern in SECRET_SHAPES):
                findings.append(
                    Finding(
                        code="CREDENTIAL_SHAPED_ADDITION",
                        severity="high",
                        title="Added line matches a credential shape",
                        detail=(
                            "The added line matches a known credential pattern. "
                            "This is a review heuristic pointing at a real diff "
                            "line; a human adjudicates whether it is a fixture."
                        ),
                        disposition=BLOCK,
                        path=changed.path,
                        line=line,
                        evidence={"path": changed.path, "line": line},
                    )
                )
    return findings


def _check_findings(
    snapshot: PullRequestSnapshot, *, required_checks: Sequence[str]
) -> list[Finding]:
    findings: list[Finding] = []
    if not snapshot.checks_observed:
        findings.append(
            Finding(
                code="CHECKS_UNOBSERVED",
                severity="medium",
                title="Check runs could not be read",
                detail=(
                    "GitHub did not return check runs for the head commit. An "
                    "unread check set is not a passing one."
                ),
                disposition=HUMAN_DECISION,
            )
        )
        return findings

    observed_names = {check.name for check in snapshot.checks}
    for name in required_checks:
        if name not in observed_names:
            findings.append(
                Finding(
                    code="REQUIRED_CHECK_MISSING",
                    severity="high",
                    title=f"Required check '{name}' did not run on this head",
                    detail=(
                        "A required check has no run on the reviewed head. The "
                        "gate cannot be satisfied by absence."
                    ),
                    disposition=BLOCK,
                    evidence={"required_check": name, "observed": sorted(observed_names)},
                )
            )

    for check in snapshot.checks:
        conclusion = (check.conclusion or "").lower()
        if conclusion in FAILING_CONCLUSIONS:
            findings.append(
                Finding(
                    code="CHECK_FAILED",
                    severity="high",
                    title=f"Check '{check.name}' concluded {conclusion}",
                    detail=(
                        f"The check run on head {check.head_sha or snapshot.head_sha} "
                        f"reported '{conclusion}'."
                    ),
                    disposition=BLOCK,
                    evidence={
                        "check": check.name,
                        "conclusion": check.conclusion,
                        "details_url": check.details_url,
                        "head_sha": check.head_sha,
                    },
                )
            )
        elif check.status != "completed":
            findings.append(
                Finding(
                    code="CHECK_PENDING",
                    severity="low",
                    title=f"Check '{check.name}' has not completed",
                    detail=f"The check run is '{check.status}'; a pending check is not a pass.",
                    disposition=HUMAN_DECISION,
                    evidence={"check": check.name, "status": check.status},
                )
            )
    return findings


def review_pull_request(
    request: PrReviewRequest,
    *,
    reader: GitHubReader,
    policy: ReviewPolicy,
    worker: GitHubAppWorker | None = None,
    path_policy: Callable[[Sequence[str]], tuple[bool, str]] | None = None,
) -> PrReviewResult:
    """Execute a shadow review of the exact requested head.

    Fails closed at every step: a missing worker binding, an unreadable
    repository, or a moved head produce a refusal or a non-GREEN status — never
    a GREEN review built on absent evidence.
    """
    worker = worker or GitHubAppWorker.from_env()
    assert_action_permitted(READ, policy)
    assert_action_permitted(request.requested_action, policy)
    worker.verify_binding(request.repository, request.installation_id)

    if policy.repositories and request.repository not in policy.repositories:
        raise BoundaryViolation(
            f"repository '{request.repository}' is outside the active review policy"
        )

    binding = request.binding()
    job_id = request.job_id or f"PRR-{uuid.uuid4().hex[:12]}"
    authorization = {
        "decision": "READ_ONLY_SHADOW",
        "stage": policy.stage,
        "requires_human_grant_for": [
            action
            for action in (PUBLISH_COMMENT, REQUEST_CHANGES, APPROVE)
            if not stage_reaches(policy.stage, ACTION_GATES[action].minimum_stage)
            or not bool(getattr(policy, ACTION_GATES[action].requires_policy_flag or "", False))
        ],
    }

    try:
        snapshot = reader.read_pull_request(request.repository, request.pr_number)
    except RateLimited:
        # A provider rate limit is not a review outcome; the caller retries under
        # its bounded policy and the refusal stays visible.
        raise
    except GitHubUnavailable as exc:
        # An unreadable PR is not a review. Report it as such rather than
        # fabricating an empty snapshot.
        findings = (
            Finding(
                code="PR_UNREADABLE",
                severity="high",
                title="The pull request could not be read",
                detail=str(exc),
                disposition=HUMAN_DECISION,
                evidence={"reason": str(exc)},
            ),
        )
        return PrReviewResult(
            job_id=job_id,
            capability=CAPABILITY_ID,
            status=AMBER,
            binding=binding,
            findings=findings,
            evidence_complete=False,
            stale=False,
            principal=request.principal,
            subject_ref=request.subject_ref,
            policy=policy.to_dict(),
            worker=worker.status(),
            authorization=authorization,
            snapshot=None,
            event_id=request.event_id,
            work_event_ref=request.work_event_ref,
            evidence_ref=None,
            created_at=utc_now(),
        )

    findings: list[Finding] = []
    stale = snapshot.head_sha != request.head_sha
    if stale:
        findings.append(
            Finding(
                code="STALE_HEAD",
                severity="critical",
                title="The head moved after the request was made",
                detail=(
                    f"Requested head {request.head_sha}, live head {snapshot.head_sha}. "
                    "Findings for the previous head are invalidated; rerun against "
                    "the current head."
                ),
                disposition=BLOCK,
                evidence={"requested_head": request.head_sha, "live_head": snapshot.head_sha},
            )
        )
    if snapshot.base_sha and snapshot.base_sha != request.base_sha:
        findings.append(
            Finding(
                code="BASE_MOVED",
                severity="medium",
                title="The base branch head differs from the requested base",
                detail=(
                    f"Requested base {request.base_sha}, live base {snapshot.base_sha}."
                ),
                disposition=HUMAN_DECISION,
                evidence={"requested_base": request.base_sha, "live_base": snapshot.base_sha},
            )
        )
    if snapshot.state and snapshot.state != "open":
        findings.append(
            Finding(
                code="PR_NOT_OPEN",
                severity="medium",
                title=f"The pull request is '{snapshot.state}'",
                detail="A closed pull request is not reviewable for merge consideration.",
                disposition=HUMAN_DECISION,
                evidence={"state": snapshot.state},
            )
        )
    if snapshot.draft:
        findings.append(
            Finding(
                code="DRAFT_PR",
                severity="low",
                title="The pull request is a draft",
                detail="A draft is not ready for review; findings are advisory.",
                disposition=HUMAN_DECISION,
                evidence={"draft": True},
            )
        )
    if request.principal and snapshot.author and request.principal == snapshot.author:
        findings.append(
            Finding(
                code="SELF_REVIEW",
                severity="medium",
                title="The requesting principal is the pull request author",
                detail=(
                    "Independent review is required. This principal may read and "
                    "generate findings, but may never approve its own change."
                ),
                disposition=HUMAN_DECISION,
                evidence={"principal": request.principal, "author": snapshot.author},
            )
        )

    findings.extend(_check_findings(snapshot, required_checks=policy.required_checks))
    findings.extend(_diff_findings(snapshot, path_policy=path_policy))

    evidence_complete = bool(
        snapshot.files_observed
        and snapshot.checks_observed
        and path_policy is not None
        and not stale
    )
    ordered = tuple(sorted(findings, key=lambda f: f.sort_key()))
    status = _finding_status(ordered, evidence_complete=evidence_complete)

    return PrReviewResult(
        job_id=job_id,
        capability=CAPABILITY_ID,
        status=status,
        binding=binding,
        findings=ordered,
        evidence_complete=evidence_complete,
        stale=stale,
        principal=request.principal,
        subject_ref=request.subject_ref,
        policy=policy.to_dict(),
        worker=worker.status(),
        authorization=authorization,
        snapshot=snapshot,
        event_id=request.event_id,
        work_event_ref=request.work_event_ref,
        evidence_ref=None,
        created_at=utc_now(),
    )


# -- evidence ----------------------------------------------------------------


def build_evidence(
    result: PrReviewResult,
    *,
    workspace_ref: str,
    authorization_ref: str | None = None,
    actions: Iterable[str] = (READ, GENERATE_FINDINGS),
) -> EvidenceRecord:
    """Reduce a result to the canonical Lab evidence record.

    ``state`` is a RESULT_STATES value and is never inflated: a GREEN review is
    ``VERIFIED`` only because the review itself completed and its evidence was
    observed. It is never ``COMPLETED`` (a human-accepted terminal).
    """
    actions_list = list(actions)
    detail = {
        "capability": result.capability,
        "owner_principal": OWNER_PRINCIPAL,
        "principal": result.principal,
        "binding": result.binding.to_dict(),
        "worker": result.worker,
        "policy": result.policy,
        "authorization": result.authorization,
        "authorization_ref": authorization_ref,
        "status": result.status,
        "stale": result.stale,
        "evidence_complete": result.evidence_complete,
        "event_id": result.event_id,
        "work_event_ref": result.work_event_ref,
        "actions": actions_list,
        "checks": (
            [c.to_dict() for c in result.snapshot.checks] if result.snapshot else []
        ),
        "findings": [f.to_dict() for f in result.findings],
        "counts": {
            "block": sum(1 for f in result.findings if f.disposition == BLOCK),
            "human_decision": sum(
                1 for f in result.findings if f.disposition == HUMAN_DECISION
            ),
        },
    }
    if not result.evidence_complete or result.stale:
        state = "UNRESOLVED"
    elif result.status == GREEN:
        state = "VERIFIED"
    elif result.status == RED:
        state = "BLOCKED"
    else:
        state = "UNRESOLVED"
    return EvidenceRecord(
        evidence_id=f"EVD-{uuid.uuid4().hex[:12]}",
        subject_ref=result.subject_ref,
        workspace_ref=workspace_ref,
        run_ref=result.job_id,
        state=state,
        summary=(
            f"{result.capability} {result.status} for "
            f"{result.binding.repository}#{result.binding.pr_number}@"
            f"{result.binding.head_sha[:12]}"
        ),
        detail=detail,
        timestamp_utc=utc_now(),
        provenance={
            "capability_id": CAPABILITY_ID,
            "schema": SCHEMA,
            "policy_fingerprint": result.policy.get("policy_fingerprint"),
            "worker_credential_source": result.worker.get("credential_source"),
            "recorded_by": "engineering_lab",
        },
    )


def attach_evidence(result: PrReviewResult, evidence_ref: str) -> PrReviewResult:
    """Return the result carrying its durable evidence reference."""
    return replace(result, evidence_ref=evidence_ref)


# -- approval binding --------------------------------------------------------


def approval_scope(binding: HeadBinding, action: str) -> str:
    return binding.scope_ref(action)


def assert_independent(principal: str, author: str) -> None:
    """Refuse self-approval. Reading your own change is fine; approving is not."""
    if principal and author and principal == author:
        raise BoundaryViolation(
            "a principal may not approve or request changes on a pull request it "
            "authored; independent review is required"
        )


def assert_grant_matches(
    authorization: dict[str, Any] | None,
    binding: HeadBinding,
    action: str,
) -> None:
    """Fail closed unless a usable grant names this exact tuple and action."""
    if not authorization:
        raise BoundaryViolation(
            f"'{action}' requires a human-originated grant for "
            f"{binding.repository}#{binding.pr_number}@{binding.head_sha}"
        )
    if authorization.get("revoked_at"):
        raise BoundaryViolation("the grant for this action has been revoked")
    if authorization.get("consumed_at"):
        raise BoundaryViolation("the grant for this action has already been consumed")
    if not authorization_is_usable(authorization):
        raise BoundaryViolation(
            "the grant for this action has expired; record a fresh grant"
        )
    expected = binding.scope_ref(action)
    if authorization.get("scope_ref") != expected:
        raise BoundaryViolation(
            f"the grant is scoped to '{authorization.get('scope_ref')}', not "
            f"'{expected}'; a changed head or action requires a fresh grant"
        )
    if action not in set(authorization.get("operations_allowed") or ()):
        raise BoundaryViolation(
            f"the grant does not permit '{action}'; record a grant that names it"
        )


# -- retries -----------------------------------------------------------------


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded retries with a declared backoff. Dead letters are visible."""

    max_attempts: int = 3
    base_backoff_seconds: int = 15
    max_backoff_seconds: int = 300

    def backoff(self, attempt: int) -> int:
        attempt = max(1, int(attempt))
        return min(self.max_backoff_seconds, self.base_backoff_seconds * (2 ** (attempt - 1)))

    def should_retry(self, attempt: int) -> bool:
        return int(attempt) < self.max_attempts

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "base_backoff_seconds": self.base_backoff_seconds,
            "max_backoff_seconds": self.max_backoff_seconds,
        }


__all__ = [
    "ACTION_GATES",
    "AMBER",
    "APPROVE",
    "ActionGate",
    "BLOCK",
    "CAPABILITY_ID",
    "FAILING_CONCLUSIONS",
    "Finding",
    "GENERATE_FINDINGS",
    "GREEN",
    "HeadBinding",
    "HUMAN_DECISION",
    "MERGE",
    "NOTE",
    "OWNER_PRINCIPAL",
    "PUBLISH_COMMENT",
    "PrReviewRequest",
    "PrReviewResult",
    "READ",
    "RED",
    "REQUEST_CHANGES",
    "REVIEW_ACTIONS",
    "REVIEW_STATUSES",
    "ROLLOUT_STATES",
    "RetryPolicy",
    "ReviewPolicy",
    "SCHEMA",
    "SECRET_SHAPES",
    "SEVERITIES",
    "STRUCTURALLY_REFUSED",
    "StaleHead",
    "added_lines",
    "approval_scope",
    "assert_action_permitted",
    "assert_grant_matches",
    "assert_head_current",
    "assert_independent",
    "attach_evidence",
    "build_evidence",
    "capability_manifest",
    "capability_registry",
    "review_pull_request",
    "rollout_state",
    "stage_reaches",
]
