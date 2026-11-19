// Captures the live desk on the real dev stack: the sign-in page, the
// queue, one case, the scoreboard, and the settings. Run from crm/ with:
//   BASE_URL=http://172.17.0.x:5173 SHOT_DIR=docs/screenshots \
//   WORKER=rosa.meridian@northgate.example node e2e/capture_real.mjs
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const BASE = process.env.BASE_URL ?? "http://localhost:5173";
const OUT = process.env.SHOT_DIR ?? "docs/screenshots";
const WORKER = process.env.WORKER ?? "rosa.meridian@northgate.example";
const PASSWORD = process.env.PASSWORD ?? "crm-dev";

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto(BASE);
await page.waitForTimeout(1500);
await page.screenshot({ path: join(OUT, "r1-sign-in.png"), fullPage: true });

await page.getByLabel("Email").fill(WORKER);
await page.getByLabel("Password").fill(PASSWORD);
await page.getByRole("button", { name: "Sign in" }).click();
await page.waitForTimeout(1500);
await page.screenshot({ path: join(OUT, "r2-queue.png"), fullPage: true });

const link = page.getByRole("link", { name: /LN-500\d/ }).first();
if (await link.isVisible()) {
  await link.click();
  await page.waitForTimeout(1200);
  await page.screenshot({ path: join(OUT, "r3-case.png"), fullPage: true });
}

await page.goto(`${BASE}/scoreboard`);
await page.waitForTimeout(1200);
await page.screenshot({ path: join(OUT, "r4-scoreboard.png"), fullPage: true });

await page.goto(`${BASE}/settings`);
await page.waitForTimeout(1200);
await page.screenshot({ path: join(OUT, "r5-settings.png"), fullPage: true });

await browser.close();
console.log(`captured the live desk into ${OUT}`);
