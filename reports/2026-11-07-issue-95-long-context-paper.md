# Analysis: "You don't need long context" — proposals for this harness

- Issue: ArtemKoval/lab#95
- Paper: arXiv 2611.05306, "You don't need long context", Muralidharan et al., November 2026
- Date: 2026-11-07
- Status: analysis only. The proposals in section 5 need approval. Each proposal ships as its own change through the feature pipeline.

## 1. Scope

This run examines the paper and maps its results to the harness surfaces in this repository. This run does not change any skill, hook, or tool. Section 5 lists six proposals. The user picks the proposals to build. Each build is a separate change with its own review and gates.

## 2. What the paper shows

The paper studies the two workload types that produce long contexts: long-horizon tasks and long-input tasks. It compares three context regimes on 13 benchmarks against two frontier models, Claude Opus 4.5 and GPT 5.6 Sol:

- **FHA** (Full-History Accumulation): the baseline. Every action and result stays in one conversation.
- **EoCC** (End-of-Conversation Compaction): the conversation resets to the task plus a compacted state when the context crosses a threshold.
- **SAC** (Single-Action Compaction): each conversation gets the task, the current semantic state, and one action. The harness then discards the conversation.

Results, with the paper's numbers:

1. **Long-horizon tasks.** EoCC accuracy stays close to the FHA baseline. No more than 5 of 22 threshold configurations lose more than 2 percentage points. Estimated cost savings: 2.2x to 8.8x.
2. **Long-input tasks.** Selective reading (search first, then bounded reads) matches or beats the full-input baseline on almost every benchmark. RULER mean recall goes from 62.5 to 95.7 for Opus 4.5. BABILong accuracy gains 24.9 points. Cost savings reach 233.3x.
3. **Single-action contexts.** SAC keeps or nearly keeps the baseline accuracy. Median peak context falls from 130K to 200K tokens down to 7K to 9K tokens.
4. **Serving cost.** A 256K context window costs 3.6x to 7x more per output token than a 16K window on the same hardware. Local decode latency roughly doubles across the measured context lengths.
5. **Compaction quality.** Appendix A: the best compactions are briefs for future work, not narratives of the past. A good compaction carries the verbatim task, the current occupation and next step, the decomposed plan, the completion rules, and pointers to artifacts.
6. **Failure mode.** Appendix D: one open-weight model collapses at tight compaction limits because its verbose trajectories leave no room for progress. It falls from 53.0 to 3.6 on SWE-bench Verified.

Section 3.1 adds one rule: compaction is lossy. Information that a later step needs must stay retrievable. The harness keeps a full record outside the context and gives the agent a selective reader.

## 3. Method

1. Fetch the paper HTML from arxiv.org/html/2611.05306 and read it in full.
2. Examine the repo surfaces: the charter hook and charter text, the handover issue template, the plan_exec README, the handover_telemetry README, the adversarial agent definitions, and the feature-pipeline skill.
3. Map each paper result to the surfaces, and derive the proposals.

Note on the PDF: arxiv.org/pdf/2611.05306 needs poppler-utils for local rendering, and this host does not have it. The HTML rendering covers the full text, including the appendices.

## 4. Where the repo already follows the paper

| Paper idea | Repo surface |
| --- | --- |
| A fresh context with carried state | The charter hook injects the charter at session start, clear, and compaction. |
| A semantic state between contexts | The plan_exec ledger and the tasks.md ticks. The plan_exec README says: "Run `show` after a compaction. Trust the ledger and `git log` over recollection." |
| A full record outside the context, with a selective reader | The cc-logging hook writes `.cc_logging/` out of context. The handover_telemetry CLI reads the log and the transcripts on demand. |
| One action per fresh context | Each agent dispatch, for example a fork or the adversarial pair, starts with no history and one brief. |
| Compaction into a brief at the end of a run | The handover issue and its template. |
| Cost discipline | The peak-hours gate and the zai_routing_audit tools. |

The architecture already matches the paper. The gaps sit in coverage and detail, not in structure.

## 5. Proposals

Order: value against effort.

### P1. Make the ledger rule cover every multi-step run — high value, low effort

Today only the OpenSpec apply flow keeps a ledger. A long run in another pipeline step keeps its state in the conversation, and a compaction erases that state. The paper shows that a carried semantic state holds accuracy at any compaction frequency, and plan_exec already gives the mechanism.

- Change: the feature-pipeline skill gets one rule. A run that crosses several steps starts a ledger with plan_exec and appends one entry at each step boundary.
- Change: the charter gets one line. After a compaction, run the ledger show command and read the change artifacts before the next action.
- ASIT: Unification. plan_exec takes any markdown plan, so no new tool is necessary.

### P2. Add two lines to the charter — high value, low effort

- Line 1: after a compaction, re-establish the task state from the ledger, the change artifacts, and git log before the next action.
- Line 2: keep tool output small. Write a large output to a file and read it in bounded windows.

Evidence: Appendix G says "Keep command output focused". Appendix D shows the collapse case for verbose trajectories.

### P3. Add "Dead ends" to the handover template — medium value, low effort

The paper's compaction prompt records dead ends: failed approaches that later work must not repeat. The handover template has Observations and Follow-ups but no dead-ends section. The Observations guidance also does not separate verified facts from unverified ideas.

- Change: add a `## Dead ends` section to `.github/ISSUE_TEMPLATE/handover.md`.
- Change: extend the Observations comment. It tells the writer to separate verified facts from unverified ideas.
- Change: extend `tests/claude_infra/test_working_rules.py` to pin the new section.

### P4. Write the selective-reading rule for long inputs — high value, low effort

The paper converts a long-input task into a long-horizon task. The input stays in a file, and the agent reads it with search commands and bounded windows. Accuracy matches or beats full ingestion, and the cost falls by large factors.

This run fetched the paper HTML as one document, and the paper fits one fetch. Larger inputs, for example a transcript set or a big log, do not fit one fetch.

- Change: the feature-pipeline skill gets a rule for tasks with long inputs. The run saves the input to a file and reads it with targeted, bounded reads. The run does not paste whole documents into the conversation.
- CLAUDE.md already says "Build a tool first". This rule covers the reading side.

### P5. Put the brief checklist into the agent dispatch guidance — medium value, low effort

Appendix A defines the brief that keeps a fresh context effective. Section 5 shows that a fresh context works at one action per context when the brief is good.

- Change: the feature-pipeline inner loop gets a dispatch checklist. Every agent brief carries: the task text verbatim, the current state and the rejected options, exact file pointers, the expected output shape, and a narrow command that retrieves anything truncated.

### P6. Add a context-size block to handover telemetry — medium value, medium effort

The repo does not control the provider context window. It can measure the context it sends. handover_telemetry already parses the transcripts and the hook log. A block with the input-token distribution per call, median and peak, makes the effect of P1 to P5 visible in every handover issue.

- Change: new fields in the report and the JSON output.
- The spec at `openspec/specs/handover-telemetry/` owns the behavior, so this proposal needs a spec delta and its gates.

## 6. Non-goals

- No new skill, hook, or tool in this run. P1 to P5 are text edits to surfaces that exist. P6 is a tool change with its own spec delta.
- No change to the model context window at the serving level. The repo does not control the provider.

## 7. Sources

- Paper: https://arxiv.org/abs/2611.05306 (HTML: https://arxiv.org/html/2611.05306)
- Issue: https://github.com/ArtemKoval/lab/issues/95
