import { api } from "../api";
import { awardText, useAwardFormat, useLabel } from "../vocabulary";
import { useWorker } from "../worker";
import { useLoad } from "../useLoad";

// Says what the signed-in worker can't do and why, in place of the button
// that would do it.
export function NotAllowed({ action }: Readonly<{ action: string }>) {
  const worker = useWorker();
  const { data: settings } = useLoad(api.getSettings);
  const word = useLabel();
  const format = useAwardFormat();
  return (
    <p className="not-allowed">
      {settings && (
        <>
          {word(
            "not_allowed.text",
            "Only a worker who can sign off awards over {limit} can {action}. {worker} can't.",
          )
            .replaceAll(
              "{limit}",
              awardText(settings.current.approval_limit, format),
            )
            .replaceAll("{action}", action)
            .replaceAll("{worker}", worker.name)}
        </>
      )}
    </p>
  );
}
