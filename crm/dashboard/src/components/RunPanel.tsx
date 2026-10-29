import { Fragment } from "react";
import { Link } from "react-router";
import { api, type Run } from "../api";
import { time } from "../format";
import { casePage } from "../paths";
import { REFRESH_MS, useLoad } from "../useLoad";
import { RunChip, TodoChip } from "./Chips";
import { Message } from "./Message";

const CASE_ID = /(CLM-\d+)/;

export function RunPanel() {
  const { data: run, error } = useLoad(api.getLatestRun, REFRESH_MS);

  return (
    <section className="panel run" aria-labelledby="run-title">
      <div className="run-heading">
        <h2 id="run-title">Current run</h2>
        {run && <RunChip status={run.status} />}
      </div>
      {run === undefined && <Message error={error} />}
      {run === null && <p className="muted">No run yet.</p>}
      {run && <RunDetails run={run} />}
    </section>
  );
}

function RunDetails({ run }: Readonly<{ run: Run }>) {
  return (
    <>
      <p className="muted small">
        Started at {time(run.started_at)}, up to {run.cap}{" "}
        {run.cap === 1 ? "case" : "cases"}
        {run.finished_at && `, finished at ${time(run.finished_at)}`}
      </p>
      <h3>To-do list</h3>
      {run.todos.length === 0 ? (
        <p className="muted">The agent hasn't written its to-do list yet.</p>
      ) : (
        <ol className="todos">
          {run.todos.map((todo, index) => (
            <li className="todo" key={`${String(index)}-${todo.content}`}>
              <TodoChip status={todo.status} />
              <span>
                <LinkedCases text={todo.content} />
              </span>
            </li>
          ))}
        </ol>
      )}
      {run.summary && (
        <>
          <h3>Summary for the workers</h3>
          <p className="summary">{run.summary}</p>
        </>
      )}
    </>
  );
}

function LinkedCases({ text }: Readonly<{ text: string }>) {
  return text.split(CASE_ID).map((part, index) =>
    CASE_ID.test(part) ? (
      <Link className="mono" key={index} to={casePage(part)}>
        {part}
      </Link>
    ) : (
      <Fragment key={index}>{part}</Fragment>
    ),
  );
}
