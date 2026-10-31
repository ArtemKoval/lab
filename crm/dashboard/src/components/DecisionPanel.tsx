import type { Case, Decision } from "../api";
import { money, time } from "../format";
import { useWorker } from "../worker";
import { DecisionDetails } from "./DecisionDetails";
import { NotAllowed } from "./NotAllowed";
import { SendBackForm } from "./SendBackForm";
import { SignOffForm } from "./SignOffForm";

type SignOff = Pick<Decision, "signed_off_by" | "signed_off_at">;

function whoAndWhen({ signed_off_by, signed_off_at }: SignOff): string | null {
  return signed_off_by && signed_off_at
    ? `${signed_off_by} at ${time(signed_off_at)}`
    : null;
}

function progress(entry: Case): string {
  if (entry.status === "in_progress")
    return "The agent is working on this case.";
  if (entry.status === "sent_back")
    return "Sent back to the agent, which hasn't taken it up yet. The next dispatch works on it.";
  if (entry.status === "left_for_worker")
    return `The agent couldn't finish this case in ${String(entry.attempts)} attempts, so it's left for a worker.`;
  if (entry.attempts > 0) return "Back in the queue after a failed attempt.";
  return "The agent hasn't started on this case.";
}

export function DecisionPanel({
  entry,
  onAnswered,
}: Readonly<{ entry: Case; onAnswered: () => void }>) {
  const { decision, effect } = entry;

  return (
    <section className="panel" aria-labelledby="decision-title">
      <h2 id="decision-title">Decision</h2>
      {!decision && <p className="muted">{progress(entry)}</p>}
      {decision && <DecisionDetails decision={decision} />}
      {effect && (
        <p className="payment">{effect.summary ?? "The effect has run."}</p>
      )}
      {decision?.decision === "approve" &&
        !effect &&
        entry.status === "in_progress" && (
          <p className="payment">Waiting for the agent to run its effect.</p>
        )}
      {decision && entry.status === "waiting_for_sign_off" && (
        <HeldPayment
          entry={entry}
          decision={decision}
          onAnswered={onAnswered}
        />
      )}
    </section>
  );
}

// Why a payment waits for a worker's sign-off: it's over the approval limit,
// or the Gateway refused it.
function WhyHeld({ decision }: Readonly<{ decision: Decision }>) {
  const amount = <span className="mono">{money(decision.payload?.award ?? 0)}</span>;
  if (decision.gateway_refusal)
    return (
      <>
        <p>
          The Gateway refused the payment of {amount}, so it waits for a
          worker's sign-off.
        </p>
        <p className="small muted">{decision.gateway_refusal}</p>
      </>
    );
  return (
    <p>
      The payment of {amount} is over the approval limit and waits for a
      worker's sign-off.
    </p>
  );
}

// A payment over the limit or refused by the Gateway, which waits for a
// worker to sign it off or send it back, unless the case is an evaluation's
// copy, which nobody can answer.
function HeldPayment({
  entry,
  decision,
  onAnswered,
}: Readonly<{ entry: Case; decision: Decision; onAnswered: () => void }>) {
  const worker = useWorker();
  if (entry.evaluation_id)
    return (
      <p className="payment">
        Held for sign-off. In an evaluation this counts as finished, and a copy
        can't be signed off.
      </p>
    );
  return (
    <div className="sign-off">
      <WhyHeld decision={decision} />
      {worker.can_approve_over_limit ? (
        <div className="held-answers">
          <SignOffForm caseId={entry.case_id} onSignedOff={onAnswered} />
          <SendBackForm caseId={entry.case_id} onSentBack={onAnswered} />
        </div>
      ) : (
        <NotAllowed action="sign this off or send it back" />
      )}
    </div>
  );
}
