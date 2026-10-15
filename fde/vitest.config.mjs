import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary'],
      include: [
        'src/main/**/*.mjs',
        'src/preload/**/*.mjs',
        'src/renderer/logic/**/*.mjs',
      ],
      // Excluded with reason: src/main/main.mjs is the process entry point.
      // It only wires the tested modules together and runs inside a real
      // Electron process; its behavior is covered by the integration tests
      // of the modules it wires and by the packaged smoke test.
      exclude: ['src/main/main.mjs'],
      thresholds: {
        lines: 100,
        branches: 100,
        functions: 100,
        statements: 100,
      },
    },
  },
})
