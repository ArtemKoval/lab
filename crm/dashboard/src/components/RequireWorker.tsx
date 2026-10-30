import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { api } from "../api";
import { WorkerContext, type SignInState, useSignedIn } from "../worker";
import { SIGN_IN } from "../paths";
import { useLoad } from "../useLoad";
import { PageFrame } from "./PageFrame";
import { StateMessage } from "./StateMessage";
import { SignOutButton } from "./SignOutButton";

// Keeps a page to signed-in workers. A visitor goes to the sign-in page,
// which brings them back here once they have signed in.
export function RequireWorker({ children }: Readonly<{ children: ReactNode }>) {
  const signedIn = useSignedIn();
  const location = useLocation();
  if (signedIn === undefined) return null;
  if (!signedIn) {
    const state: SignInState = { from: location };
    return <Navigate to={SIGN_IN} state={state} replace />;
  }
  return <WorkerProvider>{children}</WorkerProvider>;
}

// Loads the worker signed in for the pages, or says why it can't.
function WorkerProvider({ children }: Readonly<{ children: ReactNode }>) {
  const { data: worker, error } = useLoad(api.getSignedInWorker);
  if (!worker)
    return (
      <PageFrame>
        <StateMessage error={error} />
        {error && <SignOutButton className="button" />}
      </PageFrame>
    );
  return <WorkerContext value={worker}>{children}</WorkerContext>;
}
