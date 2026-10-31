"""The pack validator: one named examination per pack-contract rule.

Run from the crm directory: uv run -m crm_validate <pack-name>, or
uv run -m crm_validate --all to examine every pack. Exit 0 means the pack is
onboardable; exit 2 means at least one examination failed, and every finding
names its file. The validator never imports the engine's FastAPI app. It
imports the loader and the pack's rules module only.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from domains import loader  # noqa: E402
from domains.loader import DOMAINS, PackError  # noqa: E402

# The manifest keys the engine reads, and the settings key the gates compare.
REQUIRED_MANIFEST_KEYS = (
    "name",
    "display_name",
    "engine_api",
    "rules",
    "protocol",
    "settings",
    "documents",
    "seed",
    "resolutions",
    "outcomes",
    "config",
    "effects",
)
REQUIRED_SETTINGS_KEYS = ("award_approval_limit",)
REQUIRED_SEED_FILES = ("cases", "customers", "contracts", "workers", "company")

# The rules contract: the exact parameter names, in order.
RULES_CONTRACT = {
    "work_out_award": ["contract", "plans", "request", "approval_limit"],
    "needs_sign_off": ["award", "approval_limit"],
}

# The protocol contract: the four verbs and the metric accessor, with the
# exact parameter names, in order.
PROTOCOL_CONTRACT = {
    "resolve": ["case", "config", "request"],
    "gate": ["outcome", "config"],
    "execute": ["case", "outcome"],
    "summarize": ["outcome"],
    "metric": ["payload"],
}

# The tools the engine serves to the case agent; instructions may only name these.
SERVED_TOOLS = (
    "get_case",
    "get_contract",
    "get_case_history",
    "search_documents",
    "read_section",
    "calculate_award",
    "record_decision",
    "run_effect",
    "list_cases",
    "write_todos",
    "work_case",
)

# Tool-like words in the instructions that the engine does not serve. Any hit
# means the pack's instructions were written against another engine.
UPSTREAM_TOOL_PATTERN = re.compile(r"\b(work_claim|list_claims|pay_claim|pay_payout)\b")

# Engine-facing folders: file NAMES in them carry no domain noun.
PACK_CONTENT_FOLDERS = ("data", "policy", "instructions", "evals")

# Domain nouns a pack file name must not carry. The pack's CONTENT keeps its
# own words; only file names are engine-facing.
NOUN_FILE_PATTERN = re.compile(r"claim|payout|handler", re.IGNORECASE)

LEGAL_DECISIONS = {"approve", "decline", "refer"}
FRONT_MATTER = "---\n"


class Finding:
    """One failed examination, named by file."""

    def __init__(self, file: str, message: str) -> None:
        self.file = file
        self.message = message

    def __str__(self) -> str:
        return f"{self.file}: {self.message}"


class Examiner:
    """The examinations of one pack, with the findings they raise."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.root = DOMAINS / name
        self.findings: list[Finding] = []
        self.manifest: dict = {}

    def examine(self) -> list[Finding]:
        """Run every examination in order."""
        self.examine_manifest()
        if self.manifest:
            self.examine_rules()
            self.examine_protocol()
            self.examine_documents()
            self.examine_seeds()
            self.examine_evals()
            self.examine_instructions()
        self.examine_file_names()
        return self.findings

    def examine_manifest(self) -> None:
        path = self.root / "manifest.json"
        if not path.is_file():
            self.findings.append(Finding(f"manifest.json", "the pack has no manifest"))
            return
        try:
            self.manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            self.findings.append(
                Finding("manifest.json", f"the manifest is not JSON: {error}")
            )
            return
        for key in REQUIRED_MANIFEST_KEYS:
            if key not in self.manifest:
                self.findings.append(
                    Finding("manifest.json", f"the manifest lacks the key '{key}'")
                )
        if self.manifest.get("name") != self.name:
            self.findings.append(
                Finding(
                    "manifest.json",
                    f"the manifest name {self.manifest.get('name')!r} does not match the folder {self.name!r}",
                )
            )
        settings = self.manifest.get("settings", {})
        for key in REQUIRED_SETTINGS_KEYS:
            if key not in settings:
                self.findings.append(
                    Finding("manifest.json", f"the settings lack the key '{key}'")
                )
        for key in self.manifest.get("config", {}):
            if key not in settings:
                self.findings.append(
                    Finding(
                        "manifest.json",
                        f"the config declares the missing setting '{key}'",
                    )
                )

    def examine_rules(self) -> None:
        self.examine_module("rules.py", RULES_CONTRACT, "rules module")

    def examine_protocol(self) -> None:
        self.examine_module("protocol.py", PROTOCOL_CONTRACT, "protocol module")

    def examine_module(
        self, file: str, contract: dict[str, list[str]], kind: str
    ) -> None:
        """Load one pack module by file, and examine its functions against a
        contract of exact parameter names."""
        path = self.root / file
        if not path.is_file():
            self.findings.append(Finding(file, f"the pack has no {kind}"))
            return
        sys.path.insert(0, str(self.root))
        try:
            spec = importlib.util.spec_from_file_location(
                f"{self.name}_{path.stem}", path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as error:  # the module is the pack's own code
            self.findings.append(
                Finding(file, f"the {kind} does not import: {error}")
            )
            return
        for function_name, parameters in contract.items():
            function = getattr(module, function_name, None)
            if function is None:
                self.findings.append(
                    Finding(file, f"the {kind} lacks the function '{function_name}'")
                )
                continue
            actual = list(inspect.signature(function).parameters)
            if actual != parameters:
                self.findings.append(
                    Finding(
                        file,
                        f"{function_name} takes {actual}, but the contract is {parameters}",
                    )
                )

    def examine_documents(self) -> None:
        for name in self.manifest.get("documents", []):
            path = self.root / "policy" / f"{name}.md"
            if not path.is_file():
                self.findings.append(
                    Finding(f"policy/{name}.md", "the document is absent")
                )
                continue
            text = path.read_text(encoding="utf-8")
            if not text.startswith(FRONT_MATTER):
                self.findings.append(
                    Finding(f"policy/{name}.md", "the document carries no front matter")
                )
                continue
            front = text.split(FRONT_MATTER, 2)[1]
            if "version:" not in front:
                self.findings.append(
                    Finding(f"policy/{name}.md", "the front matter lacks a version")
                )
            for key in ("system", "owner", "reviewed"):
                if key not in front:
                    self.findings.append(
                        Finding(
                            f"policy/{name}.md",
                            f"the front matter's source lacks '{key}'",
                        )
                    )

    def examine_seeds(self) -> None:
        data = self.root / "data"
        try:
            cases = json.loads((data / "cases.json").read_text(encoding="utf-8"))
            customers = {
                c["customer_id"]
                for c in json.loads(
                    (data / "customers.json").read_text(encoding="utf-8")
                )
            }
            contracts = {
                c["contract_id"]
                for c in json.loads(
                    (data / "contracts.json").read_text(encoding="utf-8")
                )
            }
            workers = {
                w["worker_id"]
                for w in json.loads((data / "workers.json").read_text(encoding="utf-8"))
            }
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as error:
            self.findings.append(
                Finding("data/", f"the seed files do not read: {error}")
            )
            return
        for worker in json.loads((data / "workers.json").read_text(encoding="utf-8")):
            if not worker.get("email"):
                self.findings.append(
                    Finding(
                        "data/workers.json", f"{worker['worker_id']} carries no email"
                    )
                )
            if "can_approve_over_limit" not in worker:
                self.findings.append(
                    Finding(
                        "data/workers.json",
                        f"{worker['worker_id']} carries no can_approve_over_limit",
                    )
                )
        for case in cases:
            if case["customer_id"] not in customers:
                self.findings.append(
                    Finding(
                        "data/cases.json",
                        f"{case['case_id']} refers to the missing customer {case['customer_id']}",
                    )
                )
            if case["contract_id"] not in contracts:
                self.findings.append(
                    Finding(
                        "data/cases.json",
                        f"{case['case_id']} refers to the missing contract {case['contract_id']}",
                    )
                )
        for contract in json.loads(
            (data / "contracts.json").read_text(encoding="utf-8")
        ):
            if contract["customer_id"] not in customers:
                self.findings.append(
                    Finding(
                        "data/contracts.json",
                        f"{contract['contract_id']} refers to the missing customer {contract['customer_id']}",
                    )
                )
        worker_count = len(workers)
        senior = sum(
            1
            for w in json.loads((data / "workers.json").read_text(encoding="utf-8"))
            if w.get("can_approve_over_limit")
        )
        if senior == 0 and worker_count > 0:
            self.findings.append(
                Finding("data/workers.json", "no worker can approve over the limit")
            )

    def examine_evals(self) -> None:
        evals = self.root / "evals"
        decisions_path = evals / "decisions.json"
        if not decisions_path.is_file():
            self.findings.append(
                Finding("evals/decisions.json", "the eval decisions are absent")
            )
            return
        try:
            decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            self.findings.append(
                Finding(
                    "evals/decisions.json", f"the eval decisions do not read: {error}"
                )
            )
            return
        case_ids = {
            c["case_id"]
            for c in json.loads(
                (self.root / "data" / "cases.json").read_text(encoding="utf-8")
            )
        }
        for decision in decisions:
            if decision["case_id"] not in case_ids:
                self.findings.append(
                    Finding(
                        "evals/decisions.json",
                        f"{decision['case_id']} is not a case in the pack's queue",
                    )
                )
            if decision.get("decision") not in LEGAL_DECISIONS:
                self.findings.append(
                    Finding(
                        "evals/decisions.json",
                        f"{decision['case_id']} carries the illegal decision {decision.get('decision')!r}",
                    )
                )

    def examine_instructions(self) -> None:
        folder = self.root / "instructions"
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            hit = UPSTREAM_TOOL_PATTERN.search(text)
            if hit:
                self.findings.append(
                    Finding(
                        f"instructions/{path.name}",
                        f"the instructions name the tool '{hit.group(0)}', which the engine does not serve",
                    )
                )

    def examine_file_names(self) -> None:
        for folder in PACK_CONTENT_FOLDERS:
            folder_path = self.root / folder
            if not folder_path.is_dir():
                continue
            for path in folder_path.rglob("*"):
                if NOUN_FILE_PATTERN.search(path.name):
                    self.findings.append(
                        Finding(
                            str(path.relative_to(self.root)),
                            f"the file name carries the domain noun in '{path.name}'",
                        )
                    )


def examine_all() -> tuple[list[str], list[Finding]]:
    """Examine every pack under domains/ and return (names, findings)."""
    names = sorted(
        entry.name
        for entry in DOMAINS.iterdir()
        if entry.is_dir() and (entry / "manifest.json").is_file()
    )
    findings: list[Finding] = []
    for name in names:
        findings.extend(Examiner(name).examine())
    return names, findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("pack", nargs="?", help="The pack name under crm/domains/")
    group.add_argument("--all", action="store_true", help="Examine every pack")
    args = parser.parse_args()

    if args.all:
        names, findings = examine_all()
        for name in names:
            print(f"examined {name}")
    elif args.pack:
        findings = Examiner(args.pack).examine()
        print(f"examined {args.pack}")
    else:
        parser.print_usage()
        return 2

    for finding in findings:
        print(f"FAIL {finding}")
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
