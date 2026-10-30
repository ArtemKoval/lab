// The dashboard's way to the auth service. The service's address is public,
// and the browser keeps the access token for the session. The AWS rollout
// later points VITE_AUTH_URL at Cognito's token endpoint, on the same shape.

const AUTH_URL = import.meta.env.VITE_AUTH_URL ?? "http://127.0.0.1:8004";
const TOKEN = "crm-access-token";

export const WRONG_PASSWORD = "The email or password is wrong.";

interface TokenReply {
  access_token: string;
}

// Signs a worker in, or throws the service's reason for refusing.
export async function signIn(email: string, password: string): Promise<void> {
  const response = await fetch(`${AUTH_URL}/signin`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const detail = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(
      response.status === 401
        ? WRONG_PASSWORD
        : (detail.detail ?? response.statusText),
    );
  }
  const reply = (await response.json()) as TokenReply;
  localStorage.setItem(TOKEN, reply.access_token);
  window.dispatchEvent(new Event("crm-session"));
}

// Signs the worker out of this browser only.
export function signOut(): void {
  localStorage.removeItem(TOKEN);
  window.dispatchEvent(new Event("crm-session"));
}

// The session's access token, or nothing when no one is signed in.
export function accessToken(): string | undefined {
  return localStorage.getItem(TOKEN) ?? undefined;
}

// The access token after any renewal. The local auth service signs tokens
// that last twelve hours, so this reads the stored token as it is; Cognito
// renews here at the rollout.
export function freshAccessToken(): Promise<string | undefined> {
  return Promise.resolve(accessToken());
}

// Tells the callback whether a worker is signed in, at once and again on each
// sign-in and sign-out, until the function it returns is called.
export function followSession(
  callback: (signedIn: boolean) => void,
): () => void {
  const tell = () => {
    callback(localStorage.getItem(TOKEN) !== null);
  };
  tell();
  window.addEventListener("crm-session", tell);
  window.addEventListener("storage", tell);
  return () => {
    window.removeEventListener("crm-session", tell);
    window.removeEventListener("storage", tell);
  };
}
