---
name: Handover
about: Logs, metrics, and observations from a solved task, for later analysis
labels:
  - handover
---

<!-- Open this issue after you merge the pull request. Remove secrets before
     you paste any artifact. Build the Telemetry block with the
     handover-telemetry tool (see the handover-telemetry skill). -->

## Task

<!-- What the task was. Give the pull request link and the merged commit. -->

## Telemetry

<!-- Paste the tool output here: handover_telemetry build --out report.md.
     The block is redacted, and its numbers are estimates with source dates. -->

## Logs

<!-- Command output, traces, and run logs that show what happened. -->

## Gates

<!-- One line per quality gate this run ran or skipped: the command, the
     result, and the exit code. A skip carries the reason: an env gate,
     missing credentials, or not applicable. A gate that vanished from the
     run without a reason counts as a failed gate. -->

## Metrics

<!-- Numbers from the run that the tool does not carry: coverage,
     mutation score, sizes. -->

## Observations

<!-- What behaved differently from the plan. Ideas and causes for later work. -->

## Follow-ups

<!-- Links to the issues that this run opened, or write "None". -->
