"""The command line for handover_telemetry.

Subcommands build and sessions. The build reads one session transcript
plus the cc-logging hook log, and renders a redacted telemetry report
as markdown or JSON. The sessions listing names the candidate
transcripts. Exit 0 on success and 2 on operational failure. The gh
issue path runs only behind --create; every other path stays offline.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from . import logparse, machine, metrics, pricing, redact, render, transcript


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "sessions":
        return _run_sessions(args)
    return _run_build(args)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="handover_telemetry", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="render the telemetry report for one session")
    build.add_argument("--project-dir", type=Path, help="Claude Code project directory")
    build.add_argument("--transcript", type=Path, help="path to the session transcript")
    build.add_argument("--session", help="session id or transcript file stem")
    build.add_argument("--repo", type=Path, default=Path.cwd(), help="repository root")
    build.add_argument("--prices", type=Path, help="override the packaged price table")
    build.add_argument("--out", type=Path, help="write the report to this file")
    build.add_argument("--json", action="store_true", help="emit JSON with GenAI names")
    build.add_argument("--create", action="store_true", help="open the issue via gh")
    sessions = sub.add_parser("sessions", help="list the session transcripts")
    sessions.add_argument("--project-dir", type=Path, help="project directory")
    return parser


def _resolve_project_dir(args) -> Path:
    if args.project_dir is not None:
        return args.project_dir
    return transcript.project_dir_for(Path.cwd())


def _resolve_transcript(args, project_dir: Path) -> Path | None:
    if args.transcript is not None:
        return args.transcript
    if args.session is not None:
        named = project_dir / f"{args.session}.jsonl"
        if named.is_file():
            return named
    return transcript.newest_transcript(project_dir)


def _run_build(args) -> int:
    project_dir = _resolve_project_dir(args)
    path = _resolve_transcript(args, project_dir)
    if path is None or not path.is_file():
        name = path or project_dir
        print(f"handover_telemetry: no transcript at {name}", file=sys.stderr)
        return 2
    try:
        report = _build_report(args, path)
    except pricing.CostError as error:
        print(f"handover_telemetry: {error}", file=sys.stderr)
        return 2
    return _emit(args, report)


def _build_report(args, path: Path) -> str:
    hook_log = _hook_log(args.repo, path.stem)
    session = transcript.parse_session(path)
    logparse.apply_hook_durations(session.primary.tool_calls, hook_log)
    prices = pricing.load_prices(args.prices)
    got = metrics.compute(
        session,
        price_table=prices,
        repo_root=args.repo,
        hook_log=hook_log,
    )
    host = machine.collect(repo=args.repo)
    scrubber = redact.default_redactor()
    if args.json:
        return render.render_json(got, host, scrubber)
    return render.render_markdown(got, host, scrubber)


def _hook_log(repo: Path, session_id: str) -> Path | None:
    path = repo / ".cc_logging" / f"{session_id}.jsonl"
    return path if path.is_file() else None  # pragma: no mutate: missing log reads none


def _emit(args, report: str) -> int:
    if args.create:
        return _create_issue(args, report)
    if args.out is not None:
        args.out.write_text(report, encoding="utf-8")  # pragma: no mutate: utf-8 locale
        print(f"wrote {args.out}")
        return 0
    sys.stdout.write(report)
    return 0


def _create_issue(args, report: str) -> int:
    title = f"Handover telemetry: {args.repo.name}"
    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(report)
        body_path = handle.name
    try:
        out = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body-file",
                body_path,
                "--label",
                "handover",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"handover_telemetry: gh failed: {error}", file=sys.stderr)
        return 2
    if out.returncode != 0:
        print(f"handover_telemetry: gh failed: {out.stderr.strip()}", file=sys.stderr)
        return 2
    sys.stdout.write(out.stdout)
    return 0


def _run_sessions(args) -> int:
    project_dir = _resolve_project_dir(args)
    if not project_dir.is_dir():
        print(
            f"handover_telemetry: no project directory at {project_dir}",
            file=sys.stderr,
        )
        return 2
    for path in sorted(project_dir.glob("*.jsonl")):
        record = transcript.parse_session(path)
        models = ", ".join(record_model_names(record))
        first = record.first_ts or "unknown"
        last = record.last_ts or "unknown"
        print(f"{path.name}  {first} -> {last}  models: {models or 'none'}")
    return 0



def record_model_names(record: transcript.Session) -> list[str]:
    runs = [record.primary, *record.sidechains]
    names = {turn.model for run in runs for turn in run.turns if turn.model}
    return sorted(names)
