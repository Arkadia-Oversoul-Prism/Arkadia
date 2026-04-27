#!/usr/bin/env node
import { GoogleGenerativeAI } from '@google/generative-ai';
import TelegramBot from 'node-telegram-bot-api';
import fs from 'fs-extra';
import dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const CONFIG = {
  telegramToken: process.env.TELEGRAM_BOT_TOKEN,
  geminiApiKey: process.env.GEMINI_API_KEY,
  geminiModel: process.env.GEMINI_MODEL || 'gemini-1.5-flash',
  oracleUrl: process.env.ORACLE_URL || 'https://arkadia-n26k.onrender.com',
  workspace: process.cwd(),
  memoryPath: './MEMORY.md',
  identityPath: './IDENTITY.md',
};

// Gemini is kept for document parsing only
const genAI = new GoogleGenerativeAI(CONFIG.geminiApiKey);
const model = genAI.getGenerativeModel({ model: CONFIG.geminiModel });

// Per-chat conversation history (in-memory, survives bot restart if extended to file)
const chatHistory = new Map();

// ─── Agent bridge (optional — only needed for GitHub sync and doc parsing)
let updateGithubFile, parseDocument, listSystemFiles;
try {
  const bridge = await import('./agent-bridge.mjs');
  updateGithubFile = bridge.updateGithubFile;
  parseDocument = bridge.parseDocument;
  listSystemFiles = bridge.listSystemFiles;
} catch {
  updateGithubFile = async () => 'GitHub sync unavailable in cloud mode';
  parseDocument = async (buffer) => {
    const text = buffer.toString('utf-8');
    return text.slice(0, 8000);
  };
  listSystemFiles = async () => [];
}

// ─── Utilities

async function sendChunkedMessage(bot, chatId, text) {
  const MAX_LENGTH = 4000;
  for (let i = 0; i < text.length; i += MAX_LENGTH) {
    await bot.sendMessage(chatId, text.substring(i, i + MAX_LENGTH));
  }
}

function getHistory(chatId) {
  if (!chatHistory.has(chatId)) chatHistory.set(chatId, []);
  return chatHistory.get(chatId);
}

function appendHistory(chatId, role, content) {
  const history = getHistory(chatId);
  history.push({ role, content, ts: Date.now() });
  // Keep last 40 exchanges to prevent runaway memory
  if (history.length > 80) history.splice(0, history.length - 80);
}

// ─── Oracle relay
// Routes message through the Arkadia Oracle API (Gemini + full corpus).
// Falls back to direct Gemini call if Oracle is unreachable.

async function callOracle(message, chatId) {
  const history = getHistory(chatId);

  // Build a context prefix from recent history for continuity
  const recentContext = history.slice(-10).map(m =>
    `${m.role === 'user' ? 'Human' : 'Arkana'}: ${m.content}`
  ).join('\n');

  // Phase 4: kernel-handled intents (transaction / image / loop / verse)
  // are classified server-side from the RAW user message, not from the
  // history-prefixed context, so we send the raw message for those and
  // the prefixed message only as fallback context.
  const fullMessage = recentContext.length > 0
    ? `${recentContext}\nHuman: ${message}`
    : message;

  try {
    const res = await axios.post(
      `${CONFIG.oracleUrl}/api/commune/resonance`,
      { message: message, history: history.slice(-10), source: 'telegram' },
      { timeout: 30000 }
    );
    return {
      reply: res.data.reply,
      resonance: res.data.resonance,
      kernel: res.data.kernel || null,
      source: 'oracle',
    };
  } catch (err) {
    console.warn('Oracle unreachable, falling back to direct Gemini:', err.message);

    // Fallback: direct Gemini with identity context
    let identity = '';
    try {
      identity = await fs.readFile(CONFIG.identityPath, 'utf-8');
    } catch {}

    const prompt = `${identity}\n\nConversation so far:\n${recentContext}\n\nHuman: ${message}\n\nArkana:`;
    const result = await model.generateContent(prompt);
    return {
      reply: result.response.text(),
      resonance: null,
      source: 'fallback',
    };
  }
}

