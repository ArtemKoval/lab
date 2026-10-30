// A case as the backend gives it to the case page, with its decision and
// the agent's steps, for the page's tests.

import type { Case, Decision, Step } from "./api";
import type { Source } from "./sources";
import {
  entry,
  history,
  panel,
  contract,
  renderAt,
  type Routes,
  stubApi,
} from "./testing";

export const decidedAt = "2026-09-27T17:06:16+00:00";

// A step of the agent's work, from no context file unless it's a lookup.
export const step = (
  step_id: number,
  kind: Step["kind"],
  content: string,
  sources: Source[] = [],
): Step => ({
  step_id,
  thread_id: "t-1",
  kind,
  content,
  sources,
  created_at: decidedAt,
});

export function showCase(shown: Case, stepsShown: Step[] = []) {
  const routes: Routes = {
    "GET /api/cases/CLM-1002": shown,
    "GET /api/cases/CLM-1002/steps": stepsShown,
    "GET /api/contracts/POL-2002": contract,
    "GET /api/customers/CUS-3002/cases": history,
  };
  const fetchMock = stubApi(routes);
  renderAt("/cases/CLM-1002");
  return { routes, fetchMock };
}

export const decisionPanel = () => panel("Decision");

export const approval: Decision = {
  decision: "approve",
  award: 420,
  calculation: {
    lines: [
      { step: "Suitcase, limited to $300.00", amount: 300 },
      { step: "Clothes", amount: 170 },
      { step: "Less the deductible", amount: -50 },
    ],
    award: 420,
  },
  section: "Section 5, Baggage and Personal Effects",
  reason: "The suitcase was lost by the carrier.",
  decided_by: "CRM Agent, version 1",
  decided_at: decidedAt,
  manual_version: "2026.2",
  signed_off_by: null,
  signed_off_at: null,
  gateway_refusal: null,
};

export const approved: Case = {
  ...entry,
  status: "decided",
  thread_id: "t-1",
  decision: approval,
  payment: {
    amount: 420,
    paid_at: decidedAt,
    signed_off_by: null,
    signed_off_at: null,
  },
};

export const held: Case = {
  ...approved,
  status: "waiting_for_sign_off",
  decision: { ...approval, award: 1350 },
  payment: null,
};
