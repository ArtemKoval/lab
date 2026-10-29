# The port tool

The tool ports one upstream milestone tree into `crm/`. It reads blobs from a
local clone of `github.com/ed-donner/undercover`, maps engine paths to crm
paths, applies the engine rename to engine files, and copies pack content
verbatim with schema-key renames only. The openspec change artifacts own the
mapping decisions. This tool carries them out and keeps the three port
changes consistent.

## The rename

Engine code gets word-boundary renames: claim to case, payout to award,
handler to worker, policy to contract, and the two document names
`policy_wording` to `wording` and `claims_manual` to `manual`. Upstream
variable names map first: `UNDERCOVER_DB` to `CRM_DB` and its siblings in
the table in `port.py`. The brand strings become `CRM` in engine code.
Pack content under `crm/domains/` keeps its text verbatim. Pack JSON gets
schema-key renames only, and values stay untouched.

## Passes

Run from the repository root. The pass for each milestone diffs the two
milestone refs, so each change ports only its own delta. Files that both
milestones touch port twice, and the second pass wins.

```bash
# Change one, pass one: the pilot (week1day3)
python3 crm/port/port.py --ref week1day3-end --base main --dest crm \
  --file .gitignore --file .python-version --file .nvmrc --file .npmrc \
  --file .gitattributes --file eslint.config.js --file tsconfig.json \
  --file pyproject.toml

# Change one, pass two: the harness (week1day5)
python3 crm/port/port.py --ref week1day5-end --base week1day3-end --dest crm
```

The passes skip the upstream course folders, the docs that this repository
rewrites, and the lockfiles, which a fresh `npm install` and `uv sync`
regenerate. A file that a later milestone deletes is removed by hand in that
change. Give `--dry-run` to print the mapping without writing. The
`UPSTREAM_REPO` variable moves the upstream clone. The default is
`/home/repos/undercover-upstream`.
