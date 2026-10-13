"""Read-only GitHub evidence collection for Engineering Acceptance Authority.

This adapter only issues GitHub REST GET requests. It does not merge, write
repository contents, trigger workflows, deploy, or treat an approval as
authorized unless the reviewer numeric ID is explicitly allow-listed.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .engineering_acceptance import (
    CheckState,
    GateEvidence,
    HumanApprovalEvidence,
    MergePolicy,
    PullRequestEvidence,
    ReviewEvidence,
    RiskClass,
    evaluate_merge_readiness,
)

_API_ROOT = "https://api.github.com"
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-f]{40}$")


class EvidenceCollectionError(RuntimeError):
    """Raised when authoritative evidence cannot safely be collected."""


@dataclass(frozen=True)
class AdapterEvaluation:
    evidence: PullRequestEvidence
    decision: Any
    warnings: tuple[str, ...]


class GitHubReadOnlyEvidenceAdapter:
    """Collect a SHA-bound EAA evidence snapshot from GitHub's read APIs."""

    def __init__(
        self,
        repository: str,
        token: str | None = None,
        authorized_reviewer_ids: frozenset[str] | None = None,
        timeout_seconds: float = 15.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        if not _REPO.fullmatch(repository):
            raise ValueError("repository must be in owner/repo form")
        self.repository = repository
        self._token = token if token is not None else os.getenv("GITHUB_TOKEN", "")
        self._authorized_ids = authorized_reviewer_ids
        if self._authorized_ids is None:
            raw = os.getenv("ARKADIA_EAA_AUTHORIZED_REVIEWER_IDS", "")
            self._authorized_ids = frozenset(
                item.strip() for item in raw.split(",") if item.strip()
            )
        if not self._token:
            raise ValueError("GITHUB_TOKEN is required for evidence collection")
        if any(not item.isdigit() for item in self._authorized_ids):
            raise ValueError("authorized reviewer IDs must be numeric GitHub user IDs")
        self._timeout = timeout_seconds
        self._opener = opener or urlopen

    def _get(self, url_or_path: str) -> tuple[Any, str | None]:
        """Issue one GET; reject any URL outside GitHub's API origin."""
        url = urljoin(_API_ROOT + "/", url_or_path.lstrip("/"))
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "api.github.com":
            raise EvidenceCollectionError("refusing a non-GitHub API URL")
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "Arkadia-EAA-ReadOnly-Evidence-Adapter",
            },
            method="GET",
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload, response.headers.get("Link")
        except HTTPError as exc:
            # Never include request headers or token in error messages.
            raise EvidenceCollectionError(
                f"GitHub GET returned HTTP {exc.code} for {parsed.path}"
            ) from None
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise EvidenceCollectionError(
                f"GitHub GET failed for {parsed.path}: {type(exc).__name__}"
            ) from None

    def _pages(self, path: str) -> list[dict[str, Any]]:
        """Read all pages when GitHub supplies a rel=next link."""
        url = path
        results: list[dict[str, Any]] = []
        while url:
            payload, link_header = self._get(url)
            if not isinstance(payload, list):
                raise EvidenceCollectionError(f"expected a list from {url}")
            results.extend(item for item in payload if isinstance(item, dict))
            next_url = None
            if link_header:
                for part in link_header.split(","):
                    if 'rel="next"' in part:
                        candidate = part.split(";", 1)[0].strip().strip("<>")
                        next_url = candidate
                        break
            url = next_url or ""
        return results

    @staticmethod
    def _check_state(run: dict[str, Any]) -> CheckState:
        status = str(run.get("status", "")).lower()
        conclusion = str(run.get("conclusion") or "").lower()
        if status != "completed":
            return CheckState.NOT_TESTED
        if conclusion == "success":
            return CheckState.PASS
        if conclusion in {"failure", "timed_out", "action_required", "startup_failure"}:
            return CheckState.FAIL
        return CheckState.NOT_TESTED

    @staticmethod
    def _latest_by(items: list[dict[str, Any]], key: Callable[[dict[str, Any]], str]) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for item in items:
            value = key(item)
            if not value:
                continue
            old = latest.get(value)
            order = (str(item.get("submitted_at") or item.get("created_at") or ""), int(item.get("id") or 0))
            old_order = (
                str((old or {}).get("submitted_at") or (old or {}).get("created_at") or ""),
                int((old or {}).get("id") or 0),
            )
            if old is None or order >= old_order:
                latest[value] = item
        return list(latest.values())

    def collect(self, pr_number: int, policy: MergePolicy) -> AdapterEvaluation:
        if not isinstance(pr_number, int) or pr_number < 1:
            raise ValueError("pr_number must be a positive integer")
        prefix = f"/repos/{self.repository}"
        start, _ = self._get(f"{prefix}/pulls/{pr_number}")
        if not isinstance(start, dict) or not isinstance(start.get("head"), dict) or not isinstance(start.get("base"), dict):
            raise EvidenceCollectionError("GitHub returned an incomplete pull request record")
        head = start["head"]
        base = start["base"]
        head_sha = str(head.get("sha") or "")
        base_sha = str(base.get("sha") or "")
        base_ref = str(base.get("ref") or "")
        if not _SHA.fullmatch(head_sha) or not _SHA.fullmatch(base_sha) or not base_ref:
            raise EvidenceCollectionError("PR head/base SHA or base branch is invalid")

        runs = self._pages(f"{prefix}/commits/{head_sha}/check-runs?per_page=100")
        by_name = self._latest_by(runs, lambda run: str(run.get("name") or ""))
        checks: dict[str, GateEvidence] = {}
        for run in by_name:
            name = str(run.get("name") or "")
            tested_sha = str(run.get("head_sha") or "")
            checks[name] = GateEvidence(
                name=name,
                state=self._check_state(run),
                tested_sha=tested_sha,
                artifact_url=str(run.get("html_url") or "") or None,
                detail=f"GitHub check conclusion: {run.get('conclusion') or run.get('status') or 'unknown'}",
            )

        reviews_raw = self._pages(f"{prefix}/pulls/{pr_number}/reviews?per_page=100")
        latest_reviews = self._latest_by(
            reviews_raw, lambda review: str((review.get("user") or {}).get("id") or "")
        )
        author_id = str((start.get("user") or {}).get("id") or "")
        reviews: list[ReviewEvidence] = []
        approvals: list[HumanApprovalEvidence] = []
        warnings: list[str] = []
        for review in latest_reviews:
            user = review.get("user") or {}
            reviewer_id = str(user.get("id") or "")
            reviewer = str(user.get("login") or "")
            state = str(review.get("state") or "").upper()
            reviewed_sha = str(review.get("commit_id") or "")
            if state == "APPROVED" and reviewer and reviewed_sha == head_sha:
                reviews.append(ReviewEvidence(
                    approved=True,
                    reviewer=reviewer,
                    reviewed_sha=reviewed_sha,
                    independent=bool(reviewer_id and reviewer_id != author_id),
                ))
                if reviewer_id in self._authorized_ids:
                    approvals.append(HumanApprovalEvidence(
                        approved=True,
                        reviewer=reviewer,
                        reviewer_id=reviewer_id,
                        reviewed_sha=reviewed_sha,
                        record_id=str(review.get("id") or ""),
                        source="github-pull-request-review",
                        authorized=True,
                    ))

        protection_ok = False
        complete = True
        try:
            protection, _ = self._get(f"{prefix}/branches/{base_ref}/protection")
            if not isinstance(protection, dict):
                raise EvidenceCollectionError("branch protection response is not an object")
            required_status = protection.get("required_status_checks") or {}
            required_contexts = set(required_status.get("contexts") or [])
            required_contexts.update(
                str(item.get("context") or "")
                for item in (required_status.get("checks") or [])
                if isinstance(item, dict) and item.get("context")
            )
            check_map = {str(run.get("name") or ""): run for run in runs}
            missing_or_failed = []
            for context in required_contexts:
                run = check_map.get(context)
                if not run or str(run.get("head_sha") or "") != head_sha or self._check_state(run) is not CheckState.PASS:
                    missing_or_failed.append(context)
            required_reviews = protection.get("required_pull_request_reviews") or {}
            required_count = int(required_reviews.get("required_approving_review_count") or 0)
            exact_approvals = {
                str((r.get("user") or {}).get("id") or "")
                for r in latest_reviews
                if str(r.get("state") or "").upper() == "APPROVED"
                and str(r.get("commit_id") or "") == head_sha
                and str((r.get("user") or {}).get("id") or "") != author_id
            }
            protection_ok = not missing_or_failed and len(exact_approvals) >= required_count
            if missing_or_failed:
                warnings.append("branch-protection required checks missing, stale, or non-passing: " + ", ".join(sorted(missing_or_failed)))
            if len(exact_approvals) < required_count:
                warnings.append("branch-protection approving-review count is not satisfied")
        except EvidenceCollectionError as exc:
            complete = False
            warnings.append(f"branch protection evidence unavailable; fail-closed: {exc}")

        # Re-read the PR after evidence collection to detect movement during the
        # snapshot. The evaluator compares observed SHA values with the initial SHA.
        end, _ = self._get(f"{prefix}/pulls/{pr_number}")
        end_head = str(((end.get("head") or {}).get("sha")) or "")
        end_base = str(((end.get("base") or {}).get("sha")) or "")
        if end_head != head_sha or end_base != base_sha:
            complete = False
            warnings.append("PR head or base moved while evidence was being collected")

        risk = RiskClass.UNKNOWN
        evidence = PullRequestEvidence(
            pr_number=pr_number,
            head_sha=head_sha,
            base_sha=base_sha,
            observed_head_sha=end_head,
            observed_base_sha=end_base,
            checks=checks,
            reviews=tuple(reviews),
            draft=bool(start.get("draft", True)),
            mergeable=start.get("mergeable") is True,
            branch_protection_satisfied=protection_ok,
            risk_class=risk,
            human_approvals=tuple(approvals),
            policy_authorizes_auto_merge=False,
            evidence_complete=complete,
            policy_version=policy.version,
        )
        decision = evaluate_merge_readiness(evidence, policy)
        return AdapterEvaluation(evidence=evidence, decision=decision, warnings=tuple(warnings))
