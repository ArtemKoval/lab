# A Personal Lab of Art Koval

## Communication Style

Write messages, reports, code comments, commit messages, and documentation in ASD-STE100 Simplified Technical English (STE), Issue 9. Do not use STE rules for code, commands, paths, identifiers, error messages, quoted text, or names. If the user tells you to use a different style for content, use that style. Use approved STE words, technical nouns, and technical verbs, each with one meaning and one part of speech. Write "do" (not "perform"), "use" (not "utilize"), "make sure" (not "ensure"), "give" (not "provide"), and "examine" (not "check"). Use the active voice. Do not use perfect tenses, progressive tenses, phrasal verbs, contractions, or semicolons. Use "-ing" forms only in technical nouns. Write one topic in each sentence. Use a maximum of 20 words in a procedural sentence and 25 words in a descriptive sentence. Do not write multi-word nouns of more than three words. In procedures, write each step as one imperative instruction, with the condition first. The ASD-STE100 output style at .claude/output-styles/asd-ste100.md has the full rules.

## Workflow
- Every repository change goes through the `feature-pipeline` skill; questions that change nothing don't.
- VCS: Git on GitHub. Mainline is `main`; review via pull requests (`gh`); squash-merge, then delete the branch.

## Specs
- Behavior specs: `openspec/specs/` (source of truth). In-flight changes: `openspec/changes/`.