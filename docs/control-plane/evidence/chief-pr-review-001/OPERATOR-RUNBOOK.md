# Chief PR Review — operator runbook

Capability: `chief.pr_review` (`ARKADIA-CHIEF-PR-REVIEW-001`).
Owner identity: `ARKADIA-CHIEF-001` (existing canonical Chief).
Execution boundary: Engineering Lab (`lab/engineering_lab`).

Nothing in this runbook authorizes a merge, a deployment, or a release. Merge
remains human-only and is structurally refused by the capability.

---

## 1. What this capability does

Given a repository, a pull request number, an exact base SHA and an exact head
SHA, it reads the PR, its changed files and the check runs on that head, and
produces:

* structured findings (severity, path, line, evidence, disposition),
* a review status — `GREEN`, `AMBER` or `RED`,
* a Lab evidence record and a review job record,
* a Markdown report for the conversational surface.

`GREEN` means "evidence-backed and eligible for a separately authorized next
step". It is never merge authorization.

---

## 2. Prerequisites (one-time, human)

1. Register a GitHub App. Name it distinctly (for example
   `arkadia-chief-review`) so it cannot be confused with a user credential.
2. Grant exactly these repository permissions:
   `metadata: read`, `contents: read`, `checks: read`, `pull_requests: write`.
   Do **not** grant `checks: write`, `statuses: write`, `administration: write`,
   `secrets: read`, `workflows: write`, `deployments: write`, or
   `contents: write`. See `PERMISSION-MATRIX.md`.
3. Install the App on the **single** repository the capability may review. Note
   the installation id.
4. Subscribe the App to **Pull request** events only.
5. Set the webhook URL to
   `https://<canonical-origin>/api/lab/engineering/pr-review/webhook` and set a
   webhook secret. ADR-016 makes `https://arkadia-qzu4.onrender.com` the sole
   canonical origin; do not point this at any other host.
6. Mint an installation token and place it in the deployment's secret manager.

## 3. Configuration

| Variable | Purpose | Default if unset |
|---|---|---|
| `ARKADIA_PR_REVIEW_APP_ID` | App identity | worker `UNCONFIGURED` |
| `ARKADIA_PR_REVIEW_APP_SLUG` | App slug (display) | omitted |
| `ARKADIA_PR_REVIEW_INSTALLATION_ID` | Installation binding | worker `UNCONFIGURED` |
| `ARKADIA_PR_REVIEW_REPOSITORIES` | Comma-separated allowlist | worker `UNCONFIGURED` |
| `ARKADIA_PR_REVIEW_INSTALLATION_TOKEN` | Installation token | worker `UNCONFIGURED` |
| `ARKADIA_PR_REVIEW_WEBHOOK_SECRET` | HMAC secret | webhook refuses (503) |
| `ARKADIA_PR_REVIEW_STAGE` | `IMPLEMENTED` / `SHADOW` / `ACTIVATED` | `SHADOW` |
| `ARKADIA_PR_REVIEW_ACTIVATION_REF` | Human activation record | not activated |
| `ARKADIA_PR_REVIEW_ALLOW_COMMENT` | `true` enables `PUBLISH_COMMENT` | disabled |
| `ARKADIA_PR_REVIEW_ALLOW_REQUEST_CHANGES` | `true` enables `REQUEST_CHANGES` | disabled |
| `ARKADIA_PR_REVIEW_ALLOW_APPROVE` | `true` enables `APPROVE` | disabled |
| `ARKADIA_PR_REVIEW_REQUIRED_CHECKS` | Comma-separated required check names | none enforced |
| `ARKADIA_PR_REVIEW_MAX_ATTEMPTS` | Retry bound | `3` |
| `ARKADIA_PR_REVIEW_BACKOFF_SECONDS` | Base backoff | `15` |
| `ARKADIA_PR_REVIEW_REPLAY_WINDOW_SECONDS` | Delivery dedup window | `600` |
| `ARKADIA_PR_REVIEW_TEST_EVIDENCE_REF` | Evidence ref for `TESTED` | omitted |

**Never** set `GITHUB_TOKEN` and expect the worker to use it. It will not.

## 4. Daily operation

### 4.1 Check the rollout state

```
GET /api/lab/engineering/pr-review/status
```

Read `rollout.state`. It is derived: `IMPLEMENTED` (code present, worker not
configured), `SHADOW` (worker configured, read-only), `ACTIVATED` (worker
configured **and** an activation reference present). A stage string alone never
produces `ACTIVATED`.

### 4.2 Request a shadow review

```
POST /api/lab/engineering/pr-review/request
{
  "repository": "Arkadia-Oversoul-Prism/Arkadia",
  "pr_number": 748,
  "base_sha": "<40-char base sha>",
  "head_sha": "<40-char head sha>",
  "installation_id": 12345678,
  "event_id": "manual-2026-11-26-1"
}
```

The response carries `result.status`, `result.findings`, `markdown` and
`evidence`. Re-posting the same `event_id` for the same head returns the stored
result with `deduplicated: true`; it does not review twice.

### 4.3 Read a queued ingress job

Webhook deliveries enqueue jobs. Run one with:

```
POST /api/lab/engineering/pr-review/jobs/{job_id}/run
```

Then read it with `GET /api/lab/engineering/pr-review/jobs/{job_id}`. The
response includes the findings, the report, and the Lab evidence records.

### 4.4 Dead letters

```
GET /api/lab/engineering/pr-review/jobs?state=DEAD_LETTER
```

Each dead letter carries `failure_reason`. The three causes worth knowing:

| Reason | Meaning | Action |
|---|---|---|
| `GitHub App worker is not configured: missing …` | Configuration gap | set the named variables |
| `GitHub read … failed: http 401/403` | Token expired or under-scoped | re-mint the installation token |
| `repository '…' is not in the worker installation allowlist` | Delivery for a repository this worker is not installed on | investigate; do not widen the allowlist to "fix" it |

## 5. Publishing a review (stage D — not enabled by default)

Publishing requires **four** independent conditions. Any one of them missing is
a refusal:

1. stage `ACTIVATED` **and** an activation reference,
2. the action's policy flag (`ALLOW_COMMENT` / `ALLOW_REQUEST_CHANGES` /
   `ALLOW_APPROVE`),
3. a human grant binding `repository#pr@head:ACTION`, recorded by an
   authenticated principal that is **not** the PR author,
4. the head unchanged at publish time, re-fetched immediately before the write.

Record the grant:

```
POST /api/lab/engineering/pr-review/jobs/{job_id}/grant
{ "action": "PUBLISH_COMMENT", "duration_minutes": 15 }
```

The response states the exact tuple, the expiry, and the consequences. Then:

```
POST /api/lab/engineering/pr-review/jobs/{job_id}/publish
{ "action": "PUBLISH_COMMENT", "authorization_ref": "AUTH-…" }
```

The grant is single-use: it is consumed atomically. A second publish with the
same grant is refused. A head change invalidates it.

## 6. Disable

Set `ARKADIA_PR_REVIEW_STAGE=SHADOW` (or unset the installation token). Both
take effect on the next request — nothing is cached at import time. To stop
ingress entirely, delete the App webhook; a delivery without a secret is
refused with 503 regardless.

## 7. What this capability will never do

* Merge, enable auto-merge, or add a PR to a merge queue.
* Push, force-push, or write to a branch.
* Deploy, release, sign, or activate a production surface.
* Read a secret or a repository secret.
* Approve a change authored by the approving principal.
* Treat a `GREEN` review as authorization for any of the above.

If any of these appear to have happened, treat it as a boundary regression and
stop for human review.
