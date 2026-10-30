import { expect, test } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";
import { AGENT_KEY_HEADERS } from "./servers";
import {
  decide,
  finishRun,
  recordStep,
  startCase,
  startEvaluation,
  stopTheWork,
} from "./api";

// The visual tour: one full-page screenshot per product flow, written to
// e2e/screenshots/ for the repository wiki. It runs only when CRM_TOUR=1, so
// the default suite stays as it is:
//   CRM_TOUR=1 npx playwright test tour --headed
// Every shot needs no model key. The emulator proves the wiring; agent
// behavior stays with the hermetic tests.

const TOUR = process.env.CRM_TOUR === "1";
// The tour is opt-in by design: it works cases the other specs also
// work, so it runs only when CRM_TOUR=1 asks for the screenshots. The
// playwright plugin notes the skip as a warning; the gate fails on errors
// only.
test.skip(!TOUR, "the visual tour runs when CRM_TOUR=1");

// Reads the queue with the agent's key, so the tour never depends on a
// worker's sign-in, and returns the waiting cases in queue order.
async function waitingCases(request: APIRequestContext) {
  const response = await request.get("/api/cases", {
    headers: AGENT_KEY_HEADERS,
  });
  const body: unknown = await response.json();
  const cases = (
    Array.isArray(body) ? body : ((body as { cases?: unknown[] }).cases ?? [])
  ) as { case_id: string; status: string }[];
  expect(cases.length).toBeGreaterThan(0);
  return cases.filter((c) => c.status === "waiting");
}

async function shot(page: import("@playwright/test").Page, name: string) {
  await page.screenshot({
    path: `e2e/screenshots/${name}.png`,
    fullPage: true,
  });
}

test("the queue with its dispatch panel", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await shot(page, "01-queue");
});

test("a case held for the worker's sign-off", async ({ page, request }) => {
  const [first] = await waitingCases(request);
  const caseId = first.case_id;
  await startCase(request, caseId, "tour-1");
  await recordStep(request, caseId, "tool_call", "get_case for the tour");
  await recordStep(request, caseId, "tool_result", "the case, read");
  await decide(request, caseId, {
    decision: "approve",
    award: 3750.0,
    section: "10. How we work out your payment",
    reason:
      "The cancellation is covered; the hotel was prepaid, non-refundable.",
  });
  await page.goto(`/cases/${caseId}`);
  await expect(page.getByText(/sign[- ]off/i).first()).toBeVisible();
  await shot(page, "02-case-held-for-sign-off");
});

test("a case declined by the agent", async ({ page, request }) => {
  const waiting = await waitingCases(request);
  const caseId = waiting[waiting.length - 1].case_id;
  await startCase(request, caseId, "tour-2");
  await decide(request, caseId, {
    decision: "decline",
    award: 0,
    section: "9. General exclusions",
    reason: "The illness was pre-existing, inside the look-back window.",
  });
  await page.goto(`/cases/${caseId}`);
  await expect(page.getByText(/declined/i).first()).toBeVisible();
  await shot(page, "03-case-declined");
});

test("the configuration versions", async ({ page }) => {
  await page.goto("/configuration");
  await expect(
    page.getByRole("heading", { name: /configuration/i }),
  ).toBeVisible();
  await shot(page, "04-configuration");
});

test("the scoreboard with a finished evaluation", async ({ page, request }) => {
  await stopTheWork(request);
  const { run_id } = await startEvaluation(request, "held_out", true, 3);
  await finishRun(request, run_id);
  await page.goto("/scoreboard");
  await expect(
    page.getByRole("heading", { name: /scoreboard/i }),
  ).toBeVisible();
  await shot(page, "05-scoreboard");
});

test("the settings a senior worker can change", async ({ page }) => {
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible();
  await shot(page, "06-settings");
});

test("the improvement rounds page", async ({ page }) => {
  await page.goto("/improvement");
  await expect(
    page.getByRole("heading", { name: /improvement/i }),
  ).toBeVisible();
  await shot(page, "07-improvement");
});

test("the copilot sidebar beside the queue", async ({ page }) => {
  await page.goto("/");
  const opener = page.getByRole("button", { name: /copilot/i });
  if (await opener.count()) await opener.first().click();
  await expect(page.getByText(/copilot/i).first()).toBeVisible();
  await shot(page, "08-copilot-sidebar");
});
