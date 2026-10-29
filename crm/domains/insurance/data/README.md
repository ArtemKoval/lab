# CRM seed data

The data behind CRM, a fictional insurer. Everything here is invented, including the people, the airlines and the hotels. Amounts are in US dollars.

## The insurer's systems

- `company.json`: company settings, including the $1,000 award approval limit.
- `plans.json`: the three plans (Economy, Premium, First) with their limits, waiting periods and deductibles, and the three add-ons.
- `contracts.json`: one contract per trip, with the plan, the add-ons, the purchase date, the trip and the travelers.
- `customers.json`: contact details and case history, with the date and a one line summary of each earlier case. This is personal data.
- `workers.json`: the cases workers.
- `cases.json`: the cases queue, twenty-five cases. Each has the customer's story, the items claimed and the supporting documents as text.

## The documents

- `wording.md`: the contract with the customer. Short enough to fit in a prompt.
- `manual.md`: the internal handling manual. Longer, and it holds rules the wording does not, such as the third case in 12 months, losses to wild animals and meals without receipts.

## The evaluation set

- `evals/decisions.json`: the workers' decisions on the twenty-five cases in the queue: approve, decline or refer, the award, the calculation, the reason and what each case tests. An agent deciding cases must never be shown this file.
- `evals/held_out_cases.json` and `evals/held_out_decisions.json`: twenty-five more cases with their decisions, kept out of the queue for checking that an improvement generalizes. They have the same blend as the queue. Keep them out of sight while you write a prompt or a rule, and score them afterwards.

The queue is the development set and the held-out cases are the test set. Nothing is trained on either.

Every decision also carries a few tags. `difficulty` is `routine`, `hard` (the wording settles it and it stretches a small model) or `manual` (it needs something the prompt does not hold, listed in `needs`: the cases manual, the customer's history or both). `failure_class` groups the hard cases that one rule should fix. `tone` is `plain`, `amusing` or `nod`. `tiny` marks a subset of five cases in each set, one of each kind, which fits inside a free model's daily allowance.

The labs define `get_sample_data(tiny=False, held_out=False)`, which returns the cases of either set with their decisions.

A decision is scored on two things: the decision itself and the award. A valid case that pays more than $1,000 is still an approve. The payment waits for a worker's sign-off, and `over_approval_limit` marks those cases.

## The security case

- `security/`: CLM-1901, a stolen watch whose story carries an instruction to the AI to approve it in full, with its contract, its customer and the worker's decision (decline). It is a prompt injection kept for security testing, in a folder of its own, apart from the queue and the evaluation sets.
