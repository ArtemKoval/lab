import { Link } from "react-router";
import { api, type Status } from "../api";
import { DecisionChip, StatusChip } from "../components/Chips";
import { Message } from "../components/Message";
import { date, label, money, statusLabels } from "../format";
import { REFRESH_MS, useLoad } from "../useLoad";

const states: Status[] = [
  "waiting",
  "in_progress",
  "waiting_for_sign_off",
  "decided",
];

export function QueuePage() {
  const { data: cases, error } = useLoad(api.listCases, REFRESH_MS);
  if (!cases) return <Message error={error} />;

  return (
    <>
      <h1>Cases queue</h1>
      <section className="tiles" aria-label="Cases by state">
        {states.map((status) => {
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
            {cases.map((case) => (
              <tr key={case.case_id}>
                <td className="nowrap">
                  <Link className="mono" to={`/cases/${case.case_id}`}>
                    {case.case_id}
                  </Link>
                </td>
                <td>{case.customer_name}</td>
                <td>{label(case.case_type)}</td>
                <td>{case.summary}</td>
                <td className="num mono">{money(case.amount_claimed)}</td>
                <td className="nowrap">{date(case.submitted_on)}</td>
                <td>
                  <StatusChip status={case.status} />
                </td>
                <td>
                  {case.decision && <DecisionChip decision={case.decision} />}
                </td>
                <td className="num mono">
                  {case.award !== null && money(case.award)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
