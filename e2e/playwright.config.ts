import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for the Sprint 8 smoke test. Runs against an already-running
 * stack (start it with `docker compose up`). Override the target with BASE_URL.
 */
export default defineConfig({
  testDir: ".",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
