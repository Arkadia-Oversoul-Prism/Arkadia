#!/usr/bin/env node
/**
 * Arkadia Oracle Gateway
 * Bridges Telegram + webhooks → Oracle spawn endpoint → polls → replies.
 * Replaces OpenClaw; runs as a plain foreground Node.js process in Docker.
 */

import express from "express";
import TelegramBot from "node-telegram-bot-api";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ── Config ────────────────────────────────────────────────────────────────────
const cfg = JSON.parse(readFileSync(join(__dirname, "config.json"), "utf8"));
const ORACLE_BASE   = cfg.oracle.base_url;
const SPAWN_PATH    = cfg.oracle.spawn_endpoint;
const POLL_TEMPLATE = cfg.oracle.poll_endpoint;          // "/api/job/{job_id}"
const POLL_INTERVAL = cfg.oracle.poll_interval_ms  ?? 2000;
const POLL_TIMEOUT  = cfg.oracle.poll_timeout_ms   ?? 120_000;
const DEFAULTS      = cfg.spawn_defaults ?? {};
const PORT          = parseInt(process.env.PORT ?? cfg.server?.port ?? 3000, 10);
const BOT_TOKEN     = process.env.TELEGRAM_BOT_TOKEN ?? "";
const WEBHOOK_SECRET= process.env.WEBHOOK_SECRET   ?? "";

// ── Oracle helpers ────────────────────────────────────────────────────────────
async function spawnJob(intent, source = "webhook") {
  const res = await fetch(`${ORACLE_BASE}${SPAWN_PATH}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intent, source, ...DEFAULTS }),
  });
  if (!res.ok) throw new Error(`spawn ${res.status}: ${await res.text()}`);
  return res.json();                // { job_id, status, … }
}

async function pollJob(jobId) {
  const url = `${ORACLE_BASE}${POLL_TEMPLATE.replace("{job_id}", jobId)}`;
  const deadline = Date.now() + POLL_TIMEOUT;
  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, POLL_INTERVAL));
    const res = await fetch(url);
    if (!res.ok) continue;
    const data = await res.json();
    if (data.status === "completed" || data.status === "failed") return data;
  }
  throw new Error(`job ${jobId} timed out after ${POLL_TIMEOUT}ms`);
}

async function runIntent(intent, source = "webhook") {
  const job  = await spawnJob(intent, source);
  const done = await pollJob(job.job_id ?? job.id);
  return done?.result ?? done?.summary ?? JSON.stringify(done);
}

// ── Express server ────────────────────────────────────────────────────────────
const app = express();
app.use(express.json());

// Health check — Render / Fly.io require this
app.get("/health", (_req, res) => res.json({ status: "ok", gateway: "arkadia" }));
app.get("/",       (_req, res) => res.json({ status: "ok", gateway: "arkadia" }));

// Oracle webhook trigger
const webhookCfg = cfg.triggers?.webhook;
if (webhookCfg?.enabled) {
  const path = webhookCfg.path ?? "/webhook/oracle";
  app.post(path, async (req, res) => {
    // Optional secret check
    if (WEBHOOK_SECRET) {
      const sig = req.headers["x-webhook-secret"] ?? req.headers["authorization"];
      if (sig !== WEBHOOK_SECRET && sig !== `Bearer ${WEBHOOK_SECRET}`) {
        return res.status(401).json({ error: "unauthorized" });
      }
    }
    try {
      const intent = req.body?.intent ?? req.body?.text ?? JSON.stringify(req.body);
      const result = await runIntent(intent, "webhook");
      res.json({ ok: true, result });
    } catch (err) {
      console.error("[webhook]", err.message);
      res.status(500).json({ ok: false, error: err.message });
    }
  });
  console.log(`[gateway] Webhook listener: POST ${path}`);
}

app.listen(PORT, "0.0.0.0", () =>
  console.log(`[gateway] HTTP server listening on port ${PORT}`)
);

// ── Telegram bot ──────────────────────────────────────────────────────────────
const tgCfg = cfg.triggers?.telegram;
if (tgCfg?.enabled && BOT_TOKEN) {
  const bot = new TelegramBot(BOT_TOKEN, { polling: true });

  bot.on("message", async (msg) => {
    const chatId = msg.chat.id;
    const text   = msg.text?.trim();
    if (!text || text.startsWith("/start")) {
      return bot.sendMessage(chatId,
        "🜂 Arkadia Oracle gateway active. Send any message to invoke the Oracle.");
    }
    try {
      await bot.sendMessage(chatId, "⟳ Routing to Oracle…");
      const result = await runIntent(text, "telegram");
      await bot.sendMessage(chatId, result, { parse_mode: "Markdown" });
    } catch (err) {
      console.error("[telegram]", err.message);
      await bot.sendMessage(chatId, `⚠ Oracle error: ${err.message}`);
    }
  });

  bot.on("polling_error", (err) =>
    console.error("[telegram polling]", err.message)
  );

  console.log("[gateway] Telegram bot polling active");
} else if (tgCfg?.enabled && !BOT_TOKEN) {
  console.warn("[gateway] TELEGRAM_BOT_TOKEN not set — Telegram trigger disabled");
}

console.log(`[gateway] Oracle → ${ORACLE_BASE}`);
