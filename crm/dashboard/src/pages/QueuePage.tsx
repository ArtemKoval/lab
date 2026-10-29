import { api, statuses } from "../api";
import { DecisionChip, StatusChip } from "../components/Chips";
import { CaseLink } from "../components/CaseLink";
import { Message } from "../components/Message";
import { DispatchPanel } from "../components/DispatchPanel";
import { date, label, money, statusLabels } from "../format";
import { REFRESH_MS, useLoad } from "../useLoad";

export function QueuePage() {
  const { data: cases, error } = useLoad(api.listCases, REFRESH_MS);
  if (!cases) return <Message error={error} />;

  return (
    <>
      <h1>Cases queue</h1>
      <section className="tiles" aria-label="Cases by state">
        {statuses.map((status) => {
          const count = cases.filter((c) => c.status === status).length;
          return (
            <div
              className="panel tile"
              key={status}
              aria-label={`${statusLabels[status]}: ${String(count)}`}
            >
              <StatusChip status={status} />
              <span className="tile-count mono">{count}</span>
            </div>
          );
        })}
      </section>
      <DispatchPanel />
      <section className="panel table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Case</th>
              <th>Customer</th>
              <th>Type</th>
              <th>Summary</th>
              <th className="num">Claimed</th>
              <th>Submitted</th>
              <th>State</th>
              <th>Decision</th>
              <th className="num">Award</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((entry) => (
              <tr key={entry.case_id}>
                <td className="nowrap">
                  <CaseLink caseId={entry.case_id} />
                </td>
                <td>{entry.customer_name}</td>
                <td>{label(entry.case_type)}</td>
                <td>{entry.summary}</td>
                <td className="num mono">{money(entry.amount_claimed)}</td>
                <td className="nowrap">{date(entry.submitted_on)}</td>
                <td>
                  <StatusChip status={entry.status} />
                </td>
                <td>
                  {entry.decision && <DecisionChip decision={entry.decision} />}
                </td>
                <td className="num mono">
                  {entry.award !== null && money(entry.award)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