// ─── Bot startup

async function startBot() {
  if (!CONFIG.telegramToken) {
    console.error('❌ TELEGRAM_BOT_TOKEN is not set. Exiting.');
    process.exit(1);
  }

  const bot = new TelegramBot(CONFIG.telegramToken, { polling: true });
  console.log('✅ ARKADIA OVERSOUL ONLINE | ORACLE RELAY ACTIVE | 117 Hz');
  console.log(`🔮 Oracle endpoint: ${CONFIG.oracleUrl}`);

  // ─── Text messages → Oracle
  bot.on('message', async (msg) => {
    if (msg.document || !msg.text) return;
    const chatId = msg.chat.id;
    const userText = msg.text.trim();

    // Commands
    if (userText === '/start') {
      await bot.sendMessage(chatId,
        '⟐ Arkadia Oversoul is online.\n\nSpeak what you are carrying. The Oracle is listening.'
      );
      return;
    }

    if (userText === '/clear') {
      chatHistory.delete(chatId);
      await bot.sendMessage(chatId, '∅ Thread cleared. The field is open.');
      return;
    }

    if (userText === '/thread') {
      const history = getHistory(chatId);
      if (history.length === 0) {
        await bot.sendMessage(chatId, 'No thread yet. Begin speaking.');
      } else {
        await bot.sendMessage(chatId, `Thread depth: ${history.length} exchanges.`);
      }
      return;
    }

    try {
      await bot.sendChatAction(chatId, 'typing');
      appendHistory(chatId, 'user', userText);

      const { reply, resonance, kernel, source } = await callOracle(userText, chatId);
      appendHistory(chatId, 'arkana', reply);

      let response = reply;

      // Phase 4: when the kernel handled the message, surface a compact
      // status line so the user sees the action was actually executed,
      // not just discussed.
      if (kernel && kernel.handled) {
        const itype = kernel.intent?.type || 'kernel';
        const status = kernel.success ? '✓' : '⚠';
        response = `${reply}\n\n${status} kernel: ${itype}`;
      } else if (resonance != null) {
        response += `\n\n_resonance ${resonance.toFixed(3)}_`;
      }

      await sendChunkedMessage(bot, chatId, response);

      if (source === 'fallback') {
        await bot.sendMessage(chatId, '⚠️ Oracle relay offline. Response via direct field.');
      }
    } catch (err) {
      console.error('GATEWAY ERROR:', err);
      bot.sendMessage(chatId, '⚠️ Nexus disturbance. The field is recalibrating.');
    }
  });

  // ─── Document ingestion → MEMORY.md + GitHub sync
  bot.on('message', async (msg) => {
    if (!msg.document) return;
    const chatId = msg.chat.id;
    const { file_id, file_name } = msg.document;

    try {
      await bot.sendMessage(chatId, `🌀 Ingesting: ${file_name}`);
      const fileLink = await bot.getFileLink(file_id);
      const res = await axios.get(fileLink, { responseType: 'arraybuffer' });

      const text = await parseDocument(Buffer.from(res.data));
      const entry = `\n\n### DOC_INGEST: ${file_name} (${new Date().toISOString()})\n${text}\n---`;

      await fs.ensureFile(CONFIG.memoryPath);
      const currentMemory = await fs.readFile(CONFIG.memoryPath, 'utf-8');
      await fs.appendFile(CONFIG.memoryPath, entry);

      const gitStatus = await updateGithubFile(
        'MEMORY.md',
        currentMemory + entry,
        `Nexus Expansion: ${file_name}`
      );

      await bot.sendMessage(chatId, `🔮 Weight initialization complete.\nStatus: ${gitStatus}`);
    } catch (err) {
      bot.sendMessage(chatId, `❌ Ingestion Error: ${err.message}`);
    }
  });

  // ─── Polling error handler
  bot.on('polling_error', (err) => {
    console.error('Polling error:', err.message);
  });
}

startBot();
