import { createContext, use, useEffect, useState } from "react";
import type { Location } from "react-router";
import type { Worker } from "./api";
import { followSession } from "./auth";

// The worker signed in, which RequireWorker provides to the pages it guards.
export const WorkerContext = createContext<Worker | undefined>(undefined);

// Where the sign-in page sends a worker once they have signed in.
export interface SignInState {
  from?: Location;
}

// The worker signed in, for the pages inside RequireWorker.
export function useWorker(): Worker {
  const worker = use(WorkerContext);
  if (!worker) throw new Error("This page needs a signed-in worker");
  return worker;
}

// Whether a worker is signed in, or undefined until Supabase has said.
export function useSignedIn(): boolean | undefined {
  const [signedIn, setSignedIn] = useState<boolean>();
  useEffect(() => followSession(setSignedIn), []);
  return signedIn;
}
