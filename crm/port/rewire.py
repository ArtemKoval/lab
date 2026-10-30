"""Re-apply the house wiring after a port pass.

A fresh port brings the upstream wiring back: data folder reads, instruction
file reads, the award module import, renamed framework names, and engine
message grammar. This tool applies the house wiring to a freshly ported
tree, so each pass ends the same way. Run it from the crm directory after
every port pass, then run the suites.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# Files a milestone may delete upstream; remove them when present.
DELETED_FILES = [
    "agent/main.py",
    "agent/tests/test_agent.py",
    "agent/tests/test_queue.py",
    "agent/tests/test_queue_agent.py",
    "backend/instructions.md",
    "backend/instructions/queue.md",
    "backend/instructions/claim.md",
    "dashboard/src/testing.ts",
    "dashboard/src/RunPanel.tsx",
    "dashboard/src/RunPanel.test.tsx",
    "backend/tests/conftest.py",
]

# Whole-file replacements: path -> list of (old, new). The first match wins.
REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "backend/main.py": [
        (
            'INSTRUCTIONS = Path(__file__).parent / "instructions"\n',
            "",
        ),
        (
            'INSTRUCTIONS = Path(__file__).resolve().parent / "instructions"\n',
            "",
        ),
        (
            '    queue = (INSTRUCTIONS / "queue.md").read_text(encoding="utf-8")\n'
            '    case = (INSTRUCTIONS / "case.md").read_text(encoding="utf-8")',
            '    queue = loader.pack().instruction("queue")\n'
            '    case = loader.pack().instruction("case")',
        ),
        (
            "from backend.award import needs_sign_off, work_out_award\n",
            "",
        ),
        (
            "from backend.award import needs_sign_off\n",
            "",
        ),
        (
            "def approval_limit(",
            "def rules():\n"
            '    """Return the active pack\'s deterministic rules module."""\n'
            "    return loader.pack().rules_module()\n"
            "\n\n"
            "def approval_limit(",
        ),
        (
            "elif needs_sign_off(award, approval_limit(db)):",
            "elif rules().needs_sign_off(award, approval_limit(db)):",
        ),
        (
            "return work_out_award(contract, plans(db), request, approval_limit(db))",
            "return rules().work_out_award(\n"
            "        contract, plans(db), request, approval_limit(db)\n"
            "    )",
        ),
        ("A award over", "An award over"),
        (
            "elif needs_sign_off(award, limit):",
            "elif rules().needs_sign_off(award, limit):",
        ),
        (
            "from backend.database import",
            "from domains import loader\nfrom backend.database import",
        ),
    ],
    "backend/database.py": [
        (
            'HELD_OUT_CASES = "evals/held_out_cases.json"',
            'HELD_OUT_CASES = "held_out_cases.json"',
        ),
        (
            'LabeledSet(cases, "evals/decisions.json")',
            'LabeledSet(cases, "decisions.json")',
        ),
        (
            'held_out_cases, "evals/held_out_decisions.json"',
            'held_out_cases, "held_out_decisions.json"',
        ),
        (
            "held_out = load(HELD_OUT_CASES)",
            "held_out = loader.pack().load_eval(HELD_OUT_CASES)",
        ),
        (
            "for d in load(labeled.decisions)",
            "for d in loader.pack().load_eval(labeled.decisions)",
        ),
        (
            "and the file in data/evals/ with the workers' decisions",
            "and the eval file with the workers' decisions",
        ),
        (
            'INSTRUCTIONS = Path(__file__).resolve().parent / "instructions"\n',
            "",
        ),
        (
            '    "recipe": (INSTRUCTIONS / "recipe.md").read_text(encoding="utf-8"),',
            '    "recipe": loader.pack().instruction("recipe"),',
        ),
        (
            "            instructions=(INSTRUCTIONS / \"case.md\").read_text(encoding=\"utf-8\"),",
            '            instructions=loader.pack().instruction("case"),',
        ),
        (
            'DATA = ROOT / "data"\n',
            "",
        ),
        (
            'def load(name: str) -> Any:\n'
            '    """Read one of the JSON files in data/."""\n'
            '    return json.loads((DATA / name).read_text(encoding="utf-8"))',
            'def load(name: str) -> Any:\n'
            '    """Read one of the JSON files in the pack data folder."""\n'
            "    return loader.pack().load_json(name)",
        ),
        (
            '    """Build the tables afresh from data/ and count what they hold."""\n'
            '    company = load("company.json")',
            '    """Build the tables afresh from the pack and count what they hold."""\n'
            "    active = loader.pack()\n"
            '    company = active.load_json("company.json")',
        ),
        ('"text": (DATA / f"{name}.md").read_text(encoding="utf-8"),',
         '"text": active.read_doc(name),'),
        ('"award_approval_limit": company["award_approval_limit"],',
         '"award_approval_limit": active.settings["award_approval_limit"],'),
        (
            "from sqlalchemy import (",
            "from domains import loader\n\nfrom sqlalchemy import (",
        ),
    ],
    "agent/api.py": [
        (
            'BACKEND_URL = os.getenv("CRM_AGENT_API", "http://127.0.0.1:8000")',
            'BACKEND_URL = os.getenv("CRM_API", "http://127.0.0.1:8000")',
        ),
    ],
    "backend/improvement.py": [
        (
            "    INSTRUCTIONS,\n",
            "",
        ),
        (
            '    improver = (INSTRUCTIONS / "improver.md").read_text(encoding="utf-8")',
            '    improver = loader.pack().instruction("improver")',
        ),
    ],
    "conftest.py": [
        (
            "from backend.tests.sign_in import PUBLIC_KEYS, SUPABASE_URL",
            "from backend.tests.sign_in import AUTH_URL, PUBLIC_KEYS",
        ),
        (
            'monkeypatch.setenv("VITE_SUPABASE_URL", SUPABASE_URL)',
            'monkeypatch.setenv("AUTH_URL", AUTH_URL)',
        ),
    ],
    "backend/tests/test_database.py": [
        ('SUPABASE = "postgresql', 'POSTGRES_URL = "postgresql'),
        ('setenv("DATABASE_URL", SUPABASE)', 'setenv("DATABASE_URL", POSTGRES_URL)'),
        ('setenv("DATABASE_URL", f"{SUPABASE}?sslmode', 'setenv("DATABASE_URL", f"{POSTGRES_URL}?sslmode'),
    ],
    "backend/agent_service.py": [
        (
            'AGENT_URL = os.getenv("CRM_AGENT_API", "http://127.0.0.1:8002")',
            'AGENT_URL = os.getenv("CRM_AGENT_SERVICE", "http://127.0.0.1:8002")',
        ),
    ],
    "agent/service.py": [
        ("@app.exception_worker(", "@app.exception_handler("),
    ],
    "dashboard/src/components/DecisionPanel.tsx": [
        ("${String(case.attempts)}", "${String(entry.attempts)}"),
    ],
    "dashboard/vite.config.ts": [
        ("process.env.CRM_AGENT_API", "process.env.CRM_API"),
    ],
    "playwright.config.ts": [
        ("CRM_AGENT_API: AGENT_STAND_IN", "CRM_AGENT_SERVICE: AGENT_STAND_IN"),
        ('env: { CRM_AGENT_API: "http://127.0.0.1:8001" }',
         'env: { CRM_API: "http://127.0.0.1:8001" }'),
    ],
    "dashboard/src/format.ts": [
        ("} entry ${agents === 1", "} case ${agents === 1"),
    ],
    "dashboard/src/pages/InstructionsPage.tsx": [
        ("What each entry agent reads before it starts on a entry",
         "What each case agent reads before it starts on a case"),
        (">Working a entry<", ">Working a case<"),
    ],
    "dashboard/src/App.test.tsx": [
        ("/# Working a entry/", "/# Working a case/"),
    ],
    "dashboard/src/DispatchPanel.test.tsx": [
        ("/with 3 entry agents at once/", "/with 3 case agents at once/"),
    ],
    "dashboard/src/Scoreboard.test.tsx": [
        ("/Oct 3, .*, 25 entry agents at once/", "/Oct 3, .*, 25 case agents at once/"),
    ],
    "e2e/run.spec.ts": [
        ("/with 2 entry agents at once/", "/with 2 case agents at once/"),
    ],
    "agent/dispatcher.py": [
        ("from langgraph.types import RetryContract, Send",
         "from langgraph.types import RetryPolicy, Send"),
        ("RetryContract(", "RetryPolicy("),
        ("retry_contract=RETRY", "retry_policy=RETRY"),
    ],
    "agent/tests/test_dispatcher.py": [
        (".retry_contract", ".retry_policy"),
        ("dispatcher.RETRY", "dispatcher.RETRY"),
        ("error_worker=", "error_handler="),
        ("a node's error_worker", "a node's error_handler"),
    ],
    "agent/tests/test_costs.py": [],
    "agent/harness.py": [
        ("from langgraph.types import Command, RetryContract",
         "from langgraph.types import Command, RetryPolicy"),
        ("RetryContract(", "RetryPolicy("),
        ("retry_contract=RETRY", "retry_policy=RETRY"),
        ("retry_contract=SCREEN_RETRY", "retry_policy=SCREEN_RETRY"),
        ("from langfuse.langchain import CallbackWorker",
         "from langfuse.langchain import CallbackHandler"),
        ('"callbacks": [CallbackWorker()],', '"callbacks": [CallbackHandler()],'),
    ],
    "agent/tests/conftest.py": [
        ("from langchain_core.callbacks import BaseCallbackWorker",
         "from langchain_core.callbacks import BaseCallbackHandler"),
        ("class RecordRoots(BaseCallbackWorker):",
         "class RecordRoots(BaseCallbackHandler):"),
        (
            '    def on_chain_start(self, serialized, inputs, *, parent_run_id=None, **kwargs):',
            "    def on_chain_start(\n"
            "        self, serialized, inputs, *, run_id=None, parent_run_id=None, **kwargs\n"
            "    ):",
        ),
        ('monkeypatch.setattr(harness, "CallbackWorker", lambda: RecordRoots(roots))',
         'monkeypatch.setattr(harness, "CallbackHandler", lambda: RecordRoots(roots))'),
    ],
    "backend/tests/test_documents.py": [
        ('"Repeat cases"', '"Repeat claims"'),
        ("section 9: Repeat cases", "section 9: Repeat claims"),
        ('search(client, "repeat cases")', 'search(client, "repeat claims")'),
        ("# CRM Agent: running the queue", "# UnderCover Agent: running the queue"),
        ("# CRM Agent: working a case", "# UnderCover Agent: working a claim"),
        ("# CRM Cases Handling Manual", "# UnderCover Claims Handling Manual"),
        (
            "Before deciding any case, check the customer's case history",
            "Before deciding any claim, check the customer's claim history",
        ),
    ],
    "agent/tests/test_case_agent.py": [
        ("section 9: Repeat cases", "section 9: Repeat claims"),
        ("status 403: A award", "status 403: An award"),
    ],
    "backend/tests/test_workflow.py": [
        ('"A award over', '"An award over'),
    ],
    "dashboard/src/CaseWork.test.tsx": [
        ("shows a decline without a award", "shows a decline without an award"),
    ],
    "e2e/agent.spec.ts": [
        ("a worker signs off a award over", "a worker signs off an award over"),
    ],
    "e2e/pages.spec.ts": [
        ("/you run the cases queue/", "/you run the claims queue/"),
        ("/9\\. Repeat cases/", "/9\\. Repeat claims/"),
    ],
}


