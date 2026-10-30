import { use } from "react";
import { Link, NavLink, useMatch } from "react-router";
import { WorkerContext } from "../worker";
import {
  CASE_PAGE,
  CONFIGURATION,
  IMPROVEMENT,
  QUEUE,
  SCOREBOARD,
} from "../paths";
import { AccountMenu } from "./AccountMenu";
import { Brand } from "./Brand";

// The band across the top of every signed-in page: the brand, the main nav,
// and the worker signed in with their menu once they have loaded.
export function Header() {
  const worker = use(WorkerContext);
  // A case's page belongs to the queue.
  const queuePage = useMatch(QUEUE);
  const casePage = useMatch(CASE_PAGE);
  const onQueue = queuePage !== null || casePage !== null;
  return (
    <header className="header">
      <div className="header-bar">
        <Link to={QUEUE} className="brand">
          <Brand />
        </Link>
        <nav className="nav" aria-label="Main">
          <Link
            to={QUEUE}
            className={onQueue ? "active" : undefined}
            aria-current={onQueue ? "page" : undefined}
          >
            Queue
          </Link>
          <NavLink to={SCOREBOARD}>Scoreboard</NavLink>
          <NavLink to={IMPROVEMENT}>Improvement</NavLink>
          <NavLink to={CONFIGURATION}>Configuration</NavLink>
        </nav>
        {worker && (
          <div className="who" role="group" aria-label="Signed in">
            <p className="who-text">
              <span className="who-name">{worker.name}</span>
              <span className="who-role">{worker.role}</span>
            </p>
            <AccountMenu />
          </div>
        )}
      </div>
    </header>
  );
}
