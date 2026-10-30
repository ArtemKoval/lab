import { type APIRequestContext, expect } from "@playwright/test";
import type {
  DecisionKind,
  EvaluationSet,
  RoundStatus,
  Run,
  StepKind,
} from "../dashboard/src/api";
import type { Source } from "../dashboard/src/sources";
import { WORKERS, signedInAs } from "./workers";
import { roundPath, runPath } from "./paths";
import { AGENT_KEY_HEADERS, AGENT_STAND_IN } from "./servers";

// Stands in for the agent and its case agents, with one function for each
// backend operation the tests use, sent through the dashboard's proxy with the
// agent's key.
type Request = APIRequestContext;

const casePath = (caseId: string) => `/api/cases/${encodeURIComponent(caseId)}`;

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
      decision.award - (await awardOnABill(request, caseId, decision.award));
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

// Takes a sent-back case back into work, for a dispatch's run or, with none,
// for a resume.
export const takeCase = (
  request: Request,
  caseId: string,
  runId: string | null,
) => send(request, "POST", `${casePath(caseId)}/take`, { run_id: runId });

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

// A run as the agent reads it.
export async function getRun(request: Request, runId: string): Promise<Run> {
  const response = await request.get(runPath(runId), {
    headers: AGENT_KEY_HEADERS,
  });
  await expect(response).toBeOK();
  return (await response.json()) as Run;
}

// Starts a run as a worker does, and returns it as the agent reads it.
async function startRun(
  request: Request,
  path: string,
  data: object,
): Promise<Run> {
  const before = (await started(request)).length;
  const response = await request.post(path, {
    data,
    headers: await signedInAs(request, WORKERS.dana),
  });
  await expect(response).toBeOK();
  const { run_id } = await nextStarted(request, before);
  return getRun(request, String(run_id));
}

export const startDispatch = (request: Request, agents: number) =>
  startRun(request, "/api/dispatches", { agents });

export const startEvaluation = (
  request: Request,
  evaluationSet: EvaluationSet,
  tiny: boolean,
  agents: number,
) =>
  startRun(request, "/api/evaluations", {
    evaluation_set: evaluationSet,
    tiny,
    agents,
  });

export const recordRunCases = (
  request: Request,
  runId: string,
  caseIds: string[],
) => send(request, "PUT", `${runPath(runId)}/cases`, { case_ids: caseIds });

export const finishRun = (request: Request, runId: string) =>
  send(request, "POST", `${runPath(runId)}/finish`);

// A round of the improver, started by Dana Whitfield and played out as the
// agent would record it.
export async function startRound(request: Request): Promise<string> {
  const before = (await started(request)).length;
  const response = await request.post("/api/improvement/rounds", {
    headers: await signedInAs(request, WORKERS.dana),
  });
  await expect(response).toBeOK();
  return String((await nextStarted(request, before)).round_id);
}

// A round as the agent reads it, as far as the tests need.
export async function getRound(
  request: Request,
  roundId: string,
): Promise<{ round_id: string; number: number; status: RoundStatus }> {
  const response = await request.get(roundPath(roundId), {
    headers: AGENT_KEY_HEADERS,
  });
  await expect(response).toBeOK();
  return (await response.json()) as {
    round_id: string;
    number: number;
    status: RoundStatus;
  };
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

// A proposal with its review, as the agent reads it.
export async function getProposal(
  request: Request,
  roundId: string,
  proposalId: string,
): Promise<{ review: string | null; rejection_reason: string | null }> {
  const response = await request.get(
    `${roundPath(roundId)}/proposals/${proposalId}`,
    { headers: AGENT_KEY_HEADERS },
  );
  await expect(response).toBeOK();
  return (await response.json()) as {
    review: string | null;
    rejection_reason: string | null;
  };
}

export const createVersion = (request: Request, roundId: string) =>
  send(request, "POST", `${roundPath(roundId)}/version`);

// Stops the runs and rounds the tests started that are still going, through
// the stand-in for the agent, so the next test can start its own.
export async function stopTheWork(request: Request) {
  const response = await request.post(`${AGENT_STAND_IN}/api/stop`);
  await expect(response).toBeOK();
}

// A payload the backend sent the agent, naming its operation.
export type Payload = { operation: string } & Record<string, unknown>;

// Every payload the stand-in for the agent took, oldest first.
export async function started(request: Request): Promise<Payload[]> {
  const response = await request.get(`${AGENT_STAND_IN}/api/started`);
  await expect(response).toBeOK();
  return (await response.json()) as Payload[];
}

// Waits for the stand-in for the agent to take exactly one payload more than
// the `before` it had, and returns that payload.
export async function nextStarted(
  request: Request,
  before: number,
): Promise<Payload> {
  let payloads: Payload[] = [];
  await expect
    .poll(async () => {
      payloads = await started(request);
      return payloads.length;
    })
    .toBe(before + 1);
  const next = payloads.at(before);
  if (!next) throw new Error("The stand-in for the agent took nothing");
  return next;
}

// The cases the backend has asked the agent to resume, oldest first.
export async function resumes(request: Request): Promise<unknown[]> {
  return (await started(request))
    .filter((payload) => payload.operation === "resume_case")
    .map((payload) => payload.case_id);
}
