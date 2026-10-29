"""Port upstream UnderCover milestone trees into the crm project.

The tool reads blobs from a local clone of github.com/ed-donner/undercover,
maps engine paths to crm paths, applies the engine rename to engine files,
and copies pack content verbatim with schema-key renames only. The change
artifacts own the mapping decisions; this tool carries them out. See
crm/port/README.md for the per-change passes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Directories of the upstream tree the port never reads.
EXCLUDED_PREFIXES = (
    "labs/",
    "setup/",
    "community_contributions/",
    "assets/",
    "guides/",
    "docs/",
    "lefthook.yml",
)

# Upstream path prefix or file -> crm path. Longest prefix wins.
PATH_MAP = [
    ("data/evals/held_out_claims.json", "domains/insurance/evals/held_out_cases.json"),
    ("data/evals/held_out_decisions.json", "domains/insurance/evals/held_out_decisions.json"),
    ("data/evals/", "domains/insurance/evals/"),
    ("data/policy_wording_short.md", "domains/insurance/policy/wording_short.md"),
    ("data/policy_wording.md", "domains/insurance/policy/wording.md"),
    ("data/claims_manual.md", "domains/insurance/policy/manual.md"),
    ("data/claims.json", "domains/insurance/data/cases.json"),
    ("data/policies.json", "domains/insurance/data/contracts.json"),
    ("data/handlers.json", "domains/insurance/data/workers.json"),
    ("data/", "domains/insurance/data/"),
    ("backend/instructions.md", "domains/insurance/instructions/case.md"),
    ("backend/instructions/claim.md", "domains/insurance/instructions/case.md"),
    ("backend/instructions/queue.md", "domains/insurance/instructions/queue.md"),
    ("docs/SPEC.md", "docs/BRIEF.md"),
]

# Upstream environment variable names -> engine names, applied before the
# word renames so an exact variable name never half-matches.
ENV_MAP = [
    ("UNDERCOVER_DB", "CRM_DB"),
    ("UNDERCOVER_API_KEY", "CRM_AGENT_KEY"),
    ("UNDERCOVER_API", "CRM_AGENT_API"),
    ("UNDERCOVER_CONTEXT", "CRM_CONTEXT_URL"),
    ("UNDERCOVER_COPILOT", "CRM_COPILOT"),
    ("UNDERCOVER_GATEWAY_URL", "CRM_GATEWAY_URL"),
    ("UNDERCOVER_MEMORY_ID", "CRM_MEMORY_ID"),
    ("UNDERCOVER_AGENT_RUNTIME", "CRM_AGENT_RUNTIME"),
    ("UNDERCOVER_COPILOT_RUNTIME", "CRM_COPILOT_RUNTIME"),
    ("UNDERCOVER_AGENT", "CRM_AGENT_API"),
]

# Word-boundary renames for engine code. Order matters: the two-word
# document names go before the single words they contain.
WORD_MAP = [
    ("policy_wording", "wording"),
    ("claims_manual", "manual"),
    ("claims", "cases"),
    ("claim", "case"),
    ("payouts", "awards"),
    ("payout", "award"),
    ("handlers", "workers"),
    ("handler", "worker"),
    ("policies", "contracts"),
    ("policy", "contract"),
    ("UnderCover Travel Insurance", "CRM"),
    ("Undercover Travel Insurance", "CRM"),
    ("UnderCover", "CRM"),
    ("Undercover", "CRM"),
    ("undercover", "crm"),
]


def rename_words(text: str) -> str:
    for env_name, engine_name in ENV_MAP:
        text = text.replace(env_name, engine_name)
    for old, new in WORD_MAP:
        text = re.sub(rf"\b{old}\b", new, text)
        text = re.sub(rf"\b{old.upper()}\b", new.upper(), text)
        text = re.sub(rf"\b{old.capitalize()}\b", new.capitalize(), text)
        # CamelCase compounds: ClaimPage, PolicyPanels, getClaimPage.
        text = re.sub(rf"\b{old}(?=[A-Z])", new, text)
        text = re.sub(rf"\b{old.capitalize()}(?=[A-Z])", new.capitalize(), text)
        # Mid-compound capitalized word: PreviousClaim.
        text = re.sub(rf"(?<=[a-z]){old.capitalize()}\b", new.capitalize(), text)
        # Mid-compound on both sides: getClaimHistory, setHandlerId.
        text = re.sub(rf"(?<=[a-z]){old.capitalize()}(?=[A-Z])", new.capitalize(), text)
        # snake_case compounds: claim_id, previous_claims, get_claim_history.
        text = re.sub(rf"{old}_", f"{new}_", text)
        text = re.sub(rf"{old.upper()}_", f"{new.upper()}_", text)
        text = re.sub(rf"_{old}\b", f"_{new}", text)
        text = re.sub(rf"_{old}s\b", f"_{new}s", text)
    return text

# Files copied exactly as they are.
VERBATIM_NAMES = ("favicon.svg", ".gitignore", ".python-version", ".nvmrc", ".npmrc")


def git(upstream: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(upstream), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def changed_files(upstream: Path, base: str, ref: str) -> list[str]:
    """List files the ref adds or modifies against the base, minus exclusions."""
    lines = git(upstream, "diff", "--name-status", base, ref).splitlines()
    names = []
    for line in lines:
        parts = line.split("\t")
        name = parts[-1].strip()
        if name.startswith(EXCLUDED_PREFIXES):
            continue
        if parts[0].startswith(("A", "M", "R")):
            names.append(name)
    return sorted(set(names))


def map_path(name: str) -> str:
    for prefix, target in PATH_MAP:
        if name.startswith(prefix) or name == prefix:
            return target + name[len(prefix):]
    return name


def rename_json_keys(node: Any) -> Any:
    if isinstance(node, list):
        return [rename_json_keys(item) for item in node]
    if isinstance(node, dict):
        return {rename_words(key): rename_json_keys(value) for key, value in node.items()}
    return node


def is_pack(name: str) -> bool:
    return name.startswith("domains/")


def transform(upstream_name: str, mapped_name: str, text: str) -> str:
    if is_pack(mapped_name):
        if mapped_name.endswith(".json"):
            data = json.loads(text)
            return json.dumps(rename_json_keys(data), indent=2, ensure_ascii=False) + "\n"
        return text
    if Path(upstream_name).name in VERBATIM_NAMES:
        return text
    return rename_words(text)


def port_files(upstream: Path, ref: str, names: list[str], dest: Path, dry_run: bool) -> int:
    written = 0
    for name in names:
        probe = subprocess.run(
            ["git", "-C", str(upstream), "cat-file", "-e", f"{ref}:{name}"],
            capture_output=True,
        )
        if probe.returncode != 0:
            print(f"skip, absent at {ref}: {name}", file=sys.stderr)
            continue
        text = git(upstream, "show", f"{ref}:{name}")
        mapped = map_path(name)
        # Pack paths stay verbatim; engine paths get the rename.
        target = dest / (mapped if is_pack(mapped) else rename_words(mapped))
        target.parent.mkdir(parents=True, exist_ok=True)
        if dry_run:
            print(f"{name} -> {target}")
            continue
        target.write_text(transform(name, mapped, text), encoding="utf-8")
        written += 1
    return written


def tree_files(upstream: Path, ref: str, prefix: str) -> list[str]:
    """List every file under the prefix at the ref, minus exclusions."""
    out = git(upstream, "ls-tree", "-r", "--name-only", ref, "--", prefix)
    return [n for n in out.splitlines() if n and not n.startswith(EXCLUDED_PREFIXES)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_upstream = Path(os.environ.get("UPSTREAM_REPO", "/home/repos/undercover-upstream"))
    parser.add_argument("--upstream", type=Path, default=default_upstream,
        help="Path to the local undercover clone")
    parser.add_argument("--ref", required=True, help="Upstream ref to port from")
    parser.add_argument("--base", default=None, help="Diff base for the file list")
    parser.add_argument("--file", action="append", default=[],
        help="Port this upstream path; repeatable. Empty with --base diffs the base")
    parser.add_argument("--tree", action="append", default=[],
        help="Port every file under this prefix at the ref; repeatable")
    parser.add_argument("--dest", type=Path, default=Path(__file__).resolve().parents[1],
        help="The crm project directory")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.upstream.is_dir():
        print(f"upstream clone not found: {args.upstream}", file=sys.stderr)
        return 2
    names = list(args.file)
    for prefix in args.tree:
        names.extend(tree_files(args.upstream, args.ref, prefix))
    if not names and args.base:
        names = changed_files(args.upstream, args.base, args.ref)
    if not names:
        print("give --base, --file, or --tree", file=sys.stderr)
        return 2

    count = port_files(args.upstream, args.ref, names, args.dest, args.dry_run)
    print(f"ported {count} files from {args.ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
