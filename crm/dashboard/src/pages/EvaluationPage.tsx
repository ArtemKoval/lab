import { useCallback } from "react";
import { useParams } from "react-router";
import { api, type ScoredCase, type ScoredEvaluation } from "../api";
import { DecisionAward, RightChip, RunChip } from "../components/Chips";
import { CaseLink } from "../components/CaseLink";
import { Message } from "../components/Message";
import { ModelName } from "../components/ModelName";
import {
  agentsAtOnce,
  dateTime,
  duration,
  evaluationSetName,
  modelCost,
  money,
} from "../format";
import { MEASURES } from "../measures";
import { REFRESH_MS, useLoad } from "../useLoad";

export function EvaluationPage() {
  const { runId = "" } = useParams();
  const load = useCallback(() => api.getEvaluation(runId), [runId]);
  const { data: evaluation, error } = useLoad(load, REFRESH_MS);

  if (!evaluation)
    return <Message error={error} notFound="Evaluation not found" />;

  return (
    <>
      <div className="title-row">
        <h1>Evaluation #{evaluation.number}</h1>
        <RunChip status={evaluation.status} />
      </div>
      <div className="column">
        <MeasuresPanel evaluation={evaluation} />
        <ScoredCases cases={evaluation.cases} />
      </div>
    </>
  );
}

function MeasuresPanel({
  evaluation,
}: Readonly<{ evaluation: ScoredEvaluation }>) {
  return (
    <section className="panel" aria-labelledby="measures-title">
      <h2 id="measures-title">Measures</h2>
      <p className="muted small">
        {evaluationSetName(evaluation.evaluation_set, evaluation.size)}, with{" "}
        {agentsAtOnce(evaluation.agents)} on <ModelName run={evaluation} />.
        Started {dateTime(evaluation.started_at)}.
      </p>
      <dl className="facts measures">
        {MEASURES.map(({ label, show }) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd className="mono">{show(evaluation.measures)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function ScoredCases({ cases }: Readonly<{ cases: ScoredCase[] }>) {
  return (
    <section className="panel" aria-labelledby="cases-title">
      <h2 id="cases-title">Cases</h2>
      <p className="muted small">
        A entry the agent didn't decide counts as a referral.
      </p>
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Copy</th>
              <th>Of</th>
              <th>Worker</th>
              <th>Agent</th>
              <th>Score</th>
              <th className="num">Mistake cost</th>
              <th className="num">Model cost</th>
              <th className="num">Time</th>
              <th>The agent's reason</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((entry) => (
              <tr key={entry.case_id}>
                <td className="nowrap">
                  <CaseLink caseId={entry.case_id} />
                </td>
                <td className="mono nowrap">{entry.copy_of}</td>
                <td className="nowrap">
                  <DecisionAward
                    decision={entry.worker_decision}
                    award={entry.worker_award}
                  />
                </td>
                <td className="nowrap">
                  {entry.decision && entry.award !== null ? (
                    <DecisionAward
                      decision={entry.decision}
                      award={entry.award}
                    />
                  ) : (
                    <span className="muted">No decision</span>
                  )}
                </td>
                <td>
                  <RightChip right={entry.right} />
                </td>
                <td className="num mono">{money(entry.mistake_cost)}</td>
                <td className="num mono">{modelCost(entry.model_cost)}</td>
                <td className="num mono">{duration(entry.seconds)}</td>
                <td className="small">{entry.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
