export type Status =
  "waiting" | "in_progress" | "waiting_for_sign_off" | "decided";
export type DecisionKind = "approve" | "decline" | "refer";
export type StepKind = "tool_call" | "tool_result" | "message";

export interface CaseSummary {
  case_id: string;
  customer_name: string;
  case_type: string;
  summary: string;
  amount_claimed: number;
  submitted_on: string;
  status: Status;
  decision: DecisionKind | null;
  award: number | null;
}

export interface Item {
  description: string;
  category: string;
  amount: number;
}

export interface CaseDocument {
  name: string;
  type: string;
  content: string;
}

export interface Decision {
  decision: DecisionKind;
  award: number;
  section: string;
  reason: string;
  decided_at: string;
}

export interface Payment {
  amount: number;
  paid_at: string;
  signed_off_by: string | null;
}

export interface Case {
  case_id: string;
  contract_id: string;
  customer_id: string;
  customer_name: string;
  case_type: string;
  submitted_on: string;
  incident_date: string;
  incident_location: string;
  summary: string;
  story: string;
  items: Item[];
  amount_claimed: number;
  documents: CaseDocument[];
  status: Status;
  thread_id: string | null;
  decision: Decision | null;
  payment: Payment | null;
}

export interface Contract {
  contract_id: string;
  customer_id: string;
  plan: string;
  add_ons: string[];
  purchased_on: string;
  sold_through: string;
  trip: {
    destination: string;
    departs_on: string;
    returns_on: string;
    trip_cost: number;
  };
  travelers: string[];
  status: string;
}

export interface PreviousCase {
  case_id: string;
  filed_on: string;
  incident_date: string;
  case_type: string;
  summary: string;
  outcome: string;
  amount_paid: number;
}

export interface Worker {
  worker_id: string;
  name: string;
  role: string;
  can_approve_over_limit: boolean;
}

export interface Step {
  step_id: number;
  thread_id: string;
  kind: StepKind;
  content: string;
  created_at: string;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body = (await response.json()) as { detail?: unknown };
    const detail =
      typeof body.detail === "string" ? body.detail : "The request failed";
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

function post<T>(path: string, body: object): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

const casePath = (caseId: string) =>
  `/api/cases/${encodeURIComponent(caseId)}`;

export const api = {
  listCases: () => request<CaseSummary[]>("/api/cases"),
  getCase: (caseId: string) => request<Case>(casePath(caseId)),
  listSteps: (caseId: string) =>
    request<Step[]>(`${casePath(caseId)}/steps`),
  getContract: (contractId: string) =>
    request<Contract>(`/api/contracts/${encodeURIComponent(contractId)}`),
  getCaseHistory: (customerId: string) =>
    request<PreviousCase[]>(
      `/api/customers/${encodeURIComponent(customerId)}/cases`,
    ),
  getInstructions: () => request<{ text: string }>("/api/instructions"),
  listWorkers: () => request<Worker[]>("/api/workers"),
  signOff: (caseId: string, workerId: string) =>
    post<Case>(`${casePath(caseId)}/sign-off`, { worker_id: workerId }),
};
