# Design: add-crm-local-aws

## Source

ADR 0008 owns the rule. This change builds the runbook that makes it true on a dev box. The user asked for a skill that runs the app inside the devcontainer with floci.

## Plan review

One insight drove the design. The backend's runtime caller is plain boto3 with no endpoint override, so boto3's native `AWS_ENDPOINT_URL` variable bridges to the emulator with no engine code change. The emulator's canned runtime answer is configurable, so the compose file sets it to the acceptance the backend's `take_answer` reads. The wiring gate then asserts the real path: backend caller → botocore → floci → acceptance.

## Key decisions

- No engine code changes: the bridge is `AWS_ENDPOINT_URL`, `AWS_DEFAULT_REGION`, and dummy credentials, which botocore reads natively.
- The compose file sets `FLOCI_SERVICES_BEDROCK_AGENT_CORE_INVOKE_RESPONSE` to the backend's acceptance, and names its container for the down step.
- The devcontainer gains a Docker feature, so compose runs from inside it.
- The wiring gate is a committed script at `crm/deploy/verify_wiring.py`, run by the skill as its gate. It is not a pytest, because it needs the emulator up.
- The gateway and memory variables are set by the skill. The skill marks their emulator coverage as partial: the runtime invoke path is the proven one.
- The skill changes no engine behavior: with `CRM_AGENT_RUNTIME` unset, the app runs on the laptop route exactly as before.

## Failure modes

- The emulator is down: the gate exits 2 and names the connection.
- The runtime ARN is not registered in the emulator: the invoke returns a control-plane error, and the gate names it.
- Port 4566 is taken: compose fails, and the readiness step names the check.
