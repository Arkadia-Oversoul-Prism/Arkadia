import http from "node:http";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const port = Number(process.env.PORT || 3000);
const token = process.env.BROWSER_CONTROL_TOKEN || "";
const runnerDir = path.resolve(process.env.BROWSER_RUNNER_DIR || ".");
const defaultTarget = process.env.TARGET_URL || "https://arkadia-pr-337.onrender.com/solspire/engineering-lab";
const rootEvidence = path.resolve(process.env.EVIDENCE_ROOT || "/tmp/arkadia-browser-evidence");

async function json(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, {"content-type":"application/json","cache-control":"no-store"});
  res.end(data);
}

function authorized(req) {
  if (!token) return false;
  return req.headers.authorization === `Bearer ${token}`;
}

async function body(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  if (!chunks.length) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function runProbe(env) {
  return new Promise((resolve, reject) => {
    const child = spawn("node", [path.join(runnerDir, "runner.mjs")], {env, cwd: runnerDir});
    let stdout = "", stderr = "";
    child.stdout.on("data", x => { stdout += x; });
    child.stderr.on("data", x => { stderr += x; });
    child.on("error", reject);
    child.on("close", async code => {
      let evidence = null;
      try { evidence = JSON.parse(await fs.readFile(path.join(env.EVIDENCE_DIR, "browser-evidence.json"), "utf8")); } catch {}
      resolve({exit_code: code ?? 1, stdout, stderr, evidence});
    });
  });
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/health") {
      return json(res, 200, {ok:true, service:"arkadia-aeas-browser-runner", schema:"arkadia.browser-runner.v1", target:defaultTarget});
    }
    if (!authorized(req)) return json(res, 401, {ok:false, error:"unauthorized"});
    if (req.method === "POST" && req.url === "/probe") {
      const input = await body(req);
      const id = randomUUID();
      const evidenceDir = path.join(rootEvidence, id);
      await fs.mkdir(evidenceDir, {recursive:true});
      const result = await runProbe({
        ...process.env,
        TARGET_URL: input.target_url || defaultTarget,
        EXPECTED_STATUS: input.expected_status ? String(input.expected_status) : process.env.EXPECTED_STATUS || "",
        EVIDENCE_DIR: evidenceDir,
      });
      return json(res, result.exit_code === 0 ? 200 : 502, {ok: result.exit_code === 0, run_id:id, ...result});
    }
    return json(res, 404, {ok:false, error:"not_found"});
  } catch (error) {
    return json(res, 500, {ok:false, error:String(error)});
  }
});

server.listen(port, "0.0.0.0", () => {
  console.log(`AEAS browser control listening on 0.0.0.0:${port}`);
});
