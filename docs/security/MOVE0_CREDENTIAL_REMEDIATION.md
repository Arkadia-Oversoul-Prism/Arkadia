# Move 0 — Credential Remediation Record

**Date:** 2026-09-12
**Authorization:** Full Credential Remediation, Phases 2–8
**Disposition:** PARTIALLY EXECUTED / BLOCKED AT EXTERNAL PROVIDER + HISTORY CLEANUP BOUNDARIES

## Scope authorized

1. Determine active credentials
2. Rotate compromised credentials
3. Move active secrets to deployment secret storage
4. Remove credential artifacts from the repository
5. Clean Git history
6. Verify runtime consumers
7. Re-audit the credential boundary

## Executed

### Current repository surface

- Removed `data/ims_credentials_sealed.json` from the current tree.
- Added `data/ims_credentials_sealed.json` to `.gitignore`.
- Removed hardcoded IMS passwords from `scripts/create_ims_accounts.py`.
- Reworked the IMS provisioner so passwords are supplied through environment variables or generated in memory and are never persisted to a credential document.
- Added an explicit `ROTATE_EXISTING=1` path for Firebase password rotation.
- Removed the legacy sovereign-key value from `.env.example`.
- Removed the legacy sovereign-key value from repository security documentation.
- Recorded the historical exposure without reproducing the credential values.

### Runtime secret

- Generated a new high-entropy `SOVEREIGN_KEY`.
- Updated the production Render `Arkadia` web service secret.
- Render automatically triggered a deployment from the updated secret.
- No secret value is recorded in the repository or remediation document.

## Not yet executable through the connected interfaces

### IMS Firebase password rotation

The repository now contains a safe rotation-capable provisioner, but the connected interfaces do not provide a safe one-off execution channel with the existing Firebase Admin service-account secret. The provisioner must be run in an approved operator environment with Firebase Admin credentials and `ROTATE_EXISTING=1`.

Until that execution occurs, previously exposed IMS passwords must be treated as compromised.

### Historical Gemini credential rotation

The historical Gemini credential was removed from the current source surface before this remediation. Provider-side invalidation/rotation still requires access to the Google/Gemini credential-management surface. No replacement credential was fabricated, because doing so would break the provider boundary rather than rotate it.

### Git history cleanup

The repository contains historical credential-bearing commits. Current-tree deletion does not remove those objects from Git history.

The connected GitHub interface permits ref updates and object creation, but does not provide a safe bulk history-rewrite/filter operation. A destructive squashed replacement of the post-exposure history would discard legitimate commit ancestry and is therefore not performed merely to satisfy the appearance of completion.

The history-cleanup phase remains blocked until a history-rewrite operation can preserve the legitimate repository ancestry while removing all credential-bearing objects and references.

## Verification state

| Boundary | State |
|---|---|
| Current IMS credential artifact | CLEANED FROM CURRENT TREE |
| IMS artifact ignore rule | ESTABLISHED |
| IMS source hardcoded passwords | REMOVED |
| Current sovereign secret | ROTATED IN RENDER |
| Current `.env.example` sovereign secret | CLEANED |
| Current security-audit secret references | SANITIZED |
| Historical IMS credential objects | REMAIN IN HISTORY |
| Historical sovereign-key objects | REMAIN IN HISTORY |
| Historical Gemini-key objects | REMAIN IN HISTORY |
| IMS live-password rotation | PENDING OPERATOR EXECUTION |
| Gemini provider rotation | PENDING PROVIDER ACCESS |
| Git history rewrite | BLOCKED BY AVAILABLE TOOLING |
| Final Move 0 gate | **BLOCKED** |

## Constitutional boundary

Credential remediation does not establish Architect identity.

The sequence remains:

```text
Credential remediation
        ↓
Known-safe credential boundary
        ↓
STOP
        ↓
Architect authorization
        ↓
Move 1 — Architect Identity
```

No Architect identity was provisioned by this remediation.

## Re-audit requirement

Move 0 may only be marked **PASS** after:

1. all historically exposed active credentials have been invalidated or rotated;
2. IMS passwords have been rotated through Firebase Admin;
3. the historical Gemini credential has been invalidated/rotated;
4. Git history has been rewritten without losing legitimate ancestry;
5. the rewritten repository has been scanned for credential-bearing objects and references;
6. Render authentication and provider-backed runtime paths have been verified after rotation;
7. no secret material remains reachable through the repository's retained history.

Until those conditions are satisfied, **Move 1 remains blocked**.
