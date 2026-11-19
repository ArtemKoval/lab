// The improvement loop's shapes: rounds, proposals, versions, and recipes.
// The types live here so api.ts stays under its line budget, and api.ts
// re-exports them for the pages. The cycle is type-only, so it erases at
// compile time.
import type { Diff, Evaluation, Measures, Verdict } from "./api";

export type RoundStatus = "open" | "finished" | "stopped";
export type RoundStage =
  | "first_evaluations"
  | "improving"
  | "change_waiting"
  | "evaluating"
  | "verdict"
  | "recipe_waiting";
export type ProposalKind = "change" | "recipe";
export type Review = "approved" | "rejected";

// Who approved or rejected one of the improver's proposals, and when.
export interface RoundReview {
  kind: ProposalKind;
  review: Review;
  reviewed_by: string;
  reviewed_at: string;
  rejection_reason: string | null;
}

// The proposal waiting for a worker, with what it would change. A recipe has
// no model.
export interface WaitingProposal {
  proposal_id: string;
  kind: ProposalKind;
  reason: string;
  proposed_at: string;
  diff: Diff;
  model_before: string | null;
  reasoning_effort_before: string | null;
  model_after: string | null;
  reasoning_effort_after: string | null;
}

export interface RoundSummary {
  round_id: string;
  number: number;
  status: RoundStatus;
  // Where an open round has got to, and how far, such as "2 of 3".
  stage: RoundStage | null;
  progress: string | null;
  started_by: string;
  started_at: string;
  finished_at: string | null;
  stopped_by: string | null;
  stopped_because: string | null;
  recipe: number;
  settings: number;
  spending_limit: number;
  cost: number;
  // The version the round tried, if any, and its verdict.
  version: number | null;
  model: string | null;
  reasoning_effort: string | null;
  reason: string | null;
  verdict: Verdict | null;
  verdict_reason: string | null;
  held_out_before: Measures | null;
  held_out_after: Measures | null;
  reviews: RoundReview[];
}

export interface RoundView extends RoundSummary {
  waiting: WaitingProposal | null;
  evaluations: Evaluation[];
}

// A version's held-out accuracy and grade, for the chart.
export interface VersionPoint {
  number: number;
  verdict: Verdict | null;
  accuracy: number | null;
  grade: number | null;
}

export interface RecipeSummary {
  number: number;
  current: boolean;
  reason: string;
  proposed_by: string;
  round_id: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  lines_added: number;
  lines_removed: number;
}

export interface RecipeDetails extends RecipeSummary {
  recipe: string;
  diff: Diff | null;
}

export interface Improvement {
  // The open round, or the newest.
  round: RoundView | null;
  rounds: RoundSummary[];
  first_version: VersionPoint;
  versions_tried: VersionPoint[];
  recipes: RecipeSummary[];
}
