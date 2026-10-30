import {
  act,
  cleanup,
  fireEvent,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Case, Step } from "./api";
import type { Source } from "./sources";
import {
  approval,
  approved,
  decidedAt,
  decisionPanel,
  held,
  showCase,
  step,
} from "./caseTesting";
import { time } from "./format";
import { wholeText, Refusal, entry, marcus, panel, sent } from "./testing";
import { REFRESH_MS } from "./useLoad";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const steps: Step[] = [
  step(1, "tool_call", 'get_case(case_id="CLM-1002")'),
  step(
    2,
    "tool_result",
    `get_case: {"case_id":"CLM-1002","story":"${"A long story. ".repeat(10)}"}`,
  ),
  step(3, "message", "Approved and paid."),
];

const wording: Source = {
  file: "wording.md",
  system: "Published contract documents",
  owner: "Legal",
  reviewed: "2026-09-01",
};
const manual: Source = {
  file: "manual.md",
  system: "Cases operations",
  owner: "Head of cases operations",
  reviewed: "2026-09-01",
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

it("shows the context used once each, grouped by file, and failed attempts", async () => {
  showCase({ ...entry, attempts: 1 }, [
    step(1, "lookup", "Contract wording, section 3: Trip Delay", [wording]),
    step(2, "lookup", 'Documents: "unattended"', [wording, manual]),
    step(3, "lookup", "Contract wording, section 3: Trip Delay", [wording]),
    step(4, "lookup", 'Reference data: "zeppelin"'),
    step(5, "error", "RuntimeError: The model timed out"),
  ]);
  const used = await panel("Context used");
  const files = used.getAllByRole("heading", { level: 3 });
  expect(files.map((file) => file.textContent)).toEqual([
    "wording.md",
    "manual.md",
    "Found nothing",
  ]);
  const lookedUp = (file: HTMLElement) =>
    within(file.parentElement ?? document.body)
      .getAllByRole("listitem")
      .map((item) => item.textContent);
  expect(lookedUp(files[0])).toEqual([
    "Contract wording, section 3: Trip Delay",
    'Documents: "unattended"',
  ]);
  expect(lookedUp(files[1])).toEqual(['Documents: "unattended"']);
  expect(lookedUp(files[2])).toEqual(['Reference data: "zeppelin"']);
  expect(
    used.getByText(
      "Cases operations, owned by the Head of cases operations, reviewed Sep 1, 2026",
    ),
  ).toBeDefined();
  expect(
    used.getByText(
      "Published contract documents, owned by Legal, reviewed Sep 1, 2026",
    ),
  ).toBeDefined();
  const failed = screen.getByText("Failed");
  expect(failed.className).toBe("chip step-failed");
  expect(failed.parentElement?.textContent).toBe(
    "Failed RuntimeError: The model timed out",
  );
  expect(screen.queryByText("Sections read")).toBeNull();
});

it("shows no context used when the agent has looked nothing up", async () => {
  showCase(approved, steps);
  expect(
    await screen.findByText('get_case(case_id="CLM-1002")'),
  ).toBeDefined();
  expect(screen.queryByText("Context used")).toBeNull();
});

it("shows each lookup, memory search and save with its icon", async () => {
  showCase({ ...entry, status: "in_progress", thread_id: "t-1" }, [
    step(1, "lookup", "Cases manual, section 14: Records", [manual]),
    step(2, "memory_search", '"earlier cases"\n- Oliver Grant travels a lot.'),
    step(3, "memory_save", "Case CLM-1002: A lost suitcase"),
    step(4, "lookup", 'Reference data: "zeppelin"'),
  ]);
  // The steps, not the files listed inside a lookup.
  const [list] = (await panel("Agent at work")).getAllByRole("list");
  const items = Array.from(list.children);
  const lookup = items[0];
  expect(lookup.querySelector("svg.lucide-book-open")).not.toBeNull();
  expect(lookup.textContent).toContain(
    "Looked up Cases manual, section 14: Records",
  );
  expect(lookup.textContent).toContain(
    "manual.md: Cases operations, owned by the Head of cases operations, reviewed Sep 1, 2026",
  );
  expect(items[1].querySelector("svg.lucide-history")).not.toBeNull();
  expect(items[1].textContent).toContain(
    'Searched memory "earlier cases"\n- Oliver Grant travels a lot.',
  );
  expect(items[2].querySelector("svg.lucide-notebook-pen")).not.toBeNull();
  expect(items[2].textContent).toContain(
    "Saved to memory Case CLM-1002: A lost suitcase",
  );
  expect(items[3].textContent).toContain(
    'Looked up Reference data: "zeppelin"Found nothing',
  );
});

it("says when the agent is working", async () => {
  showCase({ ...entry, status: "in_progress", thread_id: "t-1" });
  const panel = await decisionPanel();
  expect(panel.getByText("The agent is working on this case.")).toBeDefined();
});

it("shows an approval's whole record and its payment", async () => {
  showCase(approved, steps);
  const panel = await decisionPanel();
  expect(panel.getByText("Approved")).toBeDefined();
  const lines = within(panel.getByRole("table")).getAllByRole("row");
  expect(lines.map((row) => row.textContent)).toEqual([
    "Suitcase, limited to $300.00$300.00",
    "Clothes$170.00",
    "Less the deductible-$50.00",
    "Award$420.00",
  ]);
  expect(
    panel.getByText(
      `Decided by CRM Agent, version 1 at ${time(decidedAt)}`,
    ),
  ).toBeDefined();
  expect(panel.getByText("Cases manual version 2026.2")).toBeDefined();
  expect(panel.getAllByText("$420.00")).toHaveLength(3);
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
    decision: {
      ...approval,
      decision: "decline",
      award: 0,
      calculation: null,
    },
    payment: null,
  });
  const panel = await decisionPanel();
  expect(panel.getByText("Declined")).toBeDefined();
  expect(panel.queryByRole("table")).toBeNull();
  expect(panel.getByText("Cases manual version 2026.2")).toBeDefined();
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
  expect(
    panel.getByText(
      wholeText(
        "The payment of $1,350.00 is over the approval limit and waits for a worker's sign-off.",
      ),
    ),
  ).toBeDefined();
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

it("says when the Gateway refused a payment, with its reason", async () => {
  const refused = "Tool Execution Denied: the Contract forbids it";
  showCase({
    ...held,
    decision: { ...approval, award: 1500, gateway_refusal: refused },
  });
  const panel = await decisionPanel();
  expect(
    panel.getByText(
      wholeText(
        "The Gateway refused the payment of $1,500.00, so it waits for a worker's sign-off.",
      ),
    ),
  ).toBeDefined();
  expect(panel.getByText(refused)).toBeDefined();
  expect(panel.queryByText(/over the approval limit/)).toBeNull();
  expect(panel.getByRole("button", { name: "Sign off" })).toBeDefined();
});

it("tells a worker who can't sign off over the limit why", async () => {
  const { routes } = showCase(held);
  routes["GET /api/me"] = marcus;
  const panel = await decisionPanel();
  expect(
    await panel.findByText(
      wholeText(
        "Only a worker who can sign off awards over $1,000.00 can sign this off or send it back. Marcus Oyelaran can't.",
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

it("shows a refusal standing out from the other steps", async () => {
  const refusal = "record_decision: Refused with status 422: No calculation";
  showCase({ ...entry, status: "in_progress", thread_id: "t-1" }, [
    ...steps,
    step(4, "refusal", refusal),
  ]);
  const chip = await screen.findByText("Refused");
  expect(chip.className).toBe("chip step-refused");
  expect(chip.querySelector("svg.lucide-ban")).not.toBeNull();
  expect(chip.parentElement?.textContent).toBe(`Refused ${refusal}`);
  const items = (await panel("Agent at work")).getAllByRole("listitem");
  expect(items.filter((item) => item.querySelector(".step-refused"))).toEqual([
    items[3],
  ]);
});

it("shows the security check as the first step", async () => {
  showCase({ ...entry, status: "in_progress", thread_id: "t-1" }, [
    step(
      1,
      "screening",
      "No instructions found. The case describes a delayed flight.",
    ),
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
