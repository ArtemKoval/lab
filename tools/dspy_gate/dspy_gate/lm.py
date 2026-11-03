"""The one model factory: every model call of the gate system is
declared here, pinned by gates.yaml.

A second constructor site would silently opt a code path out of the
pin governance, so this module is the only place that builds a model
client. Bumping any pin routes through Gate 5 re-certification.
"""

import os
from pathlib import Path

from . import gatepolicy

ZAI_BASE = "https://api.z.ai/api/paas/v4/"
POLICY_PATH = Path(__file__).resolve().parents[1] / "gates.yaml"
_built = []


class MissingKeyError(RuntimeError):
    """A live model build without the provider key in the environment."""


def load_policy():
    """Read the effective policy file."""
    return gatepolicy.load(POLICY_PATH)


def lm_for(role, policy=None, key_var=None):
    """Build the pinned model client for one role.

    The dspy import stays lazy: the hermetic root suite stubs the
    module, and a live build needs the provider key.
    """
    effective = policy or load_policy()
    spec = gatepolicy.roles(effective)[role]
    key_name = key_var or spec_key_var(effective)
    key = os.environ.get(key_name, "")
    if not key:
        raise MissingKeyError(f"missing {key_name} for role {role}")
    import dspy

    thinking = spec.get("thinking")
    client = dspy.LM(
        "openai/" + spec["model"],
        api_base=spec_base(effective),
        api_key=key,
        max_tokens=spec.get("max_tokens", 8192),
        temperature=spec.get("temperature", 0.6),
        num_retries=2,
        model_kwargs=(
            {"extra_body": {"thinking": {"type": thinking}}} if thinking else {}
        ),
    )
    _built.append(client)
    return client


def spec_key_var(policy):
    """The env variable name the policy names for the provider key."""
    return policy.get("models", {}).get("key_var", "ZAI_API_KEY")


def spec_base(policy):
    """The provider base URL from the policy."""
    return policy.get("models", {}).get("base_url", ZAI_BASE)
