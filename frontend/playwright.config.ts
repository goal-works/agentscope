import { defineConfig, devices } from "@playwright/test";

const runId = `${process.pid}-${Date.now()}`;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3001",
    colorScheme: "dark",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command:
        "uv run uvicorn agentscope_server.main:app --host 127.0.0.1 --port 8001 --app-dir backend",
      cwd: "..",
      url: "http://127.0.0.1:8001/api/health",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        AGENTSCOPE_DATABASE_URL: `sqlite:////tmp/agentscope-playwright-${runId}.db`,
        UV_CACHE_DIR: "/tmp/agentscope-uv-cache",
      },
    },
    {
      command: "npm run start",
      url: "http://127.0.0.1:3001",
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
