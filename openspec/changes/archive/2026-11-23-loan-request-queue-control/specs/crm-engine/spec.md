## ADDED Requirements

### Requirement: The desk adds a case at run time
The API SHALL offer `POST /api/cases` behind the worker and agent guard.
The route SHALL write the new case straight to the database with status
`waiting`. The route SHALL refuse a customer or a contract the database
does not hold with a 404, and SHALL not touch the seed files. The route
SHALL set `submitted_on` to the current date when the request omits it,
and SHALL refuse a request whose summary, story, or items are missing or
empty.

#### Scenario: A created request lands in the queue as waiting
- **GIVEN** a seeded library database
- **WHEN** the desk posts a valid request for an existing customer and
  contract
- **THEN** the reply carries a generated case id with the pack prefix and
  a `waiting` status
- **AND** a following `GET /api/cases` lists the new case

#### Scenario: An unknown customer is refused
- **GIVEN** a seeded library database
- **WHEN** the desk posts a request naming a customer the database does
  not hold
- **THEN** the reply is 404 and no case row is written

#### Scenario: An unknown contract is refused
- **GIVEN** a seeded library database
- **WHEN** the desk posts a request naming a contract the database does
  not hold
- **THEN** the reply is 404 and no case row is written

#### Scenario: An empty summary is refused
- **GIVEN** a seeded library database
- **WHEN** the desk posts a request whose summary or story is empty, or
  whose item list carries no item
- **THEN** the reply is 422 and no case row is written

### Requirement: The case id comes from the pack's series
The route SHALL generate the case id from the pack's id series: the scan
runs over the cases that carry no evaluation copy marker, reads the
alphabetic prefix and the trailing number of the highest existing case
id, and takes the next number. A database with no cases at all SHALL
receive `C-1` as the first generated id.

#### Scenario: The id series skips past the seed
- **GIVEN** a library database whose highest case id is `LN-5003`
- **WHEN** the desk posts three valid requests in a row
- **THEN** the generated ids run `LN-5004`, `LN-5005`, `LN-5006` in order

#### Scenario: An evaluation copy does not move the series
- **GIVEN** a library database whose highest regular case id is `LN-5003`
  and whose highest evaluation copy id is `LN-5003-E7`
- **WHEN** the desk posts one valid request
- **THEN** the generated id is `LN-5004`, not a number read off the copy

#### Scenario: The first case in an empty database
- **GIVEN** a database whose case table holds no cases
- **WHEN** the desk posts one valid request
- **THEN** the generated id is `C-1`

### Requirement: The control's pickers read the desk's people and memberships
The existing customer search SHALL return every customer when the name
query is absent, and SHALL sit behind the same worker and agent guard as
the queue reads, returning the identifier and the name of every match.
The API SHALL offer `GET /api/customers/{customer_id}/contracts`,
returning only the contracts that belong to that customer.

#### Scenario: The customer list feeds the picker
- **GIVEN** a seeded library database
- **WHEN** the desk reads the customer search without a name query
- **THEN** every seed customer appears with the identifier and the name

#### Scenario: The contract picker filters by customer
- **GIVEN** two customers with separate contracts
- **WHEN** the desk reads the contracts of the first customer
- **THEN** only that customer's contracts come back
