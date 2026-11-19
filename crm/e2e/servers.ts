// The servers the end-to-end tests run on ports of their own, so they never touch
// the ones `npm run dev` starts: the backend, the dashboard, and the stand-ins
// for the agent, the Copilot, Supabase Auth and the judge.
//
// E2E_HOST names the address the URLs carry, for a run that proves the
// externally reachable addresses of a public demo, such as
// E2E_HOST=203.0.113.10 npm run e2e. The address must be one the host itself
// reaches, because the servers here call each other by it: on a NAT address
// that only the outside can reach, the backend's key fetch fails and every
// sign-in turns 503. With E2E_HOST set, every server binds every interface;
// without it, the defaults stay the loopback ones the suite has always
// used.
export const E2E_HOST = process.env.E2E_HOST ?? "";

export const BIND_HOST = E2E_HOST ? "0.0.0.0" : "127.0.0.1";

export const BACKEND = `http://${E2E_HOST || "127.0.0.1"}:8001`;
export const DASHBOARD = `http://${E2E_HOST || "localhost"}:5174`;
export const AGENT_STAND_IN = `http://${E2E_HOST || "127.0.0.1"}:8003`;
export const AUTH_STAND_IN = `http://${E2E_HOST || "127.0.0.1"}:8004`;
export const JUDGE_STAND_IN = `http://${E2E_HOST || "127.0.0.1"}:8005`;
export const COPILOT_STAND_IN = `http://${E2E_HOST || "127.0.0.1"}:8007`;

// The test backend's API key for the agent's side, and the header that carries it.
export const AGENT_KEY = "e2e-agent-key-0123456789abcdefghijklmnopq";
export const AGENT_KEY_HEADERS = { "X-API-Key": AGENT_KEY };
