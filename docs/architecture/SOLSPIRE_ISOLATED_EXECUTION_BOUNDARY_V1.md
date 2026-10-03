# SolSpire Isolated Project Execution Boundary v1

## Scope of this slice

This change adds a fail-closed OCI invocation builder and a reviewed-patch gate. It is a boundary primitive, not yet a claim that every Engineering Lab execution route has been migrated to it.

## Container policy

- Container runtime missing: refuse execution; never fall back to host execution.
- Network: disabled by default (`--network=none`).
- Container root filesystem: read-only.
- Linux capabilities: all dropped; no-new-privileges enabled.
- Process identity: unprivileged UID/GID.
- Resource limits: memory, CPU, process count, temporary filesystem, and execution timeout.
- Invocation: argv-only, no shell interpolation.
- Workspace: caller must supply a disposable copy of the canonical project snapshot. Never mount the canonical project-store directory as the writable workspace.

## Persistence contract

Container output is a candidate patch, not canonical project state. Before persistence, the application must:

1. compute the candidate diff and changed-path set;
2. validate paths and the project-specific allowlist;
3. compare the canonical base digest to the digest reviewed by the human;
4. require explicit human approval for the exact patch;
5. persist through the existing canonical project file API, not by writing directly to the project database;
6. append a WorkEvent with patch digest, approver identity, affected paths, and result.

The included `require_reviewed_patch` helper enforces approval, freshness, and path allowlisting. It does not itself write canonical files. No agent output may bypass this gate.

## Threat-model boundary

An OCI container is not a virtual machine and does not protect against a compromised host kernel or malicious container runtime. Production deployment must pin images by immutable digest, apply host-level seccomp/AppArmor/SELinux policy where available, enforce quotas, and verify that the selected runtime honors all requested flags. The image string accepted by the helper should be digest-pinned by production configuration and deployment policy.

## Verification

Unit tests cover network-disabled defaults, read-only root filesystem, dropped capabilities, no-new-privileges, unprivileged execution, resource limits, path traversal rejection, human approval, stale-base rejection, and patch allowlisting.

## Explicitly not claimed

- Engineering Lab routes are not yet all wired to call `run_isolated`.
- No production container runtime has been probed by this change.
- Candidate patches are not yet automatically applied to canonical project files.
- No live deployment or production isolation claim is made by adding these primitives alone.
