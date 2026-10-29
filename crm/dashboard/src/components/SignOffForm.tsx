import { useState } from "react";
import { api } from "../api";
import { useLoad } from "../useLoad";
import { ActionForm } from "./ActionForm";

export function SignOffForm({
  caseId,
  onSignedOff,
}: Readonly<{ caseId: string; onSignedOff: () => void }>) {
  const { data: workers } = useLoad(api.listWorkers);
  const [workerId, setWorkerId] = useState("");

  return (
    <ActionForm
      label="Sign off"
      ready={workerId !== ""}
      action={() => api.signOff(caseId, workerId).then(onSignedOff)}
    >
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
    </ActionForm>
  );
}
