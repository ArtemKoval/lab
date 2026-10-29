import { expect, test } from "@playwright/test";
import type { DecisionKind } from "../dashboard/src/api";
import {
  createEvaluation,
  finishRun,
  payCase,
  recordDecision,
  recordModelCall,
  recordWorkTime,
  startCase,
} from "./api";

// This test stands in for the agent's service and its case agents, playing
// out an evaluation of the held-out set's tiny cases through the API, and
// checks the Scoreboard and the evaluation's page. Only this file records
// evaluations, and its copies are its own.

test("the Scoreboard shows an evaluation played out through the API", async ({
  page,
  request,
}) => {
  const { run_id, number, cases } = await createEvaluation(
    request,
    "held_out",
    true,
    5,
  );
  const copyOf = (original: string) => `${original}-E${String(number)}`;
  expect(cases).toHaveLength(5);

  for (const { case_id } of cases) {
    await startCase(request, case_id, `e2e-${case_id}`);
    await recordModelCall(request, case_id, run_id, 0.0125);
    await recordWorkTime(request, case_id, run_id, 40);
  }
  const decide = (original: string, decision: DecisionKind, award: number) =>
    recordDecision(request, copyOf(original), {
      decision,
      award,
      section: "Section 5",
      reason: `The agent's reason on ${original}.`,
    });
  const pay = (original: string, amount: number) =>
    payCase(request, copyOf(original), amount);
  await decide("CLM-1104", "approve", 250);
  await pay("CLM-1104", 250);
  await decide("CLM-1106", "approve", 300);
  await pay("CLM-1106", 300);
  await decide("CLM-1110", "refer", 0);
  await decide("CLM-1112", "approve", 1200);
  await finishRun(request, run_id);

  await page.goto("/scoreboard");
  const evaluation = `Evaluation #${String(number)}`;
  const row = page.getByRole("row", { name: new RegExp(`^${evaluation} `) });
  await expect(row.getByText("Finished")).toBeVisible();
  for (const shown of ["80%", "40%", "$620.00", "60%", "$0.0125", "40 s"])
    await expect(row.getByText(shown, { exact: true })).toBeVisible();
  await expect(row.getByRole("cell").last()).toHaveText(/^\d+ s$/);

  await row.getByRole("link", { name: evaluation }).click();
  await expect(page).toHaveURL(`/scoreboard/${run_id}`);
  const scored = page.getByRole("region", { name: "Cases" });
  for (const original of ["CLM-1106", "CLM-1112", "CLM-1114"])
    await expect(
      scored
        .getByRole("row", { name: new RegExp(copyOf(original)) })
        .getByText("Miss"),
    ).toBeVisible();
  for (const original of ["CLM-1104", "CLM-1110"])
    await expect(
      scored
        .getByRole("row", { name: new RegExp(copyOf(original)) })
        .getByText("Right"),
    ).toBeVisible();
  await expect(
    scored.getByRole("row", { name: new RegExp(copyOf("CLM-1114")) }),
  ).toContainText("No decision");

  await scored.getByRole("link", { name: copyOf("CLM-1112") }).click();
  await expect(page).toHaveURL(`/cases/${copyOf("CLM-1112")}`);
  await expect(
    page.getByText("A copy of CLM-1112 in an evaluation"),
  ).toBeVisible();
  await expect(
    page.getByText(
      "Held for sign-off. In an evaluation this counts as finished, and a copy can't be signed off.",
    ),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign off" })).toHaveCount(0);
});
