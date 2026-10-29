"""The renderers for the telemetry block: markdown for the issue and
JSON with OpenTelemetry GenAI field names. Every string passes the
redactor before it lands in an output. Missing data renders as n/a,
and an unknown price renders as unknown."""

import json

from .metrics import TaskMetrics

_NA = "n/a"


def _ms(value: float | None) -> str:
    return f"{value:.0f}" if value is not None else _NA


def _money(value: float | None) -> str:
    return f"${value:.4f}" if value is not None else "unknown"


def _clean(value: object, scrubber) -> object:
    if isinstance(value, str):
        return scrubber.scrub(value)
    if isinstance(value, dict):
        return {
            scrubber.scrub(key): _clean(item, scrubber) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_clean(item, scrubber) for item in value]
    return value


def render_markdown(metrics: TaskMetrics, host: dict, scrubber) -> str:
    lines = ["## Telemetry", ""]
    lines += _run_section(metrics, host, scrubber)
    lines += _funnel_section(metrics, scrubber)
    lines += _models_section(metrics, scrubber)
    lines += _cost_section(metrics, scrubber)
    lines += _pipeline_section(metrics)
    lines += _decisions_section(metrics, scrubber)
    lines += _friction_section(metrics, scrubber)
    lines += _machine_section(host, scrubber)
    lines += _redaction_section(scrubber)
    return "\n".join(lines).rstrip() + "\n"


def _run_section(metrics: TaskMetrics, host: dict, scrubber) -> list[str]:
    fp = _clean(metrics.fingerprint, scrubber)
    agent_version = fp.get("version") or _NA
    return [
        "### Run",
        f"- session: {fp.get('session_id') or _NA}",
        f"- agent version: {agent_version}",
        f"- entrypoint: {fp.get('entrypoint') or _NA}",
        f"- branch: {fp.get('git_branch') or _NA}",
        f"- host: {host.get('kernel') or _NA} {host.get('arch') or _NA}",
        "",
    ]


def _funnel_section(metrics: TaskMetrics, scrubber) -> list[str]:
    header = "| # | Agent | Tool | Start | ms | Exit |"
    rule = "|---|---|---|---|---|---|"
    lines = ["### Funnel", "", header, rule]
    for index, call in enumerate(metrics.funnel, start=1):
        agent = scrubber.scrub(str(call["agent"]))
        tool = scrubber.scrub(str(call["tool"]))
        start = scrubber.scrub(str(call["start"] or _NA))
        exit_code = _NA if call["exit_code"] is None else str(call["exit_code"])
        duration = _ms(call["duration_ms"])
        row = f"| {index} | {agent} | {tool} | {start}"
        row += f" | {duration} | {exit_code} |"
        lines.append(row)
    if not metrics.funnel:
        lines.append(f"| 1 | - | - | - | {_NA} | - |")
    lines.append("")
    return lines


def _models_section(metrics: TaskMetrics, scrubber) -> list[str]:
    lines = ["### Models and tokens", ""]
    lines.append("Served models carry the token sums. The requested models follow.")
    header = "| Model | Input | Output | Cache read | Cache write | Turns |"
    lines += ["", header, "|---|---|---|---|---|---|"]
    for model, stats in metrics.models.items():
        name = scrubber.scrub(model)
        lines.append(
            f"| {name} | {stats['input']} | {stats['output']} | {stats['cache_read']}"
            f" | {stats['cache_creation']} | {stats['turns']} |"
        )
    if not metrics.models:
        lines.append(f"| - | {_NA} | {_NA} | {_NA} | {_NA} | {_NA} |")
    requested = _requested_text(metrics, scrubber)
    hit = _NA if metrics.cache_hit_rate is None else f"{metrics.cache_hit_rate:.0%}"
    lines += [
        "",
        f"- requested models: {requested or _NA}",
        f"- cache hit rate: {hit}",
        "",
    ]
    return lines


def _requested_text(metrics: TaskMetrics, scrubber) -> str:
    pairs = [
        f"{scrubber.scrub(name)} x{count}"
        for name, count in metrics.requested_models.items()
    ]
    return ", ".join(pairs)


def _cost_section(metrics: TaskMetrics, scrubber) -> list[str]:
    lines = [
        "### Cost (estimate)",
        "",
        "The estimate uses the packaged price table with its source date.",
        "A model with no rate renders as unknown.",
        "",
        "| Model | USD |",
        "|---|---|",
    ]
    for model, cost in metrics.cost_by_model.items():
        lines.append(f"| {scrubber.scrub(model)} | {_money(cost)} |")
    for model in metrics.unknown_models:
        lines.append(f"| {scrubber.scrub(model)} | unknown (no rate in the table) |")
    lines.append(f"| total | {_money(metrics.cost_total)} |")
    lines += ["", "Cost split per agent:", "", "| Agent | USD |", "|---|---|"]
    if not metrics.per_agent:
        lines.append("| - | - |")
    for agent, stats in metrics.per_agent.items():
        lines.append(f"| {scrubber.scrub(agent)} | {_money(stats['cost'])} |")
    lines.append("")
    return lines


