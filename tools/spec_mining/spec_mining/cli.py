"""The spec_mining CLI: one run writes the mining report set.

Exit 0 when the run completed and 2 when a fact call failed, with the
reason on stderr and an empty stdout. `--json` switches the human report
on stdout for one machine payload on the success path.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import core

META_ROOTS = {"adr", "glossary", "openspec", "reports", "target", "tests", "tools"}
SCENARIO_RE = re.compile(r"^#### Scenario: (.+)$", re.MULTILINE)
SECTION_RE = re.compile(r"^## (\w+) Requirements$", re.MULTILINE)
DELTA_SECTIONS = ("ADDED", "MODIFIED")
GIT_LOG_ARGS = ("git", "log", "--name-only", "--format=%H", "main")
OWNED_FILES = ("coverage.json", "report.md")


def run_git(argv):
    """Run one git call whose argv carries the program name."""
    try:
        proc = subprocess.run(
            list(argv), capture_output=True, text=True, check=False
        )
    except OSError as exc:
        return 1, "", f"the git call failed: {exc}"
    return proc.returncode, proc.stdout, proc.stderr


def _walk(root):
    """Return the unit paths per class from the tree."""
    root = Path(root)
    tools = [
        f"tools/{p.name}" for p in sorted((root / "tools").glob("*")) if p.is_dir()
    ]
    hooks = [
        f".claude/hooks/{p.stem}"
        for p in sorted((root / ".claude" / "hooks").glob("*"))
        if p.is_file()
    ]
    skills = [
        f".claude/skills/{p.name}"
        for p in sorted((root / ".claude" / "skills").glob("*"))
        if p.is_dir()
    ]
    projects = [
        p.name
        for p in sorted(root.iterdir())
        if p.is_dir() and not p.name.startswith(".") and p.name not in META_ROOTS
    ]
    return {
        "tools": tools,
        "hooks": hooks,
        "skills": skills,
        "projects": projects,
    }


def _load_data():
    """Return the committed units.json from the package."""
    return json.loads((Path(__file__).parent / "units.json").read_text())


def _delta_scenarios(text):
    """Return the scenario names of the ADDED and MODIFIED sections."""
    parts = SECTION_RE.split(text)
    names = []
    for i in range(1, len(parts) - 1, 2):
        if parts[i] in DELTA_SECTIONS:
            names.extend(SCENARIO_RE.findall(parts[i + 1]))
    return names


def _archive_rows(root):
    """Return one parsed delta row per archived change and capability."""
    archive = Path(root) / "openspec" / "changes" / "archive"
    rows = []
    for change in sorted(p for p in archive.iterdir() if p.is_dir()):
        for spec in sorted((change / "specs").glob("*/spec.md")):
            rows.append(
                {
                    "change": change.name,
                    "capability": spec.parent.name,
                    "scenarios": _delta_scenarios(spec.read_text(encoding="utf-8")),
                }
            )
    return rows


def _spec_scenarios(root):
    """Return the scenario names per capability in openspec/specs/.

    The capability name is the path under specs/, so nested capability
    directories like fde/backend-service keep their full name.
    """
    specs = Path(root) / "openspec" / "specs"
    held = {}
    for spec in sorted(specs.rglob("spec.md")):
        name = spec.parent.relative_to(specs).as_posix()
        held[name] = SCENARIO_RE.findall(spec.read_text(encoding="utf-8"))
    return held


def _git_commits(runner):
    """Return (commits, error) from the one bounded git log call.

    Each commit is the list of the file paths it touches.
    """
    code, out, err = runner(list(GIT_LOG_ARGS))
    if code != 0:
        return None, err.strip() or f"the git log exited with code {code}"
    commits = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            commits.append([])
        elif commits:
            commits[-1].append(line)
    return commits, None


def _counts(commits, uncovered):
    """Return the commit counts per uncovered unit path."""
    counts = {row["unit"]: 0 for row in uncovered}
    for files in commits:
        for unit in counts:
            if any(p == unit or p.startswith(unit + "/") for p in files):
                counts[unit] += 1
    return counts


def _candidate(unit):
    """Return the kebab candidate name of one unit path."""
    return core.normalize(unit.rsplit("/", 1)[-1])


def _seed_text(candidate, units, commits, drift_rows):
    """Return the scaffold proposal text for one candidate capability."""
    lines = [
        f"# Proposal: add-{candidate} (seed)",
        "",
        "## Why",
        "",
        "Retroactive mining found this surface without OpenSpec coverage.",
        "",
        "## What Changes",
        "",
        "- (describe the change)",
        "",
        "## Capabilities",
        "",
        "### New Capabilities",
        "",
        f"- `{candidate}`: (describe the capability)",
        "",
        "### Modified Capabilities",
        "",
        "- (none)",
        "",
        "## Impact",
        "",
        "Mined evidence:",
        "",
    ]
    for unit in units:
        lines.append(f"- unit `{unit['unit']}` with {commits.get(unit['unit'], 0)} commits")
    for row in drift_rows:
        lines.append(f"- drift: `{row['scenario']}` from {row['change']}")
    return "\n".join(lines) + "\n"


def _report_text(payload):
    """Return the human summary text of one run."""
    lines = ["# Spec mining report", ""]
    uncovered = payload["tree"]["uncovered"]
    lines.append(f"Uncovered units: {len(uncovered)}")
    for row in uncovered:
        lines.append(f"- {row['unit']} ({row['class']})")
    stale = payload["tree"]["stale"]
    lines.append("")
    lines.append(f"Stale data-file entries: {len(stale)}")
    for unit in stale:
        lines.append(f"- {unit}")
    lines.append("")
    lines.append(f"Archive drift entries: {len(payload['drift'])}")
    for row in payload["drift"]:
        mark = " (missing spec)" if row["missing_spec"] else ""
        lines.append(f"- {row['capability']}: {row['scenario']}{mark}")
    lines.append("")
    lines.append("Ranking by merged commits:")
    for row in payload["ranking"]:
        lines.append(f"- {row['area']}: {row['commits']}")
    return "\n".join(lines) + "\n"


def _write_run(root, today, payload, data_specs):
    """Write the report set into the dated run directory."""
    run_dir = Path(root) / "reports" / "spec_mining" / today
    run_dir.mkdir(parents=True, exist_ok=True)
    for owned in OWNED_FILES:
        target = run_dir / owned
        if target.exists():
            target.unlink()
    drafts = run_dir / "drafts"
    if drafts.exists():
        shutil.rmtree(drafts)
    (run_dir / "coverage.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "report.md").write_text(_report_text(payload), encoding="utf-8")
    return _write_drafts(run_dir, payload)


def _write_drafts(run_dir, payload):
    """Write one seed per candidate capability."""
    drafts = run_dir / "drafts"
    by_candidate = {}
    for row in payload["tree"]["uncovered"]:
        by_candidate.setdefault(_candidate(row["unit"]), []).append(row)
    for candidate, units in sorted(by_candidate.items()):
        commits = {r["area"]: r["commits"] for r in payload["ranking"]}
        drift_rows = [
            r for r in payload["drift"] if r["capability"] == candidate
        ]
        target = drafts / candidate / "proposal.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            _seed_text(candidate, units, commits, drift_rows), encoding="utf-8"
        )


def _gather(root, runner):
    """Return (payload, error). The payload is None on a failed fact."""
    if not (Path(root) / "openspec" / "specs").is_dir():
        return None, "the openspec/specs directory is missing"
    if not (Path(root) / "openspec" / "changes" / "archive").is_dir():
        return None, "the openspec/changes/archive directory is missing"
    units = _walk(root)
    specs = _spec_scenarios(root)
    tree = core.scan_tree(units, set(specs), _load_data())
    drift = core.scan_drift(_archive_rows(root), specs)
    paths, error = _git_commits(runner)
    if error:
        return None, f"the git read failed: {error}"
    ranking = core.rank(_counts(paths, tree["uncovered"]))
    return {"tree": tree, "drift": drift, "ranking": ranking}, None


def main(argv=None, run=None, repo_root=None, today=None):
    """Run the mining run subcommand and return the exit code."""
    parser = argparse.ArgumentParser(prog="spec_mining")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--repo-root", default=None, help="The repository root for the reads"
    )
    args = parser.parse_args(argv)
    root = repo_root if repo_root is not None else args.repo_root
    root = Path(root) if root is not None else Path.cwd()
    dispatch = run if run is not None else run_git
    payload, error = _gather(root, dispatch)
    if error:
        print(f"spec_mining: {error}", file=sys.stderr)
        return 2
    stamp = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _write_run(root, stamp, payload, None)
    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_report_text(payload))
    return 0
