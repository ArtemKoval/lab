# 0015 - Remove the fde mutation carve-out

- Status: accepted
- Date: 2026-11-09

## Context

The charter names one mutation bar: no surviving mutant on changed
code. The fde area sits outside that bar today. The tests workflow
ignores the `fde/**` paths, so the root suite job never gates a fde
change, and the fde backend keeps its own mutmut target at 95
percent. The saturation baseline of issue 123 measured nine owned
tools and left fde outside, and ADR 0014 placed the scheduled pass
over those nine. The handover issue of the saturation run asked the
operator to decide the carve-out, and the operator chose removal:
fde joins the same bar. The fde work itself is a separate, larger
effort inside the fde area.

## Decision

Remove the fde mutation carve-out in steps. The fde Python backend
moves to the no-survivors mutation bar under its own area suite, and
the fde mutmut target rises from 95 percent to the bar. When the fde
suite holds the bar, the tests workflow drops `fde/**` from its
`paths-ignore` lists, and the root gates cover fde changes like
every other area. That workflow edit touches a protected gate path,
so the pull request carries the gate-integrity acknowledgment. The
scheduled saturation pass keeps its nine-tool table, and a later
change adds fde to the table with its own area suite. Until those
steps
land, the carve-out stays in place, and this record marks it as
debt.

## Consequences

The charter text stays unchanged, because it already names no
exemption. The fde area gains the mutation work: its suite needs
assertions that kill every mutant of the backend. The tests workflow
change is a protected gate path and needs the operator acknowledgment
at that step. The ratchet and the scheduled pass gain one tool when
fde joins the table, and its baseline moves only through review. No
root gate changes now, so this record carries no CI risk on its own.
