## 1. The loader and the pack endpoint

- [x] 1.1 Validate the vocabulary in the loader. Refuse unknown formats and name the key. Accept a pack with no section. Unit tests for the three paths.
- [x] 1.2 Carry the vocabulary on `PackView` and serve it on `GET /api/pack`. Pytest for the library answer and the absent field.

## 2. The packs' vocabulary

- [x] 2.1 Write the insurance vocabulary with today's words. Carry the labels, the contract rows with their empty words and trip template, the `money` format, and the four messages.
- [x] 2.2 Write the library vocabulary from `crm/docs/vocabulary_inventory.md`. Carry the loan-desk keys, the Membership rows over the record's fields, the `days` format, and the four messages.

## 3. The dashboard renders the pack's words

- [x] 3.1 Add the pack context with the label lookup and the award formatter. Unit tests for lookup, fallback, and both formats.
- [x] 3.2 Rewrite `ContractPanel` as the rows renderer over the record. Unit tests against both packs' records.
- [x] 3.3 Swap the labels on every surface that `crm/docs/vocabulary_inventory.md` lists. Make the sign-in lead pack-neutral. Follow `inventory.md`'s keys.
- [x] 3.4 Call the award formatter at every call site that `crm/docs/vocabulary_inventory.md` names. Assert the days rendering in vitest at each.
- [x] 3.5 Give the settings input its unit from the pack's award format. Pin the insurance input at today's rendering in vitest.
- [x] 3.6 Pin today's insurance contract panel output in vitest, so the pack with no rows renders as before.

## 4. The backend's refusal messages

- [x] 4.1 Compose the four refusals from the pack's messages, with the limit in the pack's unit. Pytest for both packs. The insurance templates carry today's strings, so their three pinned e2e specs stay green.
- [x] 4.2 Add the library pack test for the vocabulary. Assert no row names a field outside the mapped ones, and no label carries an insurance word.

## 5. Tests and gates

- [x] 5.1 Update the library e2e spec to the loan-desk words. Run the library e2e on external addresses.
- [x] 5.2 Run the default-pack e2e. Prove the insurance pages and specs unchanged.
- [x] 5.3 Run the whole hermetic suite, the TypeScript gates, and the three gates on the changed code.
