import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Case, Worker } from "./api";
import { entry } from "./testing";
import { DeskDecisionForm } from "./components/DeskDecisionForm";
import { WorkerContext } from "./worker";
import { dana, marcus, sent } from "./testing";

afterEach(cleanup);

const waiting: Case = { ...entry, status: "waiting" };

function renderFor(worker: Worker, posted: () => void) {
  return render(
    <WorkerContext.Provider value={worker}>
      <DeskDecisionForm entry={waiting} onDecided={posted} />
    </WorkerContext.Provider>,
  );
}

it("shows the desk its three actions", () => {
  renderFor(dana, vi.fn());
  expect(
    screen.getByRole("button", { name: "Approve and issue" }),
  ).toBeTruthy();
  expect(
    screen.getByRole("button", { name: "Decline the request" }),
  ).toBeTruthy();
  expect(
    screen.getByRole("button", { name: "Refer to the lead librarian" }),
  ).toBeTruthy();
  expect(screen.getByLabelText("Amount")).toBeTruthy();
});

it("approves and issues with the term in days", async () => {
  const posted = vi.fn();
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify(waiting), { status: 200 })),
  );
  vi.stubGlobal("fetch", fetchMock);
  renderFor(dana, posted);
  fireEvent.click(screen.getByRole("button", { name: "Approve and issue" }));
  await vi.waitFor(() => {
    expect(sent(fetchMock, "POST /api/cases/CLM-1002/worker-decision")).toEqual(
      [
        {
          decision: "approve",
          days: 14,
          reason: "",
          section: "The rules the desk relied on",
          benefit: "",
        },
      ],
    );
    expect(posted).toHaveBeenCalled();
  });
});

it("refers to the lead librarian", async () => {
  const posted = vi.fn();
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify(waiting), { status: 200 })),
  );
  vi.stubGlobal("fetch", fetchMock);
  renderFor(dana, posted);
  fireEvent.click(
    screen.getByRole("button", { name: "Refer to the lead librarian" }),
  );
  await vi.waitFor(() => {
    const [body] = sent(
      fetchMock,
      "POST /api/cases/CLM-1002/worker-decision",
    ) as { decision: string }[];
    expect(body.decision).toBe("refer");
    expect(posted).toHaveBeenCalled();
  });
});

it("shows every worker the form, the desk decides as itself", () => {
  renderFor(marcus, vi.fn());
  expect(
    screen.getByRole("button", { name: "Approve and issue" }),
  ).toBeTruthy();
});