def rewire(root: Path) -> None:
    for name in DELETED_FILES:
        path = root / name
        if path.exists():
            path.unlink()
            print(f"deleted {name}")
    for name, pairs in REPLACEMENTS.items():
        path = root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in pairs:
            if new and new in text and old in text:
                continue  # already applied; the pair is idempotent
            if old in text:
                text = text.replace(old, new)
            else:
                print(f"note: pattern absent in {name}: {old[:60]!r}")
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"rewired {name}")


# Lines of TypeScript that keep the upstream `case` word untouched.
TS_SKIP = re.compile(r"^\s*//")

# Segments kept verbatim: regex literals and quoted strings on one line.
TS_VERBATIM = re.compile(
    r'/(?:[^/\\\n]*\\[^/\n]+)[^/\n]*/'  # a regex with an escape inside
    r"|/\^[^/\n]*/"  # a regex anchored at the start
    r'|"(?:[^"\\\n]|\\.)*"'
    r"|'(?:[^'\\\n]|\\.)*'"
)

# A declaration of the reserved word: `const case: Case = ...`.
TS_DECL = re.compile(r"\b(const|let|var)(\s+)case\b")

# A spread of the variable: ...case.
TS_SPREAD = re.compile(r"\.\.\.case\b")

# A parameter or spread use: function progress(case: Case), ...case.
TS_PARAM = re.compile(r"([{(:,]\s*)\bcase\b(?=\s*[:),}])")

