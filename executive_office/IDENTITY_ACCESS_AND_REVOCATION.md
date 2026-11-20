# ARKADIA-CHIEF-001 — Identity, Workspace Access and Revocation Contract

**Document:** ARK-EXEC-IDENTITY-ADR-001  
**Status:** PROPOSED — security design for human review; not commissioned  
**Applies to:** Chief Agent API access, data access, delegated operations and emergency suspension  
**Policy baseline:** `ARK-EXEC-AUTH-001`, version 1 (still proposed/inactive)

This document makes the identity and access model explicit. It does not create credentials, bind a real founder UID, activate access, or grant execution authority.

## 1. Decision summary

1. `ARKADIA-CHIEF-001` is a distinct machine principal. It never logs in as, impersonates, or inherits the Firebase identity of the Founder.
2. The Founder remains the data owner and human authority. The Chief Agent is an explicitly delegated actor whose access is limited by a durable grant.
3. The Chief Agent gets no access to any workspace until a Founder-authenticated commissioning action binds the service principal to the Founder’s verified Firebase UID and one exact existing workspace ID.
4. The first grant is read-only and organizationally scoped. Personal conversations, private codex, credentials, secrets, and unrelated personal records are excluded.
5. The agent authenticates to Arkadia through a separate identity broker that issues short-lived, audience-bound machine tokens. The agent never receives the broker signing key and never receives a Firebase user token.
6. Every API request and every execution dispatch checks the current durable delegation state. A valid token is necessary but is never sufficient after revocation, expiry or policy change.
7. Revocation is a durable server-side state transition, not merely deletion of a token or rotation of a secret. It blocks new requests and outstanding execution authorizations.

**No runtime code may be implemented against a weaker interpretation of this contract.**

## 2. Principal and authentication

### 2.1 Canonical principal

| Field | Required value |
|---|---|
| Principal ID | `ARKADIA-CHIEF-001` |
| Principal type | `machine_service` |
| Human owner / delegator | Founder, resolved from verified Firebase authentication at commissioning |
| Authentication issuer | Dedicated Arkadia Executive Identity Broker |
| Audience | `arkadia-executive-api` |
| Default state | `DISABLED` |
| Default authority | `NONE` |
| Credential lifetime | Maximum 5 minutes per access token |
| Interactive login | Prohibited |
| Firebase user impersonation | Prohibited |
| Founder approval credential | Separate human Firebase ID token; never delegated to the agent |

The Founder UID must not be guessed, copied from an unverified client payload, committed to YAML, or supplied by the agent. A Founder-only commissioning screen obtains it from the server-side verified Firebase principal. The screen resolves the existing canonical workspace using `WorkspaceManager.get_for_subject(verified_uid)`; it must not silently create a workspace as a side effect of granting access.

### 2.2 Token issuance

The selected pattern is a broker-issued, asymmetric-signed, short-lived JWT. It is preferred over extending `api.auth.require_auth` to accept machine tokens indiscriminately.

The broker is a separate trust boundary from the agent process:
- The broker owns the signing private key; the Chief Agent runtime cannot read or export it.
- The runtime authenticates to the broker using a hosting-native workload identity (preferred) or a broker-specific, rotatable client credential constrained to this one principal. The latter is a temporary fallback, not equivalent to workload identity.
- The broker issues a token only when the durable delegation record is `ACTIVE`, not expired, not revoked, and bound to the current approved policy digest.
- The broker fixes `sub`, owner, workspace, audience and allowed scopes from the server-side grant. The agent cannot choose or widen these claims.
- The API verifies signature, issuer, audience, expiry, not-before, token type and key ID against pinned broker JWKS. It then checks the live delegation record and policy version before serving the request.
- Maximum token TTL: 300 seconds. No refresh token. No long-lived JWT. No token in prompts, logs, WorkEvents, Git history or model context.

Required claims:

