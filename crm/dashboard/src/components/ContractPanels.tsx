import { useCallback } from "react";
import { api } from "../api";
import type { Contract } from "../api";
import { addOnName, date, label, money } from "../format";
import { useLoad } from "../useLoad";
import {
  type ContractRow,
  fieldText,
  useContractPresentation,
  useLabel,
} from "../vocabulary";
import { StateMessage } from "./StateMessage";

export function ContractPanel({
  contractId,
}: Readonly<{ contractId: string }>) {
  const load = useCallback(() => api.getContract(contractId), [contractId]);
  const { data: contract, error } = useLoad(load);
  const presentation = useContractPresentation();

  return (
    <section className="panel" aria-labelledby="contract-title">
      <h2 id="contract-title">{presentation?.title ?? "Contract"}</h2>
      {contract === undefined && <StateMessage error={error} />}
      {contract && !presentation && <LegacyContract contract={contract} />}
      {contract && presentation?.rows.length && (
        <dl className="facts">
          {presentation.rows.map((row) => (
            <Row key={row.label} row={row} contract={contract} />
          ))}
        </dl>
      )}
    </section>
  );
}

// One row of the pack's presentation: the label beside the field's value in
// the row's format, or the template's slots filled. A row whose fields hold
// nothing shows the row's empty word, and stays out when it names none.
function Row({
  row,
  contract,
}: Readonly<{ row: ContractRow; contract: Contract }>) {
  const record = contract as unknown as Record<string, unknown>;
  if (row.template) {
    const paths = Object.keys(row.formats ?? {});
    const filled = row.template.replaceAll(
      /\{([^{}]+)\}/g,
      (_match, path: string) =>
        fieldText(record, path, row.formats?.[path] ?? "text"),
    );
    const holds =
      row.formats &&
      paths.some((path) =>
        fieldText(record, path, row.formats?.[path] ?? "text"),
      );
    if (!holds) {
      if (!row.empty) return null;
      return (
        <div>
          <dt>{row.label}</dt>
          <dd>{row.empty}</dd>
        </div>
      );
    }
    return (
      <div>
        <dt>{row.label}</dt>
        <dd>{filled}</dd>
      </div>
    );
  }
  const value = fieldText(record, row.field ?? "", row.format ?? "text");
  if (!value) {
    if (!row.empty) return null;
    return (
      <div>
        <dt>{row.label}</dt>
        <dd>{row.empty}</dd>
      </div>
    );
  }
  return (
    <div>
      <dt>{row.label}</dt>
      <dd
        className={
          row.format === "money" || row.format === "days" ? "mono" : undefined
        }
      >
        {value}
      </dd>
    </div>
  );
}

// The panel the core ships for a pack that names no contract rows yet.
function LegacyContract({ contract }: Readonly<{ contract: Contract }>) {
  return (
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
  );
}

export function HistoryPanel({ customerId }: Readonly<{ customerId: string }>) {
  const load = useCallback(() => api.getCaseHistory(customerId), [customerId]);
  const { data: history, error } = useLoad(load);
  const word = useLabel();

  return (
    <section className="panel" aria-labelledby="history-title">
      <h2 id="history-title">Earlier cases</h2>
      {!history && <StateMessage error={error} />}
      {history?.length === 0 && (
        <StateMessage empty="No earlier cases: this is the customer's first case with us." />
      )}
      {history && history.length > 0 && (
        <ul className="history">
          {history.map((entry) => (
            <li key={entry.case_id}>
              <p className="small muted">
                <span className="mono">{entry.case_id}</span>,{" "}
                {label(entry.case_type)}, {word("history.filed", "filed")}{" "}
                {date(entry.filed_on)}
              </p>
              <p>{entry.summary}</p>
              <p className="small">
                {label(entry.outcome)}, {word("history.paid", "paid")}{" "}
                <span className="mono">{money(entry.amount_paid)}</span>
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
