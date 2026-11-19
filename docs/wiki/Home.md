# The library assignment wiki

This is the wiki of the library assignment
([issue 1](https://github.com/ArtemKoval/library_crm/issues/1)). The GitHub
wiki of this repository stays disabled, because private repositories on the
free plan carry no wiki. These pages are the wiki, and they live in version
control beside the code they document.

## Pages

- [Architecture](Architecture.md) — the C4 view: context, containers,
  components, the case flow, and deployment.
- [Screenshots](Screenshots.md) — the loan desk flow, captured end to end.
- [Library domain](Library-Domain.md) — the loan desk: entities, rules, and
  the flow of one request.
- [IT setup](IT-Setup.md) — the stack, the install, the run, the
  devcontainer, and the floci emulator.
- [Agentic harness](Agentic-Harness.md) — the software factory: inception,
  construction, and observability.
- [Self-improving agent](Self-Improving-Agent.md) — the loop that raises the
  desk agent's score.

## The four videos

Each video runs about one minute, with narration. The files live under
[docs/videos/](../videos/), with their decks under
[docs/videos/decks/](../videos/decks/):

| Video | File |
| --- | --- |
| Business setup | [business.mp4](../videos/business.mp4) |
| IT setup | [it.mp4](../videos/it.mp4) |
| The software factory | [factory.mp4](../videos/factory.mp4) |
| The self-improving agent | [self-improving.mp4](../videos/self-improving.mp4) |

## Where the records live

- The setup around the agents: [HARNESS.md](../../HARNESS.md)
- The team-scale plan: [SCALE.md](../../SCALE.md)
- The behavior specs: [openspec/specs/](../../openspec/specs/)
- The handover issue with the run telemetry: issue 6