| Claim | Required semantics |
|---|---|
| `iss` | Exact configured Executive Identity Broker issuer |
| `aud` | Exactly `arkadia-executive-api` |
| `sub` | Exactly `service:ARKADIA-CHIEF-001` |
| `principal_type` | `machine_service` |
| `owner_sub` | Founder Firebase UID from the active delegation record |
| `workspace_id` | One exact canonical SolSpire workspace ID |
| `delegation_id` | Durable grant identifier |
| `policy_id` / `policy_version` / `policy_digest` | Exact approved policy snapshot |
| `scope` | Server-issued capability/resource allowlist; never client-selected |
| `jti` | Unique token identifier for audit and replay controls |
| `iat`, `nbf`, `exp` | Short validity window; maximum 300 seconds |

A token is rejected if any claim is missing, malformed, broader than the active grant, or inconsistent with the durable delegation record.

### 2.3 Hosting prerequisite

The repository does not establish a hosting-native workload identity on the current Render deployment. Therefore:
- Do not invent a Render identity feature or assume the service has one.
- Before commissioning, select and verify the broker-to-runtime authentication mechanism with the actual hosting provider.
- If a broker client secret is unavoidable for the first deployment, keep it in the platform secret store, never expose it to model/tool input, restrict it to requesting tokens for this one fixed principal, rotate it, and provide a tested kill/revoke path.
- A GitHub App is a separate repository credential. It does not authenticate the Chief Agent to Arkadia APIs and does not authorize access to the Founder’s workspace.

### 2.4 Integration with existing Firebase auth

Human Console routes continue to use `api.auth.require_auth` and verified Firebase UID. Machine routes use a new explicit machine-principal dependency, e.g. `require_executive_principal`, that validates the broker token and durable delegation. Do not weaken `require_auth` or treat an arbitrary JWT as Firebase.

Production Executive Office routes must fail closed if Firebase production auth is not initialized. The current `api.auth` development mode decodes JWT payloads without signature verification when credentials are absent; that mode is strictly local development and must never be enabled for the Chief Agent, broker, or any deployed Executive Office route.

The Chief Agent must not receive the `Flamekeeper` role or `access_level >= 3`. It is not a governance principal. Human authorization remains a separate authenticated Founder action.

## 3. Workspace and subject binding

### 3.1 Owner model

- **Data subject:** Founder’s verified Firebase UID.
- **Workspace:** one existing canonical SolSpire workspace whose `canonical_subject_ref` equals that UID.
- **Actor:** `service:ARKADIA-CHIEF-001`.
- **Delegation:** explicit, revocable relation connecting actor → owner → workspace → policy → allowed resources/capabilities.

The service principal must never become the `subject_ref` owner of Founder records merely because it performs an action. Where existing records require `subject_ref`, preserve the Founder as subject and record the Chief Agent as actor/provenance. If a record schema cannot separately represent actor and owner, do not write through that schema until it is extended and reviewed.

### 3.2 Workspace access

Initial read-only grant: exactly one Founder-owned canonical SolSpire workspace, by immutable workspace ID. No wildcard workspace selection, no access to other users, no public/shared workspaces beyond the specifically enumerated public corpus.

The grant must include:
- `owner_uid` (server-bound; never supplied by the agent);
- `workspace_id` (resolved from the owner UID);
- allowed project/workload IDs (explicit list; empty means no project-level access);
- allowed record families and fields;
- allowed Knowledge OS note IDs or a deliberately curated organizational collection;
- policy version/digest;
- start time, expiry, status and revocation metadata.

The agent cannot call `get_or_create` to acquire access. It can only resolve the workspace already named by an active delegation.

### 3.3 First-phase data allowlist

The initial read-only commissioning scope should be limited to the following, with every query filtered by both verified owner UID and workspace/resource grant where applicable:

