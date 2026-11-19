import type { Measures } from "./api";
import { duration, grade, modelCost, percent } from "./format";
import { awardText } from "./vocabulary";

// A run that's running or stopped has no run time.
const NOT_FINISHED = "Not finished";
export const NOT_GRADED = "Not graded";

// The scoreboard's measures, in order, each with how it's shown. The cost
// of mistakes and the straight-through column carry the pack's words, since
// the library's mistake cost is days, not money.
export function MEASURES(
  awardFormat: "money" | "days" = "money",
  straightThrough = "Straight-through",
): {
  label: string;
  show: (measures: Measures) => string;
}[] {
  return [
    { label: "Decision accuracy", show: (m) => percent(m.decision_accuracy) },
    { label: "Accuracy", show: (m) => percent(m.accuracy) },
    {
      label: "Cost of mistakes",
      show: (m) => awardText(m.cost_of_mistakes, awardFormat),
    },
    { label: straightThrough, show: (m) => percent(m.straight_through) },
    {
      label: "Grade (of 3)",
      show: (m) => (m.grade === null ? NOT_GRADED : grade(m.grade)),
    },
    {
      label: "Model cost per case",
      show: (m) => modelCost(m.model_cost_per_case),
    },
    { label: "Time per case", show: (m) => duration(m.seconds_per_case) },
    {
      label: "Run time",
      show: (m) =>
        m.run_seconds === null ? NOT_FINISHED : duration(m.run_seconds),
    },
  ];
}
