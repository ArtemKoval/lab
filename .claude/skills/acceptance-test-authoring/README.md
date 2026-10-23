# acceptance-test-authoring

Ported from intent-driven-dev/intent-driven-template (MIT, commit b5bda460a218).

Harness notes:

- The `stack:` key in `openspec/config.yaml` is a convention this skill reads itself. The openspec CLI does not parse it.
- The `spec-as-source` layer is disabled in this harness. The skill still works for standalone acceptance-suite setup.
