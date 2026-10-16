"""Minimal server-sent-event reader for the OpenRouter chat stream.

The OpenRouter stream sends one `data:` field per line and ends the stream
with a `data: [DONE]` line. Comment lines and empty lines carry no data.
"""

DATA_FIELD = "data:"
DONE_MARKER = "[DONE]"


def parse_data_line(line):
    """Return the value of one SSE data line, or None when it carries no data.

    `line` is a str without its line terminator, as `iter_lines` yields it.
    The value loses one optional leading space, per the SSE field rules.
    """
    text = line.rstrip("\r")
    if not text.startswith(DATA_FIELD):
        return None
    value = text[len(DATA_FIELD):]
    if value.startswith(" "):
        value = value[1:]
    if not value:
        return None
    return value
