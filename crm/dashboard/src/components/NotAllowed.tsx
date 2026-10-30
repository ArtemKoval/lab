import { api } from "../api";
import { money } from "../format";
import { useWorker } from "../worker";
import { useLoad } from "../useLoad";

// Says what the signed-in worker can't do and why, in place of the button
// that would do it.
export function NotAllowed({ action }: Readonly<{ action: string }>) {
  const worker = useWorker();
  const { data: settings } = useLoad(api.getSettings);
  return (
    <p className="not-allowed">
      {settings && (
        <>
          Only a worker who can sign off awards over{" "}
          <span className="mono">{money(settings.current.approval_limit)}</span>{" "}
          can {action}. {worker.name} can't.
        </>
      )}
    </p>
  );
}
