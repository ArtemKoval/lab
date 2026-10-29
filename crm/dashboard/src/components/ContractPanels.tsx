import { useCallback } from "react";
import { api } from "../api";
import { addOnName, date, label, money } from "../format";
import { useLoad } from "../useLoad";
import { Message } from "./Message";

export function ContractPanel({ contractId }: Readonly<{ contractId: string }>) {
  const load = useCallback(() => api.getContract(contractId), [contractId]);
  const { data: contract, error } = useLoad(load);

  return (
    <section className="panel" aria-labelledby="contract-title">
      <h2 id="contract-title">Contract</h2>
      {contract ? (
        <dl className="facts">
          <div>
            <dt>Contract</dt>
            <dd className="mono">{contract.contract_id}</dd>
          </div>
          <div>
            <dt>Plan</dt>
            <dd>{label(contract.plan)}</dd>
          </div>
          <div>
            <dt>Add-ons</dt>
            <dd>
              {contract.add_ons.length > 0
                ? contract.add_ons.map(addOnName).join(", ")
                : "None"}
            </dd>
          </div>
          <div>
            <dt>Purchased</dt>
            <dd>{date(contract.purchased_on)}</dd>
          </div>
          <div>
            <dt>Sold through</dt>
            <dd>{contract.sold_through}</dd>
          </div>
          <div>
            <dt>Trip</dt>
            <dd>
              {contract.trip.destination}, {date(contract.trip.departs_on)} to{" "}
              {date(contract.trip.returns_on)}
            </dd>
          </div>
          <div>
            <dt>Trip cost</dt>
            <dd className="mono">{money(contract.trip.trip_cost)}</dd>
          </div>
          <div>
            <dt>Travelers</dt>
            <dd>{contract.travelers.join(", ")}</dd>
          </div>
        </dl>
      ) : (
        <Message error={error} />
      )}
    </section>
  );
}

export function HistoryPanel({ customerId }: Readonly<{ customerId: string }>) {
  const load = useCallback(() => api.getCaseHistory(customerId), [customerId]);
  const { data: history, error } = useLoad(load);

  return (
    <section className="panel" aria-labelledby="history-title">
      <h2 id="history-title">Earlier cases</h2>
      {!history && <Message error={error} />}
      {history?.length === 0 && <p className="muted">No earlier cases</p>}
      {history && history.length > 0 && (
        <ul className="history">
          {history.map((case) => (
            <li key={case.case_id}>
              <p className="small muted">
                <span className="mono">{case.case_id}</span>,{" "}
                {label(case.case_type)}, filed {date(case.filed_on)}
              </p>
              <p>{case.summary}</p>
              <p className="small">
                {label(case.outcome)}, paid{" "}
                <span className="mono">{money(case.amount_paid)}</span>
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