| Record family | Initial access | Conditions |
|---|---|---|
| Arkadia repository | Read-only | Explicit repository installation and branch/path allowlist; no secrets, Actions secrets, environment variables or write scopes |
| Project/workload metadata | Read-only | Only enumerated project/workload IDs in the Founder workspace |
| SolSpire proposals and feedback | Read-only | `subject_ref = owner_uid` AND `workspace_ref = workspace_id`; exclude unrelated subjects/workspaces |
| SolSpire WorkEvents | Read-only | Same subject + workspace filter; bounded page/limit and time range |
| ARK-WEAVER-01 operational records | Read-only | Same subject + enterprise/workspace binding; expose only fields needed for operational reporting |
| Authorizations and execution evidence | Metadata/read-only | Same owner binding; redact secret-bearing payloads; never treat existing authorization as a standing agent grant |
| Knowledge OS public corpus | Read-only | NULL-owner seeded corpus only where `note_type <> 'conversation'` |
| Founder-owned Knowledge OS notes | Denied by default | Add only exact note IDs or a curated Arkadia organizational collection through an explicit grant |
| Conversation notes, chat transcripts, private threads | **Denied** | No broad owner UID access to private conversations; no session/thread IDs supplied by the agent can widen scope |
| Personal Codex and personal profile files | **Denied** | Not required for Arkadia operations |
| Secrets, API keys, tokens, environment variables, private credentials | **Denied** | No read path, listing, logging or model-context injection |
| Personal, family, health, financial or other unrelated personal records | **Denied** | Outside organizational purpose; no inferred access from Founder ownership |
| Other users’ workspaces or records | **Denied** | No cross-subject access, even if IDs are known |

The existing Knowledge OS `assemble_context` owner filter allows all notes owned by the supplied UID plus the public non-conversation corpus. That is broader than the Chief Agent’s intended organizational need. Therefore **do not pass the Founder UID to generic Knowledge OS retrieval for the Chief Agent** until a narrower collection/note-ID filter is implemented and tested. Do not use a blank UID as a workaround: it is not a substitute for a purpose-specific data grant.

### 3.4 Query enforcement

Every repository adapter and database read must derive owner/workspace/resource filters from the validated delegation context, not from request JSON, prompt text, tool arguments or model-generated SQL.

Mandatory checks:
1. Validate active machine token and live delegation.
2. Resolve `owner_uid`, `workspace_id`, allowed resource IDs and data classes from the durable grant.
3. Apply owner + workspace + resource predicates in the database query itself.
4. Reject caller-supplied owner/workspace overrides, or verify exact equality with the grant.
5. Enforce field redaction before data reaches the model.
6. Record the data class, resource reference, query purpose, policy digest and result count in audit metadata; never log raw secrets or unnecessary personal content.

A missing owner, workspace, allowlist, policy digest or scope means deny.

## 4. Authority model

The Chief Agent receives no general role-based authority. It receives named capabilities from a signed delegation record.

### Initial commissioning envelope

| Capability | Initial state |
|---|---|
| Read approved Arkadia repository paths | Allow after commissioning |
| Read approved Arkadia project/workload metadata | Allow after commissioning |
| Read approved SolSpire/Weaver operational records | Allow after commissioning |
| Read approved organizational Knowledge OS collection | Allow after collection is explicitly curated |
| Produce internal analysis and reports | Allow after commissioning |
| Create proposals for human review | Not in initial read-only grant; add as a separately reviewed capability |
| Create or modify tasks/docs | Deny until separately allowlisted |
| Run tools, tests or commands | Deny until separately allowlisted and sandboxed |
| Create branches or pull requests | Deny until separately allowlisted |
| Authorize proposals or issue human authority events | Always human-only |
| Execute payments, contracts, hiring, legal acts, protected merges, deployments, security changes | Always human-only |

The machine principal cannot approve itself, modify the delegation, grant new capabilities, change its owner/workspace, alter policy, revoke its own audit trail, or mint human approval records.

