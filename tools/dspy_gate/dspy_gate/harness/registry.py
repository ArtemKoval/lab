"""The harness registry: the opt-in contract of the gate system.

A capability enters the governed set by declaring a module here. Gate
0 eval rules, the manifest, and the datasets cover only the
capabilities this registry declares; every other capability stays with
the ordinary suite. Promoting a module to optimized is a one-line
change here plus a regeneration.
"""

_MODULES = {
    "ticket-triage": {
        "module": "Triage",
        "impl": "hand",
        "entry": "dspy_gate.harness.triage::triage",
        "examples": {
            "outage-keywords-route-to-on-call": {
                "ticket": "production down, all hands"
            },
            "billing-disputes-route-to-billing": {
                "ticket": "refund the June charge, invoice looks wrong"
            },
            "general-tickets-route-to-general": {
                "ticket": "how do I rename my workspace"
            },
            "escalation-happens-before-reply": {"ticket": "production down"},
        },
    },
}


def modules():
    """Return the registry map. One writer: this file."""
    return dict(_MODULES)
