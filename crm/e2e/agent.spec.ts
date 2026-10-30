import { expect, test } from "@playwright/test";
import {
  askToPay,
  payCase,
  decide,
  recordStep,
  startCase,
  started,
} from "./api";
import { WORKERS } from "./workers";

// These tests stand in for the agent by calling the API through the
// dashboard's proxy, and watch the case page update without a reload.

test("the case page shows the agent at work", async ({ page, request }) => {
  await page.goto("/cases/CLM-1003");
  const heading = page.locator(".page-header");
  await expect(heading.getByText("Waiting")).toBeVisible();
  await expect(page.getByText(/No steps yet/)).toBeVisible();

  await startCase(request, "CLM-1003", "e2e-1");
  await recordStep(
    request,
    "CLM-1003",
    "screening",
    "No instructions found. The case describes a medical bill in Lisbon.",
  );
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
  const steps = page.locator(".steps > li");
  await expect(steps.first()).toHaveText(
    /Security check No instructions found\. The case describes a medical bill/,
  );
  await expect(
    page.getByText('get_case: {"case_id":"CLM-1003"}').first(),
  ).toBeVisible();

  await decide(request, "CLM-1003", {
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

test("the case page shows every kind of step, the context used and the whole record", async ({
  page,
  request,
}) => {
  const manual = {
    file: "manual.md",
    system: "Cases operations",
    owner: "Head of cases operations",
    reviewed: "2026-09-01",
  };
  await page.goto("/cases/CLM-1006");
  await expect(page.getByText(/No steps yet/)).toBeVisible();

  await startCase(request, "CLM-1006", "e2e-steps");
  await recordStep(
    request,
    "CLM-1006",
    "lookup",
    "Cases manual, section 9: Repeat cases",
    [manual],
  );
  await recordStep(request, "CLM-1006", "lookup", 'Reference data: "zeppelin"');
  await recordStep(
    request,
    "CLM-1006",
    "memory_search",
    '"earlier cases"\n- CLM-1005 was approved for $243.00.',
  );
  await recordStep(
    request,
    "CLM-1006",
    "refusal",
    "record_decision: Refused with status 422: Cases manual section 14",
  );
  const steps = page.locator(".steps > li");
  await expect(steps).toHaveText([
    /Looked up Cases manual, section 9: Repeat cases.*owned by the Head of cases operations, reviewed Sep 1, 2026/,
    /Looked up Reference data: "zeppelin"/,
    /Searched memory "earlier cases"\s+- CLM-1005 was approved for \$243\.00\./,
    /Refused record_decision: Refused with status 422/,
  ]);
  const used = page.locator("section", {
    has: page.getByRole("heading", { name: "Context used" }),
  });
  await expect(used.getByRole("heading", { level: 3 })).toHaveText([
    "manual.md",
    "Found nothing",
  ]);
  await expect(
    used.getByText(
      "Cases operations, owned by the Head of cases operations, reviewed Sep 1, 2026",
    ),
  ).toBeVisible();

  await decide(request, "CLM-1006", {
    decision: "approve",
    award: 243,
    section: "Section 6, Emergency Medical",
    reason: "The hospital bill is covered.",
  });
  await recordStep(
    request,
    "CLM-1006",
    "memory_save",
    "Case CLM-1006: Food poisoning in Porto",
  );
  await expect(steps.last()).toHaveText(
    /Saved to memory Case CLM-1006: Food poisoning in Porto/,
  );
  const decision = page.locator("section", {
    has: page.getByRole("heading", { name: "Decision" }),
  });
  await expect(decision.getByRole("row").last()).toHaveText("Award$243.00");
  await expect(
    decision.getByText(/^Decided by CRM Agent, version 1 at /),
  ).toBeVisible();
  await expect(decision.getByText("Cases manual version 2026.2")).toBeVisible();
});

test("a sign-off on the dashboard pays the held award and asks the agent to resume the case", async ({
  page,
  request,
}) => {
  await startCase(request, "CLM-1020", "e2e-2");
  await decide(request, "CLM-1020", {
    decision: "approve",
    award: 1350,
    section: "Section 5, Baggage and Personal Effects",
    reason: "The loss is covered.",
  });
  const refused = await askToPay(request, "CLM-1020", 1350);
  expect(refused.status()).toBe(403);
  const before = await started(request);

  await page.goto("/cases/CLM-1020");
  const heading = page.locator(".page-header");
  await expect(heading.getByText("Waiting for sign-off")).toBeVisible();
  await expect(page.getByRole("combobox")).toHaveCount(0);
  await page.getByRole("button", { name: "Sign off" }).click();
  await expect(heading.getByText("Decided")).toBeVisible();
  await expect(
    page.getByText(/^Paid \$1,350\.00, signed off by Dana Whitfield at /),
  ).toBeVisible();
  await expect(page.getByText(/Waiting for the agent/)).toHaveCount(0);
  expect(await started(request)).toEqual([
    ...before,
    { operation: "resume_case", case_id: "CLM-1020" },
  ]);
});

test.describe("signed in as Marcus Oyelaran", () => {
  test.use({ storageState: WORKERS.marcus.storage });

  test("a held award says why he can't sign it off", async ({
    page,
    request,
  }) => {
    await startCase(request, "CLM-1024", "e2e-7");
    await decide(request, "CLM-1024", {
      decision: "approve",
      award: 1350,
      section: "Section 5, Baggage and Personal Effects",
      reason: "The loss is covered.",
    });

    await page.goto("/cases/CLM-1024");
    await expect(
      page.getByLabel("Signed in").getByText("Marcus Oyelaran"),
    ).toBeVisible();
    await expect(
      page.getByText(
        "Only a worker who can sign off awards over $1,000.00 can sign this off or send it back. Marcus Oyelaran can't.",
      ),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign off" })).toHaveCount(0);
  });
});
