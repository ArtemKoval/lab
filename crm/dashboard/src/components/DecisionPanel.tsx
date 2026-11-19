import type { Case, Decision } from "../api";
import { awardText, useAwardFormat, useLabel } from "../vocabulary";
import { useWorker } from "../worker";
import { DecisionDetails } from "./DecisionDetails";
import { NotAllowed } from "./NotAllowed";
import { ResolutionForm } from "./ResolutionForm";
import { SendBackForm } from "./SendBackForm";
import { SignOffForm } from "./SignOffForm";

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
      <ResolutionSlot entry={entry} onAnswered={onAnswered} />
    </section>
  );
}

// The one spot that lets a lead resolve a referred request: a decided
// referral with no effect, evaluation, or duplicate behind it.
function ResolutionSlot({
  entry,
  onAnswered,
}: Readonly<{ entry: Case; onAnswered: () => void }>) {
  const { decision, effect } = entry;
  if (
    decision?.decision === "refer" &&
    entry.status === "decided" &&
    !effect &&
    !entry.evaluation_id &&
    !entry.copy_of
  ) {
    return <ResolutionForm entry={entry} onResolved={onAnswered} />;
  }
  return null;
}

// Why a payment waits for a worker's sign-off: it's over the approval limit,
// or the Gateway refused it.
function WhyHeld({ decision }: Readonly<{ decision: Decision }>) {
  const word = useLabel();
  const format = useAwardFormat();
  const award = (
    <span className="mono">
      {awardText(decision.payload?.award ?? 0, format)}
    </span>
  );
  const held = (key: string, fallback: string) => {
    const [before, after] = word(key, fallback).split("{award}");
    return (
      <p>
        {before}
        {award}
        {after}
      </p>
    );
  };
  if (decision.gateway_refusal)
    return (
      <>
        {held(
          "hold.gateway_refused",
          "The Gateway refused the payment of {award}, so it waits for a worker's sign-off.",
        )}
        <p className="small muted">{decision.gateway_refusal}</p>
      </>
    );
  return held(
    "hold.over_limit",
    "The payment of {award} is over the approval limit and waits for a worker's sign-off.",
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
