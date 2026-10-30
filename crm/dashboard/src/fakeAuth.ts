import { vi } from "vitest";
import type * as auth from "./auth";

// Stands in for auth.ts in the dashboard's tests, keeping the session in
// memory. A sign-in succeeds unless the test refuses it.
export const TOKEN = "test-access-token";

// The next access token the auth stand-in answers with, for the tests that
// walk the renewed sign-in.
export const freshAccessToken = vi.fn<typeof auth.freshAccessToken>(() => {
  return Promise.resolve(token);
});

let token: string | undefined;
let refusal: string | undefined;
const listeners = new Set<(signedIn: boolean) => void>();

function tell() {
  for (const listener of listeners) listener(token !== undefined);
}

export function startSession() {
  token = TOKEN;
  refusal = undefined;
}

export function endSession() {
  token = undefined;
}

export function refuseSignIn(reason: string) {
  refusal = reason;
}

export const signIn = vi.fn<typeof auth.signIn>(() => {
  if (refusal) return Promise.reject(new Error(refusal));
  token = TOKEN;
  tell();
  return Promise.resolve();
});

export const signOut = vi.fn<typeof auth.signOut>(() => {
  token = undefined;
  tell();
});

export function accessToken(): string | undefined {
  return token;
}

export function followSession(
  callback: (signedIn: boolean) => void,
): () => void {
  listeners.add(callback);
  queueMicrotask(() => {
    callback(token !== undefined);
  });
  return () => {
    listeners.delete(callback);
  };
}
