import {
  cleanup,
  fireEvent,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Case, Evaluation, ScoredCase, ScoredEvaluation } from "./api";
import {
  Refusal,
  type Routes,
  entry,
  history,
  panel,
  contract,
  renderAt,
  sent,
  stubApi,
  summary,
} from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const finished: Evaluation = {
  run_id: "run-7",
  number: 7,
  kind: "evaluation",
  agents: 25,
  model: "openai/gpt-6-luna",
  reasoning_effort: "low",
  evaluation_set: "evaluation",
  tiny: false,
  status: "finished",
  started_at: "2026-10-03T17:02:13+00:00",
  finished_at: "2026-10-03T17:04:54+00:00",
  seconds: 161,
  model_cost: 0.3125,
  size: 25,
  measures: {
    decision_accuracy: 0.8,
    accuracy: 0.64,
    cost_of_mistakes: 1600,
    straight_through: 0.88,
    model_cost_per_case: 0.0125,
    seconds_per_case: 40,
    run_seconds: 161,
  },
};

const running: Evaluation = {
  ...finished,
  run_id: "run-9",
  number: 9,
  agents: 5,
  evaluation_set: "held_out",
  tiny: true,
  status: "running",
  finished_at: null,
  seconds: null,
  size: 5,
  measures: { ...finished.measures, run_seconds: null },
};

function showScoreboard(routes: Routes = {}) {
  const fetchMock = stubApi({
    "GET /api/evaluations": [running, finished],
    ...routes,
  });
  renderAt("/scoreboard");
  return fetchMock;
}

it("lists the evaluations in the backend's order, with their measures", async () => {
  showScoreboard();
  const list = await panel("Evaluations");
  const rows = (await list.findAllByRole("row")).slice(1);
  expect(
    rows.map((row) => within(row).getAllByRole("link")[0].textContent),
  ).toEqual(["Evaluation #9", "Evaluation #7"]);
  const [newest, older] = rows.map((row) => within(row));
  expect(newest.getByText("Held-out set, 5 cases")).toBeDefined();
  expect(newest.getByText("Running")).toBeDefined();
  expect(older.getByText("Evaluation set, 25 cases")).toBeDefined();
  expect(older.getByText("openai/gpt-6-luna")).toBeDefined();
  for (const shown of ["80%", "64%", "$1,600.00", "88%", "$0.0125", "40 s"])
    expect(older.getByText(shown)).toBeDefined();
  expect(older.getByText("2 min 41 s")).toBeDefined();
  expect(newest.queryByText("2 min 41 s")).toBeNull();
  expect(older.getByText(/Oct 3, .*, 25 case agents at once/)).toBeDefined();
  const link = older.getByRole("link", { name: "Evaluation #7" });
  expect(link.getAttribute("href")).toBe("/scoreboard/run-7");
});

it("says when there are no evaluations yet", async () => {
  stubApi({ "GET /api/evaluations": [] });
  renderAt("/scoreboard");
  expect(await screen.findByText("No evaluations yet.")).toBeDefined();
});

it("starts an evaluation with the choices made", async () => {
  const fetchMock = showScoreboard({
    "POST /api/evaluations": { status: "accepted" },
  });
  const form = await panel("Start an evaluation");
  const set = form.getByRole("combobox", { name: "Set" });
  const cases = form.getByRole("combobox", { name: "Cases" });
  const agents = form.getByRole("combobox", { name: "Case agents at once" });
  expect(
    [set, cases, agents].map((c) => (c as HTMLSelectElement).value),
  ).toEqual(["evaluation", "all", "3"]);

  fireEvent.change(set, { target: { value: "held_out" } });
  fireEvent.change(cases, { target: { value: "tiny" } });
  fireEvent.change(agents, { target: { value: "5" } });
  fireEvent.click(form.getByRole("button", { name: "Start an evaluation" }));
  await waitFor(() => {
    expect(sent(fetchMock, "POST /api/evaluations")).toEqual([
      { evaluation_set: "held_out", tiny: true, agents: 5 },
    ]);
  });
});

it.each([
  [409, "A dispatch or an evaluation is already running"],
  [503, "The agent's service isn't running"],
])("shows a refusal with status %i", async (status, detail) => {
  showScoreboard({ "POST /api/evaluations": new Refusal(status, detail) });
  const form = await panel("Start an evaluation");
  fireEvent.click(form.getByRole("button", { name: "Start an evaluation" }));
  expect((await form.findByRole("alert")).textContent).toBe(detail);
});

const copy: ScoredCase = {
  ...summary,
  case_id: "CLM-1104-E9",
  started_at: "2026-10-03T17:02:14+00:00",
  seconds: 40,
  model_cost: 0.0125,
  status: "decided",
  decision: "approve",
  award: 250,
  copy_of: "CLM-1104",
  reason: "The delay was covered.",
  worker_decision: "approve",
  worker_award: 250,
  right: true,
  mistake_cost: 0,
};

