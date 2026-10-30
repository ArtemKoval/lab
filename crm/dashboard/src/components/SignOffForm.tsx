import { Signature } from "lucide-react";
import { api } from "../api";
import { ActionForm } from "./ActionForm";

// Signs off a held award as the worker signed in.
export function SignOffForm({
  caseId,
  onSignedOff,
}: Readonly<{ caseId: string; onSignedOff: () => void }>) {
  return (
    <ActionForm
      label="Sign off"
      icon={<Signature />}
      action={() => api.signOff(caseId).then(onSignedOff)}
    />
  );
}
