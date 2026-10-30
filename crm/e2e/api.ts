import { type APIRequestContext, expect } from "@playwright/test";
import type {
  DecisionKind,
  EvaluationSet,
  Improvement,
  Run,
  Source,
  StepKind,
} from "../dashboard/src/api";
import { WORKERS, signedInAs } from "./workers";
import { AGENT_KEY_HEADERS, AGENT_STAND_IN } from "./servers";

// Stands in for the agent's service and its case agents, with one function for
// each backend operation the tests use, sent through the dashboard's proxy with
// the agent's key.
type Request = APIRequestContext;

const casePath = (caseId: string) =>
  `/api/cases/${encodeURIComponent(caseId)}`;
const runPath = (runId: string) => `/api/runs/${runId}`;

// Sends a request as the agent's side does, with its key, and returns the
// backend's answer, which may be a refusal.
const asTheAgent = (
  request: Request,
  method: "POST" | "PUT",
  path: string,
  data: object = {},
) => request.fetch(path, { method, data, headers: AGENT_KEY_HEADERS });

async function send(
  request: Request,
  method: "POST" | "PUT",
  path: string,
  data: object = {},
) {
  const response = await asTheAgent(request, method, path, data);
  await expect(response).toBeOK();
  return response;
}

export const startCase = (request: Request, caseId: string, thread: string) =>
  send(request, "POST", `${casePath(caseId)}/start`, { thread_id: thread });

// Records a step, with the context files a lookup came from, and none for any
// other step.
export const recordStep = (
  request: Request,
  caseId: string,
  kind: StepKind,
  content: string,
  sources: Source[] = [],
) =>
  send(request, "POST", `${casePath(caseId)}/steps`, {
    kind,
    content,
    sources,
  });

// Who makes the decisions the tests record, as the case agent says it.
const MAKER = "CRM Agent, version 1";

interface DecisionRequest {
  decision: DecisionKind;
  award: number;
  section: string;
  reason: string;
  decided_by: string;
}

const recordDecision = (
  request: Request,
  caseId: string,
  decision: DecisionRequest,
) => send(request, "POST", `${casePath(caseId)}/decision`, decision);

const calculateAward = (
  request: Request,
  caseId: string,
  award: { benefit: string; lines: object[]; paid_by_others: number },
) => send(request, "POST", `${casePath(caseId)}/award`, award);

// Works out the award on one emergency medical bill, which the backend keeps
// for the case's attempt, and returns what it pays.
async function awardOnABill(request: Request, caseId: string, bill: number) {
  const response = await calculateAward(request, caseId, {
    benefit: "emergency_medical",
    lines: [
      {
        description: "The covered costs",
        amount: bill,
        quantity: 1,
        kind: "expense",
        nights: 0,
        hours: 0,
      },
    ],
    paid_by_others: 0,
  });
  const { award } = (await response.json()) as { award: number };
  return award;
}

// Records a decision as the case agent does, with its maker. An approval's
// award is worked out first: a bill for the award alone shows the plan's
// deductible, and a bill for the award and the deductible leaves exactly the
// award on file.
export async function decide(
  request: Request,
  caseId: string,
  decision: Omit<DecisionRequest, "decided_by">,
) {
  if (decision.decision === "approve") {
    const deductible =
      decision.award -
      (await awardOnABill(request, caseId, decision.award));
    await awardOnABill(request, caseId, decision.award + deductible);
  }
  return recordDecision(request, caseId, { ...decision, decided_by: MAKER });
}

// Asks to pay a case and returns the backend's answer, which may be a refusal.
export const askToPay = (request: Request, caseId: string, amount: number) =>
  asTheAgent(request, "POST", `${casePath(caseId)}/payment`, { amount });

export async function payCase(
  request: Request,
  caseId: string,
  amount: number,
) {
  await expect(await askToPay(request, caseId, amount)).toBeOK();
}

export const failCase = (request: Request, caseId: string, reason: string) =>
  send(request, "POST", `${casePath(caseId)}/failure`, { reason });

export const recordModelCall = (
  request: Request,
  caseId: string,
  runId: string,
  cost: number,
) =>
  send(request, "POST", `${casePath(caseId)}/model-calls`, {
    run_id: runId,
    input_tokens: 1200,
    output_tokens: 300,
    cost,
  });

