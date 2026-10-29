import { Link } from "react-router";
import { api, statuses } from "../api";
import { DecisionChip, StatusChip } from "../components/Chips";
import { Message } from "../components/Message";
import { RunPanel } from "../components/RunPanel";
import { date, label, money, statusLabels } from "../format";
import { casePage } from "../paths";
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
      <RunPanel />
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
                  <Link className="mono" to={casePage(entry.case_id)}>
                    {entry.case_id}
                  </Link>
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
