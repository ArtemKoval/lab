"""The stdio shell that the Electron main process spawns.

The shell owns the pipes: it reads request lines from stdin, writes response
and notification lines to stdout, and sends every log to stderr. stdout stays
reserved for protocol lines. One chat request runs in one daemon worker
thread, so a `chat_stop` or a stdin EOF is always handled at once.
"""

import itertools
import logging
import sys
import threading

from . import codec
from .errors import ClientError, KIND_API

LOG = logging.getLogger("backend.shell")

READY_METHOD = "ready"
CHUNK_METHOD = "chat/chunk"
DONE_METHOD = "chat/done"
ERROR_METHOD = "chat/error"


class Shell:
    """Request dispatcher over one writer. `run` owns the read loop."""

    def __init__(self, client, out, interpreter_path):
        self._client = client
        self._out = out
        self._interpreter_path = interpreter_path
        self._write_lock = threading.Lock()
        self._stop_events = {}
        self._stream_ids = itertools.count(1)

    def write(self, message):
        """Write one protocol line and flush before returning."""
        with self._write_lock:
            self._out.write(codec.encode_line(message))
            self._out.flush()

    def notify(self, method, params):
        self.write(codec.encode_notification(method, params))

    def write_ready_line(self):
        self.notify(READY_METHOD, {
            "version": codec.PROTOCOL_VERSION,
            "interpreter": self._interpreter_path,
        })

    def respond(self, message_id, result):
        self.write(codec.encode_response(message_id, result))

    def respond_error(self, message_id, error):
        self.write(codec.encode_error(message_id, error.kind, error.message))

    def handle_line(self, line):
        """Handle one input line. Return False when the shell must stop."""
        message = codec.decode_line(line)
        if message is None:
            LOG.warning("dropped malformed line: %.200s", line)
            return True
        method = message.get("method")
        if not method:
            LOG.warning("dropped message without a method: %.200s", line)
            return True
        if "id" in message:
            return self.handle_request(message["id"], method, message.get("params") or {})
        LOG.warning("dropped notification from the parent: %s", method)
        return True

    def handle_request(self, message_id, method, params):
        if method == "validate_key":
            self._call(message_id, lambda: self._validate_key(params))
        elif method == "list_models":
            self._call(message_id, lambda: {"models": self._client.list_models()})
        elif method == "chat_start":
            self._chat_start(message_id, params)
        elif method == "chat_stop":
            self._chat_stop(message_id, params)
        elif method == "shutdown":
            self.respond(message_id, {"stopping": True})
            return False
        else:
            self.respond_error(message_id, ClientError(KIND_API, f"Unknown method {method}"))
        return True

    def _call(self, message_id, action):
        try:
            self.respond(message_id, action())
        except ClientError as exc:
            self.respond_error(message_id, exc)

    def _validate_key(self, params):
        self._client.validate_key(_required(params, "key"))
        return {"valid": True}

    def _chat_start(self, message_id, params):
        stream_id = next(self._stream_ids)
        stop_event = threading.Event()
        self._stop_events[stream_id] = stop_event
        worker = threading.Thread(
            target=self._run_stream,
            args=(stream_id, _required(params, "key"), params.get("model", "any"),
                  _required(params, "messages"), stop_event),
            daemon=True,
        )
        worker.start()
        self.respond(message_id, {"stream_id": stream_id})

    def _chat_stop(self, message_id, params):
        stop_event = self._stop_events.get(_required(params, "stream_id"))
        if stop_event is None:
            self.respond_error(message_id, ClientError(KIND_API, "Unknown stream"))
            return
        stop_event.set()
        self.respond(message_id, {"stopping": True})

    def _run_stream(self, stream_id, key, model, messages, stop_event):
        try:
            for event, data in self._client.chat_stream(
                key, model, messages, should_stop=stop_event.is_set
            ):
                if event == "chunk":
                    self.notify(CHUNK_METHOD, {"stream_id": stream_id, "text": data})
                elif event == "error":
                    self.notify(ERROR_METHOD, {
                        "stream_id": stream_id,
                        "kind": data.kind,
                        "message": data.message,
                    })
                    return
                else:
                    self.notify(DONE_METHOD, {
                        "stream_id": stream_id,
                        "text": data["text"],
                        "stopped": data["stopped"],
                    })
                    return
        except Exception:
            LOG.exception("chat stream %s crashed", stream_id)
            self.notify(ERROR_METHOD, {
                "stream_id": stream_id,
                "kind": KIND_API,
                "message": "The chat stream failed inside the backend",
            })
        finally:
            # The key is always present here, so the default is unreachable;
            # the no-default mutant is equivalent.
            self._stop_events.pop(stream_id, None)  # pragma: no mutate

    def run(self, lines):
        """Serve until a shutdown request or the end of the input."""
        self.write_ready_line()
        for line in lines:
            if not self.handle_line(line):
                return


def _required(params, name):
    value = params.get(name)
    if value is None:
        raise ClientError(KIND_API, f"Missing parameter {name}")
    return value


def serve(stdin, stdout, client, interpreter_path):
    """Run the shell on the given pipes with the given client."""
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    shell = Shell(client, stdout, interpreter_path)
    shell.run(stdin)
    LOG.info("backend stopped")