A Founder-authenticated action must bind any future authorization to:
- the exact proposal and payload digest;
- exact tool/channel and resource scope;
- exact owner/workspace;
- policy ID/version/digest;
- constraints (read-only, network, repository root, budget, time window);
- expiry;
- one-time or explicitly bounded use;
- an independent human actor.

## 5. Revocation and emergency suspension

### 5.1 Durable delegation record

Create a dedicated, durable Executive Delegation Registry before issuing any token. This is not yet present in the inspected repository and must not be simulated with process memory.

Minimum fields:

| Field | Purpose |
|---|---|
| `delegation_id` | Immutable grant ID |
| `principal_id` | `ARKADIA-CHIEF-001` |
| `owner_uid` | Founder UID from verified Firebase session |
| `workspace_id` | Exact canonical workspace |
| `policy_id`, `policy_version`, `policy_digest` | Approved authority snapshot |
| `resource_scope`, `capability_scope` | Explicit allowlists |
| `status` | `PENDING`, `ACTIVE`, `SUSPENDED`, `REVOKED`, `EXPIRED` |
| `effective_from`, `expires_at` | Time bounds |
| `created_by`, `approved_by` | Human provenance; must be the authorized Founder |
| `created_at`, `updated_at` | Audit timestamps |
| `revoked_at`, `revoked_by`, `revocation_reason` | Revocation evidence |
| `credential_epoch` | Invalidates previously issued tokens after rotation/revoke |
| `last_policy_check_at` | Operational visibility, not a source of authority |

The record is append-only in its event history. Current status is a materialized state derived from those events. No runtime-local cache may outlive the token TTL; for consequential execution, re-check live state immediately before dispatch.

### 5.2 Revocation triggers

Any one of the following must suspend or revoke access:
- Founder selects **Suspend Chief Agent** or **Revoke delegation**;
- suspected credential compromise or unexpected principal use;
- Founder UID/workspace binding changes;
- policy version/digest changes without explicit re-approval;
- runtime or broker integrity failure;
- audit store or revocation registry unavailable;
- expiry reached;
- hosting/operator emergency kill switch activated.

### 5.3 Revocation sequence

1. Set the delegation to `SUSPENDED` or `REVOKED` in the authoritative registry; commit the revocation event first.
2. Increment `credential_epoch` and reject all tokens carrying the previous epoch.
3. Disable token issuance at the broker for this principal.
4. Reject all Executive Office API requests immediately, including otherwise unexpired JWTs.
5. Stop/cancel queued and scheduled Chief Agent work; do not dispatch new tool calls.
6. Revoke or disable the broker client credential/workload binding.
7. Revoke the GitHub App installation or reduce its permissions if repository access is in scope; rotate any associated credentials.
8. Mark every outstanding agent-associated Authorization as revoked/invalid and make Weaver dispatch reject it. Existing authorizations must not survive revocation merely because they have not expired.
9. Preserve audit records, evidence and reports; do not delete history.
10. Emit a Founder-visible confirmation with the delegation ID, time, affected credentials and outstanding work inventory.

Suspension is reversible only by a new Founder-authorized reactivation event. Revocation is terminal for that delegation ID; reactivation creates a new grant and new credentials.

### 5.4 Fail-closed requirements

- Registry unavailable, stale, unreadable or inconsistent → deny.
- Broker unavailable → deny new token issuance; existing token requests still fail if live status cannot be checked.
- Policy digest mismatch → deny.
- Expired token or delegation → deny.
- Revoked/suspended credential epoch → deny.
- Unrecognized principal, audience, issuer or scope → deny.
- Revocation event cannot be durably committed → do not claim revoked; keep emergency network/process kill active and report incomplete revocation.

### 5.5 Existing execution authorization gap

The inspected `weaver.enterprise_orchestration` Authorization schema has `expires_at`, but the current `authorization()` read method does not itself enforce expiry or a revocation state. The existing execution adapter validates tool scope and constraints but has no durable authorization-revocation check. The architecture notes also record missing expiry transitions.

