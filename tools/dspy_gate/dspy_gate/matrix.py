"""The PR conformance matrix: the suite report as a stable table."""

import json


def render(report):
    """Render one report as the markdown matrix for the pull request."""
    lines = ["| scenario | status | tier | route |", "|---|---|---|---|"]
    for row in report.rows:
        if not row["green"]:
            status = "red"
        elif row["deferred"]:
            status = "deferred"
        else:
            status = "green"
        tier = ",".join(sorted(row["tiers"])) or "-"
        lines.append(
            f"| {row['scenario_id']} | {status} | {tier} | {row['route'] or '-'} |"
        )
    return "\n".join(lines)


def to_json(report):
    """Render one report as a stable JSON string."""
    return json.dumps(
        {"exit": report.exit, "rows": report.rows}, indent=2, sort_keys=True
    )
