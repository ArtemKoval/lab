"""The pilot triage hand module.

Behavior contract: openspec/changes/add-dspy-gate/specs/ticket-triage/
spec.md. A hand implementation: deterministic keyword routing with no
model call at eval time. Escalation precedes any reply for P0.
"""

OUTAGE_KEYWORDS = ("production down", "data loss")
BILLING_KEYWORDS = ("charge", "refund", "invoice")


def triage(ticket, when=None):
    """Assign a severity and a routing team to one support ticket.

    Returns (prediction, trace). The trace records the escalate tool
    call before the reply step for every P0 ticket.
    """
    del when  # the generic input slot; the ticket is the real input
    text = ticket.lower()
    trace = []
    if any(k in text for k in OUTAGE_KEYWORDS):
        prediction = {"severity": "P0", "team": "on-call"}
        trace.append({"tool": "escalate", "severity": "P0"})
    elif any(k in text for k in BILLING_KEYWORDS):
        prediction = {"severity": "P2", "team": "billing"}
    else:
        prediction = {"severity": "P3", "team": "general"}
    trace.append({"step": "reply", "team": prediction["team"]})
    return prediction, trace
