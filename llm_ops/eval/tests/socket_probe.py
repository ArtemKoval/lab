"""Run one question with the real metric and the apfel judge. Print each network target.

A subprocess starts this file. It blocks DNS lookups and connections, and it records the
target of each attempt. The judge uses a mock transport, so the judge itself opens no
socket. Any recorded target comes from other code, for example telemetry.
"""

import atexit
import json
import socket

targets = []
result = {}


def block(target):
    targets.append(str(target))
    raise OSError("blocked by the probe")


def blocked_getaddrinfo(host, *args, **kwargs):
    block(host)


def blocked_connect(self, address):
    block(address)


def report():
    # The handler is first in the list, so it runs after the exit handlers of other code.
    print(json.dumps({"targets": targets, **result}))


atexit.register(report)
socket.getaddrinfo = blocked_getaddrinfo
socket.socket.connect = blocked_connect

import httpx2  # noqa: E402
from fake_apfel import FakeApfel  # noqa: E402

from apfel_eval import run  # noqa: E402
from apfel_eval.judge import ApfelJudge  # noqa: E402

client = httpx2.Client(transport=httpx2.MockTransport(FakeApfel()))
judge = ApfelJudge("http://host.docker.internal:11434/v1", http_client=client)
outcome = run.run_case(judge, run.build_metric(judge, 0.5), run.cases()[0])
result["error"] = outcome.error
result["score"] = outcome.score
