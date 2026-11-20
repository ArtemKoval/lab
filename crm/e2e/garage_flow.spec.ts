import { expect, test } from "@playwright/test";
import { WORKERS } from "./workers";

// This spec walks the repair desk flow of the garage pack. The playwright
// config runs it only on CRM_DOMAIN=garage, and leaves it out of the
// default insurance run.

test.describe("the service manager's queue", () => {
  test.use({ storageState: WORKERS.gordon.storage });

  test("the repair desk queue lists the seed jobs", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Cases queue" }),
    ).toBeVisible();
    const row = page.getByRole("row").filter({ hasText: "JOB-1001" });
    await expect(row.getByText("Waiting")).toBeVisible();
    await expect(page.getByRole("link", { name: "JOB-1005" })).toBeVisible();
  });

  test("the service manager is signed in", async ({ page }) => {
    await page.goto("/scoreboard");
    const who = page.getByLabel("Signed in");
    await expect(who.getByText("Gordon Vale")).toBeVisible();
    await expect(who.getByText("Service Manager")).toBeVisible();
  });

  test("a repair job opens with the pack words", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "JOB-1001" }).click();
    await expect(page).toHaveURL("/cases/JOB-1001");
    await expect(
      page.getByRole("heading", { name: /Volkswagen Golf 2016/ }),
    ).toBeVisible();
    await expect(page.getByText("Jenny Doyle's repair job")).toBeVisible();
    // The queue and the case page speak the repair desk: the queue column
    // reads Estimate, the incident line reads Reported fault, and the
    // agreement card carries the pack's rows.
    await page.goto("/");
    await expect(
      page.getByRole("columnheader", { name: "Estimate" }),
    ).toBeVisible();
    await page.getByRole("link", { name: "JOB-1001" }).click();
    await expect(page.getByText("Reported fault")).toBeVisible();
    await expect(page.getByText("Covered vehicle")).toBeVisible();
    await expect(page.getByText("Vehicle make")).toBeVisible();
  });
});
