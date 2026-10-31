import type { DecisionRecord } from "../api";
import { money, time } from "../format";
import { DecisionChip } from "./Chips";

// A decision's whole record, as cases manual section 14 asks for it: the
// decision, the outcome payload the pack resolved, the section, the reason,
// who made it and when, and the manual's version.
export function DecisionDetails({
  decision,
}: Readonly<{ decision: DecisionRecord }>) {
  const calculation = decision.payload?.calculation;
  return (
    <>
      <div className="decision-line">
        <DecisionChip decision={decision.decision} />
        {decision.payload?.award !== undefined && (
          <span className="award mono">{money(decision.payload.award)}</span>
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
        Cases manual version {decision.manual_version}
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
  return (
    <div className="table-scroll calculation">
      <table className="table">
        <caption className="small muted">How the award was worked out</caption>
        <tbody>
          {calculation.map((line, index) => (
            // Two lines can read alike, so each is known by its place too.
            <tr key={`${String(index)} ${line.step}`}>
              <td>{line.step}</td>
              <td className="num mono">{money(line.amount)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">Award</th>
            <td className="num mono">{money(award)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
