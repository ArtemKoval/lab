import { expect, test } from "@playwright/test";

// This spec walks the loan desk flow of the library pack. The playwright
// config runs it only on CRM_DOMAIN=library, and leaves it out of the
// default insurance run.

test("the loan desk queue lists the seed requests", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Cases queue" }),
  ).toBeVisible();
  const row = page.getByRole("row").filter({ hasText: "LN-5001" });
  await expect(row.getByText("Waiting")).toBeVisible();
  await expect(page.getByRole("link", { name: "LN-5003" })).toBeVisible();
});

test("the lead librarian is signed in", async ({ page }) => {
  await page.goto("/scoreboard");
  const who = page.getByLabel("Signed in");
  await expect(who.getByText("Rosa Meridian")).toBeVisible();
  await expect(who.getByText("Library Lead")).toBeVisible();
});

test("a loan request opens with the pack words", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "LN-5001" }).click();
  await expect(page).toHaveURL("/cases/LN-5001");
  await expect(
    page.getByRole("heading", { name: /Checkout of The Lighthouse Keeper/ }),
  ).toBeVisible();
  await expect(page.getByText("Marta Voss's checkout request")).toBeVisible();
  // The queue and the case page speak the loan desk: the queue column reads
  // Replacement price, the incident line reads Received at, and the
  // membership card carries the pack's rows.
  await page.goto("/");
  await expect(
    page.getByRole("columnheader", { name: "Replacement price" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "LN-5001" }).click();
  await expect(page.getByText("Received at")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Membership" })).toBeVisible();
  await expect(page.getByText("Members on the card")).toBeVisible();
  await expect(
    page.getByText("Northgate Public Library, Central branch", {
      exact: true,
    }),
  ).toBeVisible();
});

test("the settings page names the pack's approval limit", async ({ page }) => {
  await page.goto("/settings");
  await expect(
    page.getByRole("spinbutton", { name: "Approval limit" }),
  ).toHaveValue("14");
  await expect(page.getByText("days", { exact: true })).toBeVisible();
});
