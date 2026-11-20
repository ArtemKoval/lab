---
source:
  system: AutoFix service operations
  owner: Head of Service Operations
  reviewed: "2026-11-19"
version: "2026.1"
---

# The AutoFix desk manual

The manual says how the desk reads the wording. It carries the routing
order, the certified EV gate, the desk's authority, and the escalation
rule. The wording always comes first.

## 1. The desk's authority

A desk worker decides approve, decline, or refer on a waiting job. A desk
worker authorizes up to 600 pounds. An authorization over 600 pounds is
still an approve the desk records: the engine holds it, and the payment
waits for the service manager's sign-off. A referred job waits for the
service manager's resolution.

## 2. The routing order

The desk routes every job to one garage, in this order. Each step filters
or ranks the candidates, and the next step works on what the step before it
left.

1. Brand first. The garage services the vehicle's make. A brand match
   outranks every other fact.
2. Specialisms next. The garage holds the specialisms the fault lines need.
   A garage with more of the needed specialisms outranks a garage with
   fewer.
3. Location next. A garage in the caller's city outranks a garage in
   another city. Distance follows the city facts in the reference data.
4. Queue capacity last. A garage with more free slots outranks a garage
   with fewer. The free-slot facts live in the reference data.

## 3. The certified EV gate

An EV vehicle never goes to a garage without the certified EV mark, at any
step of the routing order. The gate filters the candidates before the brand
step. When the caller's city holds no certified garage, the desk refers the
job to the service manager, and the reason names the gap.

## 4. The decision

The desk names the chosen garage in the decision reason, with the routing
facts it relied on: the brand match, the specialisms, the city, and the
free slots. The estimate comes from the fault lines of the job, and the
wording's excess and cap apply to it.

## 5. The escalation

Two roads lead to the service manager. The sign-off hold: an approve whose
authorization passes 600 pounds waits for the service manager's sign-off,
and the desk records it as an approve. The referral: when the certified EV
gate finds no garage in the caller's city, the desk refers the job, and
the reason names the gap. The service manager resolves a referred job with
the same wording and the same routing order.
