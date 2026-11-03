"""Scenario extraction from OpenSpec change specs (Gate 0 enforcement
point). The parser walks every spec.md under a change, extracts the
requirement and scenario blocks, and refuses anything unparseable.

The scenario_id slug is the traceability key for the manifest, the
pytest IDs, the PR matrix, and the frozen suites. Renaming a scenario
is a spec migration, not a typo fix.
"""

import hashlib
import re
from pathlib import Path

SURFACES = ("dspy-eval", "e2e-ui", "e2e-visual", "agent-e2e")

SCENARIO_RE = re.compile(
    r"#### Scenario: (?P<title>[^\n]+?)(?P<tags>\[.*?\])?\s*\n(?P<body>.*?)(?=####|\Z)",
    re.S,
)
REQUIREMENT_RE = re.compile(
    r"### Requirement: (?P<name>[^\n]+)\n(?P<body>.*?)(?=### Requirement:|\Z)",
    re.S,
)
WHEN_RE = re.compile(r"\*\*WHEN\*\* (?P<when>.+)")
THEN_RE = re.compile(r"\*\*(?:THEN|AND)\*\* (?P<then>.+)")
JUDGE_RE = re.compile(r"\[judge\s*:\s*rubric\s*=\s*(?P<rubric>[^\]]+)\]", re.I)


class ScenarioParseError(ValueError):
    """A spec block the compiler cannot consume. This is Gate 0's final
    enforcement point: the bridge refuses to proceed."""


def slug(title):
    """Lowercase kebab slug, capped at 60 chars. Forever names."""
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60]


def parse_tags(tag_text):
    """Split a heading tag bracket into surface, judged, and rubric.

    The surface holds the runner names; the judge marker may sit in the
    tag list or inline in a THEN clause.
    """
    surface = None
    judged = False
    rubric = None
    for part in tag_text.strip("[]").split(","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("surface:"):
            surface = part.split(":", 1)[1].strip()
        elif part.startswith("judge"):
            judged = True
    return surface, judged, rubric


def parse_inline_judge(body):
    """Return the rubric named by an inline [judge: rubric = ...] tag."""
    m = JUDGE_RE.search(body)
    return m.group("rubric").strip() if m else None


def parse_scenario(match, capability):
    """Turn one heading match into a scenario dict, or raise."""
    title = match.group("title").strip()
    raw_tags = match.group("tags") or ""
    surface, judged, rubric = parse_tags(raw_tags)
    body = match.group("body")
    when = WHEN_RE.search(body)
    thens = [t.group("then").strip() for t in THEN_RE.finditer(body)]
    if not when or not thens:
        raise ScenarioParseError(
            f"Unparseable scenario in {capability}: {title!r}"
        )
    inline_rubric = parse_inline_judge(body)
    if inline_rubric:
        judged = True
        rubric = inline_rubric
    return {
        "scenario_id": slug(title),
        "title": title,
        "capability": capability,
        "when": when.group("when").strip(),
        "thens": thens,
        "surface": surface,
        "judged": judged,
        "rubric": rubric,
        "source_hash": hashlib.sha1(match.group(0).encode()).hexdigest()[:10],
    }


def parse_change(change_dir):
    """Parse one openspec/changes/<id>/ directory into bridge JSON.

    Requirements keep their names and carry their scenarios in spec
    order; specs are walked in sorted order for stable output.
    """
    change_dir = Path(change_dir)
    requirements = []
    for spec in sorted(change_dir.joinpath("specs").rglob("spec.md")):
        capability = spec.parent.name
        text = spec.read_text(encoding="utf-8")
        for req in REQUIREMENT_RE.finditer(text):
            scenarios = [
                parse_scenario(m, capability)
                for m in SCENARIO_RE.finditer(req.group("body"))
            ]
            requirements.append(
                {"name": req.group("name").strip(), "scenarios": scenarios}
            )
    if not any(r["scenarios"] for r in requirements):
        raise ScenarioParseError(
            f"No scenarios found in {change_dir.name}"
        )
    return {"change_id": change_dir.name, "requirements": requirements}
