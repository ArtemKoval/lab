import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { LoanRequestControl } from "./LoanRequestControl";
import { pack, stubApi, type Routes } from "../testing";
import { QueuePage } from "../pages/QueuePage";
import type { LoanRequestWords } from "../vocabulary";

const WORDS: LoanRequestWords = {
  label: "Add a loan request",
  member_picker: "Member",
  membership_picker: "Membership",
  title: "Title of the loan",
  story: "The desk's note",
  price: "Replacement price",
  submit: "Add the request",
  case_type: "checkout",
  item_category: "checkout",
};

const MEMBERS = [
  { customer_id: "CUS-5001", name: "Marta Voss" },
  { customer_id: "CUS-5002", name: "Iris Bonnell" },
];

const MEMBERSHIPS = [{ contract_id: "MEM-5001" }, { contract_id: "MEM-5009" }];

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function fillAndSubmit() {
  fireEvent.click(screen.getByRole("button", { name: WORDS.label }));
  await screen.findByRole("option", { name: "Marta Voss" });
  fireEvent.change(screen.getByLabelText(WORDS.member_picker), {
    target: { value: "CUS-5001" },
  });
  await screen.findByRole("option", { name: "MEM-5001" });
  fireEvent.change(screen.getByLabelText(WORDS.membership_picker), {
    target: { value: "MEM-5001" },
  });
  fireEvent.change(screen.getByLabelText(WORDS.title), {
    target: { value: "The Lighthouse Keeper" },
  });
  fireEvent.change(screen.getByLabelText(WORDS.story), {
    target: { value: "Marta asks at the desk." },
  });
  fireEvent.change(screen.getByLabelText(WORDS.price), {
    target: { value: "24" },
  });
  fireEvent.click(screen.getByRole("button", { name: WORDS.submit }));
}

interface PostedCase {
  case_type: string;
  summary: string;
  items: { description: string; category: string; amount: number }[];
}

it("adds a request with the pack-shaped payload and reports the post", async () => {
  const routes: Routes = {
    "GET /api/customers": MEMBERS,
    "GET /api/customers/CUS-5001/contracts": MEMBERSHIPS,
    "POST /api/cases": { case_id: "LN-5009", status: "waiting" },
  };
  const fetchMock = stubApi(routes);
  const onPosted = vi.fn();
  render(<LoanRequestControl words={WORDS} onPosted={onPosted} />);
  await fillAndSubmit();
  await vi.waitFor(() => {
    expect(onPosted).toHaveBeenCalled();
  });
  const bodies = fetchMock.mock.calls.filter(([path]) => path === "/api/cases");
  expect(bodies).toHaveLength(1);
  const body = bodies[0]?.[1]?.body;
  expect(typeof body).toBe("string");
  const payload = JSON.parse(body as string) as PostedCase;
  expect(payload.case_type).toBe("checkout");
  expect(payload.summary).toBe("The Lighthouse Keeper");
  expect(payload.items[0]?.description).toBe("The Lighthouse Keeper");
  expect(payload.items[0]?.category).toBe("checkout");
  expect(payload.items[0]?.amount).toBe(24);
});

it("surfaces a server refusal in the form", async () => {
  const routes: Routes = {
    "GET /api/customers": MEMBERS,
    "GET /api/customers/CUS-5001/contracts": MEMBERSHIPS,
  };
  stubApi(routes);
  render(<LoanRequestControl words={WORDS} />);
  await fillAndSubmit();
  const refusal = await screen.findByRole("alert");
  expect(screen.getByRole("alert")).toBeDefined();
  expect(screen.getByRole("button", { name: WORDS.submit })).toBeDefined();
  expect(refusal.textContent).not.toBe("");
});

it("gates the control on the pack vocabulary", async () => {
  // The fixture pack names no loan-request key: no control renders.
  stubApi({ "GET /api/cases": [] });
  render(<QueuePage />);
  await screen.findByText("Cases queue");
  expect(screen.queryByRole("button", { name: WORDS.label })).toBeNull();
  cleanup();
  vi.unstubAllGlobals();
  // A pack that names the key gets the control.
  const withWords = {
    ...pack,
    vocabulary: { loan_request: WORDS },
  } as typeof pack;
  stubApi({ "GET /api/pack": withWords, "GET /api/cases": [] });
  render(<QueuePage />);
  await screen.findByRole("button", { name: WORDS.label });
  expect(screen.getByRole("button", { name: WORDS.label })).toBeDefined();
});
