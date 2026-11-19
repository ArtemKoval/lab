import { cleanup, render, screen } from "@testing-library/react";
import { afterEach } from "vitest";
import { expect, it, vi } from "vitest";
import { PackWordsContext, type Vocabulary } from "./vocabulary";
import { ContractPanel } from "./components/ContractPanels";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// The words the library pack serves, as /api/pack carries them.
const library: Vocabulary = {
  labels: {},
  contract: {
    title: "Membership",
    rows: [
      { label: "Card", field: "contract_id", format: "text" },
      { label: "Tier", field: "plan", format: "text" },
      {
        label: "Members on the card",
        field: "travelers",
        format: "list",
      },
      {
        label: "Home branch",
        field: "trip.destination",
        format: "text",
      },
      { label: "Loans held today", field: "active_loans", format: "days" },
    ],
  },
  award_format: "days",
  messages: {},
};

const membership = {
  contract_id: "MEM-5001",
  plan: "standard",
  travelers: ["Marta Voss"],
  trip: {
    destination: "Northgate Public Library, Central branch",
    departs_on: "2026-02-10",
    returns_on: "2027-02-10",
    trip_cost: 0,
  },
  active_loans: 2,
};

function renderPanel() {
  return render(
    <PackWordsContext.Provider value={{ vocabulary: library }}>
      <ContractPanel contractId="MEM-5001" />
    </PackWordsContext.Provider>,
  );
}

function stubContract(body: object) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify(body), { status: 200 })),
    ),
  );
}

it("renders the library membership card from the pack's rows", async () => {
  stubContract(membership);
  renderPanel();
  await screen.findByText("MEM-5001");
  expect(screen.getByRole("heading", { name: "Membership" })).toBeTruthy();
  expect(screen.getByText("Card")).toBeTruthy();
  expect(screen.getByText("Tier")).toBeTruthy();
  expect(screen.getByText("Standard")).toBeTruthy();
  expect(screen.getByText("Members on the card")).toBeTruthy();
  expect(
    screen.getByText("Northgate Public Library, Central branch"),
  ).toBeTruthy();
  expect(screen.getByText("2 days")).toBeTruthy();
});

it("a row whose field holds nothing stays hidden", async () => {
  const hollow = { ...membership, travelers: [] };
  stubContract(hollow);
  renderPanel();
  await screen.findByText("MEM-5001");
  expect(screen.queryByText("Members on the card")).toBeNull();
  expect(screen.getByText("Tier")).toBeTruthy();
});
