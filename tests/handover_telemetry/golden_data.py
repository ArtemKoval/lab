"""The pinned goldens for the renderers: the fixture session, the
stub machine dict, and the exact markdown and JSON text. The golden
text is generated from the committed fixtures only. Read the goldens
line by line before you change them."""

import tempfile
from pathlib import Path

from handover_telemetry import logparse, metrics, pricing, redact, render, transcript

FIXTURES = Path(__file__).parent / "fixtures"
SESSION_DIR = FIXTURES / "session"
HOOK_LOG = FIXTURES / "hook" / "sess-1.jsonl"

HOST = {
    "kernel": "Linux",
    "arch": "x86_64",
    "distro": "Ubuntu 24.04.3 LTS",
    "cpu_model": "AMD Ryzen 9 7950X",
    "cpu_count": 32,
    "mem_total_gb": 62.7,
    "disk_total_gb": 500.0,
    "python": "3.12.3",
    "git": "git version 2.43.0",
    "node": "v22.20.0",
    "container": "docker",
    "gpu": "NVIDIA GeForce RTX 4090",
}


def build_metrics() -> metrics.TaskMetrics:
    """Parse the committed fixture session and derive the metrics."""
    with tempfile.TemporaryDirectory() as name:
        root = Path(name)
        main = root / "main.jsonl"
        main.write_text(
            (SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8"
        )
        sub = root / "sess-1" / "subagents"
        sub.mkdir(parents=True)
        (sub / "agent-42.jsonl").write_text(
            (SESSION_DIR / "sess-1" / "subagents" / "agent-42.jsonl").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        session = transcript.parse_session(main)
        logparse.apply_hook_durations(session.primary.tool_calls, HOOK_LOG)
        return metrics.compute(
            session, price_table=pricing.load_prices(), hook_log=HOOK_LOG
        )


def render_reports() -> tuple[str, str]:
    """Render the fixture session to the markdown and JSON pair."""
    got = build_metrics()
    scrubber = redact.default_redactor()
    md = render.render_markdown(got, dict(HOST), scrubber)
    js = render.render_json(got, dict(HOST), scrubber)
    return md, js

GOLDEN_MD = """\
## Telemetry

### Run
- session: sess-1
- agent version: 2.1.312
- entrypoint: cli
- branch: feat/demo
- host: Linux x86_64

### Funnel

| # | Agent | Tool | Start | ms | Exit |
|---|---|---|---|---|---|
| 1 | primary | Bash | 2026-10-29T10:00:05.000Z | 1960 | 1 |
| 2 | primary | Agent | 2026-10-29T10:00:09.000Z | 1000 | n/a |
| 3 | agent-42 | Read | 2026-10-29T10:00:10.200Z | n/a | n/a |
| 4 | primary | AskUserQuestion | 2026-10-29T10:00:13.000Z | n/a | n/a |
| 5 | primary | AskUserQuestion | 2026-10-29T10:00:13.000Z | n/a | n/a |

### Models and tokens

Served models carry the token sums. The requested models follow.

| Model | Input | Output | Cache read | Cache write | Turns |
|---|---|---|---|---|---|
| glm-5.3-flash | 1250 | 350 | 10000 | 200 | 5 |

- requested models: glm-5.3-flash[1m] x4, claude-opus-5-5 x1
- cache hit rate: 87%

### Cost (estimate)

The estimate uses the packaged price table with its source date.
A model with no rate renders as unknown.

| Model | USD |
|---|---|
| glm-5.3-flash | $0.0062 |
| total | $0.0062 |

### Pipeline proxies

- change lead time: n/a ms
- deployment frequency: n/a (no per-task proxy)
- change fail signals: 2
- recovery time: 3000 ms
- rework rate: n/a

### Decisions

- [2026-10-29T10:00:09.000Z] primary via Agent: adversarial-reviewer: review the diff
- [2026-10-29T10:00:13.000Z] primary via AskUserQuestion: Which gate runs first?
- [2026-10-29T10:00:13.000Z] primary via AskUserQuestion: Which model serves this task?

### Friction

- api errors: 1
- failed tool calls: 2
- retries: 0
- compactions: 1
- max compaction pre-tokens: 90000
- permission events: 1
  - 2026-10-29T10:00:16.000Z: deny on Bash

### Machine

- kernel: Linux
- arch: x86_64
- distro: Ubuntu 24.04.3 LTS
- cpu_model: AMD Ryzen 9 7950X
- cpu_count: 32
- mem_total_gb: 62.7
- disk_total_gb: 500.0
- python: 3.12.3
- git: git version 2.43.0
- node: v22.20.0
- container: docker
- gpu: NVIDIA GeForce RTX 4090

### Redaction

- nothing needed redaction
"""

GOLDEN_JSON = """\
{
  "cache_hit_rate": 0.8733624454148472,
  "cost": {
    "by_model": {
      "glm-5.3-flash": 0.00624
    },
    "total": 0.00624,
    "unknown_models": []
  },
  "decisions": [
    {
      "agent": "primary",
      "summary": "adversarial-reviewer: review the diff",
      "tool": "Agent",
      "ts": "2026-10-29T10:00:09.000Z"
    },
    {
      "agent": "primary",
      "summary": "Which gate runs first?",
      "tool": "AskUserQuestion",
      "ts": "2026-10-29T10:00:13.000Z"
    },
    {
      "agent": "primary",
      "summary": "Which model serves this task?",
      "tool": "AskUserQuestion",
      "ts": "2026-10-29T10:00:13.000Z"
    }
  ],
  "dora": {
    "change_fail_signals": 2,
    "deployment_frequency": null,
    "lead_time_ms": null,
    "recovery_ms": 3000.0,
    "rework_rate": null
  },
  "fingerprint": {
    "entrypoint": "cli",
    "git_branch": "feat/demo",
    "session_id": "sess-1",
    "version": "2.1.312"
  },
  "friction": {
    "api_errors": 1,
    "compactions": 1,
    "failed_tool_calls": 2,
    "max_compaction_pre_tokens": 90000,
    "permission_events": [
      {
        "decision": "deny",
        "tool": "Bash",
        "ts": "2026-10-29T10:00:16.000Z"
      }
    ],
    "retries": 0
  },
  "gen_ai.tool.calls": [
    {
      "agent": "primary",
      "duration_ms": 1960.0,
      "error": false,
      "gen_ai.tool.name": "Bash"
    },
    {
      "agent": "primary",
      "duration_ms": 1000.0,
      "error": false,
      "gen_ai.tool.name": "Agent"
    },
    {
      "agent": "agent-42",
      "duration_ms": null,
      "error": true,
      "gen_ai.tool.name": "Read"
    },
    {
      "agent": "primary",
      "duration_ms": null,
      "error": false,
      "gen_ai.tool.name": "AskUserQuestion"
    },
    {
      "agent": "primary",
      "duration_ms": null,
      "error": false,
      "gen_ai.tool.name": "AskUserQuestion"
    }
  ],
  "machine": {
    "arch": "x86_64",
    "container": "docker",
    "cpu_count": 32,
    "cpu_model": "AMD Ryzen 9 7950X",
    "disk_total_gb": 500.0,
    "distro": "Ubuntu 24.04.3 LTS",
    "git": "git version 2.43.0",
    "gpu": "NVIDIA GeForce RTX 4090",
    "kernel": "Linux",
    "mem_total_gb": 62.7,
    "node": "v22.20.0",
    "python": "3.12.3"
  },
  "models": {
    "glm-5.3-flash": {
      "gen_ai.request.model": "glm-5.3-flash",
      "gen_ai.usage.cache_creation_input_tokens": 200,
      "gen_ai.usage.cache_read_input_tokens": 10000,
      "gen_ai.usage.input_tokens": 1250,
      "gen_ai.usage.output_tokens": 350,
      "turns": 5
    }
  },
  "requested_models": {
    "claude-opus-5-5": 1,
    "glm-5.3-flash[1m]": 4
  }
}
"""

GOLDEN_EMPTY_MD = """\
## Telemetry

### Run
- session: n/a
- agent version: n/a
- entrypoint: n/a
- branch: n/a
- host: n/a n/a

### Funnel

| # | Agent | Tool | Start | ms | Exit |
|---|---|---|---|---|---|
| 1 | - | - | - | n/a | - |

### Models and tokens

Served models carry the token sums. The requested models follow.

| Model | Input | Output | Cache read | Cache write | Turns |
|---|---|---|---|---|---|
| - | n/a | n/a | n/a | n/a | n/a |

- requested models: n/a
- cache hit rate: n/a

### Cost (estimate)

The estimate uses the packaged price table with its source date.
A model with no rate renders as unknown.

| Model | USD |
|---|---|
| total | unknown |

### Pipeline proxies

- change lead time: n/a ms
- deployment frequency: n/a (no per-task proxy)
- change fail signals: n/a
- recovery time: n/a ms
- rework rate: n/a

### Decisions

- none recorded

### Friction

- api errors: 0
- failed tool calls: 0
- retries: 0
- compactions: 0
- max compaction pre-tokens: n/a
- permission events: 0

### Machine


### Redaction

- nothing needed redaction
"""
