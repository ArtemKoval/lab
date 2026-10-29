import { expect, test } from "@playwright/test";
import {
  askToPay,
  payCase,
  recordDecision,
  recordStep,
  resumed,
  startCase,
} from "./api";

// These tests stand in for the agent by calling the API through the
// dashboard's proxy, and watch the case page update without a reload.

test("the case page shows the agent at work", async ({ page, request }) => {
  await page.goto("/cases/CLM-1003");
  const heading = page.locator(".case-heading");
  await expect(heading.getByText("Waiting")).toBeVisible();
  await expect(page.getByText(/No steps yet/)).toBeVisible();

  await startCase(request, "CLM-1003", "e2e-1");
  await recordStep(
    request,
    "CLM-1003",
    "tool_call",
    'get_case(case_id="CLM-1003")',
  );
  await recordStep(
    request,
    "CLM-1003",
    "tool_result",
    'get_case: {"case_id":"CLM-1003"}',
  );
  await expect(heading.getByText("In progress")).toBeVisible();
  await expect(
    page.getByText("The agent is working on this case."),
  ).toBeVisible();
  await expect(page.getByText('get_case(case_id="CLM-1003")')).toBeVisible();
  await expect(
    page.getByText('get_case: {"case_id":"CLM-1003"}').first(),
  ).toBeVisible();

  await recordDecision(request, "CLM-1003", {
    decision: "approve",
    award: 500,
    section: "Section 7, Emergency Medical",
    reason: "The treatment was necessary and covered.",
  });
  const decision = page.locator("section", {
    has: page.getByRole("heading", { name: "Decision" }),
  });
  await expect(decision.getByText("Approved")).toBeVisible();
  await expect(heading.getByText("In progress")).toBeVisible();
  await payCase(request, "CLM-1003", 500);
  await recordStep(
    request,
    "CLM-1003",
    "message",
    "Approved and paid $500.00.",
  );
  await expect(heading.getByText("Decided")).toBeVisible();
  await expect(decision.getByText("Paid $500.00")).toBeVisible();
  await expect(page.getByText("Approved and paid $500.00.")).toBeVisible();
});

test("a sign-off on the dashboard reaches the agent's service", async ({
  page,
  request,
}) => {
  await startCase(request, "CLM-1020", "e2e-2");
  await recordDecision(request, "CLM-1020", {
    decision: "approve",
    award: 1350,
    section: "Section 5, Baggage and Personal Effects",
    reason: "The loss is covered.",
  });
  const refused = await askToPay(request, "CLM-1020", 1350);
  expect(refused.status()).toBe(403);

  await page.goto("/cases/CLM-1020");
  const heading = page.locator(".case-heading");
  await expect(heading.getByText("Waiting for sign-off")).toBeVisible();
  expect(await resumed(request)).not.toContain("CLM-1020");
  await page.getByRole("combobox", { name: "Worker" }).selectOption({
    label: "Dana Whitfield",
  });
  await page.getByRole("button", { name: "Sign off" }).click();
  await expect(heading.getByText("In progress")).toBeVisible();
  await expect(page.getByText(/Signed off by Dana Whitfield/)).toBeVisible();
  await expect.poll(() => resumed(request)).toContain("CLM-1020");

  // The test plays the agent, which pays the case once it is told.
  await payCase(request, "CLM-1020", 1350);
  await expect(heading.getByText("Decided")).toBeVisible();
  await expect(
    page.getByText(/^Paid \$1,350\.00, signed off by Dana Whitfield at /),
  ).toBeVisible();
});
