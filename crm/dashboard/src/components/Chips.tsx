import type {
  DecisionKind,
  RoundStatus,
  RunStatus,
  Status,
  Verdict,
  VersionStatus,
} from "../api";
import {
  decisionLabels,
  roundLabels,
  runLabels,
  statusLabels,
  verdictLabels,
  versionLabels,
} from "../format";
import { awardText, useAwardFormat, useLabel } from "../vocabulary";

export function StatusChip({ status }: Readonly<{ status: Status }>) {
  return (
    <span className={`chip status-${status}`}>{statusLabels[status]}</span>
  );
}

export function DecisionChip({
  decision,
}: Readonly<{ decision: DecisionKind }>) {
  const word = useLabel();
  const text =
    decision === "approve"
      ? word("decision.approve", decisionLabels.approve)
      : decisionLabels[decision];
  return <span className={`chip decision-${decision}`}>{text}</span>;
}

export function RunChip({ status }: Readonly<{ status: RunStatus }>) {
  return <span className={`chip run-${status}`}>{runLabels[status]}</span>;
}

export function VersionChip({ status }: Readonly<{ status: VersionStatus }>) {
  return (
    <span className={`chip version-${status}`}>{versionLabels[status]}</span>
  );
}

export function RoundChip({ status }: Readonly<{ status: RoundStatus }>) {
  return <span className={`chip round-${status}`}>{roundLabels[status]}</span>;
}

export function VerdictChip({ verdict }: Readonly<{ verdict: Verdict }>) {
  return (
    <span className={`chip verdict-${verdict}`}>{verdictLabels[verdict]}</span>
  );
}

// Whether the agent's decision and award match the worker's.
export function RightChip({ right }: Readonly<{ right: boolean }>) {
  return right ? (
    <span className="chip score-right">Right</span>
  ) : (
    <span className="chip score-miss">Miss</span>
  );
}

export function DecisionAward({
  decision,
  award,
}: Readonly<{ decision: DecisionKind; award: number }>) {
  const format = useAwardFormat();
  return (
    <>
      <DecisionChip decision={decision} />{" "}
      <span className="mono">{awardText(award, format)}</span>
    </>
  );
}
