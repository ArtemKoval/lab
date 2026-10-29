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
  const { data: case, error, reload } = useLoad(load, REFRESH_MS);

  if (!case) {
    if (error instanceof ApiError && error.status === 404)
      return <p className="message">Case not found</p>;
    return <Message error={error} />;
  }

  return (
    <>
      <div className="case-heading">
        <p className="mono muted">{case.case_id}</p>
        <h1>{case.summary}</h1>
        <StatusChip status={case.status} />
      </div>
      <div className="case-layout">
        <div className="column">
          <CaseDetails case={case} />
          <ItemsPanel case={case} />
          <DocumentsPanel case={case} />
        </div>
        <div className="column">
          <DecisionPanel case={case} onSignedOff={reload} />
          <StepList caseId={case.case_id} />
          <ContractPanel contractId={case.contract_id} />
          <HistoryPanel customerId={case.customer_id} />
        </div>
      </div>
    </>
  );
}

function CaseDetails({ case }: Readonly<{ case: Case }>) {
  return (
    <section className="panel" aria-labelledby="case-title">
      <h2 id="case-title">Case</h2>
      <dl className="facts">
        <div>
          <dt>Customer</dt>
          <dd>{case.customer_name}</dd>
        </div>
        <div>
          <dt>Type</dt>
          <dd>{label(case.case_type)}</dd>
        </div>
        <div>
          <dt>Incident</dt>
          <dd>
            {date(case.incident_date)}, {case.incident_location}
          </dd>
        </div>
        <div>
          <dt>Submitted</dt>
          <dd>{date(case.submitted_on)}</dd>
        </div>
        <div>
          <dt>Amount claimed</dt>
          <dd className="mono">{money(case.amount_claimed)}</dd>
        </div>
      </dl>
      <h3>The customer's story</h3>
      <p className="story">{case.story}</p>
    </section>
  );
}

function ItemsPanel({ case }: Readonly<{ case: Case }>) {
  const total = case.items.reduce((sum, item) => sum + item.amount, 0);
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
            {case.items.map((item) => (
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

function DocumentsPanel({ case }: Readonly<{ case: Case }>) {
  return (
    <section className="panel" aria-labelledby="documents-title">
      <h2 id="documents-title">Documents</h2>
      {case.documents.map((document) => (
        <article className="document" key={document.name}>
          <h3>{document.name}</h3>
          <p className="muted small">{label(document.type)}</p>
          <p>{document.content}</p>
        </article>
      ))}
    </section>
  );
}