def _pipeline_section(metrics: TaskMetrics) -> list[str]:
    dora = metrics.dora
    lead = _ms(dora.get("lead_time_ms"))
    recovery = _ms(dora.get("recovery_ms"))
    rework = dora.get("rework_rate")
    rework_text = _NA if rework is None else f"{rework:.0%}"
    fail = dora.get("change_fail_signals")
    return [
        "### Pipeline proxies",
        "",
        f"- change lead time: {lead} ms",
        "- deployment frequency: n/a (no per-task proxy)",
        f"- change fail signals: {_NA if fail is None else str(fail)}",
        f"- recovery time: {recovery} ms",
        f"- rework rate: {rework_text}",
        "",
    ]


def _decisions_section(metrics: TaskMetrics, scrubber) -> list[str]:
    lines = ["### Decisions", ""]
    if not metrics.decisions:
        lines.append("- none recorded")
    for decision in metrics.decisions:
        summary = scrubber.scrub(str(decision["summary"] or "-"))
        agent = scrubber.scrub(str(decision["agent"]))
        tool = scrubber.scrub(str(decision["tool"]))
        stamp = decision["ts"] or _NA
        lines.append(f"- [{stamp}] {agent} via {tool}: {summary}")
    lines.append("")
    return lines


def _friction_section(metrics: TaskMetrics, scrubber) -> list[str]:
    friction = metrics.friction
    events = friction.get("permission_events") or []
    peak = friction.get("max_compaction_pre_tokens")
    lines = [
        "### Friction",
        "",
        f"- api errors: {friction.get('api_errors', 0)}",
        f"- failed tool calls: {friction.get('failed_tool_calls', 0)}",
        f"- compactions: {friction.get('compactions', 0)}",
        f"- max compaction pre-tokens: {_NA if peak is None else str(peak)}",
        f"- permission events: {len(events)}",
    ]
    for event in events:
        clean = _clean(event, scrubber)
        stamp = clean.get("ts") or _NA
        tool = clean.get("tool") or _NA
        lines.append(f"  - {stamp}: {tool}")
    lines.append("")
    return lines


def _machine_section(host: dict, scrubber) -> list[str]:
    lines = ["### Machine", ""]
    for key, value in host.items():
        text = _NA if value is None else str(value)
        lines.append(f"- {key}: {scrubber.scrub(text)}")
    lines.append("")
    return lines


def _redaction_section(scrubber) -> list[str]:
    lines = ["### Redaction", ""]
    counts = getattr(scrubber, "counts", {})
    if not counts:
        lines.append("- nothing needed redaction")
    for category, count in sorted(counts.items()):
        lines.append(f"- {category}: {count}")
    lines.append("")
    return lines


def render_json(metrics: TaskMetrics, host: dict, scrubber) -> str:
    payload = {
        "fingerprint": _clean(metrics.fingerprint, scrubber),
        "machine": _clean(host, scrubber),
        "models": {
            model: {
                "gen_ai.response.model": model,
                "gen_ai.usage.input_tokens": stats["input"],
                "gen_ai.usage.output_tokens": stats["output"],
                "gen_ai.usage.cache_read_input_tokens": stats["cache_read"],
                "gen_ai.usage.cache_creation_input_tokens": stats["cache_creation"],
                "turns": stats["turns"],
            }
            for model, stats in metrics.models.items()
        },
        "requested_models": metrics.requested_models,
        "cache_hit_rate": metrics.cache_hit_rate,
        "cost": {
            "by_model": metrics.cost_by_model,
            "by_agent": {
                agent: stats["cost"] for agent, stats in metrics.per_agent.items()
            },
            "unknown_models": metrics.unknown_models,
            "total": metrics.cost_total,
        },
        "gen_ai.tool.calls": [
            {
                "gen_ai.tool.name": call["tool"],
                "agent": call["agent"],
                "duration_ms": call["duration_ms"],
                "error": call["error"],
            }
            for call in metrics.funnel
        ],
        "decisions": _clean(metrics.decisions, scrubber),
        "friction": _clean(metrics.friction, scrubber),
        "dora": metrics.dora,
    }
    return json.dumps(_clean(payload, scrubber), indent=2, sort_keys=True) + "\n"
