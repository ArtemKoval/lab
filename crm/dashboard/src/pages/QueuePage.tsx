import {
  Bot,
  CircleCheck,
  Flag,
  Inbox,
  type LucideIcon,
  Signature,
  Undo2,
} from "lucide-react";
import { api, type Status, statuses } from "../api";
import { DecisionChip, StatusChip } from "../components/Chips";
import { CaseLink } from "../components/CaseLink";
import { StateMessage } from "../components/StateMessage";
import { DispatchPanel } from "../components/DispatchPanel";
import { PageHeader } from "../components/PageHeader";
import { date, label, money, statusLabels } from "../format";
import { REFRESH_MS, useLoad } from "../useLoad";

// Each state's icon on its tile.
const STATUS_ICONS: Record<Status, LucideIcon> = {
  waiting: Inbox,
  in_progress: Bot,
  waiting_for_sign_off: Signature,
  sent_back: Undo2,
  decided: CircleCheck,
  left_for_worker: Flag,
};

export function QueuePage() {
  const { data: cases, error } = useLoad(api.listCases, REFRESH_MS);
  const { data: pack } = useLoad(api.getPack, REFRESH_MS);
  // The money column carries the outcome the pack declares, and "Award"
  // until the declarations arrive.
  const outcomeName = label(Object.keys(pack?.outcomes ?? { award: "" })[0] ?? "award");
  const header = <PageHeader title="Cases queue" />;
  if (!cases)
    return (
      <>
        {header}
        <StateMessage error={error} />
      </>
    );

  return (
    <>
      {header}
      <section className="tiles" aria-label="Cases by state">
        {statuses.map((status) => {
          const count = cases.filter((c) => c.status === status).length;
          const Icon = STATUS_ICONS[status];
          return (
            <div
              className={`tile status-${status}`}
              key={status}
              role="group"
              aria-label={`${statusLabels[status]}: ${String(count)}`}
            >
              <p className="tile-label">{statusLabels[status]}</p>
              <p className="tile-figure">
                <span className="tile-count">{count}</span>
                <Icon />
              </p>
            </div>
          );
        })}
      </section>
      <DispatchPanel />
      <section className="panel" aria-labelledby="cases-title">
        <h2 id="cases-title">Cases</h2>
        <div className="table-scroll">
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
                <th className="num">{outcomeName}</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((entry) => (
                <tr key={entry.case_id}>
                  <td className="nowrap">
                    <CaseLink caseId={entry.case_id} />
                  </td>
                  <td className="nowrap">{entry.customer_name}</td>
                  <td className="nowrap">{label(entry.case_type)}</td>
                  <td>{entry.summary}</td>
                  <td className="num mono">{money(entry.amount_claimed)}</td>
                  <td className="nowrap">{date(entry.submitted_on)}</td>
                  <td>
                    <StatusChip status={entry.status} />
                  </td>
                  <td>
                    {entry.decision && (
                      <DecisionChip decision={entry.decision} />
                    )}
                  </td>
                  <td className="num mono">
                    {entry.award !== null && money(entry.award)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
