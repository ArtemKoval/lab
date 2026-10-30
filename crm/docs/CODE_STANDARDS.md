# Code standards

- Keep functions small. The complexity cap is 10.
- Name engine things with engine nouns: case, contract, award, worker,
  decision. Name nothing in a pack from the engine.
- Every API operation has an `operation_id`, a one-line docstring, and no
  optional inputs in its request model.
- Tests never call a model or a network. The stub model stands in for
  OpenRouter, and the e2e posts decisions through the API.
- Do not lower a threshold, turn off a rule, or exclude a file to get a
  green run. If a rule looks wrong, stop and ask. One written exception
  exists: the duplication gate skips the two API clients, whose one
  function per operation is a contract, and other gates still cover them.