# A use of the variable: not a property read, not an object key or field.
TS_VARIABLE = re.compile(r"(?<!\.)\bcase\b(?!\s*:)")


def ts_rename(root: Path) -> None:
    """Rename the reserved word `case` to `entry` in the TypeScript sources."""
    for folder in ("dashboard/src", "e2e"):
        for path in sorted((root / folder).rglob("*")):
            if path.suffix not in (".ts", ".tsx"):
                continue
            out = []
            changed = False
            for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
                if TS_SKIP.search(line):
                    out.append(line)
                    continue
                stashed: list[str] = []

                def stash(match: re.Match[str]) -> str:
                    stashed.append(match.group(0))
                    return f"\x00{len(stashed) - 1}\x00"

                masked = TS_VERBATIM.sub(stash, line)
                masked = TS_SPREAD.sub("...entry", masked)
                masked = TS_DECL.sub(r"\1\2entry", masked)
                masked = TS_PARAM.sub(r"\1entry", masked)
                masked = TS_VARIABLE.sub("entry", masked)
                for index, segment in enumerate(stashed):
                    restored = segment
                    if restored.startswith("`"):
                        restored = TS_VARIABLE.sub("entry", restored)
                    masked = masked.replace(f"\x00{index}\x00", restored)
                if masked != line:
                    changed = True
                out.append(masked)
            if changed:
                path.write_text("".join(out), encoding="utf-8")
                print(f"renamed case in {path.relative_to(root)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
        help="The crm project directory")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(f"crm root not found: {args.root}")
        return 2
    rewire(args.root)
    ts_rename(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
