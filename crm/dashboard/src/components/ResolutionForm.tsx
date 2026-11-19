import { useState } from "react";
import { api, type Case } from "../api";
import { useWorker } from "../worker";
import { useAwardFormat, useBenefit, useLabel } from "../vocabulary";

// The lead's in-person decision on a referred request: issue the loan for
// the term in days, or decline it with a reason. Only a worker who can sign
// off over the limit sees the form, and only on a referred case.
export function ResolutionForm({
  entry,
  onResolved,
}: Readonly<{ entry: Case; onResolved: () => void }>) {
  const word = useLabel();
  const format = useAwardFormat();
  const worker = useWorker();
  const benefit = useBenefit();
  const [days, setDays] = useState("14");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | undefined>();
  const [sending, setSending] = useState(false);

  if (!worker.can_approve_over_limit) return null;

  const termLabel =
    format === "days"
      ? word("resolution.days", "Days")
      : word("resolution.amount", "Amount");

  const post = async (resolution: "loan" | "decline") => {
    setSending(true);
    setError(undefined);
    try {
      await api.resolveReferral(entry.case_id, {
        resolution,
        days: Number(days) || 14,
        reason,
        benefit: benefit,
      });
      onResolved();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="resolution">
      <div className="setting-fields">
        <div>
          <label htmlFor="resolution-days">{termLabel}</label>
          <input
            id="resolution-days"
            className="mono"
            type="number"
            min={1}
            value={days}
            onChange={(event) => {
              setDays(event.target.value);
            }}
          />
        </div>
        <div>
          <label htmlFor="resolution-reason">
            {word("resolution.reason", "Why the lead decides so")}
          </label>
          <input
            id="resolution-reason"
            value={reason}
            onChange={(event) => {
              setReason(event.target.value);
            }}
          />
        </div>
      </div>
      {error && <p className="stopped">{error}</p>}
      <div className="actions">
        <button
          type="button"
          className="button"
          disabled={sending}
          onClick={() => {
            void post("loan");
          }}
        >
          {word("resolution.issue", "Issue the loan")}
        </button>
        <button
          type="button"
          className="button quiet"
          disabled={sending}
          onClick={() => {
            void post("decline");
          }}
        >
          {word("resolution.decline", "Decline the request")}
        </button>
      </div>
    </div>
  );
}
