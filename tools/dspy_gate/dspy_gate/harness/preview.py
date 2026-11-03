"""The fixture preview page: the deterministic e2e target.

A stdlib http.server serves fixed labels and fixed data rows, with no
animation and no clock. The journeys and the visual baselines bind to
this page behind the DSPY_GATE_E2E gate until a product surface binds
to the same machinery.
"""

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Triage Console</title></head>
<body>
  <main>
    <h1>Triage Console</h1>
    <table id="triage-results" aria-label="Triage results">
      <thead>
        <tr><th>ticket</th><th>severity</th><th>team</th></tr>
      </thead>
      <tbody>
        <tr><td>production down</td><td>P0</td><td>on-call</td></tr>
        <tr><td>refund the June charge</td><td>P2</td><td>billing</td></tr>
        <tr><td>rename my workspace</td><td>P3</td><td>general</td></tr>
      </tbody>
    </table>
    <p id="escalation-banner" role="status">Escalation recorded before reply</p>
  </main>
</body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    """One deterministic page for every request."""

    def do_GET(self):  # noqa: N802 - http.server contract
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # keep the run output clean


class PreviewServer:
    """The started server handle: port and shutdown."""

    def __init__(self, httpd):
        self._httpd = httpd
        self.port = httpd.server_address[1]

    def shutdown(self):
        self._httpd.shutdown()
        self._httpd.server_close()


def configured_port(default=8321):
    """Read the port from the environment, or return the default."""
    raw = os.environ.get("DSPY_GATE_PREVIEW_PORT")
    return int(raw) if raw else default


def start_server(port=None):
    """Start the preview server; port 0 picks a free ephemeral port."""
    bind_port = configured_port() if port is None else port
    httpd = HTTPServer(("127.0.0.1", bind_port), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return PreviewServer(httpd)
