# 10 — OpenClaw Blueprint

OpenClaw is a **real, separately-deployed subsystem** — not absent from the project as might be assumed from `replit.md` (which does not mention it at all; this is a documentation gap).

## Purpose
The WhatsApp gateway for Arkadia. Per `docs/DOC1_MASTER_WEIGHTS.md`, it is bound to a specific WhatsApp number (`+2348144942818`) and per `CLOUD_ARCHITECTURE.md` is described as "Gateway intelligence," deployed independently via Railway/Ubuntu PRoot (per that doc) with its own `render.yaml`/`fly.toml` also present (indicating the deploy target may have moved or is multi-target — **not fully reconciled this session, flagged for owner clarification**).

## Directory Contents (`openclaw/`)
| File | Purpose |
|---|---|
| `gateway.js` | Main Node.js process — routes WhatsApp messages through to the Oracle backend |
| `config.json` | Gateway configuration |
| `package.json` | Dependencies: `express` (^4.19.2), `node-telegram-bot-api` (^0.66.0) — **note**: a Telegram library dependency inside the WhatsApp gateway's package.json is unexpected and should be confirmed as intentional (possibly shared/copy-pasted from the `bot/` package, or genuinely used for cross-posting) |
| `Dockerfile` | Node 22-slim container |
| `render.yaml` | Deploys as `arkadia-oracle-gateway` on Render, port 3000, with Telegram-token-named env vars (per prior audit) — again suggesting Telegram/WhatsApp code may be intertwined |
| `fly.toml` | Fly.io deploy config — a **second** cloud target for the same service |
| `railway.json` | Railway deploy config — a **third** cloud target |

## Identity / Memory / Tools
- No dedicated "identity file" or "memory file" distinct from the main Oracle backend was found inside `openclaw/` — it appears to be a thin message-routing gateway rather than an independent reasoning agent, forwarding to the same backend endpoints (`/api/commune/resonance` style) used by Discord/Telegram, based on the pattern established by those two bots. **Not independently confirmed this session which endpoint `gateway.js` calls** — flagged for follow-up (would require reading `gateway.js` directly, not yet done).

## Automation / Messaging / Integrations
- Messaging: WhatsApp (primary, by name), possibly Telegram (per dependency + render.yaml naming — unconfirmed).
- No confirmed CI/CD automation specific to this service beyond its three deploy-config files.

## Security
- Not directly audited for secrets in this pass beyond the general secret scan (see Security Audit) — `openclaw/config.json` should be manually checked for embedded tokens before treating it as safe to commit/share (JSON config files are historically where WhatsApp/Telegram bot tokens get accidentally hardcoded).

## Recommendation
This is the least-documented live subsystem in the repo. Recommend a dedicated follow-up pass reading `openclaw/gateway.js` and `openclaw/config.json` directly, and reconciling which of the three deploy targets (Render / Fly.io / Railway) is actually the one running in production — right now the repo implies all three are configured simultaneously, which is either intentional redundancy or configuration drift.
