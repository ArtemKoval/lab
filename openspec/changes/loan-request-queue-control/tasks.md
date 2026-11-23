## 1. Backend

- [x] 1.1 The `POST /api/cases` route in `crm/backend/main.py`: the
  request model, the customer and contract validation with 404s, the id
  generation from the pack's series, the waiting write, and the reply.
- [x] 1.2 The customer-search amendment (the name query turns optional,
  absent means every customer, the guard widens to the worker and agent
  guard) and the new `GET /api/customers/{customer_id}/contracts` read.
- [x] 1.3 The id-generation helper as a pure function with unit tests
  (prefix retention, the next number past the highest regular case,
  evaluation copies excluded, the no-cases `C-1` fallback).

## 2. Dashboard

- [x] 2.1 The API client gains the create and picker calls in
  `crm/dashboard/src/api.ts`.
- [x] 2.2 The "Add a loan request" control on `QueuePage.tsx`: the form
  (member picker, contract picker filtered by member, title, story,
  replacement price), the refusal surface, and the queue refresh, reading
  the words from the pack vocabulary.
- [x] 2.3 QueuePage tests: the control renders on the library pack,
  submits, surfaces a refusal, and does not render without the
  vocabulary.

## 3. Verification

- [x] 3.1 The crm Python suite green with the new route tests.
- [x] 3.2 The dashboard suite (vitest) green with the new QueuePage
  tests.
- [x] 3.3 ruff and pyright clean on the changed backend files.
- [x] 3.4 tsc and eslint clean on the changed dashboard files.
- [x] 3.5 `openspec validate --strict` and the spec STE pytest gate pass
  (run before push. The Write hook cannot see worktree paths).
- [x] 3.6 The vendored gates on the new id helper's module: crapper at 10
  or less, dryer with no pair at 0.8, the mutator with no survivors.
