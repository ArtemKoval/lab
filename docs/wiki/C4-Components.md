# C4 components

Inside the backend container: the parts one case passes through.

```mermaid
flowchart TB
    routes["Routes<br/>cases, runs, settings"]
    decisions["Decision pipeline<br/>resolve, gate, sign-off"]
    loader["Pack loader<br/>the one seam"]
    runs["Runs and evaluations<br/>dispatch, judge, scoreboard"]
    improvement["Improvement engine<br/>versions and rounds"]
    authz["Auth dependency<br/>worker or agent key"]
    db[("SQLite")]

    routes --> authz
    routes --> decisions
    decisions --> loader
    routes --> runs
    runs --> improvement
    routes --> db
    runs --> db
    loader --> db
```

## Notes

- **The seam.** The loader is the only module that reads a pack, and the
  protocol verbs (`resolve`, `gate`, `execute`, `summarize`, `metric`) are
  the only code a pack ships.
- **The gate.** Every approval passes the pack's sign-off question; a held
  decision waits for a lead and cannot pay before one.
- **The improvement engine.** Held-out sets, judge grades, and instruction
  versions; the lead approves what ships.
