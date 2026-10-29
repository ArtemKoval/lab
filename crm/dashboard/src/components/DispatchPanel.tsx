import { Fragment, useState } from "react";
import { api, type DispatchSummary, type Run, type RunCase } from "../api";
import {
  agentsAtOnce,
  dateTime,
  duration,
  modelCost,
  money,
  time,
} from "../format";
import { REFRESH_MS, useLoad } from "../useLoad";
import { DecisionChip, RunChip, StatusChip } from "./Chips";
import { CaseLink } from "./CaseLink";
import { Message } from "./Message";
import { ActionForm } from "./ActionForm";
import { AgentsChoice, FIRST_CHOICE } from "./AgentsChoice";

export function DispatchPanel() {
  const { data: dispatch, error } = useLoad(api.getLatestDispatch, REFRESH_MS);
  const [agents, setAgents] = useState(FIRST_CHOICE);

  return (
    <section className="panel dispatch" aria-labelledby="dispatch-title">
      <div className="title-row">
        <h2 id="dispatch-title">Dispatch</h2>
        {dispatch && <RunChip status={dispatch.status} />}
      </div>
      <ActionForm
        label="Start a dispatch"
        action={() => api.startDispatch(agents)}
      >
        <AgentsChoice agents={agents} onChange={setAgents} />
      </ActionForm>
      {dispatch === undefined && <Message error={error} />}
      {dispatch === null && <p className="muted">No dispatch yet.</p>}
      {dispatch && <DispatchDetails dispatch={dispatch} />}
    </section>
  );
}

function DispatchDetails({ dispatch }: Readonly<{ dispatch: Run }>) {
  return (
    <>
      <p className="muted small">
        <span className="mono">#{dispatch.number}</span> started at{" "}
        {dateTime(dispatch.started_at)} with {agentsAtOnce(dispatch.agents)}.
        Model cost{" "}
        <span className="mono">{modelCost(dispatch.model_cost)}</span>
        {dispatch.seconds !== null && (
          <>
            , took <span className="mono">{duration(dispatch.seconds)}</span>
          </>
        )}
        .
      </p>
      {dispatch.status === "stopped" && (
        <p className="stopped">
          It stopped before it finished. The next dispatch carries on its cases.
        </p>
      )}
      {dispatch.cases.length > 0 ? (
        <RunCases cases={dispatch.cases} />
      ) : (
        <p className="muted">No cases in this dispatch.</p>
      )}
      {dispatch.summary && <Summary summary={dispatch.summary} />}
    </>
  );
}

function RunCases({ cases }: Readonly<{ cases: RunCase[] }>) {
  return (
    <div className="table-scroll">
      <table className="table">
        <thead>
          <tr>
            <th>Case</th>
            <th>Customer</th>
            <th>State</th>
            <th>Decision</th>
            <th className="num">Award</th>
            <th>Started</th>
            <th className="num">Time</th>
            <th className="num">Model cost</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((entry) => (
            <tr key={entry.case_id}>
              <td className="nowrap">
                <CaseLink caseId={entry.case_id} />
              </td>
              <td>{entry.customer_name}</td>
              <td>
                <StatusChip status={entry.status} />
              </td>
              <td>
                {entry.decision && <DecisionChip decision={entry.decision} />}
              </td>
              <td className="num mono">
                {entry.award !== null && money(entry.award)}
              </td>
              <td className="nowrap">
                {entry.started_at && time(entry.started_at)}
              </td>
              <td className="num mono">{duration(entry.seconds)}</td>
              <td className="num mono">{modelCost(entry.model_cost)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Summary({ summary }: Readonly<{ summary: DispatchSummary }>) {
  const held = summary.waiting_for_sign_off.map(({ case_id, award }) => ({
    case_id,
    note: money(award),
  }));
  const only = (ids: string[]) => ids.map((case_id) => ({ case_id }));
  return (
    <div className="dispatch-summary">
      <h3 id="dispatch-summary-title">Summary</h3>
      <ul aria-labelledby="dispatch-summary-title">
        <li>
          {summary.approved} approved, {summary.declined} declined and{" "}
          {summary.referred} referred.
        </li>
        <CaseLine label="Waiting for sign-off" cases={held} />
        <CaseLine
          label="Left for a worker"
          cases={only(summary.left_for_worker)}
        />
        <CaseLine
          label="Left for the next dispatch"
          cases={only(summary.unfinished)}
        />
      </ul>
    </div>
  );
}

function CaseLine({
  label,
  cases,
}: Readonly<{ label: string; cases: { case_id: string; note?: string }[] }>) {
  if (cases.length === 0) return null;
  return (
    <li>
      {label}:{" "}
      {cases.map(({ case_id, note }, index) => (
        <Fragment key={case_id}>
          {index > 0 && ", "}
          <CaseLink caseId={case_id} />
          {note && <span className="mono"> {note}</span>}
        </Fragment>
      ))}
    </li>
  );
}
