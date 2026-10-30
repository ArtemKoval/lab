import type { Case, Payment } from "../api";
import { money, time } from "../format";
import { useWorker } from "../worker";
import { DecisionChip } from "./Chips";
import { NotAllowed } from "./NotAllowed";
import { SignOffForm } from "./SignOffForm";

type SignOff = Pick<Payment, "signed_off_by" | "signed_off_at">;

function whoAndWhen({ signed_off_by, signed_off_at }: SignOff): string | null {
  return signed_off_by && signed_off_at
    ? `${signed_off_by} at ${time(signed_off_at)}`
    : null;
}

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
  const paidSignedOff = payment && whoAndWhen(payment);

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
          {paidSignedOff && `, signed off by ${paidSignedOff}`}
        </p>
      )}
      {decision?.decision === "approve" &&
        !payment &&
        entry.status === "in_progress" && (
          <p className="payment">Waiting for the agent to pay it.</p>
        )}
      {decision && entry.status === "waiting_for_sign_off" && (
        <HeldPayment
          entry={entry}
          award={decision.award}
          onSignedOff={onSignedOff}
        />
      )}
    </section>
  );
}

// A payment over the limit, which waits for a worker's sign-off, unless the
// case is an evaluation's copy, which nobody can sign off.
function HeldPayment({
  entry,
  award,
  onSignedOff,
}: Readonly<{ entry: Case; award: number; onSignedOff: () => void }>) {
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
      <p>
        The payment of <span className="mono">{money(award)}</span> is over the
        approval limit and waits for a worker's sign-off.
      </p>
      {worker.can_approve_over_limit ? (
        <SignOffForm caseId={entry.case_id} onSignedOff={onSignedOff} />
      ) : (
        <NotAllowed action="sign this off" />
      )}
    </div>
  );
}
