import { expect, test as setup } from "@playwright/test";
import { WORKERS, TEST_PASSWORD } from "./workers";

// Signs in on the sign-in page as each worker the tests use, and keeps each
// browser's storage, with its session, for the tests.
for (const worker of Object.values(WORKERS)) {
  setup(`sign in as ${worker.name}`, async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL("/sign-in");
    await page.getByLabel("Email").fill(worker.email);
    await page.getByLabel("Password").fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(
      page.getByLabel("Signed in").getByText(worker.name),
    ).toBeVisible();
    await page.context().storageState({ path: worker.storage });
  });
}
