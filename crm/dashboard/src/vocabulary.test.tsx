import { cleanup, render, screen } from "@testing-library/react";
import { afterEach } from "vitest";
import { expect, it } from "vitest";
import {
  type Vocabulary,
  PackWordsContext,
  awardText,
  fieldText,
  useAwardFormat,
  useLabel,
} from "./vocabulary";

// The words a library pack serves, as /api/pack carries them.
const library: Vocabulary = {
  labels: {
    "case.incident": "Received at",
    "decision.approve": "Issued",
    "not_allowed.text":
      "Only a librarian over {limit} can {action}. {worker} can't.",
  },
  contract: {
    title: "Membership",
    rows: [
      { label: "Card", field: "contract_id", format: "text" },
      { label: "Tier", field: "plan", format: "text" },
      { label: "Members on the card", field: "travelers", format: "list" },
      {
        label: "The card",
        template: "{trip.destination}, {trip.departs_on} to {trip.returns_on}",
        formats: {
          "trip.destination": "text",
          "trip.departs_on": "date",
          "trip.returns_on": "date",
        },
      },
      { label: "Add-ons", field: "add_ons", format: "list", empty: "None" },
      { label: "Loans held today", field: "active_loans", format: "days" },
    ],
  },
  award_format: "days",
  messages: {},
};

const record = {
  contract_id: "MEM-5001",
  plan: "standard",
  travelers: ["Marta Voss"],
  trip: {
    destination: "Northgate Public Library, Central branch",
    departs_on: "2026-02-10",
    returns_on: "2027-02-10",
    trip_cost: 0,
  },
  add_ons: [],
  active_loans: 2,
};

// A panel that reads the pack's words, the way the pages do.
function Probe({ text, award }: Readonly<{ text?: string; award?: number }>) {
  const label = useLabel();
  const format = useAwardFormat();
  return (
    <p>
      {text && <span data-testid="word">{label(text, "Fallback words")}</span>}
      {award !== undefined && (
        <span data-testid="award">{awardText(award, format)}</span>
      )}
    </p>
  );
}

afterEach(cleanup);

function inPack(ui: React.ReactNode, vocabulary: Vocabulary | null = library) {
  return render(
    <PackWordsContext.Provider value={{ vocabulary }}>
      {ui}
    </PackWordsContext.Provider>,
  );
}

it("shows the pack's word for a key", () => {
  inPack(<Probe text="case.incident" />);
  expect(screen.getByTestId("word").textContent).toBe("Received at");
});

it("shows the fallback when the pack names no key", () => {
  inPack(<Probe text="case.unknown" />);
  expect(screen.getByTestId("word").textContent).toBe("Fallback words");
});

it("renders an award in the pack's unit", () => {
  inPack(<Probe award={14} />);
  expect(screen.getByTestId("award").textContent).toBe("14 days");
});

it("renders money when the pack names no format", () => {
  inPack(<Probe award={14} />, null);
  expect(screen.getByTestId("award").textContent).toBe("$14.00");
});

it("renders a contract row over the record's field", () => {
  expect(fieldText(record, "plan", "text")).toBe("Standard");
  expect(fieldText(record, "travelers", "list")).toBe("Marta Voss");
  expect(fieldText(record, "trip.departs_on", "date")).toContain("2026");
  expect(fieldText(record, "trip.trip_cost", "money")).toBe("$0.00");
  expect(fieldText(record, "active_loans", "days")).toBe("2 days");
});

it("fills a template row from several fields", () => {
  expect(
    fieldText(record, "trip.destination", "text") +
      ", " +
      fieldText(record, "trip.departs_on", "date") +
      " to " +
      fieldText(record, "trip.returns_on", "date"),
  ).toContain(
    "Northgate Public Library, Central branch, Feb 10, 2026 to Feb 10, 2027",
  );
});

it("fills the refusal templates' slots", () => {
  const word = library.labels?.["not_allowed.text"];
  expect(word).toBeTruthy();
  const sentence = (word ?? "")
    .replaceAll("{limit}", awardText(14, "days"))
    .replaceAll("{action}", "start a round")
    .replaceAll("{worker}", "Iris Bonnell");
  expect(sentence).toBe(
    "Only a librarian over 14 days can start a round. Iris Bonnell can't.",
  );
});
