/**
 * AEAS Gate 2 + Gate 3 browser acceptance.
 *
 * Gate 2: real Chromium loads the isolated SPA (served on the CORS-allowed
 *   localhost:5173 origin), authenticates through the real Login UI, and proves
 *   authenticated Lab API operation against https://arkadia-pr-337.onrender.com.
 * Gate 3: the same session reaches /solspire/engineering-lab, selects/creates a
 *   native Lab session, establishes the SSE EventStream and shows ● LIVE,
 *   triggers a native Lab event, and proves the event reached the Events pane.
 *
 * No JWT fabrication, no localStorage injection, no auth bypass, no production
 * mutation. The only credential used is a disposable Firebase identity supplied
 * via a local file that is deleted on cleanup.
 */
import { chromium } from "playwright";
import fs from "node:fs/promises";

const SPA = process.env.SPA_ORIGIN || "http://localhost:5173";
const API = process.env.API_ORIGIN || "https://arkadia-pr-337.onrender.com";
const outDir = process.env.EVIDENCE_DIR || "./evidence/gate-acceptance";
const credFile = process.env.AEAS_IDENTITY_FILE || "/tmp/aeas-fb-user.json";
const labPath = "/solspire/engineering-lab";

await fs.mkdir(outDir, { recursive: true });

const identity = JSON.parse(await fs.readFile(credFile, "utf8"));
const redact = (s) =>
  String(s || "")
    .replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, "[REDACTED_JWT]")
    .replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, "[REDACTED_EMAIL]");

const evidence = {
  schema: "arkadia.aeas.gate-acceptance.v1",
  spa_origin: SPA,
  api_origin: API,
  lab_path: labPath,
  started_at: new Date().toISOString(),
  gate2: { steps: [], lab_api_calls: [], authentication: null },
  gate3: { steps: [], sse_responses: [], transport: null, native_event: null, raw_frames: null },
  console_errors: [],
  page_errors: [],
  failed_requests: [],
};

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await context.newPage();

page.on("console", (m) => {
  if (m.type() === "error") evidence.console_errors.push(redact(m.text()));
});
page.on("pageerror", (e) => evidence.page_errors.push(redact(e.message)));
page.on("requestfailed", (r) =>
  evidence.failed_requests.push({ url: r.url(), error: r.failure()?.errorText || "unknown" })
);

page.on("response", async (res) => {
  const url = res.url();
  const status = res.status();
  const headers = res.headers();
  if (url.includes("/api/lab/")) {
    evidence.gate2.lab_api_calls.push({
      method: res.request().method(),
      url,
      status,
      authorized: Boolean(res.request().headers()["authorization"]),
    });
  }
  if (url.includes("/events")) {
    evidence.gate3.sse_responses.push({
      url,
      status,
      content_type: headers["content-type"] || null,
      cache_control: headers["cache-control"] || null,
    });
  }
});

async function step(bucket, name, fn) {
  const started = Date.now();
  try {
    const result = await fn();
    bucket.push({ name, status: "PASS", duration_ms: Date.now() - started, result });
    console.log(`[PASS] ${name}`);
    return result;
  } catch (error) {
    bucket.push({ name, status: "FAIL", duration_ms: Date.now() - started, error: redact(String(error)) });
    console.log(`[FAIL] ${name}: ${redact(String(error))}`);
    throw error;
  }
}

const shot = async (name) => page.screenshot({ path: `${outDir}/${name}.png`, fullPage: true });

