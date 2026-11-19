# Case flow

One case, from the queue to the executed outcome. The sequence shows the
library desk of the current assignment; every pack follows the same shape.

```mermaid
sequenceDiagram
    participant w as Desk worker
    participant b as Backend
    participant a as Case agent
    participant l as Lead worker

    w->>b: Start a dispatch
    b->>a: Work the waiting cases
    a->>b: Read the case, the membership, the wording
    a->>b: resolve the outcome, record the decision
    alt term over the limit
        b-->>w: Held for sign-off
        l->>b: Sign off the held decision
    end
    b->>b: Run the effect and write the record
    b-->>w: Decided, with the reason and the calculation
```

## Where to watch it

- The queue page shows each case's state: waiting, in progress, held,
  decided.
- The run panel follows a dispatch while it works.
- The scoreboard keeps the score of every run and evaluation.
- [Screenshots](Screenshots.md) captures each step of this flow on the
  library pack.
