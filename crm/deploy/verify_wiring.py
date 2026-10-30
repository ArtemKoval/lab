"""The wiring gate for the local AWS emulator: create the emulated runtime,
then invoke it through the backend's own runtime caller, and assert the
acceptance the backend reads.

Run from the crm directory, with the emulator up:

    AWS_ENDPOINT_URL=http://localhost:4566 \\
    AWS_DEFAULT_REGION=us-east-1 \\
    AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \\
    .venv/bin/python deploy/verify_wiring.py

Exit 0 when the wiring passes; exit 2 with the named step when it doesn't.
The emulator's runtime answers are canned, so this proves the wiring, not
the agent's behavior.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RUNTIME_NAME = "crm_agent"
REGION = "us-east-1"
ACCOUNT = "000000000000"
ACCEPTED = {"accepted": True}


def _aws_env() -> dict[str, str]:
    return {
        "AWS_ENDPOINT_URL": os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566"),
        "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION", REGION),
        "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    }


def fail(step: str, reason: str) -> int:
    print(f"FAIL at step '{step}': {reason}")
    return 2


def main() -> int:
    env = _aws_env()
    for key, value in env.items():
        os.environ[key] = value

    import boto3

    # Step 1: the emulator answers the control plane. The control-plane
    # operations live in the bedrock-agentcore-control client.
    try:
        control = boto3.client("bedrock-agentcore-control")
        control.list_agent_runtimes()
    except Exception as error:  # noqa: BLE001 — every failure names its step
        return fail("control-plane client", str(error))

    # Step 2: the runtime is registered (created once, reused after).
    arn = ""
    try:
        listed = control.list_agent_runtimes()
        for summary in listed.get("agentRuntimes", []):
            if summary.get("agentRuntimeName") == RUNTIME_NAME:
                arn = summary["agentRuntimeArn"]
                break
        if not arn:
            created = control.create_agent_runtime(
                agentRuntimeName=RUNTIME_NAME,
                roleArn=f"arn:aws:iam::{ACCOUNT}:role/crm-agent-runtime",
                agentRuntimeArtifact={
                    "containerConfiguration": {"containerUri": "crm/agent:latest"}
                },
                networkConfiguration={"networkMode": "PUBLIC"},
            )
            arn = created["agentRuntimeArn"]
    except Exception as error:  # noqa: BLE001
        return fail("create or find the runtime", str(error))
    print(f"runtime: {arn}")

    # Step 3: the backend's own runtime caller invokes it, and reads the
    # acceptance the emulator is configured to answer with.
    os.environ["CRM_AGENT_RUNTIME"] = arn
    from backend.runtime_calls import Wording, invoke

    wording = Wording(
        not_running="the runtime wasn't reached",
        couldnt_take="the runtime refused: {reason}",
        no_answer="the runtime didn't answer in time",
    )
    try:
        invoke(arn, "wiring-gate-session-00000000-0000-0000", {"operation": "wiring"}, wording)
    except Exception as error:  # noqa: BLE001
        return fail("invoke through the backend's runtime caller", str(error))

    print("wiring ok: backend caller -> botocore -> emulator -> acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
