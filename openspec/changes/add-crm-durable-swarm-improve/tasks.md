# Tasks: add-crm-durable-swarm-improve

## 1. Durable state (week2day3)

- [ ] 1.1 Run the port pass one and remove the files the milestone deletes.
- [ ] 1.2 Move the payout engine into `domains/insurance/rules.py` behind the pack contract, and pin the contract with pack tests.
- [ ] 1.3 Port the SQLAlchemy dual engine, the calculations table, and the refusal of a mismatched award.
- [ ] 1.4 Port the hand-written case-agent graph with the saver factory, the interrupt for sign-off, and the pay step.
- [ ] 1.5 Port the agent service on port 8002, the resume after sign-off, and the idempotent decision and payment repeats.
- [ ] 1.6 Port the durable-state tests: restart carries a case, sign-off resumes, repeats return, failures start afresh.

## 2. Swarm (week2day4)

- [ ] 2.1 Run the port pass two and remove the files the milestone deletes.
- [ ] 2.2 Port the dispatcher, the run records, and the cost and time records.
- [ ] 2.3 Port the evaluations with their copies, the scoring, and the scoreboard.
- [ ] 2.4 Port the dashboard dispatch panel, run panel, scoreboard, and evaluation pages.
- [ ] 2.5 Port the swarm tests: parallel dispatch, one-bad-case recovery, second-start refusal, run totals, evaluation copies.

## 3. Self-improvement (week2day5)

- [ ] 3.1 Run the port pass three and remove the files the milestone deletes.
- [ ] 3.2 Port the auth service, the backend JWT gate, and the dashboard sign-in, and pin the token contract with a test.
- [ ] 3.3 Port the versions, the judge, the improver, the rounds, the recipes, the spending limits, and the verdict.
- [ ] 3.4 Port the settings table, the settings page, and the pack models and improvement data.
- [ ] 3.5 Port the dashboard configuration, improvement, settings, and sign-in pages, and the enterprise UI pass.
- [ ] 3.6 Port the improvement tests: versions, judge grades, round flow with the stub model, spending limit, verdict, and role refusals.

## 4. Infra, docs, and gates

- [ ] 4.1 Update `.env.example`, the devcontainer, the registry, the `crm-app` skill, and `crm/docs` for the new services and variables.
- [ ] 4.2 Port the e2e specs and stand-ins for the new pages, with the auth stand-in.
- [ ] 4.3 Run the crm suite, the root suite, and the three gate tools, and raise the coverage floor to the new total.
- [ ] 4.4 Commit the three milestone commits, push, and open the pull request.
- [ ] 4.5 Run the adversarial review on the diff, fix the confirmed findings, and merge, then archive through the archive pull request.
