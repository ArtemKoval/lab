import { Link } from "react-router";
import { casePage } from "../paths";

export function CaseLink({ caseId }: Readonly<{ caseId: string }>) {
  return (
    <Link className="mono" to={casePage(caseId)}>
      {caseId}
    </Link>
  );
}
