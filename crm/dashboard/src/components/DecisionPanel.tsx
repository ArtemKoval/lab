import type { Case, Payment } from "../api";
import { money, time } from "../format";
import { DecisionChip } from "./Chips";
import { SignOffForm } from "./SignOffForm";

type SignOff = Pick<Payment, "signed_off_by" | "signed_off_at">;

function whoAndWhen({ signed_off_by, signed_off_at }: SignOff): string | null {
  return signed_off_by && signed_off_at
    ? `${signed_off_by} at ${time(signed_off_at)}`
    : null;
}

function progress(case: Case): string {
  if (case.status === "in_progress")
    return "The agent is working on this case.";
  if (case.status === "left_for_worker")
    return `The agent couldn't finish this case in ${String(case.attempts)} attempts, so it's left for a worker.`;
  if (case.attempts > 0) return "Back in the queue after a failed attempt.";
  return "The agent hasn't started on this case.";
}

export function DecisionPanel({
  case,
  onSignedOff,
}: Readonly<{ case: Case; onSignedOff: () => void }>) {
  const { decision, payment } = case;
  const signedOff = decision && whoAndWhen(decision);
  const paidSignedOff = payment && whoAndWhen(payment);

  return (
    <section className="panel" aria-labelledby="decision-title">
      <h2 id="decision-title">Decision</h2>
      {!decision && <p className="muted">{progress(case)}</p>}
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
          {paidSignedOff && `, signed off by ${paidSignedOff}`}
        </p>
      )}
      {decision?.decision === "approve" &&
        !payment &&
        case.status === "in_progress" && (
          <p className="payment">
            {signedOff && `Signed off by ${signedOff}. `}
            Waiting for the agent to pay it.
          </p>
        )}
      {decision && case.status === "waiting_for_sign_off" && (
        <div className="sign-off">
          <p>
            The payment of{" "}
            <span className="mono">{money(decision.award)}</span> is over the
            approval limit and waits for a worker's sign-off.
          </p>
          <SignOffForm caseId={case.case_id} onSignedOff={onSignedOff} />
        </div>
      )}
    </section>
  );
}
