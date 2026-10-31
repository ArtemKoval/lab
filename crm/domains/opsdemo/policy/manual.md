---
source:
  system: Nimbus OpsDesk
  owner: Head of operations
  reviewed: "2026-10-01"
version: "2026.1"
---

# Nimbus OpsDesk: Operations Manual

Version 2026.1. This manual says how the desk reads the operations wording.

## 1. Working an escalation

Work one escalation at a time. Read the report, the site's SLA and the site's earlier escalations. Read the section of the wording that bears on the fault with `read_section`, and look up a term, a field meaning, the tier's numbers or the outside facts in the context layer. Then estimate the effort with the effort rules, decide, and record the decision. Record the decision last, so its reason carries the explanation.

## 2. The three decisions

- Approve, when the fault meets everything in section 3 of the wording. The escalation carries the effort the rules worked out for the items judged covered.
- Decline, when the fault fails anything in section 3, or the filing window is gone. The reason names what failed.
- Refer, when the facts do not say, or when the fault needs a decision the desk does not own. The reason says what is needed and who should look at it.

An approval's effort is the one the rules worked out. The operations lead signs off an approval over the escalation limit, and nothing moves until the lead signs.

## 3. Repeat faults

An escalation that names a fault the platform team already fixed inside 3 months escalates with that history attached. Read the site's earlier escalations, and name the earlier reference in the reason, so the platform team sees the pattern. A fault a restart cleared and that came back is a repeat fault.

## 4. The filing window

The window is 14 days from the incident, and the desk gives a site 2 days of grace. Count from the incident date to the filed date. A report inside the window plus the grace is in time.

## 5. When to refer

Refer when the fault may be the site's own wiring, and the facts cannot separate the two. Refer when the site asks for an exception to the wording. The reason says what is needed and who should look at it, so the lead can answer it in one reading.
