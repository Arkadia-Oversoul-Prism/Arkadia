"""ARKADIA-CHIEF-PR-REVIEW-001 — GitHub App worker identity and ingress.

This module is the *identity and ingress* half of the governed PR-review
capability. It owns exactly two things:

  * the **GitHub App worker** — an installation-scoped execution identity with a
    least-privilege permission matrix and a repository allowlist. A user PAT, an
    ambient connector credential, or a prompt claim is never accepted as the
    worker: ``credential()`` returns ``None`` rather than borrowing one.
  * **webhook verification** — HMAC-SHA256 over the raw body with constant-time
    comparison, plus installation identity, repository allowlist, event class
    and payload validation. A delivery that fails any check is refused.

Boundary rules (all normative):

  UNVERIFIED_DELIVERY   != DELIVERY
  INSTALLATION_TOKEN    != USER_PAT
  WEBHOOK_SIGNATURE     != REPOSITORY_AUTHORIZATION   (it proves the sender,
                                                       not the target)
  READ_PERMISSION       != WRITE_PERMISSION

Nothing here executes a review, writes a comment, approves, or merges. The
review engine (``pr_review``) consumes a verified delivery; the API layer
composes the two. GitHub remains the repository authority.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .contracts import utc_now

SCHEMA = "arkadia.lab.github_app/1"

#: Where a pre-minted GitHub App installation token is read from.
INSTALLATION_TOKEN_ENV = "ARKADIA_PR_REVIEW_INSTALLATION_TOKEN"
APP_ID_ENV = "ARKADIA_PR_REVIEW_APP_ID"
APP_SLUG_ENV = "ARKADIA_PR_REVIEW_APP_SLUG"
INSTALLATION_ID_ENV = "ARKADIA_PR_REVIEW_INSTALLATION_ID"
REPOSITORIES_ENV = "ARKADIA_PR_REVIEW_REPOSITORIES"
WEBHOOK_SECRET_ENV = "ARKADIA_PR_REVIEW_WEBHOOK_SECRET"

#: Credentials this worker will never use. Named so a refusal can state what it
#: declined to borrow instead of failing vaguely.
REFUSED_CREDENTIAL_SOURCES: tuple[str, ...] = (
    "GITHUB_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "GH_TOKEN",
    "ambient_connector",
)

#: Least-privilege permission matrix, declared per capability. Read review needs
#: only read scopes; publishing needs pull-request write. ``checks:write`` and
#: ``statuses:write`` are deliberately absent — a review never manufactures a
#: check result.
PERMISSION_MATRIX: dict[str, dict[str, str]] = {
    "read_repository": {"contents": "read", "metadata": "read"},
    "read_pull_request": {"pull_requests": "read", "contents": "read", "metadata": "read"},
    "read_checks": {"checks": "read", "metadata": "read"},
    "publish_review": {"pull_requests": "write", "contents": "read", "metadata": "read"},
}

#: The union the App is asked to grant. Anything outside it is not requested.
GRANTED_PERMISSIONS: dict[str, str] = {
    "metadata": "read",
    "contents": "read",
    "pull_requests": "write",
    "checks": "read",
}

#: Webhook events this capability accepts. Everything else is ignored, not
#: treated as a review trigger.
ALLOWED_EVENTS: frozenset[str] = frozenset({"pull_request"})
ALLOWED_ACTIONS: frozenset[str] = frozenset(
    {"opened", "reopened", "synchronize", "ready_for_review", "edited"}
)

#: Installation target type GitHub sends for App (not OAuth) deliveries.
EXPECTED_TARGET_TYPE = "integration"


class GitHubAppError(RuntimeError):
    """Base class for worker/ingress failures. Callers fail closed."""


class WorkerUnavailable(GitHubAppError):
    """The worker is not configured or cannot mint a credential."""


class WebhookRejected(GitHubAppError):
    """A delivery failed verification. ``status_code`` is the HTTP refusal."""

    def __init__(self, reason: str, *, status_code: int = 401) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


# -- worker identity ---------------------------------------------------------


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _allowlist() -> tuple[str, ...]:
    raw = _env(REPOSITORIES_ENV)
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class GitHubAppWorker:
    """The installation-scoped execution identity for this capability.

    ``installation_id`` and ``repositories`` are the *server-side* binding. A
    request naming a different installation, or a repository outside the
    allowlist, is refused even when it carries a valid signature.
    """

    app_id: str | None = None
    app_slug: str | None = None
    installation_id: int | None = None
    repositories: tuple[str, ...] = ()
    has_credential: bool = False
    schema: str = SCHEMA

    @classmethod
    def from_env(cls) -> "GitHubAppWorker":
        raw_installation = _env(INSTALLATION_ID_ENV)
        installation_id: int | None = None
        if raw_installation:
            try:
                installation_id = int(raw_installation)
            except ValueError:
                # A malformed binding is an unconfigured worker, never a guess.
                installation_id = None
        return cls(
            app_id=_env(APP_ID_ENV) or None,
            app_slug=_env(APP_SLUG_ENV) or None,
            installation_id=installation_id,
            repositories=_allowlist(),
            has_credential=bool(_env(INSTALLATION_TOKEN_ENV)),
        )

    # -- truthful status ----------------------------------------------------

    def status(self) -> dict[str, Any]:
        """Report the worker's configuration honestly.

        ``AVAILABLE`` requires every binding component. A partially configured
        worker is ``UNCONFIGURED`` with the missing parts named — never assumed
        usable because *some* variable was set.
        """
        missing: list[str] = []
        if not self.app_id:
            missing.append(APP_ID_ENV)
        if self.installation_id is None:
            missing.append(INSTALLATION_ID_ENV)
        if not self.repositories:
            missing.append(REPOSITORIES_ENV)
        if not self.has_credential:
            missing.append(INSTALLATION_TOKEN_ENV)
        if missing:
            return {
                "state": "UNCONFIGURED",
                "missing": missing,
                "credential_source": "github_app_installation_token",
                "refused_credential_sources": list(REFUSED_CREDENTIAL_SOURCES),
                "detail": (
                    "the GitHub App worker binding is incomplete; no review may be "
                    "attributed to an unverified worker"
                ),
            }
        return {
            "state": "AVAILABLE",
            "app_id": self.app_id,
            "app_slug": self.app_slug,
            "installation_id": self.installation_id,
            "repositories": list(self.repositories),
            "credential_source": "github_app_installation_token",
            "refused_credential_sources": list(REFUSED_CREDENTIAL_SOURCES),
        }

    # -- binding verification ----------------------------------------------

    def verify_binding(self, repository: str, installation_id: int | None) -> None:
        """Fail closed unless this worker is bound to *repository* and install.

        Checked in order so a refusal names the most specific failure.
        """
        state = self.status()
        if state["state"] != "AVAILABLE":
            raise WorkerUnavailable(
                "GitHub App worker is not configured: missing "
                + ", ".join(state["missing"])
            )
        if repository not in self.repositories:
            raise WorkerUnavailable(
                f"repository '{repository}' is not in the worker installation "
                "allowlist; the delivery is refused rather than trusted"
            )
        if installation_id is None:
            raise WorkerUnavailable(
                "the request names no installation; installation identity is "
                "required and is never inferred"
            )
        if int(installation_id) != int(self.installation_id or -1):
            raise WorkerUnavailable(
                f"installation {installation_id} does not match the configured "
                f"installation {self.installation_id}"
            )

    # -- credential ---------------------------------------------------------

    def credential(self) -> str:
        """Return the installation token, or refuse.

        A missing installation token is a refusal. The worker does not fall back
        to ``GITHUB_TOKEN`` or any ambient connector credential: doing so would
        attribute an installation-scoped action to a human principal.
        """
        token = _env(INSTALLATION_TOKEN_ENV)
        if not token:
            raise WorkerUnavailable(
                f"{INSTALLATION_TOKEN_ENV} is not set; refusing to borrow "
                f"any of {', '.join(REFUSED_CREDENTIAL_SOURCES)}"
            )
        return token

    def permissions(self) -> dict[str, Any]:
        return {
            "granted": dict(GRANTED_PERMISSIONS),
            "by_capability": {k: dict(v) for k, v in PERMISSION_MATRIX.items()},
            "not_requested": ["checks:write", "statuses:write", "administration:write",
                              "secrets:read", "workflows:write", "deployments:write"],
        }


# -- webhook verification ----------------------------------------------------


@dataclass(frozen=True)
class WebhookDelivery:
    """A *verified* GitHub App delivery. Not authorization, only identity."""

    delivery_id: str
    event: str
    action: str
    repository: str
    installation_id: int | None
    pr_number: int | None
    base_sha: str | None
    head_sha: str | None
    sender: str | None
    accepted: bool
    reason: str
    payload_digest: str
    received_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "event": self.event,
            "action": self.action,
            "repository": self.repository,
            "installation_id": self.installation_id,
            "pr_number": self.pr_number,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "sender": self.sender,
            "accepted": self.accepted,
            "reason": self.reason,
            "payload_digest": self.payload_digest,
            "received_at": self.received_at,
        }


def _header(headers: Mapping[str, str], name: str) -> str:
    target = name.lower()
    for key, value in headers.items():
        if str(key).lower() == target:
            return str(value)
    return ""


def signature_matches(secret: str, body: bytes, signature_header: str) -> bool:
    """Constant-time check of ``X-Hub-Signature-256``.

    A missing or malformed header is a mismatch, never a pass. The comparison
    is ``hmac.compare_digest`` so a partial match cannot be timed out of the
    secret.
    """
    if not secret or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header, expected)


def verify_webhook_delivery(
    *,
    headers: Mapping[str, str],
    body: bytes,
    worker: GitHubAppWorker,
    secret: str | None = None,
) -> WebhookDelivery:
    """Verify a delivery and return it, or raise :class:`WebhookRejected`.

    Order matters: signature first (cheapest rejection of a forged sender), then
    event class, then payload, then the server-side installation and repository
    binding. Signature verification proves *who sent it*; it never proves the
    repository is one this worker may act on, so both are checked.
    """
    resolved_secret = secret if secret is not None else _env(WEBHOOK_SECRET_ENV)
    if not resolved_secret:
        raise WebhookRejected(
            f"{WEBHOOK_SECRET_ENV} is not configured; an unsigned delivery is "
            "never accepted",
            status_code=503,
        )

    signature = _header(headers, "X-Hub-Signature-256")
    if not signature_matches(resolved_secret, body, signature):
        raise WebhookRejected("webhook signature verification failed", status_code=401)

    delivery_id = _header(headers, "X-GitHub-Delivery")
    if not delivery_id:
        raise WebhookRejected(
            "missing X-GitHub-Delivery; a delivery with no identity cannot be "
            "deduplicated or replayed safely",
            status_code=400,
        )

    target_type = _header(headers, "X-GitHub-Hook-Installation-Target-Type")
    if target_type and target_type != EXPECTED_TARGET_TYPE:
        raise WebhookRejected(
            f"installation target type '{target_type}' is not '{EXPECTED_TARGET_TYPE}'; "
            "a non-App delivery is not accepted",
            status_code=403,
        )

    event = _header(headers, "X-GitHub-Event")
    if event not in ALLOWED_EVENTS:
        return WebhookDelivery(
            delivery_id=delivery_id,
            event=event,
            action="",
            repository="",
            installation_id=None,
            pr_number=None,
            base_sha=None,
            head_sha=None,
            sender=None,
            accepted=False,
            reason=f"event '{event}' is not a review trigger",
            payload_digest=hashlib.sha256(body).hexdigest(),
        )

    try:
        payload = json.loads(body or b"{}")
    except json.JSONDecodeError as exc:
        raise WebhookRejected(f"payload is not JSON: {exc}", status_code=400) from exc
    if not isinstance(payload, dict):
        raise WebhookRejected("payload is not a JSON object", status_code=400)

    action = str(payload.get("action") or "")
    if action not in ALLOWED_ACTIONS:
        return WebhookDelivery(
            delivery_id=delivery_id,
            event=event,
            action=action,
            repository="",
            installation_id=None,
            pr_number=None,
            base_sha=None,
            head_sha=None,
            sender=None,
            accepted=False,
            reason=f"action '{action}' is not a review trigger",
            payload_digest=hashlib.sha256(body).hexdigest(),
        )

    repository = str(((payload.get("repository") or {}).get("full_name")) or "")
    if not repository:
        raise WebhookRejected("payload names no repository", status_code=400)

    installation = payload.get("installation") or {}
    raw_installation_id = installation.get("id")
    installation_id: int | None = None
    if raw_installation_id is not None:
        try:
            installation_id = int(raw_installation_id)
        except (TypeError, ValueError):
            raise WebhookRejected(
                "payload installation id is not an integer", status_code=400
            ) from None

    # The server-side binding is authoritative. A correctly signed delivery for
    # a repository this worker is not installed on is refused.
    try:
        worker.verify_binding(repository, installation_id)
    except WorkerUnavailable as exc:
        raise WebhookRejected(str(exc), status_code=403) from exc

    pull_request = payload.get("pull_request") or {}
    number = pull_request.get("number")
    try:
        pr_number = int(number) if number is not None else None
    except (TypeError, ValueError):
        pr_number = None
    if pr_number is None:
        raise WebhookRejected("payload names no pull request number", status_code=400)

    head = (pull_request.get("head") or {}).get("sha")
    base = (pull_request.get("base") or {}).get("sha")

    return WebhookDelivery(
        delivery_id=delivery_id,
        event=event,
        action=action,
        repository=repository,
        installation_id=installation_id,
        pr_number=pr_number,
        base_sha=str(base) if base else None,
        head_sha=str(head) if head else None,
        sender=str(((payload.get("sender") or {}).get("login")) or "") or None,
        accepted=True,
        reason="verified",
        payload_digest=hashlib.sha256(body).hexdigest(),
    )


# -- read-only GitHub reader -------------------------------------------------


class GitHubUnavailable(GitHubAppError):
    """A required GitHub read could not be performed. Never a silent empty."""


class RateLimited(GitHubAppError):
    """GitHub asked us to slow down. Carries the provider's retry hint."""

    def __init__(self, message: str, *, retry_after_seconds: int = 60) -> None:
        super().__init__(message)
        self.retry_after_seconds = int(retry_after_seconds)


