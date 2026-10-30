// Stands in for the auth service in the end-to-end tests. It signs in the
// pack's three workers with the test password, signing each access token with
// a key pair it makes as it starts, and serves the public key for the backend
// to check them. It answers the browser's cross-origin checks, since the
// dashboard calls it from another port. The contract is the dev auth
// service's: POST /signin and GET /jwks.json.

import { generateKeyPairSync, sign } from "node:crypto";
import { readFileSync } from "node:fs";
import {
  createServer,
  type IncomingMessage,
  type ServerResponse,
} from "node:http";
import { json } from "node:stream/consumers";

interface Worker {
  worker_id: string;
  email: string;
}

const workers = JSON.parse(
  readFileSync("domains/insurance/data/workers.json", "utf8"),
) as Worker[];
const password = process.env.WORKER_PASSWORD;
// The dashboard, the one origin the browser may call this from.
const dashboard = process.env.DASHBOARD ?? "";
const KEY_ID = "e2e-key";
const LIFETIME = 3600;
const { privateKey, publicKey } = generateKeyPairSync("ec", {
  namedCurve: "P-256",
});
const kid = { kid: KEY_ID, alg: "ES256", use: "sig" };
const publicJwk = {
  ...publicKey.export({ format: "jwk" }),
  ...kid,
};

function b64url(input: string | object | Buffer): string {
  return Buffer.from(
    typeof input === "string" || Buffer.isBuffer(input)
      ? input
      : JSON.stringify(input),
  ).toString("base64url");
}

function accessToken(worker: Worker): string {
  const now = Math.floor(Date.now() / 1000);
  const header = b64url({ ...kid, alg: "ES256", typ: "JWT" });
  const payload = b64url({
    sub: worker.email,
    email: worker.email,
    aud: "crm",
    iat: now,
    exp: now + LIFETIME,
  });
  const signature = b64url(
    sign("SHA256", Buffer.from(`${header}.${payload}`), {
      key: privateKey,
      dsaEncoding: "ieee-p1363",
    }),
  );
  return `${header}.${payload}.${signature}`;
}

function answer(response: ServerResponse, code: number, body: object): void {
  response.writeHead(code, {
    "content-type": "application/json",
    "access-control-allow-origin": dashboard,
    "access-control-allow-headers": "content-type",
    "access-control-allow-methods": "POST, GET, OPTIONS",
  });
  response.end(JSON.stringify(body));
}

async function route(request: IncomingMessage, response: ServerResponse) {
  if (request.method === "OPTIONS") {
    answer(response, 204, {});
    return;
  }
  if (request.url === "/jwks.json") {
    answer(response, 200, { keys: [publicJwk] });
    return;
  }
  if (request.url === "/api/health") {
    answer(response, 200, { status: "ok" });
    return;
  }
  if (request.url === "/signin" && request.method === "POST") {
    const body = (await json(request)) as { email?: string; password?: string };
    const worker = workers.find((candidate) => candidate.email === body.email);
    if (!worker || body.password !== password) {
      answer(response, 401, { detail: "The email or password is wrong." });
      return;
    }
    answer(response, 200, { access_token: accessToken(worker) });
    return;
  }
  answer(response, 404, { msg: "Invalid token" });
}

const server = createServer((request, response) => {
  route(request, response).catch(() => {
    answer(response, 500, { msg: "error" });
  });
});
const port = Number(process.env.PORT ?? 8004);
server.listen(port, "127.0.0.1", () => {
  console.log(`auth stand-in on http://127.0.0.1:${String(port)}`);
});
