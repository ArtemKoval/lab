"""Inventory the prohibitive instructions in the agentic harness text.

The tool answers one question: which harness sentences tell the agent
what not to do, and which of them the guard tests pin? The scan is
read-only and runs without a network. Each interpretation has one
owner: the tool owns the sentence detection and the pin
classification, and the operator owns the contract judgment on the
unpinned candidates.

Usage:
    PYTHONPATH=tools/negative_instruction_audit python -m \
        negative_instruction_audit [--json] [--repo-root PATH]

Exit 0 on success and 2 on operational failure. The failure message
names one next action.
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

NEGATIVE_RE = re.compile(
    r"\b(never|do not|don't|must not|shall not|cannot|avoid)\b|^(no|never)\b",
    re.IGNORECASE | re.MULTILINE,
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
MIN_PIN_LEN = 20


def iter_harness_files(root):
    """Return the harness text files to scan, in a stable order."""
    files = [root / "CLAUDE.md"]
    files.extend(sorted((root / ".claude" / "skills").glob("*/SKILL.md")))
    files.extend(sorted((root / ".claude" / "agents").glob("*.md")))
    charter = root / ".claude" / "hooks" / "harness-charter.sh"
    if charter.exists():
        files.append(charter)
    return [path for path in files if path.exists()]


def extract_sentences(text):
    """Split the prose into sentence candidates.

    Code fences go first: commands are not instructions to the agent.
    Wrapped lines join with spaces, and markdown bullets split into
    their own candidates.
    """
    text = FENCE_RE.sub(" ", text)
    units = []
    for raw_line in text.splitlines():
        line = BULLET_RE.sub("", raw_line).strip()
        if not line:
            continue
        units.append(line)
    sentences = []
    for sentence in SENTENCE_RE.split(" ".join(units)):
        cleaned = sentence.strip()
        if len(cleaned) >= 12:
            sentences.append(cleaned)
    return sentences


def load_pin_literals(tests_dir):
    """Return the string literals the test tree asserts on."""
    literals = []
    for test_file in sorted(tests_dir.rglob("*.py")):
        try:
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if len(node.value) >= MIN_PIN_LEN:
                    literals.append(re.sub(r"\s+", " ", node.value))
    return literals


def is_pinned(sentence, pins):
    """Return True when a guard literal covers the sentence."""
    collapsed = re.sub(r"\s+", " ", sentence)
    for pin in pins:
        if pin in collapsed or collapsed in pin:
            return True
    return False


def is_negative(sentence):
    """Return True when the sentence carries a prohibitive marker."""
    return bool(NEGATIVE_RE.search(sentence))


def scan_file(path, pins):
    """Return the scan record for one harness file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    sentences = extract_sentences(text)
    findings = []
    for sentence in sentences:
        if is_negative(sentence):
            findings.append(
                {
                    "sentence": sentence,
                    "pinned": is_pinned(sentence, pins),
                }
            )
    return {
        "path": str(path),
        "sentences": len(sentences),
        "negative": len(findings),
        "pinned": sum(1 for item in findings if item["pinned"]),
        "candidates": [item for item in findings if not item["pinned"]],
        "findings": findings,
    }


def run(root):
    """Return the full scan payload for the harness tree."""
    pins = load_pin_literals(root / "tests")
    records = [scan_file(path, pins) for path in iter_harness_files(root)]
    totals = {
        "files": len(records),
        "sentences": sum(record["sentences"] for record in records),
        "negative": sum(record["negative"] for record in records),
        "pinned": sum(record["pinned"] for record in records),
        "candidates": sum(record["negative"] - record["pinned"] for record in records),
    }
    return {"root": str(root), "totals": totals, "files": records}


def main(argv=None):
    """Run the CLI. Exit 0 on success and 2 on operational failure."""
    parser = argparse.ArgumentParser(
        prog="negative_instruction_audit",
        description="Inventory the prohibitive instructions in the harness text.",
    )
    parser.add_argument("--json", action="store_true", help="machine output")
    parser.add_argument("--repo-root", default=".", help="repository root")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    if not (root / "tests").is_dir():
        print(
            "negative_instruction_audit: no tests/ under "
            f"{root}. Run from the repository root or pass --repo-root.",
            file=sys.stderr,
        )
        return 2
    payload = run(root)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            "{files} files, {sentences} sentences, {negative} negative, "
            "{pinned} pinned, {candidates} candidates".format(**payload["totals"])
        )
        for record in payload["files"]:
            if not record["negative"]:
                continue
            print(f"\n{record['path']}")
            for item in record["findings"]:
                mark = "pinned " if item["pinned"] else "cand   "
                print(f"  [{mark}] {item['sentence'][:110]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
