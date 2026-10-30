import { expect, test } from "@playwright/test";
import { WORKERS } from "./workers";

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

test("signing out from the account menu lands on the sign-in page", async ({
  browser,
}) => {
  // A browser of its own, so signing out leaves the other tests signed in.
  const context = await browser.newContext({
    storageState: WORKERS.dana.storage,
  });
  const page = await context.newPage();
  await page.goto("/scoreboard");
  const who = page.getByLabel("Signed in");
  await expect(who.getByText("Dana Whitfield")).toBeVisible();
  await expect(who.getByText("Senior Cases Worker")).toBeVisible();
  await who.getByRole("button", { name: "Account" }).click();
  await who.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL("/sign-in");
  await expect(
    page.getByRole("heading", { name: "Sign in", level: 1 }),
  ).toBeVisible();
  await page.goto("/scoreboard");
  await expect(page).toHaveURL("/sign-in");
  await context.close();
});
