# SolSpire Isolated Project Execution Boundary v1

## Execution boundary

Project-scoped Engineering Lab sessions materialize a unique disposable copy of the canonical project files. Snapshot creation is bracketed by canonical base digests; if the canonical store changes during materialization, the run is refused. The canonical project-store directory is never mounted into a container.

Project terminal operations route through the configured Docker-compatible OCI runtime using argv-only execution. The configured image must be pinned by immutable SHA-256 digest. If the runtime or image configuration is missing, execution fails closed with no host-command fallback.

Container defaults:
- `--network=none`
- read-only container root filesystem
- all Linux capabilities dropped
- no-new-privileges
- unprivileged UID/GID 65532:65532
- CPU, memory, process-count and timeout limits
- bounded writable mount only for the disposable project snapshot
- `/tmp` mounted as no-exec, no-suid tmpfs
- shell-free host process invocation

The L1 terminal grammar remains closed to its existing allowlisted commands, and git commands remain read-only. The new `filesystem.propose_edit` tool returns replacement text for an existing seeded project file without writing even to the disposable workspace. It is exposed only when the agent has EDIT capability and the human authorization explicitly includes `candidate_write`. New files and deletions are not accepted by this first patch flow.

## Candidate and canonical persistence

After a project-scoped agent loop, the API compares the disposable workspace against the canonical snapshot and returns a candidate patch, its base digest, its exact patch digest, changed paths, rejected paths, and `persistence: NOT_APPLIED`.

Canonical persistence is a separate owner-authenticated action:
1. Preview validates the expected base digest, existing canonical paths and explicit allowlist.
2. The human reviews the exact candidate content and receives a deterministic patch digest.
3. Apply requires the same base digest, the same exact patch digest and the explicit allowed-path set.
4. The canonical project store validates all file bindings and applies existing-file updates atomically in one transaction.
5. A WorkEvent records the authenticated approver, project scope, changed file references, base/result digests and patch digest.

A stale base, unapproved digest, path outside the allowlist, missing canonical workspace, duplicate path, or non-existing file fails closed. This first version supports updates to existing text files only. Creating and deleting canonical files remain separate governed operations.

Endpoints:
- `POST /solspire/projects/{project_id}/patches/preview`
- `POST /solspire/projects/{project_id}/patches/apply`
- `POST /api/lab/engineering/sessions/{session_id}/run-agent` returns candidate-only edits for project sessions.

## Arkana, continuity and Knowledge OS

The owner-scoped project runtime context composes the existing canonical project store with Daily Pulse, project-matching WorkEvents, the bounded semantic knowledge graph and Arkana's project context. These are read-only context/evidence, not authority. Missing pulse or WorkEvent project bindings remain `UNKNOWN`; they are not synthesized from project existence.

## Live integration health and Living Larder

`GET /solspire/projects/{project_id}/integration-health` exercises local capability paths for Weaver, Arkana and Knowledge OS, verifies the container runtime/image configuration, and reports Living Larder as `PROJECT_BOUND` only when an order was explicitly bound to that project.

`POST /solspire/projects/{project_id}/living-larder/orders/{order_id}/bind` verifies the order exists in the configured Living Larder order store and records a bounded financial snapshot in project events plus a WorkEvent. It deliberately excludes customer details. No historical order is auto-associated with a project.

A configured capability is not proof of a successful probe. `AVAILABLE`, `UNAVAILABLE`, and `UNBOUND` have distinct meanings. Integration health never grants execution or patch approval.

## Threat-model boundary

An OCI container is not a virtual machine and does not defend against a compromised host kernel or malicious container runtime. Production still requires a trusted hardened host, seccomp/AppArmor/SELinux policy where available, quotas, immutable image verification, and deployment-level testing. The API route must not be considered production-isolated until the live runtime acceptance test passes in the target environment.

## Verification

Tests cover argv hardening, no-host-fallback behavior, digest pinning, exact patch digest approval, canonical base freshness, atomic canonical file updates, WorkEvent evidence, candidate-only workspace diffs, explicit Living Larder binding, and integration-health truthfulness. A live OCI acceptance test is included and uses a SHA-256-pinned minimal BusyBox image by default (overridable with `SOLSPIRE_TEST_AGENT_IMAGE`). It skips only when a Docker-compatible runtime is unavailable.

## Current limitations

- The live OCI acceptance test has not yet been confirmed to run in this environment.
- CI must be inspected after the final branch commit; absence of workflow runs is not a green result.
- No production deployment or end-to-end production isolation claim is made here.
- Patch application currently updates existing canonical text files only; new-file/deletion workflows remain out of scope.
