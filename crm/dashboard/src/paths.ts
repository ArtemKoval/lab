import { generatePath } from "react-router";

// The route of a entry's page, and the link to one case's page.
export const CASE_PAGE = "/cases/:caseId";
export const casePage = (caseId: string) => generatePath(CASE_PAGE, { caseId });
