import { expect, test } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { decide, payCase, recordRunCases, startDispatch } from "./api";

// Walks the loan desk flow of the active pack end to end, and captures a
// screenshot of every main step for the documentation pages. It runs only
// when WIKI_SHOTS_DIR names an output folder.
const OUT = process.env.WIKI_SHOTS_DIR;
// The dispatch walk depends on the same agent stand-in flow that fails on
// this host on the clean tree (run.spec's dispatch test), so it stays behind
// its own gate until that environment issue is fixed.
const FULL = process.env.WIKI_FLOW_FULL === "1";

// The lane is opt-in by design: the screenshots land only when the output
// folder is named, exactly like the tour lane's CRM_TOUR gate.
// eslint-disable-next-line playwright/no-skipped-test
test.skip(!OUT, "the flow screenshots run only with WIKI_SHOTS_DIR set");

function outDir(): string {
  // The module-level skip guarantees OUT at test time.
  if (!OUT) throw new Error("WIKI_SHOTS_DIR is unset");
  return OUT;
}

async function shot(page: import("@playwright/test").Page, name: string) {
  const dir = outDir();
  mkdirSync(dir, { recursive: true });
  await page.screenshot({ path: join(dir, `${name}.png`), fullPage: true });
}

// eslint-disable-next-line playwright/no-skipped-test
test.skip(!FULL, "the sign-in capture runs with the dispatch walk");

test("the sign-in page greets the worker", async ({ browser }) => {
  const fresh = await browser.newContext();
  const page = await fresh.newPage();
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible({
    timeout: 15000,
  });
  await shot(page, "01-sign-in");
  await fresh.close();
});

test("the queue waits for the dispatch", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Cases queue" }),
  ).toBeVisible();
  await shot(page, "02-queue");
});

// The dispatch walk fails on this host on the clean tree, so it stays
// behind its own gate until that environment issue is fixed.
// eslint-disable-next-line playwright/no-skipped-test
test.skip(!FULL, "the dispatch walk runs only with WIKI_FLOW_FULL=1");

test("the dispatch works cases to decisions and a held sign-off", async ({
  page,
  request,
}) => {
  await page.goto("/");
  const panel = page.getByRole("region", { name: "Dispatch" });
  await expect(panel).toBeVisible();

  const { run_id } = await startDispatch(request, 2);
  await recordRunCases(request, run_id, ["LN-5001", "LN-5003"]);
  await expect(panel.getByText("Running", { exact: true })).toBeVisible();
  await shot(page, "03-dispatch-running");

  // The desk case approves the simple checkout at the base term.
  await decide(
    request,
    "LN-5001",
    {
      decision: "approve",
      section: "Loan rules 2 and 3",
      reason:
        "A copy of The Lighthouse Keeper is free and the membership holds two loans, so the desk issues the base term.",
    },
    14,
  );
  await payCase(request, "LN-5001");
  await expect(panel.getByText("LN-5001").getByText("Decided")).toBeVisible();

  // The renewal to 21 days sits over the limit, so the decision holds.
  await decide(
    request,
    "LN-5003",
    {
      decision: "approve",
      section: "Loan rules 2 and 4",
      reason:
        "The renewal runs 7 days past the base term, for 21 days in total, which the research tier allows.",
    },
    21,
  );
  await expect(panel.getByText("Held for sign-off")).toBeVisible();
  await shot(page, "04-run-panel");

  await page.goto("/cases/LN-5001");
  await expect(page.getByText("The Lighthouse Keeper").first()).toBeVisible();
  await shot(page, "05-case-decided");

  await page.goto("/cases/LN-5003");
  const signOff = page.getByRole("button", { name: /sign off/i });
  await expect(signOff).toBeVisible();
  await shot(page, "06-held-sign-off");
  await signOff.click();
  await expect(page.getByText("Decided").first()).toBeVisible();
  await shot(page, "07-signed-off");
});

test("the scoreboard keeps the run scores", async ({ page }) => {
  await page.goto("/scoreboard");
  await expect(
    page.getByRole("heading", { name: /Scoreboard/ }).first(),
  ).toBeVisible();
  await shot(page, "08-scoreboard");
});

test("the settings page carries the pack limit", async ({ page }) => {
  await page.goto("/settings");
  await expect(
    page.getByRole("spinbutton", { name: "Approval limit" }),
  ).toHaveValue("14");
  await shot(page, "09-settings");
});
