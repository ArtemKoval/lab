import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import type { Case, Decision, Worker, Step } from "./api";
import { Refusal, case, history, contract, stubApi } from "./testing";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const decidedAt = "2026-09-27T17:06:16+00:00";

const workers: Worker[] = [
  {
    worker_id: "HND-01",
    name: "Dana Whitfield",
    role: "Senior Cases Worker",
    can_approve_over_limit: true,
  },
  {
    worker_id: "HND-04",
    name: "Sam Trainee",
    role: "Trainee",
    can_approve_over_limit: false,
  },
];

const steps: Step[] = [
  {
    step_id: 1,
    thread_id: "t-1",
    kind: "tool_call",
    content: 'get_case(case_id="CLM-1002")',
    created_at: decidedAt,
  },
  {
    step_id: 2,
    thread_id: "t-1",
    kind: "tool_result",
    content: `get_case: {"case_id":"CLM-1002","story":"${"A long story. ".repeat(10)}"}`,
    created_at: decidedAt,
  },
  {
    step_id: 3,
    thread_id: "t-1",
    kind: "message",
    content: "Approved and paid.",
    created_at: decidedAt,
  },
];

function showCase(shown: Case, stepsShown: Step[] = []) {
  const routes: Record<string, unknown> = {
    "GET /api/cases/CLM-1002": shown,
    "GET /api/cases/CLM-1002/steps": stepsShown,
    "GET /api/contracts/POL-2002": contract,
    "GET /api/customers/CUS-3002/cases": history,
    "GET /api/workers": workers,
  };
  const fetchMock = stubApi(routes);
  render(
    <MemoryRouter initialEntries={["/cases/CLM-1002"]}>
      <App />
    </MemoryRouter>,
  );
  return { routes, fetchMock };
}

async function decisionPanel() {
  const heading = await screen.findByRole("heading", { name: "Decision" });
  const panel = heading.closest("section");
  if (!panel) throw new Error("The decision heading has no panel");
  return within(panel);
}

const approval: Decision = {
  decision: "approve",
  award: 420,
  section: "Section 5, Baggage and Personal Effects",
  reason: "The suitcase was lost by the carrier.",
  decided_at: decidedAt,
};

const approved: Case = {
  ...case,
  status: "decided",
  thread_id: "t-1",
  decision: approval,
  payment: { amount: 420, paid_at: decidedAt, signed_off_by: null },
};

const held: Case = {
  ...approved,
  status: "waiting_for_sign_off",
  decision: { ...approval, award: 1350 },
  payment: null,
};

it("says when the agent hasn't started", async () => {
  showCase(case);
  const panel = await decisionPanel();
  expect(
    panel.getByText("The agent hasn't started on this case."),
  ).toBeDefined();
  expect(await screen.findByText(/No steps yet/)).toBeDefined();
});

it("says when the agent is working", async () => {
  showCase({ ...case, status: "in_progress", thread_id: "t-1" });
  const panel = await decisionPanel();
  expect(panel.getByText("The agent is working on this case.")).toBeDefined();
});

it("shows an approval and its payment", async () => {
  showCase(approved, steps);
  const panel = await decisionPanel();
  expect(panel.getByText("Approved")).toBeDefined();
  expect(panel.getAllByText("$420.00")).toHaveLength(2);
  expect(panel.getByText(approval.section)).toBeDefined();
  expect(panel.getByText(approval.reason)).toBeDefined();
  expect(panel.getByText(/^Paid/).textContent).toBe("Paid $420.00");
});

it("shows an approval that hasn't been paid yet", async () => {
  showCase({ ...approved, payment: null });
  const panel = await decisionPanel();
  expect(panel.getByText("Not paid yet")).toBeDefined();
});

it("shows a decline without a award", async () => {
  showCase({
    ...approved,
    decision: { ...approval, decision: "decline", award: 0 },
    payment: null,
  });
  const panel = await decisionPanel();
  expect(panel.getByText("Declined")).toBeDefined();
  expect(panel.queryByText("$0.00")).toBeNull();
  expect(panel.queryByText(/paid/i)).toBeNull();
});

it("shows each kind of step, with results folded", async () => {
  showCase(approved, steps);
  expect(
    await screen.findByText('get_case(case_id="CLM-1002")'),
  ).toBeDefined();
  const result = screen.getAllByText(/^get_case: /)[0].closest("details");
  expect(result?.open).toBe(false);
  expect(result?.querySelector("summary")?.textContent).toMatch(/\.\.\.$/);
  expect(result?.querySelector("pre")?.textContent).toBe(steps[1].content);
  expect(screen.getByText("Approved and paid.")).toBeDefined();
});

it("shows new steps and the decision as the agent works", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const { routes } = showCase({
    ...case,
    status: "in_progress",
    thread_id: "t-1",
  });
  expect(await screen.findByText(/No steps yet/)).toBeDefined();

  routes["GET /api/cases/CLM-1002/steps"] = steps.slice(0, 1);
  await act(() => vi.advanceTimersByTimeAsync(2000));
  expect(screen.getByText('get_case(case_id="CLM-1002")')).toBeDefined();

  routes["GET /api/cases/CLM-1002"] = approved;
  routes["GET /api/cases/CLM-1002/steps"] = steps;
  await act(() => vi.advanceTimersByTimeAsync(2000));
  expect(screen.getByText("Approved and paid.")).toBeDefined();
  expect(screen.getAllByText("Decided").length).toBeGreaterThan(0);
});

it("lets a worker sign off a held payment", async () => {
  const { routes, fetchMock } = showCase(held);
  const panel = await decisionPanel();
  expect(panel.getByText(/waits for a worker's sign-off/)).toBeDefined();
  const button = panel.getByRole("button", { name: "Sign off" });
  expect(button).toHaveProperty("disabled", true);

  const select = panel.getByRole("combobox", { name: "Worker" });
  expect(await within(select).findByText("Dana Whitfield")).toBeDefined();
  expect(within(select).queryByText("Sam Trainee")).toBeNull();

  const signedOff: Case = {
    ...held,
    status: "decided",
    payment: {
      amount: 1350,
      paid_at: decidedAt,
      signed_off_by: "Dana Whitfield",
    },
  };
  routes["POST /api/cases/CLM-1002/sign-off"] = signedOff;
  fireEvent.change(select, { target: { value: "HND-01" } });
  routes["GET /api/cases/CLM-1002"] = signedOff;
  fireEvent.click(button);

  const payment = await panel.findByText(/signed off by Dana Whitfield/);
  expect(payment.textContent).toBe(
    "Paid $1,350.00, signed off by Dana Whitfield",
  );
  const [, init] = fetchMock.mock.calls.find(
    ([path, request]) =>
      path === "/api/cases/CLM-1002/sign-off" && request?.method === "POST",
  ) ?? [undefined, undefined];
  expect(init?.body).toBe(JSON.stringify({ worker_id: "HND-01" }));
});

it("shows why a sign-off was refused", async () => {
  const { routes } = showCase(held);
  const panel = await decisionPanel();
  routes["POST /api/cases/CLM-1002/sign-off"] = new Refusal(
    409,
    "Case CLM-1002 is not waiting for sign-off",
  );
  const select = panel.getByRole("combobox", { name: "Worker" });
  await within(select).findByText("Dana Whitfield");
  fireEvent.change(select, { target: { value: "HND-01" } });
  fireEvent.click(panel.getByRole("button", { name: "Sign off" }));
  expect((await panel.findByRole("alert")).textContent).toBe(
    "Case CLM-1002 is not waiting for sign-off",
  );
});
