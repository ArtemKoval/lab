# Council Notes: proposal.md

## Author Summary

The proposal frames the change as two additions: the Langfuse server
stack (a compose profile for the local and floci runs, a dedicated CDK
app for AWS) and the copilot callback config. The case agent and
improver handlers exist and only need the variables. The env contract
is `LANGFUSE_BASE_URL`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`.
The judge and the Lambda stay untraced. Three capability deltas:
`crm-runtime`, `crm-copilot`, `crm-engine`.

## Reviewer Challenges

1. The Why section ran four sentences against the template's two.
2. "The emulator flow stays unchanged" buried the floci run, which the
   request names explicitly.
3. The read path contradicted itself: SETTINGS seam vs no code change
   vs the SDK variable name, and the reviewer held that
   `LANGFUSE_HOST` is the documented name.
4. The `crm/.env` read path named no loader mechanism.
5. The three-capability claim did not enumerate the spec tree.
6. Impact omitted the skill and README edits that What Changes
   promises.
7. Server-stack bullets carried design-level topology, and the
   "login is its guard" claim outran the component list.
8. Three load-bearing claims were unverified: the uv.lock pin, the
   deploy-time key writes, and the disabled-client behavior.
9. Compound sentences, vague wording, the heading shape, and a
   sequencing line for reviewers.

## Resolutions

- Accepted: the Why section is two sentences. The floci bullet states
  the behavior: the profile adds services beside the emulator, traces
  export to the compose server, the emulator service itself stays
  unchanged. The read path is explicit: the dev services read
  `crm/.env` through `--env-file`, the agent CLI through
  `load_dotenv`, the runtimes through the SETTINGS seam, and the SDK
  reads its own environment, so the handlers need no code change.
  Impact names the three skills, the README row, and the ADR.
- Accepted with correction: the reviewer's variable-name correction
  is wrong for the pinned SDK. The wheel of `langfuse` 4.16.0 reads
  `LANGFUSE_BASE_URL` as canonical and `LANGFUSE_HOST` as a
  deprecated alias (read from `langfuse/_client/environment_variables.py`
  of the downloaded wheel). The contract keeps the canonical name,
  and the proposal states the verification basis.
- Accepted: the AWS stack seeds through the same `LANGFUSE_INIT_*`
  mechanism as the compose, with operator-given values at deploy
  time. This removed the last asymmetry between the environments and
  keeps no UI step in the rollout.
- Accepted: the topology, secrets, and subnet reasoning moved to
  design.md. The proposal keeps the behavior-level inventory and the
  separate-app-bin contract. The guard wording is now "the Langfuse
  login guards the public endpoint".
- Verified, kept: `crm/uv.lock` pins `langfuse` 4.16.0 in the runtime
  group (read from the lock), and the disabled-client fallback is in
  `get_client.py` of the wheel. The deploy-time key write follows the
  existing rollout step that writes the same values into `crm/.env`.
- Verified, kept: the heading shape matches the archived proposals
  (H1 title, H3 subsections under What Changes).
- Accepted: the deltas carry the no-fail rule per capability, the
  spec-tree enumeration sits in the review summary, and one Order
  section states the landing sequence.

## Remaining Risks

- The AWS stack shape (ClickHouse on one task, public ALB over HTTP)
  is a design commitment that only a real rollout exercises.
- The compose smoke needs Docker on the host. The host notes say
  Docker Desktop starts by hand.
- The `openspec validate --strict` command failed once right after
  each file write in the same shell pipeline and passed on the re-run
  three times in a row. The cause is unexamined, and the handover
  carries
  the observation.
