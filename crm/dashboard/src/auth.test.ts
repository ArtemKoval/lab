import { expect, it, vi } from "vitest";

// auth.ts itself, on a stand-in for the auth service's fetch.
const fetchMock = vi.hoisted(() => vi.fn<() => Promise<Response>>());
vi.stubGlobal("fetch", fetchMock);
vi.unmock("./auth");

import {
  WRONG_PASSWORD,
  accessToken,
  followSession,
  signIn,
  signOut,
} from "./auth";

const reply = (body: object, status: number) =>
  new Response(JSON.stringify(body), { status });

it("signs in and keeps the token for the session", async () => {
  fetchMock.mockResolvedValue(reply({ access_token: "token-1" }, 200));
  await signIn("dana.whitfield@undercover.example", "crm-dev");
  expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8004/signin", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      email: "dana.whitfield@undercover.example",
      password: "crm-dev",
    }),
  });
  expect(accessToken()).toBe("token-1");
});

it("gives the friendly reason for a wrong password", async () => {
  fetchMock.mockResolvedValue(reply({ detail: "no" }, 401));
  await expect(
    signIn("dana.whitfield@undercover.example", "no"),
  ).rejects.toThrow(WRONG_PASSWORD);
});

it("signs in at the laptop service when VITE_AUTH_URL is empty", async () => {
  // The template .env leaves VITE_AUTH_URL empty, and an empty address must
  // fall back to the laptop service, or the sign-in posts to a path the
  // dashboard origin doesn't serve.
  vi.stubEnv("VITE_AUTH_URL", "");
  vi.resetModules();
  const { signIn: freshSignIn } = await import("./auth");
  fetchMock.mockResolvedValue(reply({ access_token: "token-3" }, 200));
  await freshSignIn("dana.whitfield@undercover.example", "crm-dev");
  expect(fetchMock).toHaveBeenLastCalledWith(
    "http://127.0.0.1:8004/signin",
    expect.anything(),
  );
  vi.unstubAllEnvs();
});

it("signs out and follows the session", async () => {
  localStorage.clear();
  fetchMock.mockResolvedValue(reply({ access_token: "token-2" }, 200));
  const seen: boolean[] = [];
  const stop = followSession((signedIn) => {
    seen.push(signedIn);
  });
  await signIn("dana.whitfield@undercover.example", "crm-dev");
  signOut();
  stop();
  expect(seen).toEqual([false, true, false]);
  expect(accessToken()).toBeUndefined();
});
