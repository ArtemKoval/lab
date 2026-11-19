import type { DecisionRecord } from "../api";
import { time } from "../format";
import { awardText, useAwardFormat, useLabel } from "../vocabulary";
import { DecisionChip } from "./Chips";

// A decision's whole record, as cases manual section 14 asks for it: the
// decision, the outcome payload the pack resolved, the section, the reason,
// who made it and when, and the manual's version.
export function DecisionDetails({
  decision,
}: Readonly<{ decision: DecisionRecord }>) {
  const word = useLabel();
  const format = useAwardFormat();
  const calculation = decision.payload?.calculation;
  return (
    <>
      <div className="decision-line">
        <DecisionChip decision={decision.decision} />
        {decision.payload?.award !== undefined && (
          <span className="award mono">
            {awardText(decision.payload.award, format)}
          </span>
        )}
      </div>
      {calculation && (
        <CalculationTable
          calculation={calculation}
          award={decision.payload?.award ?? 0}
        />
      )}
      <p className="section-ref">{decision.section}</p>
      <p className="reason">{decision.reason}</p>
      <p className="small muted">
        Decided by {decision.decided_by} at {time(decision.decided_at)}
      </p>
      <p className="small muted">
        {word(
          "decision.manual_version",
          "Cases manual version {version}",
        ).replaceAll("{version}", decision.manual_version)}
      </p>
    </>
  );
}

// How the pack worked the outcome out, line by line.
function CalculationTable({
  calculation,
  award,
}: Readonly<{
  calculation: NonNullable<
    NonNullable<DecisionRecord["payload"]>["calculation"]
  >;
  award: number;
}>) {
  const word = useLabel();
  const format = useAwardFormat();
  const caption = word(
    "decision.calculation_caption",
    "How the award was worked out",
  );
  return (
    <div className="table-scroll calculation">
      <table className="table">
        <caption className="small muted">{caption}</caption>
        <tbody>
          {calculation.map((line, index) => (
            // Two lines can read alike, so each is known by its place too.
            <tr key={`${String(index)} ${line.step}`}>
              <td>{line.step}</td>
              <td className="num mono">{awardText(line.amount, format)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">{word("decision.award_label", "Award")}</th>
            <td className="num mono">{awardText(award, format)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