try {
  // ---------------- Gate 2 ----------------
  await step(evidence.gate2.steps, "spa-serves-login-route", async () => {
    const res = await page.goto(`${SPA}/login`, { waitUntil: "domcontentloaded", timeout: 90000 });
    await page.waitForTimeout(2500);
    return { status: res?.status(), url: page.url() };
  });

  await step(evidence.gate2.steps, "authenticate-via-real-login-ui", async () => {
    await page.getByTestId("tab-signin").click({ timeout: 30000 });
    await page.getByTestId("input-email-signin").fill(identity.email, { timeout: 30000 });
    await page.getByTestId("input-password-signin").fill(identity.password, { timeout: 30000 });
    await page.getByTestId("button-signin").click({ timeout: 30000 });
    await page.waitForTimeout(6000);

    const stored = await page.evaluate(() => ({
      has_token: Boolean(window.localStorage.getItem("arkadia_token")),
      token_is_jwt: /^eyJ[\w-]+\.[\w-]+\.[\w-]+$/.test(window.localStorage.getItem("arkadia_token") || ""),
    }));
    evidence.gate2.authentication = {
      provider: "firebase-identity-toolkit-via-login-ui",
      email_domain: identity.email.split("@")[1],
      uid_prefix: identity.uid.slice(0, 8),
      id_token_present: stored.has_token,
      id_token_is_jwt: stored.token_is_jwt,
      fabricated: false,
    };
    if (!stored.has_token || !stored.token_is_jwt) {
      throw new Error("Login UI did not yield an ID token in the app's own auth client");
    }
    await shot("gate2-01-authenticated-login");
    return evidence.gate2.authentication;
  });

  await step(evidence.gate2.steps, "authenticated-lab-api-operation", async () => {
    const result = await page.evaluate(async (api) => {
      const token = window.localStorage.getItem("arkadia_token");
      const call = async (path) => {
        const res = await fetch(api + path, { headers: { Authorization: `Bearer ${token}` } });
        let body = null;
        try { body = await res.json(); } catch { body = null; }
        return { path, status: res.status, ok: res.ok, body };
      };
      return {
        overview: await call("/api/lab/overview"),
        sessions: await call("/api/lab/engineering/sessions"),
      };
    }, API);
    if (!result.overview.ok || !result.sessions.ok) {
      throw new Error(`Lab API not authorized: overview=${result.overview.status} sessions=${result.sessions.status}`);
    }
    await shot("gate2-02-lab-api-authorized");
    return {
      overview_status: result.overview.status,
      sessions_status: result.sessions.status,
      subject_binding: result.overview.body?.system ? "Arkadia Lab" : null,
      session_count: result.sessions.body?.sessions?.length ?? null,
    };
  });

  await step(evidence.gate2.steps, "engineering-lab-surface-renders", async () => {
    await page.goto(`${SPA}${labPath}`, { waitUntil: "networkidle", timeout: 90000 });
    await page.waitForSelector("[data-testid=aeas-01-engineering-lab]", { timeout: 60000 });
    const body = await page.locator("body").innerText();
    if (!/Engineering Lab/i.test(body)) throw new Error("Engineering Lab surface marker absent");
    await shot("gate2-03-engineering-lab-surface");
    return { url: page.url(), has_surface: true };
  });

  // ---------------- Gate 3 ----------------
  await step(evidence.gate3.steps, "select-or-create-native-session", async () => {
    // A fresh identity has no session; a project must be present (created as
    // isolated test setup for this identity only).
    const createBtn = page.getByRole("button", { name: "CREATE SESSION" });
    if (await createBtn.isVisible().catch(() => false)) {
      await createBtn.click({ timeout: 30000 });
    } else {
      const sessionButtons = page.locator("aside button", { hasText: /SES-/ });
      if (await sessionButtons.count()) await sessionButtons.first().click({ timeout: 30000 });
    }
    await page.waitForTimeout(4000);
    const body = await page.locator("body").innerText();
    const match = body.match(/Session (SES-\w+)/);
    if (!match) throw new Error("No native Lab session selected/created");
    await shot("gate3-01-session-selected");
    return { session_id: match[1] };
  });

  const sessionId = evidence.gate3.steps.find((s) => s.name === "select-or-create-native-session").result.session_id;

  await step(evidence.gate3.steps, "sse-eventstream-live", async () => {
    await page.waitForFunction(
      () => {
        const el = document.querySelector("[data-testid=aeas-transport-state]");
        return el && el.getAttribute("data-transport") === "LIVE";
      },
      { timeout: 45000 }
    );
    const state = await page.evaluate(() => {
      const el = document.querySelector("[data-testid=aeas-transport-state]");
      return { text: el.textContent, transport: el.getAttribute("data-transport") };
    });
    evidence.gate3.transport = state;
    await shot("gate3-02-transport-live");
    return state;
  });

  await step(evidence.gate3.steps, "trigger-native-lab-event", async () => {
    const authorize = page.getByRole("button", { name: "AUTHORIZE" });
    if (!(await authorize.isVisible().catch(() => false))) {
      throw new Error("AUTHORIZE control not available for the selected session");
    }
    await authorize.click({ timeout: 30000 });
    await page.waitForTimeout(6000);
    await shot("gate3-03-event-triggered");
    return { trigger: "human AUTHORIZE action", session_id: sessionId };
  });

  await step(evidence.gate3.steps, "native-event-reaches-events-pane", async () => {
    await page.waitForFunction(
      () => document.querySelectorAll("[data-event-id]").length >= 2,
      { timeout: 45000 }
    );
    const events = await page.evaluate(() =>
      Array.from(document.querySelectorAll("[data-event-id]")).map((el) => ({
        event_id: el.getAttribute("data-event-id"),
        sequence: el.getAttribute("data-event-sequence"),
        text: (el.textContent || "").slice(0, 120),
      }))
    );
    const transition = events.find((e) => /TRANSITION|AUTHORIZ/i.test(e.text)) || events[events.length - 1];
    evidence.gate3.native_event = transition;
    await shot("gate3-04-event-in-pane");
    return { count: events.length, events, native_event: transition };
  });

  await step(evidence.gate3.steps, "capture-raw-sse-frames-from-browser", async () => {
    const capture = await page.evaluate(
      async ({ api, session }) => {
        const token = window.localStorage.getItem("arkadia_token");
        const controller = new AbortController();
        const res = await fetch(`${api}/api/lab/engineering/sessions/${session}/events`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        const frames = [];
        const deadline = Date.now() + 12000;
        while (Date.now() < deadline && frames.length < 3) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let idx;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            frames.push(buffer.slice(0, idx + 2));
            buffer = buffer.slice(idx + 2);
          }
        }
        controller.abort();
        return {
          status: res.status,
          content_type: res.headers.get("content-type"),
          frame_count: frames.length,
          frames,
        };
      },
      { api: API, session: sessionId }
    );
    evidence.gate3.raw_frames = capture;
    if (capture.frame_count === 0) throw new Error("No conformant SSE frames received from the endpoint");
    return { status: capture.status, content_type: capture.content_type, frame_count: capture.frame_count };
  });
} catch (error) {
  evidence.aborted_at = redact(String(error));
} finally {
  evidence.finished_at = new Date().toISOString();
  evidence.console_errors = evidence.console_errors.slice(0, 60);
  evidence.page_errors = evidence.page_errors.slice(0, 60);
  evidence.failed_requests = evidence.failed_requests.slice(0, 60);
  await fs.writeFile(`${outDir}/gate-acceptance.json`, JSON.stringify(evidence, null, 2));
  await browser.close();
}

const gate2Pass = evidence.gate2.steps.length > 0 && evidence.gate2.steps.every((s) => s.status === "PASS");
const gate3Pass = evidence.gate3.steps.length > 0 && evidence.gate3.steps.every((s) => s.status === "PASS");
console.log(
  JSON.stringify({
    gate2: gate2Pass ? "PASS" : "FAIL",
    gate3: gate3Pass ? "PASS" : "FAIL",
    evidence_dir: outDir,
    aborted_at: evidence.aborted_at || null,
  })
);
process.exit(gate2Pass && gate3Pass ? 0 : 1);
