import { expect, test } from "@playwright/test";

test("the queue lists every case", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Cases queue" }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(25);
  const last = page.getByRole("row").filter({ hasText: "CLM-1025" });
  await expect(last.getByText("Waiting")).toBeVisible();
});

test("a case opens from the queue", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "CLM-1001" }).click();
  await expect(page).toHaveURL("/cases/CLM-1001");
  await expect(page.getByText(/My flight home from Rome/)).toBeVisible();
  await expect(
    page.getByText("Hotel Aurelia Fiumicino", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText("POL-2001")).toBeVisible();
});

test("the header opens the instructions", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Instructions" }).click();
  await expect(page).toHaveURL("/instructions");
  const queue = page.getByRole("region", { name: "Running the queue" });
  await expect(queue.getByText(/you run the claims queue/)).toBeVisible();
  const entry = page.getByRole("region", { name: "Working a case" });
  await expect(
    entry.getByText(/10\. How we work out your payment/),
  ).toBeVisible();
  await expect(entry.getByText(/9\. Repeat claims/)).toBeVisible();
});
