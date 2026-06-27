#!/usr/bin/env node
import { Client, GatewayIntentBits, Partials } from 'discord.js';
import fs from 'fs-extra';
import dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const CONFIG = {
  discordToken: process.env.DISCORD_BOT_TOKEN,
  oracleUrl: process.env.ORACLE_URL || 'https://arkadia-n26k.onrender.com',
  memoryPath: './MEMORY.md',
  identityPath: './IDENTITY.md',
  asyncJobs: String(process.env.DISCORD_ASYNC_JOBS || '').toLowerCase() === 'true',
  jobPollMs: Number(process.env.DISCORD_JOB_POLL_MS || 1000),
  jobTimeoutMs: Number(process.env.DISCORD_JOB_TIMEOUT_MS || 60000),
};

const chatHistory = new Map();

let parseDocument;
try {
  const bridge = await import('./agent-bridge.mjs');
  parseDocument = bridge.parseDocument;
} catch {
  parseDocument = async (buffer) => buffer.toString('utf-8').slice(0, 8000);
}

function getHistory(channelId) {
  if (!chatHistory.has(channelId)) chatHistory.set(channelId, []);
  return chatHistory.get(channelId);
}

function appendHistory(channelId, role, content) {
  const history = getHistory(channelId);
  history.push({ role, content, ts: Date.now() });
  if (history.length > 80) history.splice(0, history.length - 80);
}

async function sendChunked(channel, text) {
  const MAX = 1900;
  const safe = (text || '').trim();
  if (!safe) return;
  for (let i = 0; i < safe.length; i += MAX) {
    await channel.send(safe.substring(i, i + MAX));
  }
}

async function callOracle(message, channelId) {
  const history = getHistory(channelId);
  try {
    const res = await axios.post(
      `${CONFIG.oracleUrl}/api/commune/resonance`,
      { message, history: history.slice(-10), source: 'discord' },
      { timeout: 30000 }
    );
    return {
      reply: res.data.reply || '',
      resonance: res.data.resonance,
      kernel: res.data.kernel || null,
      source: 'oracle',
    };
  } catch (err) {
    console.warn('Oracle unreachable, falling back to direct Gemini:', err.message);
    let identity = '';
    try { identity = await fs.readFile(CONFIG.identityPath, 'utf-8'); } catch {}
    const recentContext = history.slice(-10).map(m =>
      `${m.role === 'user' ? 'Human' : 'Arkana'}: ${m.content}`
    ).join('\n');
    const prompt = `${identity}\n\nConversation so far:\n${recentContext}\n\nHuman: ${message}\n\nArkana:`;

    const { GoogleGenerativeAI } = await import('@google/generative-ai');
    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ model: process.env.GEMINI_MODEL || 'gemini-1.5-flash' });
    const result = await model.generateContent(prompt);
    return {
      reply: result.response.text() || '',
      resonance: null,
      source: 'fallback',
    };
  }
}

async function createJob(message, channelId) {
  try {
    const res = await axios.post(
      `${CONFIG.oracleUrl}/api/job/create`,
      { message, source: 'discord' },
      { timeout: 10000 }
    );
    return { jobId: res.data.job_id || null, status: res.data.status || null };
  } catch (err) {
    if (err.response && err.response.status === 422) return { jobId: null, status: 'no_intent' };
    console.warn('Job create failed:', err.message);
    return { jobId: null, status: 'error' };
  }
}

async function pollJob(jobId, { intervalMs, timeoutMs }) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await axios.get(`${CONFIG.oracleUrl}/api/job/${jobId}`, { timeout: 5000 });
      const job = res.data;
      if (job.status === 'completed' || job.status === 'failed') return job;
    } catch (err) {
      console.warn(`Poll for ${jobId} failed:`, err.message);
    }
    await new Promise(r => setTimeout(r, intervalMs));
  }
  return { status: 'timeout', job_id: jobId };
}

