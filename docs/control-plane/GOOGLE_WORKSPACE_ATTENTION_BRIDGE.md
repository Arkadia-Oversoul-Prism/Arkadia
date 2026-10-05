# Google Workspace Attention Bridge

## Live path

`Firebase-authenticated user → Google OAuth → encrypted refresh token → Attention Event → Tasks / Keep / Workspace Studio / FCM → ATTENTION_DELIVERY_ACK evidence`

Google's Workspace Studio custom starter requires the `workspace.studio.trigger` scope and an offline refresh token for asynchronous firing. citeturn2search0

### Required server configuration

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI`
- `SOVEREIGN_KEY`
- `ARKADIA_ATTENTION_OWNER_UID`
- `ARKADIA_ATTENTION_DELIVERY_URL` when the hourly Weaver runner should fan out automatically

The OAuth consent configuration must request:
- `https://www.googleapis.com/auth/tasks`
- `https://www.googleapis.com/auth/keep`
- `https://www.googleapis.com/auth/workspace.studio.trigger`

Tasks write access uses the Tasks scope. citeturn0search1turn0search14

Keep note creation requires `https://www.googleapis.com/auth/keep`; the current Keep API is enterprise-oriented and supports note creation/listing. citeturn1search0turn1search5

### User authorization

Authenticated Console user calls:

`GET /api/google-workspace/oauth/start`

The backend returns the Google consent URL. After approval Google redirects to:

`GET /api/google-workspace/oauth/callback`

The resulting refresh token is encrypted at rest using the existing `SOVEREIGN_KEY` mechanism. No Google refresh token is committed to Git.

### Workspace Studio starter

The repository contains:

- `google_workspace/appsscript.json`
- `google_workspace/Code.gs`

The starter exposes an `arkadiaUserId` configuration input and lifecycle handler. Google sends `triggerCreation` and `triggerDeletion` lifecycle events; Arkadia stores the active trigger and notify URI per user. citeturn2search0

Configure the Studio flow to use the **Arkadia Attention Event** starter. The flow can then branch into Google-native actions such as Tasks, Gmail, Chat, or a Keep-capable integration. Workspace Studio is the routing layer, not the canonical Arkadia ledger.

### Keep response feed

Every Keep delivery creates a bounded human-readable note:

`ARKANA // <event_type> · <subject>`

This is intentionally an event feed rather than a mutable canonical record. The Keep API currently exposes create/list/get/delete operations rather than a generic note-update method, so the feed is modeled as immutable event notes. citeturn1search1turn1search3

### Push provider

Firebase Cloud Messaging is the push provider.

The Console registers a device token through:

`POST /api/google-workspace/push/device`

with the authenticated Firebase user. The server uses Firebase Admin Messaging to send an Arkana notification to that user's registered device tokens. Firebase documents the Admin SDK `send_each_for_multicast` path for multicast delivery. citeturn1search4

### Delivery acknowledgements

Each attempted channel delivery writes an `ATTENTION_DELIVERY_ACK` record into the canonical `ew_evidence` ledger with:

- event ID
- channel
- provider result
- remote ID / counts / HTTP status
- deterministic `source_ref = attention:<event_id>:<channel>`

Replay of the same event/channel resolves to the existing acknowledgement instead of creating a second evidence record.

This proves **delivery attempt/result**, not the underlying Arkadia state and not human receipt.

## Governance

Google Tasks completion never becomes authorization.

Keep content never becomes canonical evidence.

Push delivery never becomes proof that the human saw or accepted the message.

Workspace Studio never widens Arkadia authority.

The canonical sequence remains:

`state → event → attention classification → delivery → delivery evidence → human decision`

## Activation sequence

1. Configure Google Cloud OAuth consent screen and credentials.
2. Deploy the backend with the required environment variables.
3. Sign into the Arkadia Console and open `/api/google-workspace/oauth/start`.
4. Grant Tasks + Keep + Workspace Studio trigger scopes.
5. Install/configure the Workspace Studio starter from `google_workspace/appsscript.json`.
6. Create the flow that receives Arkadia Attention Event outputs and routes them to the desired Workspace surfaces.
7. Register the Android FCM token.
8. Set the Weaver runner's delivery URL and owner UID.
9. Emit one test attention event.
10. Verify Tasks/Keep/push delivery and the corresponding `ATTENTION_DELIVERY_ACK` evidence records.

