import { type SyntheticEvent, useState } from "react";
import { api } from "../api";
import { useLoad } from "../useLoad";

export function SignOffForm({
  caseId,
  onSignedOff,
}: Readonly<{ caseId: string; onSignedOff: () => void }>) {
  const { data: workers } = useLoad(api.listWorkers);
  const [workerId, setWorkerId] = useState("");
  const [error, setError] = useState<string>();
  const [sending, setSending] = useState(false);

  function submit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setSending(true);
    api.signOff(caseId, workerId).then(onSignedOff, (reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Sign-off failed");
      setSending(false);
    });
  }

  return (
    <form className="sign-off-form" onSubmit={submit}>
      <label>
        Worker
        <select
          value={workerId}
          onChange={(event) => {
            setWorkerId(event.target.value);
          }}
        >
          <option value="" disabled>
            Choose a worker
          </option>
          {workers
            ?.filter((worker) => worker.can_approve_over_limit)
            .map((worker) => (
              <option key={worker.worker_id} value={worker.worker_id}>
                {worker.name}
              </option>
            ))}
        </select>
      </label>
      <button type="submit" disabled={!workerId || sending}>
        Sign off
      </button>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
