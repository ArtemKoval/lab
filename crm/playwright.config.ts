import { defineConfig } from "@playwright/test";
import {
  AGENT_KEY,
  AGENT_STAND_IN,
  BACKEND,
  AUTH_STAND_IN,
  BIND_HOST,
  COPILOT_STAND_IN,
  DASHBOARD,
  JUDGE_STAND_IN,
} from "./e2e/servers";
import { WORKERS, TEST_PASSWORD } from "./e2e/workers";

// The insurance specs pin the insurance pack's workers and cases, and each
// pack's flow spec pins that pack's. A run on one pack leaves every other
// pack's specs out. The default run stays on insurance.
const LIBRARY = process.env.CRM_DOMAIN === "library";
const GARAGE = process.env.CRM_DOMAIN === "garage";
const INSURANCE_SPECS =
  /e2e\/(agent|configuration|copilot|improvement|pages|run|scoreboard|send_back|settings|starts|tour)\.spec\.ts/;
const FLOW_SPECS: Record<string, RegExp> = {
  library: /e2e\/(library_flow|wiki_flow)\.spec\.ts/,
  garage: /e2e\/garage_flow\.spec\.ts/,
};
function activePack(): string {
  if (LIBRARY) return "library";
  if (GARAGE) return "garage";
  return "insurance";
}
function packSpecIgnore(): RegExp {
  const active = activePack();
  const parts = [INSURANCE_SPECS.source];
  for (const [name, spec] of Object.entries(FLOW_SPECS)) {
    if (name !== active) parts.push(spec.source);
  }
  return new RegExp(parts.join("|"));
}
const testIgnore = packSpecIgnore();
const PACK_ENV: Record<string, string> = {};
if (LIBRARY) PACK_ENV.CRM_DOMAIN = "library";
if (GARAGE) PACK_ENV.CRM_DOMAIN = "garage";

// The tests run their own backend and dashboard, on their own ports and
// database, so they never touch the servers started by `npm run dev`. Every
// test runs signed in as Dana Whitfield unless it chooses another worker.
export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/test-results",
  reporter: "list",
  testIgnore,
  // The test files share one database and one set of stand-ins, so they run one
  // at a time and never see each other's work part done.
  workers: 1,
  use: { baseURL: DASHBOARD },
  projects: [
    { name: "sign in", testMatch: /sign_in\.setup\.ts/ },
    {
      name: "dashboard",
      dependencies: ["sign in"],
      // The default signed-in worker is the pack's own first worker: Dana
      // Whitfield on insurance, Rosa Meridian on the library pack.
      use: {
        storageState: (
          (WORKERS.dana as { storage: string } | undefined) ??
          Object.values(WORKERS)[0]
        ).storage,
      },
    },
  ],
  webServer: [
    {
      command: `uv run -m backend.seed && uv run -m uvicorn backend.main:app --host ${BIND_HOST} --port ${new URL(BACKEND).port}`,
      url: `${BACKEND}/api/health`,
      // Empty DATABASE_URL, MODEL_NAME, CRM_AGENT_RUNTIME and
      // CRM_COPILOT_RUNTIME keep the tests on SQLite, the default model and
      // the stand-ins for the agent and the Copilot, whatever the shell has.
      // CRM_DOMAIN passes through only when the run names a non-default
      // pack, because an empty value would not fall back to the default pack.
      env: {
        CRM_DB: "e2e/crm.db",
        ...PACK_ENV,
        DATABASE_URL: "",
        MODEL_NAME: "",
        CRM_AGENT_SERVICE: AGENT_STAND_IN,
        CRM_AGENT_RUNTIME: "",
        CRM_COPILOT: COPILOT_STAND_IN,
        CRM_COPILOT_RUNTIME: "",
        VITE_AUTH_URL: AUTH_STAND_IN,
        AUTH_URL: AUTH_STAND_IN,
        JUDGE_URL: JUDGE_STAND_IN,
        OPENROUTER_API_KEY: "e2e-key",
        CRM_AGENT_KEY: AGENT_KEY,
      },
    },
    {
      command: "node e2e/judge_stand_in.ts",
      url: `${JUDGE_STAND_IN}/health`,
      env: { PORT: new URL(JUDGE_STAND_IN).port, HOST: BIND_HOST },
    },
    {
      command: "node e2e/agent_stand_in.ts",
      url: `${AGENT_STAND_IN}/ping`,
      env: {
        PORT: new URL(AGENT_STAND_IN).port,
        HOST: BIND_HOST,
        CRM_API: BACKEND,
        CRM_AGENT_KEY: AGENT_KEY,
      },
    },
    {
      command: "node e2e/copilot_stand_in.ts",
      url: `${COPILOT_STAND_IN}/ping`,
      env: {
        PORT: new URL(COPILOT_STAND_IN).port,
        HOST: BIND_HOST,
        CRM_API: BACKEND,
      },
    },
    {
      command: "node e2e/auth_stand_in.ts",
      url: `${AUTH_STAND_IN}/jwks.json`,
      env: {
        PORT: new URL(AUTH_STAND_IN).port,
        HOST: BIND_HOST,
        WORKER_PASSWORD: TEST_PASSWORD,
        DASHBOARD,
        ...PACK_ENV,
      },
    },
    {
      command: `npx vite dashboard --port ${new URL(DASHBOARD).port} --strictPort --mode e2e --host ${BIND_HOST}`,
      url: DASHBOARD,
      env: {
        CRM_API: BACKEND,
        VITE_AUTH_URL: AUTH_STAND_IN,
        AUTH_URL: AUTH_STAND_IN,
        VITE_SUPABASE_PUBLISHABLE_KEY: "e2e-publishable-key",
      },
    },
  ],
});