@dataclass(frozen=True)
class ChangedFile:
    path: str
    status: str
    additions: int
    deletions: int
    patch: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "additions": self.additions,
            "deletions": self.deletions,
            "patch": self.patch,
        }


@dataclass(frozen=True)
class CheckRun:
    name: str
    status: str
    conclusion: str | None
    details_url: str | None
    head_sha: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "conclusion": self.conclusion,
            "details_url": self.details_url,
            "head_sha": self.head_sha,
        }


@dataclass(frozen=True)
class PullRequestSnapshot:
    """What GitHub actually returned. ``*_observed`` is not decoration.

    A field that could not be read is ``None``/empty **with** its observation
    flag ``False``, so a caller cannot mistake an unread value for a clean one.
    """

    repository: str
    number: int
    state: str
    draft: bool
    author: str
    base_sha: str
    head_sha: str
    mergeable_state: str | None
    changed_files: tuple[ChangedFile, ...]
    checks: tuple[CheckRun, ...]
    files_observed: bool
    checks_observed: bool
    observed_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "number": self.number,
            "state": self.state,
            "draft": self.draft,
            "author": self.author,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "mergeable_state": self.mergeable_state,
            "changed_files": [f.to_dict() for f in self.changed_files],
            "checks": [c.to_dict() for c in self.checks],
            "files_observed": self.files_observed,
            "checks_observed": self.checks_observed,
            "observed_at": self.observed_at,
        }


