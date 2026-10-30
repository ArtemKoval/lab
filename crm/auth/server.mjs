// The dev auth service. It signs worker JWTs and serves the public keys, so
// the dashboard and the backend run their sign-in contract with no cloud.
// The AWS rollout later points AUTH_URL at Cognito instead, on the same
// contract: POST /signin with an email and a password answers an access
// token, and GET /jwks.json publishes the signing keys.
//
// The key pair is made at the first start and kept in dev-key.json, which is
// not committed. Any pack worker email signs in with the dev password from
// AUTH_DEV_PASSWORD, default crm-dev. The backend refuses an email that is
// not a pack worker, so this service only proves the password.

import { createServer } from "node:http";
import { createPublicKey, generateKeyPairSync, sign } from "node:crypto";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const KEY_FILE = join(HERE, "dev-key.json");
const KEY_ID = "dev-key-1";
const AUDIENCE = "crm";
const PORT = Number(process.env.PORT ?? 8004);
const DEV_PASSWORD = process.env.AUTH_DEV_PASSWORD ?? "crm-dev";
const TWELVE_HOURS = 12 * 60 * 60;

function b64url(buffer) {
  return buffer.toString("base64url");
}

function loadKey() {
  if (existsSync(KEY_FILE)) {
    return JSON.parse(readFileSync(KEY_FILE, "utf8"));
  }
  const { publicKey, privateKey } = generateKeyPairSync("ec", {
    namedCurve: "P-256",
  });
  const material = {
    kid: KEY_ID,
    private: privateKey.export({ type: "sec1", format: "pem" }).toString(),
    public_jwk: JSON.parse(
      JSON.stringify(createPublicKey(publicKey).export({ format: "jwk" })),
    ),
  };
  writeFileSync(KEY_FILE, JSON.stringify(material, null, 2));
  return material;
}

const key = loadKey();
const privateKey = createPrivateKey(key.private);

function jwks() {
  return { keys: [{ ...key.public_jwk, kid: key.kid, alg: "ES256", use: "sig" }] };
}

function signToken(email) {
  const header = { alg: "ES256", typ: "JWT", kid: key.kid };
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    sub: email,
    email,
    aud: AUDIENCE,
    iat: now,
    exp: now + TWELVE_HOURS,
  };
  const head = b64url(Buffer.from(JSON.stringify(header)));
  const body = b64url(Buffer.from(JSON.stringify(payload)));
  const signature = b64url(
    sign("SHA256", Buffer.from(`${head}.${body}`), {
      key: privateKey,
      dsaEncoding: "ieee-p1363",
    }),
  );
  return `${head}.${body}.${signature}`;
}

const server = createServer((request, response) => {
  if (request.method === "GET" && request.url === "/jwks.json") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify(jwks()));
    return;
  }
  if (request.method === "POST" && request.url === "/signin") {
    let body = "";
    request.on("data", (chunk) => {
      body += chunk;
    });
    request.on("end", () => {
      const { email, password } = JSON.parse(body || "{}");
      if (password !== DEV_PASSWORD || !email) {
        response.writeHead(401, { "content-type": "application/json" });
        response.end(JSON.stringify({ detail: "The email or password is wrong." }));
        return;
      }
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify({ access_token: signToken(email) }));
    });
    return;
  }
  if (request.method === "GET" && request.url === "/api/health") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ status: "ok" }));
    return;
  }
  response.writeHead(404);
  response.end();
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`auth service on http://127.0.0.1:${PORT}`);
});
