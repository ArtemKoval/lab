# The backoffice brief

From the head of operations at the insurance domain of the crm engine.

## How the work runs today

The insurer sells travel cover on three plans: Economy, Premium, and First.
Three case workers work a queue of claims by hand. For each claim, a worker
reads the customer's story and documents and weighs them against the
contract and the policy wording. Then the worker approves the claim with a
payout, declines it, or refers it. The manual explains when a claim goes to
a person.

## What the engine does

The case agent works the queue the way a worker does. For each case it:

- reads the case, the customer's contract and history, and the sections of
  the wording and the manual it needs
- approves, declines, or refers the case
- works out the award when it approves
- explains the decision in two or three sentences, with the sections it
  relied on

The goal is to work cases straight through, as accurately as the workers.

## What the team sees

- The queue, with where each case stands: waiting, in progress, waiting for
  sign-off, or decided.
- Each case in full, with the agent's steps, its decision, and its reasons.
- The run panel, with the agent's to-do list for the current run.
- The agent's instructions, read only.

## Rules

- An award over 1,000 dollars needs a worker's sign-off. The agent can
  approve such a case, but the payment waits until a worker signs off. The
  system blocks the payment until then, even if the agent tries to pay.
- Decisions follow the policy wording and the manual.
- The workers' own decisions on these cases sit in the pack evals. The
  engine uses them to score the agent later. The agent never sees them.
- Amounts are in US dollars.

## Records

The pack at `crm/domains/insurance/` holds the queue, the contracts, the
customers, the plans, the workers, the wording, the manual, and the held-out
decision sets. The held-out sets stay out of the queue.
