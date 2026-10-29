# Status

The port of the UnderCover week one milestones is complete.

## In place

- The pilot: the backend with the queue, cases, decisions, the award limit,
  sign-off, and payment, with the dashboard pages and the first agent.
- The harness: queue runs with a cap, the to-do list, one fresh subagent per
  case, section lookup in the wording and the manual, the failure path with
  one retry, and the check for missed cases.
- The insurance pack: the manifest, the seed data, the wording, the manual,
  the instructions, and the held-out eval sets.
- The dev container, the registry units, and the `crm-app` skill.

## Not in place

- The sign-in. Everyone who uses the screens sees everything.
- The deterministic award engine. The agent works the award out itself.
- The durable checkpoints. A restart loses a run in progress.
- The dispatch panel, the scoreboard, and the self-improvement rounds.
- The AWS targets under the local emulator.
- The onboarding skill for a new domain.

A later change ports the upstream week two milestones: durable state, the
swarm, and self-improvement.
