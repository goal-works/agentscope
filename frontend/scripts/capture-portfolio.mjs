import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const outputDirectory = path.resolve(scriptDirectory, "../../../public/projects/agentscope");
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, colorScheme: "dark" });

await page.goto("http://127.0.0.1:3001", { waitUntil: "networkidle" });
await page.screenshot({ path: path.join(outputDirectory, "overview.png"), fullPage: true });

await page.goto("http://127.0.0.1:3001/traces", { waitUntil: "networkidle" });
await page.getByRole("link", { name: "Incident research — repeated search loop" }).click();
await page.waitForLoadState("networkidle");
await page.screenshot({ path: path.join(outputDirectory, "trace-detail.png"), fullPage: true });

await page.goto("http://127.0.0.1:3001/compare", { waitUntil: "networkidle" });
await page.screenshot({ path: path.join(outputDirectory, "comparison.png"), fullPage: true });

await browser.close();
