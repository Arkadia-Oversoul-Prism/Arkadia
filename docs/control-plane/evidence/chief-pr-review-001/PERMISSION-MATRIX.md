# ARKADIA-CHIEF-PR-REVIEW-001 — permission matrix

Least privilege is a property of the **worker**, not of the reviewer's intent.
The GitHub App installation token is the only credential the capability will
use; a user PAT, an ambient connector credential, or a prompt claim is refused
by name (`lab/engineering_lab/github_app.py::REFUSED_CREDENTIAL_SOURCES`).

## Requested App permissions (union the App is asked to grant)

| Scope | Level | Why it is needed |
|---|---|---|
| `metadata` | read | Required by GitHub for every App installation. |
| `contents` | read | Read the diff, the head commit, and the files the review inspects. |
| `pull_requests` | **write** | Required only for the `PUBLISH_COMMENT` / `REQUEST_CHANGES` / `APPROVE` actions, which are disabled by default. |
| `checks` | read | Read check runs on the exact head so a finding can cite a real check output. |

## Deliberately **not** requested

`checks: write`, `statuses: write`, `administration: write`, `secrets: read`,
`workflows: write`, `deployments: write`, `contents: write`, `packages: write`,
`organization_administration: write`.

Two consequences worth stating:

* A review can never manufacture a green check. It reads check output; it does
  not create it.
* A review can never push, merge, deploy, or read a secret. Those are not in the
  token's scope, so the boundary is enforced by GitHub as well as by this code.

## Capability -> permission map

| Capability | Permissions used |
|---|---|
| `read_repository` | `contents: read`, `metadata: read` |
| `read_pull_request` | `pull_requests: read`, `contents: read`, `metadata: read` |
| `read_checks` | `checks: read`, `metadata: read` |
| `publish_review` | `pull_requests: write`, `contents: read`, `metadata: read` |

## Action -> gate map

Every action has its own gate (`lab/engineering_lab/pr_review.py::ACTION_GATES`).
Passing one gate never implies another.

| Action | Writes GitHub | Minimum stage | Policy flag | Human-only |
|---|---|---|---|---|
| `READ` | no | `IMPLEMENTED` | — | no |
| `GENERATE_FINDINGS` | no | `IMPLEMENTED` | — | no |
| `PUBLISH_COMMENT` | yes | `ACTIVATED` | `allows_comment` | no (grant required) |
| `REQUEST_CHANGES` | yes | `ACTIVATED` | `allows_request_changes` | no (grant required) |
| `APPROVE` | yes | `ACTIVATED` | `allows_approve` | no (grant required, independent principal) |
| `MERGE` | — | — | — | **yes — refused unconditionally** |

`MERGE` is in `STRUCTURALLY_REFUSED`. `assert_action_permitted` raises before it
reads the stage, so no configuration can enable it. The Lab's own
`FORBIDDEN_OPERATIONS` already lists `merge`, and `HUMAN_ONLY` already lists
`MERGE`; this capability reuses that vocabulary rather than extending it.

## Repository allowlisting

Two independent allowlists must both admit the repository:

1. `ARKADIA_PR_REVIEW_REPOSITORIES` — the worker installation binding.
2. `ReviewPolicy.repositories` — the review policy.

A repository outside either is refused (`WorkerUnavailable` /
`BoundaryViolation`), including when the webhook signature is valid: a signature
proves the sender, not the target.

## Credential sources

| Source | Accepted |
|---|---|
| `ARKADIA_PR_REVIEW_INSTALLATION_TOKEN` (App installation token) | yes |
| `GITHUB_TOKEN` | **no** |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | **no** |
| `GH_TOKEN` | **no** |
| ambient connector credential | **no** |