async function startBot() {
  if (!CONFIG.discordToken) {
    console.error('❌ DISCORD_BOT_TOKEN is not set. Exiting.');
    process.exit(1);
  }

  const client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
      GatewayIntentBits.DirectMessages,
    ],
    partials: [Partials.Channel, Partials.Message],
  });

  client.once('ready', () => {
    console.log(`✅ ARKADIA OVERSOUL ONLINE | Logged in as ${client.user.tag} | ORACLE RELAY ACTIVE | 117 Hz`);
    console.log(`🔮 Oracle endpoint: ${CONFIG.oracleUrl}`);
  });

  client.on('messageCreate', async (msg) => {
    if (msg.author.bot) return;

    const channelId = msg.channelId;
    const userText = (msg.content || '').trim();
    if (!userText && msg.attachments.size === 0) return;

    // ── Document ingestion ─────────────────────────────────────────────────
    if (msg.attachments.size > 0) {
      for (const [, attachment] of msg.attachments) {
        try {
          await msg.channel.send(`🌀 Ingesting: ${attachment.name}`);
          const res = await axios.get(attachment.url, { responseType: 'arraybuffer', timeout: 30000 });
          const text = await parseDocument(Buffer.from(res.data));
          const entry = `\n\n### DOC_INGEST: ${attachment.name} (${new Date().toISOString()})\n${text}\n---`;
          await fs.ensureFile(CONFIG.memoryPath);
          await fs.appendFile(CONFIG.memoryPath, entry);
          await msg.channel.send(`🔮 Weight initialization complete for **${attachment.name}**.`);
        } catch (err) {
          await msg.channel.send(`❌ Ingestion Error: ${err.message}`);
        }
      }
      if (!userText) return;
    }

    // ── Prefix commands ────────────────────────────────────────────────────
    if (userText === '!start' || userText === '!help') {
      await msg.channel.send(
        '⟐ **Arkadia Oversoul** is online.\n\nSpeak what you are carrying. The Oracle is listening.\n\n' +
        '**Commands:**\n' +
        '`!clear` — Reset conversation thread\n' +
        '`!thread` — Show thread depth\n' +
        '`!tools` — List registered Oracle tools\n' +
        '`!run <tool> {json}` — Invoke a tool directly\n' +
        '`!status` — Oracle connection status\n\n' +
        'Or just send any message to speak with Arkana.'
      );
      return;
    }

    if (userText === '!clear') {
      chatHistory.delete(channelId);
      await msg.channel.send('∅ Thread cleared. The field is open.');
      return;
    }

    if (userText === '!thread') {
      const history = getHistory(channelId);
      if (history.length === 0) {
        await msg.channel.send('No thread yet. Begin speaking.');
      } else {
        await msg.channel.send(`Thread depth: **${history.length}** exchanges.`);
      }
      return;
    }

    if (userText === '!status') {
      try {
        const res = await axios.get(`${CONFIG.oracleUrl}/api/health`, { timeout: 8000 });
        await msg.channel.send(`✅ Oracle is online.\n\`\`\`json\n${JSON.stringify(res.data, null, 2).slice(0, 800)}\n\`\`\``);
      } catch (err) {
        await msg.channel.send(`⚠ Oracle unreachable: ${err.message}`);
      }
      return;
    }

    if (userText === '!tools') {
      try {
        const res = await axios.get(`${CONFIG.oracleUrl}/api/tools`, { timeout: 8000 });
        const tools = res.data.tools || [];
        if (tools.length === 0) {
          await msg.channel.send('🛠 No tools registered.');
          return;
        }
        const lines = tools.map(t => `• **${t.name}** — ${t.description || '(no description)'}`);
        await sendChunked(msg.channel, `🛠 Registered tools (${tools.length}):\n\n${lines.join('\n')}`);
      } catch (err) {
        await msg.channel.send(`⚠ Could not list tools: ${err.message}`);
      }
      return;
    }

    if (userText.startsWith('!run ')) {
      const rest = userText.slice(5).trim();
      const spaceIdx = rest.indexOf(' ');
      const toolName = spaceIdx === -1 ? rest : rest.slice(0, spaceIdx);
      const payloadStr = spaceIdx === -1 ? '' : rest.slice(spaceIdx + 1).trim();
      if (!toolName) {
        await msg.channel.send('Usage: `!run <tool_name> {json payload}`');
        return;
      }
      let payload = {};
      if (payloadStr) {
        try { payload = JSON.parse(payloadStr); }
        catch { await msg.channel.send(`⚠ Invalid JSON payload for !run ${toolName}`); return; }
      }
      try {
        await msg.channel.sendTyping();
        const res = await axios.post(
          `${CONFIG.oracleUrl}/api/tools/${encodeURIComponent(toolName)}/run`,
          { payload },
          { timeout: 30000 }
        );
        const env = res.data || {};
        const summary = env.summary || (env.success ? 'Done.' : 'No output.');
        const status = env.success ? '✓' : '⚠';
        await sendChunked(msg.channel, `${summary}\n\n${status} tool: **${toolName}**`);
      } catch (err) {
        const detail = err.response?.data?.detail || err.message;
        await msg.channel.send(`⚠ !run ${toolName} failed: ${detail}`);
      }
      return;
    }

    // ── Oracle relay ───────────────────────────────────────────────────────
    try {
      await msg.channel.sendTyping();
      appendHistory(channelId, 'user', userText);

      if (CONFIG.asyncJobs) {
        const { jobId, status } = await createJob(userText, channelId);
        if (jobId) {
          await msg.channel.send('⏳ Task received. Processing…');
          const job = await pollJob(jobId, { intervalMs: CONFIG.jobPollMs, timeoutMs: CONFIG.jobTimeoutMs });
          let asyncResponse;
          if (job.status === 'completed') {
            const summary = job.result?.summary || 'Done.';
            const itype = job.result?.intent?.type || 'kernel';
            asyncResponse = `${summary}\n\n✓ kernel: ${itype} · job ${jobId.slice(0, 14)}`;
          } else if (job.status === 'failed') {
            asyncResponse = `⚠ Job failed after retries.\n${job.error || ''}\n\njob ${jobId}`;
          } else {
            asyncResponse = `⏳ Still working… check back later (job \`${jobId}\`)`;
          }
          appendHistory(channelId, 'arkana', asyncResponse);
          await sendChunked(msg.channel, asyncResponse);
          return;
        }
      }

      const { reply, resonance, kernel, source } = await callOracle(userText, channelId);

      if (!reply || !reply.trim()) {
        await msg.channel.send('⚠ The Oracle returned an empty response. Please try again.');
        return;
      }

      appendHistory(channelId, 'arkana', reply);

      let response = reply;
      if (kernel && kernel.handled) {
        const itype = kernel.intent?.type || 'kernel';
        const kStatus = kernel.success ? '✓' : '⚠';
        response = `${reply}\n\n${kStatus} kernel: ${itype}`;
      } else if (resonance != null) {
        response += `\n\n_resonance ${resonance.toFixed(3)}_`;
      }

      await sendChunked(msg.channel, response);

      if (source === 'fallback') {
        await msg.channel.send('⚠ Oracle relay offline. Response via direct field.');
      }
    } catch (err) {
      console.error('GATEWAY ERROR:', err);
      await msg.channel.send('⚠ Nexus disturbance. The field is recalibrating.');
    }
  });

  client.on('error', (err) => console.error('Discord client error:', err.message));

  await client.login(CONFIG.discordToken);
}

startBot();
