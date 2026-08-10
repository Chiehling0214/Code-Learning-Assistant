import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for the Sprint 8 smoke test. Runs against an already-running
 * stack (start it with `docker compose up`). Override the target with BASE_URL.
 */
export default defineConfig({
  testDir: ".",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  webServer: {
    command: "npm --prefix ../frontend run dev -- --host 127.0.0.1 --port 4174",
    url: "http://127.0.0.1:4174",
    reuseExistingServer: true,
    env: {
      ...process.env,
      VITE_API_BASE_URL: "http://localhost:8000/api/v1",
      VITE_FIREBASE_API_KEY: "",
      VITE_FIREBASE_AUTH_DOMAIN: "",
      VITE_FIREBASE_PROJECT_ID: "",
      VITE_FIREBASE_APP_ID: "",
    },
  },
  use: {
    baseURL: process.env.BASE_URL ?? "http://127.0.0.1:4174",
    trace: "on-first-retry",
    viewport: { width: 1440, height: 900 },
    colorScheme: "light",
    locale: "en-US",
  },
  snapshotPathTemplate: "{testDir}/__screenshots__/{arg}{ext}",
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
