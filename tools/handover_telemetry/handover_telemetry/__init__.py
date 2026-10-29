"""handover_telemetry: the redacted telemetry block for handover issues.

A stdlib package with two entries. The hook module records session
events to a local log. The CLI reads that log and the Claude Code
transcripts, and renders a redacted telemetry report. See
tools/handover_telemetry/README.md for the commands.
"""

__version__ = "1.0.0"
