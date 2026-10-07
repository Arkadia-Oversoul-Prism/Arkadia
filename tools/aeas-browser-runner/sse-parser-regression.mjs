/**
 * AEAS-02 client parser regression.
 *
 * Exercises the exact parser the operator surface uses
 * (web/public_prism/src/lib/sseFrames.ts) against wire bytes captured from the
 * live EventStream during the AEAS-01 Gate 3 acceptance run.
 *
 * Negative control: the captured malformed payload must yield zero frames.
 * Positive control: conformant SSE bytes must yield the expected frames, and
 * event ids must survive parsing unchanged.
 *
 * Run: node tools/aeas-browser-runner/sse-parser-regression.mjs
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { drainSse } from "../../web/public_prism/src/lib/sseFrames.ts";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");
const FIXTURES = path.join(REPO, "tests", "fixtures", "aeas");

let failures = 0;
function check(label, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) failures++;
  console.log(`  ${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) console.log(`        expected ${JSON.stringify(expected)}\n        actual   ${JSON.stringify(actual)}`);
}

// ── Negative control: the exact bytes that escaped during AEAS-01 Gate 3 ─────
const malformed = fs.readFileSync(path.join(FIXTURES, "sse-wire-captured-malformed.bin"), "utf8");
console.log("negative control — captured malformed payload");
console.log(`  bytes: ${malformed.length}`);
check("wire contains literal backslash-n framing", malformed.includes("\\n\\n"), true);
check("wire contains no real LF framing", malformed.includes("\n"), false);
check("parser yields zero frames", drainSse(malformed).frames.length, 0);

// ── Positive control: conformant framing of the same two native events ───────
const events = [
  { event_id: "AEV-19fecaf97608", event_type: "SESSION_CREATED", sequence: 1, session_id: "SES-ed919afaa211" },
  { event_id: "AEV-1559753b3eef", event_type: "SESSION_TRANSITION", sequence: 2, session_id: "SES-ed919afaa211" },
];
const conformant =
  ": connected\n\n" + events.map((e) => `event: agent\ndata: ${JSON.stringify(e)}\n\n`).join("");
console.log("\npositive control — conformant SSE framing");
check("parser yields two frames", drainSse(conformant).frames.length, 2);
const parsed = drainSse(conformant).frames.map((f) => JSON.parse(f.data));
check("event ids survive parsing", parsed.map((e) => e.event_id), events.map((e) => e.event_id));
check("event type survives parsing", parsed.map((e) => e.event_type), events.map((e) => e.event_type));
check("sequence survives parsing", parsed.map((e) => e.sequence), [1, 2]);
check("frame event name is 'agent'", drainSse(conformant).frames.map((f) => f.event), ["agent", "agent"]);

// ── Streaming split across reads must not lose or duplicate frames ───────────
console.log("\nstreaming — partial reads reassemble exactly once");
let buffer = "";
const seen = [];
for (const chunk of [conformant.slice(0, 17), conformant.slice(17, 40), conformant.slice(40)]) {
  buffer += chunk;
  const { frames, rest } = drainSse(buffer);
  buffer = rest;
  for (const f of frames) seen.push(JSON.parse(f.data).event_id);
}
check("no loss or duplication across chunk boundaries", seen, events.map((e) => e.event_id));

console.log(`\n${failures === 0 ? "ALL PASS" : failures + " FAILURE(S)"}`);
process.exit(failures === 0 ? 0 : 1);