const scored: ScoredEvaluation = {
  ...finished,
  run_id: "run-9",
  number: 9,
  evaluation_set: "held_out",
  tiny: true,
  size: 5,
  cases: [
    copy,
    {
      ...copy,
      case_id: "CLM-1112-E9",
      copy_of: "CLM-1112",
      status: "waiting_for_sign_off",
      award: 1200,
      worker_award: 680,
      right: false,
      mistake_cost: 520,
    },
    {
      ...copy,
      case_id: "CLM-1114-E9",
      copy_of: "CLM-1114",
      status: "in_progress",
      decision: null,
      award: null,
      reason: null,
      worker_decision: "decline",
      worker_award: 0,
      right: false,
      mistake_cost: 50,
    },
  ],
};

it("shows an evaluation's cases beside the workers' decisions", async () => {
  stubApi({ "GET /api/evaluations/run-9": scored });
  renderAt("/scoreboard/run-9");
  expect(
    await screen.findByRole("heading", { name: "Evaluation #9", level: 1 }),
  ).toBeDefined();
  const measures = await panel("Measures");
  const shown = (label: string) =>
    measures.getByText(label).nextSibling?.textContent;
  expect(shown("Decision accuracy")).toBe("80%");
  expect(shown("Run time")).toBe("2 min 41 s");
  const rows = (await panel("Cases")).getAllByRole("row").slice(1);
  const [right, held, undecided] = rows.map((row) => within(row));
  expect(right.getByText("Right").className).toBe("chip score-right");
  expect(right.getAllByText("$250.00")).toHaveLength(2);
  expect(held.getByText("Miss").className).toBe("chip score-miss");
  expect(held.getByText("$680.00")).toBeDefined();
  expect(held.getByText("$1,200.00")).toBeDefined();
  expect(held.getByText("$520.00")).toBeDefined();
  expect(undecided.getByText("No decision")).toBeDefined();
  expect(undecided.getByText("Declined")).toBeDefined();
  expect(undecided.getByText("Miss")).toBeDefined();
  const link = right.getByRole("link", { name: "CLM-1104-E9" });
  expect(link.getAttribute("href")).toBe("/cases/CLM-1104-E9");
});

it("says when an evaluation doesn't exist", async () => {
  stubApi({});
  renderAt("/scoreboard/run-404");
  expect(await screen.findByText("Evaluation not found")).toBeDefined();
});

it("shows a copy's evaluation, and no sign-off for a held copy", async () => {
  const heldCopy: Case = {
    ...entry,
    case_id: "CLM-1112-E9",
    status: "waiting_for_sign_off",
    thread_id: "t-1",
    attempts: 1,
    evaluation_id: "run-9",
    copy_of: "CLM-1112",
    decision: {
      decision: "approve",
      award: 1200,
      section: "Section 5",
      reason: "The loss is covered.",
      decided_at: "2026-10-03T17:03:00+00:00",
      signed_off_by: null,
      signed_off_at: null,
    },
  };
  stubApi({
    "GET /api/cases/CLM-1112-E9": heldCopy,
    "GET /api/cases/CLM-1112-E9/steps": [],
    "GET /api/contracts/POL-2002": contract,
    "GET /api/customers/CUS-3002/cases": history,
  });
  renderAt("/cases/CLM-1112-E9");
  const note = await screen.findByText(/A copy of/);
  expect(note.textContent).toBe("A copy of CLM-1112 in an evaluation");
  const link = within(note).getByRole("link", { name: "evaluation" });
  expect(link.getAttribute("href")).toBe("/scoreboard/run-9");
  const decision = await panel("Decision");
  expect(
    decision.getByText(
      "Held for sign-off. In an evaluation this counts as finished, and a copy can't be signed off.",
    ),
  ).toBeDefined();
  expect(decision.queryByRole("button", { name: "Sign off" })).toBeNull();
});

it("links to the Scoreboard from the header", async () => {
  stubApi({ "GET /api/cases": [summary], "GET /api/dispatches/latest": null });
  renderAt("/");
  const link = await screen.findByRole("link", { name: "Scoreboard" });
  expect(link.getAttribute("href")).toBe("/scoreboard");
});

it("shows a stopped evaluation as stopped, with no run time", async () => {
  const stopped = { ...running, status: "stopped" as const };
  stubApi({
    "GET /api/evaluations": [stopped],
    "GET /api/evaluations/run-9": {
      ...scored,
      status: "stopped",
      measures: running.measures,
    },
  });
  renderAt("/scoreboard");
  const [row] = (await (await panel("Evaluations")).findAllByRole("row")).slice(
    1,
  );
  expect(within(row).getByText("Stopped")).toBeDefined();
  expect(within(row).getAllByRole("cell").at(-1)?.textContent).toBe(
    "Not finished",
  );
  cleanup();

  renderAt("/scoreboard/run-9");
  const measures = await panel("Measures");
  expect(screen.getByText("Stopped")).toBeDefined();
  expect(measures.getByText("Run time").nextSibling?.textContent).toBe(
    "Not finished",
  );
});
