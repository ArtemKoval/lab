import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Case, Worker } from "./api";
import { approval, approved } from "./caseTesting";
import { ResolutionForm } from "./components/ResolutionForm";
import { dana, marcus, sent } from "./testing";
import { PackWordsContext } from "./vocabulary";
import { WorkerContext } from "./worker";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// A referred request, as the agent left it: decided, with the referral as
// the decision of record.
const referred: Case = {
  ...approved,
  status: "decided",
  decision: {
    ...approval,
    decision: "refer",
    section: "Loan rule 7",
    reason: "The title sits on the special collection shelves.",
    payload: null,
  },
  effect: null,
};

const libraryWords = {
  labels: {
    "resolution.issue": "Issue the loan",
    "resolution.decline": "Decline the request",
    "resolution.days": "Days",
    "resolution.reason": "The lead's reason",
  },
  award_format: "days" as const,
};

function renderFor(worker: Worker, posted: () => void) {
  return render(
    <WorkerContext.Provider value={worker}>
      <PackWordsContext.Provider value={{ vocabulary: libraryWords }}>
        <ResolutionForm entry={referred} onResolved={posted} />
      </PackWordsContext.Provider>
    </WorkerContext.Provider>,
  );
}

it("shows the lead the two actions with the loan desk's words", () => {
  renderFor(dana, vi.fn());
  expect(screen.getByRole("button", { name: "Issue the loan" })).toBeTruthy();
  expect(
    screen.getByRole("button", { name: "Decline the request" }),
  ).toBeTruthy();
  expect(screen.getByLabelText("Days")).toBeTruthy();
});

it("shows nothing to a worker who cannot sign off over the limit", () => {
  renderFor(marcus, vi.fn());
  expect(screen.queryByRole("button", { name: "Issue the loan" })).toBeNull();
});

it("issues the loan with the term in days", async () => {
  const posted = vi.fn();
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify(referred), { status: 200 })),
  );
  vi.stubGlobal("fetch", fetchMock);
  renderFor(dana, posted);
  fireEvent.change(screen.getByLabelText("Days"), {
    target: { value: "21" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Issue the loan" }));
  await vi.waitFor(() => {
    expect(sent(fetchMock, "POST /api/cases/CLM-1002/resolution")).toEqual([
      { resolution: "loan", days: 21, reason: "", benefit: "" },
    ]);
    expect(posted).toHaveBeenCalled();
  });
});

it("declines with the lead's reason", async () => {
  const posted = vi.fn();
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify(referred), { status: 200 })),
  );
  vi.stubGlobal("fetch", fetchMock);
  renderFor(dana, posted);
  fireEvent.change(screen.getByLabelText("The lead's reason"), {
    target: { value: "The title stays in the building." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Decline the request" }));
  await vi.waitFor(() => {
    expect(sent(fetchMock, "POST /api/cases/CLM-1002/resolution")).toEqual([
      {
        resolution: "decline",
        days: 14,
        reason: "The title stays in the building.",
        benefit: "",
      },
    ]);
    expect(posted).toHaveBeenCalled();
  });
});
