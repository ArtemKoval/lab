import {
  act,
  cleanup,
  fireEvent,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Case, Decision, Step } from "./api";
import { time } from "./format";
import {
  wholeText,
  Refusal,
  type Routes,
  entry,
  history,
  marcus,
  panel,
  contract,
  renderAt,
  sent,
  stubApi,
} from "./testing";
import { REFRESH_MS } from "./useLoad";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const decidedAt = "2026-09-27T17:06:16+00:00";

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
  const routes: Routes = {
    "GET /api/cases/CLM-1002": shown,
    "GET /api/cases/CLM-1002/steps": stepsShown,
    "GET /api/contracts/POL-2002": contract,
    "GET /api/customers/CUS-3002/cases": history,
  };
  const fetchMock = stubApi(routes);
  renderAt("/cases/CLM-1002");
  return { routes, fetchMock };
}

const decisionPanel = () => panel("Decision");

const approval: Decision = {
  decision: "approve",
  award: 420,
  section: "Section 5, Baggage and Personal Effects",
  reason: "The suitcase was lost by the carrier.",
  decided_at: decidedAt,
  signed_off_by: null,
  signed_off_at: null,
};

const approved: Case = {
  ...entry,
  status: "decided",
  thread_id: "t-1",
  decision: approval,
  payment: {
    amount: 420,
    paid_at: decidedAt,
    signed_off_by: null,
    signed_off_at: null,
  },
};

const held: Case = {
  ...approved,
  status: "waiting_for_sign_off",
  decision: { ...approval, award: 1350 },
  payment: null,
};

it("says when the agent hasn't started", async () => {
  showCase(entry);
  const panel = await decisionPanel();
  expect(
    panel.getByText("The agent hasn't started on this case."),
  ).toBeDefined();
  expect(await screen.findByText(/No steps yet/)).toBeDefined();
});

it("says when a case is back in the queue after a failed attempt", async () => {
  showCase({ ...entry, attempts: 1 });
  const panel = await decisionPanel();
  expect(
    panel.getByText("Back in the queue after a failed attempt."),
  ).toBeDefined();
});

it("says when a case is left for a worker", async () => {
  showCase({ ...entry, status: "left_for_worker", attempts: 2 });
  const panel = await decisionPanel();
  expect(
    panel.getByText(
      "The agent couldn't finish this case in 2 attempts, so it's left for a worker.",
    ),
  ).toBeDefined();
});

it("shows the sections read once each, and failed attempts", async () => {
  const read = (step_id: number, content: string): Step => ({
    step_id,
    thread_id: "t-1",
    kind: "reading",
    content,
    created_at: decidedAt,
  });
  showCase({ ...entry, attempts: 1 }, [
    read(1, "Contract wording, section 3: Trip Delay"),
    read(2, "Cases manual, section 10: Meals without receipts"),
    read(3, "Contract wording, section 3: Trip Delay"),
    {
      step_id: 4,
      thread_id: "t-1",
      kind: "error",
      content: "RuntimeError: The model timed out",
      created_at: decidedAt,
    },
  ]);
  const heading = await screen.findByRole("heading", { name: "Sections read" });
  const list = within(heading.parentElement ?? document.body).getAllByRole(
    "listitem",
  );
  expect(list.map((item) => item.textContent)).toEqual([
    "Contract wording, section 3: Trip Delay",
    "Cases manual, section 10: Meals without receipts",
  ]);
  const reading = screen.getAllByText("Read");
  expect(reading).toHaveLength(3);
  const failed = screen.getByText("Failed");
  expect(failed.className).toBe("chip step-failed");
  expect(failed.parentElement?.textContent).toBe(
    "Failed RuntimeError: The model timed out",
  );
});

it("lists no sections when the agent has read none", async () => {
  showCase(approved, steps);
  expect(
    await screen.findByText('get_case(case_id="CLM-1002")'),
  ).toBeDefined();
  expect(screen.queryByText("Sections read")).toBeNull();
});