export const recordWorkTime = (
  request: Request,
  caseId: string,
  runId: string,
  seconds: number,
) =>
  send(request, "POST", `${casePath(caseId)}/work-times`, {
    run_id: runId,
    seconds,
  });

export async function createDispatch(
  request: Request,
  agents: number,
): Promise<Run> {
  const response = await send(request, "POST", "/api/runs/dispatches", {
    agents,
  });
  return (await response.json()) as Run;
}

export async function createEvaluation(
  request: Request,
  evaluationSet: EvaluationSet,
  tiny: boolean,
  agents: number,
): Promise<Run> {
  const response = await send(request, "POST", "/api/runs/evaluations", {
    evaluation_set: evaluationSet,
    tiny,
    agents,
  });
  return (await response.json()) as Run;
}

export const recordRunCases = (
  request: Request,
  runId: string,
  caseIds: string[],
) => send(request, "PUT", `${runPath(runId)}/cases`, { case_ids: caseIds });

export const finishRun = (request: Request, runId: string) =>
  send(request, "POST", `${runPath(runId)}/finish`);

// A round of the improver, played out as the agent's service would record it,
// for Dana Whitfield.
const ROUNDS = "/api/rounds";
const roundPath = (roundId: string) => `${ROUNDS}/${roundId}`;
const DANA = WORKERS.dana.worker_id;

export async function createRound(request: Request): Promise<string> {
  const response = await send(request, "POST", ROUNDS, { worker_id: DANA });
  return ((await response.json()) as { round_id: string }).round_id;
}

export async function recordChangeProposal(
  request: Request,
  roundId: string,
  instructions: string,
): Promise<string> {
  const response = await send(
    request,
    "POST",
    `${roundPath(roundId)}/proposals/change`,
    {
      instructions,
      model: "openai/gpt-6-luna",
      reasoning_effort: "low",
      reason: "Two stolen phones were approved without a police report",
    },
  );
  return ((await response.json()) as { proposal_id: string }).proposal_id;
}

export async function recordRecipeProposal(
  request: Request,
  roundId: string,
): Promise<string> {
  const response = await send(
    request,
    "POST",
    `${roundPath(roundId)}/proposals/recipe`,
    { recipe: "1. Read the results.\n", reason: "A shorter recipe" },
  );
  return ((await response.json()) as { proposal_id: string }).proposal_id;
}

export const recordReview = (
  request: Request,
  roundId: string,
  proposalId: string,
  review: "approved" | "rejected",
  reason = "",
) =>
  send(
    request,
    "POST",
    `${roundPath(roundId)}/proposals/${proposalId}/review`,
    { review, worker_id: DANA, reason },
  );

export const createVersion = (request: Request, roundId: string) =>
  send(request, "POST", `${roundPath(roundId)}/version`);

export const finishRound = (request: Request, roundId: string) =>
  send(request, "POST", `${roundPath(roundId)}/finish`);

// Finishes the open round, if any, rejecting a proposal it's waiting on first,
// so the next test can start one. It reads the round as Dana, as the dashboard
// does.
export async function finishOpenRound(request: Request) {
  const response = await request.get("/api/improvement", {
    headers: await signedInAs(request, WORKERS.dana),
  });
  await expect(response).toBeOK();
  const { round } = (await response.json()) as Improvement;
  if (round?.status !== "open") return;
  if (round.waiting)
    await recordReview(
      request,
      round.round_id,
      round.waiting.proposal_id,
      "rejected",
      "The test is over",
    );
  await finishRound(request, round.round_id);
}

export interface Started {
  path: string;
  body: unknown;
}

export async function started(request: Request): Promise<Started[]> {
  const response = await request.get(`${AGENT_STAND_IN}/api/started`);
  await expect(response).toBeOK();
  return (await response.json()) as Started[];
}

export async function reviews(request: Request): Promise<Started[]> {
  const response = await request.get(`${AGENT_STAND_IN}/api/reviews`);
  await expect(response).toBeOK();
  return (await response.json()) as Started[];
}