**This is a hard blocker before any Chief Agent execution capability.** Add a durable revocation/status mechanism and enforce active status, expiry, delegation status and policy digest at the last responsible execution boundary. Do not assume deleting a JWT, changing the proposal status or hiding a UI button revokes an existing authorization.

## 6. Audit and accountability

Every authentication and access decision must emit a structured event with:
- principal ID and token `jti` (never the raw token);
- owner UID and workspace ID;
- delegation ID and credential epoch;
- policy digest;
- endpoint/capability and resource/data class;
- allow/deny decision and reason;
- timestamp and correlation ID;
- human approval/authorization reference where applicable.

Sensitive values, raw private notes, credentials and tokens must not be included in audit payloads. Audit records are append-only and inaccessible for deletion by the Chief Agent.

## 7. Required negative tests before commissioning

1. No token → 401.
2. Firebase human token presented to machine-only endpoint → rejected as machine identity.
3. Machine token presented to human-only approval endpoint → rejected.
4. Wrong issuer, audience, signature, token type, expired token or future `nbf` → rejected.
5. Token with altered `sub`, owner, workspace, policy digest or scope → rejected.
6. Revoked/suspended delegation with otherwise valid JWT → rejected immediately.
7. Expired delegation with valid JWT → rejected.
8. Old credential epoch after rotation → rejected.
9. Registry unavailable → rejected.
10. Agent attempts to set owner UID/workspace ID in payload → rejected.
11. Agent attempts to read another subject’s project, note, thread, proposal or WorkEvent → no data returned and access denied/audited.
12. Agent attempts generic Knowledge OS retrieval across all Founder-owned notes → rejected until curated-scope retrieval exists.
13. Agent attempts to read conversation notes, personal Codex, credentials or secret configuration → rejected.
14. Agent attempts to create/approve its own authorization, modify policy or change its own delegation → rejected.
15. Outstanding Weaver authorization after revocation → dispatch rejected.
16. Revoke during a queued job → job cancelled or prevented from dispatch; no post-revocation new side effect.
17. Restart the API/broker and verify delegation and revocation state remain effective.

## 8. Implementation sequence

### Gate 1A — Security and identity foundation
- Approve this ADR and exact policy digest.
- Select a supported hosting-to-broker workload identity mechanism.
- Implement the durable delegation registry and append-only delegation events.
- Implement broker issuance and explicit machine-token verification.
- Add the Founder-only grant/suspend/revoke interface.
- Add the negative tests above.

### Gate 1B — Workspace and data boundary
- Resolve Founder UID from authenticated Founder session at grant time.
- Resolve and pin the existing canonical workspace ID.
- Add explicit project/resource and data-class allowlists.
- Add a Knowledge OS curated organizational collection or note-ID constrained retrieval; do not pass broad Founder UID into generic context retrieval.
- Add field redaction and access-decision audit events.

### Gate 1C — Execution revocation
- Add durable revocation/expiry enforcement for enterprise Authorizations.
- Ensure Weaver checks authorization and delegation state immediately before dispatch.
- Ensure queued work and outstanding authorizations are invalidated on revoke.
- Test kill switch, credential rotation and restart recovery.

### Gate 1 exit criteria

No Chief Agent token can be issued until identity, owner, workspace, policy, resource scope and expiry are recorded in an active delegation. No read can occur without live scope checks. No execution can occur without a separate human authorization and a live, unrevoked delegation. The Founder can suspend/revoke access and prove that the change survives restart.

## 9. Explicitly not activated

- No machine principal has been created in Firebase or any broker.
- No Founder UID or workspace has been bound.
- No token, secret, GitHub App, or broker credential has been created.
- No Knowledge OS personal data access has been granted.
- No delegation is active.
- No runtime code or endpoint has been implemented.
- `ARKADIA-CHIEF-001` remains `PROPOSED_NOT_COMMISSIONED`.
