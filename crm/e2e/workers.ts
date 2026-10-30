import { expect } from "@playwright/test";
// The workers the end-to-end tests sign in as, read from the active pack so
// the identities stay the pack's own, with the password the Auth stand-in
// signs every worker in with, and where each one's signed-in browser storage
// is kept for the tests.
import { readFileSync } from "node:fs";

export const TEST_PASSWORD = "e2e-worker-password";

// The address of the Auth stand-in the playwright config starts.
export const AUTH_STAND_IN =
  process.env.AUTH_STAND_IN_URL ?? "http://127.0.0.1:8004";

interface PackWorker {
  worker_id: string;
  name: string;
  email: string;
}

const pack_workers = JSON.parse(
  readFileSync("domains/insurance/data/workers.json", "utf8"),
) as PackWorker[];

const STORAGE: Record<string, string> = {
  "dana.whitfield@undercover.example": "e2e/.auth/dana.json",
  "marcus.oyelaran@undercover.example": "e2e/.auth/marcus.json",
  "priya.raman@undercover.example": "e2e/.auth/priya.json",
};

function key_of(email: string): string {
  return email.split("@")[0].split(".")[0];
}

export const WORKERS = Object.fromEntries(
  pack_workers.map((worker) => [
    key_of(worker.email),
    {
      worker_id: worker.worker_id,
      name: worker.name,
      email: worker.email,
      storage:
        STORAGE[worker.email] ?? `e2e/.auth/${key_of(worker.email)}.json`,
    },
  ]),
);

// Signs a request in as the worker, through the Auth stand-in's own contract.
export async function signedInAs(
  request: import("@playwright/test").APIRequestContext,
  worker: { email: string },
) {
  const response = await request.post(`${AUTH_STAND_IN}/signin`, {
    data: { email: worker.email, password: TEST_PASSWORD },
  });
  await expect(response).toBeOK();
  const { access_token } = (await response.json()) as { access_token: string };
  return { Authorization: `Bearer ${access_token}` };
}
