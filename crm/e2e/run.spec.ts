import { expect, test } from "@playwright/test";
import {
  failCase,
  finishRun,
  payCase,
  decide,
  recordModelCall,
  recordRunCases,
  recordStep,
  recordWorkTime,
  startCase,
  startDispatch,
  stopTheWork,
} from "./api";

// These tests start a dispatch as Dana Whitfield, which the app creates, then
// stand in for the agent and its case agents by calling the API through the
// dashboard's proxy, and watch the pages update without a reload. They use
// cases no other test touches.

test.afterEach(async ({ request }) => {
  await stopTheWork(request);
});

test("the dispatch panel follows a dispatch as it works", async ({
  page,
  request,
}) => {
  await page.goto("/");
  const panel = page.getByRole("region", { name: "Dispatch" });
  await expect(panel).toBeVisible();

  const { run_id } = await startDispatch(request, 2);
  await recordRunCases(request, run_id, ["CLM-1013", "CLM-1014"]);
  const rows = panel.getByRole("row");
  await expect(panel.getByText("Running", { exact: true })).toBeVisible();
  await expect(panel.getByText(/with 2 case agents at once/)).toBeVisible();
  await expect(rows).toHaveText([
    /^Case/,
    /^CLM-1013.*Waiting/,
    /^CLM-1014.*Waiting/,
  ]);

  for (const [caseId, thread] of [
    ["CLM-1013", "e2e-5"],
    ["CLM-1014", "e2e-6"],
  ]) {
    await startCase(request, caseId, thread);
    await recordModelCall(request, caseId, run_id, 0.005);
  }
  await expect(rows).toHaveText([
    /^Case/,
    /^CLM-1013.*In progress/,
    /^CLM-1014.*In progress/,
  ]);

  await decide(request, "CLM-1013", {
    decision: "approve",
    award: 300,
    section: "Section 3, Trip Delay",
    reason: "The delay was covered.",
  });
  await payCase(request, "CLM-1013", 300);
  await decide(request, "CLM-1014", {
    decision: "refer",
    award: 0,
    section: "Manual, section 2",
    reason: "The airline's report is missing.",
  });
  for (const caseId of ["CLM-1013", "CLM-1014"])
    await recordWorkTime(request, caseId, run_id, 41);
  await expect(rows).toHaveText([
    /^Case/,
    /^CLM-1013.*Decided.*Approved.*\$300\.00.*41 s.*\$0\.0050/,
    /^CLM-1014.*Decided.*Referred.*41 s.*\$0\.0050/,
  ]);

  await finishRun(request, run_id);
  await expect(panel.getByText("Finished", { exact: true })).toBeVisible();
  await expect(
    panel.getByText("1 approved, 0 declined and 1 referred."),
  ).toBeVisible();
  await expect(
    panel.getByText(/Model cost \$0\.0100, took \d+ s\./),
  ).toBeVisible();

  await rows.nth(1).getByRole("link", { name: "CLM-1013" }).click();
  await expect(page).toHaveURL("/cases/CLM-1013");
});

test("a case that fails twice is left for a worker", async ({
  page,
  request,
}) => {
  await page.goto("/cases/CLM-1016");
  const heading = page.locator(".page-header");
  await expect(heading.getByText("Waiting")).toBeVisible();

  await startCase(request, "CLM-1016", "e2e-3");
  await recordStep(
    request,
    "CLM-1016",
    "lookup",
    "Contract wording, section 7: Emergency Medical",
    [
      {
        file: "wording.md",
        system: "Published contract documents",
        owner: "Legal",
        reviewed: "2026-09-01",
      },
    ],
  );
  await failCase(request, "CLM-1016", "RuntimeError: The model timed out");
  await expect(
    page.getByText("Back in the queue after a failed attempt."),
  ).toBeVisible();

  await startCase(request, "CLM-1016", "e2e-4");
  await failCase(
    request,
    "CLM-1016",
    "RuntimeError: The model timed out again",
  );
  await expect(heading.getByText("Left for a worker")).toBeVisible();
  await expect(
    page.getByText(
      "The agent couldn't finish this case in 2 attempts, so it's left for a worker.",
    ),
  ).toBeVisible();

  const used = page.locator("section", {
    has: page.getByRole("heading", { name: "Context used" }),
  });
  await expect(used.getByRole("listitem")).toHaveText([
    "Contract wording, section 7: Emergency Medical",
  ]);
  const failed = page.locator(".step", { hasText: "Failed" });
  await expect(failed).toHaveText([
    /Failed RuntimeError: The model timed out$/,
    /Failed RuntimeError: The model timed out again$/,
  ]);
});
