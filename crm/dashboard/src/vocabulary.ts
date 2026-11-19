// The pack's words: the labels, the contract rows, and the award's unit.
// The pack endpoint serves the vocabulary section, and every page reads its
// words through this module's lookup. A key the pack names no word for falls
// back to the engine's current English words, so a page never goes blank.

import { createContext, useContext } from "react";
import { date, label, money } from "./format";

// One row of the pack's contract presentation: a label over one field, or a
// template over several, with the empty word for a record that holds nothing.
export interface ContractRow {
  label: string;
  field?: string;
  format?: string;
  template?: string;
  formats?: Record<string, string>;
  empty?: string;
}

export interface Vocabulary {
  labels?: Record<string, string>;
  benefit?: string;
  contract?: { title: string; rows: ContractRow[] };
  award_format?: "money" | "days";
  messages?: Record<string, string>;
}

export interface PackWords {
  vocabulary: Vocabulary | null;
}

export const PackWordsContext = createContext<PackWords>({
  vocabulary: null,
});

// The pack's word for a key, or the engine's fallback when the pack names
// none.
export function useLabel(): (key: string, fallback: string) => string {
  const { vocabulary } = useContext(PackWordsContext);
  return (key, fallback) => vocabulary?.labels?.[key] ?? fallback;
}

// The pack's benefit line an approval resolves, or nothing when the pack
// names none and the route falls back to the outcome's own name.
export function useBenefit(): string {
  const { vocabulary } = useContext(PackWordsContext);
  return vocabulary?.benefit ?? "";
}

// The pack's award format, money by default.
export function useAwardFormat(): "money" | "days" {
  const { vocabulary } = useContext(PackWordsContext);
  return vocabulary?.award_format ?? "money";
}

// The pack's contract presentation, or nothing when the pack names no rows
// and the panel keeps the core's own rendering.
export function useContractPresentation(): Vocabulary["contract"] | undefined {
  const { vocabulary } = useContext(PackWordsContext);
  return vocabulary?.contract;
}

// A value in the pack's award unit: money as money, days as a number of
// days. The number drops its trailing zero, so 14.0 reads `14 days`.
export function awardText(value: number, format: "money" | "days"): string {
  if (format === "days") return `${String(value)} days`;
  return money(value);
}

// One field of the contract record, at a dotted path, in a row's format.
export function fieldText(
  record: Record<string, unknown>,
  path: string,
  format: string,
): string {
  const value = path
    .split(".")
    .reduce<unknown>(
      (at, part) =>
        at && typeof at === "object"
          ? (at as Record<string, unknown>)[part]
          : undefined,
      record,
    );
  if (value === null || value === undefined || value === "") return "";
  switch (format) {
    case "date":
      return typeof value === "string" ? date(value) : "";
    case "money":
      return money(Number(value));
    case "days":
      return String(Number(value)) + " days";
    case "list":
      return (value as unknown[])
        .map((item) =>
          typeof item === "string" || typeof item === "number"
            ? String(item)
            : "",
        )
        .join(", ");
    default:
      return typeof value === "string" || typeof value === "number"
        ? label(String(value))
        : "";
  }
}
