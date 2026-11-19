---
source:
  system: Northgate Public Library
  owner: Desk operations
  reviewed: "2026-10-01"
version: "2026.2"
---

# Northgate Public Library: Librarian Manual

Version 2026.2. This manual tells the desk how to work a loan request against the loan rules. The rules are the contract with the borrower, and they always come first. This manual says how the desk reads them.

## 1. The three decisions

The desk makes one of three decisions on every request:

- **approve**: the desk issues the loan, with the term the rules give.
- **decline**: the desk refuses the request, and tells the borrower which rule refuses it.
- **refer**: the desk sends the request to the lead librarian, with the reason.

## 2. Authority

The desk librarian approves loans of 14 days or fewer. A loan term over 14 days needs the lead librarian's sign-off, and the desk librarian cannot give it. The lead librarian signs the over-limit term, and then the system issues the loan.

## 3. What a request carries

The desk examines the request before deciding:

- the title, with its ISBN and its list price;
- the copy counts of the title: how many copies the library holds, and how many are on loan right now;
- the borrower's membership, with its tier and its active loan count;
- any overdue title on the borrower's card.

## 4. When the desk declines

The desk declines a request when:

- every copy of the title is on loan, and no copy is free (rules section 3);
- the request asks more copies than the catalog holds free, as a bulk request does (rules section 3);
- the borrower already holds 3 loans (rules section 5);
- the borrower holds an overdue title (rules section 5);
- the request asks a standard membership for a term past 14 days, or a renewal past the tier cap (rules section 4).

The decline reason names the rule, so the borrower knows what changed would make the loan possible.

## 5. When the desk refers

The desk refers a request when:

- the title sits on the special collection shelves, or its list price is $200 or more (rules section 7);
- the card is in bad standing, or the identity needs a closer look (rules section 8).

The referral reason says what is needed and who should look at it.

## 6. The calculation

The desk works the term out with `resolve_outcome` after it decides the covered lines. One approved request carries one line, and its `nights` field holds the requested days, with `hours` at zero. The tool grants the base term of the plan, adds the renewal days past the base term, caps the term at the tier cap, and says whether the term needs the lead's sign-off. The desk never works the term by hand.
