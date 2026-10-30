---
name: crm-onboard-domain
description: Onboard a new domain to the crm engine from a free-form description. Use this skill when the user asks to add a domain pack, to put a new domain under crm/domains/, or to teach the crm engine a new kind of business. Gives the five steps, the gate at each step, the engine constraints, and the validator and smoke commands.
---

# crm-onboard-domain

The crm engine is generic. It runs on domain packs at `crm/domains/<name>/`,
and the pack carries every domain word. The reference pack is
`crm/domains/insurance/`. Read it first: `manifest.json`, `rules.py`, the
files under `policy/`, `data/`, `instructions/`, and `context/`, and
`evals/decisions.json`.

## Never edit engine code

This skill writes pack files only. Do not change `crm/backend/`,
`crm/agent/`, `crm/context/`, `crm/domains/loader.py`, `crm/validate.py`,
or `crm/smoke.py`. If the pack seems to need an engine change, stop, and
tell the user.

## Engine constraints

- The manifest at `crm/domains/<name>/manifest.json` carries these keys:
  `name`, `display_name`, `engine_api`, `rules`, `settings`, `documents`,
  and `seed`. The key `name` equals the folder name. The key `engine_api`
  is `1`. The key `rules` is `"rules"`. The key `settings` carries
  `award_approval_limit`. The key `documents` carries the short names of
  the policy files. The key `seed` carries `cases`, `customers`,
  `contracts`, `workers`, and `company`, each a file name under `data/`.
- `rules.py` defines `work_out_award(contract, plans, request,
  approval_limit)` and `needs_sign_off(award, approval_limit)`, with these
  exact parameter names in this order. Import the engine types from
  `backend.models`: `Benefit`, `CalculationStep`, `Line`, `Award`,
  `AwardRequest`, `Plan`, `Plans`, `Contract`. Write your own dataclass
  `Limits` when you need one. The rules are pure code, with no engine I/O.
- Each policy document starts with YAML front matter between two `---`
  lines. The front matter carries `source` with `system`, `owner`, and
  `reviewed`, and a `version`.
- `context/` holds `glossary.yaml`, `plans.yaml`, `data_dictionary.yaml`,
  `case_rules.yaml`, and `reference_data.yaml`. Copy the insurance files'
  shape. Replace the content with the new domain's content.
- The seed files use the schemas of the insurance pack. `cases` carries
  `case_id`, `customer_id`, `contract_id`, `case_type`, `submitted_on`,
  `incident_date`, `incident_location`, `summary`, `story`, `items`, and
  `documents`, with `status` at `waiting`. `customers` carries
  `customer_id`, `name`, `email`, `phone`, `date_of_birth`, `address`,
  `customer_since`, and `previous_cases`. `contracts` carries
  `contract_id`, `customer_id`, `plan`, `add_ons`, `purchased_on`,
  `sold_through`, and `status`, plus the plan fields that your `rules.py`
  reads. `workers` carries `worker_id`, `name`, `role`, `email`, and
  `can_approve_over_limit`, and at least one worker approves over the
  limit.
- `evals/decisions.json` carries `case_id`, `decision` (`approve`,
  `decline`, or `refer`), `award`, `reason`, `reference`, `worker_id`,
  `tiny`, and `difficulty`. Every `case_id` names a case in
  `data/cases.json`. The held-out sets stay out of the queue.
- `instructions/` holds `case.md` and `queue.md`. They name only the tools
  that the engine serves. Never name `work_claim`, `list_claims`,
  `pay_claim`, or `pay_payout`.
- No file name under `data/`, `policy/`, `instructions/`, or `evals/`
  carries `claim`, `payout`, or `handler`. Domain words in file content
  are fine.

The engine serves these tools to the case agent: `get_case`, `get_contract`,
`get_case_history`, `search_documents`, `read_section`, `calculate_award`,
`record_decision`, `pay_case`, `list_cases`, `write_todos`, `work_case`.

## Step 1: Extract

1. Read the free-form description.
2. Name the entities: cases, customers, contracts, workers, plans.
3. Name the decision kinds, the award rules, and the thresholds.
4. Write the extraction down, for the user to read.

Gate: do not go to step 2 before the user agrees to the extraction.

## Step 2: Generate

1. Create `crm/domains/<name>/` with `manifest.json`, `rules.py`,
   `policy/`, `context/`, `data/`, `instructions/`, and `evals/`.
2. Ground every file on the shape of the insurance pack.

Gate: every file obeys the engine constraints above.

## Step 3: Validate

Run this from `crm/`:

```bash
.venv/bin/python validate.py <name>
```

Exit 0 means the pack is clean. Exit 2 prints named findings. Repair the
named files. Run the command again, until the exit is 0.

Gate: exit 0 from the validator.

## Step 4: Smoke

Run this from `crm/`:

```bash
.venv/bin/python smoke.py <name>
```

The smoke run seeds a temporary database and works three cases on the stub
model. It needs no network and no model key.

Gate: exit 0, and three decision lines print.

## Step 5: Review

1. Show the pack to the user: the manifest, the rules, and the held-out
   eval decisions.
2. Say that the held-out evals need human review, before anyone makes an
   accuracy claim.
3. Say that this skill changed no engine code.

Gate: the user accepts the pack.