it("says when the agent is working", async () => {
  showCase({ ...entry, status: "in_progress", thread_id: "t-1" });
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

it("says the agent will pay an approval in progress", async () => {
  showCase({ ...approved, status: "in_progress", payment: null });
  const panel = await decisionPanel();
  expect(panel.getByText("Waiting for the agent to pay it.")).toBeDefined();
});

it("shows a payment with its sign-off", async () => {
  const signOff = { signed_off_by: "Dana Whitfield", signed_off_at: decidedAt };
  showCase({
    ...held,
    status: "decided",
    decision: { ...approval, award: 1350, ...signOff },
    payment: { amount: 1350, paid_at: decidedAt, ...signOff },
  });
  const panel = await decisionPanel();
  expect(panel.getByText(/^Paid/).textContent).toBe(
    `Paid $1,350.00, signed off by Dana Whitfield at ${time(decidedAt)}`,
  );
});

it("shows a decline without an award", async () => {
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
    ...entry,
    status: "in_progress",
    thread_id: "t-1",
  });
  expect(await screen.findByText(/No steps yet/)).toBeDefined();

  routes["GET /api/cases/CLM-1002/steps"] = steps.slice(0, 1);
  await act(() => vi.advanceTimersByTimeAsync(REFRESH_MS));
  expect(screen.getByText('get_case(case_id="CLM-1002")')).toBeDefined();

  routes["GET /api/cases/CLM-1002"] = approved;
  routes["GET /api/cases/CLM-1002/steps"] = steps;
  await act(() => vi.advanceTimersByTimeAsync(REFRESH_MS));
  expect(screen.getByText("Approved and paid.")).toBeDefined();
  expect(screen.getAllByText("Decided").length).toBeGreaterThan(0);
});

it("lets a worker sign off a held payment as themselves, which pays it", async () => {
  const { routes, fetchMock } = showCase(held);
  const panel = await decisionPanel();
  expect(panel.getByText(/waits for a worker's sign-off/)).toBeDefined();
  expect(panel.queryByRole("combobox")).toBeNull();

  const signOff = { signed_off_by: "Dana Whitfield", signed_off_at: decidedAt };
  const paid: Case = {
    ...held,
    status: "decided",
    decision: { ...approval, award: 1350, ...signOff },
    payment: { amount: 1350, paid_at: decidedAt, ...signOff },
  };
  routes["POST /api/cases/CLM-1002/sign-off"] = paid;
  routes["GET /api/cases/CLM-1002"] = paid;
  fireEvent.click(panel.getByRole("button", { name: "Sign off" }));

  const payment = await panel.findByText(/^Paid/);
  expect(payment.textContent).toBe(
    `Paid $1,350.00, signed off by Dana Whitfield at ${time(decidedAt)}`,
  );
  expect(sent(fetchMock, "POST /api/cases/CLM-1002/sign-off")).toEqual([
    undefined,
  ]);
});

it("tells a worker who can't sign off over the limit why", async () => {
  const { routes } = showCase(held);
  routes["GET /api/me"] = marcus;
  const panel = await decisionPanel();
  expect(
    await panel.findByText(
      wholeText(
        "Only a worker who can sign off awards over $1,000.00 can sign this off. Marcus Oyelaran can't.",
      ),
    ),
  ).toBeDefined();
  expect(panel.queryByRole("button", { name: "Sign off" })).toBeNull();
});

it("shows why a sign-off was refused", async () => {
  const { routes } = showCase(held);
  const panel = await decisionPanel();
  routes["POST /api/cases/CLM-1002/sign-off"] = new Refusal(
    409,
    "Case CLM-1002 is not waiting for sign-off",
  );
  fireEvent.click(panel.getByRole("button", { name: "Sign off" }));
  expect((await panel.findByRole("alert")).textContent).toBe(
    "Case CLM-1002 is not waiting for sign-off",
  );
});

it("shows the security check as the first step", async () => {
  showCase({ ...entry, status: "in_progress", thread_id: "t-1" }, [
    {
      step_id: 1,
      thread_id: "t-1",
      kind: "screening",
      content: "No instructions found. The case describes a delayed flight.",
      created_at: decidedAt,
    },
    ...steps,
  ]);
  const check = await screen.findByText("Security check");
  expect(check.parentElement?.textContent).toBe(
    "Security check No instructions found. The case describes a delayed flight.",
  );
  const [first] = (await panel("Agent at work")).getAllByRole("listitem");
  expect(first.textContent).toContain("Security check");
  expect(first.querySelector("svg.lucide-shield")).not.toBeNull();
});
