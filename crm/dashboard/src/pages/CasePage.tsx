import { useCallback } from "react";
import { useParams } from "react-router";
import { ApiError, api, type Case } from "../api";
import { StatusChip } from "../components/Chips";
import { DecisionPanel } from "../components/DecisionPanel";
import { Message } from "../components/Message";
import { HistoryPanel, ContractPanel } from "../components/ContractPanels";
import { StepList } from "../components/StepList";
import { date, label, money } from "../format";
import { REFRESH_MS, useLoad } from "../useLoad";

export function CasePage() {
  const { caseId = "" } = useParams();
  const load = useCallback(() => api.getCase(caseId), [caseId]);
  const { data: entry, error, reload } = useLoad(load, REFRESH_MS);

  if (!entry) {
    if (error instanceof ApiError && error.status === 404)
      return <p className="message">Case not found</p>;
    return <Message error={error} />;
  }

  return (
    <>
      <div className="case-heading">
        <p className="mono muted">{entry.case_id}</p>
        <h1>{entry.summary}</h1>
        <StatusChip status={entry.status} />
      </div>
      <div className="case-layout">
        <div className="column">
          <CaseDetails entry={entry} />
          <ItemsPanel entry={entry} />
          <DocumentsPanel entry={entry} />
        </div>
        <div className="column">
          <DecisionPanel entry={entry} onSignedOff={reload} />
          <StepList caseId={entry.case_id} />
          <ContractPanel contractId={entry.contract_id} />
          <HistoryPanel customerId={entry.customer_id} />
        </div>
      </div>
    </>
  );
}

function CaseDetails({ entry }: Readonly<{ entry: Case }>) {
  return (
    <section className="panel" aria-labelledby="case-title">
      <h2 id="case-title">Case</h2>
      <dl className="facts">
        <div>
          <dt>Customer</dt>
          <dd>{entry.customer_name}</dd>
        </div>
        <div>
          <dt>Type</dt>
          <dd>{label(entry.case_type)}</dd>
        </div>
        <div>
          <dt>Incident</dt>
          <dd>
            {date(entry.incident_date)}, {entry.incident_location}
          </dd>
        </div>
        <div>
          <dt>Submitted</dt>
          <dd>{date(entry.submitted_on)}</dd>
        </div>
        <div>
          <dt>Amount claimed</dt>
          <dd className="mono">{money(entry.amount_claimed)}</dd>
        </div>
      </dl>
      <h3>The customer's story</h3>
      <p className="story">{entry.story}</p>
    </section>
  );
}

function ItemsPanel({ entry }: Readonly<{ entry: Case }>) {
  const total = entry.items.reduce((sum, item) => sum + item.amount, 0);
  return (
    <section className="panel" aria-labelledby="items-title">
      <h2 id="items-title">Items claimed</h2>
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Category</th>
              <th className="num">Amount</th>
            </tr>
          </thead>
          <tbody>
            {entry.items.map((item) => (
              <tr key={item.description}>
                <td>{item.description}</td>
                <td>{label(item.category)}</td>
                <td className="num mono">{money(item.amount)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th scope="row" colSpan={2}>
                Total
              </th>
              <td className="num mono">{money(total)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </section>
  );
}

function DocumentsPanel({ entry }: Readonly<{ entry: Case }>) {
  return (
    <section className="panel" aria-labelledby="documents-title">
      <h2 id="documents-title">Documents</h2>
      {entry.documents.map((document) => (
        <article className="document" key={document.name}>
          <h3>{document.name}</h3>
          <p className="muted small">{label(document.type)}</p>
          <p>{document.content}</p>
        </article>
      ))}
    </section>
  );
}
