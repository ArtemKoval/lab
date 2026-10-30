// Stands in for the Copilot's AgentCore app in the end-to-end tests: it answers
// /ping and the health check, and takes each turn and each answer to a
// confirmation the backend posts to /invocations, with no key. It then plays a
// scripted turn through the backend with the worker's sign-in it was given:
// it checks the sign-in with /api/me, stopping if it's refused, reads the
// turn's message, records its cards and answers, as the Copilot does.
import { createServer } from "node:http";
import { json } from "node:stream/consumers";
import { reply } from "./stand_in.ts";

interface Payload {
  operation: string;
  conversation_id: string;
  turn_id: string;
  sign_in: string;
}

interface Turn {
  turn_id: string;
  message: string;
  confirmation_answer: string | null;
  canceled_because: string | null;
  confirmation: { case_id: string; award: number } | null;
}

const app = process.env.CRM_API ?? "";
// A pause between steps, so the sidebar shows each card working.
const STEP_MS = 250;
const SOURCE = {
  file: "wording.md",
  system: "Contract administration",
  owner: "Head of product",
  reviewed: "2026-09-01",
};
// The case the scripted turn links to, and the one it tries to send back, which
// isn't held, so the app refuses.
const LINKED = "CLM-1009";
const ANSWER = [
  `I started a dispatch and looked at the wording. ${LINKED} is worth a look.`,
  "",
  "| What | Where it stands |",
  "| --- | --- |",
  "| The dispatch | Started with 3 case agents |",
  `| ${LINKED} | Not held, so it can't be sent back |`,
].join("\n");

const pause = () => new Promise((resolve) => setTimeout(resolve, STEP_MS));

// Sends one request to the backend as the worker, with their sign-in.
async function asTheWorker(
  signIn: string,
  method: string,
  path: string,
  body?: object,
) {
  const response = await fetch(`${app}/api${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${signIn}`,
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const answer = (await response.json()) as Record<string, unknown>;
  return { ok: response.ok, answer };
}

// Records a card for one step, as it starts and again as it ends.
async function card(
  payload: Payload,
  started: { tool: string; kind: string; input: string },
  step: () => Promise<{ ok: boolean; answer: Record<string, unknown> }>,
  sources: object[] = [],
) {
  const turn = `/copilot/turns/${payload.turn_id}`;
  const asked = JSON.stringify({ input: started.input });
  const { answer: made } = await asTheWorker(
    payload.sign_in,
    "POST",
    `${turn}/steps`,
    { ...started, asked },
  );
  await pause();
  const { ok, answer } = await step();
  const result = ok
    ? { status: "done", answer: JSON.stringify(answer), reason: null, sources }
    : {
        status: "refused",
        answer: null,
        reason: String(answer.detail),
        sources: [],
      };
  await asTheWorker(
    payload.sign_in,
    "POST",
    `${turn}/steps/${String(made.step_id)}/finish`,
    result,
  );
  return ok;
}

async function finish(payload: Payload, answer: string) {
  await asTheWorker(
    payload.sign_in,
    "POST",
    `/copilot/turns/${payload.turn_id}/finish`,
    { answer, model_calls: 3, cost: 0.0021 },
  );
}

// The turn the app asked about, read with the worker's sign-in once the app
// says the sign-in is a worker's, as the Copilot checks it.
async function theTurn(payload: Payload): Promise<Turn> {
  const me = await asTheWorker(payload.sign_in, "GET", "/me");
  if (!me.ok)
    throw new Error(`The sign-in was refused: ${String(me.answer.detail)}`);
  const { answer } = await asTheWorker(
    payload.sign_in,
    "GET",
    `/copilot/conversations/${payload.conversation_id}`,
  );
  const turn = (answer.turns as Turn[]).find(
    (each) => each.turn_id === payload.turn_id,
  );
  if (!turn) throw new Error(`No turn ${payload.turn_id}`);
  return turn;
}

// A message: a sign-off asked for pauses for the worker's confirmation; any
// other gets a lookup, an action, a refusal and a formatted answer.
async function takeTurn(payload: Payload) {
  const { message } = await theTurn(payload);
  const asked = /sign off (CLM-\d{4})/i.exec(message);
  if (asked) {
    const caseId = asked[1];
    await card(
      payload,
      { tool: "get_case", kind: "cases", input: caseId },
      () => asTheWorker(payload.sign_in, "GET", `/cases/${caseId}`),
    );
    await asTheWorker(
      payload.sign_in,
      "POST",
      `/copilot/turns/${payload.turn_id}/pause`,
      { case_id: caseId },
    );
    return;
  }
  await card(
    payload,
    { tool: "read_section", kind: "context", input: "wording 3" },
    () => Promise.resolve({ ok: true, answer: { title: "Trip delay" } }),
    [SOURCE],
  );
  await card(
    payload,
    { tool: "start_dispatch", kind: "action", input: "3" },
    () => asTheWorker(payload.sign_in, "POST", "/dispatches", { agents: 3 }),
  );
  await card(
    payload,
    { tool: "send_back_case", kind: "action", input: LINKED },
    () =>
      asTheWorker(payload.sign_in, "POST", `/cases/${LINKED}/send-back`, {
        note: "Check the receipts again.",
      }),
  );
  await pause();
  await finish(payload, ANSWER);
}

// The worker's answer to a confirmation, read from the app's record of the
// turn: a Sign off signs the case off as the worker, which pays it.
async function answerConfirmation(payload: Payload) {
  const turn = await theTurn(payload);
  const caseId = turn.confirmation?.case_id ?? "";
  if (turn.confirmation_answer !== "sign_off") {
    await finish(
      payload,
      turn.canceled_because
        ? "The case changed since the card was shown, so I canceled this sign-off without making a payment. Please ask again."
        : `I haven't signed off ${caseId}. What would you like to do instead?`,
    );
    return;
  }
  const paid = await card(
    payload,
    { tool: "sign_off_case", kind: "action", input: caseId },
    () => asTheWorker(payload.sign_in, "POST", `/cases/${caseId}/sign-off`),
  );
  await finish(
    payload,
    paid
      ? `Signed off and paid ${caseId}.`
      : `I couldn't sign off ${caseId}.`,
  );
}

createServer((request, response) => {
  const url = request.url ?? "";
  if (request.method === "POST" && url === "/invocations") {
    json(request).then(
      (body) => {
        const payload = body as Payload;
        if (payload.operation === "health") {
          reply(response, 200, { healthy: true });
          return;
        }
        reply(response, 200, { accepted: true });
        const work =
          payload.operation === "take_turn" ? takeTurn : answerConfirmation;
        work(payload).catch((error: unknown) => {
          console.error(error);
        });
      },
      () => {
        reply(response, 400, { error: "Invalid JSON" });
      },
    );
  } else if (url === "/ping") {
    reply(response, 200, { status: "Healthy" });
  } else {
    reply(response, 404, { error: "Not found" });
  }
}).listen(Number(process.env.PORT), "127.0.0.1");
