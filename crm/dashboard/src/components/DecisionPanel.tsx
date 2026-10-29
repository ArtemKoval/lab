import type { Case } from "../api";
import { money, time } from "../format";
import { DecisionChip } from "./Chips";
import { SignOffForm } from "./SignOffForm";

function progress(entry: Case): string {
  if (entry.status === "in_progress")
    return "The agent is working on this case.";
  if (entry.status === "left_for_worker")
    return `The agent couldn't finish this case in ${String(entry.attempts)} attempts, so it's left for a worker.`;
  if (entry.attempts > 0) return "Back in the queue after a failed attempt.";
  return "The agent hasn't started on this case.";
}

export function DecisionPanel({
  entry,
  onSignedOff,
}: Readonly<{ entry: Case; onSignedOff: () => void }>) {
  const { decision, payment } = entry;

  return (
    <section className="panel" aria-labelledby="decision-title">
      <h2 id="decision-title">Decision</h2>
      {!decision && <p className="muted">{progress(entry)}</p>}
      {decision && (
        <>
          <div className="decision-line">
            <DecisionChip decision={decision.decision} />
            {decision.decision === "approve" && (
              <span className="award mono">{money(decision.award)}</span>
            )}
          </div>
          <p className="section-ref">{decision.section}</p>
          <p className="reason">{decision.reason}</p>
          <p className="small muted">Decided at {time(decision.decided_at)}</p>
        </>
      )}
      {payment && (
        <p className="payment">
          Paid <span className="mono">{money(payment.amount)}</span>
          {payment.signed_off_by && `, signed off by ${payment.signed_off_by}`}
        </p>
      )}
      {decision?.decision === "approve" &&
        !payment &&
        entry.status === "decided" && <p className="payment">Not paid yet</p>}
      {decision && entry.status === "waiting_for_sign_off" && (
        <div className="sign-off">
          <p>
            The payment of <span className="mono">{money(decision.award)}</span>{" "}
            is over the approval limit and waits for a worker's sign-off.
          </p>
          <SignOffForm caseId={entry.case_id} onSignedOff={onSignedOff} />
        </div>
      )}
    </section>
  );
}
