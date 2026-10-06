import { chromium } from "playwright";
import fs from "node:fs/promises";

const target = process.env.TARGET_URL || "https://arkadia-pr-337.onrender.com/solspire/engineering-lab";
const outDir = process.env.EVIDENCE_DIR || "./evidence";
const email = process.env.BROWSER_EMAIL || "";
const password = process.env.BROWSER_PASSWORD || "";
const authenticated = Boolean(email && password);

await fs.mkdir(outDir, { recursive: true });

const evidence = {
  schema: "arkadia.browser-runner.v1",
  target,
  authenticated,
  started_at: new Date().toISOString(),
  steps: [],
  console_errors: [],
  page_errors: [],
  failed_requests: [],
};

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

page.on("console", m => {
  if (m.type() === "error") evidence.console_errors.push(m.text());
});
page.on("pageerror", e => evidence.page_errors.push(e.message));
page.on("requestfailed", r => {
  evidence.failed_requests.push({ url: r.url(), error: r.failure()?.errorText || "unknown" });
});

async function step(name, fn) {
  const started = Date.now();
  try {
    const result = await fn();
    evidence.steps.push({ name, status: "PASS", duration_ms: Date.now() - started, result });
    return result;
  } catch (error) {
    evidence.steps.push({ name, status: "FAIL", duration_ms: Date.now() - started, error: String(error) });
    throw error;
  }
}

try {
  await step("reach-render-pr", async () => {
    const response = await page.goto(target, { waitUntil: "domcontentloaded", timeout: 90000 });
    await page.screenshot({ path: `${outDir}/render-pr.png`, fullPage: true });
    return { status: response?.status() ?? null, final_url: page.url() };
  });

  if (authenticated) {
    await step("authenticate-via-real-login", async () => {
      await page.goto(new URL("/login", target).toString(), { waitUntil: "networkidle", timeout: 90000 });
      await page.getByTestId("tab-signin").click();
      await page.getByTestId("input-email-signin").fill(email);
      await page.getByTestId("input-password-signin").fill(password);
      await page.getByTestId("button-signin").click();
      await page.waitForTimeout(4000);
      return { final_url: page.url(), title: await page.title() };
    });

    await step("engineering-lab-surface", async () => {
      await page.goto(target, { waitUntil: "networkidle", timeout: 90000 });
      await page.waitForTimeout(2500);
      const body = await page.locator("body").innerText();
      await page.screenshot({ path: `${outDir}/engineering-lab-authenticated.png`, fullPage: true });
      if (!body.includes("Engineering Lab")) {
        throw new Error("Engineering Lab marker not found after authenticated navigation");
      }
      return {
        final_url: page.url(),
        has_engineering_lab_marker: true,
        body_excerpt: body.slice(0, 1000),
      };
    });
  }
} finally {
  evidence.finished_at = new Date().toISOString();
  evidence.console_errors = evidence.console_errors.slice(0, 100);
  evidence.page_errors = evidence.page_errors.slice(0, 100);
  evidence.failed_requests = evidence.failed_requests.slice(0, 100);
  await fs.writeFile(`${outDir}/browser-evidence.json`, JSON.stringify(evidence, null, 2));
  await browser.close();
}

const failed = evidence.steps.some(s => s.status === "FAIL") ||
  evidence.console_errors.length > 0 ||
  evidence.page_errors.length > 0 ||
  evidence.failed_requests.length > 0;

if (failed) process.exit(1);
console.log(JSON.stringify({ status: "PASS", target, authenticated, evidence_dir: outDir }));
