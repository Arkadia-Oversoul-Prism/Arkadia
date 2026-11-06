import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

/**
 * Behavioural test runner for the console.
 *
 * Separate from `vite.config.ts` on purpose: the build config carries the dev
 * proxy and manual chunking, neither of which a jsdom test needs, and keeping
 * them apart means a test-only change can never alter the production bundle.
 *
 * `environment: "jsdom"` is required — these tests mount real React components
 * and assert on rendered DOM, not on source text.
 */
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.test.{ts,tsx}"],
    // The behavioural suite asserts bounded render counts, so a runaway loop
    // must fail the test rather than hang the runner.
    testTimeout: 20000,
  },
});
