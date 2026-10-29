import type { Case } from "../api";
import { money, time } from "../format";
import { DecisionChip } from "./Chips";
import { SignOffForm } from "./SignOffForm";

export function DecisionPanel({
  case,
  onSignedOff,
}: Readonly<{ case: Case; onSignedOff: () => void }>) {
  const { decision, payment } = case;

  return (
    <section className="panel" aria-labelledby="decision-title">
      <h2 id="decision-title">Decision</h2>
      {!decision && (
        <p className="muted">
          {case.status === "in_progress"
            ? "The agent is working on this case."
            : "The agent hasn't started on this case."}
        </p>
      )}
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
        case.status === "decided" && <p className="payment">Not paid yet</p>}
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
