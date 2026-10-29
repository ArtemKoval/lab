import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { Refusal, case, history, contract, stubApi, summary } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

it("shows the queue with counts by state", async () => {
  stubApi({
    "GET /api/cases": [
      summary,
      {
        ...summary,
        case_id: "CLM-1003",
        status: "decided",
        decision: "approve",
        award: 420,
      },
    ],
  });
  renderAt("/");
  const link = await screen.findByRole("link", { name: "CLM-1002" });
  expect(link.getAttribute("href")).toBe("/cases/CLM-1002");
  expect(screen.getByLabelText("Waiting: 1")).toBeDefined();
  expect(screen.getByLabelText("Decided: 1")).toBeDefined();
  expect(screen.getByLabelText("In progress: 0")).toBeDefined();
  const row = screen.getByRole("row", { name: /CLM-1003/ });
  expect(within(row).getByText("Approved")).toBeDefined();
  expect(within(row).getByText("$420.00")).toBeDefined();
  expect(screen.getAllByText("$1,150.00")).toHaveLength(2);
  expect(screen.getAllByText("Jul 20, 2026")).toHaveLength(2);
});

it("shows an error when the queue can't load", async () => {
  stubApi({ "GET /api/cases": new Refusal(500, "The backend is down") });
  renderAt("/");
  expect((await screen.findByRole("alert")).textContent).toBe(
    "The backend is down",
  );
});

it("shows a case in full", async () => {
  stubApi({
    "GET /api/cases/CLM-1002": case,
    "GET /api/contracts/POL-2002": contract,
    "GET /api/customers/CUS-3002/cases": history,
  });
  renderAt("/cases/CLM-1002");
  expect(await screen.findByText(case.story)).toBeDefined();
  expect(
    screen.getByRole("heading", { name: case.summary, level: 1 }),
  ).toBeDefined();
  expect(screen.getByText("Wool suit")).toBeDefined();
  const total = screen.getByRole("rowheader", { name: "Total" }).closest("tr");
  expect(total?.textContent).toContain("$1,150.00");
  expect(screen.getByText("One checked bag not delivered.")).toBeDefined();
  expect(screen.getByText("Carrier report")).toBeDefined();
  expect(await screen.findByText("Premium")).toBeDefined();
  expect(screen.getByText("Electronics Plus")).toBeDefined();
  expect(
    screen.getByText("Prague, Czech Republic, Jun 20, 2026 to Jun 30, 2026"),
  ).toBeDefined();
  expect(
    await screen.findByText("Checked bag arrived 30 hours late in Lisbon"),
  ).toBeDefined();
  expect(screen.getByText("Waiting")).toBeDefined();
});

it("shows a contract without add-ons and a customer with no earlier cases", async () => {
  stubApi({
    "GET /api/cases/CLM-1002": case,
    "GET /api/contracts/POL-2002": { ...contract, add_ons: [] },
    "GET /api/customers/CUS-3002/cases": [],
  });
  renderAt("/cases/CLM-1002");
  expect(await screen.findByText("None")).toBeDefined();
  expect(await screen.findByText("No earlier cases")).toBeDefined();
});

it("says when a case doesn't exist, and stops asking for it", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const fetchMock = stubApi({});
  renderAt("/cases/CLM-9999");
  expect(await screen.findByText("Case not found")).toBeDefined();
  await vi.advanceTimersByTimeAsync(5000);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  vi.useRealTimers();
});

it("shows other errors loading a case", async () => {
  stubApi({ "GET /api/cases/CLM-1002": new Refusal(500, "Server error") });
  renderAt("/cases/CLM-1002");
  expect((await screen.findByRole("alert")).textContent).toBe("Server error");
});

it("shows the agent's instructions read only", async () => {
  stubApi({ "GET /api/instructions": { text: "# CRM Agent" } });
  renderAt("/instructions");
  expect(await screen.findByText("# CRM Agent")).toBeDefined();
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(screen.queryByRole("button")).toBeNull();
});

it("says when a page doesn't exist", () => {
  stubApi({});
  renderAt("/nowhere");
  expect(screen.getByText("Page not found")).toBeDefined();
});
