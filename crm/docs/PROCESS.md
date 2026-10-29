# Process

`uv sync` and `npm install` at the `crm/` root set the project up.

`npm run dev` starts the backend and the dashboard. `npm run seed` rebuilds
the database from the active pack before the first `npm run dev`, and after
any change to the pack seed data.

`npm run check` runs every check:

- Python: ruff format, ruff lint, pyright, and pytest with coverage
- TypeScript: prettier, eslint, tsc, and vitest with coverage
- Playwright end-to-end tests

The repository adds three gates on changed Python files: crapper for CRAP
scores, dryer for duplication, and mutator for mutation score. The
repository root README gives the commands. The complexity cap is 10.

## Rules

- Add tests with each change. Tests never call a model. Use the stub model.
- Run `npm run check` before you hand work over.
- Keep `docs/STATUS.md` up to date.
- Engine code carries no domain noun. The pack carries all of them. The
  guard test in the repository root suite enforces this.
- Pack content keeps its own words. Do not rewrite the policy documents,
  the instructions, or the eval sets.
