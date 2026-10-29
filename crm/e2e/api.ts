import { type APIRequestContext, expect } from "@playwright/test";
import type { DecisionKind, EvaluationSet, Run } from "../dashboard/src/api";

// Stands in for the agent's service and its case agents, with one function for
// each backend operation the tests use, sent through the dashboard's proxy.
type Request = APIRequestContext;

const MODEL = { model: "openai/gpt-6-luna", reasoning_effort: "low" };
const casePath = (caseId: string) => `/api/cases/${encodeURIComponent(caseId)}`;
const runPath = (runId: string) => `/api/runs/${runId}`;

async function send(
  request: Request,
  method: "POST" | "PUT",
  path: string,
  data: object = {},
) {
  const response = await request.fetch(path, { method, data });
  await expect(response).toBeOK();
  return response;
}

export const startCase = (request: Request, caseId: string, thread: string) =>
  send(request, "POST", `${casePath(caseId)}/start`, { thread_id: thread });

export const recordStep = (
  request: Request,
  caseId: string,
  kind: "tool_call" | "tool_result" | "message" | "reading",
  content: string,
) => send(request, "POST", `${casePath(caseId)}/steps`, { kind, content });

export const recordDecision = (
  request: Request,
  caseId: string,
  decision: {
    decision: DecisionKind;
    award: number;
    section: string;
    reason: string;
  },
) => send(request, "POST", `${casePath(caseId)}/decision`, decision);

// Asks to pay a case and returns the backend's answer, which may be a refusal.
export const askToPay = (request: Request, caseId: string, amount: number) =>
  request.post(`${casePath(caseId)}/payment`, { data: { amount } });

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
    ...MODEL,
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
    ...MODEL,
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

// The stand-in for the agent's service, which Playwright starts on its own port.
export const AGENT_STAND_IN = "http://127.0.0.1:8003";

export async function resumed(request: Request): Promise<string[]> {
  const response = await request.get(`${AGENT_STAND_IN}/api/resumed`);
  await expect(response).toBeOK();
  return (await response.json()) as string[];
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
