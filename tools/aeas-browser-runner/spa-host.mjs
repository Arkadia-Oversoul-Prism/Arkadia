/**
 * Minimal SPA host for AEAS acceptance.
 *
 * Serves web/public_prism/dist with history-API fallback to index.html so the
 * real /login and /solspire/engineering-lab routes resolve. Port defaults to
 * 5173, which api/main.py's development CORS allowlist admits.
 */
import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";

const PORT = Number(process.env.PORT || 5173);
const ROOT = path.resolve(process.env.DIST_DIR || "dist");

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".map": "application/json; charset=utf-8",
};

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  let file = path.join(ROOT, decodeURIComponent(url.pathname));

  if (!file.startsWith(ROOT)) {
    res.writeHead(403).end("forbidden");
    return;
  }

  try {
    const stat = await fs.stat(file);
    if (stat.isDirectory()) file = path.join(file, "index.html");
  } catch {
    file = path.join(ROOT, "index.html"); // history-API fallback
  }

  try {
    const data = await fs.readFile(file);
    res.writeHead(200, {
      "content-type": TYPES[path.extname(file)] || "application/octet-stream",
      "cache-control": "no-store",
    });
    res.end(data);
  } catch (error) {
    res.writeHead(404).end(String(error));
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`AEAS SPA host on http://localhost:${PORT} (root ${ROOT})`);
});
