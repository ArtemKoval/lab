import { useState } from "react";
import { api, type Case } from "../api";
import { useAwardFormat, useBenefit, useLabel } from "../vocabulary";

// The desk's decisions on a waiting request: approve and issue with a term,
// decline, or refer to the lead. Every signed-in worker sees the form on a
// case that waits or is left for a worker.
export function DeskDecisionForm({
  entry,
  onDecided,
}: Readonly<{ entry: Case; onDecided: () => void }>) {
  const word = useLabel();
  const benefit = useBenefit();
  const format = useAwardFormat();
  const [days, setDays] = useState("14");
  const [reason, setReason] = useState("");
  const [sections, setSections] = useState(
    word("desk.sections.default", "The rules the desk relied on"),
  );
  const [error, setError] = useState<string | undefined>();
  const [sending, setSending] = useState(false);

  const termLabel =
    format === "days"
      ? word("desk.days", "Days")
      : word("resolution.amount", "Amount");

  const post = async (decision: "approve" | "decline" | "refer") => {
    setSending(true);
    setError(undefined);
    try {
      await api.workerDecision(entry.case_id, {
        decision,
        days: Number(days) || 14,
        reason,
        section: sections,
        benefit: benefit,
      });
      onDecided();
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
          <label htmlFor="desk-days">{termLabel}</label>
          <input
            id="desk-days"
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
          <label htmlFor="desk-sections">
            {word("desk.sections", "The rule sections relied on")}
          </label>
          <input
            id="desk-sections"
            value={sections}
            onChange={(event) => {
              setSections(event.target.value);
            }}
          />
        </div>
        <div>
          <label htmlFor="desk-reason">
            {word("desk.reason", "Why the desk decides so")}
          </label>
          <input
            id="desk-reason"
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
            void post("approve");
          }}
        >
          {word("desk.approve", "Approve and issue")}
        </button>
        <button
          type="button"
          className="button quiet"
          disabled={sending}
          onClick={() => {
            void post("decline");
          }}
        >
          {word("desk.decline", "Decline the request")}
        </button>
        <button
          type="button"
          className="button quiet"
          disabled={sending}
          onClick={() => {
            void post("refer");
          }}
        >
          {word("desk.refer", "Refer to the lead librarian")}
        </button>
      </div>
    </div>
  );
}