class GitHubReader(Protocol):
    """The read boundary the review engine depends on.

    Injected rather than imported so a test exercises the real engine against a
    recorded snapshot, and so no second HTTP client is created.
    """

    def read_pull_request(self, repository: str, number: int) -> PullRequestSnapshot: ...

    def read_head_sha(self, repository: str, number: int) -> str: ...


_API_ROOT = "https://api.github.com"


class HttpGitHubReader:
    """Read-only GitHub REST reader bound to the App worker's credential."""

    def __init__(self, worker: GitHubAppWorker, *, api_root: str = _API_ROOT,
                 timeout: float = 20.0) -> None:
        self._worker = worker
        self._api_root = api_root.rstrip("/")
        self._timeout = timeout

    def _get(self, path: str) -> Any:
        token = self._worker.credential()
        request = urllib.request.Request(
            f"{self._api_root}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if exc.code in (403, 429) and retry_after:
                raise RateLimited(
                    f"GitHub rate limit on {path}",
                    retry_after_seconds=int(retry_after) if retry_after.isdigit() else 60,
                ) from exc
            raise GitHubUnavailable(f"GitHub read {path} failed: http {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise GitHubUnavailable(f"GitHub read {path} failed: {exc.reason}") from exc

    def read_head_sha(self, repository: str, number: int) -> str:
        data = self._get(f"/repos/{repository}/pulls/{number}")
        sha = ((data or {}).get("head") or {}).get("sha")
        if not sha:
            raise GitHubUnavailable(
                f"GitHub returned no head sha for {repository}#{number}"
            )
        return str(sha)

    def read_pull_request(self, repository: str, number: int) -> PullRequestSnapshot:
        data = self._get(f"/repos/{repository}/pulls/{number}")

        files_observed = True
        changed: list[ChangedFile] = []
        try:
            files = self._get(f"/repos/{repository}/pulls/{number}/files?per_page=100")
        except GitHubUnavailable:
            files_observed = False
            files = []
        for item in files or []:
            changed.append(
                ChangedFile(
                    path=str(item.get("filename") or ""),
                    status=str(item.get("status") or ""),
                    additions=int(item.get("additions") or 0),
                    deletions=int(item.get("deletions") or 0),
                    patch=item.get("patch"),
                )
            )

        head_sha = str(((data or {}).get("head") or {}).get("sha") or "")
        checks_observed = True
        checks: list[CheckRun] = []
        try:
            runs = self._get(f"/repos/{repository}/commits/{head_sha}/check-runs?per_page=100")
        except GitHubUnavailable:
            checks_observed = False
            runs = {}
        for item in (runs or {}).get("check_runs", []) or []:
            checks.append(
                CheckRun(
                    name=str(item.get("name") or ""),
                    status=str(item.get("status") or ""),
                    conclusion=item.get("conclusion"),
                    details_url=item.get("details_url"),
                    head_sha=str(item.get("head_sha") or "") or None,
                )
            )

        return PullRequestSnapshot(
            repository=repository,
            number=int((data or {}).get("number") or number),
            state=str((data or {}).get("state") or ""),
            draft=bool((data or {}).get("draft")),
            author=str((((data or {}).get("user") or {}).get("login")) or ""),
            base_sha=str((((data or {}).get("base") or {}).get("sha")) or ""),
            head_sha=head_sha,
            mergeable_state=(data or {}).get("mergeable_state"),
            changed_files=tuple(changed),
            checks=tuple(checks),
            files_observed=files_observed,
            checks_observed=checks_observed,
        )


__all__ = [
    "ALLOWED_ACTIONS",
    "ALLOWED_EVENTS",
    "APP_ID_ENV",
    "APP_SLUG_ENV",
    "ChangedFile",
    "CheckRun",
    "GRANTED_PERMISSIONS",
    "GitHubAppError",
    "GitHubAppWorker",
    "GitHubReader",
    "GitHubUnavailable",
    "INSTALLATION_ID_ENV",
    "INSTALLATION_TOKEN_ENV",
    "HttpGitHubReader",
    "PERMISSION_MATRIX",
    "PullRequestSnapshot",
    "REFUSED_CREDENTIAL_SOURCES",
    "REPOSITORIES_ENV",
    "RateLimited",
    "SCHEMA",
    "WEBHOOK_SECRET_ENV",
    "WebhookDelivery",
    "WebhookRejected",
    "WorkerUnavailable",
    "signature_matches",
    "verify_webhook_delivery",
]
