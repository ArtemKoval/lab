import { generatePath } from "react-router";

// The routes of the pages, and the links to the pages that show one thing.
export const QUEUE = "/";
export const INSTRUCTIONS = "/instructions";
export const SCOREBOARD = "/scoreboard";
export const CASE_PAGE = "/cases/:caseId";
export const EVALUATION_PAGE = `${SCOREBOARD}/:runId`;

export const casePage = (caseId: string) => generatePath(CASE_PAGE, { caseId });
export const evaluationPage = (runId: string) =>
  generatePath(EVALUATION_PAGE, { runId });
