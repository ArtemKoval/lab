"""Line-delimited JSON-RPC 2.0 codec for the stdio protocol.

One message is one JSON object on one line that ends with a newline. The
writer flushes; the framing rule lives in the shell, which owns the file
objects. A malformed line decodes to None, and the caller drops and logs it.
"""

import json

PROTOCOL_VERSION = 1
JSONRPC = "2.0"
APPLICATION_ERROR = -32000


def encode_line(message):
    """Encode one message dict as one protocol line with the trailing newline."""
    return json.dumps(message, separators=(",", ":")) + "\n"


def encode_request(message_id, method, params):
    return {"jsonrpc": JSONRPC, "id": message_id, "method": method, "params": params}


def encode_response(message_id, result):
    return {"jsonrpc": JSONRPC, "id": message_id, "result": result}


def encode_error(message_id, kind, message):
    return {
        "jsonrpc": JSONRPC,
        "id": message_id,
        "error": {
            "code": APPLICATION_ERROR,
            "message": message,
            "data": {"kind": kind},
        },
    }


def encode_notification(method, params):
    return {"jsonrpc": JSONRPC, "method": method, "params": params}


def decode_line(line):
    """Decode one protocol line into a dict, or None when the line is malformed."""
    try:
        message = json.loads(line)
    except json.JSONDecodeError:
        return None
    return message if isinstance(message, dict) else None
