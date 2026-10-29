export const statuses = [
  "waiting",
  "in_progress",
  "waiting_for_sign_off",
  "decided",
  "left_for_worker",
] as const;
export type Status = (typeof statuses)[number];
export type DecisionKind = "approve" | "decline" | "refer";
export type StepKind =
  "tool_call" | "tool_result" | "message" | "reading" | "error";

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
  signed_off_by: string | null;
  signed_off_at: string | null;
}

export interface Payment {
  amount: number;
  paid_at: string;
  signed_off_by: string | null;
  signed_off_at: string | null;
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
  attempts: number;
  // Set on an evaluation's copy of a case.
  evaluation_id: string | null;
  copy_of: string | null;
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

export type RunStatus = "running" | "finished" | "stopped";
export type RunKind = "dispatch" | "evaluation";
export const evaluationSets = ["evaluation", "held_out"] as const;
export type EvaluationSet = (typeof evaluationSets)[number];

export interface HeldAward {
  case_id: string;
  award: number;
}

export interface DispatchSummary {
  approved: number;
  declined: number;
  referred: number;
  waiting_for_sign_off: HeldAward[];
  left_for_worker: string[];
  // In progress or back in the queue, for the next dispatch.
  unfinished: string[];
}

// A case's line in the queue, with its cost and time in a run.
export interface RunCase extends CaseSummary {
  started_at: string | null;
  seconds: number;
  model_cost: number;
}

export interface RunDetails {
  run_id: string;
  number: number;
  kind: RunKind;
  agents: number;
  model: string;
  reasoning_effort: string;
  status: RunStatus;
  started_at: string;
  finished_at: string | null;
  seconds: number | null;
  model_cost: number;
}

export interface Run extends RunDetails {
  evaluation_set: EvaluationSet | null;
  tiny: boolean | null;
  summary: DispatchSummary | null;
  cases: RunCase[];
}

export interface Measures {
  decision_accuracy: number;
  accuracy: number;
  cost_of_mistakes: number;
  straight_through: number;
  model_cost_per_case: number;
  seconds_per_case: number;
  run_seconds: number | null;
}

// An evaluation's copy of a case beside the worker's decision on it.
export interface ScoredCase extends RunCase {
  copy_of: string;
  reason: string | null;
  worker_decision: DecisionKind;
  worker_award: number;
  right: boolean;
  mistake_cost: number;
}

export interface Evaluation extends RunDetails {
  evaluation_set: EvaluationSet;
  tiny: boolean;
  size: number;
  measures: Measures;
}

export interface ScoredEvaluation extends Evaluation {
  cases: ScoredCase[];
}

export interface Accepted {
  status: "accepted";
}

export interface Instructions {
  case: string;
}

export const REQUEST_FAILED = "The request failed";

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
    const body = (await response.json().catch(() => ({}))) as {
      detail?: unknown;
    };
    const detail =
      typeof body.detail === "string" ? body.detail : REQUEST_FAILED;
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

const casePath = (caseId: string) => `/api/cases/${encodeURIComponent(caseId)}`;
const DISPATCHES = "/api/dispatches";
const EVALUATIONS = "/api/evaluations";

export const api = {
  listCases: () => request<CaseSummary[]>("/api/cases"),
  getCase: (caseId: string) => request<Case>(casePath(caseId)),
  listSteps: (caseId: string) => request<Step[]>(`${casePath(caseId)}/steps`),
  getContract: (contractId: string) =>
    request<Contract>(`/api/contracts/${encodeURIComponent(contractId)}`),
  getCaseHistory: (customerId: string) =>
    request<PreviousCase[]>(
      `/api/customers/${encodeURIComponent(customerId)}/cases`,
    ),
  getInstructions: () => request<Instructions>("/api/instructions"),
  listWorkers: () => request<Worker[]>("/api/workers"),
  getLatestDispatch: () => request<Run | null>(`${DISPATCHES}/latest`),
  startDispatch: (agents: number) => post<Accepted>(DISPATCHES, { agents }),
  listEvaluations: () => request<Evaluation[]>(EVALUATIONS),
  getEvaluation: (runId: string) =>
    request<ScoredEvaluation>(`${EVALUATIONS}/${encodeURIComponent(runId)}`),
  startEvaluation: (
    evaluationSet: EvaluationSet,
    tiny: boolean,
    agents: number,
  ) =>
    post<Accepted>(EVALUATIONS, {
      evaluation_set: evaluationSet,
      tiny,
      agents,
    }),
  signOff: (caseId: string, workerId: string) =>
    post<Case>(`${casePath(caseId)}/sign-off`, { worker_id: workerId }),
};
