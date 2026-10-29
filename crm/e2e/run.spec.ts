import { expect, test } from "@playwright/test";
import { post, put } from "./api";

// These tests stand in for the queue agent and a case agent by calling the
// API through the dashboard's proxy, and watch the pages update without a
// reload. Only this file starts runs, and it uses cases no other test touches.

test("the queue shows the agent's to-do list as it works", async ({
  page,
  request,
}) => {
  await page.goto("/");
  const panel = page.locator("section", {
    has: page.getByRole("heading", { name: "Current run" }),
  });
  await expect(panel).toBeVisible();

  const response = await post(request, "/api/runs", { cap: 2 });
  const { run_id } = (await response.json()) as { run_id: string };
  const write = (first: string, second: string) =>
    put(request, `/api/runs/${run_id}/todos`, {
      todos: [
        { content: "CLM-1013 Seven hour delay leaving Chicago", status: first },
        { content: "CLM-1014 Duffel bag lost", status: second },
      ],
    });
  const items = panel.getByRole("listitem");

  await write("to_do", "to_do");
  await expect(panel.getByText("Running", { exact: true })).toBeVisible();
  await expect(items).toHaveText([/^To do.*CLM-1013/, /^To do.*CLM-1014/]);

  await write("in_progress", "to_do");
  await expect(items).toHaveText([
    /^In progress.*CLM-1013/,
    /^To do.*CLM-1014/,
  ]);

  await write("done", "in_progress");
  await expect(items).toHaveText([/^Done.*CLM-1013/, /^In progress.*CLM-1014/]);

  await post(request, `/api/runs/${run_id}/finish`, {
    summary: "Worked 2 cases: 2 approved.",
  });
  await expect(panel.getByText("Finished", { exact: true })).toBeVisible();
  await expect(panel.getByText("Summary for the workers")).toBeVisible();
  await expect(panel.getByText("Worked 2 cases: 2 approved.")).toBeVisible();

  await items.first().getByRole("link", { name: "CLM-1013" }).click();
  await expect(page).toHaveURL("/cases/CLM-1013");
});

test("a case that fails twice is left for a worker", async ({
  page,
  request,
}) => {
  await page.goto("/cases/CLM-1016");
  const heading = page.locator(".case-heading");
  await expect(heading.getByText("Waiting")).toBeVisible();

  await post(request, "/api/cases/CLM-1016/start", { thread_id: "e2e-3" });
  await post(request, "/api/cases/CLM-1016/steps", {
    kind: "reading",
    content: "Contract wording, section 7: Emergency Medical",
  });
  await post(request, "/api/cases/CLM-1016/failure", {
    reason: "RuntimeError: The model timed out",
  });
  await expect(
    page.getByText("Back in the queue after a failed attempt."),
  ).toBeVisible();

  await post(request, "/api/cases/CLM-1016/start", { thread_id: "e2e-4" });
  await post(request, "/api/cases/CLM-1016/failure", {
    reason: "RuntimeError: The model timed out again",
  });
  await expect(heading.getByText("Left for a worker")).toBeVisible();
  await expect(
    page.getByText(
      "The agent couldn't finish this case in 2 attempts, so it's left for a worker.",
    ),
  ).toBeVisible();

  const read = page.locator(".sections-read");
  await expect(read.getByRole("listitem")).toHaveText([
    "Contract wording, section 7: Emergency Medical",
  ]);
  const failed = page.locator(".step", { hasText: "Failed" });
  await expect(failed).toHaveText([
    /Failed RuntimeError: The model timed out$/,
    /Failed RuntimeError: The model timed out again$/,
  ]);
});
